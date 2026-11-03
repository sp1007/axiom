---
id: T650
title: E16.9 — Canonical Linux x86-64 SysV ABI, ELF64 object & static ELF executable specification (SPEC-80)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T313]
priority: 92
status: todo
attempts: 0
paths: [spec/SPEC-80-linux-x86-64-elf-static.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0053, 0163, 0164, 0192, 0217, 0255, 0256, tasks/0369, tasks/0563]
covers: [REQ-TGT-002, REQ-TGT-003, REQ-TGT-037, REQ-TGT-038, REQ-TGT-039, REQ-TGT-040]
---
# T650 — E16.9 — Canonical Linux x86-64 SysV ABI, ELF64 object & static ELF executable specification (SPEC-80)

## Goal
Consolidate the canonical specification for Axiom's second native target (`x86_64-linux`), covering the System V AMD64 ABI (`CallConv.SysV64`), ELF64 relocatable object format (`ET_REL`), GNU `ar` archives, static ELF64 executable linking (`ET_EXEC`), `_start` startup/syscall contract, and `std.sys.linux` raw syscall host interface into `spec/SPEC-80-linux-x86-64-elf-static.md` (`AXS-ELFS-*` rule IDs).

## Scope
- Write `spec/SPEC-80-linux-x86-64-elf-static.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ELFS-NNN` rules.
- Specify the `x86_64-linux` `TargetDesc` record (`CallConv.SysV64`, `ObjectFormat.Elf`, `ArchiveFormat.GnuAr`, `ImageFormat.ElfExec`, 64-bit little-endian, 16-byte stack alignment before `call`, 128-byte leaf red zone disabled under `-mno-red-zone` / kernel/freestanding profiles).
- Specify the System V AMD64 calling convention (`0192 §4–9`): integer/pointer arguments in `RDI, RSI, RDX, RCX, R8, R9`, floating-point/vector arguments in `XMM0..XMM7`, eightbyte aggregate classification (`INTEGER`, `SSE`, `MEMORY`), hidden `sret` pointer in `RDI` returned in `RAX`, dual-register 16-byte returns in `RAX:RDX` / `XMM0:XMM1`, and callee-saved registers `RBX, RBP, R12..R15`.
- Specify ELF64 relocatable objects (`ET_REL`, `.text`, `.rodata`, `.data`, `.bss`, `.symtab`, `.strtab`, `.shstrtab`, `.rela.text`, `.rela.data`, `R_X86_64_64`, `R_X86_64_PC32`, `R_X86_64_PLT32`, `R_X86_64_32`, `R_X86_64_32S`, and `SHN_ABS` for `@at` fixed-address symbols) and deterministic GNU `ar` (`!<arch>`) archives.
- Specify the static ELF64 executable linker (`ET_EXEC`, `PT_LOAD` RX/R/RW segments at base `0x400000` with 4 KiB page alignment, `_start` entry point reading `argc`/`argv`/`envp` from the initial Linux process stack, calling `main`, and invoking `syscall` `SYS_exit_group = 231` / `SYS_exit = 60`) and the `std.sys.linux` syscall mapping for all `SPEC-04 AXS-EXT-110` host intrinsics.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-80-linux-x86-64-elf-static.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ELFS-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T650-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib implementation (`T066`, `T651`, `T652`).
- Dynamic ELF (`PIE`, `GOT`/`PLT`, `.so`), which is specified in `T657` (`SPEC-82`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), scheduled first in P16 (`priority: 92`) right before `T066`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:35:00 created by T216 (P16 phase planning)
