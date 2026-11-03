---
id: T458
title: E12.2 — Oracle IEEE-754 floating-point evaluator & strict FP optimizer preservation
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T457, T452]
priority: 148
status: todo
attempts: 0
paths: [compiler/interp, compiler/opt, tests/mir/float_interp, tests/opt/float_strict, tests/selfhost]
locks: [compiler/interp_opt/session.ax, tests/selfhost]
spec: [spec/SPEC-41-floating-point.md, tasks/0331, tasks/0338, tasks/0345]
covers: [REQ-SIMD-026, REQ-SIMD-271, REQ-SIMD-272]
---
# T458 — E12.2 — Oracle IEEE-754 floating-point evaluator & strict FP optimizer preservation

## Goal
Implement bit-deterministic IEEE-754 `f32`/`f64` execution, casts, and float intrinsics in the MIR interpreter oracle (`--interp` and const-eval) and enforce strict IEEE-754 preservation in the MIR optimizer (`-O1`).

## Scope
- Extend `compiler/interp/value.ax` and `compiler/interp/interp.ax` to evaluate `f32` (IEEE-754 binary32 bits) and `f64` (IEEE-754 binary64 bits) operations: `+`, `-`, `*`, `/`, `%`, unary `-`, unordered-aware IEEE comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`), `IntToFloat` (round-to-nearest-even), saturating `FloatToInt` (`NaN -> 0`, clamped to `[MIN, MAX]`), and `FloatConvert` (`f32 <-> f64`).
- Support `ConstValue.Float` in `.rdata` constant materialization and evaluate core float intrinsics (`sqrt`, `abs`, `copysign`, `floor`, `ceil`, `trunc`, `round_ties_even`, `fma`, `min`, `max`, `to_bits`, `from_bits`) in `compiler/interp/`.
- Update `compiler/opt/const_fold.ax` and `compiler/opt/dce.ax` to respect strict IEEE-754 rules (`ANUM-43..45, 98`): never fold `x + 0.0 -> x` (preserves `-0.0`), `x * 0.0 -> 0.0` (preserves `NaN` and `-0.0`), `x - x -> 0.0`, or `x == x -> true` (preserves `NaN`), and never reassociate floating-point expressions.

## Acceptance
- [ ] `tests/mir/float_interp/*.ax` passes under `--interp` for `f32`/`f64` IEEE-754 arithmetic, `NaN`, `±0.0`, `±inf`, subnormals, saturating `FloatToInt` casts, float intrinsics, and `REQ-OWNER-007` Patterns A, B, C, D.
- [ ] `tests/opt/float_strict/*.ax` (`--emit=mir-opt -O1`) verifies that `const_fold` and `dce` preserve `-0.0`, `NaN` comparisons, and evaluation order.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T458` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T458-report.md` with exact `## Files changed`.

## Out of scope
- LIR `Xmm` register class and SSE2 native x86-64 codegen (`T459`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T458/build` and `python tools/axtest.py --compiler build-snap-T458/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
