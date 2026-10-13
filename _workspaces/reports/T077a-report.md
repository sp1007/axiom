# T077a Report: Port kernel to Axiom

## Task Summary
Ported the Axiom compiler kernel from C to pure Axiom under `compiler/kernel/`, covering hashing (`AXH64`), bump arena allocation, typed IDs with ID tables, string/u32 interner, and dynamic arrays. Fully validated across interpreter, native, and native-O1 modes.

## Files changed
- compiler/kernel/arena.ax
- compiler/kernel/dynarray.ax
- compiler/kernel/hash.ax
- compiler/kernel/id.ax
- compiler/kernel/interner.ax
- compiler/kernel/mod.ax
- tests/selfhost/kernel/qa_kernel_arena.ax
- tests/selfhost/kernel/qa_kernel_dynarray.ax
- tests/selfhost/kernel/qa_kernel_hash.ax
- tests/selfhost/kernel/qa_kernel_id.ax
- tests/selfhost/kernel/qa_kernel_interner.ax

## Key Deliverables & Validation
1. **AXH64 Hashing (`compiler/kernel/hash.ax`)**:
   - Implemented exact AXH64 algorithm per ADR-0004 §4 and `bootstrap/axiom0/src/kernel/hash.c`.
   - Dual-mode support with `@intrinsic` declarations for `wrapping_add_u64`, `wrapping_mul_u64`, and `rotate_left_u64`.
   - `AxHasher`, `ax_hash_bytes`, `ax_hash_u32`, `ax_hash_u64`, `ax_hash_combine`, `ax_rotl64`.
   - Verified 100% byte-for-byte against reference vectors in `tests/selfhost/kernel/qa_kernel_hash.ax`.

2. **Arena Bump Allocator (`compiler/kernel/arena.ax`)**:
   - Geometric chunk allocation with configurable chunk sizes, alignment handling, and request accounting.
   - `arena_alloc_raw`, `arena_alloc`, `arena_alloc_array`, `arena_dup`, `arena_reset`, `arena_destroy`.
   - `impl Drop for Arena` for automatic resource cleanup.
   - Verified in `tests/selfhost/kernel/qa_kernel_arena.ax` across interpreter, native, and native-O1.

3. **Typed IDs & ID Tables (`compiler/kernel/id.ax`)**:
   - Value types `StrId`, `FileId`, `NodeId`, `SymbolId`, `TypeId` with 1-based indexing (`0` is None).
   - Dense `RawIdTable` and `U32IdTable` supporting push, get, set, contains, and iteration (`first`, `after`).
   - Verified in `tests/selfhost/kernel/qa_kernel_id.ax`.

4. **Interner (`compiler/kernel/interner.ax`)**:
   - `StrInterner` backed by `Arena` and open-addressing quadratic probe hash table.
   - `U32Interner` for 32-bit values.
   - Inlined hash map growth with deduplication and fast lookups.
   - Verified in `tests/selfhost/kernel/qa_kernel_interner.ax`.

5. **DynArray (`compiler/kernel/dynarray.ax`)**:
   - `RawDynArray` and `U32DynArray` with dynamic growth, push, pop, get, set, and clear.
   - Verified in `tests/selfhost/kernel/qa_kernel_dynarray.ax`.

6. **Acceptance Criteria & Metrics**:
   - Line count: 1,359 lines (budget ≤ 1,500 lines).
   - Test suite: 15/15 passing across `[interp]`, `[native]`, and `[native-O1]`.
   - Archcheck: 0 violations across 188 files.
   - Harness check: OK.

STATUS: COMPLETE round=0
