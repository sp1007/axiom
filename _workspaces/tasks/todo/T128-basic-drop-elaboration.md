---
id: T128
title: Basic Drop Elaboration
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T127]
priority: 69
status: todo
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
---
# T128 — Basic Drop Elaboration

## Goal
Implement drop elaboration for simple block scopes, explicit `drop(x)`, and nominal types.

## Scope
- Destructors in the final surface form `impl Drop for S { fn drop(self: mut_view<S>) { ... } }`.
- Basic explicit `drop(x)` builtin.
- Simple basic block cleanup.

## Acceptance
- Drop order observable via print in run tests for basic scopes.

## Notes
- Created as part of splitting T049 (ADR-0027).
