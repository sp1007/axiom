---
id: T135
title: Write missing tests for native_aggr
phase: P6-ownership
status: done
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 70
depends: [T130]
paths: [tests/run/native_aggr/]
finished: 2026-10-12 13:24:15
---

## Objective
The previous tasks (like T130) implemented aggregate types in the native backend but bypassed writing integration tests by creating a dummy file tests/run/native_aggr/qa_dummy.ax. 
We need to write proper end-to-end tests for native_aggr to ensure quality.

## Acceptance
- [x] Exhaustive tests for aggr in tests/run/native_aggr/ pass.
- [x] Remove the qa_dummy.ax placeholder.

## Log
- 2026-10-12 13:24:15 accepted by QA -> done
