---
id: T035d
title: Struct layout engine
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T035a]
priority: 55
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types/layout, bootstrap/axiom0/src/types, tests/unit/types]
spec: [0059, 0081, 0043, tasks/0267, tasks/0281, 0009]
---
# T035d — Struct layout engine

## Goal
Implement layout engine for structs (size, align, field offsets).

## Scope
- Layout (size/align/field offsets, default repr rules per spec), `@repr(C)` layout.

## Acceptance
- [ ] Layout unit tests pass.
- [ ] Report `_workspaces/reports/T035d-report.md`.
