---
id: T138
title: Write missing tests for native_own
phase: P6-ownership
status: done
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 70
depends: [T129]
paths: [tests/run/native_own/]
finished: 2026-10-12 13:34:56
---

## Objective
The previous tasks implemented own type in the native backend but bypassed writing integration tests by creating a dummy file tests/run/native_own/qa_dummy.ax. 
We need to write proper end-to-end tests for native_own to ensure quality.

## Acceptance
- [x] Exhaustive tests for own types in tests/run/native_own/ pass.
- [x] Remove the qa_dummy.ax placeholder.

## Log
- 2026-10-12 13:34:56 accepted by QA -> done
