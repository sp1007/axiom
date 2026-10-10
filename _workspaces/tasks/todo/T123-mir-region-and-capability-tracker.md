---
id: T123
title: MIR region representation and capability tracker
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T047]
priority: 67
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/regions, bootstrap/axiom0/src/mir/cap, tests/ui/mir]
locks: [bootstrap/axiom0/src/diag/codes/MIR.def]
spec: [spec/SPEC-11-capability.md, spec/decisions/ADR-0024-capability-tracker.md]
---
# T123 — MIR region representation and capability tracker

## Goal
Implement the foundational data structures and dataflow analyses in MIR for region representation and capability tracking.

## Scope
- Define MIR region representations.
- Implement the capability tracker structure to support region relations (DISJOINT, SAME, CONTAINS, OVERLAPS, UNKNOWN).
- Prepare infrastructure for conflict detection to be used by type-level capability rules.

## Acceptance
- [ ] MIR data structures for regions are implemented.
- [ ] Capability tracker correctly models region relations.
- [ ] Unit and basic UI tests for the dataflow passes pass.

## Out of scope
- Frontend type checking rules for views/mut_view (this is left to T048).

## Notes
- Created as a prerequisite for T048 per ADR-0024.
