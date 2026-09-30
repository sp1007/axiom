---
id: T034
title: Numeric types, casts, checked arithmetic, panic=abort
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T033]
priority: 54
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/numeric, tests/ui/numeric]
spec: [tasks/0327, tasks/0334, spec/SPEC-03-core-semantics.md, 0068]
---
# T034 — Numeric types, casts, checked arithmetic, panic=abort

## Goal
All integer widths, bool ops, `as` casts, overflow/div-zero/shift semantics exactly per SPEC-03; f32/f64 basic arithmetic if SPEC-00 schedules it here.

## Scope
- Cast rules table, checked ops emitting MIR assert/panic terminators, panic intrinsic → abort path with the defined exit code.

## Acceptance
- [ ] Boundary-value run tests per width (MIN, MAX, overflow edges) in interp.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T034-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
