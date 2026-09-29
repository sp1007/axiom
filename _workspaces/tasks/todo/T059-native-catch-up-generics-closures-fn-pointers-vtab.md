---
id: T059
title: Native catch-up: generics, closures, fn pointers
phase: P7-abstraction
owner: axiom-backend
reviewer: axiom-qa
depends: [T057]
priority: 79
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/obj, tests/run/native_p7]
spec: [0183, 0162]
---
# T059 — Native catch-up: generics, closures, fn pointers

## Goal
All P7 programs run natively.

## Scope
- Mono instance codegen and symbol emission, closure environments, indirect calls (dyn/vtables moved to E14.4).

## Acceptance
- [ ] Differential green.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T059-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
