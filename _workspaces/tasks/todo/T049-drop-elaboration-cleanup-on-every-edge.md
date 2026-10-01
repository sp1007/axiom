---
id: T049
title: Drop elaboration + cleanup on every edge
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T048b]
priority: 69
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop]
locks: [bootstrap/axiom0/src/diag/codes/DROP.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [spec/SPEC-12-drop.md, 0178, 0030, 0118, tasks/0674]
---
# T049 — Drop elaboration + cleanup on every edge

## Goal
Deterministic destruction made explicit in MIR.

## Scope
- Destructors in the final surface form `impl Drop for S { fn drop(self: mut_view<S>) { … } }`, recognised as one fixed shape for nominal non-generic types until traits exist, and built-in `drop(x)` (ADR-0006 §1; `BOOTSTRAP-SHORTCUT` retired by T055, generic types by T054b); reverse declaration order, drop flags for conditional moves, cleanup on return/break/continue/`?`/panic-abort paths, explicit `drop(x)`, drop of aggregates/enums field-wise.

## Acceptance
- [ ] Drop order observable via print in run tests; every test-matrix row tagged T049 passes. Run tests carry `// native-after: T051`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T049-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
