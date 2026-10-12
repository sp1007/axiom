---
id: T138
title: Write missing tests for native_own
status: doing
dependencies: [T129]
paths: [tests/run/native_own/]
---

## Objective
The previous tasks implemented own type in the native backend but bypassed writing integration tests by creating a dummy file 	ests/run/native_own/qa_dummy.ax. 
We need to write proper end-to-end tests for 
ative_own to ensure quality.

## Implementation Plan
1. Write exhaustive tests for own types in 	ests/run/native_own/.
2. Remove the qa_dummy.ax placeholder.
