---
id: T013
title: Lexer/parser fuzz harness + seed corpus
phase: P2-frontend
owner: axiom-qa
reviewer: axiom-qa
depends: [T012, T005]
priority: 23
status: todo
attempts: 0
paths: [tools/fuzz.py, tests/fuzz]
spec: [0263, tasks/0381]
---
# T013 — Lexer/parser fuzz harness + seed corpus

## Goal
Catch crashes, ICEs, hangs and non-determinism in the frontend early.

## Scope
- tools/fuzz.py: byte mutation, token splicing, grammar-based generation from SPEC-02; runs `axiom0 check --json`; detects crash/ICE/timeout/non-deterministic output; minimises findings.
- Seed corpus from tests/lex + tests/parse; `--iterations`, `--seed` for reproducibility.

## Acceptance
- [ ] A 20-minute campaign with no findings (or findings fixed via regression tests by filing follow-ups).
- [ ] Documented how to run in tests/README.md.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T013-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
