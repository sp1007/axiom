---
id: T038
title: Enums + match + exhaustiveness
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T036]
priority: 58
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types/match, tests/run/enum, tests/ui/enum]
locks: [bootstrap/axiom0/src/diag/codes/PAT.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0065, tasks/0268, tasks/0392, tasks/0504]
---
# T038 — Enums + match + exhaustiveness

## Goal
Algebraic data types and pattern matching.

## Scope
- Enum declarations (unit/tuple/struct variants), variant construction via dotted paths, layout (tag + payload), `enum as uN` for fieldless enums (ADR-0004 §7).
- `match` with variant, binding, wildcard, tuple, struct and nested patterns; exhaustiveness + unreachable-arm analysis over these forms (AX_PAT_NONEXHAUSTIVE with the missing patterns listed, AX_PAT_UNREACHABLE).
- Literal / range / or-patterns, guards, `if let` / `while let` / `let … else` and destructuring `let` are T038b.

## Acceptance
- [ ] run + ui tests incl. nested patterns and exhaustiveness counter-examples, written with user-defined enums only (for example `enum Maybe { Some(i32), None }`) — Option arrives in T039.
- [ ] `enum as u8` test for a fieldless enum; a cast of an enum with payload is rejected.
- [ ] Run tests carry `// native-after: T040` (removed by T040).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T038-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
