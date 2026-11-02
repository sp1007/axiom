---
id: T461
title: E12.2 — std.math deterministic elementary & transcendental library
phase: P12-numeric-floating-point-simd
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T460]
priority: 151
status: todo
attempts: 0
paths: [std/math, tests/std/math]
locks: [std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-41-floating-point.md, tasks/0334, tasks/0338, tasks/0345, tasks/0469]
covers: [REQ-SIMD-142, REQ-SIMD-143, REQ-SIMD-304, REQ-SIMD-305]
---
# T461 — E12.2 — std.math deterministic elementary & transcendental library

## Goal
Implement `std/math/` in pure Axiom (zero CRT/libm dependency), delivering deterministic elementary and transcendental functions for `f32` and `f64` that satisfy the `SPEC-41` ULP accuracy contract identically in `--interp` and native x86-64.

## Scope
- Create `std/math/mod.ax` with mathematical constants (`PI`, `TAU`, `E`, `LN_2`, `LN_10`, `LOG2_E`, `LOG10_E`, `SQRT_2`, `FRAC_1_SQRT_2`, `FRAC_PI_2`, `FRAC_PI_3`, `FRAC_PI_4`, `FRAC_PI_6`, `FRAC_PI_8`, `FRAC_1_PI`, `FRAC_2_PI`, `FRAC_2_SQRT_PI`) for `f32` and `f64`.
- Implement deterministic IEEE-754 elementary and rounding operations: `abs`, `copysign`, `signum`, `floor`, `ceil`, `trunc`, `round`, `round_ties_even`, `fract`, `modf`, `frexp`, `ldexp`, `scalbn`, `fma`, `sqrt`, `cbrt`, `hypot`, `min`, `max`, `clamp`, `div_euclid`, `rem_euclid`.
- Implement deterministic polynomial/rational minimax approximations with Cody-Waite / Payne-Hanek range reduction for `exp`, `exp2`, `expm1`, `ln`, `log2`, `log10`, `ln_1p`, `powf`, `powi`, `sin`, `cos`, `tan`, `sincos`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`, `erf`, and `erfc` within the `SPEC-41` ULP budget.

## Acceptance
- [ ] `tests/std/math/*.ax` passes under both `--interp` and native x86-64 (`WEAK-NATIVE 0`), verifying special values (`NaN`, `±0.0`, `±inf`), identities, and ≤ 1 ULP accuracy against reference vectors.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T461` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T461-report.md` with exact `## Files changed`.

## Out of scope
- SIMD vector math intrinsics (`T466`, `T473`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T461/build` and `python tools/axtest.py --compiler build-snap-T461/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
