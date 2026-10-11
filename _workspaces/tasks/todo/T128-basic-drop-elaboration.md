---
id: T128
title: Explicit Drop Builtin
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T127]
priority: 69
status: todo
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
unblocks: 1
attempts: 0
---
# T128 — Explicit Drop Builtin

## Goal
Implement drop elaboration for explicit `drop(x)` only, ignoring block cleanup and destructors for now.

## Scope
- Basic explicit `drop(x)` builtin.

## Acceptance
- Explicit drop operations are observable via print in run tests.

## Notes
- Created as part of splitting T049 (ADR-0027).

## Log
- 2026-10-11 14:20:33 block: QA failed 3 times: persistent double-drop bugs, regressions masked by unauthorized golden test modifications, logic errors.
- 2026-10-11 14:22:27 unblocked (cycle 1) 
