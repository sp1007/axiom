---
id: T437a
title: Gate tooling — axtest result cache (fallback deps), --affected, --smoke, --baseline, longest-first, tools/taskgate.py
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: []
priority: 10
status: todo
attempts: 0
timeout_min: 600
paths: [tools/axtest.py, tools/axtest_cache.py, tools/axtest_affected.py, tools/affected_map.txt, tools/taskgate.py, tools/tests/axtest, tools/tests/taskgate, tests/smoke.list]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-056, REQ-TST-057]
---
# T437a — Per-task gate tooling: cache, affected set, smoke set, baseline check, one-command gate

## Goal
The per-task QA gate (owner decision 2026-11-13: about 60-90 minutes, `.claude/agents/axiom-qa.md` "Per-task gate
scope") runs as ONE command that selects exactly the gate scope (task tests + affected set + smoke set + archcheck),
reuses sound cached results, schedules longest-first and prints a machine-readable verdict summary. Runner-only:
this task edits nothing under `compiler/`, `std/`, `tests/selfhost/` or `bootstrap/` (ADR-0041 §6).

## Scope
(a) **Result cache** (`tools/axtest_cache.py`, wired into `tools/axtest.py`): ADR-0041 §4 S1-S8 exactly. Dependency
    source: if the compiler under test accepts `--dep-file=<path>` (probe once per binary: run it with the flag on a
    trivial input and check the file was written; cache the probe result by binary hash), use the reported list (S2,
    re-hash after the run); otherwise the sound fallback superset "test directory tree + whole std root" (+ the
    test's expectation files). Both paths are implemented and self-tested now (the stub compiler emulates
    `--dep-file`); T437b adds the flag to `axiomc2`. Flags: `--cache-dir` (default
    `_workspaces/artifacts/axtest-cache/`), `--no-cache`, `--gate` (S5), `--verify-sample` (S6, seed printed),
    `CACHED n` in the summary (S8). Entries record `dep_source: exact|superset`.
(b) **`--affected <git-range | @file-list | path...>`** (`tools/axtest_affected.py`): prints the selected test ids and,
    for every id, the rule that selected it (derivation), then runs them (or `--list` only). Rules, in order:
    1. exact: a cached entry with `dep_source: exact` whose dep list contains a changed file selects that test;
    2. grep rule of axiom-qa.md "Per-task gate scope" for every test without an exact entry: changed test files
       themselves (a helper/expectation file selects the tests of its directory); for a changed `std/` file, tests and
       std files that reference its module path (`std.a.b`, `use std.a.b`) or a public name declared or changed in
       the diff; for a changed `compiler/<mod>/...` file, the test groups mapped from that module in the checked-in
       table `tools/affected_map.txt` (e.g. `compiler/mir -> tests/mir tests/selfhost/mir`, created and filled by
       this task for every `compiler/` module directory, validated: every module has a row, every target exists),
       plus the selfhost bundle tests that embed that module (grep of the bundle generators' module lists);
       a changed `tools/X.py` selects `tools/tests/X`; `spec/`, `_workspaces/`, `.claude/` changes select nothing.
    A compiler change always also triggers rule 2's module map (the binary hash changes, so exact deps alone do not
    bound it). Output ends with counts per top-level group and the list of changed files no rule matched.
(c) **`--smoke [--seed N]`**: the checked-in `tests/smoke.list` (created by this task) holds, per top-level test
    group `tests/<group>/`, a pool of candidate ids whose recorded duration is small, plus an `always:` section with
    the Xin chào thế giới run test, one compile-fail ui test, one native-vs-interp diff test. `--smoke` runs the
    `always:` ids and one id per group drawn from the pool with the printed seed (default seed = hash of the change
    set, so each gate picks differently within a group). `--smoke --check` validates the list: every top-level group
    has a pool entry, every id exists in `axtest.py --list`, the `always:` cases are present, and the sum of the
    recorded durations of the worst-case draw is ≤ 20 minutes at `-j 2` (heavy selfhost bundles are excluded from
    pools; the `selfhost` pool uses its lightest ids).
(d) **Timing**: record per-id/per-mode durations (hits and misses) in `<cache-dir>/durations.json` (atomic write);
    under `-j N` start the longest known tests first. Measure one heavy bundle
    (`tests/selfhost/opt/qa_opt_pipeline.ax`) with `axiomc2 --time-passes` in `--interp`, `-O0`, `-O1`
    (read-only use of the bundle inside `build-snap-T437a`); put the per-pass table in the report and list passes
    > 30 % of compile time or super-linear as architect candidates. Do not optimise compiler passes.
(e) **`--baseline <file>`**: after the run print `BASELINE OK` or `NEW FAILURES: <ids>`, and
    `BASELINE NOW PASSING: <ids>` for baseline ids that ran and passed (ADR-0041 §1 format); exit status unchanged.
(f) **`tools/taskgate.py --task <ID> [--range <base>..<head> | --changed @file] [--compiler PATH] [-j 2]
    [--no-cache] [--seed N] [--json-out PATH]`**: runs, deduplicated, (1) the task's own tests (test paths in the
    task's `paths:` + `--extra <ids>`), (2) `--affected` of the change set, (3) `--smoke`, (4) `tools/archcheck.py`;
    all with `--gate --baseline _workspaces/baseline-failures.txt`. Prints a Markdown block (counts per group and per
    part, affected-set derivation, CACHED/miss/sample counts and seed, WEAK-NATIVE count, NEW/BASELINE failures,
    archcheck result, wall time) that the QA agent pastes into its QA file, and the same as JSON (`--json-out`).
    Exit 0 only if archcheck is clean and there are no NEW failures and no WEAK-NATIVE; otherwise 1.

## Acceptance
- [ ] `tools/tests/axtest` self-tests (stub compiler `stubcc.py`, extended to optionally honour `--dep-file`) cover:
  hit on identical inputs; miss after changing one byte of the test, of an expectation file, of a dep (exact list)
  and of a std file (superset fallback), of the compiler binary, of the runner, of an option/env var, of the mode;
  FAIL/SKIP/timeout never stored; S4 classes never cached; corrupt entry = miss and deleted; `--gate` rejects
  `origin: local` entries and entries whose base commit is not an ancestor of HEAD; verification-sample mismatch
  disables the cache for the run; concurrent writers (`-j 4`) never produce a torn entry; longest-first order;
  `--baseline` output for subset / new failure / now passing.
- [ ] `tools/tests/taskgate` self-tests on a temporary git fixture repo: `--affected` derivation for a std change
  (module path + public name), a compiler module change (map rows + bundle grep), a test-only change, a tools change,
  a spec-only change (empty set); exact-dep rule preferred over grep when an exact entry exists; `tools/affected_map.txt`
  validation catches a missing module row; `--smoke --check` rejects a list missing a group or over the time bound;
  `taskgate.py` end-to-end with the stub compiler produces the Markdown and JSON summary and the documented exit codes.
- [ ] Measured in `build-snap-T437a` with the real `axiomc2.exe`: `python tools/axtest.py --smoke --check` passes and
  a `--smoke` run at `-j 2` finishes in ≤ 20 minutes (time in the report); `python tools/taskgate.py --task T437a`
  on this task's own change set completes, and a second identical invocation reports its cacheable ids as `CACHED`
  with an identical failing-id set (both wall times in the report); one sample `--affected` derivation for a real
  past commit touching `std/` and one touching `compiler/` (e.g. `bda2296a`, `fa86bbfc`) shown in the report.
- [ ] Profile table of (d) in the report. `python tools/tests/axtest/run_selftests.py`,
  `python tools/tests/taskgate/run_selftests.py` and `tools/archcheck.py` pass. Existing axtest behaviour without the
  new flags is unchanged (the existing self-tests pass unmodified, except adding the new ones).
- [ ] Report `_workspaces/reports/T437a-report.md` with section "Harness follow-up" (exact flag/command text for the
  architect to put in `.claude/agents/axiom-qa.md` and `.claude/skills/axiom-testing/SKILL.md`) and exact
  `## Files changed`.

## Out of scope
- The compiler `--dep-file` flag, bundle regeneration and the complete-suite cold/warm measurement (T437b); editing
  `compiler/`, `std/`, `tests/selfhost/`, `.claude/`, `bootstrap/axiom0`, `docs/`; optimising compiler passes; editing
  `_workspaces/baseline-failures.txt`.

## Notes
- Gate scope for this task itself: its own tool self-tests + smoke + archcheck (it changes only `tools/` and
  `tests/smoke.list`, which no compiled test reads).
- Machine is a shared 4-core laptop: `-j 2`. `tools/gatecheck.py` is the phase-gate checker (T022); do not merge
  `taskgate.py` into it.

## Log
- 2026-11-13 created by axiom-architect: split of T437 (owner decision 2026-11-13, first in line; ADR-0041 §6)
- 2026-11-13 11:31:02 T437 superseded: runner part here, compiler --dep-file part in T437b
