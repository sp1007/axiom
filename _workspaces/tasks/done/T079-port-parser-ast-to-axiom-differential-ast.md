---
id: T079
title: Port parser + AST to Axiom (integration + differential AST)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T079a, T079b]
priority: 113
status: done
attempts: 1
paths: [compiler/parser, tests/selfhost/parser]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-022]
started: 2026-10-14 20:25:11
finished: 2026-10-14 20:38:32
---
# T079 — Port parser + AST to Axiom (integration + differential AST)

## Goal
Integrate parser and AST in Axiom and run differential AST testing against `axiom0`.

## Scope
- Integrate `compiler/syntax/ast.ax` and `compiler/syntax/parse.ax`.
- Differential test harness comparing AST dumps with `axiom0 inspect --emit=ast` over the whole tests corpus.
- Verification of syntax error handling and recovery.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T079a and T079b integrated and passing differential checks.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T079-report.md` with exact `## Files changed`.

## Out of scope
- HIR lowering and name resolution (handled in T080).

## Notes
- Group integration task for T079a and T079b per ADR-0005 §8 and SPEC-20 §4.3.
- Exact differential artefact: `inspect --emit=ast`.
- Harness entry: `tests/selfhost/parser`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 20:25:11 started (attempt 1) axiom-frontend
- 2026-10-14 20:38:32 accepted by QA -> done
