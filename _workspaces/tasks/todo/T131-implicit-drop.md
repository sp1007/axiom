---
id: T131
title: Implicit Block Drop and Destructors
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
# T131 — Implicit Block Drop and Destructors

## Goal
Implement implicit drop elaboration for simple block scopes and destructors.

## Scope
- Destructors in the final surface form `impl Drop for S { fn drop(self: mut_view<S>) { ... } }`.
- Simple basic block cleanup (implicit drops).

## Acceptance
- Drop order observable via print in run tests for basic scopes.

## Notes
- Created as part of rescoping T128 (ADR-0029).
