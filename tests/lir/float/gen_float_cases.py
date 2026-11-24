#!/usr/bin/env python3
"""T459: generator of the native scalar floating-point semantic cases in this directory.

Writes `<name>.ax` + `<name>.txt` for arith_f64, arith_f32, compare, neg_convert, float_to_int and
int_to_float. Expected outputs come from an independent Python IEEE-754 oracle (ADR-0034): CPython
binary64 arithmetic for f64, exact integer/rational rounding (roundTiesToEven) for f32 and int <-> float,
SPEC-41 AXS-FLT-022 saturation for float -> int. Inputs are exact bit patterns, so the programs never
depend on literal parsing or constant folding.

Usage: python gen_float_cases.py          # (re)write the files
       python gen_float_cases.py --check  # exit 1 if a committed file differs
NaN results print as `nan` (payload and sign of a NaN are not observable semantics, AXS-FLT-002).
"""

import math
import os
import struct
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------------------------- oracle


def b64(x):
    return struct.unpack("<q", struct.pack("<d", x))[0]


def f64_of_bits(b):
    return struct.unpack("<d", struct.pack("<Q", b & 0xFFFFFFFFFFFFFFFF))[0]


def f32_of_bits(b):
    return struct.unpack("<f", struct.pack("<I", b & 0xFFFFFFFF))[0]


F32_MAX = f32_of_bits(0x7F7FFFFF)


def round_f32(v):
    """binary64 (or exact) value -> nearest binary32 (roundTiesToEven), as a Python float."""
    if v != v or v in (math.inf, -math.inf):
        return v
    if isinstance(v, float) and abs(v) <= F32_MAX:
        return struct.unpack("<f", struct.pack("<f", v))[0]
    return round_rational_f32(Fraction(v))


def round_rational_f32(q):
    """exact rational -> binary32 with roundTiesToEven (overflow to +-inf)."""
    if q == 0:
        return 0.0
    sign = -1.0 if q < 0 else 1.0
    a = abs(q)
    e = a.numerator.bit_length() - a.denominator.bit_length()
    if Fraction(2) ** e > a:
        e -= 1
    # a in [2^e, 2^(e+1))
    if e < -126:
        e = -126
    ulp = Fraction(2) ** (e - 23)
    m = a / ulp
    n = m.numerator // m.denominator
    r = m - n
    if r > Fraction(1, 2) or (r == Fraction(1, 2) and n % 2 == 1):
        n += 1
    val = n * ulp
    if val >= Fraction(2) ** 128:
        return sign * math.inf
    return sign * float(val)


def round_int_f64(n):
    return float(n)  # CPython int -> float is correctly rounded (RNE); 2^128 < f64 max


def round_int_f32(n):
    return round_rational_f32(Fraction(n))


def b32(x):
    return struct.unpack("<i", struct.pack("<f", x))[0]


def is_nan(x):
    return x != x


def fdiv(a, b):
    if b == 0.0:
        if a == 0.0 or is_nan(a):
            return math.nan
        neg = (math.copysign(1.0, a) < 0) != (math.copysign(1.0, b) < 0)
        return -math.inf if neg else math.inf
    return a / b


def fmod(a, b):
    if is_nan(a) or is_nan(b) or b == 0.0 or math.isinf(a):
        return math.nan
    return math.fmod(a, b)


def fop(op, a, b, f32):
    if op == "+":
        r = a + b
    elif op == "-":
        r = a - b
    elif op == "*":
        r = a * b
    elif op == "/":
        r = fdiv(a, b)
    else:
        r = fmod(a, b)
    if f32 and op != "%":
        # binary32 + - * / computed exactly in binary64 then rounded once is correctly rounded
        # (53 >= 2*24 + 2); fmod is exact in both formats.
        r = round_f32(r)
    return r


INT_TYPES = [
    ("i8", 8, True), ("i16", 16, True), ("i32", 32, True), ("i64", 64, True), ("i128", 128, True),
    ("isize", 64, True), ("u8", 8, False), ("u16", 16, False), ("u32", 32, False), ("u64", 64, False),
    ("u128", 128, False), ("usize", 64, False),
]


def sat_cast(x, bits, signed):
    if is_nan(x):
        return 0
    lo = -(1 << (bits - 1)) if signed else 0
    hi = (1 << (bits - 1)) - 1 if signed else (1 << bits) - 1
    if x == math.inf:
        return hi
    if x == -math.inf:
        return lo
    v = int(x)  # truncation toward zero, exact
    return max(lo, min(hi, v))


# ------------------------------------------------------------------------------------------- inputs

F64_IN = [
    0x0000000000000000, 0x8000000000000000, 0x3FF0000000000000, 0xBFF8000000000000,
    0x400A000000000000, 0x3FB999999999999A, 0x7E37E43C8800759C, 0x81A56E1FC2F8F359,
    0x0000000000000001, 0x7FEFFFFFFFFFFFFF, 0x7FF0000000000000, 0xFFF0000000000000,
    0x7FF8000000000000,
]
F32_IN = [
    0x00000000, 0x80000000, 0x3F800000, 0xBFC00000, 0x40500000, 0x3DCCCCCD, 0x7F7FFFFF, 0x80800000,
    0x00000001, 0x4B800001 & 0xFFFFFFFF, 0x7F800000, 0xFF800000, 0x7FC00000,
]

CAST_IN = [
    0.0, -0.0, 0.9, -0.9, 1.5, -1.5, 127.9, 128.0, -128.5, -129.0, 255.5, 256.0, 32767.5, -32768.7,
    65535.9, 2147483647.5, 2147483648.0, -2147483648.9, -2147483649.0, 4294967295.9, 4294967296.0,
    9223372036854774784.0, 9223372036854775808.0, -9223372036854775808.0, -9223372036854777856.0,
    18446744073709549568.0, 18446744073709551616.0, 1.7e38, 2.0 ** 127, -(2.0 ** 127), 3.4e38,
    2.0 ** 128, -(2.0 ** 128), 1e300, math.inf, -math.inf, math.nan,
]

INT_IN = {
    "i8": [0, 1, -1, 127, -128, 77],
    "i16": [0, -1, 32767, -32768, 12345],
    "i32": [0, 1, -1, 2147483647, -2147483648, 16777217, -16777217, 16777219, 123456789],
    "i64": [0, 1, -1, (1 << 63) - 1, -(1 << 63), (1 << 53) + 1, -((1 << 53) + 1), (1 << 53) + 3,
            (1 << 24) + 1, 0x7FFFFF7FFFFFFFFF, -0x1234567890ABCDEF],
    "i128": [0, -1, (1 << 127) - 1, -(1 << 127), (1 << 64) + 1, -((1 << 64) + 1), (1 << 100) + (1 << 47),
             (1 << 76) + (1 << 23) + 1, -((1 << 90) + (1 << 37)), 12345678901234567890123456789],
    "isize": [0, -1, (1 << 63) - 1, -(1 << 63), 9007199254740993],
    "u8": [0, 1, 255, 128],
    "u16": [0, 65535, 40000],
    "u32": [0, 1, 4294967295, 2147483648, 16777217, 4294967041],
    "u64": [0, 1, (1 << 64) - 1, 1 << 63, (1 << 63) + 1, (1 << 63) + 1024, (1 << 63) + 1025, (1 << 63) + 3072,
            0x8000008000000000, 0x8000008000000001, (1 << 53) + 1, 0xFFFFFFFFFFFFF800],
    "u128": [0, 1, (1 << 128) - 1, 1 << 127, (1 << 64) - 1, 1 << 64, (1 << 64) + 1, (1 << 128) - (1 << 103),
             (1 << 128) - (1 << 104) - 1, ((1 << 53) + 1) << 70, (((1 << 24) + 1) << 90) + 1, 1 << 100],
    "usize": [0, (1 << 64) - 1, 1 << 63, (1 << 63) + 1025],
}

# ------------------------------------------------------------------------------------------- writers

HEADER = """// test: helper
// Generated by gen_float_cases.py (T459) -- do not edit; expected output: {name}.txt
// Native SSE2 scalar float semantics (SPEC-41 AXS-FLT-010..025, AXS-FLT-040..044); oracle: Python IEEE-754.
@intrinsic unsafe fn address_of<T>(val: T) -> *const T {{ 0 as *const T }}

fn f64_of(b: i64) -> f64 {{
    unsafe {{ *(address_of(b) as *const f64) }}
}}

fn f32_of(b: i32) -> f32 {{
    unsafe {{ *(address_of(b) as *const f32) }}
}}

fn show64(x: f64) {{
    if x != x {{
        print("nan\\n");
        return;
    }}
    print_int(unsafe {{ *(address_of(x) as *const i64) }});
    print("\\n");
}}

fn show32(x: f32) {{
    if x != x {{
        print("nan\\n");
        return;
    }}
    print_int((unsafe {{ *(address_of(x) as *const i32) }}) as i64);
    print("\\n");
}}
"""


def lit64(b):
    s = b if b < (1 << 63) else b - (1 << 64)
    return "%di64" % s if s != -(1 << 63) else "(-9223372036854775807i64 - 1i64)"


def lit32(b):
    s = b if b < (1 << 31) else b - (1 << 32)
    return "%di32" % s if s != -(1 << 31) else "(-2147483647i32 - 1i32)"


def fmt_bits64(x):
    return "nan" if is_nan(x) else str(b64(x))


def fmt_bits32(x):
    return "nan" if is_nan(x) else str(b32(x))


def gen_arith(f32):
    name = "arith_f32" if f32 else "arith_f64"
    ins = F32_IN if f32 else F64_IN
    ty = "f32" if f32 else "f64"
    n = len(ins)
    src = [HEADER.format(name=name)]
    src.append("fn main() -> i32 {")
    if f32:
        src.append("    let raw: [%d]i32 = [%s];" % (n, ", ".join(lit32(b) for b in ins)))
        src.append("    let mut vals: [%d]f32 = [0.0f32; %d];" % (n, n))
        conv, show = "f32_of", "show32"
    else:
        src.append("    let raw: [%d]i64 = [%s];" % (n, ", ".join(lit64(b) for b in ins)))
        src.append("    let mut vals: [%d]f64 = [0.0; %d];" % (n, n))
        conv, show = "f64_of", "show64"
    src.append("    let mut k: usize = 0;")
    src.append("    while k < %d {" % n)
    src.append("        vals[k] = %s(raw[k]);" % conv)
    src.append("        k = k + 1;")
    src.append("    }")
    src.append("    let mut i: usize = 0;")
    src.append("    while i < %d {" % n)
    src.append("        let mut j: usize = 0;")
    src.append("        while j < %d {" % n)
    src.append("            let a: %s = vals[i];" % ty)
    src.append("            let b: %s = vals[j];" % ty)
    for op in "+-*/%":
        src.append("            %s(a %s b);" % (show, op))
    src.append("            j = j + 1;")
    src.append("        }")
    src.append("        i = i + 1;")
    src.append("    }")
    src.append("    0")
    src.append("}")
    vals = [f32_of_bits(b) if f32 else f64_of_bits(b) for b in ins]
    exp = []
    for a in vals:
        for b in vals:
            for op in "+-*/%":
                r = fop(op, a, b, f32)
                exp.append(fmt_bits32(r) if f32 else fmt_bits64(r))
    return name, "\n".join(src) + "\n", "\n".join(exp) + "\n"


def cmp_mask(a, b, nan_any):
    if nan_any:
        return 2
    m = 0
    m |= 1 if a == b else 0
    m |= 2 if a != b else 0
    m |= 4 if a < b else 0
    m |= 8 if a <= b else 0
    m |= 16 if a > b else 0
    m |= 32 if a >= b else 0
    return m


def gen_compare():
    name = "compare"
    src = [HEADER.format(name=name)]
    src.append("""fn mask64(a: f64, b: f64) -> i64 {
    let mut m: i64 = 0i64;
    let eq = a == b;
    let ne = a != b;
    let lt = a < b;
    let le = a <= b;
    let gt = a > b;
    let ge = a >= b;
    if eq { m = m + 1i64; }
    if ne { m = m + 2i64; }
    if lt { m = m + 4i64; }
    if le { m = m + 8i64; }
    if gt { m = m + 16i64; }
    if ge { m = m + 32i64; }
    m
}

fn branch64(a: f64, b: f64) -> i64 {
    let mut m: i64 = 0i64;
    if a == b { m = m + 1i64; }
    if a != b { m = m + 2i64; }
    if a < b { m = m + 4i64; }
    if a <= b { m = m + 8i64; }
    if a > b { m = m + 16i64; }
    if a >= b { m = m + 32i64; }
    m
}

fn mask32(a: f32, b: f32) -> i64 {
    let mut m: i64 = 0i64;
    if a == b { m = m + 1i64; }
    if a != b { m = m + 2i64; }
    if a < b { m = m + 4i64; }
    if a <= b { m = m + 8i64; }
    if a > b { m = m + 16i64; }
    if a >= b { m = m + 32i64; }
    m
}
""")
    n = len(F64_IN)
    src.append("fn main() -> i32 {")
    src.append("    let raw: [%d]i64 = [%s];" % (n, ", ".join(lit64(b) for b in F64_IN)))
    src.append("    let raw32: [%d]i32 = [%s];" % (n, ", ".join(lit32(b) for b in F32_IN)))
    src.append("    let mut i: usize = 0;")
    src.append("    while i < %d {" % n)
    src.append("        let mut j: usize = 0;")
    src.append("        while j < %d {" % n)
    src.append("            let a = f64_of(raw[i]);")
    src.append("            let b = f64_of(raw[j]);")
    src.append("            print_int(mask64(a, b) + 100i64 * branch64(a, b) + 10000i64 * mask32(f32_of(raw32[i]), f32_of(raw32[j])));")
    src.append('            print("\\n");')
    src.append("            j = j + 1;")
    src.append("        }")
    src.append("        i = i + 1;")
    src.append("    }")
    src.append("    0")
    src.append("}")
    exp = []
    v64 = [f64_of_bits(b) for b in F64_IN]
    v32 = [f32_of_bits(b) for b in F32_IN]
    for i in range(n):
        for j in range(n):
            a, b = v64[i], v64[j]
            m = cmp_mask(a, b, is_nan(a) or is_nan(b))
            c, d = v32[i], v32[j]
            m32 = cmp_mask(c, d, is_nan(c) or is_nan(d))
            exp.append(str(m + 100 * m + 10000 * m32))
    return name, "\n".join(src) + "\n", "\n".join(exp) + "\n"


def gen_neg_convert():
    name = "neg_convert"
    src = [HEADER.format(name=name)]
    n = len(F64_IN)
    src.append("fn main() -> i32 {")
    src.append("    let raw: [%d]i64 = [%s];" % (n, ", ".join(lit64(b) for b in F64_IN)))
    src.append("    let raw32: [%d]i32 = [%s];" % (n, ", ".join(lit32(b) for b in F32_IN)))
    src.append("    let mut i: usize = 0;")
    src.append("    while i < %d {" % n)
    src.append("        let a = f64_of(raw[i]);")
    src.append("        let c = f32_of(raw32[i]);")
    src.append("        show64(-a);")
    src.append("        show32(-c);")
    src.append("        show32(a as f32);")
    src.append("        show64(c as f64);")
    src.append("        show64(-(c as f64) * 2.0);")
    src.append("        i = i + 1;")
    src.append("    }")
    src.append("    0")
    src.append("}")
    exp = []
    for i in range(n):
        a = f64_of_bits(F64_IN[i])
        c = f32_of_bits(F32_IN[i])
        exp.append(fmt_bits64(-a))
        exp.append(fmt_bits32(-c))
        exp.append(fmt_bits32(round_f32(a)))
        exp.append(fmt_bits64(c))
        exp.append(fmt_bits64(-c * 2.0))
    return name, "\n".join(src) + "\n", "\n".join(exp) + "\n"


def gen_float_to_int():
    name = "float_to_int"
    src = [HEADER.format(name=name)]
    n = len(CAST_IN)
    bits = [b64(x) & 0xFFFFFFFFFFFFFFFF for x in CAST_IN]
    src.append("fn main() -> i32 {")
    src.append("    let raw: [%d]i64 = [%s];" % (n, ", ".join(lit64(b) for b in bits)))
    src.append("    let mut i: usize = 0;")
    src.append("    while i < %d {" % n)
    src.append("        let x = f64_of(raw[i]);")
    src.append("        let y = x as f32;")
    for tn, _, _ in INT_TYPES:
        src.append("        print_int(x as %s);" % tn)
        src.append('        print(" ");')
        src.append("        print_int(y as %s);" % tn)
        src.append('        print("\\n");')
    src.append("        i = i + 1;")
    src.append("    }")
    src.append("    0")
    src.append("}")
    exp = []
    for x in CAST_IN:
        y = round_f32(x)
        for tn, bw, sg in INT_TYPES:
            exp.append("%d %d" % (sat_cast(x, bw, sg), sat_cast(y, bw, sg)))
    return name, "\n".join(src) + "\n", "\n".join(exp) + "\n"


def gen_int_to_float():
    name = "int_to_float"
    src = [HEADER.format(name=name)]
    src.append("fn main() -> i32 {")
    exp = []
    for tn, bw, sg in INT_TYPES:
        vals = INT_IN[tn]
        n = len(vals)
        arr = "a_" + tn
        src.append("    let %s: [%d]%s = [%s];" % (arr, n, tn, ", ".join(lit_int(v, tn, bw, sg) for v in vals)))
        src.append("    let mut i_%s: usize = 0;" % tn)
        src.append("    while i_%s < %d {" % (tn, n))
        src.append("        let v = %s[i_%s];" % (arr, tn))
        src.append("        show64(v as f64);")
        src.append("        show32(v as f32);")
        src.append("        i_%s = i_%s + 1;" % (tn, tn))
        src.append("    }")
        for v in vals:
            exp.append(fmt_bits64(round_int_f64(v)))
            exp.append(fmt_bits32(round_int_f32(v)))
    src.append("    0")
    src.append("}")
    return name, "\n".join(src) + "\n", "\n".join(exp) + "\n"


def lit_int(v, tn, bw, sg):
    if sg and v == -(1 << (bw - 1)):
        return "(-%d%s - 1%s)" % ((1 << (bw - 1)) - 1, tn, tn)
    return "%d%s" % (v, tn)


GENS = [lambda: gen_arith(False), lambda: gen_arith(True), gen_compare, gen_neg_convert, gen_float_to_int,
        gen_int_to_float]


def main():
    check = "--check" in sys.argv
    bad = 0
    for g in GENS:
        name, ax, expected = g()
        for path, text in ((name + ".ax", ax), (name + ".txt", expected)):
            full = os.path.join(HERE, path)
            if check:
                try:
                    with open(full, encoding="utf-8", newline="") as f:
                        cur = f.read()
                except OSError:
                    cur = None
                if cur != text:
                    print("STALE " + path)
                    bad += 1
            else:
                with open(full, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
    if check:
        print("GEN-FLOAT-CASES %s" % ("STALE" if bad else "up to date"))
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
