---
id: T032
title: Functions: multiple fns, recursion, params, returns
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T031]
priority: 52
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/fn, tests/ui/fn]
spec: [0069, 0266, tasks/0284]
---
# T032 — Functions: multiple fns, recursion, params, returns

## Goal
Full function semantics in the oracle.

## Scope
- Order-independent item use, recursion/mutual recursion, many params, unit fns, early return, argument evaluation order.

## Acceptance
- [ ] run + ui tests in interp mode.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T032-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
