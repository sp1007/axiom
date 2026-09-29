---
id: T072
title: Iterator protocol, for-loop desugaring, ranges
phase: P9-stdlib
owner: axiom-semantics
reviewer: axiom-qa
depends: [T069]
priority: 103
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/hir, bootstrap/axiom0/src/types, std/core/iter, tests/run/for]
spec: [tasks/0333, tasks/0476, 0045]
---
# T072 — Iterator protocol, for-loop desugaring, ranges

## Goal
`for x in iter` via the Iterator lang item.

## Scope
- Iterator trait (`fn next(self: mut_view<Self>) -> Option<Self.Item>`), for desugaring in HIR, Range/RangeInclusive, iteration over arrays/views.

## Acceptance
- [ ] run tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T072-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
