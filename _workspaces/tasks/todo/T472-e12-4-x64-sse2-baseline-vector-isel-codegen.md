---
id: T472
title: E12.4 — x86-64 SSE2 baseline 128-bit vector instruction selection & native lowering
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T470, T471, T466, T467]
priority: 162
status: todo
attempts: 0
paths: [compiler/target/x64/isel.ax, compiler/target/x64/frame.ax, tests/run/simd/sse2_native, tests/selfhost]
locks: [compiler/target/x64/mod.ax, tests/std/simd, tests/std/tensor_matrix, tests/selfhost]
spec: [spec/SPEC-43-simd-backend.md, 0095, 0179, tasks/0403, tasks/0407]
covers: [REQ-SIMD-058, REQ-SIMD-059, REQ-SIMD-060, REQ-SIMD-061, REQ-SIMD-062, REQ-SIMD-063, REQ-SIMD-068, REQ-SIMD-069, REQ-SIMD-070, REQ-SIMD-071, REQ-SIMD-072, REQ-SIMD-073, REQ-SIMD-074, REQ-SIMD-075, REQ-SIMD-076, REQ-SIMD-077, REQ-SIMD-080, REQ-SIMD-081, REQ-SIMD-082, REQ-SIMD-083, REQ-SIMD-084]
---
# T472 — E12.4 — x86-64 SSE2 baseline 128-bit vector instruction selection & native lowering

## Goal
Implement x86-64 SSE2 baseline instruction selection in `compiler/target/x64/isel.ax` for all portable `Vector<T, N>` and `Mask<N>` operations so `std.simd`, `TensorView`, and `MatrixView` execute natively on every `x86_64-windows` CPU.

## Scope
- Implement SSE2 instruction selection in `compiler/target/x64/isel.ax` for 128-bit `Vec128` and `Mask` operations: aligned/unaligned loads and stores (`MOVDQA`/`MOVDQU`, `MOVAPS`/`MOVUPS`, `MOVAPD`/`MOVUPD`), packed integer wrapping & checked arithmetic (`PADDB/W/D/Q`, `PSUBB/W/D/Q`, `PMULLW`, `PMULUDQ`), hardware saturating arithmetic (`PADDSB/W`, `PADDUSB/W`, `PSUBSB/W`, `PSUBUSB/W` plus software saturation for 32/64-bit lanes), and packed IEEE-754 float ops (`ADDPS`/`ADDPD`, `SUBPS`/`SUBPD`, `MULPS`/`MULPD`, `DIVPS`/`DIVPD`, `SQRTPS`/`SQRTPD`, `MINPS`/`MINPD`, `MAXPS`/`MAXPD`).
- Implement SSE2 bitwise ops (`PAND`, `POR`, `PXOR`, `PANDN`), lane shifts (`PSLLW/D/Q`, `PSRLW/D/Q`, `PSRAW/D`), lane comparisons (`PCMPEQB/W/D`, `PCMPGTB/W/D` with sign-bias for unsigned & 64-bit lanes, `CMPPS`/`CMPPD`), mask extraction (`PMOVMSKB`, `MOVMSKPS`, `MOVMSKPD`), mask `select` (`(a & mask) | (b & ~mask)`), broadcast/extract/insert/shuffle (`PSHUFD`, `PSHUFLW`, `PSHUFHW`, `SHUFPS`, `SHUFPD`, `PUNPCKL*`/`PUNPCKH*`, `PINSRW`, `PEXTRW`), and horizontal reductions.
- Remove any `native-after: T472` markers from `tests/std/simd/` and `tests/std/tensor_matrix/` so all portable SIMD tests run natively with `WEAK-NATIVE 0`.

## Acceptance
- [ ] `tests/run/simd/sse2_native/*.ax`, `tests/std/simd/*.ax`, and `tests/std/tensor_matrix/*.ax` pass in both `--interp` and native x86-64 execution (`WEAK-NATIVE 0`).
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T472` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T472-report.md` with exact `## Files changed`.

## Out of scope
- SSE4.1/AVX2/FMA 256-bit `YMM` instruction selection and `std.arch.x86_64` intrinsics (`T473`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T472/build` and `python tools/axtest.py --compiler build-snap-T472/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
