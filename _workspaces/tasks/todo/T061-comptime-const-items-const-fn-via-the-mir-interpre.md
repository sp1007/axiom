---
id: T061
title: Comptime: const items, const fn via the MIR interpreter
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
depends: [T059]
priority: 81
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types/const, tests/run/comptime, tests/ui/comptime]
spec: [0102, 0140, 0274, tasks/0509, tasks/0346]
---
# T061 — Comptime: const items, const fn via the MIR interpreter

## Goal
Compile-time evaluation reusing the oracle (no separate mini-language).

## Scope
- const items, `comptime fn`, `comptime {}` blocks, const generics for array sizes if in spec, evaluation limits and diagnostics.

## Acceptance
- [ ] run + ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T061-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
