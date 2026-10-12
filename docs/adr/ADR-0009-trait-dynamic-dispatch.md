# ADR-0009: Trait Dynamic Dispatch Deferred

## Tóm tắt
Dynamic dispatch (trait objects, vtables, `dyn Trait`) is separated from the core trait system implementation (associated items, default methods, derive). Dynamic dispatch is deferred to a later phase to unblock immediate trait dependencies. The task filename `T056-traits-dynamic-dispatch-vtables.md` was misleading; dynamic dispatch implementation details for C11 will be specified in a future task.

## Context
During the implementation of T056, the agent was blocked because the task filename mentioned "dynamic-dispatch-vtables", but the actual task scope only covered associated items, default methods, supertraits, operator traits, and derive. The C11 implementation details for dynamic dispatch were missing from the task scope and specs, leading to confusion.

## Decision
1. Dynamic dispatch implementation (vtables, `dyn Trait` in C11) is explicitly deferred to a later dedicated task.
2. T056 will strictly focus on the static aspects of traits: associated items, default methods, supertraits, operator traits, and derive.
3. In the future, dynamic dispatch in C11 will likely be implemented using fat pointers (a struct containing a void pointer to the data and a pointer to the vtable struct), but this design will be finalized in the subsequent task.

## Consequences
- Unblocks T056 by clarifying the scope.
- Prevents agents from attempting to implement dynamic dispatch without complete C11 specifications.

## Sources
- T056 task description.
