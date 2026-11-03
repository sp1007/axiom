---
id: T658
title: E16.2 — PIC/PIE codegen, GOT/PLT lowering, ELF dynamic sections (.dynsym/.gnu.hash/.dynamic) & RELRO
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T066, T313, T655, T657]
priority: 101
status: todo
attempts: 0
paths: [compiler/target/x64/pic, compiler/obj/elf_dyn, tests/obj/elf_dyn, tests/selfhost/encode, tests/selfhost/obj]
spec: [spec/SPEC-82-linux-elf-dynamic.md, 0192, 0197, tasks/0563]
covers: [REQ-TGT-066, REQ-TGT-067, REQ-TGT-068, REQ-TGT-145, REQ-TGT-146]
---
# T658 — E16.2 — PIC/PIE codegen, GOT/PLT lowering, ELF dynamic sections (.dynsym/.gnu.hash/.dynamic) & RELRO

## Goal
Implement position-independent (`PIC`/`PIE`) x86-64 code generation, `GOT`/`PLT` relocation lowering, and ELF64 dynamic section builders (`.dynsym`, `.dynstr`, `.gnu.hash`, `.dynamic`, `.got`, `.got.plt`, `.plt`, `.rela.dyn`, `.rela.plt`, `PT_GNU_RELRO`) in `compiler/target/x64/pic` and `compiler/obj/elf_dyn`.

## Scope
- Implement x86-64 PIC/PIE codegen in `compiler/target/x64/pic`: `RIP`-relative addressing for local symbols, `R_X86_64_GOTPCREL` indirect loads through `.got` for external/preemptible symbols and function addresses (`AMACHINE-79`), `R_X86_64_PLT32` direct calls to external functions, and ELF TLS access lowering (`Initial-Exec` `R_X86_64_GOTTPOFF` and `General-Dynamic` `R_X86_64_TLSGD`).
- Implement ELF64 dynamic table and section synthesis in `compiler/obj/elf_dyn`: `.dynsym` and `.dynstr` symbol/string tables, bloom-filter `.gnu.hash` lookup table, `.got` and `.got.plt` global offset tables, 16-byte `.plt` trampolines (`jmp [rip + disp32]`; `push reloc_index`; `jmp .plt[0]`), `.rela.dyn` (`R_X86_64_RELATIVE`, `R_X86_64_GLOB_DAT`, `R_X86_64_64`) and `.rela.plt` (`R_X86_64_JUMP_SLOT`), `.dynamic` tag array, and `PT_GNU_RELRO` + `PT_GNU_STACK` program header metadata.
- Add unit and selfhost tests in `tests/obj/elf_dyn`, `tests/selfhost/encode`, and `tests/selfhost/obj`.

## Acceptance
- [ ] `compiler/obj/elf_dyn` emits valid `.dynsym`, `.gnu.hash`, `.dynamic`, `.got`/`.plt`, and `.rela.dyn`/`.rela.plt` tables verified by `readelf -d -r -s` / structural assertions.
- [ ] Positive and negative tests in `tests/obj/elf_dyn`, `tests/selfhost/encode`, and `tests/selfhost/obj` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T658-report.md` with exact `## Files changed`.

## Out of scope
- Full `ET_DYN` PIE/shared-object linking and `libc`/`dlopen` runtime integration (`T659`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:37:00 created by T216 (P16 phase planning)
