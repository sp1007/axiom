---
id: T130
title: Aggregates and Conditional Moves
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T129]
priority: 69
status: todo
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
---
# T130 — Aggregates and Conditional Moves

## Goal
Implement drop flags for conditional moves and field-wise drop of aggregates/enums.

## Scope
- Drop flags for conditional moves.
- Field-wise drop for structs, tuples, and enums.

## Acceptance
- Field-wise drops correctly executed.
- Conditional drop triggers appropriately based on flags.

## Notes
- Created as part of splitting T049 (ADR-0027).
