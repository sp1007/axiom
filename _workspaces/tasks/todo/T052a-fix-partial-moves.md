---
id: T052a
title: Compiler fix: Partial moves invalidate whole struct
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-architect
model: opus
depends: []
priority: 72
status: todo
paths: [src/compiler/semantics]
---
# T052a — Compiler fix: Partial moves invalidate whole struct

## Goal
Fix the compiler so that a partial move out of a struct invalidates the entire struct aggregate.

## Scope
- Update the semantics pass so that when a field (e.g., `user.name`) is moved, the root symbol (`user`) is marked as invalid for by-value use.

## Acceptance
- `tests/conformance/adversarial/partial_002.ax` correctly fails with `AX_MOVE_USE_AFTER_MOVE`.
