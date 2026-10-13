---
id: T080a
title: Port resolver and module graph to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T079]
priority: 114
status: todo
attempts: 0
paths: [compiler/resolve, tests/selfhost/resolve]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-MOD-142, REQ-PKG-023, REQ-RES-243]
---
# T080a — Port resolver and module graph to Axiom

## Goal
Port name resolver, scoping ribs, and module graph (`compiler/resolve/`) from C to Axiom.

## Scope
- Port lexical scoping ribs, symbol table, multi-file module loader, `use` import resolution, and visibility checks.
- Match resolution rules from `bootstrap/axiom0/src/resolve/`.
- Unit tests under `tests/selfhost/resolve/`.

## Acceptance
- [ ] Resolver implemented in `compiler/resolve/` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Symbol resolution diagnostics match `axiom0` on resolution error fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T080a-report.md` with exact `## Files changed`.

## Out of scope
- HIR lowering (handled in T080b).

## Notes
- Sub-task of T080 split per ADR-0005 §8 and SPEC-20 §4.4.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
