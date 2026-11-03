---
id: T701
title: E17.1 Target-independent Debug IR builder, location-range tracker & CodeView .debug$S/.debug$T emitter
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T700]
priority: 171
status: todo
attempts: 0
paths: [compiler/debug/ir, compiler/obj/codeview, tests/selfhost/debug/codeview]
spec: [spec/SPEC-92-debug-ir-codeview-pdb.md, spec/SPEC-04-core-extensibility.md, 0190, tasks/0419, tasks/0525]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T701 — E17.1 Target-independent Debug IR builder, location-range tracker & CodeView .debug$S/.debug$T emitter

## Goal
Implement the target-independent Debug IR builder, post-RA variable location-range tracker, and CodeView C13 .debug$S/.debug$T COFF section emitter for Windows x64 and Windows ARM64.

## Scope
- Implement `compiler/debug/ir` (`DebugModule`, `DebugFileId`, `DebugFunctionId`, `DebugScopeId`, `DebugVarId`, `DebugTypeId`, bidirectional `SourceOrigin` tables, lexical scope hierarchy, inline call-site trees, and post-RA `MachineLocation` range lists with explicit `OptimizedOut` tracking) without retaining AST pointers or altering codegen when `-g` is enabled or omitted.
- Implement `compiler/obj/codeview` lowering `DebugModule` into deterministic CodeView C13 `.debug$T` (`LF_STRUCTURE`, `LF_FIELDLIST`, `LF_ENUM`, `LF_POINTER`, `LF_ARRAY`, `LF_PROCEDURE`, `LF_FUNC_ID`, `LF_UDT_SRC_LINE` with actual machine field offsets) and `.debug$S` (`DEBUG_S_SYMBOLS`, `DEBUG_S_LINES`, `DEBUG_S_FILECHKSMS` SHA-256, `DEBUG_S_STRINGTABLE`, `DEBUG_S_INLINEELINES` and COFF section relocations `IMAGE_REL_AMD64_SECREL`/`SECTION` and `IMAGE_REL_ARM64_SECREL`/`SECTION`).
- Add selfhost unit and golden tests in `tests/selfhost/debug/codeview` verifying `.debug$S`/`.debug$T` binary records and `-g` vs stripped codegen invariance.

## Acceptance
- [ ] `axiomc build -g --emit=obj` on Windows x64 and Windows ARM64 emits valid `.debug$S` and `.debug$T` COFF sections verified by `tests/selfhost/debug/codeview`.
- [ ] Compiling with `-g` vs without `-g` produces byte-identical `.text`, `.rdata`, and `.data` sections (`DEBUG-20` / `ADBG-20`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T701-report.md` with exact `## Files changed`.

## Out of scope
- MSF v7 container and `.pdb` file linking (`T702`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
