---
id: T047
title: Initialization analysis (definite init, reinit after move)
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T046]
priority: 67
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/own/init, tests/ui/init, tests/run/init]
locks: [bootstrap/axiom0/src/diag/codes/INIT.def]
spec: [spec/SPEC-10-ownership.md, tasks/0394]
---
# T047 — Initialization analysis (definite init, reinit after move)

## Goal
Definite initialization across CFG including loops and conditional moves.

## Scope
- Uninit use errors, conditional init, reinitialisation of moved places, struct field init.

## Acceptance
- [ ] Every test-matrix row tagged T047 passes. Run tests carry `// native-after: T051`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T047-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
