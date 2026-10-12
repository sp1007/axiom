---
gate_model: none
id: T052c
title: Fix drop() use-after-move bug
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-architect
model: opus
depends: []
priority: 71
status: doing
paths: [src/semantics]
attempts: 1
started: 2026-10-12 11:37:28
---
gate_model: none
# T052c — Fix drop() use-after-move bug

## Goal
Fix compiler bug where explicit `drop()` fails to trigger `AX_MOVE_USE_AFTER_MOVE`.

## Scope
- Ensure that `drop(b)` correctly moves `b` and any subsequent uses trigger the correct move error, as found in `own_branch_003.ax`.

## Log
- 2026-10-12 11:37:28 started (attempt 1) 

## Acceptance
All tests pass.
