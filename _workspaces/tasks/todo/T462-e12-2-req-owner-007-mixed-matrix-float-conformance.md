---
id: T462
title: E12.2 — REQ-OWNER-007 complex mixed-type expression matrix & IEEE-754 conformance suite
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: sonnet
depends: [T456, T457, T458, T459, T460, T461]
priority: 152
status: todo
attempts: 0
paths: [tests/run/numeric/mixed_expr_matrix, tests/conformance/p12/e12_2_floating_point]
spec: [spec/SPEC-41-floating-point.md, spec/requirements/OWNER.md, tasks/0331, tasks/0338, tasks/0345]
covers: [REQ-OWNER-007, REQ-SIMD-164, REQ-SIMD-165, REQ-SIMD-326, REQ-SIMD-327]
---
# T462 — E12.2 — REQ-OWNER-007 complex mixed-type expression matrix & IEEE-754 conformance suite

## Goal
Certify `REQ-OWNER-007` (Complex Mixed-Type Expression Matrix Patterns A, B, C, D and homogeneous `MIR_RVALUE_CAST` lowering) and the `E12.2` IEEE-754 floating-point exit criteria with differential `--interp` vs native x86-64 conformance tests.

## Scope
- Create `tests/run/numeric/mixed_expr_matrix/` containing the four mandatory `REQ-OWNER-007` expression patterns without suffixes or manual `as` casts:
  - **Pattern A**: `let y: f64 = ((a + i * k - 1) / (2 * n + u - 3)) * (w + 0.5) + (base - u * 4 + i) / (a * a / 6.0 - k + 2)` mixing `a: f64`, `w: f32`, `i: i32`, `k: i16`, `u: u16`, `n: usize`, `base: i64`, and unsuffixed int/float literals;
  - **Pattern B**: `let z: f64 = (((mask >> sh) & 0x3F) + delta * step - 5) * scale / ((1 << sh) + 3)` mixing `mask: u32`, `sh: u8`, `delta: i8`, `step: isize`, `scale: f64`, and hex/int literals;
  - **Pattern C**: `let p: f64 = coeff[idx + off] * (x - 3) / (idx * 2 + 1) + coeff[idx - 1] * 4` and `let ok: bool = (p + i * 0.5) > (base / 10 - u + 1.25)` mixing `idx: u8`, `off: isize`, `coeff: [4]f32`, `x: f64`, array indexing, and relational comparisons;
  - **Pattern D**: `let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8)` mixing `b8: u8`, `s8: i8`, `u16v: u16`, `s32: i32`, `s64: i64`;
  plus golden `--emit=mir` checks proving every implicit promotion is emitted as an explicit `MIR_RVALUE_CAST` temporary with 100% homogeneous instruction operands.
- Create `tests/conformance/p12/e12_2_floating_point/` testing IEEE-754 edge cases (`NaN` payloads, `-0.0`, subnormals, rounding, saturating `FloatToInt`, Win64 XMM ABI stress with 16+ live float locals, round-trip formatting/parsing, and `std.math` accuracy) with differential `--interp` vs native x86-64 verification.

## Acceptance
- [ ] All tests in `tests/run/numeric/mixed_expr_matrix/` (including Patterns A, B, C, D) and `tests/conformance/p12/e12_2_floating_point/` pass under `axiomc2.exe` (`0 FAIL`, `WEAK-NATIVE 0`) with bit-identical `--interp` and native x86-64 outputs.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T462-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or standard library production source files.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T462/build` and `python tools/axtest.py --compiler build-snap-T462/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
