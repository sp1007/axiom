---
id: T657
title: E16.2 — Canonical Linux ELF dynamic linking, PIE, GOT/PLT, .so & libc interop specification (SPEC-82)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T511, T650]
priority: 100
status: done
attempts: 1
paths: [spec/SPEC-82-linux-elf-dynamic.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-80-linux-x86-64-elf-static.md, 0164, 0192, 0197, 0217, tasks/0369, tasks/0563]
covers: [REQ-TGT-061, REQ-TGT-062, REQ-TGT-063, REQ-TGT-064, REQ-TGT-065]
started: 2026-11-03 15:03:40
finished: 2026-11-03 15:21:50
---
# T657 — E16.2 — Canonical Linux ELF dynamic linking, PIE, GOT/PLT, .so & libc interop specification (SPEC-82)

## Goal
Consolidate the canonical specification for Linux ELF64 dynamic linking, Position-Independent Executables (`PIE`), Global Offset Table (`GOT`) and Procedure Linkage Table (`PLT`), shared libraries (`.so`), symbol visibility/versioning, and `libc`/`dlopen` interoperability into `spec/SPEC-82-linux-elf-dynamic.md` (`AXS-ELFD-*` rule IDs).

## Scope
- Write `spec/SPEC-82-linux-elf-dynamic.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ELFD-NNN` rules.
- Specify the separation between static ELF (`ET_EXEC`, `SPEC-80`) and dynamic ELF (`ET_DYN`, `0197 §1–12`): `PIE` executables (`ET_DYN` with `PT_INTERP` `/lib64/ld-linux-x86-64.so.2`, `DF_1_PIE`) and shared objects (`ET_DYN` `--kind dll` producing `lib<name>.so` with `DT_SONAME`).
- Specify PIC codegen and dynamic relocations (`0197 §6–16`): `RIP`-relative local addressing, `R_X86_64_GOTPCREL` / `R_X86_64_REX_GOTPCRELX` indirect address loads through `.got`, `R_X86_64_PLT32` calls through `.plt`/`.got.plt`, runtime relocations (`R_X86_64_RELATIVE`, `R_X86_64_GLOB_DAT`, `R_X86_64_JUMP_SLOT`, `R_X86_64_64`, `R_X86_64_TPOFF64`/`R_X86_64_DTPMOD64`/`R_X86_64_DTPOFF64`), and function-address equality preservation (`AMACHINE-79`).
- Specify ELF dynamic sections and segments (`tasks/0563 §304.10–13`): `PT_DYNAMIC`, `PT_GNU_RELRO` + `DT_BIND_NOW` (full RELRO) vs lazy PLT binding, `PT_GNU_STACK` (`PF_R | PF_W`, non-executable stack), `.dynsym`, `.dynstr`, `.gnu.hash` (and SysV `.hash`), `.dynamic` (`DT_NEEDED`, `DT_SONAME`, `DT_RPATH`, `DT_RUNPATH`, `DT_INIT_ARRAY`, `DT_FINI_ARRAY`, `DT_FLAGS`, `DT_FLAGS_1`), `.init_array`/`.fini_array`, symbol visibility (`STV_DEFAULT` for `@export`, `STV_HIDDEN` default for internal symbols), and GNU symbol versioning (`SHT_GNU_versym`, `SHT_GNU_verdef`, `SHT_GNU_verneed`).
- Specify `libc`, `libm`, `libpthread`, and `libdl` (`dlopen`/`dlsym`/`dlclose`/`dlerror`) interoperability (`0197 §20–25`, `0220 §2–5`): `libc` is an optional platform FFI library rather than a mandatory Core dependency, while dynamic PIE/shared builds interoperate cleanly with system `libc` and C shared objects.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-82-linux-elf-dynamic.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ELFD-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T657-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and linker implementation of ELF dynamic linking (`T658`, `T659`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:37:00 created by T216 (P16 phase planning)
- 2026-11-03 15:03:40 started (attempt 1) 
- 2026-11-03 15:21:50 accepted by QA -> done
