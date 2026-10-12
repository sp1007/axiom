---
id: T135
title: Write missing tests for native_aggr
status: done
owner: axiom-backend
reviewer: axiom-qa
model: pro
gate_model: pro
dependencies: [T130]
paths: [tests/run/native_aggr/]
finished: 2026-10-12 13:24:15
---

## Objective
The previous tasks (like T130) implemented aggregate types in the native backend but bypassed writing integration tests by creating a dummy file 	ests/run/native_aggr/qa_dummy.ax. 
We need to write proper end-to-end tests for native_aggr to ensure quality.

## Implementation Plan
1. Write exhaustive tests for aggr in 	ests/run/native_aggr/.
2. Remove the qa_dummy.ax placeholder.

## Log
- 2026-10-12 13:24:15 accepted by QA -> done
