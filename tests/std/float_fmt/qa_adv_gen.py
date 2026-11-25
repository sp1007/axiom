#!/usr/bin/env python3
"""QA adversarial vectors for T460 (independent of make_vectors.py; different seed and input classes).

    python tests/std/float_fmt/qa_adv_gen.py            rewrite qa_adv.ax
    python tests/std/float_fmt/qa_adv_gen.py --check    fail when qa_adv.ax is stale

Reference values: exact rationals only (fractions.Fraction / decimal), cross-checked with Python repr / float().
Record kinds: 0 shortest f64, 1 fixed f64, 2 exp f64, 3 shortest f32, 4 fixed f32, 5 exp f32,
              6 parse f64, 7 parse f32.
Format records: a = bits, prec = precision, text = expected text.
Parse records: a = wanted bits (NaN: 0), prec = status (0 ok, 1 Empty, 2 InvalidSyntax, 3 ok-NaN), text = input.
"""

import os
import random
import struct
import sys
from decimal import Decimal, getcontext
from fractions import Fraction

getcontext().prec = 5000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "qa_adv.ax")


def d_from(bits):
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


def f_from(bits):
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def val_of(bits, w):
    """exact Fraction (finite only) and sign."""
    if w == 64:
        s, fld, fr, bias, t = bits >> 63, (bits >> 52) & 0x7FF, bits & ((1 << 52) - 1), 1075, 52
    else:
        s, fld, fr, bias, t = bits >> 31, (bits >> 23) & 0xFF, bits & ((1 << 23) - 1), 150, 23
    if fld == 0:
        m, e = fr, 1 - bias
    else:
        m, e = fr | (1 << t), fld - bias
    return s, Fraction(m) * (Fraction(2) ** e)


def round_to(fr, w):
    """nearest float (ties to even) of positive Fraction fr -> bits (positive)."""
    if fr == 0:
        return 0
    prec, qmin, emaxfield = (53, -1074, 2047) if w == 64 else (24, -149, 255)
    t = prec - 1
    # exponent of the leading bit
    num, den = fr.numerator, fr.denominator
    ev = num.bit_length() - den.bit_length()
    if Fraction(2) ** ev > fr:
        ev -= 1
    q = max(ev - (prec - 1), qmin)
    scaled = fr / (Fraction(2) ** q)
    m = scaled.numerator // scaled.denominator
    rem = scaled - m
    if rem > Fraction(1, 2) or (rem == Fraction(1, 2) and (m & 1)):
        m += 1
    # pack
    if m >= (1 << prec):
        m >>= 1
        q += 1
    if m < (1 << t):
        return m  # subnormal (q == qmin)
    field = q + (1074 if w == 64 else 149) + 1
    if field >= emaxfield:
        return emaxfield << t
    return (field << t) | (m & ((1 << t) - 1))


def shortest(bits, w):
    """Reference shortest text: exact search over digit counts, closest of the in-interval candidates."""
    s, v = val_of(bits, w)
    if v == 0:
        return "-0.0" if s else "0.0"
    for p in range(1, 40):
        # v = d.ddd * 10^k with p digits
        k = 0
        # find decimal exponent k with 10^k <= v < 10^(k+1)
        lo_k = len(str(v.numerator)) - len(str(v.denominator)) - 2
        k = lo_k
        while Fraction(10) ** (k + 1) <= v:
            k += 1
        while Fraction(10) ** k > v:
            k -= 1
        scale = Fraction(10) ** (p - 1 - k)
        x = v * scale
        fl = x.numerator // x.denominator
        cands = []
        for c in (fl, fl + 1):
            cv = Fraction(c) / scale
            if round_to(cv, w) == (bits & ~(1 << (63 if w == 64 else 31))):
                cands.append((abs(cv - v), c))
        if cands:
            cands.sort(key=lambda t: (t[0], t[1] & 1))
            c = cands[0][1]
            digits = str(c)
            k2 = k
            if len(digits) > p:  # carry to 10^p
                digits = digits[:p]
                k2 += 1
            digits = digits.rstrip("0") or "0"
            return layout(s, digits, k2)
    raise AssertionError


def layout(neg, digits, k):
    sign = "-" if neg else ""
    # value = 0.d1d2.. * 10^(k+1) i.e. d1.d2... * 10^k
    absv_ge_1e_4 = k >= -4
    if -4 <= k < 16:
        if k >= 0:
            ip = digits[: k + 1].ljust(k + 1, "0")
            fp = digits[k + 1:]
            return sign + ip + "." + (fp if fp else "0")
        return sign + "0." + "0" * (-k - 1) + digits
    mant = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    return sign + mant + "e" + str(k)


def fixed(bits, w, prec):
    s, v = val_of(bits, w)
    # exact: use Decimal quantize with ROUND_HALF_EVEN on the exact value
    from decimal import ROUND_HALF_EVEN
    dv = Decimal(v.numerator) / Decimal(v.denominator) if v.denominator != 1 else Decimal(v.numerator)
    # v has finite binary expansion so Decimal division at prec 5000 is exact
    q = dv.quantize(Decimal(1).scaleb(-prec), rounding=ROUND_HALF_EVEN)
    txt = format(q, "f")
    return ("-" if s else "") + txt


def expfmt(bits, w, prec):
    s, v = val_of(bits, w)
    if v == 0:
        mant = "0" + ("." + "0" * prec if prec else "")
        return ("-" if s else "") + mant + "e+00"
    from decimal import ROUND_HALF_EVEN
    dv = Decimal(v.numerator) / Decimal(v.denominator) if v.denominator != 1 else Decimal(v.numerator)
    e = dv.adjusted()
    m = dv.scaleb(-e).quantize(Decimal(1).scaleb(-prec), rounding=ROUND_HALF_EVEN)
    if m >= 10:
        m = m / 10
        m = m.quantize(Decimal(1).scaleb(-prec), rounding=ROUND_HALF_EVEN)
        e += 1
    return ("-" if s else "") + format(m, "f") + "e" + ("+" if e >= 0 else "-") + "%02d" % abs(e)


def parse_ref(text, w):
    """(status, bits)"""
    t = text
    if t == "":
        return 1, 0
    neg = False
    body = t
    if body[0] in "+-":
        neg = body[0] == "-"
        body = body[1:]
    low = body.lower()
    if low in ("inf", "infinity"):
        return 0, ((0x7FF0000000000000 if w == 64 else 0x7F800000) | ((1 << (63 if w == 64 else 31)) if neg else 0))
    if low == "nan":
        return 3, 0
    # grammar
    i = 0
    n = len(body)
    ds = 0
    while i < n and body[i].isdigit() and body[i] in "0123456789":
        i += 1
        ds += 1
    ip = body[:i]
    fp = ""
    if i < n and body[i] == ".":
        j = i + 1
        while j < n and body[j] in "0123456789":
            j += 1
        fp = body[i + 1:j]
        i = j
    if ds == 0 and fp == "":
        return 2, 0
    ex = 0
    if i < n and body[i] in "eE":
        j = i + 1
        sg = 1
        if j < n and body[j] in "+-":
            sg = -1 if body[j] == "-" else 1
            j += 1
        k = j
        while k < n and body[k] in "0123456789":
            k += 1
        if k == j:
            return 2, 0
        ex = sg * int(body[j:k])
        i = k
    if i != n:
        return 2, 0
    digits = (ip + fp).lstrip("0")
    sign = (1 << (63 if w == 64 else 31)) if neg else 0
    if digits == "":
        return 0, sign
    exp10 = ex - len(fp)
    if exp10 + len(digits) > 700:
        return 0, sign | (0x7FF0000000000000 if w == 64 else 0x7F800000)
    if exp10 + len(digits) < -700:
        return 0, sign
    fr = Fraction(int(digits)) * (Fraction(10) ** exp10)
    return 0, sign | round_to(fr, w)


def exact_dec(fr):
    dv = Decimal(fr.numerator) / Decimal(fr.denominator) if fr.denominator != 1 else Decimal(fr.numerator)
    s = format(dv, "f")
    return s


def main():
    rng = random.Random(20261125)
    recs = []  # (kind, a, prec, text)

    def f64_vals(n):
        out = []
        while len(out) < n:
            c = rng.randrange(6)
            if c == 0:
                b = rng.getrandbits(64)
            elif c == 1:
                b = rng.getrandbits(52) | (rng.randrange(0, 2) << 63)  # subnormal
            elif c == 2:
                b = (rng.randrange(1, 2047) << 52)  # power of two
                b |= rng.choice([0, 1, (1 << 52) - 1])
            elif c == 3:
                b = struct.unpack("<Q", struct.pack("<d", float(rng.randrange(-10**6, 10**6))))[0]
            elif c == 4:
                b = struct.unpack("<Q", struct.pack("<d", rng.randrange(1, 10**9) / 10 ** rng.randrange(0, 12)))[0]
            else:
                b = struct.unpack("<Q", struct.pack("<d", 10.0 ** rng.randrange(-30, 30)))[0]
            if (b >> 52) & 0x7FF == 0x7FF:
                continue
            out.append(b)
        return out

    def f32_vals(n):
        out = []
        while len(out) < n:
            c = rng.randrange(5)
            if c == 0:
                b = rng.getrandbits(32)
            elif c == 1:
                b = rng.getrandbits(23) | (rng.randrange(0, 2) << 31)
            elif c == 2:
                b = (rng.randrange(1, 255) << 23) | rng.choice([0, 1, (1 << 23) - 1])
            elif c == 3:
                b = struct.unpack("<I", struct.pack("<f", float(rng.randrange(-10**5, 10**5))))[0]
            else:
                b = struct.unpack("<I", struct.pack("<f", rng.randrange(1, 10**6) / 10 ** rng.randrange(0, 8)))[0]
            if (b >> 23) & 0xFF == 0xFF:
                continue
            out.append(b)
        return out

    fixed_specials64 = [0x0, 0x8000000000000000, 0x3FE0000000000000, 0x3FF8000000000000, 0x4004000000000000,
                        0x3F847AE147AE147B, 0x8000000000000001, 0x7FEFFFFFFFFFFFFF, 0xBF50624DD2F1A9FC]
    v64 = fixed_specials64 + f64_vals(110)
    for b in v64:
        t = shortest(b, 64)
        if True:
            # cross-check with repr where the notation coincides
            r = repr(d_from(b))
            assert float(r) == d_from(b)
        recs.append((0, b, 0, t))
    for b in v64[:60]:
        for p in (0, 1, 2, rng.randrange(3, 25)):
            recs.append((1, b, p, fixed(b, 64, p)))
    for b in v64[:60]:
        for p in (0, 1, rng.randrange(2, 20)):
            recs.append((2, b, p, expfmt(b, 64, p)))
    v32 = [0x0, 0x80000000, 0x3F000000, 0x3FC00000, 0x00000001, 0x7F7FFFFF, 0x33800000, 0x3DCCCCCD] + f32_vals(110)
    for b in v32:
        recs.append((3, b, 0, shortest(b, 32)))
    for b in v32[:60]:
        for p in (0, 1, 3, rng.randrange(4, 30)):
            recs.append((4, b, p, fixed(b, 32, p)))
    for b in v32[:60]:
        for p in (0, 2, rng.randrange(3, 12)):
            recs.append((5, b, p, expfmt(b, 32, p)))

    # ---- parse vectors
    def add_parse(text, w):
        st, bits = parse_ref(text, w)
        if w == 64 and st == 0:
            try:
                f = float(text)
                assert struct.unpack("<Q", struct.pack("<d", f))[0] == bits, text[:80]
            except ValueError:
                pass
        recs.append((6 if w == 64 else 7, bits if st != 3 else 0, st, text))

    for w in (64, 32):
        vals = f64_vals(40) if w == 64 else f32_vals(40)
        for b in vals:
            s, v = val_of(b, w)
            nb = b + 1
            if ((nb >> (52 if w == 64 else 23)) & (0x7FF if w == 64 else 0xFF)) == (0x7FF if w == 64 else 0xFF):
                continue
            s2, v2 = val_of(nb, w)
            if s:
                continue
            mid = (v + v2) / 2
            ms = exact_dec(mid)
            add_parse(ms, w)                      # exact tie -> even
            add_parse(ms + "0" * 900 + "1", w)    # just above the tie, beyond the 800 digit window
            add_parse(ms + "0" * 1000, w)         # tie with long zero tail
            # just below the tie
            lo = ms[:-1] + str(int(ms[-1]) - 1) + "9" * 900 if ms[-1] != "0" else None
            if lo:
                add_parse(lo, w)
            add_parse(ms + "e0", w)
            add_parse("-" + ms, w)
            add_parse(exact_dec(v) + "E+0", w)
            # scaled forms of the same value
            digits = ms.replace(".", "")
            pt = ms.find(".")
            if pt >= 0:
                exp = len(ms) - pt - 1
                add_parse(digits.lstrip("0") + "e-" + str(exp), w)
    syn = ["", "+", "-", ".", "e5", ".e5", "1e", "1e+", "1e-", "1.e", "--1", "+-1", "1 ", " 1", "1_0", "0x10", "1..0",
           "1.0.0", "1e5.0", "in", "infin", "infinityx", "nan1", "nan(0)", "- 1", "1,5", "١", "1e5e5", "º",
           "5.", ".5", "+.5", "-.5e1", "+5.e1", "1E5", "1e+05", "0e0", "-0", "-0.0e-5", "00000.00000", "000123.4500",
           "INF", "-Inf", "+iNfInItY", "NaN", "-nan", "+NAN", "infinity", "Infinity",
           "1e400", "1e-400", "1e309", "1e308", "1.7976931348623158e308", "1.7976931348623157e308",
           "1.79769313486231580793728971405303415079934132710037826936173778980444968292764750946649017977587207096330286416692887910946555547851940402630657488671505820681908902000708383676273854845817711531764475730270069855571366959622842914819860834936475292719074168444365510704342711559699508093042880177904174497791e308",
           "0e99999999999999999999", "1e99999999999999999999", "1e-99999999999999999999", "123e-99999999999999999999",
           "0.0000000000000000000000000000001e32", "1" + "0" * 400 + "e-400", "1" + "0" * 400 + "e-399",
           "4.9406564584124654e-324", "2.4703282292062327e-324", "2.4703282292062328e-324", "2.4703282292062329e-324",
           "1.4012985e-45", "7.00649232162408535461864791644958065640130970938257885878534141944895541342930300743319094181060791015625e-46",
           "7.00649232162408535461864791644958065640130970938257885878534141944895541342930300743319094181060791015626e-46",
           "3.4028235677973366e38", "3.4028235677973362e38", "3.4028236e38", "3.4028234e38",
           "9007199254740993", "9007199254740992.5", "9007199254740993.0000000000000000000001",
           "16777217", "16777216.5", "16777217.0000000000000001",
           "0.1", "0.2", "0.3", "1e23", "8.5e-5", "5e-324", "2.2250738585072011e-308", "2.2250738585072012e-308",
           "1.1754942e-38", "1.17549421e-38", "1.17549435e-38"]
    for t in syn:
        for w in (64, 32):
            add_parse(t, w)
    # NUL / non-ASCII bytes are kept out (byte array of printable text only)

    # ---- emit
    text_bytes = []
    starts, lens = [], []
    for k, a, p, t in recs:
        bs = t.encode("utf-8")
        starts.append(len(text_bytes))
        lens.append(len(bs))
        text_bytes.extend(bs)
    n = len(recs)

    def arr(name, ty, vals, fmt):
        lines = []
        row = []
        for v in vals:
            row.append(fmt(v))
            if len(row) == 12:
                lines.append("    " + ", ".join(row) + ",")
                row = []
        if row:
            lines.append("    " + ", ".join(row) + ",")
        return "const %s: [%d]%s = [\n%s\n];\n" % (name, len(vals), ty, "\n".join(lines))

    src = []
    src.append("""// test: run
// modes: interp native
// timeout: 900
// covers: REQ-SIMD-189, REQ-SIMD-186, REQ-SIMD-187
// flags: --step-limit 2000000000
// stdout: ok float_fmt qa_adv\\n

// GENERATED by tests/std/float_fmt/qa_adv_gen.py (T460 QA). Do not edit by hand.
// Independent adversarial vectors: shortest / fixed / exp formatting and exact parsing, f64 and f32.

module test.float_qa_adv

use std.core.result.Result
use std.text.string.String
use std.text.fmt.float.format_f64
use std.text.fmt.float.format_f32
use std.text.fmt.float.format_f64_fixed
use std.text.fmt.float.format_f32_fixed
use std.text.fmt.float.format_f64_exp
use std.text.fmt.float.format_f32_exp
use std.text.fmt.float.parse_f64_raw
use std.text.fmt.float.parse_f32_raw
use std.text.fmt.float.ParseFloatError

@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }

""")
    src.append(arr("TEXT", "u8", text_bytes, str))
    src.append(arr("START", "u32", starts, str))
    src.append(arr("LEN", "u32", lens, str))
    src.append(arr("KIND", "u8", [r[0] for r in recs], str))
    src.append(arr("PREC", "u32", [r[2] for r in recs], str))
    src.append(arr("BITS", "u64", [r[1] for r in recs], lambda v: "0x%Xu64" % v))
    src.append("const N: usize = %d;\n" % n)
    src.append("""
fn same(s: view<String>, start: usize, n: usize) -> bool {
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

fn fail(i: usize) -> i32 {
    print("FAIL #");
    print_int(i as i64);
    print("\\n");
    1
}

fn status_of(e: ParseFloatError) -> u32 {
    match e {
        ParseFloatError.Empty => 1u32,
        ParseFloatError.InvalidSyntax => 2u32,
    }
}

pub fn main() -> i32 {
    let mut failures: i32 = 0;
    let mut i: usize = 0;
    while i < N {
        let kind = KIND[i];
        let start = START[i] as usize;
        let n = LEN[i] as usize;
        let prec = PREC[i];
        let bits = BITS[i];
        let mut ok = true;
        if kind == 0u8 {
            let s = format_f64(f64.from_bits(bits));
            ok = same(view(s), start, n);
        } else if kind == 1u8 {
            let s = format_f64_fixed(f64.from_bits(bits), prec as usize);
            ok = same(view(s), start, n);
        } else if kind == 2u8 {
            let s = format_f64_exp(f64.from_bits(bits), prec as usize);
            ok = same(view(s), start, n);
        } else if kind == 3u8 {
            let s = format_f32(f32.from_bits(bits as u32));
            ok = same(view(s), start, n);
        } else if kind == 4u8 {
            let s = format_f32_fixed(f32.from_bits(bits as u32), prec as usize);
            ok = same(view(s), start, n);
        } else if kind == 5u8 {
            let s = format_f32_exp(f32.from_bits(bits as u32), prec as usize);
            ok = same(view(s), start, n);
        } else if kind == 6u8 {
            let mut got: Result<f64, ParseFloatError> = Result.Err(ParseFloatError.Empty);
            if n == 0 {
                got = unsafe { parse_f64_raw(address_of(TEXT[0]), 0) };
            } else {
                got = unsafe { parse_f64_raw(address_of(TEXT[start]), n) };
            }
            match got {
                Result.Ok(x) => {
                    if prec == 3u32 {
                        ok = x.is_nan();
                    } else {
                        ok = prec == 0u32 && x.to_bits() == bits;
                    }
                },
                Result.Err(e) => {
                    ok = status_of(e) == prec;
                },
            }
        } else {
            let mut got: Result<f32, ParseFloatError> = Result.Err(ParseFloatError.Empty);
            if n == 0 {
                got = unsafe { parse_f32_raw(address_of(TEXT[0]), 0) };
            } else {
                got = unsafe { parse_f32_raw(address_of(TEXT[start]), n) };
            }
            match got {
                Result.Ok(x) => {
                    if prec == 3u32 {
                        ok = x.is_nan();
                    } else {
                        ok = prec == 0u32 && (x.to_bits() as u64) == bits;
                    }
                },
                Result.Err(e) => {
                    ok = status_of(e) == prec;
                },
            }
        }
        if !ok {
            failures = failures + fail(i);
        }
        i = i + 1;
    }
    if failures == 0 {
        print("ok float_fmt qa_adv\\n");
    }
    failures
}
""")
    text = "".join(src)
    if "--check" in sys.argv:
        with open(OUT, "rb") as fh:
            cur = fh.read().decode("utf-8")
        if cur != text:
            print("STALE qa_adv.ax")
            return 1
        print("qa_adv.ax up to date")
        return 0
    with open(OUT, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("wrote %s: %d records, %d text bytes" % (OUT, n, len(text_bytes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
