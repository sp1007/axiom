## Files changed

STATUS: BLOCKED The updated scope (@derive, associated types, etc.) requires frontend and syntax support before semantic checking can begin. Specifically, `@derive` is a macro/attribute expansion feature that must be implemented in `axiom-syntax` to lower into `impl` blocks. `axiom-semantics` operates on HIR, and cannot expand `@derive` attributes. Please have `axiom-frontend` implement `@derive` lowering and `axiom-syntax` provide the necessary AST nodes for operator traits and supertraits before unblocking this task.
