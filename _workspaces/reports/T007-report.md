# T007 report
## Summary
Implemented the deterministic, allocation-disciplined data structures for all compiler phases.
Features added include Typed ID macro pattern (`IdTable`), `Arena` (aligned bump allocator), `Vec` (type-safe macro wrapper), `HashMap` (open addressing, deterministic iteration order = insertion order), `StrView`/`StrBuf`, `StringInterner` → `StrId`, stable 64-bit hash algorithm, and UTF-8 decode/validate helpers. Provided macro implementations of `AX_ICE` and `AX_ASSERT`.

## Round 1
Fixed issues from `T007-qa.md`:
- Applied `AX_MAYBE_UNUSED` (which wraps `__attribute__((unused))`) to `static inline` functions inside `AX_DEFINE_VEC`, `AX_DEFINE_HASHMAP`, `AX_DEFINE_ID`, and `AX_DEFINE_ID_TABLE` to prevent `-Wunused-function` warnings in Clang builds.
- Updated `bootstrap/axiom0/src/kernel/README.md` to properly document the AXH64 v1 hash algorithm (wrapping 64-bit operations) and the HashMap iteration contract.
- Added QA test `qa_test_vec_reserve.c`.

## Tests
- Run `tools/axtest.py --compiler build/axiom0.exe` in snapshot build dir
- Results: TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0
  - tests/unit/kernel/kernel_unit.test passes (which runs all `test_*.c` functions).
  - tests/unit/kernel/hash_vectors_current.test passes, confirming hash compatibility with > 32 vectors, including `Xin chào thế giới`.
- Clang builds successfully warning-free.

## Spec deviations
none

## Follow-ups
none

## Files changed
- bootstrap/axiom0/src/kernel/README.md
- bootstrap/axiom0/src/kernel/arena.c
- bootstrap/axiom0/src/kernel/arena.h
- bootstrap/axiom0/src/kernel/base.c
- bootstrap/axiom0/src/kernel/base.h
- bootstrap/axiom0/src/kernel/hash.c
- bootstrap/axiom0/src/kernel/hash.h
- bootstrap/axiom0/src/kernel/hashmap.c
- bootstrap/axiom0/src/kernel/hashmap.h
- bootstrap/axiom0/src/kernel/id.h
- bootstrap/axiom0/src/kernel/interner.c
- bootstrap/axiom0/src/kernel/interner.h
- bootstrap/axiom0/src/kernel/kernel.h
- bootstrap/axiom0/src/kernel/str.c
- bootstrap/axiom0/src/kernel/str.h
- bootstrap/axiom0/src/kernel/utf8.c
- bootstrap/axiom0/src/kernel/utf8.h
- bootstrap/axiom0/src/kernel/vec.h
- tests/unit/kernel/arena_align_ice.test
- tests/unit/kernel/assert_banner.test
- tests/unit/kernel/cdriver_ice.c
- tests/unit/kernel/gen_hash_vectors.py
- tests/unit/kernel/hash_vectors.txt
- tests/unit/kernel/hash_vectors_current.test
- tests/unit/kernel/ice_banner.test
- tests/unit/kernel/idtable_none_ice.test
- tests/unit/kernel/idtable_range_ice.test
- tests/unit/kernel/interner_none_ice.test
- tests/unit/kernel/kernel_unit.test
- tests/unit/kernel/qa_test_vec_reserve.c
- tests/unit/kernel/test_arena.c
- tests/unit/kernel/test_hash.c
- tests/unit/kernel/test_hashmap.c
- tests/unit/kernel/test_id.c
- tests/unit/kernel/test_interner.c
- tests/unit/kernel/test_str.c
- tests/unit/kernel/test_utf8.c
- tests/unit/kernel/test_vec.c
- tests/unit/kernel/vec_range_ice.test

STATUS: COMPLETE round=1
