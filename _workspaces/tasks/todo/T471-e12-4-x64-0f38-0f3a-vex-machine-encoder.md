---
id: T471
title: E12.4 — x86-64 0F38/0F3A opcode maps & 2-byte/3-byte VEX machine encoder
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T470]
priority: 161
status: todo
attempts: 0
paths: [compiler/target/x64/encode.ax, tests/encode/simd_vex, tests/selfhost]
locks: [compiler/target/x64/mod.ax, tests/selfhost]
spec: [spec/SPEC-43-simd-backend.md, spec/SPEC-04-core-extensibility.md, 0179, tasks/0403]
covers: [REQ-SIMD-064, REQ-SIMD-065, REQ-SIMD-066, REQ-SIMD-067, REQ-SIMD-213, REQ-SIMD-214, REQ-SIMD-215, REQ-SIMD-216]
---
# T471 — E12.4 — x86-64 0F38/0F3A opcode maps & 2-byte/3-byte VEX machine encoder

## Goal
Extend the x86-64 machine encoder (`compiler/target/x64/encode.ax`) with `0F 38` and `0F 3A` escape opcode maps, 2-byte (`C5`) and 3-byte (`C4`) `VEX` prefix encoding (`AXS-EXT-053`), `VZEROUPPER`, and non-temporal/prefetch instructions.

## Scope
- Add `0F 38` and `0F 3A` opcode map support (with mandatory `66`/`F2`/`F3` prefixes and `REX.W`/`REX.R`/`REX.X`/`REX.B` handling) in `compiler/target/x64/encode.ax` for SSE4.1/SSSE3 instructions (`PMULLD`, `PBLENDVB`, `BLENDVPS`, `BLENDVPD`, `PINSRB/D/Q`, `PEXTRB/D/Q`, `PSHUFB`, `PMOVSX*`, `PMOVZX*`, `PTEST`, `ROUNDPS`/`ROUNDPD`).
- Implement 2-byte (`C5`) and 3-byte (`C4`) `VEX` prefix emission (`~R`, `~X`, `~B`, `W`, `mmmm`, `L` 128/256-bit vector length, `pp`, `~vvvv` 3/4-operand register encoding, plus immediate byte `is4` for `VBLENDVPS`/`VPBLENDVB`/`VGATHER*`) in `compiler/target/x64/encode.ax`, automatically selecting the shortest legal 2-byte `C5` form when `X=1`, `B=1`, `W=0`, and `mmmm=01`.
- Encode `VZEROUPPER` (`C5 F8 77`), non-temporal stores (`MOVNTDQ`, `MOVNTPS`, `MOVNTPD`, `VMOVNTDQ`, `VMOVNTPS`, `VMOVNTPD`), `SFENCE`, and `PREFETCHT0`/`PREFETCHT1`/`PREFETCHT2`/`PREFETCHNTA`.

## Acceptance
- [ ] `tests/encode/simd_vex/*.ax` verifies byte-exact encoding against GNU-as reference byte vectors across `XMM0`–`XMM15` and `YMM0`–`YMM15` for `0F`, `0F 38`, `0F 3A`, 2-byte `C5` VEX, 3-byte `C4` VEX, FMA3 (`VFMADD213PS/PD`), `VZEROUPPER`, and non-temporal/prefetch instructions.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T471` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T471-report.md` with exact `## Files changed`.

## Out of scope
- SSE2 and AVX2 instruction selection (`T472`–`T473`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T471/build` and `python tools/axtest.py --compiler build-snap-T471/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
