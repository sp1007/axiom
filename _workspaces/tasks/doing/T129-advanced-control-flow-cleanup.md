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
status: doing
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
attempts: 1
started: 2026-10-11 20:08:43
agent: T129-impl
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

## Log
- 2026-10-11 20:08:43 started (attempt 1) T129-impl
