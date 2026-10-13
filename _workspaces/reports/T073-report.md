# Task T073: HashMap, HashSet, and iterator adapters

## Summary
Implemented `HashMap`, `HashSet`, and iterator adapters for Axiom stdlib per ADR-0004 §4 and task T073 specification:
- **`HashMap` (`std/collections/hash_map.ax`)**:
  - Dense insertion-order index-map layout (`AxRawMap`), identical to C kernel (`bootstrap/axiom0/src/kernel/hashmap.c`).
  - Iteration sequence strictly follows insertion order (dense array traversal).
  - Open addressing with linear probing and power-of-two capacity for the index table.
  - AXH64 hash function (`ax_hash_u32`, `ax_hash_bytes`) conforming to T069.
  - Tombstone marking on removal (`AX_MAP_TOMBSTONE = 0xFFFFFFFF`).
  - Automatic compaction when `dead >= 8` and `dead * 2 >= len`, preserving relative insertion order of surviving entries and rebuilding the index table.
  - Monomorphic implementations for `U32Map` (integer key/value) and `StrU32Map` (string key, u32 value).
- **`HashSet` (`std/collections/hash_set.ax`)**:
  - Dense insertion-order index-set layout (`AxRawSet`) matching ADR-0004 §4.
  - Deduplication on insert (returns `false` if value already present, preserving original index and order).
  - Tombstone tracking and compaction identical to `HashMap`.
  - Monomorphic implementations for `U32Set` and `StrSet`.
- **UTF-8 Chars Iterators (`std/text/chars/chars.ax`)**:
  - `Chars`: yields Unicode scalar values (`char`) decoding 1 to 4 byte UTF-8 sequences.
  - `CharIndices`: yields `CharIndex { offset: usize, ch: char }` with exact byte offsets matching char boundaries.
  - Verified `"Xin chào thế giới".chars().count() == 17`.
- **Iterator Adapters (`std/core/iter/adapters/`)**:
  - `vec_iter.ax`: `VecI32`, `VecIterI32`, `vec_iter_next_i32`.
  - `map.ax`: `MapI32` adapter applying transformation `f: fn(i32) -> i32` over iterator items.
  - `filter.ax`: `FilterI32` adapter filtering items with predicate `pred: fn(i32) -> bool`.
  - `enumerate.ax`: `EnumerateI32` yielding `EnumerateItemI32 { index: usize, value: i32 }`.
  - `zip.ax`: `ZipI32` yielding `ZipItemI32 { a: i32, b: i32 }`.
- **Test Suite (`tests/std/collections/`)**:
  - `qa_chars.ax`: UTF-8 decoding, character counting (`17`), boundary byte offsets.
  - `qa_hash_map_order.ax`: Exact T007 C kernel sequence (`kernel_hashmap_order_after_delete_reinsert`), in-place updates, tombstone reinsert append, and compaction order preservation.
  - `qa_hash_map_growth.ax`: 150 items insertion, geometric capacity growth, retrieval, exact iteration order, clear, and reuse.
  - `qa_hash_set.ax`: Insertion, deduplication, order preservation, removal, reinsertion, clear, and reuse.
  - `qa_iter_adapters.ax`: VecIter, map, filter, enumerate, zip, and vector collection.
  - 100% pass across all execution modes: `interp`, `native`, and `native-O1`.

## Files changed
- std/collections/hash_map.ax
- std/collections/hash_set.ax
- std/core/iter/adapters/enumerate.ax
- std/core/iter/adapters/filter.ax
- std/core/iter/adapters/map.ax
- std/core/iter/adapters/vec_iter.ax
- std/core/iter/adapters/zip.ax
- std/text/chars/chars.ax
- tests/std/collections/qa_chars.ax
- tests/std/collections/qa_hash_map_growth.ax
- tests/std/collections/qa_hash_map_order.ax
- tests/std/collections/qa_hash_set.ax
- tests/std/collections/qa_iter_adapters.ax

## Verification
- All 14 tests in `tests/std/collections/` pass across `interp`, `native`, and `native-O1` (14/14 PASS).
- Exact T007 C kernel insertion order verified.
- `"Xin chào thế giới".chars().count() == 17` and byte boundary offsets verified.
- Geometric growth, index rebuilding, and compaction verified.
- Global regression suite run: 0 regressions from T073 changes.
- Isolated snapshot worktree `build-snap-T073` verified with `taskctl.py snapshot T073`.

## Follow-ups / Compiler Findings
1. **Win64 ABI hidden return pointer clobber**: For struct returns larger than 8 bytes, functions with multiple parameters or inner calls can experience hidden RCX return pointer register clobbers in native code generation (`isel.c`). Iterator adapters are instantiated via struct literals rather than factory functions returning structs by value.
2. **Interpreter boolean expression evaluation**: When evaluating boolean conditions with nested function calls in non-leaf expressions, interpreter evaluates overflows eagerly unless decoupled.

STATUS: COMPLETE round=0
