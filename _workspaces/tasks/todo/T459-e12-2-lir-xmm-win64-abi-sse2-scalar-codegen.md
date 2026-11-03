---
id: T459
title: E12.2 — LIR Xmm register class, Windows x64 XMM ABI & SSE2 scalar floating-point codegen
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T457, T453]
priority: 149
status: todo
attempts: 0
paths: [compiler/lir, compiler/abi, compiler/target/x64, tests/lir/float, tests/encode/sse2_scalar, tests/abi/win64_float]
locks: [compiler/backend/session.ax, tests/selfhost]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-04-core-extensibility.md, 0162, 0179, 0181, tasks/0331, tasks/0338]
covers: [REQ-SIMD-325, REQ-SIMD-332]
---
# T459 — E12.2 — LIR Xmm register class, Windows x64 XMM ABI & SSE2 scalar floating-point codegen

## Goal
Implement the LIR `f32`/`f64` scalar types and `Xmm` register class (`AXS-EXT-050`), Windows x64 `XMM0`–`XMM3` / `XMM6`–`XMM15` ABI (`AXS-EXT-052`), and x86-64 SSE2 scalar instruction selection and encoding.

## Scope
- Activate `LirType.F32`/`F64` and `RegClass.Xmm` (`XMM0`–`XMM15`) in `compiler/lir/lir.ax` and `compiler/lir/builder.ax`, emitting `.rdata` 4-byte and 8-byte IEEE-754 float constants.
- Update `compiler/abi/win64.ax` and `compiler/target/x64/frame.ax` for the Microsoft x64 calling convention: pass floating-point arguments in positions 0..3 in `XMM0`–`XMM3` (mirroring in GPRs when calling variadic `extern "C"` functions), return scalar `f32`/`f64` in `XMM0`, and save/restore callee-saved `XMM6`–`XMM15` (16-byte aligned stack slots) in function prologues/epilogues.
- Implement SSE2 scalar instruction selection and encoding in `compiler/target/x64/isel.ax` and `compiler/target/x64/encode.ax`: `MOVSS`/`MOVSD`, `ADDSS`/`ADDSD`, `SUBSS`/`SUBSD`, `MULSS`/`MULSD`, `DIVSS`/`DIVSD`, `SQRTSS`/`SQRTSD`, `UCOMISS`/`UCOMISD` (handling `PF=1` unordered `NaN` correctly for `==`, `!=`, `<`, `<=`, `>`, `>=`), `CVTSI2SS`/`CVTSI2SD` (including two-path unsigned `u64`/`u128 -> f32/f64`), saturating `CVTTSS2SI`/`CVTTSD2SI` (`NaN -> 0`, clamp to `[MIN, MAX]`), `CVTSS2SD`/`CVTSD2SS`, `MOVD`/`MOVQ` bitcasts, and `XORPS`/`XORPD`/`ANDPS`/`ANDPD` sign-bit masks.

## Acceptance
- [ ] `tests/lir/float/*.ax` and `tests/encode/sse2_scalar/*.ax` verify LIR lowering and byte-exact x86-64 SSE2 instruction encoding against GNU-as vectors.
- [ ] `tests/abi/win64_float/*.ax` verifies mixed GPR + XMM argument passing (`fn(i32, f64, u16, f32, f64)`), `XMM0` returns, and `XMM6`–`XMM15` preservation across calls.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T459` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T459-report.md` with exact `## Files changed`.

## Out of scope
- Float string formatting/parsing (`T460`) and transcendental math functions (`T461`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T459/build` and `python tools/axtest.py --compiler build-snap-T459/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
