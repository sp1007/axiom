---
id: T679
title: E16.7 — RV64GC + RVC instruction encoder, ELF64 EM_RISCV relocations/linker & std.sys.linux_riscv64
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T651, T659, T678]
priority: 122
status: todo
attempts: 0
paths: [compiler/target/riscv64/encode, compiler/obj/elf_riscv64, compiler/link/elf_riscv64, std/sys/linux_riscv64, tests/encode/riscv64, tests/selfhost/encode, tests/selfhost/obj, tests/selfhost/link]
spec: [spec/SPEC-87-riscv64-linux.md, 0152, tasks/0522, tasks/0784]
covers: [REQ-TGT-185, REQ-TGT-186, REQ-TGT-189, REQ-TGT-192, REQ-TGT-193, REQ-TGT-194, REQ-TGT-195, REQ-TGT-196]
---
# T679 — E16.7 — RV64GC + RVC instruction encoder, ELF64 EM_RISCV relocations/linker & std.sys.linux_riscv64

## Goal
Implement the RV64GC + RVC (16-bit compressed) instruction encoder, ELF64 `EM_RISCV` object writer and static/dynamic linker, and `std/sys/linux_riscv64` syscall backend for `--target riscv64-linux`.

## Scope
- Implement the RV64I/M/A/F/D + C instruction encoder in `compiler/target/riscv64/encode`:
  - Expand pseudo-instructions (`LI`, `LA`, `MV`, `NEG`, `RET`, `CALL`, `TAIL`) before final encoding (`ABACKEND-46`).
  - Encode 32-bit `R`/`I`/`S`/`B`/`U`/`J`/`R4` formats and opportunistic 16-bit `RVC` compressed instructions (`C.LWSP`, `C.LDSP`, `C.SWSP`, `C.SDSP`, `C.LI`, `C.LUI`, `C.ADDI`, `C.ADDI16SP`, `C.MV`, `C.ADD`, `C.J`, `C.JR`, `C.JALR`, `C.BEQZ`, `C.BNEZ`, `ABACKEND-43`), plus branch relaxation when `B`-type offsets exceed ±4 KiB.
- Implement ELF64 `EM_RISCV` (`243`, `e_flags = EF_RISCV_RVC | EF_RISCV_FLOAT_ABI_DOUBLE`) object emission in `compiler/obj/elf_riscv64` and static/dynamic linking in `compiler/link/elf_riscv64`:
  - Emit and resolve `R_RISCV_64`, `R_RISCV_32`, `R_RISCV_BRANCH`, `R_RISCV_JAL`, `R_RISCV_RVC_BRANCH`, `R_RISCV_RVC_JUMP`, `R_RISCV_CALL_PLT`, `R_RISCV_GOT_HI20`, and paired `R_RISCV_PCREL_HI20` + `R_RISCV_PCREL_LO12_I`/`R_RISCV_PCREL_LO12_S` (correctly resolving the `LO12` relocation through the symbol of its partner `AUIPC` instruction without requiring optional linker relaxation, `ABACKEND-47`).
- Implement `std/sys/linux_riscv64` (`ecall` with Linux generic syscall numbers in `a7`, args in `a0..a5`, result in `a0`, and `_start` stub).
- Add encoding, object, and linker tests in `tests/encode/riscv64`, `tests/selfhost/encode`, `tests/selfhost/obj`, and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc build --target riscv64-linux` emits deterministic ELF64 `EM_RISCV` objects, static executables, `.a` archives, and `.so` shared libraries whose instruction encodings and `PCREL_HI20`/`LO12` relocations validate cleanly.
- [ ] Positive and negative tests in `tests/encode/riscv64`, `tests/selfhost/encode`, `tests/selfhost/obj`, and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T679-report.md` with exact `## Files changed`.

## Out of scope
- Full RISC-V 64 conformance suite (`T680`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:42:00 created by T216 (P16 phase planning)
