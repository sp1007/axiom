---
id: T035e
title: Struct MIR and oracle execution
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T035d]
priority: 55
status: done
attempts: 1
paths: [bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/struct]
spec: [0059, 0081, 0043, tasks/0267, tasks/0281, 0009]
started: 2026-10-09 13:05:10
finished: 2026-10-09 13:33:33
---
# T035e — Struct MIR and oracle execution

## Goal
MIR emission and oracle interpretation for structs.

## Scope
- MIR emission for structs.
- Oracle interpretation for structs.

## Acceptance
- [ ] run tests (0263 §37 Point test). Run tests carry `// native-after: T037`.
- [ ] Report `_workspaces/reports/T035e-report.md`.

## Log
- 2026-10-09 13:05:10 started (attempt 1) T035e-impl
- 2026-10-09 13:33:33 accepted by QA -> done
