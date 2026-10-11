---
id: T129
title: Advanced Control Flow Cleanup
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T128]
priority: 69
status: todo
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
---
# T129 — Advanced Control Flow Cleanup

## Goal
Implement cleanup on complex control flow paths.

## Scope
- Cleanup on return, break, continue, `?`, and panic-abort paths.

## Acceptance
- Complex control flow does not leak variables.
- Appropriate cleanups generated correctly.

## Notes
- Created as part of splitting T049 (ADR-0027).
