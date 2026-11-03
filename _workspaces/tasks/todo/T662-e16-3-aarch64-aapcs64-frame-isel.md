---
id: T662
title: E16.3 — AArch64 TargetDesc, AAPCS64 ABI lowering, STP/LDP frame layout & instruction selection
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T654, T655, T661]
priority: 105
status: todo
attempts: 0
paths: [compiler/target/aarch64/isel, compiler/abi/aapcs64, tests/mc/aarch64_isel, tests/selfhost/abi, tests/selfhost/isel]
spec: [spec/SPEC-83-aarch64-linux.md, 0193, tasks/0521, tasks/0784]
covers: [REQ-TGT-123, REQ-TGT-125, REQ-TGT-126, REQ-TGT-127, REQ-TGT-128, REQ-TGT-129, REQ-TGT-130, REQ-TGT-131, REQ-TGT-132, REQ-TGT-133, REQ-TGT-135, REQ-TGT-136, REQ-TGT-137, REQ-TGT-138, REQ-TGT-139, REQ-TGT-140, REQ-TGT-141, REQ-TGT-142, REQ-TGT-143, REQ-TGT-144]
---
# T662 — E16.3 — AArch64 TargetDesc, AAPCS64 ABI lowering, STP/LDP frame layout & instruction selection

## Goal
Implement the AArch64 `TargetDesc` & `IsaTable`, `CallConv.Aapcs64` ABI classification and lowering, 16-byte aligned `STP`/`LDP` frame lowering, and AArch64 instruction selection in `compiler/abi/aapcs64` and `compiler/target/aarch64/isel`.

## Scope
- Implement `CallConv.Aapcs64` in `compiler/abi/aapcs64`: `X0..X7` integer/pointer passing, `V0..V7` scalar FP and Homogeneous Floating-point/Vector Aggregate (`HFA`/`HVA`) passing, `<= 16`-byte composite passing in GPR pairs, `> 16`-byte caller-allocated composite passing by pointer, indirect result location in `X8` (`XR` / `sret`), and callee-saved `X19..X28` + `D8..D15` preservation.
- Implement AArch64 `TargetDesc`, `IsaTable`, instruction selection, and frame lowering in `compiler/target/aarch64/isel`:
  - `X/W` 64/32-bit register aliasing, `SP` vs `XZR`/`WZR` distinction, `LR` (`X30`) and `FP` (`X29`) paired `STP`/`LDP` prologue/epilogue with strict 16-byte `SP` alignment (`0193 §7–8`).
  - Integer arithmetic/bitwise/shift ops, `MOVZ`/`MOVN`/`MOVK` immediate materialization, `ADRP`+`ADD` PC-relative symbol addressing, `CMP`/`CCMP`/`CSEL` condition-code lowering, and checked overflow checks (`ADDS`/`SUBS`/`B.VS`, `SMULL`/`UMULL`).
  - IEEE-754 `f32`/`f64` scalar FP ops (`FADD`, `FSUB`, `FMUL`, `FDIV`, `FSQRT`, `FCMP`, `FCVTZS`/`FCVTZU` with NaN/saturation checks) and 128-bit NEON SIMD vector ops (`V0..V31`).
  - Acquire/release (`LDAR`/`STLR`), LL/SC (`LDXR`/`STLXR`), optional `+lse` (`CAS`/`LDADD`/`SWP`), `DMB ISH` fences, and non-eliminable volatile/MMIO loads and stores.
- Add unit and selfhost tests in `tests/mc/aarch64_isel`, `tests/selfhost/abi`, and `tests/selfhost/isel`.

## Acceptance
- [ ] AArch64 instruction selection and `CallConv.Aapcs64` pass `compiler/backend/verify_mc` across scalar, aggregate, FP, NEON, and atomic LIR programs.
- [ ] Positive and negative tests in `tests/mc/aarch64_isel`, `tests/selfhost/abi`, and `tests/selfhost/isel` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T662-report.md` with exact `## Files changed`.

## Out of scope
- AArch64 binary instruction encoding, ELF64 `EM_AARCH64` linking, and `std.sys.linux_aarch64` (`T663`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:38:00 created by T216 (P16 phase planning)
