# ADR-0006: Ownership Semantics - Partial Moves and View Lifetimes

## Context
Task T052 revealed confusion around two semantic edge cases:
1. Partial moves: When a field of a struct is moved out, the compiler currently still allows using the whole struct.
2. View lifetimes: The `e003.ax` stress test expects the compiler to accept a mutable view after the last use of an immutable view, requiring "last-use analysis" (NLL).

## Options Considered
1. Implement full borrow checking (NLL, fine-grained field tracking).
2. Stick to the frozen semantic model: "ownership ≠ borrow checker", deterministic, simple capabilities.

## Decision
We enforce the simple capability model:
1. **Partial moves invalidate the root:** Moving a field out of a struct invalidates the entire aggregate. The struct can no longer be passed or used by value as a whole.
2. **Lexical lifetimes only, no NLL:** Axiom does not perform "last-use analysis". Views have strictly lexical scopes. A view remains active until the end of its block, meaning a conflict will correctly occur if a mutable view is requested in the same scope.

## Consequences
- The compiler must be updated to mark the parent struct as invalid when a field is moved (Fixing `partial_002.ax`).
- The `e003.ax` test is based on a flawed assumption. It must be updated to either use explicit block scoping or expect `AX_CAP_CONFLICT_MUT`.
