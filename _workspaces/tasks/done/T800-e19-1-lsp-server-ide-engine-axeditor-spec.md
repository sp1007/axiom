---
id: T800
title: E19.1 Canonical LSP server, IDE semantic engine, AXEDITOR/AXCODEEDITOR & VS Code extension specification (SPEC-100)
phase: P19-developer-tooling
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T756]
priority: 190
status: done
attempts: 1
paths: [spec/SPEC-100-lsp-server-ide-engine.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-22-incremental-compilation.md, 0101, 0146, tasks/0374, tasks/0448, tasks/0450, tasks/0479, tasks/0664, tasks/0693, tasks/0695, tasks/0696, tasks/1053, tasks/1054]
covers: [REQ-TOOL-183, REQ-TOOL-184, REQ-TOOL-185, REQ-TOOL-188, REQ-TOOL-189, REQ-TOOL-191, REQ-TOOL-297, REQ-TOOL-298, REQ-TOOL-299, REQ-TOOL-300]
started: 2026-11-08 12:20:14
finished: 2026-11-08 12:34:48
---
# T800 — E19.1 Canonical LSP server, IDE semantic engine, AXEDITOR/AXCODEEDITOR & VS Code extension specification (SPEC-100)

## Goal
Consolidate the canonical specification for Axiom's Language Server (`axiomc lsp`), `CompilerDB`-backed IDE semantic engine, `AXEDITOR` Unicode-aware piece-table text buffer, `AXCODEEDITOR` compiler-aware code intelligence layer, and thin VS Code client extension into `spec/SPEC-100-lsp-server-ide-engine.md` (`AXS-LSP-*` rule IDs).

## Scope
- Write `spec/SPEC-100-lsp-server-ide-engine.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-LSP-NNN` rules.
- Specify `CompilerDB` (`SPEC-21`/`SPEC-22`) as the single semantic authority for the CLI, LSP server, IDE, and editors (`REQ-TOOL-183`, `REQ-TOOL-297`, `REQ-TOOL-298`), with typed generational entity IDs (`LocalId`, `FunctionId`, `TypeId`, `PlaceId`, `SymbolId`; `REQ-TOOL-191`), stable identities across incremental queries (`REQ-TOOL-184`), and zero mandatory codegen for semantic queries (`REQ-TOOL-185`).
- Specify partial-program syntax/semantic recovery on incomplete source files (`REQ-TOOL-188`) and constraint-aware IDE completion, hover, go-to-definition, find-references, and rename (`0101 §6-13`, `0146 §31-37`, `tasks/0450`, `REQ-TOOL-189`) that enforce visibility, ownership, `view`/`mut_view` capability, and trait rules without arbitrary heuristics.
- Specify the `AXEDITOR` large-file Unicode-aware text buffer (`tasks/1053`, `REQ-TOOL-299`), the `AXCODEEDITOR` semantic highlighting, ownership/move/async inlay visualization, and completion subsystem (`tasks/1054`, `REQ-TOOL-300`), and the thin VS Code extension architecture (`0101 §38-41`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-100-lsp-server-ide-engine.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-LSP-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T800-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the LSP transport, `AXEDITOR`, and IDE query handlers (`T801`–`T802`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 12:20:14 started (attempt 1) T800-impl
- 2026-11-08 12:34:48 accepted by QA -> done
