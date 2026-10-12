---
id: T136
title: Write missing tests for native_enum
status: todo
dependencies: [T130]
paths: [tests/run/native_enum/]
---

## Objective
The previous tasks (like T130) implemented aggregate types in the native backend but bypassed writing integration tests by creating a dummy file 	ests/run/native_enum/qa_dummy.ax. 
We need to write proper end-to-end tests for native_enum to ensure quality.

## Implementation Plan
1. Write exhaustive tests for enum in 	ests/run/native_enum/.
2. Remove the qa_dummy.ax placeholder.
