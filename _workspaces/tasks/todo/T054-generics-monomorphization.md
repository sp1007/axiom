---
id: T054
title: Generics + monomorphization
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T053]
priority: 74
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/traits/mono, bootstrap/axiom0/src/mir, tests/run/generic, tests/ui/generic]
spec: [0083, tasks/0271, tasks/0506, tasks/0354, 0042]
---
# T054 — Generics + monomorphization

## Goal
Generic functions/types with static dispatch via monomorphization.

## Scope
- Generic params, inference of type args, generic structs/enums, instance collection, MIR instantiation, symbol mangling scheme (spec'd), Option<T>/Result<T,E> made truly generic (retire T039 shortcut).

## Acceptance
- [ ] run + ui tests; instance dedup test; mangling deterministic.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T054-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
