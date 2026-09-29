---
id: T038
title: Enums + match + exhaustiveness
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T036]
priority: 58
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types/match, tests/run/enum, tests/ui/enum]
spec: [0065, 0268, tasks/0392, tasks/0504]
---
# T038 — Enums + match + exhaustiveness

## Goal
Algebraic data types and pattern matching.

## Scope
- Enum decl (unit/tuple/struct variants), variant construction via dotted paths, layout (tag + payload), match with all pattern kinds, guards if in spec, exhaustiveness + unreachable-arm analysis (AX_MATCH_NONEXHAUSTIVE with missing patterns listed).

## Acceptance
- [ ] run + ui tests incl. nested patterns and exhaustiveness counter-examples.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T038-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
