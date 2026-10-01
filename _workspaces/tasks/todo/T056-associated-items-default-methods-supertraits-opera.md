---
id: T056
title: Associated items, default methods, supertraits, operator traits, derive
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T055]
priority: 76
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/traits, bootstrap/axiom0/src/types, tests/run/trait2, tests/ui/trait2]
locks: [bootstrap/axiom0/src/diag/codes/TRAIT.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0066, tasks/0305, tasks/0476]
---
# T056 — Associated items, default methods, supertraits, operator traits, derive

## Goal
Complete the trait feature set used by the standard library.

## Scope
- Associated types (`Self.Item`) and consts, default methods, supertraits, operator traits (Add/Sub/…/Eq/Ord/Index) with `&&`/`||` staying short-circuit, `@derive(Copy, Clone, Eq, PartialEq, Ord, Hash)` (ADR-0004 §6: interning keys and deterministic sort keys in the compiler need Hash/Ord; `Debug` and the reflection-based derive framework are E14.2).

## Acceptance
- [ ] run + ui tests, incl. a derived `Hash` + `Eq` struct used as a key and a derived `Ord` used for sorting; run tests carry `// native-after: T059`.
- [ ] At least one positive run test and one negative ui test per Scope bullet; the report maps each bullet to its test files (QA checks the map).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T056-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
