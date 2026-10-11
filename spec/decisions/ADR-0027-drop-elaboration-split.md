# ADR-0027: Split Drop Elaboration Task (T049)

## Context
Task T049 (Drop elaboration + cleanup on every edge) failed QA 3 times due to hallucinated logic in `builder.c` and `interp.c`, GCC compilation errors (e.g., `AxMirBb` missing `stmt_cap`), and layer violations. The root cause is that the task's scope is too large for a single implementation step. It encompasses MIR infrastructure, control flow edge cleanup, drop flags, conditional moves, and field-wise aggregation drop. Attempting to implement all of this simultaneously overwhelms the LLM, leading to structural errors and layer violations.

## Decision
We will split T049 into smaller, incremental tasks that build upon each other:

1. **T127 (MIR Infrastructure for Drop):** Extend MIR data structures to support drop statements, drop flags, and drop terminators. This establishes the structural foundation without implementing complex elaboration logic.
2. **T128 (Basic Drop Elaboration):** Implement drop elaboration for simple block scopes, explicit `drop(x)`, and nominal types.
3. **T129 (Advanced Control Flow Cleanup):** Implement cleanup on complex control flow paths (`return`, `break`, `continue`, `?`, panic-abort).
4. **T130 (Aggregates and Conditional Moves):** Implement drop flags for conditional moves and field-wise drop of aggregates/enums.

T049 will be superseded by T127, T128, T129, and T130.

## Consequences
- **Positive:** Each task has a focused, manageable scope, reducing hallucination and compilation errors.
- **Negative:** Slightly increases the administrative overhead of task management.
