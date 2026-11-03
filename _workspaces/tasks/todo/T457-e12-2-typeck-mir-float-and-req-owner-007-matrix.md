---
id: T457
title: E12.2 — Frontend, typeck & MIR lowering for f32/f64 and REQ-OWNER-007 mixed-type promotion matrix
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T456, T451]
priority: 147
status: todo
attempts: 0
paths: [compiler/lex, compiler/syntax, compiler/hir, compiler/types, compiler/mir, tests/typeck/float, tests/mir/float_mixed]
locks: [compiler/verify/verifier.ax, compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-04-core-extensibility.md, spec/requirements/OWNER.md, tasks/0331, tasks/0338, tasks/0345]
covers: [REQ-OWNER-007, REQ-SIMD-174, REQ-SIMD-175, REQ-SIMD-270]
---
# T457 — E12.2 — Frontend, typeck & MIR lowering for f32/f64 and REQ-OWNER-007 mixed-type promotion matrix

## Goal
Enable `f32`/`f64` types and literals in `axiomc`, and implement the full `REQ-OWNER-007` Complex Mixed-Type Expression Matrix in `typeck` + HIR->MIR lowering so every implicit integer/float literal unification and variable widening promotion is lowered to an explicit `MIR_RVALUE_CAST` temporary before homogeneous MIR instructions.

## Scope
- Enable `TypeKind.Float` (`f32`, `f64`), `Infer.FloatVar` (defaulting unconstrained float literals to `f64`), `ConstValue.Float`, float literal patterns (`SPEC-04 AXS-EXT-034`), and `MirCastKind.IntToFloat`, `FloatToInt`, `FloatConvert` (`SPEC-04 AXS-EXT-042`) in `compiler/` (removing the `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` rejection on floats in `axiomc`).
- Implement the complete **`REQ-OWNER-007` Complex Mixed-Type Expression Matrix** in `compiler/types/typeck.ax` and `compiler/mir/builder.ax`: resolve unsuffixed integer (`IntVar`) and float (`FloatVar`) literals (including `IntToFloat` literal fixing `SPEC-04 AXS-EXT-035`) and variable numeric promotions along the deterministic lattice (`i8/u8 -> i16/u16 -> i32/u32 -> i64/isize -> f32 -> f64`) across nested arithmetic (`+`, `-`, `*`, `/`, `%`, unary `-`), bitwise/shift sub-trees (`>>`, `<<`, `&`, `|`, `^`) feeding arithmetic, mixed-width array indexing (`coeff[idx + off]` promoted to `usize`), function/intrinsic arguments, and relational comparisons (`<`, `<=`, `>`, `>=`, `==`, `!=`).
- Emit every implicit variable or expression promotion in `compiler/mir/builder.ax` as an explicit `MIR_RVALUE_CAST` (`IntToInt`, `IntToFloat`, `FloatConvert`) temporary before the binary, indexing, or comparison instruction.
- Enforce in `compiler/verify/verifier.ax` that every MIR binary arithmetic, bitwise, and comparison instruction has 100% homogeneous operand types (never mixing GPR integers and XMM floats or narrow/wide widths on a single MIR instruction).

## Acceptance
- [ ] `tests/typeck/float/*.ax` verifies `f32`/`f64` typing, literal suffixes, explicit narrowing `as` requirements (`f64 -> f32`, `f64 -> i32`), and complex mixed-type expression inference (`REQ-OWNER-007` Patterns A, B, C, D).
- [ ] `tests/mir/float_mixed/*.ax` (`inspect --emit=mir` and `--verify-each`) verifies that Patterns A, B, C, and D lower every implicit promotion to explicit `MIR_RVALUE_CAST` temporaries and pass the MIR verifier with 100% homogeneous instruction operands.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T457` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T457-report.md` with exact `## Files changed`.

## Out of scope
- MIR interpreter float evaluation (`T458`) and SSE2/Win64 XMM native codegen (`T459`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T457/build` and `python tools/axtest.py --compiler build-snap-T457/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
