#!/usr/bin/env python3
"""Generates the vector tests of tests/std/math (T461).

    python tests/std/math/make_vectors.py            rewrite the generated files
    python tests/std/math/make_vectors.py --check    fail when a generated file is stale

The expected values are not computed by the code under test or by the prototype: they are the correctly rounded values of
300-bit mpmath references (f64 and f32), and the inputs come from a portable splitmix64 generator (no libm, no Python
random) so that the generated files are the same on every machine. A result passes when it is within 1 ulp of the
correctly rounded value (SPEC-41 AXS-FLT-063 allows 1.0 ulp, 1.5 for tan, powf, hyperbolic functions and erf).

Generated files (tests/std/math): vec_<family>_f64.ax and vec_f32.ax run in the interpreter and natively;
stress_<family>_f64.ax and stress_f32.ax are the native-only heavy twins with ten times more inputs.
"""

import argparse
import math
import os
import struct
import sys

import mpmath
from mpmath import mp, mpf

mp.prec = 300

HERE = os.path.dirname(os.path.abspath(__file__))
MASK = (1 << 64) - 1


# ------------------------------------------------------------------------------------------------
# portable random numbers and float helpers
# ------------------------------------------------------------------------------------------------

class Rng:
    def __init__(self, seed):
        self.s = seed & MASK

    def next(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & MASK
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def unit(self):
        return (self.next() >> 11) / 9007199254740992.0

    def uniform(self, a, b):
        return a + (b - a) * self.unit()

    def randint(self, a, b):
        return a + self.next() % (b - a + 1)

    def sign(self):
        return -1.0 if (self.next() & 1) else 1.0


def bits64(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def bits32(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def expf(t):
    """e^t correctly rounded (no libm)."""
    return float(mpmath.exp(mpf(t)))


def round_f32(v):
    """The f32 nearest to the mpf v, as an exact Python float (inf on overflow)."""
    if v == 0:
        return 0.0
    neg = v < 0
    a = abs(v)
    m, e = mpmath.frexp(a)  # a = m 2^e, 0.5 <= m < 1
    q = mpf(2) ** max(e - 24, -149)
    n = mpmath.nint(a / q)
    r = n * q
    if r >= mpf(2) ** 128:
        return -math.inf if neg else math.inf
    f = float(r)
    return -f if neg else f


def f32_of(x):
    """Round a double input to f32 (inputs are chosen as f32 values)."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def lit64(x):
    return "0x%016Xu64" % bits64(x)


def lit32(x):
    return "0x%08Xu64" % bits32(x)


# ------------------------------------------------------------------------------------------------
# inputs
# ------------------------------------------------------------------------------------------------

def gen(rng, kind, n):
    out = []
    u = rng.uniform
    if kind == "exp":
        out = [u(-745, 709) for _ in range(n)] + [u(-3, 3) for _ in range(n)] + [u(-1e-3, 1e-3) for _ in range(n // 4)] + [u(700, 709.78) for _ in range(2)] + [-745.1, -708.5, 709.78, 1.0, -1.0, 0.5]
    elif kind == "expm1":
        out = [u(-40, 709) for _ in range(n)] + [u(-1, 1) for _ in range(n)] + [u(-1e-3, 1e-3) for _ in range(n // 4)] + [1e-10, -1e-10, 1.0, -1.0, 3e-17]
    elif kind == "exp2":
        out = [u(-1074, 1023) for _ in range(n)] + [u(-4, 4) for _ in range(n)] + [-1074.0, -1022.5, 10.0, -10.0, 0.5, 1023.9]
    elif kind == "pos":
        out = [expf(u(-745, 709)) for _ in range(n)] + [u(0.5, 2) for _ in range(n)] + [1 + u(-0.1, 0.1) for _ in range(n)] + \
              [1 + u(-1e-5, 1e-5) for _ in range(n // 2)] + [5e-324 * rng.randint(1, 1 << 40) for _ in range(n // 4)] + [1e-300, 2.0, 10.0, 1000.0, 0.1]
    elif kind == "log1p":
        out = [u(-1, 10) for _ in range(n)] + [u(-0.1, 0.1) for _ in range(n)] + [u(-1e-9, 1e-9) for _ in range(n // 4)] + \
              [expf(u(-3, 700)) for _ in range(n // 2)] + [-1 + u(1e-16, 0.1) for _ in range(n // 2)] + [1e-300, -0.5, 1.0, 1e15]
    elif kind == "trig":
        out = [u(-1, 1) for _ in range(n)] + [u(-100, 100) for _ in range(n)] + [u(-1e6, 1e6) for _ in range(n // 2)] + \
              [expf(u(-700, 700)) * rng.sign() for _ in range(n)] + [k * 1.5707963267948966 for k in range(1, 12)] + \
              [1e22, 5.0e22, 1e300, 1.7e308, 2.0 ** 60, 0.5, 1.0, 3.0, 355.0, 1e-8, 2.0 ** 52 * 1.1, 2.0 ** 53, 2.0 ** 53 * 1.25, 2.0 ** 53 * 1.99, 2.0 ** 54, 2.0 ** 54 * 1.5, 2.0 ** 55 * 1.1, 2.0 ** 51 * 1.3, 2.0 ** 50 * 1.7]
    elif kind == "unit":
        out = [u(-1, 1) for _ in range(n)] + [u(-1e-5, 1e-5) for _ in range(n // 4)] + [1 - 2.0 ** -rng.randint(1, 53) for _ in range(n // 4)] + \
              [-1 + 2.0 ** -rng.randint(1, 53) for _ in range(n // 4)] + [0.5, -0.5, 0.25]
    elif kind == "atan":
        out = [u(-3, 3) for _ in range(n)] + [expf(u(-700, 700)) * rng.sign() for _ in range(n)] + [u(-1e-5, 1e-5) for _ in range(n // 4)] + [1.0, -1.0, 0.5, 1e300]
    elif kind == "sinh":
        out = [u(-3, 3) for _ in range(n)] + [u(-50, 50) for _ in range(n)] + [u(-711, 711) for _ in range(n // 2)] + [u(-1e-4, 1e-4) for _ in range(n // 4)] + [709.7, 710.4, -710.4, 20.0, 1.0]
    elif kind == "acosh":
        out = [1 + u(0, 3) for _ in range(n)] + [expf(u(0, 700)) for _ in range(n)] + [1 + u(0, 1e-4) for _ in range(n // 4)] + [2.0, 1.5, 1e10, 1e300]
    elif kind == "erf":
        out = [u(-3, 3) for _ in range(n)] + [u(-6.5, 6.5) for _ in range(n)] + [u(-1e-3, 1e-3) for _ in range(n // 4)] + [1e-200, 1e-310, 5e-324, 0.5, 1.0, 3.0, -2.0]
    elif kind == "erfc":
        out = [u(-6.5, 6.5) for _ in range(n)] + [u(-6, 28) for _ in range(n)] + [u(2.5, 3.5) for _ in range(n // 2)] + [u(-1e-3, 1e-3) for _ in range(n // 4)] + \
              [0.5, 1.0, 3.0, -2.0, 26.0, 27.2, 10.0]
    elif kind == "cbrt":
        out = [u(-100, 100) for _ in range(n)] + [expf(u(-745, 709)) * rng.sign() for _ in range(n)] + [5e-324 * k for k in range(1, 5)] + \
              [1.7976931348623157e308, 8.0, 27.0, -27.0, 1000.0, 0.001, 2.0]
    elif kind == "pow":
        for _ in range(n):
            out.append((u(0.01, 10), u(-30, 30)))
        for _ in range(n):
            out.append((expf(u(-700, 700)), u(-3, 3)))
        for _ in range(n // 2):
            out.append((u(-10, -0.1), float(rng.randint(-20, 20))))
        for _ in range(n // 2):
            out.append((1 + u(-1e-6, 1e-6), u(-1e9, 1e9)))
        for _ in range(n // 2):
            out.append((u(0.5, 2), u(-1500, 1500)))
        for _ in range(n // 2):
            out.append((float(rng.randint(1, 20)), float(rng.randint(-40, 60))))
        out += [(2.0, 0.5), (10.0, 23.0), (10.0, -5.0), (2.0, 1023.0), (2.0, -1074.0), (0.5, 3.0)]
    elif kind == "hypot":
        for _ in range(n):
            out.append((u(-10, 10), u(-10, 10)))
        for _ in range(n):
            out.append((expf(u(-745, 709)) * rng.sign(), expf(u(-745, 709)) * rng.sign()))
        out += [(3.0, 4.0), (1e308, 1e308), (5e-324, 5e-324), (1e-320, 1e-320), (1.0, 1e-20), (-5.0, 12.0)]
    elif kind == "atan2":
        for _ in range(n):
            out.append((u(-3, 3), u(-3, 3)))
        for _ in range(n):
            out.append((expf(u(-700, 700)) * rng.sign(), expf(u(-700, 700)) * rng.sign()))
        for _ in range(n // 2):
            e = u(-30, 30)
            out.append((expf(e) * rng.sign(), rng.sign() * u(0.5, 2)))
        out += [(1.0, 1.0), (1.0, -1.0), (-1.0, -1.0), (-1.0, 1.0), (1e-300, -1.0), (1e300, 1e-300), (0.5, 0.25)]
    elif kind == "powi":
        for _ in range(n):
            out.append((u(-3, 3), rng.randint(-50, 50)))
        for _ in range(n // 2):
            out.append((expf(u(-100, 100)) * rng.sign(), rng.randint(-8, 8)))
        for _ in range(n // 4):
            out.append((1 + u(-1e-6, 1e-6), rng.randint(-2 ** 31, 2 ** 31 - 1)))
        for _ in range(n // 2):
            out.append((u(0.5, 2), rng.randint(-1500, 1500)))
        out += [(2.0, 1023), (2.0, -1074), (2.0, 1024), (10.0, 22), (10.0, -22), (0.1, 3), (-2.0, 5), (-2.0, -5), (3.0, 40)]
    elif kind == "log":
        for _ in range(n):
            out.append((expf(u(-30, 30)), expf(u(-5, 5))))
        out += [(8.0, 2.0), (1000.0, 10.0), (2.0, 10.0), (81.0, 3.0), (0.5, 2.0), (1.0e10, 10.0)]
    else:
        raise ValueError(kind)
    return out


# ------------------------------------------------------------------------------------------------
# references
# ------------------------------------------------------------------------------------------------

def mp_cbrt(x):
    return mpmath.cbrt(mpf(abs(x))) * (1 if x > 0 else -1)


# name -> (arity, input kind, reference, f32 domain-safe)
FUNCS = {
    "exp": (1, "exp", lambda x: mpmath.exp(mpf(x))),
    "exp2": (1, "exp2", lambda x: mpmath.power(2, mpf(x))),
    "expm1": (1, "expm1", lambda x: mpmath.expm1(mpf(x))),
    "ln": (1, "pos", lambda x: mpmath.log(mpf(x))),
    "log2": (1, "pos", lambda x: mpmath.log(mpf(x), 2)),
    "log10": (1, "pos", lambda x: mpmath.log10(mpf(x))),
    "ln_1p": (1, "log1p", lambda x: mpmath.log1p(mpf(x))),
    "log": (2, "log", lambda x, b: mpmath.log(mpf(x)) / mpmath.log(mpf(b))),
    "sin": (1, "trig", lambda x: mpmath.sin(mpf(x))),
    "cos": (1, "trig", lambda x: mpmath.cos(mpf(x))),
    "tan": (1, "trig", lambda x: mpmath.tan(mpf(x))),
    "atan": (1, "atan", lambda x: mpmath.atan(mpf(x))),
    "asin": (1, "unit", lambda x: mpmath.asin(mpf(x))),
    "acos": (1, "unit", lambda x: mpmath.acos(mpf(x))),
    "atan2": (2, "atan2", lambda y, x: mpmath.atan2(mpf(y), mpf(x))),
    "sinh": (1, "sinh", lambda x: mpmath.sinh(mpf(x))),
    "cosh": (1, "sinh", lambda x: mpmath.cosh(mpf(x))),
    "tanh": (1, "sinh", lambda x: mpmath.tanh(mpf(x))),
    "asinh": (1, "atan", lambda x: mpmath.asinh(mpf(x))),
    "acosh": (1, "acosh", lambda x: mpmath.acosh(mpf(x))),
    "atanh": (1, "unit", lambda x: mpmath.atanh(mpf(x))),
    "erf": (1, "erf", lambda x: mpmath.erf(mpf(x))),
    "erfc": (1, "erfc", lambda x: mpmath.erfc(mpf(x))),
    "cbrt": (1, "cbrt", mp_cbrt),
    "powf": (2, "pow", lambda x, y: mpmath.power(mpf(x), mpf(y))),
    "powi": (2, "powi", lambda x, n: mpmath.power(mpf(x), n)),
    "hypot": (2, "hypot", lambda x, y: mpmath.sqrt(mpf(x) ** 2 + mpf(y) ** 2)),
}

FAMILIES = {
    "exp": ["exp", "exp2", "expm1"],
    "log": ["ln", "log2", "log10", "ln_1p", "log"],
    "trig": ["sin", "cos", "tan"],
    "atan": ["atan", "atan2", "asin", "acos"],
    "hyper": ["sinh", "cosh", "tanh", "asinh", "acosh", "atanh"],
    "pow": ["powf", "powi", "cbrt", "hypot"],
    "erf": ["erf", "erfc"],
}

SEEDS = {name: 1000 + i for i, name in enumerate(FUNCS)}


def f64_rows(name, n):
    arity, kind, ref = FUNCS[name]
    rng = Rng(SEEDS[name])
    rows = []
    for p in gen(rng, kind, n):
        args = p if arity == 2 else (p,)
        try:
            v = ref(*args)
        except (ValueError, ZeroDivisionError):
            continue
        if isinstance(v, mpmath.mpc) or mpmath.isnan(v):
            continue
        if mpmath.isinf(v):
            want = math.inf if v > 0 else -math.inf
        elif abs(v) >= mpf(2) ** 1024 * (1 - mpf(2) ** -54):
            want = math.inf if v > 0 else -math.inf
        else:
            want = float(v)
        rows.append((args, want))
    return rows


def f32_rows(name, n):
    arity, kind, ref = FUNCS[name]
    rng = Rng(SEEDS[name] + 500)
    rows = []
    for p in gen(rng, kind, n):
        try:
            if arity == 2:
                args = (f32_of(p[0]), p[1]) if name == "powi" else (f32_of(p[0]), f32_of(p[1]))
            else:
                args = (f32_of(p),)
        except OverflowError:
            continue
        if any(a == 0.0 for a in args if not isinstance(a, int)):
            continue
        try:
            v = ref(*args)
        except (ValueError, ZeroDivisionError):
            continue
        if isinstance(v, mpmath.mpc) or mpmath.isnan(v):
            continue
        if mpmath.isinf(v):
            want = math.inf if v > 0 else -math.inf
        else:
            want = round_f32(v)
        rows.append((args, want))
    return rows


# ------------------------------------------------------------------------------------------------
# emitters
# ------------------------------------------------------------------------------------------------

NEAR = """fn near64(got: u64, want: u64) -> bool {
    if got == want {
        return true;
    }
    let g = f64.from_bits(got);
    let w = f64.from_bits(want);
    if g != g && w != w {
        return true;
    }
    if g != g || w != w {
        return false;
    }
    if (got >> 63u32) != (want >> 63u32) {
        return false;
    }
    let d = if got > want { got - want } else { want - got };
    d <= 1u64
}

fn near32(got: u32, want: u32) -> bool {
    if got == want {
        return true;
    }
    let g = f32.from_bits(got);
    let w = f32.from_bits(want);
    if g != g && w != w {
        return true;
    }
    if g != g || w != w {
        return false;
    }
    if (got >> 31u32) != (want >> 31u32) {
        return false;
    }
    let d = if got > want { got - want } else { want - got };
    d <= 1u32
}
"""


def table_text(name, rows, is32):
    arity = FUNCS[name][0]
    lit = lit32 if is32 else lit64
    vals = []
    for args, want in rows:
        if name == "powi":
            vals.append(lit(args[0]))
            vals.append("0x%08Xu64" % (args[1] & 0xFFFFFFFF))
        else:
            for a in args:
                vals.append(lit(a))
        vals.append(lit(want))
    width = arity + 1
    lines = ["const T_%s: [%d]u64 = [" % (name.upper(), len(vals))]
    for i in range(0, len(vals), 6):
        lines.append("    " + ", ".join(vals[i:i + 6]) + ",")
    lines.append("];")
    return "\n".join(lines), len(rows), width


def run_text(name, count, width, is32):
    arity = FUNCS[name][0]
    suffix = "_f32" if is32 else ""
    ty = "f32" if is32 else "f64"
    cast = " as u32" if is32 else ""
    fb = "f32.from_bits" if is32 else "f64.from_bits"
    L = []
    L.append("fn run_%s() -> i32 {" % name)
    L.append("    let mut bad: i32 = 0;")
    L.append("    let mut i: usize = 0;")
    L.append("    while i < %d {" % count)
    base = "%d * i" % width
    L.append("        let x = %s(T_%s[%s]%s);" % (fb, name.upper(), base, cast))
    if arity == 2:
        if name == "powi":
            L.append("        let n = (T_%s[%s + 1] as u32) as i32;" % (name.upper(), base))
            call = "std.math.powi%s(x, n)" % suffix
        else:
            L.append("        let y = %s(T_%s[%s + 1]%s);" % (fb, name.upper(), base, cast))
            call = "std.math.%s%s(x, y)" % (name, suffix)
    else:
        call = "std.math.%s%s(x)" % (name, suffix)
    L.append("        let got = %s.to_bits();" % call)
    near = "near32" if is32 else "near64"
    L.append("        if !%s(got%s, T_%s[%s + %d]%s) {" % (near, "" if not is32 else "", name.upper(), base, arity, cast))
    L.append("            bad = bad + 1;")
    L.append('            print("FAIL %s%s ");' % (name, suffix))
    L.append("            print_int(i as i64);")
    L.append('            print("\\n");')
    L.append("        }")
    L.append("        i = i + 1;")
    L.append("    }")
    L.append("    bad")
    L.append("}")
    return "\n".join(L)


def file_text(tag, title, names, n, is32, native_only, step_limit):
    L = []
    L.append("// test: run")
    if native_only:
        L.append("// modes: native")
        L.append("// reason: heavy twin (about ten times the inputs) of the interp + native vector test of the same functions")
    else:
        L.append("// modes: interp native")
    L.append("// timeout: %d" % (900 if not native_only else 600))
    L.append("// covers: REQ-SIMD-142, REQ-SIMD-143, REQ-SIMD-304, REQ-SIMD-305, REQ-SIMD-186, REQ-SIMD-187, REQ-SIMD-189")
    if not native_only:
        L.append("// flags: --step-limit %d" % step_limit)
    L.append("// stdout: ok math %s\\n" % tag)
    L.append("")
    L.append("// T461: %s. Inputs come from a portable splitmix64 generator, the expected values are the correctly rounded" % title)
    L.append("// results of 300-bit mpmath references (tests/std/math/make_vectors.py); a result passes within 1 ulp (SPEC-41")
    L.append("// AXS-FLT-063). GENERATED, do not edit.")
    L.append("")
    L.append("module test.math_%s" % tag)
    L.append("")
    L.append("use std.math")
    L.append("")
    L.append(NEAR)
    runs = []
    for name in names:
        rows = (f32_rows if is32 else f64_rows)(name, n)
        t, count, width = table_text(name, rows, is32)
        L.append(t)
        L.append("")
        L.append(run_text(name, count, width, is32))
        L.append("")
        runs.append("run_%s()" % name)
    L.append("fn main() -> i32 {")
    L.append("    let bad = " + " + ".join(runs) + ";")
    L.append("    if bad == 0 {")
    L.append('        print("ok math %s\\n");' % tag)
    L.append("        return 0;")
    L.append("    }")
    L.append("    1")
    L.append("}")
    return "\n".join(L) + "\n"


def rot_checksum(values):
    h = 0
    for v in values:
        h = (((h << 1) | (h >> 63)) & MASK) ^ v
    return h


def tables_text():
    import mathtables as T

    def dd_bits(pairs):
        out = []
        for hi, lo in pairs:
            out.append(bits64(hi))
            out.append(bits64(lo))
        return out

    sets = []
    sets.append(("SINC", "SINC", dd_bits(T.sin_coefs(14)), "dd"))
    sets.append(("COSC", "COSC", dd_bits(T.cos_coefs(15)), "dd"))
    sets.append(("EXPM1C", "EXPM1C", dd_bits(T.expm1_coefs(11)), "dd"))
    sets.append(("ATANC", "ATANC", dd_bits(T.atan_coefs(8)), "dd"))
    sets.append(("ATANHC", "ATANHC", dd_bits(T.atanh_coefs(8)), "dd"))
    sets.append(("ATANT", "ATANT", dd_bits(T.atan_table()), "dd"))
    logv = []
    for invc, h, l in T.log_table():
        logv += [bits64(invc), bits64(h), bits64(l)]
    sets.append(("LOGT", "LOGT", logv, "log"))
    words = T.two_over_pi_words()
    sets.append(("TWO_OVER_PI", "TWO_OVER_PI", words, "u64"))
    L = []
    L.append("// test: run")
    L.append("// modes: interp native")
    L.append("// timeout: 300")
    L.append("// covers: REQ-SIMD-142, REQ-SIMD-189")
    L.append("// stdout: ok math tables_bits\\n")
    L.append("")
    L.append("// T461: every f64 literal of the generated tables std/math/tables.ax is read by the compiler as the exact double")
    L.append("// (rotate-xor checksum of the bit patterns against mathtables.py, which rounds mpmath values). GENERATED.")
    L.append("")
    L.append("module test.math_tables_bits")
    L.append("")
    L.append("use std.math.dd.Dd")
    for name, _, _, _ in sets:
        L.append("use std.math.tables.%s" % name)
    L.append("use std.math.tables.LN2_HI")
    L.append("use std.math.tables.LN2_MID")
    L.append("use std.math.tables.LN2_LO")
    for name in ["PI", "PIO2", "LN2", "LOG2E", "LOG10E", "LN10", "TWO_OVER_SQRT_PI", "ONE_OVER_SQRT_PI"]:
        L.append("use std.math.tables.%s_DD" % name)
    L.append("")
    L.append("fn mix(h: u64, v: u64) -> u64 {")
    L.append("    ((h << 1u32) | (h >> 63u32)) ^ v")
    L.append("}")
    L.append("")
    L.append("fn chk(name: str, got: u64, want: u64) -> i32 {")
    L.append("    if got == want {")
    L.append("        return 0;")
    L.append("    }")
    L.append('    print("FAIL ");')
    L.append("    print(name);")
    L.append('    print("\\n");')
    L.append("    1")
    L.append("}")
    L.append("")
    body = []
    for name, _, vals, kind in sets:
        n = len(vals)
        fn = "sum_%s" % name.lower()
        L.append("fn %s() -> u64 {" % fn)
        L.append("    let mut h: u64 = 0u64;")
        if kind == "dd":
            L.append("    let mut i: usize = 0;")
            L.append("    while i < %d {" % (n // 2))
            L.append("        h = mix(h, %s[i].hi.to_bits());" % name)
            L.append("        h = mix(h, %s[i].lo.to_bits());" % name)
        elif kind == "log":
            L.append("    let mut i: usize = 0;")
            L.append("    while i < %d {" % (n // 3))
            L.append("        h = mix(h, %s[i].invc.to_bits());" % name)
            L.append("        h = mix(h, %s[i].logc.hi.to_bits());" % name)
            L.append("        h = mix(h, %s[i].logc.lo.to_bits());" % name)
        else:
            L.append("    let mut i: usize = 0;")
            L.append("    while i < %d {" % n)
            L.append("        h = mix(h, %s[i]);" % name)
        L.append("        i = i + 1;")
        L.append("    }")
        L.append("    h")
        L.append("}")
        L.append("")
        body.append("    f = f + chk(\"%s\", %s(), 0x%016Xu64);" % (name, fn, rot_checksum(vals)))
    L.append("fn sum_scalars() -> u64 {")
    L.append("    let mut h: u64 = 0u64;")
    for nm in ["LN2_HI", "LN2_MID", "LN2_LO"]:
        L.append("    h = mix(h, %s.to_bits());" % nm)
    for name in ["PI", "PIO2", "LN2", "LOG2E", "LOG10E", "LN10", "TWO_OVER_SQRT_PI", "ONE_OVER_SQRT_PI"]:
        L.append("    h = mix(h, %s_DD.hi.to_bits());" % name)
        L.append("    h = mix(h, %s_DD.lo.to_bits());" % name)
    L.append("    h")
    L.append("}")
    L.append("")
    scal = [bits64(x) for x in T.ln2_parts()]
    dds = T.dd_consts()
    for name in ["PI", "PIO2", "LN2", "LOG2E", "LOG10E", "LN10", "TWO_OVER_SQRT_PI", "ONE_OVER_SQRT_PI"]:
        scal += [bits64(dds[name][0]), bits64(dds[name][1])]
    body.append("    f = f + chk(\"scalars\", sum_scalars(), 0x%016Xu64);" % rot_checksum(scal))
    L.append("fn main() -> i32 {")
    L.append("    let mut f: i32 = 0;")
    L += body
    L.append("    if f == 0 {")
    L.append('        print("ok math tables_bits\\n");')
    L.append("        return 0;")
    L.append("    }")
    L.append("    1")
    L.append("}")
    return chr(10).join(L) + chr(10)


def outputs():
    out = {}
    out["tables_bits.ax"] = tables_text()
    for fam, names in FAMILIES.items():
        out["vec_%s_f64.ax" % fam] = file_text("vec_%s_f64" % fam, "std.math %s functions, f64" % fam, names, 14, False, False, 4000000000)
        out["stress_%s_f64.ax" % fam] = file_text("stress_%s_f64" % fam, "std.math %s functions, f64, heavy" % fam, names, 150, False, True, 0)
    all_names = [n for names in FAMILIES.values() for n in names]
    out["vec_f32.ax"] = file_text("vec_f32", "std.math f32 variants of every transcendental function", all_names, 5, True, False, 4000000000)
    out["stress_f32.ax"] = file_text("stress_f32", "std.math f32 variants, heavy", all_names, 100, True, True, 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    for fname, text in outputs().items():
        path = os.path.join(HERE, fname)
        if args.check:
            try:
                with open(path, "rb") as f:
                    cur = f.read().decode("utf-8")
            except OSError:
                print("missing " + path)
                bad = 1
                continue
            if cur != text:
                print("stale " + path)
                bad = 1
        else:
            with open(path, "wb") as f:
                f.write(text.encode("utf-8"))
            print("wrote %s (%d bytes)" % (fname, len(text)))
    if args.check and not bad:
        print("ok")
    return bad


if __name__ == "__main__":
    sys.exit(main())
