---
id: T079a
title: Port AST data structures & visitor to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T078]
priority: 113
status: done
attempts: 1
paths: [compiler/syntax/ast.ax, tests/selfhost/ast]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-022]
started: 2026-10-14 10:33:38
finished: 2026-10-14 12:45:29
---
# T079a — Port AST data structures & visitor to Axiom

## Goal
Port Abstract Syntax Tree (AST) node definitions and AST visitor traits (`compiler/syntax/ast.ax`) from C to Axiom.

## Scope
- Port AST definitions: items, statements, expressions, patterns, types, attributes, visibility.
- Port AST visitor pattern / traversal methods for walking the AST.
- Unit tests under `tests/selfhost/ast/`.

## Acceptance
- [ ] AST data model implemented in `compiler/syntax/ast.ax` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] AST serialization matches format expected by `inspect --emit=ast`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T079a-report.md` with exact `## Files changed`.

## Out of scope
- Parsing logic (handled in T079b).

## Notes
- Sub-task of T079 split per ADR-0005 §8 and SPEC-20 §4.3.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 10:33:38 started (attempt 1) axiom-frontend
- 2026-10-14 12:45:29 accepted by QA -> done
