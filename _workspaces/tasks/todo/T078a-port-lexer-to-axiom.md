---
id: T078a
title: Port lexer scanner to Axiom (UTF-8, tokens, literals)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T077]
priority: 112
status: todo
attempts: 0
paths: [compiler/lex, tests/selfhost/lex]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-LEX-114]
---
# T078a — Port lexer scanner to Axiom (UTF-8, tokens, literals)

## Goal
Port lexical scanner (`compiler/lex/`) from C to Axiom.

## Scope
- Port UTF-8 source scanner, token kinds, keyword lookup, and literal decoders (integer, char, string).
- Match tokenization rules from `bootstrap/axiom0/src/lex/` and `spec/SPEC-01-lexical.md`.
- Unit tests under `tests/selfhost/lex/`.

## Acceptance
- [ ] Lexer implemented in `compiler/lex/` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Differential token stream matches `axiom0 inspect --emit=tokens` on representative fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T078a-report.md` with exact `## Files changed`.

## Out of scope
- Full corpus differential validation (handled in integration task T078).

## Notes
- Sub-task of T078 split per ADR-0005 §8 and SPEC-20 §4.2.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
