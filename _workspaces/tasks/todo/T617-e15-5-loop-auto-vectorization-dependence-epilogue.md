---
id: T617
title: E15.5 — Loop auto-vectorization legality, capability-disjoint dependence proving, reduction recognition & scalar tail/epilogue generation
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T312, T611, T616]
priority: 111
status: todo
attempts: 0
paths: [compiler/opt/vectorize, tests/run/opt_loop_vec]
spec: [spec/SPEC-74-auto-vectorization.md, 0095, tasks/0402, tasks/0403, tasks/0406, tasks/0407]
covers: [REQ-OPT-206, REQ-OPT-209, REQ-OPT-210, REQ-OPT-211]
---
# T617 — E15.5 — Loop auto-vectorization legality, capability-disjoint dependence proving, reduction recognition & scalar tail/epilogue generation

## Goal
Implement the loop auto-vectorization engine in `compiler/opt/vectorize` consuming `SCEV`, `AliasInfo`, and `RangeInfo` to vectorize counted scalar loops into typed `OptIR`/MIR vector operations with scalar tail/epilogue cleanup per `spec/SPEC-74-auto-vectorization.md`.

## Scope
- Implement loop-carried memory dependence proving in `compiler/opt/vectorize` leveraging `AliasInfo` (disjoint `mut_view<[T]>` / `view<[T]>`) and `SCEV` distance analysis, rejecting loops with backward loop-carried dependencies, atomics, `volatile`, or unproven aliasing.
- Implement associative integer (`wrapping_*` and proven non-overflowing) and permitted floating-point reduction recognition (`REQ-OPT-206`), uniform/broadcast operand widening, and predicated select (`cmov`/blend) lowering.
- Query target SIMD capabilities (`REQ-OPT-209..211`) to select legal lane widths (`128`-bit SSE2 baseline or `256`-bit AVX2 when enabled) and emit the vectorized main loop plus scalar remainder epilogue for non-multiple trip counts.

## Acceptance
- [ ] Differential run and dump tests in `tests/run/opt_loop_vec` verify automatic vectorization of slice/array elementwise loops and reductions across non-multiple trip counts, and verify conservative scalar retention on overlapping/unknown-alias pointers or strict FP reductions.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T617-report.md` with exact `## Files changed`.

## Out of scope
- Straight-line SLP vectorization and LIR cost-model lowering (`T618`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`); depends on P12 gate `T312` (`ROADMAP.md` §3/§4).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T617/build` and `python tools/axtest.py --compiler build-snap-T617/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:42:00 created by T215 (P15 phase planning)
