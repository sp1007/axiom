---
id: T666
title: E16.4 — Apple ARM64 ABI specialization (X18 reserve, packed stack/variadics) & Mach-O 64 object/archive writer
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T662, T665]
priority: 109
status: todo
attempts: 0
paths: [compiler/abi/apple_arm64, compiler/obj/macho, tests/obj/macho, tests/selfhost/abi, tests/selfhost/obj]
spec: [spec/SPEC-84-macos-aarch64-macho.md, 0193, 0196, 0217, tasks/0369]
covers: [REQ-TGT-299, REQ-TGT-300, REQ-TGT-301, REQ-TGT-302]
---
# T666 — E16.4 — Apple ARM64 ABI specialization (X18 reserve, packed stack/variadics) & Mach-O 64 object/archive writer

## Goal
Implement the Apple Darwin ARM64 ABI specialization in `compiler/abi/apple_arm64` and the Mach-O 64 relocatable object (`MH_OBJECT`) and BSD `ar` archive writer/reader in `compiler/obj/macho`.

## Scope
- Implement Apple ARM64 ABI specialization in `compiler/abi/apple_arm64`: mark `X18` as permanently reserved in the `aarch64-macos` `RegisterFile`, enforce caller sign/zero extension for `i8`/`u8`/`i16`/`u16`/`bool` arguments, pack spilled non-variadic stack arguments at natural alignment (1/2/4/8/16 bytes) while placing variadic arguments on the stack at 8-byte alignment, maintain the `X29` (`FP`) frame-record chain, and prepend `_` to C/symbol names (`0196 §11–12`).
- Implement the deterministic Mach-O 64 `MH_OBJECT` writer in `compiler/obj/macho`: `mach_header_64` (`MH_SUBSECTIONS_VIA_SYMBOLS`), `LC_SEGMENT_64`, `LC_BUILD_VERSION` (`PLATFORM_MACOS`), `LC_SYMTAB`, `LC_DYSYMTAB`, `__TEXT,__text`, `__TEXT,__cstring`, `__TEXT,__const`, `__DATA,__data`, `__DATA,__bss`, `nlist_64` symbol table, and ARM64 Mach-O relocations (`ARM64_RELOC_UNSIGNED`, `ARM64_RELOC_SUBTRACTOR`, `ARM64_RELOC_BRANCH26`, `ARM64_RELOC_PAGE21`, `ARM64_RELOC_PAGEOFF12`, `ARM64_RELOC_GOT_LOAD_PAGE21`, `ARM64_RELOC_GOT_LOAD_PAGEOFF12`, `ARM64_RELOC_ADDEND`).
- Implement BSD `ar` (`__.SYMDEF SORTED` and `#1/<len>` long names) archive reading and writing in `compiler/obj/macho`.
- Add unit and selfhost tests in `tests/obj/macho`, `tests/selfhost/abi`, and `tests/selfhost/obj`.

## Acceptance
- [ ] `axiomc build --target aarch64-macos --emit=obj` emits deterministic Mach-O 64 `MH_OBJECT` files with valid sections, `nlist_64` symbols, and `ARM64_RELOC_*` relocations.
- [ ] Positive and negative tests in `tests/obj/macho`, `tests/selfhost/abi`, and `tests/selfhost/obj` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T666-report.md` with exact `## Files changed`.

## Out of scope
- Mach-O `MH_EXECUTE` / `MH_DYLIB` linking, chained fixups, ad-hoc code signing, and `std.sys.macos` (`T667`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:39:00 created by T216 (P16 phase planning)
