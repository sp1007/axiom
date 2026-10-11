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
status: done
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir, tests/run/slice]
attempts: 1
started: 2026-10-12 04:07:39
finished: 2026-10-12 06:05:00
---
# T131 — Implicit Block Drop and Destructors

## Goal
Implement implicit drop elaboration for simple block scopes and destructors.

## Scope
- Destructors in the final surface form `impl Drop for S { fn drop(self: mut_view<S>) { ... } }`.
- Destructor symbols must be mangled as `<Type>_drop` (e.g., `S_drop`) in MIR/LIR (ADR-0032).
- Simple basic block cleanup (implicit drops) for nominal types.
- EXPLICITLY EXCLUDED: Array and aggregate element-wise drops (deferred to T130).

## Acceptance
- Drop order observable via print in run tests for basic scopes.

## Notes
- Created as part of rescoping T128 (ADR-0029).

## Log
- 2026-10-12 04:07:39 started (attempt 1) 
- 2026-10-12 06:05:00 accepted by QA -> done
