---
id: T132
title: Frontend explicit drop builtin
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T127]
priority: 68
status: done
attempts: 1
paths: [bootstrap/axiom0/src/resolve, bootstrap/axiom0/src/types, tests/ui, tests/run/drop, tests/hir, tests/mir, tests/resolve, tests/typeck]
started: 2026-10-11 19:00:19
finished: 2026-10-11 19:30:05
---
## Goal
Add the explicit `drop` builtin to the frontend (name resolution, type checking) and update all affected golden tests.

## Scope
- Add `"drop"` builtin to the prelude and name resolution.
- Add type checking support for `drop(x)`.
- Fix the 11 broken golden tests caused by symbol ID shifts from adding the builtin.

## Acceptance
- Name resolution and type checking for `drop(x)` compile correctly.
- All golden tests in `tests/ui` and `tests/run/drop` pass.

## Out of scope
- MIR generation and execution for `drop` (handled by T128).
- Block cleanup and destructors.

## Notes
- Extracted from T128 to fix scope violations and test regressions (ADR-0030).
## Log
- 2026-10-11 19:00:19 started (attempt 1) T132-impl
- 2026-10-11 19:30:05 accepted by QA -> done
