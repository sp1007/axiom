---
id: T451
title: E12.1 — Frontend, typeck & MIR lowering for i128/u128, saturating ops & integer promotion lattice
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T450]
priority: 141
status: doing
attempts: 1
paths: [compiler/lex, compiler/syntax, compiler/hir, compiler/types, compiler/mir, tests/typeck/int128, tests/mir/int128, tests/ui/int128, tests/selfhost/lex, tests/selfhost/lexer, tests/selfhost/parse, tests/selfhost/parser, tests/selfhost/ast, tests/selfhost/hir, tests/selfhost/resolve, tests/selfhost/resolve_hir, tests/selfhost/types, tests/selfhost/typeck, tests/selfhost/typeck_traits, tests/selfhost/traits, tests/selfhost/mir, tests/selfhost/cap, tests/selfhost/own, tests/selfhost/own_mir_verify, tests/selfhost/verify, tests/selfhost/drop, tests/selfhost/intrinsics, tests/selfhost/abi, tests/selfhost/interp, tests/selfhost/interp_opt, tests/selfhost/stage1, tests/selfhost/diag]
locks: [compiler/verify/verifier.ax, compiler/diag/code.ax, tests/ui/lex, tests/conformance/vs0/lit_u64_max_plus_one.ax, tests/selfhost/opt, tests/selfhost/link, tests/selfhost/obj, tests/selfhost/backend, tests/selfhost/isel, tests/selfhost/lir, tests/selfhost/encode, tests/selfhost/driver, tests/selfhost/obj_link_driver, tests/selfhost/kernel_source_diag]
spec: [spec/SPEC-40-integers.md, spec/SPEC-04-core-extensibility.md, spec/requirements/OWNER.md, tasks/0327, tasks/0334, tasks/0431]
covers: [REQ-OWNER-007, REQ-SIMD-247, REQ-SIMD-263, REQ-SIMD-268, REQ-SIMD-318]
started: 2026-11-03 22:52:04
agent: T451-impl
---
# T451 — E12.1 — Frontend, typeck & MIR lowering for i128/u128, saturating ops & integer promotion lattice

## Goal
Activate `TypeKind.Int128` (`i128`, `u128`), `ConstValue.Int128`, and `MirBinOp.SatAdd`/`SatSub`/`SatMul` in `axiomc`, and implement the pure-integer multi-width expression promotion lattice (`REQ-OWNER-007` Pattern D) in `typeck` + HIR->MIR lowering.

## Scope
- Enable `i128` and `u128` type resolution, literal suffixes (`123i128`, `456u128`), and 128-bit literal range checks (`AX_TYPE_LITERAL_OUT_OF_RANGE` outside `-2^127..=2^127-1` / `0..=2^128-1`) in `compiler/lex/`, `compiler/types/`, and `compiler/hir/` (replacing the `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` guard in `axiomc`).
- Update `compiler/types/layout.ax` so `i128` and `u128` report `size = 16`, `align = 16`, and implement `Copy`, `Clone`, `Eq`, `PartialEq`, `Ord`, and `Hash`.
- Lower `saturating_add`, `saturating_sub`, and `saturating_mul` intrinsics/methods to `MirBinOp.SatAdd`, `SatSub`, and `SatMul` (`SPEC-04 AXS-EXT-042`) in `compiler/mir/builder.ax` and validate them in `compiler/verify/verifier.ax`.
- Implement the integer sub-lattice of `REQ-OWNER-007` in `compiler/types/typeck.ax` and `compiler/mir/builder.ax`: resolve unsuffixed `IntVar` literals and mixed-width integer operands (`i8/u8 -> i16/u16 -> i32/u32 -> i64/isize -> i128`) in nested arithmetic, bitwise/shift, array-index, and comparison expressions exclusively during type checking and HIR->MIR lowering, emitting every implicit widening promotion as an explicit `MIR_RVALUE_CAST` (`IntToInt`) temporary before the operation so `compiler/verify/verifier.ax` and all downstream IRs see 100% homogeneous instruction operand types.

## Acceptance
- [ ] `tests/typeck/int128/*.ax` verifies `i128`/`u128` literals, boundary range errors (`-170141183460469231731687303715884105729i128`), `as` casts, and mixed-width integer expression typing.
- [ ] `tests/mir/int128/*.ax` (`inspect --emit=mir`) verifies `SatAdd`/`SatSub`/`SatMul` rvalues and confirms that mixed-width integer expressions (`REQ-OWNER-007` Pattern D) emit explicit `MIR_RVALUE_CAST` temporaries with homogeneous binary operands.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T451` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T451-report.md` with exact `## Files changed`.

## Out of scope
- MIR interpreter 128-bit execution (`T452`), x86-64 native 128-bit codegen (`T453`), and floating-point promotions (`T457`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T451/build` and `python tools/axtest.py --compiler build-snap-T451/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-03 09:58:12 started (attempt 1) T451-impl
- 2026-11-03 22:51:47 requeue: restart (not charged: attempt refunded)
- 2026-11-03 22:52:04 started (attempt 1) T451-impl
