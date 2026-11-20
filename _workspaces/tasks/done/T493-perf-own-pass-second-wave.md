---
id: T493
title: Perf — cut the remaining `own` pass time (~28 s on qa_backend_unit, ~40% of post-T486 compile time) by ≥ 3× with byte-identical output
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T449, T486]
priority: 10
status: done
attempts: 1
timeout_min: 900
paths: [compiler/own, tests/perf/own_scaling]
locks: [compiler/driver/pipeline.ax]
spec: [spec/SPEC-76-performance-contract.md, spec/SPEC-20-selfhost.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-OPT-292]
started: 2026-11-20 01:46:46
finished: 2026-11-20 07:38:41
---
# T493 — Perf: second-wave optimisation of the `own` pass

## Why (owner request 2026-11-19)
After T485 (3.4×–7.2× on `own`) and T486 (11.6×–20.7× on `build`), `own` is now the single largest remaining stage of
compilation: on `tests/selfhost/backend/qa_backend_unit.ax` (~95k lines) post-T486 (`a3d22928`), `own` takes **28.2 s**
out of **74.2 s** total wall time (**38–42% of the entire compile**; ~40 s on `qa_driver_commands_b.ax`), while
`lex + parse + resolve + hir + typeck` together take only ~9.6 s. Cutting `own` further speeds up every compiler build
and every `taskgate` run without dropping any test coverage.

## Scope
- First split and profile `own` (sampling profiler on native `axiomc2` + optional `time-own:` sub-timers under
  `--time-passes` in `compiler/driver/pipeline.ax` while keeping all existing top-level `time:` lines unchanged):
  measure `unsafe_check` / concurrency check vs `own_check` (init/move/drop dataflow) vs `own_cap_check` (borrow/cap
  analysis) vs any remaining per-body/per-block allocations or scans.
- Note from T485 report: `tests/selfhost/bundle_common.py` text-patches the fixpoint loops of `own_check` /
  `own_cap_check` when assembling bundles. Either preserve those patch anchors intact (verify identical patch counts
  in regenerated bundles) or cleanly move the algorithmic speedups into the compiled Axiom code without breaking
  bundle assembly.
- Eliminate the dominant remaining hot spots in `compiler/own/**` (e.g. per-block state copying / merge overhead,
  repeated path-tree / symbol / def lookups in `unsafe.ax` / `cap.ax` / `move.ax` / `init.ax`, redundant passes over
  pure/trivial functions, dense loops over all locals when only a few change). Purely algorithmic changes — no semantic
  or diagnostic changes.
- Tighten/extend `tests/perf/own_scaling/` to guard the improved scaling and verify sub-timer / determinism hygiene.

## Acceptance (quality guards — mandatory, this is a compiler)
- **Byte-identical output**: every `tests/selfhost/**` bundle and every `tests/run/**` program produces byte-identical
  `.exe` at `-O0` and `-O1` (and identical `--emit=mir` dumps) before/after (`INV-DET-004`); script + summary in the
  report.
- Diagnostics: `tests/ui/**` and `tests/conformance/**` outputs unchanged (normal gate).
- Self-host fixed point holds (`stage-2 == stage-3`, byte-identical).
- Report before/after `--time-passes` for at least 3 large bundles (`qa_backend_unit.ax`, `qa_driver_commands_b.ax`,
  `axiomc_bundle`); target: `own` ≥ 3× faster on `qa_backend_unit.ax` (from ~28 s to ≤ ~9 s). If the target is not
  reached, document the measured speedup and remaining hot spots honestly.
- Normal gate (`taskgate.py --task T493`); report `_workspaces/reports/T493-report.md` with exact `## Files changed`.

## Out of scope
- Changing ownership/borrow/concurrency semantics or diagnostic wording; `bootstrap/axiom0`; `docs/`; `std/`.

## Log
- 2026-11-19 created by orchestrator (owner request: option 1 — optimise remaining `own` pass after T486)
- 2026-11-20 01:46:46 started (attempt 1) T493-impl
- 2026-11-20 07:38:41 accepted by QA -> done
