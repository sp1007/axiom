#!/usr/bin/env python3
"""Generates the vector tests of tests/std/float_fmt (T460).

    python tests/std/float_fmt/make_vectors.py            rewrite the generated files
    python tests/std/float_fmt/make_vectors.py --check    fail when a generated file is stale

The expected values do not come from the code under test: shortest formatting is checked against Python's repr (f64)
and an independent exact-rational digit search (f32 and f64), fixed/exponent formatting against `%.*f` / `%.*e`
(exact), and parsing against Python's float() (f64) and an exact-rational rounding routine (f32 and f64).

Generated files: fmt_shortest_f64.ax, fmt_shortest_f32.ax, fmt_fixed_exp.ax, parse_f64.ax, parse_f32.ax.
"""

import argparse
import math
import os
import random
import struct
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
BS = chr(92)


# ------------------------------------------------------------------------------------------------
# Reference arithmetic (exact rationals)
# ------------------------------------------------------------------------------------------------

def f64_from_bits(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def f32_to_double(b):
    return struct.unpack("<f", struct.pack("<I", b))[0]


def bits_of_f64(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def decompose(bits, width):
    """(sign, m, e) with value = (-1)^sign * m * 2^e for a finite float."""
    if width == 64:
        sign = bits >> 63
        field = (bits >> 52) & 0x7FF
        frac = bits & ((1 << 52) - 1)
        if field == 0:
            return sign, frac, -1074
        return sign, frac | (1 << 52), field - 1075
    sign = bits >> 31
    field = (bits >> 23) & 0xFF
    frac = bits & ((1 << 23) - 1)
    if field == 0:
        return sign, frac, -149
    return sign, frac | (1 << 23), field - 150


def two_pow(e):
    return Fraction(2) ** e


def layout(neg, digits, x10):
    """Shortest-format text of the digit string `digits` with decimal exponent x10 (value = d.ddd * 10^x10)."""
    s = "-" if neg else ""
    n = len(digits)
    if -4 <= x10 < 16:
        k = x10 + 1
        if k <= 0:
            return s + "0." + "0" * (-k) + digits
        if k >= n:
            return s + digits + "0" * (k - n) + ".0"
        return s + digits[:k] + "." + digits[k:]
    body = digits[0] + ("." + digits[1:] if n > 1 else "")
    return s + body + "e" + str(x10)


def shortest(bits, width):
    """Shortest round-trip decimal by exact search over n-digit candidates."""
    sign, m, e = decompose(bits, width)
    if m == 0:
        return "-0.0" if sign else "0.0"
    prec, qmin = (53, -1074) if width == 64 else (24, -149)
    v = Fraction(m) * two_pow(e)
    ulp_up = two_pow(e)
    boundary = m == (1 << (prec - 1)) and e > qmin
    ulp_down = ulp_up / 2 if boundary else ulp_up
    lo = v - ulp_down / 2
    hi = v + ulp_up / 2
    even = (m % 2) == 0
    t = int(math.floor(math.log10(float(v)))) if float(v) > 0 else -400
    while Fraction(10) ** t > v:
        t -= 1
    while Fraction(10) ** (t + 1) <= v:
        t += 1
    for n in range(1, 20):
        p = t - n + 1
        scale = Fraction(10) ** p
        base = math.floor(v / scale)
        best = None
        for d in (base, base + 1):
            val = d * scale
            ok = (lo <= val <= hi) if even else (lo < val < hi)
            if ok:
                dist = abs(val - v)
                if best is None or dist < best[0] or (dist == best[0] and d % 2 == 0):
                    best = (dist, d)
        if best is not None:
            d = best[1]
            s = str(d)
            x10 = len(s) - 1 + p
            s = s.rstrip("0") or "0"
            return layout(bool(sign), s, x10)
    raise AssertionError("no digits")


def repr64(bits):
    r = repr(f64_from_bits(bits))
    if "e" in r:
        mant, ex = r.split("e")
        r = mant + "e" + str(int(ex))
    return r


def round_fraction(fr, prec, qmin):
    """Nearest (ties to even) m * 2^q, m <= 2^prec, for a positive Fraction."""
    t = fr.numerator.bit_length() - fr.denominator.bit_length()
    while two_pow(t) > fr:
        t -= 1
    while two_pow(t + 1) <= fr:
        t += 1
    q = max(t - (prec - 1), qmin)
    scaled = fr / two_pow(q)
    m = math.floor(scaled)
    rem = scaled - m
    if rem > Fraction(1, 2) or (rem == Fraction(1, 2) and m % 2 == 1):
        m += 1
    return m, q


def pack_bits(neg, m, q, width):
    if width == 64:
        prec, bias_q, fmax, hidden, man_bits = 53, 1075, 2047, 1 << 52, 52
    else:
        prec, bias_q, fmax, hidden, man_bits = 24, 150, 255, 1 << 23, 23
    sign = (1 << (width - 1)) if neg else 0
    if m == 0:
        return sign
    if m == (1 << prec):
        m = hidden
        q += 1
    if m < hidden:
        return sign | m
    field = q + bias_q
    if field >= fmax:
        return sign | (fmax << man_bits)
    return sign | (field << man_bits) | (m & (hidden - 1))


def parse_expected(text, width):
    """Bits of the correctly rounded value of a finite decimal string."""
    neg = text.startswith("-")
    body = text.lstrip("+-")
    mant, _, ex = body.lower().partition("e")
    ip, _, fp = mant.partition(".")
    digits = (ip + fp).lstrip("0")
    exp10 = (int(ex) if ex else 0) - len(fp)
    prec, qmin = (53, -1074) if width == 64 else (24, -149)
    if not digits:
        return pack_bits(neg, 0, 0, width)
    if len(digits) + exp10 > 330:
        return pack_bits(neg, 1 << prec, 10000, width)
    if len(digits) + exp10 < -400:
        return pack_bits(neg, 0, 0, width)
    n = int(digits)
    fr = Fraction(n * 10 ** exp10) if exp10 >= 0 else Fraction(n, 10 ** (-exp10))
    m, q = round_fraction(fr, prec, qmin)
    return pack_bits(neg, m, q, width)


def exact_decimal(m, e):
    """Exact decimal text of m * 2^e."""
    if e >= 0:
        return str(m << e)
    k = -e
    digits = str(m * 5 ** k).rjust(k + 1, "0")
    text = digits[:-k] + "." + digits[-k:]
    return text.rstrip("0").rstrip(".")


# ------------------------------------------------------------------------------------------------
# Value selection
# ------------------------------------------------------------------------------------------------

def finite64(b):
    return ((b >> 52) & 0x7FF) != 0x7FF


def finite32(b):
    return ((b >> 23) & 0xFF) != 0xFF


def pick_values64(rng, count):
    vals = [
        0x0000000000000000, 0x8000000000000000, 0x3FF0000000000000, 0xBFF0000000000000, 0x3FB999999999999A,
        0x3FE0000000000000, 0x4000000000000000, 0x4024000000000000, 0x0000000000000001, 0x8000000000000001,
        0x000FFFFFFFFFFFFF, 0x0010000000000000, 0x7FEFFFFFFFFFFFFF, 0xFFEFFFFFFFFFFFFF, 0x400921FB54442D18,
        0x4005BF0A8B145769, 0x3F1A36E2EB1C432D, 0x3F1A36E2EB1C432C, 0x3F1A36E2EB1C432E,
        bits_of_f64(1e22), bits_of_f64(1e23), bits_of_f64(1e21), bits_of_f64(1e15), bits_of_f64(1e16),
        bits_of_f64(9.999999999999999e15), bits_of_f64(123456789012345680.0), bits_of_f64(0.0001),
        bits_of_f64(0.00009999999999999999), bits_of_f64(1e-5), bits_of_f64(5e-324),
        bits_of_f64(2.2250738585072014e-308), bits_of_f64(2.2250738585072009e-308),
        bits_of_f64(9007199254740993.0), bits_of_f64(9007199254740992.0), bits_of_f64(4.35), bits_of_f64(0.3),
        bits_of_f64(100.0), bits_of_f64(1.0e100), bits_of_f64(8.41e21), bits_of_f64(2.0 ** -1022),
        bits_of_f64(2.0 ** 1023), bits_of_f64(2.0 ** 52), bits_of_f64(2.0 ** 53), bits_of_f64(1.5),
        bits_of_f64(2.5), bits_of_f64(0.125), bits_of_f64(0.375), bits_of_f64(2.675), bits_of_f64(1e300),
    ]
    for k in range(-1074, 1024, 83):
        base = bits_of_f64(math.ldexp(1.0, k))
        vals.append(base)
        vals.append(base + 1)
        vals.append((base - 1) | (1 << 63))
    while len(vals) < count:
        b = rng.getrandbits(64)
        if finite64(b):
            vals.append(b)
    for _ in range(count // 4):
        digits = rng.randint(1, 17)
        mant = rng.randint(10 ** (digits - 1), 10 ** digits - 1)
        ex = rng.randint(-30, 30)
        vals.append(bits_of_f64(float("%de%d" % (mant, ex))))
    return vals


def pick_values32(rng, count):
    vals = [
        0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x3DCCCCCD, 0x3F000000, 0x40000000, 0x41200000,
        0x00000001, 0x80000001, 0x007FFFFF, 0x00800000, 0x7F7FFFFF, 0xFF7FFFFF, 0x40490FDB, 0x3F800001,
        0x3F7FFFFF, 0x4B000000, 0x4B800000, 0x4C000000, 0x7149F2CA, 0x358637BD, 0x3F400000, 0x40200000,
        0x3E000000, 0x3EC00000, 0x7E967699,
    ]
    for k in range(-149, 128, 17):
        b = ((k + 127) << 23) if k >= -126 else (1 << (k + 149))
        vals.append(b)
        vals.append(b + 1)
        vals.append((b - 1) | 0x80000000)
    while len(vals) < count:
        b = rng.getrandbits(32)
        if finite32(b):
            vals.append(b)
    for _ in range(count // 4):
        digits = rng.randint(1, 9)
        mant = rng.randint(10 ** (digits - 1), 10 ** digits - 1)
        ex = rng.randint(-20, 20)
        vals.append(parse_expected("%de%d" % (mant, ex), 32))
    return vals


# ------------------------------------------------------------------------------------------------
# Output helpers
# ------------------------------------------------------------------------------------------------

def array_text(values, per_line):
    out = []
    for i in range(0, len(values), per_line):
        out.append("    " + ", ".join(str(v) for v in values[i:i + per_line]) + ",")
    return "\n".join(out)


class Table:
    """All strings of a test in one byte array."""

    def __init__(self):
        self.text = []

    def add(self, s):
        start = len(self.text)
        self.text.extend(s.encode("ascii"))
        return start, len(s)


def decl(name, ty, values, per_line, suffix=""):
    items = [("%s%s" % (v, suffix)) if suffix and not isinstance(v, str) else str(v) for v in values]
    return "const %s: [%d]%s = [\n%s\n];" % (name, len(values), ty, array_text(items, per_line))


def hexes(values, suffix):
    return ["0x%X%s" % (v, suffix) for v in values]


def text_decl(table):
    return "const TEXT: [%d]u8 = [\n%s\n];" % (len(table.text), array_text(table.text, 32))


def header(name, timeout, covers, what, uses):
    lines = [
        "// test: run",
        "// modes: interp native",
        "// timeout: %d" % timeout,
        "// covers: %s" % covers,
        "// flags: --step-limit 2000000000",
        "// stdout: ok float_fmt %s%sn" % (name, BS),
        "",
        "// GENERATED by tests/std/float_fmt/make_vectors.py (T460). Do not edit by hand: edit the generator and rerun it.",
        "// " + what,
        "",
        "module test.float_%s" % name,
        "",
        "use std.core.result.Result",
        "use std.text.string.String",
    ]
    lines.extend("use " + u for u in uses)
    lines.append("")
    lines.append("@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }")
    lines.append("")
    return "\n".join(lines)


COMMON = """
fn show_failure(kind: i32, index: usize) {
    print("FAIL ");
    print_int(kind as i64);
    print(" #");
    print_int(index as i64);
    print("%sn");
}

// true when `s` holds exactly TEXT[start .. start + n]
fn same_text(s: view<String>, start: usize, n: usize) -> bool {
    if s.len != n {
        return false;
    }
    let mut i: usize = 0;
    while i < n {
        let c = unsafe { *(s.ptr + i) };
        if c != TEXT[start + i] {
            return false;
        }
        i = i + 1;
    }
    true
}
""" % BS


def finish(name):
    return ("    if failures == 0 {\n        print(\"ok float_fmt %s%sn\");\n    }\n    failures\n}\n" % (name, BS))


# ------------------------------------------------------------------------------------------------
# fmt_shortest_f64 / fmt_shortest_f32
# ------------------------------------------------------------------------------------------------

def gen_shortest(width, rng):
    ty, ut = ("f64", "u64") if width == 64 else ("f32", "u32")
    vals = pick_values64(rng, 140) if width == 64 else pick_values32(rng, 120)
    table = Table()
    starts, lens = [], []
    for b in vals:
        text = shortest(b, width)
        if width == 64:
            assert text == repr64(b), (hex(b), text, repr64(b))
        else:
            assert parse_expected(text, 32) == b, (hex(b), text)
        st, ln = table.add(text)
        starts.append(st)
        lens.append(ln)
    name = "fmt_shortest_f%d" % width
    out = [header(name, 600, "REQ-SIMD-189, REQ-SIMD-186, REQ-SIMD-187",
                  "Shortest round-trip formatting (SPEC-41 AXS-FLT-050, 051) of %d %s values, and the read-back of every text." % (len(vals), ty),
                  ["std.text.fmt.float.format_%s" % ty, "std.text.fmt.float.parse_%s_raw" % ty])]
    out.append(text_decl(table))
    out.append(decl("START", "u32", starts, 16, "u32"))
    out.append(decl("LEN", "u32", lens, 24, "u32"))
    out.append(decl("BITS", ut, hexes(vals, ut), 6))
    out.append(COMMON)
    out.append("""pub fn main() -> i32 {
    let mut failures: i32 = 0;
    let mut i: usize = 0;
    while i < %(n)d {
        let x = %(ty)s.from_bits(BITS[i]);
        let s = format_%(ty)s(x);
        if !same_text(view(s), START[i] as usize, LEN[i] as usize) {
            show_failure(1, i);
            failures = failures + 1;
        }
        let back = unsafe { parse_%(ty)s_raw(s.ptr as *const u8, s.len) };
        match back {
            Result.Ok(y) => {
                if y.to_bits() != BITS[i] {
                    show_failure(2, i);
                    failures = failures + 1;
                }
            },
            Result.Err(_) => {
                show_failure(3, i);
                failures = failures + 1;
            },
        }
        i = i + 1;
    }
""" % {"n": len(vals), "ty": ty})
    out.append(finish(name))
    return name, "\n".join(out)


# ------------------------------------------------------------------------------------------------
# fmt_fixed_exp
# ------------------------------------------------------------------------------------------------

def gen_fixed_exp(rng):
    table = Table()
    rows = []   # (kind, bits, prec, fixed_start, fixed_len, exp_start, exp_len)

    def add(kind, bits, prec):
        if kind == 0:
            x = f64_from_bits(bits)
        else:
            x = f32_to_double(bits)
        fixed = "%.*f" % (prec, x)
        expo = "%.*e" % (prec, x)
        fs, fl = table.add(fixed)
        es, el = table.add(expo)
        rows.append((kind, bits, prec, fs, fl, es, el))

    must = [0.5, 1.5, 2.5, 3.5, 0.125, 0.375, 0.625, 2.675, 1e21, 123456789.987654321, 0.1, 1.0, 9.5, 99.5, 0.05,
            9.999, 9.995, 0.0, -0.0, -0.5, -2.5, 1e-7, 5e-324, 1.7976931348623157e308, 999999.5, 0.99999, 1.005]
    for x in must:
        for prec in (0, 1, 2, 3, 6):
            add(0, bits_of_f64(x), prec)
    add(0, bits_of_f64(5e-324), 400)
    add(0, bits_of_f64(5e-324), 1100)
    add(0, bits_of_f64(0.1), 60)
    add(0, bits_of_f64(1.7976931348623157e308), 3)
    add(0, bits_of_f64(2.0 ** 70), 20)
    for b in pick_values64(rng, 60):
        add(0, b, rng.choice([0, 1, 2, 3, 5, 8, 15, 17, 25]))
    for b in pick_values32(rng, 60):
        add(1, b, rng.choice([0, 1, 2, 3, 5, 8, 12, 20]))
    for x in (0.5, 1.5, 2.5, 0.1, 16777216.0, 3.4028235e38, 1.1754944e-38, 1e-45, 0.0, -0.0):
        for prec in (0, 1, 4, 10):
            add(1, struct.unpack("<I", struct.pack("<f", x))[0], prec)
    name = "fmt_fixed_exp"
    out = [header(name, 600, "REQ-SIMD-189, REQ-SIMD-186, REQ-SIMD-187",
                  "Fixed and exponent formatting (SPEC-41 AXS-FLT-051) of %d values/precisions against exact printf results." % len(rows),
                  ["std.text.fmt.float.format_f64_fixed", "std.text.fmt.float.format_f64_exp",
                   "std.text.fmt.float.format_f32_fixed", "std.text.fmt.float.format_f32_exp"])]
    out.append(text_decl(table))
    out.append(decl("KIND", "u32", [r[0] for r in rows], 24, "u32"))
    out.append(decl("BITS", "u64", hexes([r[1] for r in rows], "u64"), 6))
    out.append(decl("PREC", "u32", [r[2] for r in rows], 24, "u32"))
    out.append(decl("FSTART", "u32", [r[3] for r in rows], 16, "u32"))
    out.append(decl("FLEN", "u32", [r[4] for r in rows], 24, "u32"))
    out.append(decl("ESTART", "u32", [r[5] for r in rows], 16, "u32"))
    out.append(decl("ELEN", "u32", [r[6] for r in rows], 24, "u32"))
    out.append(COMMON)
    out.append("""pub fn main() -> i32 {
    let mut failures: i32 = 0;
    let mut i: usize = 0;
    while i < %(n)d {
        let prec = PREC[i] as usize;
        if KIND[i] == 0u32 {
            let x = f64.from_bits(BITS[i]);
            let fixed = format_f64_fixed(x, prec);
            if !same_text(view(fixed), FSTART[i] as usize, FLEN[i] as usize) {
                show_failure(1, i);
                failures = failures + 1;
            }
            let expo = format_f64_exp(x, prec);
            if !same_text(view(expo), ESTART[i] as usize, ELEN[i] as usize) {
                show_failure(2, i);
                failures = failures + 1;
            }
        } else {
            let x = f32.from_bits(BITS[i] as u32);
            let fixed = format_f32_fixed(x, prec);
            if !same_text(view(fixed), FSTART[i] as usize, FLEN[i] as usize) {
                show_failure(3, i);
                failures = failures + 1;
            }
            let expo = format_f32_exp(x, prec);
            if !same_text(view(expo), ESTART[i] as usize, ELEN[i] as usize) {
                show_failure(4, i);
                failures = failures + 1;
            }
        }
        i = i + 1;
    }
""" % {"n": len(rows)})
    out.append(finish(name))
    return name, "\n".join(out)


# ------------------------------------------------------------------------------------------------
# parse_f64 / parse_f32
# ------------------------------------------------------------------------------------------------

def next_up_bits(bits, width):
    return bits + 1


def parse_texts(width, rng):
    """(text, status, expected bits). status 0 = value, 1 = Err(Empty), 2 = Err(InvalidSyntax), 3 = NaN."""
    rows = []

    def value(text):
        rows.append((text, 0, parse_expected(text, width)))

    vals = pick_values64(rng, 70) if width == 64 else pick_values32(rng, 70)
    for b in vals:
        sign, m, e = decompose(b, width)
        x = f32_to_double(b) if width == 32 else f64_from_bits(b)
        value(shortest(b, width))
        value("%.17g" % x)
        value("%.25e" % x)
        if abs(x) < 1e30 and abs(x) > 1e-30:
            value("%.30f" % x)
        dec = exact_decimal(m, e)
        if len(dec) <= 90 or rng.random() < 0.04:
            value(dec if sign == 0 else "-" + dec)
    # midpoints between neighbours: ties to even, just above, just below
    mids = []
    for b in vals[:70]:
        sign, m, e = decompose(b, width)
        if sign:
            continue
        mid = exact_decimal(2 * m + 1, e - 1)
        if len(mid) <= 120 or len(mids) % 7 == 0:
            mids.append(mid)
    for mid in mids:
        value(mid)
        value(mid + "0" * 30 + "1")
        if mid.endswith("5"):
            value(mid[:-1] + "4" + "9" * 30)
    long_mid = mids[-1]
    value(long_mid + "0" * 850 + "1")
    value(mids[3] + "0" * 900)
    edge = [
        "0", "-0", "+0", "0.0", "-0.0", "0e0", "0.0e99999", "000", "00012", "0001.5000", "1", "-1", "+1", "1.", ".5", "-.5",
        "1e0", "1E0", "1e+0", "1e-0", "12e-1", "0.000001", "1e5", "123456789e-5", "9007199254740993", "9007199254740992",
        "9007199254740991", "18014398509481985", "16777217", "16777216", "16777219", "33554433",
        "1e-400", "1e400", "-1e400", "1e-324", "4.9e-324", "2.4703282292062327e-324", "2.4703282292062328e-324",
        "2.4703282292062327208e-324", "4.9406564584124654e-324", "7.4109846876186981e-324", "1e-45", "7e-46", "7.006492321624085e-46",
        "7.0064923216240855e-46", "2.2250738585072011e-308", "2.2250738585072012e-308", "2.2250738585072014e-308",
        "2.225073858507201e-308", "1.7976931348623157e308", "1.7976931348623158e308", "1.797693134862315807e308",
        "1.7976931348623159e308", "3.4028235e38", "3.4028236e38", "3.4028235677973366e38", "3.4028235677973367e38",
        "1.1754943508222875e-38", "1.1754942e-38", "1e38", "1e39", "1e-37", "1e-46", "1e-47", "0.1", "0.2", "0.3", "0.7",
        "5e-324", "123456789012345678901234567890", "1" + "0" * 400, "0." + "0" * 400 + "1", "0." + "0" * 340 + "5",
        "1" + "0" * 308, "1" + "0" * 309, "17976931348623158" + "0" * 292, "123456789" * 100,
        "0." + "123456789" * 100, "1e99999999999", "1e-99999999999", "0e99999999999", "123e-99999999999",
        "1e22", "1e23", "8.41e21", "8.5e21", "4.35", "1e15", "1e16", "9.999999999999999e22",
        "3.14159265358979323846264338327950288", "2.718281828459045235360287471352662497757",
    ]
    for t in edge:
        value(t)
        if t[0] not in "+-":
            value("-" + t)
    # specials
    for t in ("inf", "Inf", "INF", "infinity", "Infinity", "INFINITY", "+inf", "-inf", "-Infinity", "+INF"):
        neg = t.startswith("-")
        bits = ((1 << (width - 1)) if neg else 0) | (((1 << (11 if width == 64 else 8)) - 1) << (52 if width == 64 else 23))
        rows.append((t, 0, bits))
    for t in ("nan", "NaN", "NAN", "+nan", "-nan", "-NaN"):
        rows.append((t, 3, 0))
    rows.append(("", 1, 0))
    bad = ["+", "-", ".", "+.", "e5", ".e5", "1e", "1e+", "1e-", "1.2.3", " 1", "1 ", "1\t", "0x10", "1_0", "1e5.5", "--1", "+-1",
           "i", "in", "infx", "infinit", "nan1", "nann", "1f", "1d", "1,5", "e", "E", "1ee5", "1e5e5", "--", "inf inf",
           "- 1", "+ 1", "1.5.", "..5", "1e+-5", "0x", "1.0f64"]
    for t in bad:
        rows.append((t, 2, 0))
    return rows


def gen_parse(width, rng):
    ty, ut = ("f64", "u64") if width == 64 else ("f32", "u32")
    rows = parse_texts(width, rng)
    if width == 64:
        for text, status, want in rows:
            if status == 0 and text.lower().lstrip("+-") not in ("inf", "infinity"):
                got = bits_of_f64(float(text))
                assert got == want, (text[:60], hex(got), hex(want))
    table = Table()
    starts, lens, status, want = [], [], [], []
    for text, st, bits in rows:
        s, ln = table.add(text)
        starts.append(s)
        lens.append(ln)
        status.append(st)
        want.append(bits)
    name = "parse_f%d" % width
    out = [header(name, 900, "REQ-SIMD-189, REQ-SIMD-186, REQ-SIMD-187",
                  "Exact decimal parsing (SPEC-41 AXS-FLT-052) of %d strings into %s, against exact-rational rounding." % (len(rows), ty),
                  ["std.text.fmt.float.parse_%s_raw" % ty, "std.text.fmt.float.ParseFloatError"])]
    out.append(text_decl(table))
    out.append(decl("START", "u32", starts, 16, "u32"))
    out.append(decl("LEN", "u32", lens, 24, "u32"))
    out.append(decl("STATUS", "u32", status, 24, "u32"))
    out.append(decl("WANT", ut, hexes(want, ut), 6))
    out.append("""
fn show_failure(kind: i32, index: usize) {
    print("FAIL ");
    print_int(kind as i64);
    print(" #");
    print_int(index as i64);
    print("%sn");
}

pub fn main() -> i32 {
    let mut failures: i32 = 0;
    let mut i: usize = 0;
    while i < %d {
        let n = LEN[i] as usize;
        let start = START[i] as usize;
        let mut got: Result<%s, ParseFloatError> = Result.Err(ParseFloatError.Empty);
        if n == 0 {
            got = unsafe { parse_%s_raw(address_of(TEXT[0]), 0) };
        } else {
            got = unsafe { parse_%s_raw(address_of(TEXT[start]), n) };
        }
        let status = STATUS[i];
        match got {
            Result.Ok(x) => {
                if status == 3u32 {
                    if !x.is_nan() {
                        show_failure(1, i);
                        failures = failures + 1;
                    }
                } else if status != 0u32 {
                    show_failure(2, i);
                    failures = failures + 1;
                } else if x.to_bits() != WANT[i] {
                    show_failure(3, i);
                    failures = failures + 1;
                }
            },
            Result.Err(e) => {
                let code: u32 = match e {
                    ParseFloatError.Empty => 1u32,
                    ParseFloatError.InvalidSyntax => 2u32,
                };
                if code != status {
                    show_failure(4, i);
                    failures = failures + 1;
                }
            },
        }
        i = i + 1;
    }
""" % (BS, len(rows), ty, ty, ty))
    out.append(finish(name))
    return name, "\n".join(out)



ROUNDTRIP = """module test.float_%(name)s

use std.core.result.Result
use std.text.string.String
use std.text.fmt.float.format_f64
use std.text.fmt.float.format_f32
use std.text.fmt.float.format_f64_exp
use std.text.fmt.float.format_f32_exp
use std.text.fmt.float.parse_f64_raw
use std.text.fmt.float.parse_f32_raw
use std.text.fmt.float.ParseFloatError

const COUNT: usize = %(count)d;

// splitmix64
fn next(state: mut_view<u64>) -> u64 {
    *state = (*state).wrapping_add(0x9E3779B97F4A7C15u64);
    let mut z = *state;
    z = (z ^ (z >> 30u32)).wrapping_mul(0xBF58476D1CE4E5B9u64);
    z = (z ^ (z >> 27u32)).wrapping_mul(0x94D049BB133111EBu64);
    z ^ (z >> 31u32)
}

fn bits_ok64(s: view<String>, want: u64) -> bool {
    let back = unsafe { parse_f64_raw(s.ptr as *const u8, s.len) };
    match back {
        Result.Ok(y) => y.to_bits() == want,
        Result.Err(_) => false,
    }
}

fn bits_ok32(s: view<String>, want: u32) -> bool {
    let back = unsafe { parse_f32_raw(s.ptr as *const u8, s.len) };
    match back {
        Result.Ok(y) => y.to_bits() == want,
        Result.Err(_) => false,
    }
}

pub fn main() -> i32 {
    let mut failures: i32 = 0;
    let mut state: u64 = 460u64;
    let mut i: usize = 0;
    while i < COUNT {
        // a random finite f64: random bits, or a random 17-digit-ish decimal
        let mut b = next(mut_view(state));
        if (i %% 4) == 1 {
            // small integers and halves exercise the fixed-notation paths
            b = f64.from_bits(0x3FF0000000000000u64 | (b >> 12u32)).to_bits();
        }
        if ((b >> 52u32) & 0x7FFu64) != 0x7FFu64 {
            let x = f64.from_bits(b);
            let s = format_f64(x);
            if !bits_ok64(view(s), b) {
                print("FAIL f64 shortest ");
                print_int(b as i64);
                print("\\n");
                failures = failures + 1;
            }
            if s.len > 26 {
                print("FAIL f64 length ");
                print_int(b as i64);
                print("\\n");
                failures = failures + 1;
            }
            let e = format_f64_exp(x, 16);
            if !bits_ok64(view(e), b) {
                print("FAIL f64 exp17 ");
                print_int(b as i64);
                print("\\n");
                failures = failures + 1;
            }
        }
        let c = (next(mut_view(state)) >> 32u32) as u32;
        if ((c >> 23u32) & 0xFFu32) != 0xFFu32 {
            let y = f32.from_bits(c);
            let t = format_f32(y);
            if !bits_ok32(view(t), c) {
                print("FAIL f32 shortest ");
                print_int(c as i64);
                print("\\n");
                failures = failures + 1;
            }
            if t.len > 21 {
                print("FAIL f32 length ");
                print_int(c as i64);
                print("\\n");
                failures = failures + 1;
            }
            let g = format_f32_exp(y, 8);
            if !bits_ok32(view(g), c) {
                print("FAIL f32 exp9 ");
                print_int(c as i64);
                print("\\n");
                failures = failures + 1;
            }
        }
        i = i + 1;
    }
    if failures == 0 {
        print("ok float_fmt %(name)s\\n");
    }
    failures
}
"""


def gen_roundtrip(name, count, native_only):
    lines = ["// test: run"]
    if native_only:
        lines.append("// modes: native")
        lines.append("// reason: heavy twin (%d values per type) of roundtrip.ax, which runs in both modes" % count)
    else:
        lines.append("// modes: interp native")
    lines.append("// timeout: %d" % (600 if native_only else 300))
    lines.append("// covers: REQ-SIMD-189, REQ-SIMD-186")
    lines.append("// flags: --step-limit 2000000000")
    lines.append("// stdout: ok float_fmt %s%sn" % (name, BS))
    lines.append("")
    lines.append("// GENERATED by tests/std/float_fmt/make_vectors.py (T460). Do not edit by hand: edit the generator and rerun it.")
    lines.append("// Round trip of %d pseudo-random f64 and f32 values: parse(format(x)) has the bits of x, the shortest text is short," % count)
    lines.append("// and 17 (9) significant digits in exponent form read back exactly.")
    lines.append("")
    return name, "\n".join(lines) + "\n" + (ROUNDTRIP % {"name": name, "count": count}).replace("%%", "%")

# ------------------------------------------------------------------------------------------------

def generate_all():
    rng = random.Random(460)
    files = []
    files.append(gen_shortest(64, rng))
    files.append(gen_shortest(32, rng))
    files.append(gen_fixed_exp(rng))
    files.append(gen_parse(64, rng))
    files.append(gen_parse(32, rng))
    files.append(gen_roundtrip("roundtrip", 24, False))
    files.append(gen_roundtrip("roundtrip_stress", 12000, True))
    return files


def write(name, text, check):
    path = os.path.join(HERE, name + ".ax")
    data = text.replace("\r\n", "\n")
    if check:
        try:
            with open(path, encoding="utf-8", newline="") as f:
                cur = f.read()
        except OSError:
            cur = None
        if cur != data:
            sys.stderr.write("stale: %s\n" % path)
            return False
        return True
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    ok = True
    for name, text in generate_all():
        ok = write(name, text, args.check) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
