---
id: T078
title: Port lexer to Axiom (integration + differential tokens)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T078a]
priority: 112
status: done
attempts: 1
paths: [compiler/lexer, tests/selfhost/lexer]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-LEX-114]
started: 2026-10-14 10:05:15
finished: 2026-10-14 10:33:21
---
# T078 — Port lexer to Axiom (integration + differential tokens)

## Goal
Integrate lexer in Axiom and run differential token testing against `axiom0`.

## Scope
- Integrate `compiler/lex` and execute tokenization over the full test corpus.
- Differential test harness comparing token streams with `axiom0 inspect --emit=tokens`.
- Validation of span tracking, escape sequences, and comment handling.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-task T078a integrated and verified across all tests.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T078-report.md` with exact `## Files changed`.

## Out of scope
- Parsing (handled in T079).

## Notes
- Group integration task for T078a per ADR-0005 §8 and SPEC-20 §4.2.
- Exact differential artefact: `inspect --emit=tokens`.
- Harness entry: `tests/selfhost/lexer`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 10:05:15 started (attempt 1) axiom-frontend
- 2026-10-14 10:33:21 accepted by QA -> done
