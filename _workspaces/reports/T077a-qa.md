# QA Report: T077a

## Round 0
- 15/15 test variants under tests/selfhost/kernel/ pass across interp, native-O0, native-O1.
- Kernel hash test vectors match exact ADR-0004 reference test vectors.
- Arena allocation, geometric growth, alignment, reset, and drop cleanup fully verified.
- Typed ID tables and dynamic arrays verified with dynamic resizing and element indexing.
- String and U32 interners verified with deduplication and open-addressing hash table lookup.
- Total kernel line count: 1,359 lines (well below the limit of 1,500 lines).
- `git grep -rn "native-after: T077a" tests` returns 0 hits.
- archcheck: 188 files scanned, 0 violations.
- reqcov --strict: COVERAGE OK (covers REQ-DRV-020).
- harness_check.py: HARNESS OK.
- taskctl changes: 0 refused files.

VERDICT: PASS round=0
