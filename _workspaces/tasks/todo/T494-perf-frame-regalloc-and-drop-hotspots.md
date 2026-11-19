---
id: T494
title: Perf — cut the remaining `frame`/regalloc, `mir_drop`, and `isel` hotspots in `build` (~35.5 s of 50.3 s on axiomc_bundle) by ≥ 2.5× with byte-identical output
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T486]
priority: 10
status: todo
attempts: 0
timeout_min: 900
paths: [compiler/target/x64/frame.ax, compiler/target/x64/isel.ax, compiler/mir/drop.ax, tests/perf/build_scaling]
locks: [compiler/backend/session.ax]
spec: [spec/SPEC-76-performance-contract.md, spec/SPEC-20-selfhost.md]
covers: [REQ-OPT-292]
---
# T494 — Perf: optimise remaining `frame`, `mir_drop`, and `isel` hotspots in `build`

## Why (owner request 2026-11-19)
T486 (`a3d22928`) cut the `build` phase by 11.6×–20.7× (from 1041.9 s to 50.3 s on `axiomc_bundle -O1` and from 373.3 s
to 32.2 s on `qa_backend_unit -O0`). T486's `time-build:` sub-timers show that **70% of the remaining `build` time**
is concentrated in just three sub-phases:

| Sub-phase | `qa_backend_unit -O0` | `qa_backend_unit -O1` | `axiomc_bundle -O1` |
|---|---:|---:|---:|
| `frame` (`compiler/target/x64/frame.ax`) | 12.86 s (40%) | 9.74 s (38%) | 18.80 s (37%) |
| `mir_drop` (`compiler/mir/drop.ax`) | 5.43 s (17%) | 4.30 s (17%) | 8.27 s (16%) |
| `isel` (`compiler/target/x64/isel.ax`) | 3.14 s (10%) | 4.29 s (17%) | 8.40 s (17%) |
| **Subtotal of these 3** | **21.43 s / 32.16 s** | **18.33 s / 25.62 s** | **35.47 s / 50.29 s** |

Optimising these three hotspots cuts `build` time another 2.5×–3× on every self-host compile and every `taskgate` run
with zero loss of test coverage.

## Scope
- Profile `frame` (`compiler/target/x64/frame.ax`), `mir_drop` (`compiler/mir/drop.ax`), and `isel`
  (`compiler/target/x64/isel.ax`) on `qa_backend_unit.ax` and `axiomc_bundle` (sampling profiler / targeted counters).
- Eliminate the dominant algorithmic bottlenecks in each module:
  - `frame.ax`: live-range construction, interference / spill-slot coloring, register allocation inner loops,
    per-function arena/array zeroing & scans.
  - `mir/drop.ax`: drop elaboration dataflow, per-local/per-block scans, type-has-drop caching across locals/types.
  - `isel.ax`: instruction-selection dispatch, operand/vreg table scans, constant/symbol lowering overhead.
- Purely algorithmic changes: preserve **100% byte-identical** `.exe` output at both `-O0` and `-O1` (no change to
  allocation order, spill-slot assignment, or emitted machine code).
- Extend `tests/perf/build_scaling/` with a regression check guarding the tighter `frame` / `build` budget.

## Acceptance (quality guards — mandatory, this is a compiler)
- **Byte-identical output**: every `tests/selfhost/**` bundle and every `tests/run/**` program produces byte-identical
  `.exe` at `-O0` and `-O1` before/after (`INV-DET-004`); script + summary in the report.
- Self-host fixed point holds (`stage-2 == stage-3`, byte-identical).
- Report before/after `time-build:` sub-timers for at least 3 large bundles (`qa_backend_unit.ax` -O0/-O1,
  `axiomc_bundle` -O1, `qa_backend_diff_mi_mc_b.ax` -O0); target: combined `frame + mir_drop + isel` ≥ 2.5× faster on
  `axiomc_bundle` and `qa_backend_unit.ax` (and total `build` on `qa_backend_unit -O1` ≤ ~12 s). If a target is not
  reached, document the measured speedup and remaining hot spots honestly.
- Normal gate (`taskgate.py --task T494`); report `_workspaces/reports/T494-report.md` with exact `## Files changed`.

## Out of scope
- Changing register allocation heuristics or generated code bytes (output must stay byte-identical); `bootstrap/axiom0`;
  `docs/`; `std/`.

## Log
- 2026-11-19 created by orchestrator (owner request: option 1 — optimise remaining `frame`, `mir_drop`, and `isel` hotspots after T486)
