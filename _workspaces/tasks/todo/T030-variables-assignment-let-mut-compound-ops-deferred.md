---
id: T030
title: Variables & assignment: let mut, compound ops, deferred init
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T029]
priority: 50
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/vars, tests/ui/vars]
spec: [tasks/0476, 0263, spec/SPEC-03-core-semantics.md]
---
# T030 — Variables & assignment: let mut, compound ops, deferred init

## Goal
Mutable bindings and assignment through the full pipeline (oracle).

## Scope
- `let mut`, assignment, compound assignment, shadowing, `let x: T` + later assignment with basic definite-assignment check; mutation of immutable binding → AX_TYPE_ASSIGN_IMMUTABLE.

## Acceptance
- [ ] run + ui tests pass in interp mode (native catch-up in T033).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T030-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
