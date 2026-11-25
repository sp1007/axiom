# T460 report: E12.2 float methods, formatting and exact parsing (std only)

## Summary
Everything is Axiom over the five T458a intrinsics; no compiler change.

- `std/core/float.ax` (`module std.core.float`): associated constants of `f32`/`f64` (`RADIX`, `MANTISSA_DIGITS`,
  `DIGITS`, `EPSILON`, `MIN`, `MAX`, `MIN_POSITIVE`, `MIN_POSITIVE_SUBNORMAL`, `MIN_EXP`, `MAX_EXP`, `MIN_10_EXP`,
  `MAX_10_EXP`, `INFINITY`, `NEG_INFINITY`, `NAN`), `FpCategory`, `classify` and the `is_*` predicates, `total_cmp`,
  `min`, `max`, `clamp` (panics on `min > max` or NaN bounds), `to_bits`/`from_bits`, byte conversions
  (`to_le/be/ne_bytes`, `from_le/be/ne_bytes`), `abs`/`copysign`/`sqrt` wrappers, `floor`, `ceil`, `trunc`, `round`,
  `round_ties_even`, `fract`, `next_up`, `next_down`, `to_degrees`, `to_radians`, `mul_add`.
  - Rounding to integral values is exact bit manipulation on `f64`; the `f32` forms widen to `f64` (exact) and narrow back (exact).
  - `mul_add` is exact integer soft-float (`u128`): product mantissas, alignment with jammed sticky bits, one
    round-to-nearest-even at the final precision, correct for subnormal and overflow ranges (ADR-0049 section 4).
    The same core serves `f32` (24 bits, quantum 2^-149) and `f64`.
- `std/text/fmt/float.ax` (`module std.text.fmt.float`): all arithmetic on a fixed 160-limb big integer.
  - `format_f64/f32` (+ `_into`): shortest round-trip digits, Burger-Dybvig free-format with exact arithmetic and
    the correct asymmetric interval at powers of two; ties on the last digit go to the even digit.
  - `format_*_fixed`, `format_*_exp`: exact decimal expansion of the binary value, then round to the requested digit
    count, ties to even on the exact value; `NaN`/`inf`/`-inf`/`-0.0` per AXS-FLT-050.
  - `parse_f64/f32` (`view<[u8]>`), `parse_*_str` (`view<String>`), `unsafe parse_*_raw(ptr, len)`: exact
    round-to-nearest-even through big-integer long division (up to 800 significant digits kept, the rest only as a
    sticky digit), `inf`/`infinity`/`nan` in any case, signs, no whitespace/underscores,
    `Err(Empty)` for "" and `Err(InvalidSyntax)` otherwise; overflow gives `inf`, underflow `0.0`/`-0.0`.
- `std/text/fmt/format.ax`: `format_into_f64/f32`, `_fixed`, `_exp` wrappers and `pub use` of the float API.
- Deleted the helper `tests/mir/float_interp/intrinsics.ax`; its ten derived-operation vector tables now run as
  `tests/std/float_fmt/derived_f64|f32.ax` and `fma_f64|f32.ax` over the library functions.

## Design decisions (for the architect)
- **D1 notation of the shortest format**: decimal for 1e-4 <= |x| < 1e16 (whole numbers end in `.0`), otherwise
  `d[.ddd]e[-]N` without plus sign or padding (`1e16`, `1.5e-7`, `5e-324`). The spec only fixes the `.0` rule. The
  fixed-precision exponent mode keeps the spec form `d.ddde+XX` (two digit minimum).
- **D2 parse input type**: `Str` is not indexable in the bootstrap language, so `parse_*` take `view<[u8]>` like
  `std.text.fmt.int`; `parse_*_str(view<String>)` and `parse_*_raw(ptr, len)` are added. Spec signature `Str` stays open.
- **D3 not in the prelude**: `std.core.float` is loaded by a `use std.core.float.<item>` (on-demand std loader,
  ADR-0048), like `std.core.num`. Methods exist only when the module is part of the program. I did not edit
  `std/core/prelude.ax`, so no program pays for it implicitly.
- **D4 FpCategory** uses `@derive(Copy)` plus hand-written `Clone`/`PartialEq`/`Eq` impls (see follow-up 1).
- **D5 panic**: `clamp` uses a local `@intrinsic fn panic(msg: str)` (as `std/fiber/mod.ax`) because
  `std/core/panics.ax` does not parse (`-> !`); the runtime message is `panic: explicit panic`.
- **D6** NaN-returning helpers (`min`/`max`/`next_*`/rounding of NaN) return `x + x`/the other operand so the result
  is a quiet NaN.

## Tests (snapshot `build-snap-T460`, compiler built there)
All under `tests/std/float_fmt`, interp + native -O0 + -O1 unless noted. Expected data does not come from the code
under test: Python `repr` / `%.*f` / `%.*e` / `float()` and exact-rational reference routines in `make_vectors.py`.
- `derived_f64/f32.ax`, `fma_f64/f32.ax`: 7 rounding/neighbour ops x 82 vectors, min/max 484 pairs each, 1576 fma vectors per type.
- `core_float.ax`: constants (bits), classification, `total_cmp` over the full chain incl. signalling NaNs, min/max/clamp
  zero and NaN cases, rounding, neighbours, byte conversions, `a * b + c` versus `a.mul_add(b, c)` (REQ-SIMD-272),
  overflow/underflow/cancellation in fma, angle conversion. `clamp_panic.ax` (exit 101).
- `fmt_shortest_f64/f32.ax` (text compared with repr / exact search, and read back), `fmt_fixed_exp.ax` (fixed and
  exponent text for f64 and f32 incl. ties, carries, 1100 digits), `parse_f64/f32.ax` (halfway cases, subnormal and
  overflow boundaries, 800+ digit strings, specials, syntax errors), `format_wiring.ax`.
- `roundtrip.ax` (24 values per type, both modes) and `roundtrip_stress.ax` (12000 per type, `// modes: native`,
  heavy twin of the former); `check_vectors.test` keeps the generated files in sync with `make_vectors.py`.
- Interp speed is about 3 us per MIR step, hence `// flags: --step-limit 2000000000` and 15-130 s per vector file in interp.
- Native mutation sanity: the checks print `FAIL` and return a non-zero exit, `WEAK-NATIVE 0`.
- Gate in the snapshot: `python tools/taskgate.py --task T460 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`: `TOTAL 218 PASS 218 FAIL 0`, BASELINE OK, TASKGATE T460 exit=0, WEAK-NATIVE 0 in own tests; `archcheck.py`: 240 files, 0 violations.

## Spec deviations
none beyond D1-D3 (spec text leaves them open).

## Follow-ups
1. Compiler: `==`/`!=` on a user enum with a hand-written `PartialEq` impl gives `AX_VERIFY_TYPE_MISMATCH` (field
   projection on non-aggregate); `@derive(PartialEq)` / `@derive(Clone)` on an enum fail too. Tests use `match`.
   Repro: `impl PartialEq for Cat {..}; if c == Cat.B {..}`.
2. `std/core/panics.ax` does not parse (`-> !`, `AX_PARSE_EXPECTED_TYPE`) and `panic` ignores its message at run time.
3. `Str` is neither indexable nor convertible to `view<[u8]>`; slicing syntax `v[a..b]` does not exist, so the
   spec signatures `parse_f64(s: Str)` are not expressible.
4. Interp cost of std code is high (~3 us/step): a faster big-integer path or a native big-int intrinsic would
   cut test times; not needed for correctness.
5. T461 (`std.math`) should `use std.core.float` rather than re-declaring the five intrinsics.

## Files changed
- std/core/float.ax
- std/text/fmt/float.ax
- std/text/fmt/format.ax
- tests/mir/float_interp/intrinsics.ax
- tests/std/float_fmt/make_vectors.py
- tests/std/float_fmt/check_vectors.test
- tests/std/float_fmt/core_float.ax
- tests/std/float_fmt/clamp_panic.ax
- tests/std/float_fmt/derived_f32.ax
- tests/std/float_fmt/derived_f64.ax
- tests/std/float_fmt/fma_f32.ax
- tests/std/float_fmt/fma_f64.ax
- tests/std/float_fmt/fmt_fixed_exp.ax
- tests/std/float_fmt/fmt_shortest_f32.ax
- tests/std/float_fmt/fmt_shortest_f64.ax
- tests/std/float_fmt/format_wiring.ax
- tests/std/float_fmt/parse_f32.ax
- tests/std/float_fmt/parse_f64.ax
- tests/std/float_fmt/roundtrip.ax
- tests/std/float_fmt/roundtrip_stress.ax

STATUS: COMPLETE round=0
