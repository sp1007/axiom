---
id: T700
title: E17.1 Canonical Debug IR, CodeView object records & PDB/MSF container specification (SPEC-92)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316]
priority: 170
status: todo
attempts: 0
paths: [spec/SPEC-92-debug-ir-codeview-pdb.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0190, 0191, tasks/0419, tasks/0525]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T700 — E17.1 Canonical Debug IR, CodeView object records & PDB/MSF container specification (SPEC-92)

## Goal
Consolidate the canonical specification for Axiom target-independent Debug IR, Windows CodeView C13 object debug records (.debug$S and .debug$T), and the deterministic PDB 7.00 / MSF v7 container writer into spec/SPEC-92-debug-ir-codeview-pdb.md (AXS-PDB-* rules).

## Scope
- Write `spec/SPEC-92-debug-ir-codeview-pdb.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-PDB-NNN` rules.
- Specify the target-independent `DebugIR` model (`0190 §4–30`, `tasks/0525 §188`): strong IDs (`DebugFileId`, `DebugFunctionId`, `DebugScopeId`, `DebugVarId`, `DebugTypeId`), bidirectional `SourceOrigin` provenance from HIR/MIR/OptIR/LIR to machine instructions, lexical scopes distinct from ownership/capability lifetimes (`ADBG-22`), post-RA `MachineLocation` range lists (`Register`, `FrameSlot`, `Constant`, `Composite`, and explicit `OptimizedOut` without fabricating runtime values per `DEBUG-20`/`ADBG-25`), and logical inline call trees (`ADBG-29`).
- Specify CodeView C13 object sections (`0190 §31–61`): `.debug$S` subsections (`DEBUG_S_SYMBOLS` with `S_OBJNAME`, `S_COMPILE3`, `S_GPROC32_ID`/`S_LPROC32_ID`, `S_BLOCK32`, `S_REGREL32`, `S_LOCAL`, `S_DEFRANGE_REGISTER`, `S_DEFRANGE_FRAMEPOINTER_REL`, `S_INLINESITE`, `S_END`; `DEBUG_S_LINES`; `DEBUG_S_FILECHKSMS` with SHA-256 source checksums; `DEBUG_S_STRINGTABLE`; `DEBUG_S_INLINEELINES`) and `.debug$T` type records (`LF_MODIFIER`, `LF_POINTER`, `LF_ARRAY`, `LF_STRUCTURE`, `LF_FIELDLIST`, `LF_ENUM`, `LF_PROCEDURE`, `LF_MFUNCTION`, `LF_FUNC_ID`, `LF_STRING_ID`, `LF_UDT_SRC_LINE`) reflecting final machine layout (`0190 §18`).
- Specify the deterministic MSF v7 container and PDB 7.00 writer (`0191 §3–60`): `Microsoft C/C++ MSF 7.00\r\n\x1aDS\0\0\0` superblock, 4096-byte page allocator, Free Page Map (FPM1/FPM2), two-phase Stream Directory layout, Stream 1 (PDB Info with content-hash GUID and deterministic `Age = 1`, zero random timestamps), Stream 2 (TPI), Stream 3 (DBI module descriptors, section contributions, section map), Stream 4 (IPI), Global/Public hashed symbol streams (GSI/PSI), and PE `IMAGE_DIRECTORY_ENTRY_DEBUG` (`IMAGE_DEBUG_TYPE_CODEVIEW` `RSDS` header).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-92-debug-ir-codeview-pdb.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-PDB-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T700-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or linker implementation (`T701`, `T702`, `T703`).
- DWARF v5 serialization (`T704` `SPEC-93`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
