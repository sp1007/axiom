---
id: T066
title: E16.9 Linux x86-64: SysV ABI, ELF64 writer, static ELF linker
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T216, T313, T650]
priority: 93
status: todo
attempts: 0
paths: [compiler/abi/sysv64, compiler/obj/elf, compiler/link/elf, tests/run/linux, tests/selfhost/abi, tests/selfhost/obj, tests/selfhost/link]
spec: [spec/SPEC-80-linux-x86-64-elf-static.md, 0192, 0053, 0255, 0256]
covers: [REQ-TGT-041, REQ-TGT-042, REQ-TGT-043, REQ-TGT-059, REQ-TGT-060, REQ-TGT-101, REQ-TGT-103, REQ-TGT-104]
---
# T066 — Linux x86-64: SysV ABI, ELF64 writer, static ELF linker

## Goal
Implement the `x86_64-linux` System V AMD64 ABI pass, ELF64 relocatable object writer (`ET_REL`), and static ELF64 executable linker (`ET_EXEC`) so `axiomc` produces static Linux x86-64 binaries directly without external assemblers or linkers.

## Scope
- Implement `CallConv.SysV64` argument/return classification (`RDI, RSI, RDX, RCX, R8, R9`, `XMM0..XMM7`, eightbyte `INTEGER`/`SSE`/`MEMORY` aggregate classification, `sret` in `RDI`, dual-register 16-byte returns in `RAX:RDX`/`XMM0:XMM1`, callee-saved `RBX, RBP, R12..R15`, 16-byte stack alignment before `call`, and red-zone control) in `compiler/abi/sysv64`.
- Implement the deterministic ELF64 relocatable object writer (`ET_REL`, `.text`, `.rodata`, `.data`, `.bss`, `.symtab`, `.strtab`, `.shstrtab`, `.rela.text`, `.rela.data`, `R_X86_64_64`, `R_X86_64_PC32`, `R_X86_64_PLT32`, `R_X86_64_32`, `R_X86_64_32S`, and `SHN_ABS` for `@at` symbols) in `compiler/obj/elf`.
- Implement the static ELF64 executable linker (`ET_EXEC`, 4 KiB page-aligned `PT_LOAD` RX/R/RW segments at `0x400000`, relocation resolution, and `_start` → `main` → `SYS_exit_group` syscall stub) in `compiler/link/elf`.
- Add unit and selfhost tests in `tests/run/linux`, `tests/selfhost/abi`, `tests/selfhost/obj`, and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc build --target x86_64-linux --emit=obj` and `axiomc build --target x86_64-linux` emit deterministic ELF64 `ET_REL` and `ET_EXEC` binaries validated by `readelf`/`objdump` (and executed under `wsl` when available).
- [ ] Positive and negative tests in `tests/run/linux`, `tests/selfhost/abi`, `tests/selfhost/obj`, and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T066-report.md` with exact `## Files changed`.

## Out of scope
- Full `std.sys.linux` host-interface syscalls and WSL test runner integration (`T651`).
- Dynamic ELF (`PIE`, `GOT`/`PLT`, `.so`), which is implemented in `E16.2` (`T658`–`T659`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Roadmap epic E16.9 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; refined by T216 to depend on `T313` and `T650` (`SPEC-80`).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-11-03 08:35:00 refined by T216 (added T313, T650 depends, narrow paths, covers)
