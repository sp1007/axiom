---
id: T128
title: Explicit Drop Builtin
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T127, T132]
priority: 69
status: done
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir]
unblocks: 2
attempts: 1
started: 2026-10-11 19:30:27
finished: 2026-10-11 20:08:26
---
# T128 — Explicit Drop Builtin

## Goal
Implement drop elaboration for explicit `drop(x)` only, ignoring block cleanup and destructors for now.

## Scope
- Basic explicit `drop(x)` builtin.

## Acceptance
- Explicit drop operations are observable via print in run tests (e.g., interpreter logs dropping behavior for primitives or structs).

## Notes
- Created as part of splitting T049 (ADR-0027).

## Log
- 2026-10-11 14:20:33 block: QA failed 3 times: persistent double-drop bugs, regressions masked by unauthorized golden test modifications, logic errors.
- 2026-10-11 14:22:27 unblocked (cycle 1) 
- 2026-10-11 14:23:58 started (attempt 1) T128-impl
- 2026-10-11 18:57:27 block: QA failed 3 times: Scope violations outside locks, 11 broken golden tests, missing print observation
- 2026-10-11 18:59:26 unblocked (cycle 2) 
- 2026-10-11 19:30:27 started (attempt 1) T128-impl
- 2026-10-11 20:08:26 accepted by QA -> done
