---
id: T058
title: dyn Trait: vtables and dynamic dispatch
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
depends: [T057]
priority: 78
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/traits/dyn, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/dyn, tests/ui/dyn]
spec: [tasks/0476, 0212]
---
# T058 — dyn Trait: vtables and dynamic dispatch

## Goal
Explicit dynamic dispatch.

## Scope
- dyn compatibility rules, coercion to dyn, vtable layout (spec'd), dispatch in interp.

## Acceptance
- [ ] run + ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T058-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
