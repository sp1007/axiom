---
id: T081a
title: Port types data model, interner & layout to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T080]
priority: 115
status: todo
attempts: 0
paths: [compiler/types/types.ax, compiler/types/layout.ax, tests/selfhost/types]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-TYP-354]
---
# T081a — Port types data model, interner & layout to Axiom

## Goal
Port TypeKind definitions, type interner, and target memory layout calculation (`compiler/types/`) from C to Axiom.

## Scope
- Port primitive types, compound types (struct, tuple, enum, array, slice), pointer/view types, and function types.
- Port type interning table and TypeId allocations.
- Port layout calculation: size, alignment, field offsets, and enum discriminant layout.
- Unit tests under `tests/selfhost/types/`.

## Acceptance
- [ ] Types data model implemented in `compiler/types/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Type size, alignment, and field offsets match `axiom0` layout calculations.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T081a-report.md` with exact `## Files changed`.

## Out of scope
- Trait solving and type checking (handled in T081b and T081c).

## Notes
- `model: opus`: Porting the type system requires semantic precision (model policy).
- Sub-task of T081 split per ADR-0005 §8 and SPEC-20 §4.5.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
