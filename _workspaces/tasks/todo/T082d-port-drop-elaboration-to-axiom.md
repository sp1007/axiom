---
id: T082d
title: Port drop elaboration and cleanup edges to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082c]
priority: 116
status: todo
attempts: 0
paths: [compiler/mir/drop.ax, tests/selfhost/drop]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRP-183]
---
# T082d — Port drop elaboration and cleanup edges to Axiom

## Goal
Port drop elaboration, drop flag tracking, and cleanup blocks (`compiler/mir/drop.ax`) from C to Axiom.

## Scope
- Port drop flag synthesis for conditionally moved variables.
- Port insertion of drop terminators at scope exit, returns, break, and panic edges.
- Port synthesis of destructor calls for compound structures and generic containers.
- Unit tests under `tests/selfhost/drop/`.

## Acceptance
- [ ] Drop elaboration implemented in `compiler/mir/drop.ax` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Elaborated drop calls and cleanup CFG blocks match `axiom0 inspect --emit=mir`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082d-report.md` with exact `## Files changed`.

## Out of scope
- MIR verification (handled in T082e).

## Notes
- `model: opus`: Drop elaboration requires semantic precision (model policy).
- Sub-task of T082 split per ADR-0005 §8 and SPEC-20 §4.6.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
