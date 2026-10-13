---
id: T079b
title: Port recursive-descent parser to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T079a]
priority: 113
status: todo
attempts: 0
paths: [compiler/syntax/parse.ax, tests/selfhost/parse]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-022]
---
# T079b — Port recursive-descent parser to Axiom

## Goal
Port the recursive-descent parser and Pratt expression parser (`compiler/syntax/parse.ax`) from C to Axiom.

## Scope
- Port top-level item parser, statement parser, type parser, pattern parser, and Pratt expression parser.
- Match grammar specification from `spec/SPEC-02-grammar.md` and error recovery from `bootstrap/axiom0/src/syntax/parse.c`.
- Unit tests under `tests/selfhost/parse/`.

## Acceptance
- [ ] Parser implemented in `compiler/syntax/parse.ax` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Parsed AST matches `axiom0 inspect --emit=ast` on representative syntax tests.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T079b-report.md` with exact `## Files changed`.

## Out of scope
- Full corpus differential validation (handled in integration task T079).

## Notes
- Sub-task of T079 split per ADR-0005 §8 and SPEC-20 §4.3.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
