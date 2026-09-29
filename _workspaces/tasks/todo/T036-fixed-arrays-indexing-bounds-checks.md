---
id: T036
title: Fixed arrays, indexing, bounds checks
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T035]
priority: 56
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/array, tests/ui/array]
spec: [tasks/0476, tasks/0326, 0087]
---
# T036 — Fixed arrays, indexing, bounds checks

## Goal
`[N]T` arrays with safe indexing.

## Scope
- Array literals, repeat literals if spec'd, indexing read/write, bounds checks → panic, arrays of structs, arrays in structs, `len`.

## Acceptance
- [ ] run tests incl. out-of-bounds abort exit code; ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T036-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
