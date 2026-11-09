---
id: T480
title: E12.2 IEEE-754 f16 scalar lattice, bf16 storage/SIMD model & SSE2/F16C lowering
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T457, T459]
priority: 149
status: todo
attempts: 0
paths: [compiler/types, compiler/mir, compiler/target/x64, std/num, tests/run/float16]
locks: [compiler/verify/verifier.ax, compiler/diag/codes/TYPE.def]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-42-simd.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-SIMD-108, REQ-SIMD-109, REQ-SIMD-110]
---
# T480 — E12.2 IEEE-754 f16 scalar lattice, bf16 storage/SIMD model & SSE2/F16C lowering

## Goal
Implement IEEE-754 half-precision `f16` in the type promotion lattice and runtime lowering, and provide `bf16` as an explicit storage and SIMD dot-product type without scalar arithmetic operators.

## Scope
- Integrate `f16` into `compiler/types/typeck.ax` promotion lattice (`I < f16 < f32 < f64`): implicit widening `f16 -> f32 -> f64`, explicit narrowing `x as f16`.
- Lower `f16` scalar arithmetic in `compiler/mir/builder.ax` and `compiler/target/x64`: on x86-64 without native FP16 execution units, promote `f16` to `f32` (using `F16C` `vcvtph2ps` when available or bit-exact software emulation), perform single-precision SSE2 scalar math, and convert back (`vcvtps2ph`).
- Introduce `bf16` in `std/num/bf16.ax` as an opaque 16-bit storage and conversion type (`to_f32()`, `from_f32()`, `to_bits()`, `from_bits()`) and SIMD dot-product primitive (`std.simd.dot_bf16`).
- Prohibit scalar binary arithmetic operators (`+`, `-`, `*`, `/`) on `bf16` in `typeck.ax`, reporting diagnostic `AX_TYPE_BF16_NO_ARITHMETIC` to maintain lattice invariants and prevent ill-defined mixed `f16`/`bf16` operations.
- Enforce vector legalizer boundary in `compiler/target/x64`: keep full AVX-512 EVEX vector registers out of P12, legalizing 512-bit vector types to paired 256-bit operations.

## Acceptance
- [ ] `tests/run/float16/f16_lattice.ax` verifies IEEE-754 `f16` precision, subnormals, infinities, NaNs, and promotion lattice widening.
- [ ] `tests/run/float16/bf16_storage.ax` verifies `bf16` bitwise roundtrips to/from `f32`, rejection of scalar math (`//~ ERROR AX_TYPE_BF16_NO_ARITHMETIC`), and SIMD dot-product calculation.
- [ ] Full suite passes in `build-snap-T480` under `axiomc2.exe`.
- [ ] Report `_workspaces/reports/T480-report.md` with exact `## Files changed`.

## Out of scope
- Full AVX-512 EVEX register allocation in P12 (deferred).
- GPU-specific half-precision execution (covered in P22 E22.8).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`), ADR-0039.
- Uses canonical Axiom syntax (`=` for bindings, `.` for paths).

## Log
- 2026-11-09 created for ADR-0039 P12 numeric refinement
