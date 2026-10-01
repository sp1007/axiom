---
id: T013
title: Lexer/parser fuzz harness + seed corpus
phase: P2-frontend
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T012, T005, T016]
priority: 28
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
- [ ] The gate campaign `python tools/fuzz.py --seed 1 --iterations 200000` (command recorded in tests/fuzz/README.md) ends with 0 findings. Campaigns are defined by seed and iteration count, never by wall time (ADR-0005 §3).
- [ ] No open findings: each crash/ICE/hang/non-determinism found on the way is minimised into a regression test under tests/ui or tests/parse that passes. A finding that needs a compiler fix → report BLOCKED with the minimised repro; the architect files the fix task (ids T112–T199) and this task resumes after it.
- [ ] `--smoke` mode (fixed seed, ≤ 60 s) for the CI hook pre-wired by T004. Documented in tests/fuzz/README.md (tests/README.md is not edited).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T013-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
