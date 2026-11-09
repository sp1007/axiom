---
id: T460
title: E12.2 — Float formatting, exact parsing & std.core.float methods
phase: P12-numeric-floating-point-simd
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T458, T459, T454]
priority: 150
status: todo
attempts: 0
paths: [std/core/float.ax, std/text/fmt/float.ax, tests/std/float_fmt]
locks: [std/core/prelude.ax, std/text/fmt/format.ax, tests/selfhost]
spec: [spec/SPEC-41-floating-point.md, tasks/0331, tasks/0338, tasks/0345]
covers: [REQ-SIMD-160, REQ-SIMD-322]
---
# T460 — E12.2 — Float formatting, exact parsing & std.core.float methods

## Goal
Implement `std/core/float.ax` (`f32`/`f64` constants, classification, `total_cmp`, bit conversions) and `std/text/fmt/float.ax` (shortest round-trip decimal formatting, fixed/scientific formatting, and exact decimal parsing).

## Scope
- Create `std/core/float.ax` providing `f32` and `f64` (and `f16` half-precision per ADR-0039 / `T480`) associated constants (`INFINITY`, `NEG_INFINITY`, `NAN`, `EPSILON`, `MIN`, `MAX`, `MIN_POSITIVE`, `MANTISSA_DIGITS`, `MIN_EXP`, `MAX_EXP`, `RADIX`), `FpCategory`, classification predicates (`is_nan`, `is_infinite`, `is_finite`, `is_normal`, `is_subnormal`, `is_sign_positive`, `is_sign_negative`, `classify`), IEEE total ordering (`total_cmp`), `clamp`, `to_bits`, `from_bits`, `to_degrees`, `to_radians`, `next_up`, and `next_down`.
- Create `std/text/fmt/float.ax` and wire it into `std/text/fmt/format.ax`: shortest round-trip decimal output (`parse(format(x)) == x` bit-for-bit for all finite `f32`/`f64`), fixed-precision (`format_f64_fixed(x, decimals)`), scientific notation (`format_f64_exp`), and canonical formatting of `NaN`, `inf`, `-inf`, and `-0.0`.
- Implement exact round-to-nearest-even float parsing (`parse_f32`, `parse_f64` -> `Result<f32/f64, ParseFloatError>`) in `std/text/fmt/float.ax`.

## Acceptance
- [ ] `tests/std/float_fmt/*.ax` passes under both `--interp` and native x86-64 (`WEAK-NATIVE 0`), verifying `f32`/`f64` classification, `total_cmp` across `-inf < -0.0 < +0.0 < +inf < NaN`, shortest round-trip formatting, fixed-precision formatting, and exact decimal parsing (including subnormals and boundary midpoints).
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T460` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T460-report.md` with exact `## Files changed`.

## Out of scope
- Transcendental mathematical library `std.math` (`T461`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T460/build` and `python tools/axtest.py --compiler build-snap-T460/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
