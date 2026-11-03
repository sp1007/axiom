---
id: T473
title: E12.4 — x86-64 SSE4.1/AVX2/FMA 256-bit vector instruction selection & std.arch.x86_64 intrinsics
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T472]
priority: 163
status: todo
attempts: 0
paths: [compiler/target/x64/isel.ax, std/arch/x86_64.ax, tests/lir/simd_avx2, tests/run/simd/avx2_native, tests/selfhost]
locks: [std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-43-simd-backend.md, 0095, tasks/0341, tasks/0344, tasks/0403, tasks/0407]
covers: [REQ-SIMD-009, REQ-SIMD-010, REQ-SIMD-093, REQ-SIMD-117, REQ-SIMD-172, REQ-SIMD-173, REQ-SIMD-255, REQ-SIMD-279]
---
# T473 — E12.4 — x86-64 SSE4.1/AVX2/FMA 256-bit vector instruction selection & std.arch.x86_64 intrinsics

## Goal
Extend `compiler/target/x64/isel.ax` with target-feature-gated SSE4.1, AVX2 (256-bit `YMM`), and FMA3 instruction selection plus `VZEROUPPER` hygiene, and provide explicit target-specific intrinsics in `std/arch/x86_64.ax`.

## Scope
- When `sse4.1` is active on the function/compilation target, select single-instruction `PMULLD`, `PCMPEQQ`, `PBLENDVB`/`BLENDVPS`/`BLENDVPD`, `PINSRB/D/Q`, `PEXTRB/D/Q`, `PMINSD/UD`, `PMAXSD/UD`, and `ROUNDPS`/`ROUNDPD` (`floor`/`ceil`/`trunc`/`round_ties_even`).
- When `avx2` (and optionally `fma`) is active, lower 256-bit `Vec256` operations to native `YMM0`–`YMM15` VEX instructions (`VMOVDQA`/`VMOVDQU`, `VMOVAPS`/`VMOVUPS`, `VPADDB/W/D/Q`, `VPSUBB/W/D/Q`, `VPMULLD`, `VADDPS`/`VADDPD`, `VMULPS`/`VMULPD`, `VFMADD213PS`/`VFMADD213PD`, `VPAND`/`VPOR`/`VPXOR`, `VPSLLVD/Q`, `VPSRLVD/Q`, `VPERMD`, `VPSHUFB`, `VPBLENDVB`, `VGATHERDPS`/`VGATHERDPD`) and emit `VZEROUPPER` before calling non-AVX functions or returning.
- Create `std/arch/x86_64.ax` exposing explicit `unsafe` architecture intrinsics (`prefetch_t0`, `prefetch_nta`, `store_nontemporal_i128`, `store_nontemporal_f32x4`, `sfence`, `lfence`, `mfence`, `pause`, and SSE2/SSE4.1/AVX2/FMA vector intrinsics, `ANUM-28, 52`, `ASIMD-26..27, 68..70`).

## Acceptance
- [ ] `tests/lir/simd_avx2/*.ax` verifies that SSE4.1, AVX2 256-bit `YMM`, FMA3, and `VZEROUPPER` instructions are selected only when the corresponding target features are enabled.
- [ ] `tests/run/simd/avx2_native/*.ax` passes under `--interp` and native x86-64 (`WEAK-NATIVE 0`), verifying `std/arch/x86_64.ax` prefetch/non-temporal/fence intrinsics and AVX2/FMA vector operations.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T473` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T473-report.md` with exact `## Files changed`.

## Out of scope
- Runtime CPUID detection and `@multiversion` dispatcher generation (`E12.5` `T475`–`T479`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T473/build` and `python tools/axtest.py --compiler build-snap-T473/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
