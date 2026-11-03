---
id: T659
title: E16.2 — ELF64 PIE executable & shared object (.so) linker, DT_NEEDED resolution & libc/dlopen interop
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T651, T658]
priority: 102
status: todo
attempts: 0
paths: [compiler/link/elf_dyn, std/sys/linux_dl, tests/run/linux_dyn, tests/selfhost/link]
spec: [spec/SPEC-82-linux-elf-dynamic.md, 0164, 0197, 0217, tasks/0369, tasks/0563]
covers: [REQ-TGT-182, REQ-TGT-183, REQ-TGT-184, REQ-TGT-307, REQ-TGT-308]
---
# T659 — E16.2 — ELF64 PIE executable & shared object (.so) linker, DT_NEEDED resolution & libc/dlopen interop

## Goal
Implement the ELF64 `ET_DYN` linker for Position-Independent Executables (`PIE`) and shared objects (`.so`), external shared-library `DT_NEEDED` symbol resolution, `libc` FFI interop, and `std.sys.linux_dl` dynamic loading.

## Scope
- Implement the ELF64 `ET_DYN` linker in `compiler/link/elf_dyn`:
  - PIE executables (`--pie` / dynamic mode): emit `PT_PHDR`, `PT_INTERP` (`/lib64/ld-linux-x86-64.so.2`), `PT_LOAD` segments, `PT_DYNAMIC`, `PT_GNU_RELRO`, `PT_GNU_STACK`, `.init_array`/`.fini_array`, and PIC `_start` startup code.
  - Shared objects (`--kind dll` on Linux): emit `ET_DYN` `lib<name>.so` with `DT_SONAME`, `@export` default-visibility (`STV_DEFAULT`) symbols in `.dynsym`, hidden (`STV_HIDDEN`) internal symbols, GNU symbol version tables (`SHT_GNU_versym`/`SHT_GNU_verneed`), and `.init_array` module initializer hooks (including E13.7 module-relative bindings).
  - External `.so` consumption: parse external `.so` `.dynsym`/`.gnu.hash` tables for `@link("<lib>")` and `-l<lib>`, record `DT_NEEDED`, and generate `PLT`/`GOT` bindings (supporting both lazy binding and `-z now` / `DT_BIND_NOW`).
- Implement `std/sys/linux_dl` wrapping `dlopen`, `dlsym`, `dlclose`, `dlerror`, and `/proc/self/maps` / `dl_iterate_phdr` module base lookup for Linux dynamic libraries.
- Add tests in `tests/run/linux_dyn` and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc` builds ELF64 PIE executables and `.so` shared libraries that link against `libc.so.6` and custom `.so` libraries and run under WSL / Linux.
- [ ] Positive and negative tests in `tests/run/linux_dyn` and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T659-report.md` with exact `## Files changed`.

## Out of scope
- Non-Linux dynamic formats (Mach-O `.dylib` is `E16.4`; cross-target matrix is `E16.10`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:37:00 created by T216 (P16 phase planning)
