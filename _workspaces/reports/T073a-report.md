# Task T073a: Arenas and typed ID tables (Axiom library for the compiler data model)

## Summary
Implemented phase-owned Arena bump allocator, typed ID newtypes pattern, dense `IdTable`, and hash-consing `Interner` in Axiom for the self-hosted compiler data model per tasks/0260 (ABOOT-52..57) and 0172 (AKERNEL-24):

- **Arena bump allocator (`std/core/arena/arena.ax`)**:
  - `Arena` bump allocator with dynamic chunk allocation (`AX_ARENA_DEFAULT_CHUNK_CAP = 65536`).
  - Allocation headers / chunk chaining via intrusive `ArenaChunk` metadata.
  - Explicit `reset(mut_view(a))` resetting chunk pointer and byte offset to the initial chunk without deallocating ($O(1)$ reuse matching C `kernel/arena.c`).
  - Explicit `destroy(mut_view(a))` and `impl Drop for Arena` deallocating all OS chunks via `ax_mem_free`, returning allocator counters (`chunks_in_use`) to 0.
  - Preserves pointer provenance in interpreter mode by performing typed pointer offset arithmetic (`(*cur).data + off`) rather than integer address casts, avoiding $O(N)$ allocation search overhead.
  - Stored-view and non-aliasing rules documented and adhered to (SPEC-11 / ADR-0004).
- **Arena Architecture Documentation (`std/core/arena/README.md`)**:
  - Documents phase-owned arena lifecycles across compiler phases (lexing/parsing, type checking, IR lowering, code generation).
  - Documents borrow/view conventions, prohibition of storing views in heap structs, and arena reset safety.
- **Typed IDs & IdTable (`std/collections/idtable/id_table.ax`)**:
  - Typed ID newtypes pattern: `StrId`, `FileId`, `NodeId`, `SymbolId`, `TypeId`, with `.none()` returning index 0 (`AX_ID_NONE = 0`).
  - `RawIdTable` & `U32IdTable`: dense 1-based indexing (`push` returning typed ID), contiguous dense storage, insertion-order iteration, `get` and `get_mut` bounds-checked view accesses, capacity reservation.
  - `StrInterner`: deduplicating string slices into unique `StrId`s, using AXH64 deterministic byte hashing (`ax_hash_bytes`), power-of-two open-addressing index hash table, and dedicated arena storage for interned string bytes.
  - `U32Interner`: deduplicating 32-bit values into unique `u32` IDs using AXH64 integer hashing (`ax_hash_u32`).
  - Avoids 64-byte `AxInterpValue` interpreter return aggregate truncation by providing `interner_init(mut_view(in_))` in-place initialization matching C kernel conventions (`ax_interner_init`).
  - Replaced `* 2` on `usize` with `+` to evade backend `UMUL_OVERFLOW` bug.
- **IdTable Architecture Documentation (`std/collections/idtable/README.md`)**:
  - Documents dense 1-based indexing, cache-friendly array traversal, pointer-elimination advantages, and determinism guarantees.
- **Test Suite (`tests/std/arena/`)**:
  - `qa_arena_alloc.ax`: Base allocation, alignments (1, 2, 4, 8, 16), chunk growth across chunk boundaries, reset reuse, drop cleanup. (interp, native, native-O1).
  - `qa_arena_scale_native.ax`: 1,000,000 allocations natively, chunk metrics, reset reuse, drop returning allocator counters back to zero. (native, native-O1).
  - `qa_arena_scale_interp.ax`: 10,000 allocations twin in interpreter mode, reset reuse, drop allocator counter validation. (interp).
  - `qa_idtable.ax`: `RawIdTable` and `U32IdTable`, dense 1-based IDs, get/get_mut via views, insertion-order iteration, bounds checks, capacity growth. (interp, native, native-O1).
  - `qa_interner.ax`: `StrInterner` and `U32Interner`, identity (same key returns same ID), distinct keys yield distinct IDs, insertion-order iteration, determinism across separate runs. (interp, native, native-O1).
  - `qa_ast_arena.ax`: Mini "AST in an arena" tree construction (binary expressions, literals, variables, statements), recursive evaluation and traversal in interp, native, and native-O1.

## Files changed
- std/collections/idtable/README.md
- std/collections/idtable/id_table.ax
- std/core/arena/README.md
- std/core/arena/arena.ax
- tests/std/arena/qa_arena_alloc.ax
- tests/std/arena/qa_arena_scale_interp.ax
- tests/std/arena/qa_arena_scale_native.ax
- tests/std/arena/qa_ast_arena.ax
- tests/std/arena/qa_idtable.ax
- tests/std/arena/qa_interner.ax

## Verification
- All 15 test variants in `tests/std/arena/` pass across `interp`, `native`, and `native-O1` (15/15 PASS):
  - `qa_arena_alloc`: interp PASS, native PASS, native-O1 PASS.
  - `qa_arena_scale_native`: native PASS, native-O1 PASS (1,000,000 allocations verified).
  - `qa_arena_scale_interp`: interp PASS (10,000 allocations verified).
  - `qa_idtable`: interp PASS, native PASS, native-O1 PASS.
  - `qa_interner`: interp PASS, native PASS, native-O1 PASS.
  - `qa_ast_arena`: interp PASS, native PASS, native-O1 PASS.
- Full test suite run (`tools/axtest.py --compiler build/axiom0.exe`): zero regressions across all existing tests.
- Task validation (`taskctl.py changes T073a`): passes clean approval.

## Compiler & Interpreter Findings
1. **Interpreter Aggregate Return Value Limit (64 bytes)**:
   In `bootstrap/axiom0/src/interp/host.h`, `AxInterpValue` is defined as `uint64_t vals[8]` (64 bytes). Returning structs larger than 64 bytes by value (such as `StrInterner` containing an embedded `Arena`, size > 100 bytes) truncates the return value in `interp.c:654, 1534`, corrupting trailing fields. Solved by providing in-place initialization `interner_init(in_: mut_view<StrInterner>)` matching C kernel convention `ax_interner_init(AxStrInterner *in)`.
2. **Interpreter Pointer Provenance**:
   Casting `(c_addr + off) as *mut u8` strips allocation tagging and causes `ax_interp_validate_raw_ptr` to linearly scan all allocations in `ctx->allocs` on every dereference ($O(N)$ overhead). Preserving pointer provenance via typed pointer arithmetic `(*cur).data + off` maintains constant-time pointer checks.
3. **Interpreter String Literal Pointer Dereference**:
   In `interp.c`, `*(bytes + offset)` triggers `error[AX_UNSAFE_INTERP_UB]` if `bytes` references constant string literal memory instead of a registered heap/stack allocation. In interpreter tests, test strings copied into arena buffers before byte hashing avoid this limitation.
4. **View Non-Aliasing in Function Call Arguments (`AX_CAP_CONFLICT_MUT`)**:
   Nested expressions passing `mut_view(arena)` into inner arguments of outer functions also taking `mut_view(arena)` are rejected by the capability checker. Allocating nodes into separate sequential local variables before passing to composite constructors cleanly avoids capability conflicts.

STATUS: COMPLETE round=0
