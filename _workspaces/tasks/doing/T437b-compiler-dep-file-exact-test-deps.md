---
id: T437b
title: Compiler --dep-file (exact per-test inputs) for the axtest cache and --affected; selfhost bundle regeneration
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T452, T437a]
priority: 11
status: doing
attempts: 1
timeout_min: 900
paths: [tests/driver/dep_file]
locks: [compiler/driver, compiler/source, tests/selfhost, tools/axtest_cache.py, tools/axtest_affected.py]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-056]
started: 2026-11-13 16:42:55
agent: T437b-impl
---
# T437b — Compiler `--dep-file` and exact test dependencies

## Goal
`axiomc2` reports every source file it loaded, so the T437a cache keys and the `--affected` selection use exact
per-test inputs instead of the "test dir + whole std" superset: a std-only change keeps unrelated tests cached and
selects only the tests that load the changed file (ADR-0041 §4 S2, §6).

## Scope
- Compiler: `axiomc2 build|run|check|inspect --dep-file=<path>` writes every source file the source database loaded
  (root, module files, std, prelude, lang-item modules, `axiom.toml`), one `<path> <sha256>` per line, sorted, paths
  relative to the repo root or `<std>/`. Written also when the compile fails. In `compiler/driver` (and
  `compiler/source` if the file list lives there); regenerate with their generators the selfhost bundles that embed
  the edited modules.
- Runner: only the fixes the real flag needs in `tools/axtest_cache.py` / `tools/axtest_affected.py` (the probe and
  the exact path were built and stub-tested in T437a).
- G2 (T437a-qa, ADR-0042 §5): the never-cache (nondeterministic leaf binding) scan must cover the implicitly loaded
  prelude files. Exact mode: `exact_deps_nondet` scans every file of the dep list, prelude included (assert it in a
  test). Superset mode (compiler without `--dep-file`): seed the `std.a.b` traversal with
  `std/core/{prelude,option,result,host}.ax` (or the list the compiler loads implicitly, read from one place).
- Measure the complete `tests/selfhost` group twice with the same binary (cold `--no-cache`, then warm) and one
  std-only change scenario (touch one std file in a scratch copy: count of misses vs the superset fallback).

## Acceptance
- [ ] `tests/driver/dep_file/*` checks `--dep-file` output (multi-file module, std import, prelude, failing compile)
  in the exact format above.
- [ ] Measured in `build-snap-T437b`: a second run of the `tests/selfhost` group and of the smoke set with the same
  binary and no source change reports every cacheable id as `CACHED`, still runs every non-cacheable id, and its
  failing-id set equals the first run's; cache entries show `dep_source: exact`; the std-only scenario re-runs only
  tests whose dep list contains the file; numbers in the report.
- [ ] G2 self-test: a synthetic prelude function calling a nondeterministic leaf (`monotonic_ns`) used by a test with
  no `std.` text makes that test uncacheable in both exact and superset mode (scratch copy, as in T437a-qa G2).
- [ ] Gate per axiom-qa.md "Per-task gate scope" via `tools/taskgate.py`, plus the regenerated selfhost bundle tests
  of the edited modules; failing ids ⊆ `_workspaces/baseline-failures.txt` (`--baseline`); `archcheck.py` clean;
  `python tools/tests/axtest/run_selftests.py` passes.
- [ ] Report `_workspaces/reports/T437b-report.md` with timings, a "Harness follow-up" section and exact
  `## Files changed`.

## Out of scope
- Caching `cmd:` tests without `cache-inputs:`; remote caches; optimising compiler passes; `.claude/`;
  `bootstrap/axiom0`; `docs/`.

## Notes
- Stage-2 builds are reproducible (T087 fixed point), so the same sources give the same binary hash.
- Machine is a shared 4-core laptop: `-j 2`.

## Log
- 2026-11-13 created by axiom-architect: split of T437 (compiler part; ADR-0041 §6)
- 2026-11-13 axiom-architect: G2 (prelude files in the never-cache scan) added to scope (ADR-0042 §5)
- 2026-11-13 16:42:55 started (attempt 1) T437b-impl
