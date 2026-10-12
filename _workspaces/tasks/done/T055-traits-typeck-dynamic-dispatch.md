---
id: T055
title: Traits + trait solver + static dispatch
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T054b]
priority: 75
status: done
attempts: 0
paths: [bootstrap/axiom0/src, tests/run/trait, tests/ui/trait, tests/run/drop, tests/ui/drop, tests/ui/method]
locks: [bootstrap/axiom0/src/diag/codes/TRAIT.def, bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/pipeline.c]
timeout_min: 300
spec: [0158, 0212, 0046, tasks/0272, tasks/0389, tasks/0611]
finished: 2026-10-12 23:32:51
---
# T055 — Traits + trait solver + static dispatch

## Goal
Trait system with a solver that never guesses.

## Scope
- Trait decls, impls, bounds, where clauses, solver results PROVEN/DISPROVEN/AMBIGUOUS/OVERFLOW with cache, coherence/orphan rules (basic), static dispatch through monomorphization.
- `Drop` becomes an ordinary lang-item trait: the fixed-shape recognition of T049 is retired (ADR-0006 §1).

## Acceptance
- [ ] ui tests for missing impl, ambiguity, overlap; run tests for dispatch (they carry `// native-after: T059`).
- [ ] At least one positive run test and one negative ui test per Scope bullet; the report maps each bullet to its test files (QA checks the map).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T055-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-12 23:32:51 accepted by QA -> done
