---
id: T455
title: E12.1 — Integer model completion & Pattern D mixed-width conformance suite
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T450, T451, T452, T453, T454]
priority: 145
status: todo
attempts: 0
paths: [tests/conformance/p12/e12_1_integers, tests/run/numeric/mixed_int_matrix]
spec: [spec/SPEC-40-integers.md, spec/requirements/OWNER.md, tasks/0327, tasks/0334, tasks/0431]
covers: [REQ-OWNER-007, REQ-SIMD-100, REQ-SIMD-262]
---
# T455 — E12.1 — Integer model completion & Pattern D mixed-width conformance suite

## Goal
Certify the `E12.1` integer model completion and `REQ-OWNER-007` Pattern D pure-integer multi-width expression promotion rules across the MIR interpreter oracle and native Windows x86-64 execution.

## Scope
- Create `tests/conformance/p12/e12_1_integers/` testing all 12 integer types (`i8..i128`, `u8..u128`, `isize`, `usize`): boundary values (`MIN`, `MAX`, `0`, `-1`), checked overflow panics, `wrapping_*`, `saturating_*`, `checked_*`, `overflowing_*`, bit operations, endian byte round-trips, and `From`/`TryFrom` conversions.
- Create `tests/run/numeric/mixed_int_matrix/` exercising `REQ-OWNER-007` **Pattern D** (`let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8)` with `b8: u8 = 200`, `s8: i8 = -50`, `u16v: u16 = 3000`, `s32: i32 = -100000`, `s64: i64 = 5000000000`) and deep multi-width integer/shift/bitwise/comparison trees, verifying both `--emit=mir` homogeneous `MIR_RVALUE_CAST` lowering and bit-identical `--interp` vs native execution.

## Acceptance
- [ ] All tests in `tests/conformance/p12/e12_1_integers/` and `tests/run/numeric/mixed_int_matrix/` pass under `axiomc2.exe` with `0 FAIL` and `WEAK-NATIVE 0`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T455-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or standard library production source files.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T455/build` and `python tools/axtest.py --compiler build-snap-T455/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
