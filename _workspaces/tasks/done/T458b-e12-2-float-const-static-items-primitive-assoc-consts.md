---
id: T458b
title: E12.2 — Float const and static items, f32./f64. path heads & inherent associated constants on primitive types
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T458, T459, T501]
priority: 149
status: done
attempts: 1
paths: [compiler/types, compiler/interp_opt, compiler/resolve, tests/run/float_const, tests/ui/float_const]
locks: [compiler/hir, compiler/mir, compiler/interp, compiler/opt/const_fold.ax, compiler/lir/builder.ax, compiler/backend/session.ax, compiler/driver/pipeline.ax, compiler/diag/code.ax]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-04-core-extensibility.md, spec/decisions/ADR-0049-float-intrinsics-minimal-set.md]
covers: [REQ-OWNER-007]
started: 2026-11-25 13:07:08
finished: 2026-11-25 14:51:13
---
# T458b — E12.2 — Float const/static items, `f32.`/`f64.` path heads & primitive associated constants

## Goal
Everything SPEC-41 AXS-FLT-003 §4, AXS-FLT-004 and AXS-FLT-010 §3 needs from the compiler so that T460/T461 can be plain library code:
float constants, constant tables, and `f64.NAME` / `f64.f(...)`.

## Scope
- `is_valid_const_type` (typeck) and `session_is_valid_const_type` (interp_opt) accept `f32`/`f64`, alone and inside arrays, tuples,
  structs and enums. The initializer is evaluated with the oracle's strict soft-float (T458); `1.0 / 0.0`, `0.0 / 0.0` and `-0.0`
  are valid constants (no `AX_CONST_OVERFLOW` / `AX_CONST_DIV_ZERO`); casts and REQ-OWNER-007 promotions work in initializers.
- Reads of float constants, constant tables (`const T: [N]f64` indexed at run time) and float `static` / `static mut` /
  `@thread_local static` items (scalar and aggregate) give the same bits in the oracle and natively (`.rdata` / `.data` / `.bss`);
  `-0.0` is never placed as zero-fill or materialised with `XORPS`.
- A float constant is not a const-generic argument, an array length or an integer pattern; diagnostics stay the existing ones.
- Resolver and typeck accept `f32` and `f64` as path heads exactly like the integer names: `f64.from_x(...)` (inherent or trait
  function) and `f64.NAME` (today `AX_NAME_UNRESOLVED`).
- Inherent associated constants on primitive types (`impl f64 { pub const EPSILON: f64 = …; }`, read as `f64.EPSILON`, also for the
  integer types, where today `AX_TYPE_UNKNOWN_FIELD`). Built-in integer `MIN`/`MAX`/`BITS` keep working.

## Acceptance
- [ ] `tests/run/float_const/*.ax` pass in interp and native (`-O0`, `-O1`; `WEAK-NATIVE 0`): scalar consts with exact bits (±0, inf,
      NaN-ness, subnormal, f32 direct rounding), expression initializers with REQ-OWNER-007 promotion, const arrays/structs/tuples
      indexed at run time, float statics of every storage class, constants as operands and arguments, `f32.`/`f64.` static calls,
      trait static dispatch on `f64`, associated constants on `f64`, `f32` and one integer type.
- [ ] `tests/ui/float_const/*.ax`: `const X: f32 = 1` style mismatches, a float as array length, an unknown `f64.NOPE`, and a
      non-constant call in an initializer report the existing codes.
- [ ] `grep -rn "AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP" tests` has no test that still expects it for a float const.
- [ ] `tests/selfhost/bundles_current.test` passes in the snapshot; fixed point holds; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T458b-report.md` with exact `## Files changed`.

## Out of scope
- The constants themselves (`f64.EPSILON`, … are written in `std/core/float.ax` by T460); intrinsics (T458a); `f16` (T480).

## Notes
- The read side of bit checks may use the pointer pun of the T458 tests (or the T458a intrinsics if already accepted).
- T458 already accepts `CONST_FLOAT` results in `compiler/interp_opt/session.ax` and `interp_eval_const_expr_into`.
- If T458's `const_fold` guard (`opt_is_scalar_const_op`) sees a float const through a new operand kind, extend it: float bits are
  never folded as integers.

## Log
- 2026-11-24 created by architect (unblock T458, ADR-0049)
- 2026-11-25 11:49:11 started (attempt 1) axiom-semantics
- 2026-11-25 13:07:02 requeue:  (not charged: attempt refunded)
- 2026-11-25 13:07:08 started (attempt 1) T458b-impl
- 2026-11-25 14:51:13 accepted by QA -> done
