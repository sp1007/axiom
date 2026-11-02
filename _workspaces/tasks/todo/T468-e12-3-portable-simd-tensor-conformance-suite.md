---
id: T468
title: E12.3 — Portable SIMD, mask, gather/scatter & tensor-view conformance suite
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T463, T464, T465, T466, T467]
priority: 158
status: todo
attempts: 0
paths: [tests/conformance/p12/e12_3_simd_vectors, tests/ui/simd/capability_bounds]
spec: [spec/SPEC-42-simd.md, 0095, tasks/0337, tasks/0341, tasks/0344, tasks/0347]
covers: [REQ-SIMD-044, REQ-SIMD-045, REQ-SIMD-078, REQ-SIMD-161, REQ-SIMD-162, REQ-SIMD-245, REQ-SIMD-246, REQ-SIMD-323, REQ-SIMD-324]
---
# T468 — E12.3 — Portable SIMD, mask, gather/scatter & tensor-view conformance suite

## Goal
Certify the `E12.3` portable SIMD, mask, gather/scatter, and `TensorView`/`MatrixView` conformance suite.

## Scope
- Create `tests/conformance/p12/e12_3_simd_vectors/` exercising all `Vector<T, N>` and `Mask<N>` widths (`N = 2, 4, 8, 16, 32, 64`) and element types (`i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`), lane-wise checked/wrapping/saturating arithmetic, IEEE-754 NaN/signed-zero lane behavior, `select`, `shuffle`, ordered vs associative reductions, inactive-lane memory safety on `load_masked`/`store_masked`/`gather`/`scatter`, and `TensorView`/`MatrixView` operations.
- Create negative compile-time tests in `tests/ui/simd/capability_bounds/` verifying that `TensorMutView` and `std.simd` slice operations obey Axiom capability exclusivity and reject mutating through shared views or mismatched `bitcast` types.

## Acceptance
- [ ] All tests in `tests/conformance/p12/e12_3_simd_vectors/` and `tests/ui/simd/capability_bounds/` pass under `axiomc2.exe` (`0 FAIL`).
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T468-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or standard library production source files.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T468/build` and `python tools/axtest.py --compiler build-snap-T468/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
