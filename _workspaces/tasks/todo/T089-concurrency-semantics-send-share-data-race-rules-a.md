---
id: T089
title: Concurrency semantics: Send/Share, data-race rules, atomics in MIR
phase: P11-v1
owner: axiom-semantics
reviewer: axiom-qa
depends: [T075]
priority: 131
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/traits/auto, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/ui/concurrency]
spec: [0091, 0092, 0079, 0276, tasks/0298, 0208]
---
# T089 — Concurrency semantics: Send/Share, data-race rules, atomics in MIR

## Goal
Compile-time data-race freedom.

## Scope
- Send/Share auto traits, spawn capture checks, atomic intrinsics with memory orderings in MIR and interp (deterministic scheduler in oracle).

## Acceptance
- [ ] ui + run tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T089-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
