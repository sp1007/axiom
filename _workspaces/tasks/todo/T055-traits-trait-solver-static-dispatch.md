---
id: T055
title: Traits + trait solver + static dispatch
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
depends: [T054]
priority: 75
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/traits, bootstrap/axiom0/src/types, tests/run/trait, tests/ui/trait]
spec: [0158, 0212, 0046, 0272, tasks/0389, tasks/0611]
---
# T055 — Traits + trait solver + static dispatch

## Goal
Trait system with a solver that never guesses.

## Scope
- Trait decls, impls, bounds, where clauses, solver results PROVEN/DISPROVEN/AMBIGUOUS/OVERFLOW with cache, coherence/orphan rules (basic), static dispatch through monomorphization.

## Acceptance
- [ ] ui tests for missing impl, ambiguity, overlap; run tests for dispatch.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T055-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
