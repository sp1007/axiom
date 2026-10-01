---
id: T035
title: Structs, tuples, layout engine
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T034]
priority: 55
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types/layout, bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/struct, tests/ui/struct]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0059, 0081, 0043, tasks/0267, tasks/0281, 0009]
---
# T035 — Structs, tuples, layout engine

## Goal
Aggregate data through the oracle with a layout engine the backend will use.

## Scope
- Struct decl/literal/field read/write, nested structs, tuples + `.0`, struct params/returns by value, layout (size/align/field offsets, default repr rules per spec), `@repr(C)` layout.

## Acceptance
- [ ] run tests (0263 §37 Point test) + ui tests (unknown field, missing field) + layout unit tests. Run tests carry `// native-after: T037` (removed by T037).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T035-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
