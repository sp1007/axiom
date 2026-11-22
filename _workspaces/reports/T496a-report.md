# T496a report — inclusive sub-range `s[a..=b]` / `s[..=b]` (ADR-0045)

## Root cause
The parser, AST, HIR lowering (`compiler/hir/lower.ax`) and typeck all carry `HirExpr.is_inclusive` for a range in index
brackets, but `mb_build_range_subslice_lvalue` in `compiler/mir/builder.ax` never read
it: `s[a..=b]` was lowered exactly like `s[a..b]` (bounds check `b <= len`, projection end `b`), so `len(s[0..=2])` was 2 in
every mode. A second silent case: the parser accepts `a..=` with no end (it shares `is_range_end` with `a..`), and the
builder then lowered `s[1..=]` as `s[1..]` (printed 7 for an 8-element slice) although SPEC-02 AXS-GRM-070 says `a..=` is a
syntax error.

## Fix
`compiler/mir/builder.ax`
- `mb_build_range_subslice_lvalue`: `end_inclusive = has_end && idx_arg.is_inclusive`. The bound check is
  `mb_emit_range_bounds_check(..., end_inclusive, ...)`; after it (and after the ADR-0044 §1 truncation of 128-bit bounds)
  an inclusive end is turned into the exclusive end `b + 1` computed in `usize` (new `mb_emit_usize_add_one`), which cannot
  overflow because `b < len` was asserted. Then `a <= b + 1` is asserted on usize values (the start was already checked
  `<= len`, so its truncation is exact), and the sub-slice projection uses `b + 1`.
- `mb_emit_range_bounds_check`: new `end_inclusive` parameter; the end is checked with `LT` instead of `LE` (in u128 for a
  128-bit bound, in usize otherwise, exactly as ADR-0045 requires: `b < len` in the bound's own width, never `b + 1 <= len`).
  For an inclusive range it returns before its own `start <= end` check (the caller does `start <= end + 1`). Exclusive
  ranges are lowered byte-for-byte as before.
- New `mb_range_base_is_checked` (array / view / mut_view / slice / str) shared by both functions.

MIR of `len(s[lo..=hi])` (usize bounds):
```
_7 = copy _2 as usize; _6 = copy _7 <= copy _5; assert(... "index out of bounds")   // lo <= len
_9 = copy _3 as usize; _8 = copy _9 < copy _5;  assert(... "index out of bounds")   // hi < len
_10 = copy _3 as usize; _11 = copy _10 + const 1usize; _12 = copy _2 as usize;
_13 = copy _12 <= copy _11; assert(... "index out of bounds")                       // lo <= hi + 1
... subslice [_2 .. _11]
```

`compiler/hir/lower.ax`
- A range with `is_inclusive` and no end now reports `AX_PARSE_EXPECTED_EXPR` ("inclusive range needs an end bound after
  ..="). Decision: the right place is the parser (`compiler/syntax/parse.ax`), which is outside this task's paths; lowering
  is the earliest pass in my paths that sees every range expression, the code is the existing "expected expression" parse
  code (no new code, as ADR-0045 says), and it closes the silent `s[a..=]` == `s[a..]` mis-slice. Follow-up suggestion
  (optional): move the check into `parse_binary_suffix` when parse.ax is next touched.

`compiler/types/typeck.ax`: not changed (typeck already accepts both forms and types them as the exclusive forms).

## Tests
- `tests/run/slice_inclusive/` (all three modes, exact `stdout:` + `exit:`; traps also `stderr-contains: index out of bounds`):
  - `basic_view.ax`: `s[0..=2]`, `s[..=2]`, `s[k..=k]`, `s[k..=k-1]` (empty), `s[k..=len-1]` on `view<[i32]>`.
  - `bound_types.ax`: u8 / i32 / usize / u64 / u128 / i128 bounds, prefix forms, mixed widths (u128..=i32, u8..=i128),
    end = len - 1, empty ranges `3..=2`, `8..=7` (u128, start == len), `1..=0`.
  - `array_and_mut_view.ax`: `[N]T` base; writes through `mut_view` inclusive sub-slices (`v[1..=3]`, `w[4u64..=4u64]`,
    `u[..=0u128]`) reach element `b`.
  - 12 trap tests: `trap_end_eq_len_usize`, `trap_prefix_end_eq_len`, `trap_end_eq_len_u8` (b == len),
    `trap_end_usize_max`, `trap_prefix_end_usize_max`, `trap_end_u64_max`, `trap_end_u128_max`, `trap_end_u128_alias`
    (2^64 + 2), `trap_end_i128_negative`, `trap_end_i32_negative` (b = -1 so b + 1 would be 0), `trap_start_gt_end_plus_one`
    (usize 5..=3), `trap_start_gt_end_plus_one_u128` (7..=2).
- `tests/ui/slice_inclusive/inclusive_without_end.ax`: `s[1..=2]`, `s[..=2]`, `s[1..]` accepted; `s[1..=]` rejected with
  `AX_PARSE_EXPECTED_EXPR`.
- Mutation evidence: with the HEAD compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O1_b64ea0de4626c290.exe`)
  19 of 46 test runs FAIL (basic_view, bound_types, array_and_mut_view, the three `b == len` traps in all 3 modes, and the
  ui test); with the fix all 46 PASS. The MAX / negative / a > b + 1 traps already trapped at HEAD (b > len) and guard
  against a naive `b + 1` lowering.

## Results (snapshot `build-snap-T496a`, HEAD 5e38733 + this change)
- `python tools/build_axiomc.py --out build`: STAGE2/STAGE3 (O1) OK, FIXED-POINT (O1) OK (sha256 3ec4d671894f28a7),
  STAGE0-GUARD OK (log `_workspaces/T496a_build.log`).
- `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -j 2 --filter slice_inclusive/`:
  `TOTAL 46 PASS 46 FAIL 0`, WEAK-NATIVE 0.
- `python tools/taskgate.py --task T496a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  `TOTAL 416 PASS 414 FAIL 0 SKIP 2 XFAIL 0`, BASELINE OK, failing ids none, archcheck clean (232 files, 0 violations),
  WEAK-NATIVE 0 in the task's own/changed tests (3 elsewhere in the run). TASKGATE exit=0. (Log tail in
  `_workspaces/T496a_taskgate.log`.)
- Acceptance groups `--gate -j 2 --filter run/ --filter conformance/p12/ --filter selfhost/mir --filter ui/slice`:
  `TOTAL 3522 PASS 3522 FAIL 0 SKIP 0 XFAIL 0` (includes all of `tests/run`, `run/index_128_range`, `conformance/p12`,
  selfhost mir groups); WEAK-NATIVE 122 are pre-existing tests outside this task (own tests 0) (log `_workspaces/T496a_suites.log`).

## Files changed
- compiler/mir/builder.ax
- compiler/hir/lower.ax
- tests/run/slice_inclusive/basic_view.ax
- tests/run/slice_inclusive/bound_types.ax
- tests/run/slice_inclusive/array_and_mut_view.ax
- tests/run/slice_inclusive/trap_end_eq_len_usize.ax
- tests/run/slice_inclusive/trap_prefix_end_eq_len.ax
- tests/run/slice_inclusive/trap_end_eq_len_u8.ax
- tests/run/slice_inclusive/trap_end_usize_max.ax
- tests/run/slice_inclusive/trap_prefix_end_usize_max.ax
- tests/run/slice_inclusive/trap_end_u64_max.ax
- tests/run/slice_inclusive/trap_end_u128_max.ax
- tests/run/slice_inclusive/trap_end_u128_alias.ax
- tests/run/slice_inclusive/trap_end_i128_negative.ax
- tests/run/slice_inclusive/trap_end_i32_negative.ax
- tests/run/slice_inclusive/trap_start_gt_end_plus_one.ax
- tests/run/slice_inclusive/trap_start_gt_end_plus_one_u128.ax
- tests/ui/slice_inclusive/inclusive_without_end.ax

STATUS: COMPLETE round=0
