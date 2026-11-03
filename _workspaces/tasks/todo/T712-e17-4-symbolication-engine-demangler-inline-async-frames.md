---
id: T712
title: E17.4 Cross-format symbolication engine (PDB/DWARF/source-map), demangler & inline/async frame resolver
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T702, T706, T709, T711]
priority: 183
status: todo
attempts: 0
paths: [compiler/debug/symbolicate, std/debug/symbolicate, tests/selfhost/debug/symbolicate]
spec: [spec/SPEC-95-debugger-contract-symbolication.md, 0100, 0147, tasks/0596, tasks/0811, tasks/1055]
covers: [REQ-DBG-116, REQ-DBG-118, REQ-DBG-120]
---
# T712 — E17.4 Cross-format symbolication engine (PDB/DWARF/source-map), demangler & inline/async frame resolver

## Goal
Implement the cross-format symbolication engine (PDB, DWARF v5, and WASM debug sections), canonical Axiom symbol demangler, and logical inline/async frame reconstructor.

## Scope
- Implement `compiler/debug/symbolicate` and `std.debug.symbolicate` reading PDB 7.00 (Publics/Globals, DBI module C13 lines, `S_INLINESITE` + `DEBUG_S_INLINEELINES`), DWARF v5 (`.debug_names`, `.debug_aranges`, `.debug_line`, `.debug_info` `DW_TAG_inlined_subroutine`, `.debug_rnglists`), and WASM debug sections to map code RVAs to ordered logical frames (`SymbolicatedFrame`).
- Implement the deterministic Axiom symbol demangler formatting module paths (`.` syntax), generic type arguments, trait impl paths, closures, and async/generator state machines.
- Implement async task suspension-tree reconstruction and build-ID / source-SHA-256 mismatch diagnostics (`ADEBUG-96`, `0811 §589.193–195`).
- Add selfhost unit tests in `tests/selfhost/debug/symbolicate`.

## Acceptance
- [ ] Symbolication engine resolves physical instruction RVAs to exact `function + file:line:col` and expands nested inline call chains across both PDB and DWARF v5 artifacts.
- [ ] Mismatched binary/debug build IDs and modified source hashes emit structured mismatch warnings (`ADEBUG-96`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T712-report.md` with exact `## Files changed`.

## Out of scope
- Natvis/GDB/LLDB visualizers and CLI subcommands (`T713`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
