# T461 report: E12.2 std.math, deterministic elementary and transcendental library (std only)

## Summary
`std/math/` is pure Axiom over the five float intrinsics of `std.core.float` (ADR-0049); no compiler change, no new
`@intrinsic`, no libm / CRT. All elementary operations that already exist in `std.core.float` are thin wrappers of its
methods (no second implementation); every other function is new.

Design: all transcendental functions run in double-double arithmetic (about 100 bits, `std/math/dd.ax`, Dekker/Veltkamp
products, no FMA) and round once, so every `f64` function is within **0.5000 ulp** in all probes (SPEC-41 allows 1.0 / 1.5).
The `f32` functions evaluate the `f64` function and round once to `f32` (0.5 ulp + 2^-29 ulp). Interpreter and native
code run the same Axiom and agree bit for bit (probe: 26 functions x 1200-3200 inputs, 0 mismatches against the Python
prototype in `--mode native`, and the vector tests pass in interp, native and native-O1).

Modules (all under `std/math/`, module names `std.math.*`): `dd` (double-double, `scale2`, `scale_dd` = single rounding into
the subnormal range), `tables` (GENERATED constants), `f64/consts`, `f32/consts` (GENERATED, the AXS-FLT-061 table),
`exp_core` (exp, exp2, expm1), `log_core` (ln, log2, log10, ln_1p, log), `trig_core` (sin, cos, tan, sincos),
`atan_core` (atan, atan2, asin, acos), `hyper_core` (sinh, cosh, tanh, asinh, acosh, atanh), `pow_core` (powf, powi,
cbrt, hypot), `erf_core` (erf, erfc), `mod` (API).

Algorithms (see the file headers):
- exp family: x = k ln2 + z (ln2 in three parts, `k * LN2_HI` exact), e^z - 1 by Taylor of z/16 in double-double and four
  doublings p -> p (p + 2); result 2^k (1 + p) rounded once (`scale_dd`).
- log family: x = 2^k m, 128-entry table (invc, -log invc as double-double), r = m * invc - 1 exact (two_prod), log1p(r) =
  2 atanh(r / (2 + r)) series in double-double; |x - 1| < 1/16 skips the table (full relative accuracy near 1).
- trig: Payne-Hanek reduction for every |x| > pi/4 (53-bit significand times a 192-bit window of 2/pi, 21 u64 words of the
  expansion, 256-bit product with u128 limbs), Taylor kernels in double-double (14 / 15 terms), tan = dd quotient.
- atan2 core: atan(q) = atan(i/16) + atan(z) with a 17-entry table, asin / acos feed sqrt((1-x)(1+x)) as a double-double.
- pow: 2^(y log2|x|) with the logarithm and the product in double-double; powi in double-double with the exponent of the
  partial products kept in an integer (no early overflow / underflow); cbrt Newton + one double-double step; hypot exact
  sum of squares in double-double.
- erf / erfc: Kummer series (x < 3) and a continued fraction (x >= 3) in double-double, `e^(-x^2)` from the double-double
  exponential of the exactly squared argument.
- hyperbolic functions through `expm1` in double-double (no cancellation), inverse ones through log1p of a double-double.

## Files changed
- std/math/atan_core.ax
- std/math/dd.ax
- std/math/erf_core.ax
- std/math/exp_core.ax
- std/math/f32/consts.ax
- std/math/f64/consts.ax
- std/math/hyper_core.ax
- std/math/log_core.ax
- std/math/mod.ax
- std/math/pow_core.ax
- std/math/tables.ax
- std/math/trig_core.ax
- tests/std/math/README.md
- tests/std/math/check_tables.test
- tests/std/math/check_vectors.test
- tests/std/math/consts.ax
- tests/std/math/elementary.ax
- tests/std/math/example_071.ax
- tests/std/math/f32_special.ax
- tests/std/math/gen_tables.py
- tests/std/math/identities.ax
- tests/std/math/make_vectors.py
- tests/std/math/mathproto.py
- tests/std/math/mathtables.py
- tests/std/math/methods.ax
- tests/std/math/probe.py
- tests/std/math/special_values.ax
- tests/std/math/stress_atan_f64.ax
- tests/std/math/stress_erf_f64.ax
- tests/std/math/stress_exp_f64.ax
- tests/std/math/stress_f32.ax
- tests/std/math/stress_hyper_f64.ax
- tests/std/math/stress_log_f64.ax
- tests/std/math/stress_pow_f64.ax
- tests/std/math/stress_trig_f64.ax
- tests/std/math/tables_bits.ax
- tests/std/math/validate.py
- tests/std/math/vec_atan_f64.ax
- tests/std/math/vec_erf_f64.ax
- tests/std/math/vec_exp_f64.ax
- tests/std/math/vec_f32.ax
- tests/std/math/vec_hyper_f64.ax
- tests/std/math/vec_log_f64.ax
- tests/std/math/vec_pow_f64.ax
- tests/std/math/vec_trig_f64.ax

(`std/core/prelude.ax`, listed in `locks:`, is not edited: std.math is on demand like std.core.float.)

## Tests (snapshot `build-snap-T461`, compiler built there)
- `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 4 std/math`:
  `TOTAL 66 PASS 66 FAIL 0`, `WEAK-NATIVE 0` (interp, native and native-O1 for the 20 interp+native tests, native / O1 for the 8 heavy twins).
- `bundles_current` (34 selfhost bundle tests): 34 PASS. `archcheck.py`: 252 files, 0 violations.
- Expected values never come from the code under test: `make_vectors.py` uses 300-bit mpmath (correctly rounded to f64 / f32)
  and a portable splitmix64 input generator; `special_values.ax`, `elementary.ax`, `consts.ax`, `f32_special.ax` use the
  SPEC-41 table or values computed with mpmath; `tables_bits.ax` checks that every literal of `tables.ax` is read as the exact double.
- Native mutation sanity: changing one expected constant makes the native binary print `FAIL <id>` (checks print FAIL and
  return a non-zero status; no test relies on `assert`).
- Development tools (committed, `tests/std/math/README.md`): `probe.py` compares a compiled program with the Python
  prototype (`mathproto.py`, line-by-line model, bit identical) and with mpmath: 26 functions, random / adversarial / raw
  bit-pattern inputs (subnormals, huge values, inf, nan), 4 seeds x 700-3200 inputs per function, `--mode native` and `--mode interp`:
  0 mismatches, worst error 0.5000 ulp. The raw fuzz found one bug (reduction for |x| in [2^53, 2^54), `j0 = 0`), fixed and
  now covered by the trig vectors.
- Gate: `python tools/taskgate.py --task T461 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` in `build-snap-T461` (snapshot taken after the last source edit): `axtest TOTAL 876 PASS 876 FAIL 0`, failing ids none, BASELINE OK (one baseline id now passes: `std/async/reactor/timer_wheel_100_timers.ax`), archcheck 252 files 0 violations, smoke OK, `TASKGATE T461 exit=0`. WEAK-NATIVE: 3 in the whole run, 0 in the task's own tests (the 3 are pre-existing tests of other tasks).

## Design decisions (for the architect)
- **D1 algorithms**: SPEC-41 AXS-FLT-063 names Cody-Waite below 2^20 and minimax polynomials. I used double-double Taylor
  kernels and a single Payne-Hanek path for every |x| > pi/4: simpler, one code path, 0.5 ulp instead of 1.0 / 1.5. The
  price is speed: about 5 us per call (native -O0 measured: sin + exp + ln + atan + powf + erf = 33 us per iteration); interp about 15 ms per call.
  A fast path (double-only kernel with a Ziv-style rounding test) can be added later without changing results.
- **D2 f32**: `*_f32` = f64 function rounded once (also `ldexp_f32`, `powi_f32`).
- **D3 naming and import**: f64 plain names, f32 suffix `_f32`; methods (`x.sin()`, `y.atan2(x)`, `x.powi(n)`, ...) only for names not
  already in std.core.float. Constants: `std.math.PI` (f64, `pub use` of `std.math.f64.consts`) and `std.math.f32.consts.PI`; a program
  must `use std.math.f32.consts` to reach the f32 set (a module is loaded by `use` only). Importing both `std.math.f32.consts` and `std.math.f64.consts` binds the name `consts` twice (`AX_NAME_DUPLICATE`), so use one of them and the full path of the other.
- **D4 not in the prelude** (same as T460, ADR-0048 on-demand loader).
- **D5 semantics fixed where SPEC-41 leaves a choice**: `signum(+-0) = +-1` (sign bit), `powi(NaN, 0) = 1`, `modf` parts carry the sign of x (`-3.0` gives `-0.0` fraction), `frexp` of 0 / inf / NaN returns `(x, 0)`, `rem_euclid` returns `+0.0` for a zero result and, like Rust, `r + |b|` for negative `r` (can round to `|b|`), `div_euclid` is `trunc(a / b)` corrected by the sign of `a % b`, `lerp` is the C++20 `std::lerp` (exact at t = 0, 1, monotonic), `log(x, base)` is the quotient of two double-double logarithms, `exp2` of a tiny subnormal result is correctly rounded (`scale_dd` avoids double rounding).
- **D6 spec text**: AXS-FLT-071 example runs unchanged (the `Ordering` comparison in the test uses `match`, T460 follow-up 1).

## Spec deviations
- AXS-FLT-063 algorithm column (D1): different algorithms, better error bound.
- AXS-FLT-061 path `std.math.f64.consts` / `std.math.f32.consts` exist as modules; `std.math` re-exports only the f64 set (the f32 set cannot share the names).

## Follow-ups
1. Compiler: two `use` of modules with the same last segment (`std.math.f32.consts`, `std.math.f64.consts`) collide (`AX_NAME_DUPLICATE`); module aliasing (`use a.b as c`) or path-qualified access without `use` of an already loaded module would remove the need for D3's workaround.
2. Compiler: `==` on `Ordering` / user enums with a hand-written `PartialEq` (T460 follow-up 1) is still rejected (`AX_TYPE_OPERATOR`).
3. Performance: a fast double-only path for sin / cos / exp / ln / atan (Ziv test, fall back to the double-double code) would cut calls from about 5 us to a few hundred ns; not needed for correctness, results would not change.
4. Optional: SSE4.1 / FMA selection (T473) can replace `dd.ax` `two_prod` by a hardware FMA only if the results stay bit identical.

STATUS: COMPLETE round=0
