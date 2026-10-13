---
id: T082b
title: Port ownership move analysis and definite initialization to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082a]
priority: 116
status: todo
attempts: 0
paths: [compiler/own/move.ax, compiler/own/init.ax, tests/selfhost/own]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-OWN-338]
---
# T082b — Port ownership move analysis and definite initialization to Axiom

## Goal
Port ownership move/copy analysis and definite initialization analysis (`compiler/own/`) from C to Axiom.

## Scope
- Port place model, move paths, liveness bitsets, and use-after-move detection.
- Port definite initialization analysis across all CFG edges and loops.
- Unit tests under `tests/selfhost/own/`.

## Acceptance
- [ ] Move and initialization analyses implemented in `compiler/own/` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Move and initialization diagnostics match `axiom0` on error test fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082b-report.md` with exact `## Files changed`.

## Out of scope
- Capability analysis and drop elaboration (handled in T082c and T082d).

## Notes
- `model: opus`: Ownership and initialization analyses require semantic precision (model policy).
- Sub-task of T082 split per ADR-0005 §8 and SPEC-20 §4.6.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
