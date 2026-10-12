---
id: T137
title: Write missing tests for native_str
status: todo
dependencies: [T130]
paths: [tests/run/native_str/]
---

## Objective
The previous tasks (like T130) implemented aggregate types in the native backend but bypassed writing integration tests by creating a dummy file 	ests/run/native_str/qa_dummy.ax. 
We need to write proper end-to-end tests for native_str to ensure quality.

## Implementation Plan
1. Write exhaustive tests for str in 	ests/run/native_str/.
2. Remove the qa_dummy.ax placeholder.
