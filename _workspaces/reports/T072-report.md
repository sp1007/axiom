# Task T072: Iterator protocol, for-loop desugaring, ranges

## Summary
Implemented the Iterator protocol, range types, and for-loop desugaring in the Axiom compiler:
- **`std/core/iter/iter.ax`**:
  - Defined `@lang("Iterator") pub trait Iterator { type Item; fn next(self: mut_view<Self>) -> Option<Self.Item>; }`.
  - Implemented `Range<T>` and `RangeInclusive<T>` with `@derive(Copy)`.
  - Implemented `Iterator` for `Range<i32>` and `RangeInclusive<i32>`.
- **`bootstrap/axiom0/src/types/typeck.c`**:
  - Implemented AST desugaring for `for` loops (`desugar_for`) and range literals (`desugar_range`):
    - Half-open (`start..end`) and inclusive (`start..=end`) range literals desugar directly to efficient induction while loops.
    - `Range` and `RangeInclusive` struct variables desugar to induction while loops.
    - Arrays and slice views (`view<[T]>`) desugar to index-based while loops using `len` and array indexing.
    - General iterators desugar to `while let Option.Some(pat) = __iter.next()`.
  - Enhanced `lookup_path_type` to resolve `Self.<AssocType>` and `Self` references within trait definitions and implementations.
  - Fixed type variable leakage in `find_method` by restoring `cx->int_vars_len` after method lookup on generic impl candidates.
  - Fixed struct literal type resolution in `AX_HIR_EXPR_STRUCT` to resolve generic arguments to concrete types, ensuring derive-generated `Copy` checks correctly recognize copyable fields.
- **Tests**:
  - `tests/run/for/test_for_range.ax`: Range loops, inclusive range loops, negative ranges, empty ranges, break/continue.
  - `tests/run/for/test_for_array.ax`: Array literal loops, array variable loops, slice view (`view<[T]>`) loops, subslice loops, break/continue.
  - `tests/run/for/test_for_custom_iter.ax`: Custom iterators (`Counter`, `StepCounter`, `PointGen`) implementing `Iterator` with `next(self: mut_view<Self>) -> Option<T>`.
  - `tests/run/for/test_range_standalone.ax`: Range struct instantiation, field access (`r.start`, `r.end`), and iterating range variables.

## Files changed
- bootstrap/axiom0/src/types/typeck.c
- std/core/iter/iter.ax
- tests/run/for/test_for_array.ax
- tests/run/for/test_for_custom_iter.ax
- tests/run/for/test_for_range.ax
- tests/run/for/test_range_standalone.ax

## Verification
- Built compiler with warning-free flags: 0 warnings, 0 errors.
- Checked standard library file: `axiom0 check std/core/iter/iter.ax` passes with 0 errors.
- Target test suite: `python tools/axtest.py --compiler build-snap-T072/build/axiom0.exe --filter run/for -v` -> 12 PASS, 0 FAIL (interp, native, native-O1).
- Full regression suite: `python tools/axtest.py --compiler build-snap-T072/build/axiom0.exe --root build-snap-T072` -> TOTAL 1396 PASS 1374 FAIL 0 SKIP 22 XFAIL 0.

STATUS: COMPLETE round=0
