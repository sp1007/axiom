---
id: T678
title: E16.7 — RISC-V 64 (RV64GC) TargetDesc, LP64D psABI lowering & flagless instruction selection
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T654, T655, T677]
priority: 121
status: todo
attempts: 0
paths: [compiler/target/riscv64/isel, compiler/abi/riscv64, tests/mc/riscv64_isel, tests/selfhost/abi, tests/selfhost/isel]
spec: [spec/SPEC-87-riscv64-linux.md, 0152, tasks/0522, tasks/0784]
covers: [REQ-TGT-176, REQ-TGT-177, REQ-TGT-178, REQ-TGT-179, REQ-TGT-180, REQ-TGT-181, REQ-TGT-187, REQ-TGT-188, REQ-TGT-190, REQ-TGT-191]
---
# T678 — E16.7 — RISC-V 64 (RV64GC) TargetDesc, LP64D psABI lowering & flagless instruction selection

## Goal
Implement the `riscv64-linux` (`RV64GC`) `TargetDesc`, `CallConv.RiscV` (`LP64D`) ABI pass, and flagless RV64GC instruction selection in `compiler/abi/riscv64` and `compiler/target/riscv64/isel`.

## Scope
- Implement `CallConv.RiscV` (`LP64D`) in `compiler/abi/riscv64`:
  - `a0..a7` integer/pointer and `fa0..fa7` floating-point parameter/return registers, hardware FP struct flattening (`{f32/f64}`, `{f32/f64, f32/f64}`, `{int, f32/f64}`), `<= 16`-byte composite passing in up to 2 GPRs, `> 16`-byte composite passing by reference (caller-allocated copy), sign-extension of both `i32` and `u32` values to 64 bits at ABI boundaries, and callee-saved `s0..s11` + `fs0..fs11` preservation.
- Implement `riscv64-linux` `TargetDesc`, `IsaTable`, frame lowering, and instruction selection in `compiler/target/riscv64/isel`:
  - Reserve `x0` (`zero`), `x2` (`sp`), `x3` (`gp`), and `x4` (`tp`) from general allocation (`ABACKEND-45`).
  - Lower flagless comparisons (`SLT`, `SLTU`, `SLTI`, `SLTIU`, `XOR`+`SEQZ`/`SNEZ`) and fuse conditional branches directly into `BEQ`/`BNE`/`BLT`/`BGE`/`BLTU`/`BGEU` (`ABACKEND-22..23`).
  - Expand checked signed/unsigned `add`/`sub`/`mul`/`div`/`shl` overflow checks without a flags register (`ADD` + sign-bit/carry comparison, `MUL` + `MULH`/`MULHU` high-half verification), use 32-bit word instructions (`ADDW`, `SUBW`, `MULW`, `DIVW`, `SLLW`, `SRLW`, `SRAW`) for 32-bit operations, and lower `F`/`D` IEEE-754 floating-point and `A` extension (`LR.W`/`SC.W`, `LR.D`/`SC.D`, `AMOSWAP`, `AMOADD`, `FENCE rw, rw`) atomics.
- Add unit and selfhost tests in `tests/mc/riscv64_isel`, `tests/selfhost/abi`, and `tests/selfhost/isel`.

## Acceptance
- [ ] `compiler/target/riscv64/isel` and `compiler/abi/riscv64` pass `compiler/backend/verify_mc` across scalar, checked-overflow, aggregate, FP, and atomic LIR programs without using any flags register.
- [ ] Positive and negative tests in `tests/mc/riscv64_isel`, `tests/selfhost/abi`, and `tests/selfhost/isel` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T678-report.md` with exact `## Files changed`.

## Out of scope
- RV64GC + RVC binary encoding, ELF64 `EM_RISCV` linking, and `std.sys.linux_riscv64` (`T679`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:42:00 created by T216 (P16 phase planning)
