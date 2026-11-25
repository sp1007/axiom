# tests/std/math (T461)

Tests and tools of `std.math` (`std/math/`, SPEC-41 section 7, AXS-FLT-060..064).

## How std.math is built

Everything is Axiom over the five float intrinsics of `std.core.float` (ADR-0049). The transcendental functions are
computed in double-double arithmetic (about 100 bits, `std/math/dd.ax`) and rounded once, so every `f64` function is
within 0.5 ulp except for the rare hard-to-round inputs (measured worst case 0.5000 ulp over millions of probe values).
The `f32` functions evaluate the `f64` function and round once. There is no libm, no fused multiply-add instruction and
no hardware transcendental: the interpreter and native code run the same Axiom and give the same bits.

| file | content |
|---|---|
| `dd.ax` | double-double arithmetic, exact power-of-two scaling, single rounding into the subnormal range |
| `tables.ax` | GENERATED constants (Taylor coefficients, log and atan tables, bits of 2/pi), `gen_tables.py` |
| `f64/consts.ax`, `f32/consts.ax` | GENERATED correctly rounded constants of AXS-FLT-061 |
| `exp_core.ax` | exp, exp2, expm1 and the exponential kernel |
| `log_core.ax` | ln, log2, log10, ln_1p, log and the logarithm in double-double |
| `trig_core.ax` | Payne-Hanek reduction, sin, cos, tan, sincos |
| `atan_core.ax` | atan, atan2, asin, acos |
| `hyper_core.ax` | sinh, cosh, tanh, asinh, acosh, atanh |
| `pow_core.ax` | powf, powi, cbrt, hypot |
| `erf_core.ax` | erf, erfc |
| `mod.ax` | public API: constants, the thin wrappers of `std.core.float`, f32 variants, signum, modf, frexp, ldexp, scalbn, div_euclid, rem_euclid, lerp and the inherent methods |

## Tests

| test | modes | content |
|---|---|---|
| `vec_<family>_f64.ax`, `vec_f32.ax` | interp, native | GENERATED vectors vs correctly rounded mpmath values (within 1 ulp) |
| `stress_<family>_f64.ax`, `stress_f32.ax` | native | GENERATED heavy twins with ten times more inputs |
| `special_values.ax`, `f32_special.ax` | interp, native | the special-value table of AXS-FLT-064, overflow / underflow thresholds, exact cases |
| `elementary.ax` | interp, native | wrappers of std.core.float, signum, modf, frexp, ldexp (single rounding), euclid, lerp |
| `identities.ax` | interp, native | odd / even symmetry bit for bit, inverse pairs, monotonicity, exact powers of two and ten |
| `consts.ax` | interp, native | bit patterns of the constants against the SPEC-41 table |
| `tables_bits.ax` | interp, native | GENERATED: the literals of `tables.ax` are read as the exact doubles |
| `methods.ax` | interp, native | the inherent methods return the bits of the free functions |
| `example_071.ax` | interp, native | the canonical example AXS-FLT-071 |
| `check_vectors.test`, `check_tables.test` | | the generated files are up to date |

## Generators and tools (Python 3 and mpmath)

* `make_vectors.py [--check]` writes the generated tests. Inputs come from a splitmix64 generator (portable), expected
  values are 300-bit mpmath results rounded to f64 or f32.
* `gen_tables.py [--check]` writes `std/math/tables.ax` and the two constants modules from `mathtables.py` (mpmath, 400 bits).
* `mathproto.py` is the algorithm prototype written with plain Python floats (IEEE binary64 operations only), a line by line
  model of `std/math`. `probe.py` compiles a program with random, adversarial and raw bit-pattern inputs, runs it
  (`--mode native|interp`) and compares bit for bit with the prototype and in ulps with mpmath:

      python tests/std/math/probe.py --compiler <build>/axiomc2.exe --std-root std --n 400 [--raw] [--mode interp]

  A failing bit comparison means a porting error, an ulp above 0.6 means an algorithm error.
