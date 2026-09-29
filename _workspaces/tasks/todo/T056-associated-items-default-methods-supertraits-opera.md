---
id: T056
title: Associated items, default methods, supertraits, operator traits, derive
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
depends: [T055]
priority: 76
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/traits, bootstrap/axiom0/src/types, tests/run/trait2, tests/ui/trait2]
spec: [0066, 0305, tasks/0476]
---
# T056 — Associated items, default methods, supertraits, operator traits, derive

## Goal
Complete the trait feature set used by the standard library.

## Scope
- Associated types (`Self.Item`) and consts, default methods, supertraits, operator traits (Add/Sub/…/Eq/Ord/Index) with `&&`/`||` staying short-circuit, `@derive(Copy, Clone, Eq, Debug?)` basic.

## Acceptance
- [ ] run + ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T056-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
