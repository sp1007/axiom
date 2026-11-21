# T454 report - E12.1 std.core.num complete integer API, fallible conversions, endian bytes, 128-bit formatting

## Summary

All of SPEC-40 AXS-INT-022..026, 031, 032, 033 is delivered as Axiom source in `std/`, plus the lossless/fallible
conversions of AXS-INT-042/043 with two documented deviations (below).  Every test runs the live std sources under
`run --interp`, native `-O0` and native `-O1` and the three legs must agree.  The work found six compiler bugs; five still have a
minimal `xfail` repro in `tests/std/num/`; the sixth (trait impl selection ignores i128/u128) is fixed in round 1.

- `std/core/num.ax` (generated, 4841 lines): for each of the 12 integer types an `impl` with
  - `min`, `max`, `clamp`, `abs_diff`, `pow`;
  - wrapping: `wrapping_div/rem/shl/shr/pow` (+ `wrapping_abs` signed);
  - saturating: `saturating_div/pow` (+ `saturating_neg/abs` signed);
  - checked: `checked_add/sub/mul/div/rem/neg/shl/shr/pow` (+ `checked_abs` signed);
  - overflowing: `overflowing_add/sub/mul/div/rem/neg/shl/shr/pow` (+ `overflowing_abs` signed);
  - bits: `count_zeros`, `leading_ones`, `trailing_ones`;
  - bytes: `to_le/be/ne_bytes`, `from_le/be/ne_bytes` as `[N]u8` with N = 1, 2, 4, 8, 16;
  - signed: `abs`, `unsigned_abs`, `signum`, `is_positive`, `is_negative`;
  - unsigned: `is_power_of_two`, `next_power_of_two` (panics "arithmetic overflow" above 2^(BITS-1)), `checked_next_power_of_two`.
  The members the compiler already provides on every integer type (`wrapping_add/sub/mul/neg`, `saturating_add/sub/mul`,
  `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones`, `swap_bytes`, `reverse_bits`, `T.MIN/MAX/BITS`) are
  not redefined; the old suffixed `@intrinsic fn wrapping_add_i32 ...` declarations and the duplicate `impl` methods
  were removed (nothing imported them) and the tests exercise all of them on all 12 types.  `char.from_u32` is kept.
- `std/core/convert.ax` (generated, 898 lines): `TryFromIntError` (Clone, PartialEq, Eq, `@derive(Copy)`), the generic
  traits `From<T>`, `Into<T>`, `TryFrom<T>`, `TryInto<T>`, and on all 12 integer types the inherent
  `Dst.from(x)` (lossless pairs of AXS-INT-042, `bool` included, checked at compile time) and `Dst.try_from(x)` (any integer
  source, range-checked).  Lossy `from` is rejected with `AX_TRAIT_UNSATISFIED_BOUND` (three compile-fail tests).
- `std/text/fmt/int.ax`: `format_u128_into/format_i128_into`, `format_u128/i128`, `_dec`, `_dec_padded`, `format_u128_hex/bin/oct`,
  `format_u128_radix/format_i128_radix`, `format_u128_prefixed` (0x, 0b, 0o), `parse_u128_radix/parse_i128_radix`,
  `parse_u128/parse_i128` (prefixes, sign, `i128.MIN`, Empty/InvalidDigit/Overflow).
- `tests/std/num/gen_num.py` generates `num.ax` and `convert.ax`; `tests/std/num/gen_tests.py` generates the test programs.
  `generated_num_current.test` / `generated_tests_current.test` fail when a checked-in file is stale.

## Design decisions (for the architect)

1. **Generated std source.**  Twelve near-identical `impl` blocks are produced by `gen_num.py`; the checked-in `.ax` is the
   reviewable artefact and carries a banner.  A `--check` mode and two tests keep it current.
2. **The std modules are not auto-loaded.**  `compiler/driver` only loads option/result/prelude/host/future/cmp/atomic by
   itself (`tests/std/core/qa_driver_std_discovery.ax` documents it), so the new methods exist only in programs that
   contain `std/core/num.ax` / `convert.ax`.  The tests therefore stage a package (the T160 arena_drop pattern) in
   `tests/std/num/num_oracle.py`: `src/main.ax` is the program and the std files named in its `// std:` header are copied
   live from `--std-root`.  I did not touch `std/core/prelude.ax`.
3. **`from`/`try_from` are inherent generic methods, not trait impls** (deviation from AXS-INT-042/043, forced by compiler
   bugs 2 and 3 below).  They use small non-generic helper traits (`LosslessToD`, one per destination; `IntValue`), so the
   SPEC-40 call syntax `u16.try_from(x)` / `i128.from(x)` is unchanged and the lossless rule is enforced by the bound.
4. **`x.into()` and `x.try_into()` for integers are NOT provided** (deviation).  They choose the destination from the expected
   type, which needs generic-trait dispatch or a static trait method through a type parameter; both are broken (bugs 2, 3).
   `tests/std/num/into_xfail.test` is the executable specification: it XPASSes when the compiler is fixed.
5. **128-bit sources of `from`/`try_from`** (QA finding F1, fixed in round 1): `convert.test` covers the ten sources up to
   64 bits (all 12 destinations), `convert128.test` the i128/u128 sources, `qa_try_from_128_source.test` the QA range cases.
   Round 0 shipped them as xfail because `prim_kind_matches_name` had no i128/u128 branch; round 1 fixes it in
   `compiler/traits/solver.ax` and the three tests now pass.
6. **Tuples.**  `overflowing_*` return `(Self, bool)`, built field by field in a private `pair_T` helper because a tuple
   expression that names a variable does not compile (bug 4).  The rest of the module avoids tuple expressions.
7. `checked_rem(MIN, -1)` is `None` and `overflowing_rem(MIN, -1)` is `(0, true)`, as AXS-INT-024/025 say, although the
   remainder itself is representable.
8. The associated constants `T.MIN/MAX/BITS` are compiler built-ins (SPEC-40 AXS-INT-003); they are tested for all 12 types
   but not redefined in std.
9. The u128 formatting loop divides by the radix (`/` and `%` on u128 are exact in both modes since T452/T453); it does not
   use `print_int`, so the known native `print_int(u64 >= 2^63)` problem is not involved.  The tests compare values and
   print only a fixed `OK <name>` line.

## Tests (`tests/std/num/`)

| test | content | cases |
|---|---|---|
| `checked.test` | checked add/sub/mul/div/rem/neg/abs/shl/shr/pow, all 12 types | generated, one exit code per case |
| `overflowing.test` | overflowing add/sub/mul/div/rem/neg/abs/shl/shr/pow, all 12 types | |
| `wrapping_saturating.test` | wrapping_* and saturating_* (built-in and library), all 12 types | |
| `misc.test` | `MIN/MAX/BITS`, min/max/clamp/abs_diff/abs/unsigned_abs/signum/is_positive/is_negative/pow | |
| `bits.test` | count_ones/zeros, leading/trailing zeros/ones, rotate_left/right (7 counts), swap_bytes, reverse_bits, is_power_of_two, next/checked_next_power_of_two | |
| `bytes.test` | to/from le/be/ne bytes with exact byte values for pattern inputs, all 12 types | |
| `convert.test`, `convert128.test` | `from` (lossless pairs) and `try_from` (range edges) from 10 source types, and from i128/u128, to 12 destinations, bool, the SPEC-40 example | |
| `fmt128.test` | decimal/hex/binary/octal/radix-36/prefixed/padded formatting and parsing of i128/u128 incl. both extremes, overflow and error cases | |
| `panic_*.test` (9) | pow overflow (i32, u128), `i64.MIN.abs()`, `next_power_of_two` overflow (u8, u128), `wrapping_div/saturating_div/overflowing_rem` by zero, `clamp` bounds: exit 101 in all three legs | |
| `reject_*.test` (3) | lossy/signed-to-unsigned/pointer-width `from` is `AX_TRAIT_UNSATISFIED_BOUND` | |
| `int128_generic_dispatch.ax` | regression for the solver fix (generic bound on i128/u128) | |
| `into_xfail.test`, `*_xfail.ax` (tuple_names, static_dispatch, trait_dispatch, empty_copy) | remaining compiler-gap repros (xfail) | |
| `qa_edges.test`, `qa_try_from_128_source.test` | QA adversarial tests | |

Expected values come from exact Python integers (`gen_tests.py`), never from the library.  A failing case returns its case
number, so a regression points at one generated line.  The first run found one wrong expectation of mine (`checked_rem`
MIN % -1) and, more importantly, the 128-bit dispatch bug (bug 1) through case 928 of `convert`.

## Results

Round 0 (before the solver fix) is summarised in `T454-qa.md`.  Round 1 results are below.

## Round 1 (QA finding F1)

- `compiler/traits/solver.ax`: `prim_kind_matches_name` gained the `TY_I128` ("i128") and `TY_U128` ("u128") branches (plus the two
  `TY_I128`/`TY_U128` imports).  Before, trait impl selection for a 128-bit type fell back to the first impl, so
  `u64.try_from(100000000000000000000u128)` returned `Ok 0`; it now returns `Err` in interp, native -O0 and native -O1.
- `convert128.test` and `qa_try_from_128_source.test` lost their `xfail:` lines and pass; `int128_dispatch_xfail.ax` became the
  regression test `int128_generic_dispatch.ax` (no xfail) and passes in all three modes.  `qa_edges.test` is kept.
  `gen_tests.py` / `gen_num.py` were updated (the convert.ax header note 4 now says the bug is fixed).
- No other xfail turned into XPASS: the 13 remaining XFAIL are `into_xfail.test` and the tuple_names, static_dispatch,
  trait_dispatch and empty_copy repros (3 modes each).  Design decisions 3, 4 and 6 and follow-ups 2 to 6 stand.
- `--filter std/num/` in `build-snap-T454` (`axiomc2.exe` built from HEAD 9548f5e + this change, Release stage-0): TOTAL 41, PASS 28,
  FAIL 0, XFAIL 13, WEAK-NATIVE 0.
- Real task gate, from the snapshot: `python tools/taskgate.py --task T454 --compiler build/axiomc2.exe --build-dir build
  --exclude-requires axiom0-internal -j 2` (log `_workspaces/T454_taskgate_r1.log`, JSON `_workspaces/artifacts/taskgate-T454-r1.json`):
  `TOTAL 1012 PASS 997 FAIL 0 SKIP 2 XFAIL 13`, failing ids none, baseline OK, archcheck clean (230 files, 0 violations),
  WEAK-NATIVE 23 in the run and 0 in the task's own tests.  The 2 SKIPs are in the affected set, not in this task's tests (same as
  QA round 0).
- Selfhost bundles are regenerated by `taskctl snapshot`; none is listed below.


## Follow-ups (compiler bugs found; each has a minimal repro in tests/std/num)

1. (done in round 1) Trait impl selection ignored i128/u128; see Round 1.
2. **Static trait method called through a type parameter** (`static_dispatch_xfail.ax`): `D.mk(0)` runs the first impl whatever
   D is (with no argument the verifier reports `AX_VERIFY_CALL_SIGNATURE`); with an argument whose type has an impl, that
   impl wins.  Blocks `x.into()`/`x.try_into()`.  Probably belongs to T448 (explicit type arguments / bound inference).
3. **Several impls of one generic trait for the same Self** (`trait_dispatch_xfail.ax`): `u32.from(7u8)` with `From<u8>` and
   `From<u16>` for u32 is `AX_TRAIT_AMBIGUOUS_METHOD`; through a generic bound the first impl is silently used
   (miscompile: prints `7 7` instead of `7 5007`).  Needed for the spec form `impl From<u8> for u32`.
4. **Tuple expressions naming a variable** (`tuple_names_xfail.ax`): `(total, true)` with a `let` local is
   `AX_NAME_UNRESOLVED`; with a parameter, `(value, flag)` makes the compiler die with a stack overflow (status
   3221225725) at `check`/`inspect --emit=thir`.  Only literal elements work.  Workaround in `num.ax`: `pair_T` helpers.
5. **Empty struct with `@derive(Copy)`** (`empty_copy_xfail.ax`): second use is `AX_VERIFY_USE_AFTER_MOVE`; SPEC-40 declares
   `pub struct TryFromIntError {}`.
6. **Driver does not discover std modules** (`tests/std/core/qa_driver_std_discovery.ax`): `std.core.num`, `std.core.convert`,
   `std.text.fmt.int` cannot be imported by a plain program; the integer methods only exist when the module is part of the
   package.  A driver task should load `std/core/num.ax` (and convert) like option/result, or scan `use std.*`.
7. Not in this task's paths: `std/core/cmp.ax` has no `PartialEq/Eq/Ord` impls for `i128`/`u128`; `Option`/`Result` have no
   methods (`is_ok`, `is_none`, ... used by the SPEC-40 example 2 text; the test uses `match`); there are no `Debug`/`Display`
   traits for `TryFromIntError`.
8. Known and avoided: native `print_int` of a u64 >= 2^63 prints negative (T453 note).

## Files changed
- compiler/traits/solver.ax
- std/core/convert.ax
- std/core/num.ax
- std/text/fmt/int.ax
- tests/std/num/bits.test
- tests/std/num/bytes.test
- tests/std/num/checked.test
- tests/std/num/convert.test
- tests/std/num/convert128.test
- tests/std/num/empty_copy_xfail.ax
- tests/std/num/fmt128.test
- tests/std/num/gen_num.py
- tests/std/num/gen_tests.py
- tests/std/num/generated_num_current.test
- tests/std/num/generated_tests_current.test
- tests/std/num/int128_generic_dispatch.ax
- tests/std/num/into_xfail.test
- tests/std/num/misc.test
- tests/std/num/num_oracle.py
- tests/std/num/overflowing.test
- tests/std/num/panic_abs_min.test
- tests/std/num/panic_clamp_bounds.test
- tests/std/num/panic_next_power_of_two.test
- tests/std/num/panic_next_power_of_two_u128.test
- tests/std/num/panic_overflowing_rem_zero.test
- tests/std/num/panic_pow_overflow.test
- tests/std/num/panic_pow_overflow_u128.test
- tests/std/num/panic_saturating_div_zero.test
- tests/std/num/panic_wrapping_div_zero.test
- tests/std/num/prog/bits.ax
- tests/std/num/prog/bytes.ax
- tests/std/num/prog/checked.ax
- tests/std/num/prog/convert.ax
- tests/std/num/prog/convert128.ax
- tests/std/num/prog/fmt128.ax
- tests/std/num/prog/into_xfail.ax
- tests/std/num/prog/misc.ax
- tests/std/num/prog/overflowing.ax
- tests/std/num/prog/panic_abs_min.ax
- tests/std/num/prog/panic_clamp_bounds.ax
- tests/std/num/prog/panic_next_power_of_two.ax
- tests/std/num/prog/panic_next_power_of_two_u128.ax
- tests/std/num/prog/panic_overflowing_rem_zero.ax
- tests/std/num/prog/panic_pow_overflow.ax
- tests/std/num/prog/panic_pow_overflow_u128.ax
- tests/std/num/prog/panic_saturating_div_zero.ax
- tests/std/num/prog/panic_wrapping_div_zero.ax
- tests/std/num/prog/qa_edges.ax
- tests/std/num/prog/qa_try_from_128_source.ax
- tests/std/num/prog/reject_lossy_from.ax
- tests/std/num/prog/reject_same_width_pointer_from.ax
- tests/std/num/prog/reject_signed_to_unsigned_from.ax
- tests/std/num/prog/wrapping_saturating.ax
- tests/std/num/qa_edges.test
- tests/std/num/qa_try_from_128_source.test
- tests/std/num/reject_lossy_from.test
- tests/std/num/reject_same_width_pointer_from.test
- tests/std/num/reject_signed_to_unsigned_from.test
- tests/std/num/static_dispatch_xfail.ax
- tests/std/num/trait_dispatch_xfail.ax
- tests/std/num/tuple_names_xfail.ax
- tests/std/num/wrapping_saturating.test

STATUS: COMPLETE round=1
