---
id: T470
title: E12.4 — LIR vector types (v128/v256), legalizer splitting/scalarization & Windows x64 vector ABI
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T469, T464, T459]
priority: 160
status: todo
attempts: 0
paths: [compiler/lir, compiler/abi, tests/lir/simd, tests/abi/win64_simd]
locks: [compiler/backend/session.ax, tests/selfhost]
spec: [spec/SPEC-43-simd-backend.md, spec/SPEC-04-core-extensibility.md, 0162, 0181, tasks/0403, tasks/0407]
covers: [REQ-SIMD-014, REQ-SIMD-015, REQ-SIMD-040, REQ-SIMD-157, REQ-SIMD-169, REQ-SIMD-170, REQ-SIMD-208, REQ-SIMD-209, REQ-SIMD-210, REQ-SIMD-244, REQ-SIMD-319]
---
# T470 — E12.4 — LIR vector types (v128/v256), legalizer splitting/scalarization & Windows x64 vector ABI

## Goal
Implement LIR vector types (`v128`, `v256`, `v512`) and register classes (`Vec128`, `Vec256`, `Vec512`, `Mask`), MIR->LIR vector legalizer (multi-register splitting and scalar fallback), and Windows x64 vector ABI lowering.

## Scope
- Add `LirType.V128`, `V256`, `V512` and `RegClass.Vec128`, `Vec256`, `Vec512`, `Mask` in `compiler/lir/lir.ax`, plus LIR instructions for vector arithmetic, bitwise, shift, compare, blend/select, splat, extract, insert, shuffle, horizontal reduction, masked load/store, gather/scatter, prefetch, and `nontemporal` load/store flags (`SPEC-04 AXS-EXT-050/051`).
- Implement the vector legalizer in `compiler/lir/builder.ax`: lower 128-bit vectors directly to `Vec128`, split 256-bit and 512-bit vectors into `Vec128` pairs/quads when target feature `avx2` is not active (or keep `Vec256` when `avx2` is active), widen sub-128-bit vectors (`i32x2`, `i16x4`, `u8x8`) into defined low lanes of `Vec128`, and scalarize operations without direct hardware instructions (such as integer vector `/`, `%`, and checked overflow traps where needed).
- Update `compiler/abi/win64.ax` to pass and return `Vector<T, N>` and `Mask<N>` according to `SPEC-43` (16-byte aligned stack/pointer passing or XMM registers as specified, preserving 16/32-byte alignment on stack slots).

## Acceptance
- [ ] `tests/lir/simd/*.ax` (`inspect --emit=lir`) verifies LIR vector lowering, `v256 -> 2x v128` splitting on baseline SSE2, and `v256` preservation when `avx2` is enabled.
- [ ] `tests/abi/win64_simd/*.ax` verifies Windows x64 vector argument/return ABI lowering and stack slot alignment.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T470` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T470-report.md` with exact `## Files changed`.

## Out of scope
- x86-64 VEX machine encoding (`T471`) and SSE2/AVX2 instruction selection (`T472`–`T473`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T470/build` and `python tools/axtest.py --compiler build-snap-T470/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
