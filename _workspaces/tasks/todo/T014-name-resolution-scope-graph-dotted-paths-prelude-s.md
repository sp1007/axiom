---
id: T014
title: Name resolution: scope graph, dotted paths, prelude stub
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T012]
priority: 24
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/resolve, tests/resolve, tests/ui/resolve]
spec: [0156, tasks/0387, tasks/0357, tasks/0497, 0103, .claude/skills/axiom-syntax]
---
# T014 — Name resolution: scope graph, dotted paths, prelude stub

## Goal
Resolve every identifier and DottedChain to SymbolIds within a single module (multi-module comes in T060).

## Scope
- Symbol table, scopes (block, fn, module), lookup order local → param → module → import → re-export → prelude; forward references for items; shadowing rules; duplicate definitions.
- DottedChain disambiguation (value vs module vs type vs enum variant) per axiom-syntax; AX_NAME_SHADOW_MODULE warning.
- Built-in prelude stub (primitive types, Option/Result names reserved until P5).
- `inspect --emit=resolved` (AST annotated with symbol ids).

## Acceptance
- [ ] ui tests: unknown name, duplicate item, use before let, shadowing allowed, variant paths, field access on locals vs module paths.
- [ ] Golden tests of resolution dumps.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T014-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
