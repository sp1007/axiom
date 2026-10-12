---
id: T054
title: Generics: type checking and inference
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T053]
priority: 74
status: done
attempts: 0
paths: [bootstrap/axiom0/src, tests/typeck/generic, tests/ui/generic]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0083, tasks/0271, tasks/0506, tasks/0354, 0042]
finished: 2026-10-12 17:41:37
---
# T054 — Generics: type checking and inference

## Goal
Generic functions and types in the type checker. Monomorphization, mangling and generic drop glue are T054b (split, ADR-0005 §8).

## Scope
- Generic parameters on fns, structs, enums and impls; explicit type arguments (`f<T>(x)`, `Vec<i32>.new()`); inference of type arguments; generic struct/enum construction and field/variant typing; bounds are parsed and stored (checked by T055).
- Typed HIR carries the substitution of every generic use (input of T054b).

## Acceptance
- [ ] ui tests (wrong number of type arguments, cannot infer, mismatched instantiation) and THIR golden tests showing the substitutions.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T054-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-12 17:41:37 accepted by QA -> done
