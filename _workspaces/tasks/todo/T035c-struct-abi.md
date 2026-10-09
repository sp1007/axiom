---
id: T035c
title: Structs ABI and linkage
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T035d, T035e]
priority: 55
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/abi, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/link, bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target]
spec: [0059, 0081, 0043, tasks/0267, tasks/0281, 0009]
---
# T035c — Structs ABI and linkage

## Goal
Implement ABI and linkages for struct params/returns by value.

## Scope
- Struct params/returns by value, C ABI handling, linkages.

## Acceptance
- [ ] Backend tests for ABI and linkages.
- [ ] Full test suite passes.
- [ ] Report `_workspaces/reports/T035c-report.md`.

## Notes
- Third part of original T035.
