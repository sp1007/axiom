---
id: T017
title: Type interner + typeck for the bootstrap subset (typed HIR)
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
depends: [T015, T003]
priority: 30
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, tests/typeck, tests/ui/typeck]
spec: [0157, 0175, 0245, tasks/0388, tasks/0482, spec/SPEC-03-core-semantics.md]
---
# T017 — Type interner + typeck for the bootstrap subset (typed HIR)

## Goal
Type the subset: integers (all widths), bool, unit, never, functions, let (annotated/inferred), literals, operators, if/while/loop/return, calls.

## Scope
- TypeInterner (hash-consed TypeId), primitive types, function types.
- Local inference with literal defaulting per SPEC-03; no implicit conversions; operator typing table.
- Typed HIR (THIR) with a type on every expression; `inspect --emit=thir`.
- Diagnostics: AX_TYPE_MISMATCH, AX_TYPE_UNKNOWN, AX_TYPE_NOT_CALLABLE, AX_TYPE_ARG_COUNT, AX_TYPE_RETURN…

## Acceptance
- [ ] First negative test `return true` in i32 fn → AX_TYPE_MISMATCH.
- [ ] ui tests for each rule; golden THIR tests; i32→i64 assignment rejected.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T017-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
