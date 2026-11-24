---
id: T458a
title: E12.2 — Float intrinsics to_bits/from_bits/sqrt/abs/copysign — registration, MIR, oracle and native lowering in one task
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T458, T459, T501]
priority: 149
status: todo
attempts: 0
paths: [compiler/types, compiler/mir, tests/mir/float_intrinsics, tests/ui/float_intrinsics, tests/mir/float_interp, tests/opt/float_strict]
locks: [compiler/verify/verifier.ax, compiler/interp, compiler/opt, compiler/lir, compiler/target/x64, compiler/backend/session.ax]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-04-core-extensibility.md, spec/decisions/ADR-0049-float-intrinsics-minimal-set.md]
covers: [REQ-SIMD-106]
---
# T458a — E12.2 — Float intrinsics: registration, MIR, oracle and native lowering

## Goal
A program can declare and call the five float intrinsics of SPEC-41 AXS-FLT-026 (`to_bits`, `from_bits`, `sqrt`, `abs`, `copysign`,
each with suffix `_f32` / `_f64`) and gets the same bits from `--interp` and from native code at `-O0`, `-O1` and `-O2`.

## Scope
- `compiler/types/types.ax`: add the five entries to the intrinsic table with `f32`/`f64` suffixes and a signature form for "unsigned
  integer of the float's width" (`to_bits_f64: fn(f64) -> u64`, `to_bits_f32: fn(f32) -> u32`). A float name with an integer suffix
  (`sqrt_i32`), an integer name with a float suffix (`rotate_left_f64`) and a wrong signature stay `AX_TYPE_UNKNOWN_INTRINSIC`.
- `compiler/mir`: new cast kind `FloatBits` and unary ops `Sqrt`, `Fabs` (ADR-0049 §2), text printer and parser, lowering in
  `mb_build_intrinsic_mir_op`; `copysign` expands to bit casts and integer masks. Note the parser-local cast number 7 in
  `compiler/verify/verifier.ax` (`VERIFY_CAST_UNSIZE`): no collision.
- `compiler/verify/verifier.ax`: `FloatBits` only between same-width float and unsigned integer; `Sqrt`/`Fabs` only on floats.
- `compiler/interp`: evaluate the new ops with the existing `sf_intrinsic` kernel (T458); the name-based float dispatch in
  `eval_core_intrinsic` must not remain a second, divergent path.
- `compiler/opt`: every pass treats the new kinds as pure and non-foldable (no `sqrt` folding, no `FloatBits` round-trip folding that
  could quiet an sNaN, no integer fast path on float bits).
- `compiler/lir`, `compiler/target/x64`: `FloatBits` as `MOVD`/`MOVQ` (or the vreg move T459's representation needs), `Sqrt` to LIR
  `FSQRT`, `Fabs` to LIR `FABS`.
- Native catch-up for T458: remove `native-after: T458a` from `tests/mir/float_interp/*` and `tests/opt/float_strict/*` and fix what
  fails natively (T459's code is in `locks:`).
- Convert the cases of the five intrinsics from the helper `tests/mir/float_interp/intrinsics.ax` into run tests; the helper keeps
  only the vectors of the ten derived operations, for T460.

## Acceptance
- [ ] `tests/mir/float_intrinsics/*.ax` run tests pass in interp and native (`-O0`, `-O1`, `-O2`; `WEAK-NATIVE 0`): bit-exact results
      for the five intrinsics on `f32` and `f64` over ±0, subnormals, ±inf, qNaN with payload and sign, sNaN patterns (`to_bits`,
      `from_bits`, `abs`, `copysign` keep every bit; `sqrt` of NaN or a negative value compared NaN-tolerantly), and a mix of float
      and integer vregs under register pressure.
- [ ] `tests/ui/float_intrinsics/*.ax`: wrong suffix, wrong signature and a name of the ten derived operations (`floor_f64`, …) are
      rejected with `AX_TYPE_UNKNOWN_INTRINSIC`; `tests/mir/float_intrinsics` has a golden `--emit=mir` and a verifier reject test
      (`FloatBits` of unequal width).
- [ ] `grep -rn "native-after: T458a" tests` prints nothing; `tests/mir/float_interp` and `tests/opt/float_strict` pass natively.
- [ ] `tests/selfhost/bundles_current.test` passes in the snapshot; fixed point holds; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T458a-report.md` with exact `## Files changed`.

## Out of scope
- The ten derived operations (`std.core.float`, T460); float const/static items (T458b); `f16` (T480); SSE4.1/FMA (T473).

## Notes
- ADR-0049 `INV-FLT-INTR`: no oracle-only intrinsic. Until this task the native path compiles the declared stub body of an
  intrinsic it does not lower, which is a silent wrong result; the tests must prove native values, not exit 0.
- `bootstrap/axiom0` is frozen; compiler sources stay in the SPEC-00 §9 subset (no float use inside `compiler/`).

## Log
- 2026-11-24 created by architect (unblock T458, ADR-0049)
