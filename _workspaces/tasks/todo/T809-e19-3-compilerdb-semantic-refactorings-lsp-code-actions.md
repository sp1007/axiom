---
id: T809
title: E19.3 CompilerDB semantic refactorings (extract function/binding, exhaustive match, use imports) & LSP codeAction
phase: P19-developer-tooling
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T802, T808]
priority: 199
status: todo
attempts: 0
paths: [compiler/refactor/transforms, compiler/refactor/code_actions, tests/run/refactor_engine]
locks: [compiler/lsp/handlers/mod.ax]
spec: [spec/SPEC-102-refactoring-engine-semantic-vcs.md, spec/SPEC-100-lsp-server-ide-engine.md, 0101, tasks/0448]
covers: [REQ-TOOL-183, REQ-TOOL-186]
---
# T809 — E19.3 CompilerDB semantic refactorings (extract function/binding, exhaustive match, use imports) & LSP codeAction

## Goal
Implement `CompilerDB`-verified semantic refactoring transformations and LSP `textDocument/codeAction` handlers in `compiler/refactor/transforms` and `compiler/refactor/code_actions` per `spec/SPEC-102-refactoring-engine-semantic-vcs.md`.

## Scope
- Implement semantic refactoring transformations in `compiler/refactor/transforms` using `CompilerDB` ownership, capability, type, and exhaustiveness queries (`0101 §14-17`, `REQ-TOOL-183`):
  - `extract_function`: computes captured bindings, ownership transfers, and `view`/`mut_view` borrows across the selection boundary to emit a well-typed helper function and call expression;
  - `extract_variable` and `inline_variable`: verifies evaluation-order, side-effect, and capability-lifetime preservation;
  - `populate_match_arms`: expands non-exhaustive `match` expressions with canonical missing pattern arms;
  - `organize_imports`: resolves, deduplicates, and canonicalizes `use` paths.
- Enforce compiler verification of all proposed source edits before committing workspace edits (`REQ-TOOL-186`), and wire `textDocument/codeAction` and `codeAction/resolve` in `compiler/refactor/code_actions` and `compiler/lsp/handlers/mod.ax`.

## Acceptance
- [ ] Run tests in `tests/run/refactor_engine` verify `extract_function` (owned, `view`, and `mut_view` captures), `extract_variable`/`inline_variable`, `populate_match_arms`, `organize_imports`, rejection of unsafe/semantics-breaking refactorings, and LSP `codeAction` integration.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T809-report.md` with exact `## Files changed`.

## Out of scope
- AST diff/merge/patch and semantic VCS history (`T810`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T809/build` and `python tools/axtest.py --compiler build-snap-T809/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
