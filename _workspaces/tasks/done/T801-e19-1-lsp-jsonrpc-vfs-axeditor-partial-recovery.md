---
id: T801
title: E19.1 LSP JSON-RPC transport, incremental VFS, AXEDITOR piece-table buffer & partial-program recovery
phase: P19-developer-tooling
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T800]
priority: 191
status: done
attempts: 1
paths: [compiler/lsp/protocol, compiler/lsp/vfs, std/editor, tests/run/lsp_vfs]
spec: [spec/SPEC-100-lsp-server-ide-engine.md, spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-22-incremental-compilation.md, 0101, tasks/0374, tasks/0448, tasks/0450, tasks/0479, tasks/0664, tasks/1053]
covers: [REQ-TOOL-183, REQ-TOOL-184, REQ-TOOL-188, REQ-TOOL-191, REQ-TOOL-297, REQ-TOOL-298, REQ-TOOL-299]
started: 2026-11-08 12:35:07
finished: 2026-11-08 13:44:38
---
# T801 — E19.1 LSP JSON-RPC transport, incremental VFS, AXEDITOR piece-table buffer & partial-program recovery

## Goal
Implement the LSP 3.17 JSON-RPC 2.0 transport, incremental Virtual File System (`VFS`), `AXEDITOR` Unicode-aware piece-table/rope text buffer, and partial-program parser/HIR recovery per `spec/SPEC-100-lsp-server-ide-engine.md`.

## Scope
- Implement the LSP JSON-RPC 2.0 message framing, request/notification router, cancellation tokens (`$/cancelRequest`), and workspace lifecycle (`initialize`, `initialized`, `shutdown`, `exit`, `textDocument/didOpen`, `didChange`, `didSave`, `didClose`) in `compiler/lsp/protocol`.
- Implement the `AXEDITOR` Unicode-aware piece-table/rope text buffer in `std/editor` and `compiler/lsp/vfs` supporting O(log N) incremental range edits on large files (`REQ-TOOL-299`), exact UTF-8 byte offset ↔ UTF-16 line/character conversion (`0146 §22-23`), and incremental `CompilerDB` input-table updates preserving stable generational entity IDs (`LocalId`, `FunctionId`, `TypeId`, `PlaceId`; `REQ-TOOL-184`, `REQ-TOOL-191`).
- Implement partial-program syntax and HIR recovery nodes (`MissingToken`, `IncompleteExpr`, `IncompleteMemberAccess`, `IncompleteType`) so editing incomplete source files produces structured diagnostics and queryable `CompilerDB` snapshots (`REQ-TOOL-183`, `REQ-TOOL-188`, `REQ-TOOL-297`, `REQ-TOOL-298`).

## Acceptance
- [ ] Run tests in `tests/run/lsp_vfs` verify JSON-RPC framing, UTF-8/UTF-16 span conversion (including Vietnamese text `"Xin chào thế giới"`), `AXEDITOR` large-buffer incremental edits, generational ID stability across edits, and partial-program AST/HIR recovery on incomplete syntax.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T801-report.md` with exact `## Files changed`.

## Out of scope
- Semantic hover, completion, go-to-definition, rename, and VS Code client (`T802`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T801/build` and `python tools/axtest.py --compiler build-snap-T801/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 12:35:07 started (attempt 1) T801-impl
- 2026-11-08 13:44:38 accepted by QA -> done
