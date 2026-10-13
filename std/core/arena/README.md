# Arena Allocation for the Compiler Data Model

## Overview

The `Arena` is an aligned bump-pointer allocator over a linked list of heap chunks, mirroring the C stage-0 implementation in `bootstrap/axiom0/src/kernel/arena.c` and adhering to tasks/0260 ABOOT-49..53 and 0172 AKERNEL-24.

Phases in the self-hosted Axiom compiler (AST parsing, HIR lowering, MIR generation, backend lowering) allocate intermediate syntax nodes, IR instructions, and string spellings into phase-owned arenas.

## Lifecycle & Phase Boundaries

1. **Phase Ownership**:
   Each compiler phase or function worker owns its `Arena`.
   ```axiom
   let mut arena = Arena.new();
   ```

2. **Phase Boundary Reclamation**:
   - `arena.reset()`: Discards all allocated objects, keeps the first chunk's memory buffer for reuse in the next phase/function, and frees all subsequent chunks to the host heap. This amortises host heap overhead across compilation units without accumulating memory.
   - `arena.destroy()` (or automatic `Drop`): Releases all chunks (including the initial chunk) back to the system heap. Allocator counters return to zero.

3. **Determinism Invariant (INV-KERN-002 / INV-KERN-003)**:
   - All memory returned by `arena_alloc_raw` is zeroed out prior to returning. Fresh objects never depend on previous allocator history or uninitialised bytes.
   - An arena memory address is storage only, never an identity: AST/HIR/MIR nodes are identified by typed IDs (`NodeId`, `FileId`, `SymbolId`), never raw memory addresses.

4. **Stored-View Safety (SPEC-11 / T045)**:
   - Arena-owned data follows Axiom's capability and stored-view rules.
   - Arena allocations do not escape past the arena lifetime; references to arena memory are passed inward via views/capabilities, eliminating any need for garbage collection (GC) or reference counting (RC).
