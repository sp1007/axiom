---
id: T057
title: Closures, capture inference, function values
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
depends: [T056]
priority: 77
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/own, bootstrap/axiom0/src/mir, tests/run/closure, tests/ui/closure]
spec: [0060, 0069, 0273, tasks/0290, tasks/0671]
---
# T057 — Closures, capture inference, function values

## Goal
Closures without runtime objects by default.

## Scope
- Closure syntax → HIR, capture inference (copy / view / mut_view / move by usage), closure types, Fn-like traits per spec, fn pointers, passing closures to generic fns.

## Acceptance
- [ ] run + ui tests incl. capture conflicts.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T057-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
