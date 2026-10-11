---
id: T127
title: MIR Infrastructure for Drop
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T048b]
priority: 69
status: todo
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
---
# T127 — MIR Infrastructure for Drop

## Goal
Extend MIR data structures to support drop statements, drop flags, and drop terminators.

## Scope
- Update `AxMirBb` to include `stmt_cap` or appropriate structures to handle larger statement lists.
- Introduce drop terminators and drop statements in the MIR definition.
- Establish the structural foundation for drop elaboration without implementing complex elaboration logic.

## Acceptance
- MIR data structures correctly support drop constructs.
- Builds without GCC compilation errors.

## Notes
- Created as part of splitting T049 (ADR-0027).
