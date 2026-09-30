---
id: T061
title: Const items and constant expressions (via the MIR interpreter)
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T059]
priority: 81
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types/const, tests/run/comptime, tests/ui/comptime]
spec: [0102, 0140, 0274, tasks/0509, tasks/0346]
---
# T061 — Const items and constant expressions

## Goal
Compile-time evaluation reusing the oracle (no separate mini-language).

## Scope
- `const` items and constant expressions (array sizes, tables) evaluated by the MIR interpreter, evaluation limits and diagnostics. `comptime fn`, `comptime {}` blocks, const generics and reflection are E14.1/E14.2 (after self-hosting, ROADMAP R7) — but keep the evaluator reusable so they plug in without redesign.

## Acceptance
- [ ] run + ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T061-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
