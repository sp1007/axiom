---
id: T705
title: E17.2 DWARF v5 DIE tree, .debug_info/.debug_abbrev/.debug_str & .debug_line state-machine emitter
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T701, T704]
priority: 175
status: todo
attempts: 0
paths: [compiler/obj/dwarf, tests/selfhost/debug/dwarf]
spec: [spec/SPEC-93-dwarf-elf-macho.md, spec/SPEC-92-debug-ir-codeview-pdb.md, tasks/0596, tasks/0525]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T705 — E17.2 DWARF v5 DIE tree, .debug_info/.debug_abbrev/.debug_str & .debug_line state-machine emitter

## Goal
Implement the DWARF v5 DIE tree builder, .debug_info/.debug_abbrev/.debug_str/.debug_line_str serializers, and DWARF v5 .debug_line state-machine program encoder.

## Scope
- Implement `compiler/obj/dwarf` lowering target-independent `DebugModule` into DWARF v5 compilation units (`DW_UT_compile`), abbreviation tables (`.debug_abbrev`), string tables (`.debug_str`, `.debug_line_str`), and `.debug_info` DIE trees covering primitives, structs, `DW_TAG_variant_part` enums/niches, slices/views, closures, generic instantiations, lexical blocks, and `DW_TAG_inlined_subroutine`.
- Implement the DWARF v5 `.debug_line` line-number program encoder in `compiler/obj/dwarf` with `DW_LNCT_path`, `DW_LNCT_directory_index`, `DW_LNCT_MD5`, `is_stmt`, `prologue_end`, `epilogue_begin`, `discriminator`, and special-opcode compression across x86-64, AArch64, RISC-V64, and WASM32 instruction alignments.
- Add selfhost unit tests in `tests/selfhost/debug/dwarf` verifying DIE encodings, LEB128 attributes, and line-table state machine round-tripping.

## Acceptance
- [ ] `axiomc build -g --emit=obj` on ELF, Mach-O, and WASM targets emits deterministic `.debug_info`, `.debug_abbrev`, `.debug_str`, `.debug_line_str`, and `.debug_line` sections verified by `tests/selfhost/debug/dwarf`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T705-report.md` with exact `## Files changed`.

## Out of scope
- `.debug_loclists`, `.debug_rnglists`, `.debug_names`, and final ELF/Mach-O `.dSYM` linking (`T706`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
