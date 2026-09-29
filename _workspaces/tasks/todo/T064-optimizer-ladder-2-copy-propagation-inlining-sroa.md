---
id: T064
title: Optimizer ladder 2: copy propagation, inlining, SROA
phase: P8-backend
owner: axiom-semantics
reviewer: axiom-qa
depends: [T062]
priority: 91
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/opt, tests/opt2]
spec: [0165, 0226, tasks/0401, tasks/0399]
---
# T064 — Optimizer ladder 2: copy propagation, inlining, SROA

## Goal
Meaningful MIR optimizations with legality from ownership facts.

## Scope
- Copy propagation, small-function inlining, scalar replacement of aggregates, simple bounds-check elimination, return-slot construction (0152 §74).

## Acceptance
- [ ] Differential green; perf numbers recorded.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T064-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
