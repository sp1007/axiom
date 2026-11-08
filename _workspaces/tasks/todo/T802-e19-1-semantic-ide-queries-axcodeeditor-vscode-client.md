---
id: T802
title: E19.1 Semantic IDE queries (hover, definition, references, completion, rename) & AXCODEEDITOR/VS Code client
phase: P19-developer-tooling
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T801]
priority: 192
status: todo
attempts: 0
paths: [compiler/lsp/handlers, compiler/driver/lsp_cmd, tools/vscode-axiom, tests/run/lsp_queries]
spec: [spec/SPEC-100-lsp-server-ide-engine.md, 0101, 0146, tasks/0374, tasks/0448, tasks/0450, tasks/0664, tasks/0693, tasks/0695, tasks/0696, tasks/1054]
covers: [REQ-TOOL-183, REQ-TOOL-185, REQ-TOOL-188, REQ-TOOL-189, REQ-TOOL-297, REQ-TOOL-298, REQ-TOOL-300]
---
# T802 — E19.1 Semantic IDE queries (hover, definition, references, completion, rename) & AXCODEEDITOR/VS Code client

## Goal
Implement `CompilerDB`-backed semantic LSP query handlers (diagnostics, hover, go-to-definition, find-references, completion, rename, semantic tokens, ownership inlay hints), the `axiomc lsp` CLI command, and the thin VS Code extension per `spec/SPEC-100-lsp-server-ide-engine.md`.

## Scope
- Implement semantic LSP handlers in `compiler/lsp/handlers` querying `CompilerDB` directly without invoking backend codegen (`REQ-TOOL-183`, `REQ-TOOL-185`, `REQ-TOOL-297`, `REQ-TOOL-298`):
  - `textDocument/publishDiagnostics` streaming snapshot-bound diagnostics on open/change;
  - `textDocument/definition`, `typeDefinition`, `implementation`, `references`, `documentSymbol`, and `workspace/symbol` using canonical `SymbolId` resolution (`0101 §9-11`);
  - `textDocument/hover` displaying resolved type, ownership status (`owned`/`moved`), active capability (`view`/`mut_view`), trait resolution origin, and type layout summary (`0146 §33-36`);
  - `textDocument/completion` on partial programs (`REQ-TOOL-188`, `REQ-TOOL-189`) filtering candidates by lexical scope, module visibility, expected type, ownership liveness (excluding moved locals), and receiver capability (`view` vs `mut_view`) without arbitrary heuristics (`0101 §6-8`, `tasks/0450`);
  - `textDocument/prepareRename` and `textDocument/rename` across locals, functions, types, fields, modules, and generic parameters (`0101 §12-13`);
  - `AXCODEEDITOR` compiler-aware semantic tokens (`textDocument/semanticTokens/full` and `delta`) and ownership/move/capability/async suspension inlay hints (`0101 §18-22`, `tasks/1054`, `REQ-TOOL-300`).
- Implement `axiomc lsp` in `compiler/driver/lsp_cmd` and package the thin VS Code client extension in `tools/vscode-axiom` (`package.json`, language configuration, TextMate fallback grammar, LSP client entrypoint; `0101 §38-40`).

## Acceptance
- [ ] Run tests in `tests/run/lsp_queries` verify hover, go-to-definition, find-references, constraint-filtered completion on partial files (respecting visibility, moved values, and `view`/`mut_view`), cross-module rename, `AXCODEEDITOR` semantic tokens/inlay hints, and `tools/vscode-axiom` extension manifest/client wiring without running codegen.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T802-report.md` with exact `## Files changed`.

## Out of scope
- Canonical source formatter (`T804`–`T807`) and structural refactoring transforms (`T808`–`T811`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T802/build` and `python tools/axtest.py --compiler build-snap-T802/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
