---
id: T437
title: Affordable complete suite — sound per-test result cache in axtest (compiler --dep-file), selfhost compile profile, longest-first scheduling
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: []
priority: 11
status: done
attempts: 0
timeout_min: 900
paths: [tools/axtest.py, tools/axtest_cache.py, tools/tests/axtest, tests/driver/dep_file]
locks: [compiler/driver, compiler/source, tests/selfhost]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-056, REQ-TST-057]
superseded_by: T437a
finished: 2026-11-13 11:31:02
---
# T437 — Sound per-test result cache and complete-suite cost reduction

## Goal
The complete suite required at every gate (owner decision 2026-11-13) becomes affordable without dropping coverage:
a test whose compiler binary and exact inputs are byte-identical to an earlier passing run is reported from a cache,
everything else reruns; the cost of the heavy `tests/selfhost` bundles is measured and the run is scheduled so the
wall time is not dominated by a late heavy bundle.

## Scope
- Compiler: `axiomc2 build|run|check|inspect --dep-file=<path>` writes every source file the source database loaded
  (root, module files, std, prelude, lang-item modules, `axiom.toml`), one `<path> <sha256>` per line, sorted, paths
  relative to the repo root or `<std>/`. Written also when the compile fails. Add it in `compiler/driver` (and
  `compiler/source` if the file list lives there); regenerate with their generators the selfhost bundles that embed the
  edited modules.
- Runner (`tools/axtest.py`, cache logic may live in `tools/axtest_cache.py`): implement ADR-0041 §4 exactly —
  S1 key completeness, S2 dep list from the same run (re-hash after the run; fallback superset "test dir tree + whole
  std root" when the compiler lacks `--dep-file`), S3 only PASS stored, S4 never-cached classes (`cmd:` without
  `cache-inputs:`, `requires:`, thread/sync/async/time deps, `nocache:`), S5 provenance (snapshot id, base commit, change
  set hash; `--gate` mode accepts only snapshot entries whose base commit is an ancestor of HEAD and whose compiler was
  built by `tools/build_axiomc.py`), S6 verification sample (`--verify-sample`, max(20, 5 %) of hits, seed printed),
  S7 integrity (one file per entry, atomic write, record hash, corrupt = miss + delete; `--cache-dir`, default
  `_workspaces/artifacts/axtest-cache/`, LRU size bound), S8 `CACHED n` in the summary, `--no-cache`.
- `--baseline <file>`: after the run print `BASELINE OK` or `NEW FAILURES: <ids>` and `BASELINE NOW PASSING: <ids>`
  using `_workspaces/baseline-failures.txt` format (ADR-0041 §1); exit status unchanged.
- Longest-first scheduling: record per-entry durations (also of misses) and start the longest tests first under `-j N`.
- Profile one heavy bundle (`tests/selfhost/opt/qa_opt_pipeline.ax`, ~552 s for 3 modes at `-j 2`) with `--time-passes`
  under `axiomc2` in `--interp`, `-O0` and `-O1`; put the per-pass table and a measured before/after wall time of the
  complete `tests/selfhost` group (cold cache vs warm cache, same binary) in the report. Do not optimise compiler passes;
  list candidates (> 30 % of compile time or super-linear) for the architect.
- Document the new flags in the report (section "Harness follow-up") so the architect updates
  `.claude/skills/axiom-testing/SKILL.md` and `.claude/agents/axiom-qa.md`; this task does not edit `.claude/`.

## Acceptance
- [ ] `tools/tests/axtest` self-tests (stub compiler) cover: hit on identical inputs; miss after changing one byte of
  the test, of an expectation file, of any dep-file entry, of the compiler binary, of the runner, of an option/env var,
  of the mode; FAIL/SKIP/timeout never stored; S4 classes never cached; corrupt entry = miss and deleted; `--gate`
  rejects `origin: local` entries and entries whose base commit is not an ancestor of HEAD; verification-sample
  mismatch disables the cache for the run; concurrent writers (`-j 4`) never produce a torn entry.
- [ ] `tests/driver/dep_file/*` checks `--dep-file` output (multi-file module, std import, prelude, failing compile) in
  the exact format above.
- [ ] Measured in `build-snap-T437`: a second complete run with the same binary and no source change reports every
  cacheable id as `CACHED`, still runs every non-cacheable id, and its failing-id set equals the first run's; numbers in
  the report.
- [ ] Complete suite (fresh, `--no-cache`) under `axiomc2.exe` built in `build-snap-T437`: failing ids are a subset of
  `_workspaces/baseline-failures.txt` (checked with the new `--baseline`); WEAK-NATIVE 0; `archcheck.py` clean;
  `python tools/tests/axtest/run_selftests.py` passes.
- [ ] Report `_workspaces/reports/T437-report.md` with the profile table, timings, and exact `## Files changed`.

## Out of scope
- Caching `cmd:` oracle tests without declared inputs; remote/shared-machine caches; optimising compiler passes;
  editing `.claude/` harness files; `bootstrap/axiom0`; `docs/`.

## Notes
- The binary hash is in the key, so any compiler change invalidates every entry; the cache pays off on fix rounds,
  resumed/chunked gate runs and std/test-only tasks (precise `--dep-file` keeps unrelated tests cached when std changes).
  Stage-2 builds are reproducible (T087 fixed point), so the same sources give the same binary hash.
- Machine is a shared 4-core laptop: run suites with `-j 2`.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041 §4, owner decision 2026-11-13)
- 2026-11-13 11:31:02 superseded by T437a -> done (no code of its own)
- 2026-11-13 architect: split into T437a (runner/gate tooling, no deps, priority 10) and T437b (compiler `--dep-file`,
  depends T452 + T437a); dependency on T452 moved to T437b (ADR-0041 §6)
