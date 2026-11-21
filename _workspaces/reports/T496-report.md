# T496 report — 128-bit index / range-bound bounds check (ADR-0044 §1)

## Summary
`a[i]` and `a[lo..hi]` with an `i128`/`u128` index or bound used to be lowered as `Cast(IntToInt, i, usize)` followed by
`idx_usize < len`, so `2^64 + 1` aliased element 1 (interp, native -O0, native -O1). The MIR builder now follows
SPEC-40 AXS-INT-053/054 as amended by ADR-0044 §1: for a 128-bit index type the value is reinterpreted as `u128`
(a bit-cast for `i128`, so negatives become `>= 2^127`), compared in `u128` against `Cast(len, u128)`, asserted with the
existing `index out of bounds` message, and only after the assert is it cast to `usize` for `MIR_PROJ_INDEX` /
`MIR_PROJ_SUBSLICE`. Widths <= 64 bits keep the old (exact) lowering byte-for-byte; the compiler binary is unchanged
(stage-2 sha256 identical to the HEAD seed), fixed point stage2 == stage3 OK.

MIR of `fn at(a: view<[8]i32>, i: i128) -> i32 { (*a)[i] }` (snapshot `axiomc2 inspect --emit=mir`):
```
_3 = copy _2 as u128;   _4 = const 8;   _5 = copy _4 as u128;
_6 = copy _3 < copy _5; assert(copy _6 == true, "index out of bounds") -> bb1
bb1: _7 = copy _3 as usize; _0 = copy (*(_1))[_7];
```
Both compare operands are `u128` (INV-INT-003 holds).

## Implementation (`compiler/mir/builder.ax`)
- `mb_expr_as_usize_local` gains an out-param `wide_out`: for `u128`/`i128` it materialises the value in a `u128` temp
  (copy for `u128`, IntToInt cast for `i128`), returns local 0 and does not truncate.
- New `mb_wide_index_to_usize`: the post-check `Cast(IntToInt, idx_u128, usize)`.
- `mb_emit_index_bounds_check(..., idx_wide_v, ...)`: wide path emits `len_u128 = len as u128; c = idx_u128 < len_u128; assert`.
- `mb_emit_range_bounds_check(..., start_wide_v, end_wide_v, ...)`: each wide bound is checked `bound_u128 <= len_u128`;
  if any bound is wide the `start <= end` check is done in `u128` (a narrow bound is widened from its usize local; both
  are already `<= len` there, so the result equals the usize compare). Non-wide ranges unchanged.
- `mb_emit_range_le_assert` now delegates to the new `mb_emit_range_cmp_assert(cmp_op, ...)` (LE / LT).
- Callers (`HIR_EXPR_INDEX` lvalue, `mb_build_range_subslice_lvalue`) emit the cast after the check. When the base type
  has no bounds check (early return), the cast is still emitted, so lowering stays total.

## Decisions
- `i128` reinterpretation uses the existing IntToInt cast `i128 -> u128` (same width = bit-cast in interp and native);
  no new MIR construct needed.
- Mixed-width ranges (`s[lo_u128..hi_i32]`) are accepted by typeck today; the start<=end check widens the narrow bound
  rather than truncating the wide one, matching the ADR's "check in the index's own width".

## Tests
- Generator `tests/run/numeric/mixed_int_matrix/gen_matrix.py`: the three `index_trap_*128_alias*` entries no longer pass
  the `xfail` argument; regenerated (only those three files changed). Helper `repro_u128_index_alias.ax` deleted.
- New `tests/run/index_128_range/` (all three modes, exact `stdout:` + `exit:`; traps also `stderr-contains: index out of bounds`):
  `range_end_u128_alias.ax` (end 2^64+2), `range_start_i128_alias.ax` (start -(2^64)+1), `range_open_start_u128_alias.ax`
  (`s[lo..]`, lo 2^127+4), `range_start_gt_end_u128.ax` (5..3 in u128), `in_range_128.ax` (in-range u128/i128 index on array,
  view and slice, index assignment, mixed-width ranges, edge bounds 0/len/empty).
- Mutation evidence: with the HEAD compiler (`compiler-cache/axiomc2_O1_68241a2055f60a08.exe`) the 3 former xfail tests and
  the 3 new alias range tests FAIL in all 3 modes (18 failures, exit 0 instead of 101); with the fix all pass.

## Results (snapshot `build-snap-T496`, HEAD d5dbc94 + this change)
- `python tools/build_axiomc.py --out build`: STAGE1/2/3 OK, FIXED-POINT (O1) OK, STAGE0-GUARD OK (log `_workspaces/T496_build.log`).
- `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -j 2 --filter index_128_range/`: 15/15 PASS, WEAK-NATIVE 0.
- `python tools/taskgate.py --task T496 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  `TOTAL 535 PASS 527 FAIL 0 SKIP 2 XFAIL 6`, BASELINE OK, failing ids none, archcheck clean, WEAK-NATIVE 0 in own/changed
  tests (log `_workspaces/T496_taskgate.log`, JSON `_workspaces/artifacts/taskgate-T496.json`). Included selfhost groups mir,
  verify, own_mir_verify, opt, interp, interp_opt, lir, backend, drop, driver, intrinsics, obj_link_driver.
- Acceptance groups `--filter run/numeric/ --filter conformance/p12/ --filter selfhost/typeck/ --filter run/index`:
  `TOTAL 1284 PASS 1278 FAIL 0 SKIP 0 XFAIL 6`, WEAK-NATIVE 0 (log `_workspaces/T496_suites.log`). The 6 XFAIL are
  `array_copy.ax` (T498) and `tilde_widening.ax` (T499) — other tasks' xfails; no T496 xfail remains.

## Files changed
- compiler/mir/builder.ax
- tests/run/numeric/mixed_int_matrix/gen_matrix.py
- tests/run/numeric/mixed_int_matrix/index_trap_u128_alias.ax
- tests/run/numeric/mixed_int_matrix/index_trap_u128_alias_hi.ax
- tests/run/numeric/mixed_int_matrix/index_trap_i128_alias.ax
- tests/run/numeric/mixed_int_matrix/repro_u128_index_alias.ax
- tests/run/index_128_range/in_range_128.ax
- tests/run/index_128_range/range_end_u128_alias.ax
- tests/run/index_128_range/range_start_i128_alias.ax
- tests/run/index_128_range/range_open_start_u128_alias.ax
- tests/run/index_128_range/range_start_gt_end_u128.ax

STATUS: COMPLETE round=0
