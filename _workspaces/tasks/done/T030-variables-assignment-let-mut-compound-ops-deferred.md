---
id: T030
title: Variables & assignment: let mut, compound ops, deferred init
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T029, T015b]
priority: 50
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/vars, tests/ui/vars]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [tasks/0476, 0263, spec/SPEC-03-core-semantics.md]
covers: [REQ-DRP-001, REQ-DRP-002, REQ-DRP-003]
started: 2026-10-08 08:04:42
unblocks: 1
finished: 2026-10-08 08:19:49
---
# T030 — Variables & assignment: let mut, compound ops, deferred init

## Goal
Mutable bindings and assignment through the full pipeline (oracle).

## Scope
- `let mut`, assignment, compound assignment, shadowing, `let x: T` + later assignment with basic definite-assignment check; mutation of immutable binding → AX_TYPE_ASSIGN_IMMUTABLE.

## Acceptance
- [ ] run + ui tests pass in interp mode; run tests carry `// native-after: T033` (removed by T033).
- [ ] At least one positive run test and one negative ui test per Scope bullet; the report maps each bullet to its test files (QA checks the map).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T030-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
- The types module expects bindings to be represented by mapping `AxSymbolId` to `TypeId` via the `symbol_types` map in `AxThir`.

## Log
- 2026-10-06 02:23:57 covers += REQ-DRP-001, REQ-DRP-002, REQ-DRP-003 (metadata only)
- 2026-10-08 08:02:04 started (attempt 1) T030-impl
- 2026-10-08 08:02:54 block: need more information on how the types module expects bindings to be represented
- 2026-10-08 08:03:47 unblocked (cycle 1) 
- 2026-10-08 08:04:42 started (attempt 1) T030-impl
- 2026-10-08 08:19:49 accepted by QA -> done
