#!/usr/bin/env python3
"""QA adversarial vectors for the T460 float operations (independent of make_vectors.py).

    python tests/std/float_fmt/qa_adv_ops_gen.py            rewrite qa_adv_ops.ax
    python tests/std/float_fmt/qa_adv_ops_gen.py --check    fail when qa_adv_ops.ax is stale

Reference: exact rationals (fractions.Fraction) for mul_add / rounding / fract, and the unsigned-key
characterisation of IEEE totalOrder (key = bits ^ 0x8000.. for positives, ~bits for negatives) for total_cmp.
Record: op, wide (0 = f64, 1 = f32), a, b, c, want. For total_cmp want is 0 Less, 1 Equal, 2 Greater.
"""

import os
import random
import struct
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "qa_adv_ops.ax")

OPS = ["fma", "floor", "ceil", "trunc", "round", "ties_even", "fract", "total_cmp", "min", "max", "next_up", "next_down"]


def spec(w):
    if w == 64:
        return dict(bits=64, t=52, bias=1075, emax=0x7FF, qmin=-1074, prec=53)
    return dict(bits=32, t=23, bias=150, emax=0xFF, qmin=-149, prec=24)


def val_of(bits, w):
    S = spec(w)
    s = bits >> (S["bits"] - 1)
    fld = (bits >> S["t"]) & S["emax"]
    fr = bits & ((1 << S["t"]) - 1)
    if fld == 0:
        m, e = fr, S["qmin"]
    else:
        m, e = fr | (1 << S["t"]), fld - S["bias"]
    return s, Fraction(m) * (Fraction(2) ** e)


def is_nan(bits, w):
    S = spec(w)
    return ((bits >> S["t"]) & S["emax"]) == S["emax"] and (bits & ((1 << S["t"]) - 1)) != 0


def is_inf(bits, w):
    S = spec(w)
    return ((bits >> S["t"]) & S["emax"]) == S["emax"] and (bits & ((1 << S["t"]) - 1)) == 0


def round_to(fr, w):
    """nearest float bits (ties to even) of a non-negative Fraction."""
    S = spec(w)
    if fr == 0:
        return 0
    prec, qmin, t = S["prec"], S["qmin"], S["t"]
    ev = fr.numerator.bit_length() - fr.denominator.bit_length()
    if Fraction(2) ** ev > fr:
        ev -= 1
    q = max(ev - (prec - 1), qmin)
    scaled = fr / (Fraction(2) ** q)
    m = scaled.numerator // scaled.denominator
    rem = scaled - m
    if rem > Fraction(1, 2) or (rem == Fraction(1, 2) and (m & 1)):
        m += 1
    if m >= (1 << prec):
        m >>= 1
        q += 1
    if m < (1 << t):
        return m
    field = q - qmin + 1
    if field >= S["emax"]:
        return S["emax"] << t
    return (field << t) | (m & ((1 << t) - 1))


def signed(bits_pos, neg, w):
    return bits_pos | ((1 << (spec(w)["bits"] - 1)) if neg else 0)


def fma_ref(a, b, c, w):
    S = spec(w)
    sa, va = val_of(a, w)
    sb, vb = val_of(b, w)
    sc, vc = val_of(c, w)
    p = va * vb * (-1 if (sa ^ sb) else 1)
    cv = vc * (-1 if sc else 1)
    if va == 0 or vb == 0:
        # product is a signed zero; result is c, or a zero with the RN sign rule
        if vc != 0:
            return c
        pneg = bool(sa ^ sb)
        return signed(0, pneg and bool(sc), w)
    tot = p + cv
    if tot == 0:
        return 0  # exact cancellation -> +0
    return signed(round_to(abs(tot), w), tot < 0, w)


def rnd_ref(op, x, w):
    s, v = val_of(x, w)
    neg = bool(s)
    sv = -v if neg else v
    fl = sv.numerator // sv.denominator  # floor
    if op == "floor":
        r = fl
    elif op == "ceil":
        r = fl if sv == fl else fl + 1
    elif op == "trunc":
        r = fl if sv >= 0 else (fl if sv == fl else fl + 1)
    elif op == "round":
        r = int(abs(sv) + Fraction(1, 2)) if sv >= 0 else -int(abs(sv) + Fraction(1, 2))
    elif op == "ties_even":
        a = abs(sv)
        f0 = a.numerator // a.denominator
        rem = a - f0
        if rem > Fraction(1, 2) or (rem == Fraction(1, 2) and (f0 & 1)):
            f0 += 1
        r = f0 if sv >= 0 else -f0
    if r == 0:
        return signed(0, neg, w)  # a zero result keeps the sign of the input
    return signed(round_to(Fraction(abs(r)), w), r < 0, w)


def fract_ref(x, w):
    s, v = val_of(x, w)
    sv = -v if s else v
    tr = sv.numerator // sv.denominator if sv >= 0 else -((-sv).numerator // (-sv).denominator)
    d = sv - tr
    if d == 0:
        return 0  # x - trunc(x) of an integral (or zero) value is +0.0 in round-to-nearest
    return signed(round_to(abs(d), w), d < 0, w)


def key(bits, w):
    S = spec(w)
    sign = 1 << (S["bits"] - 1)
    mask = (1 << S["bits"]) - 1
    return (bits ^ sign) if not (bits & sign) else (~bits & mask)


def minmax_ref(op, a, b, w):
    if is_nan(a, w) and is_nan(b, w):
        return None  # only check is-nan
    if is_nan(a, w):
        return b
    if is_nan(b, w):
        return a
    sa, va = val_of(a, w)
    sb, vb = val_of(b, w)
    xa = -va if sa else va
    xb = -vb if sb else vb
    if xa == xb:
        if xa == 0 and sa != sb:
            neg = a if sa else b
            pos = b if sa else a
            return neg if op == "min" else pos
        return a
    if op == "min":
        return a if xa < xb else b
    return a if xa > xb else b


def next_ref(op, x, w):
    S = spec(w)
    sign = 1 << (S["bits"] - 1)
    absb = x & (sign - 1)
    neg = bool(x & sign)
    if is_nan(x, w):
        return None
    if op == "next_up":
        if x == (S["emax"] << S["t"]):
            return x
        if absb == 0:
            return 1
        return x - 1 if neg else x + 1
    if x == (sign | (S["emax"] << S["t"])):
        return x
    if absb == 0:
        return sign | 1
    return x + 1 if neg else x - 1


def main():
    rng = random.Random(0x7460AD5)
    recs = []

    def pick(w, n):
        S = spec(w)
        out = []
        top = (1 << S["bits"]) - 1
        while len(out) < n:
            c = rng.randrange(8)
            if c == 0:
                b = rng.getrandbits(S["bits"])
            elif c == 1:  # integers and halves
                x = rng.randrange(-5000, 5000) + rng.choice([0, 0.5, 0.25, 0.75])
                b = struct.unpack("<Q" if w == 64 else "<I", struct.pack("<d" if w == 64 else "<f", x))[0]
            elif c == 2:  # near 2^(t) where fractional bits vanish
                e = S["bias"] - 1 + rng.randrange(S["t"] - 3, S["t"] + 3)
                b = (e << S["t"]) | rng.getrandbits(S["t"])
                b |= rng.randrange(2) << (S["bits"] - 1)
            elif c == 3:  # subnormals
                b = rng.getrandbits(S["t"]) | (rng.randrange(2) << (S["bits"] - 1))
            elif c == 4:  # tiny and huge exponents
                b = (rng.choice([1, 2, 3, S["emax"] - 2, S["emax"] - 1]) << S["t"]) | rng.getrandbits(S["t"])
                b |= rng.randrange(2) << (S["bits"] - 1)
            elif c == 5:  # values just around 0.5, 1.5, 2.5
                x = rng.choice([0.5, 1.5, 2.5, -0.5, -1.5, -2.5, 0.49999999999999994, 3.5, 0.25])
                b = struct.unpack("<Q" if w == 64 else "<I", struct.pack("<d" if w == 64 else "<f", x))[0]
                b += rng.choice([-1, 0, 0, 1]) if (b & ((1 << S["t"]) - 1)) not in (0,) or True else 0
                b &= top
            elif c == 6:
                b = rng.choice([0, 1 << (S["bits"] - 1)])
            else:
                b = rng.getrandbits(S["bits"])
            recs_ok = not is_nan(b, w) and not is_inf(b, w)
            if recs_ok:
                out.append(b)
        return out

    for w in (64, 32):
        wide = 0 if w == 64 else 1
        xs = pick(w, 160)
        for x in xs:
            for op in ("floor", "ceil", "trunc", "round", "ties_even"):
                recs.append((OPS.index(op), wide, x, 0, 0, rnd_ref(op, x, w)))
            recs.append((OPS.index("fract"), wide, x, 0, 0, fract_ref(x, w)))
            nu = next_ref("next_up", x, w)
            nd = next_ref("next_down", x, w)
            recs.append((OPS.index("next_up"), wide, x, 0, 0, nu))
            recs.append((OPS.index("next_down"), wide, x, 0, 0, nd))
        # total_cmp / min / max on pairs, NaNs with payloads included for total_cmp
        S = spec(w)
        specials = [0, 1 << (S["bits"] - 1), S["emax"] << S["t"], (S["emax"] << S["t"]) | (1 << (S["bits"] - 1)),
                    (S["emax"] << S["t"]) | 1, (S["emax"] << S["t"]) | (1 << (S["t"] - 1)),
                    (1 << (S["bits"] - 1)) | (S["emax"] << S["t"]) | 1,
                    (1 << (S["bits"] - 1)) | (S["emax"] << S["t"]) | (1 << (S["t"] - 1)) | 5, 1, (1 << (S["bits"] - 1)) | 1]
        pool = specials + pick(w, 24)
        for a in pool:
            for b in pool:
                ka, kb = key(a, w), key(b, w)
                recs.append((OPS.index("total_cmp"), wide, a, b, 0, 0 if ka < kb else (1 if ka == kb else 2)))
        fin = [p for p in pool if not is_nan(p, w) and not is_inf(p, w)]
        for a in fin[:20]:
            for b in fin[:20]:
                for op in ("min", "max"):
                    r = minmax_ref(op, a, b, w)
                    recs.append((OPS.index(op), wide, a, b, 0, r))
        # fma
        for _ in range(300):
            a, b, c = pick(w, 3)
            kind = rng.randrange(6)
            if kind == 1:  # cancellation: c = -round(a*b)
                sa, va = val_of(a, w)
                sb, vb = val_of(b, w)
                prod = va * vb
                bits = round_to(prod, w)
                if not is_inf(bits, w):
                    c = signed(bits, not (sa ^ sb), w)
            elif kind == 2:  # c tiny relative to the product
                c = signed((1 << spec(w)["t"]) * 0 + rng.randrange(1, 1 << 10), bool(rng.getrandbits(1)), w)
            elif kind == 3:  # near-overflow product
                a = signed((spec(w)["emax"] - 1 - rng.randrange(0, 3)) << spec(w)["t"] | rng.getrandbits(spec(w)["t"]), False, w)
                b = signed(((spec(w)["bias"] - 1 + rng.randrange(0, 2)) << spec(w)["t"]) | rng.getrandbits(spec(w)["t"]), bool(rng.getrandbits(1)), w)
            elif kind == 4:  # subnormal result range
                a = signed((rng.randrange(1, 40) << spec(w)["t"]) | rng.getrandbits(spec(w)["t"]), bool(rng.getrandbits(1)), w)
                b = signed(((spec(w)["bias"] - 1 - rng.randrange(40, 70)) << spec(w)["t"]) | rng.getrandbits(spec(w)["t"]) if w == 32 else
                           ((rng.randrange(1, 40)) << spec(w)["t"]) | rng.getrandbits(spec(w)["t"]), bool(rng.getrandbits(1)), w)
            elif kind == 5:  # zero factor
                a = rng.choice([0, 1 << (spec(w)["bits"] - 1)])
                c = rng.choice([0, 1 << (spec(w)["bits"] - 1), c])
            recs.append((0, wide, a, b, c, fma_ref(a, b, c, w)))

    # emit; None wants (NaN checks) are skipped
    recs = [r for r in recs if r[5] is not None]

    def arr(name, ty, vals, fmt):
        lines, row = [], []
        for v in vals:
            row.append(fmt(v))
            if len(row) == 8:
                lines.append("    " + ", ".join(row) + ",")
                row = []
        if row:
            lines.append("    " + ", ".join(row) + ",")
        return "const %s: [%d]%s = [\n%s\n];\n" % (name, len(vals), ty, "\n".join(lines))

    hx = lambda v: "0x%Xu64" % v
    out = ["""// test: run
// modes: interp native
// timeout: 900
// covers: REQ-SIMD-160, REQ-SIMD-272, REQ-SIMD-322
// flags: --step-limit 2000000000
// stdout: ok float_fmt qa_adv_ops\\n

// GENERATED by tests/std/float_fmt/qa_adv_ops_gen.py (T460 QA). Do not edit by hand.
// Adversarial vectors for mul_add, floor/ceil/trunc/round/round_ties_even/fract, next_up/next_down,
// total_cmp and min/max, f64 and f32 (exact-rational / unsigned-key references).

module test.float_qa_adv_ops

use std.core.cmp.Ordering
use std.core.float.FpCategory

"""]
    out.append(arr("OP", "u8", [r[0] for r in recs], str))
    out.append(arr("WIDE", "u8", [r[1] for r in recs], str))
    out.append(arr("A", "u64", [r[2] for r in recs], hx))
    out.append(arr("B", "u64", [r[3] for r in recs], hx))
    out.append(arr("C", "u64", [r[4] for r in recs], hx))
    out.append(arr("WANT", "u64", [r[5] for r in recs], hx))
    out.append("const N: usize = %d;\n" % len(recs))
    out.append("""
fn fail(i: usize, op: u8, got: u64) -> i32 {
    print("FAIL #");
    print_int(i as i64);
    print(" op ");
    print_int(op as i64);
    print(" got ");
    print_int(got as i64);
    print("\\n");
    1
}

fn ord_code(o: Ordering) -> u64 {
    match o {
        Ordering.Less => 0u64,
        Ordering.Equal => 1u64,
        Ordering.Greater => 2u64,
    }
}

fn run64(op: u8, a: f64, b: f64, c: f64) -> u64 {
    if op == 0u8 {
        return a.mul_add(b, c).to_bits();
    } else if op == 1u8 {
        return a.floor().to_bits();
    } else if op == 2u8 {
        return a.ceil().to_bits();
    } else if op == 3u8 {
        return a.trunc().to_bits();
    } else if op == 4u8 {
        return a.round().to_bits();
    } else if op == 5u8 {
        return a.round_ties_even().to_bits();
    } else if op == 6u8 {
        return a.fract().to_bits();
    } else if op == 7u8 {
        return ord_code(a.total_cmp(b));
    } else if op == 8u8 {
        return a.min(b).to_bits();
    } else if op == 9u8 {
        return a.max(b).to_bits();
    } else if op == 10u8 {
        return a.next_up().to_bits();
    }
    a.next_down().to_bits()
}

fn run32(op: u8, a: f32, b: f32, c: f32) -> u64 {
    if op == 0u8 {
        return a.mul_add(b, c).to_bits() as u64;
    } else if op == 1u8 {
        return a.floor().to_bits() as u64;
    } else if op == 2u8 {
        return a.ceil().to_bits() as u64;
    } else if op == 3u8 {
        return a.trunc().to_bits() as u64;
    } else if op == 4u8 {
        return a.round().to_bits() as u64;
    } else if op == 5u8 {
        return a.round_ties_even().to_bits() as u64;
    } else if op == 6u8 {
        return a.fract().to_bits() as u64;
    } else if op == 7u8 {
        return ord_code(a.total_cmp(b));
    } else if op == 8u8 {
        return a.min(b).to_bits() as u64;
    } else if op == 9u8 {
        return a.max(b).to_bits() as u64;
    } else if op == 10u8 {
        return a.next_up().to_bits() as u64;
    }
    a.next_down().to_bits() as u64
}

pub fn main() -> i32 {
    let mut failures: i32 = 0;
    let mut i: usize = 0;
    while i < N {
        let mut got: u64 = 0u64;
        if WIDE[i] == 0u8 {
            got = run64(OP[i], f64.from_bits(A[i]), f64.from_bits(B[i]), f64.from_bits(C[i]));
        } else {
            got = run32(OP[i], f32.from_bits(A[i] as u32), f32.from_bits(B[i] as u32), f32.from_bits(C[i] as u32));
        }
        if got != WANT[i] {
            failures = failures + fail(i, OP[i], got);
        }
        i = i + 1;
    }
    if failures == 0 {
        print("ok float_fmt qa_adv_ops\\n");
    }
    failures
}
""")
    text = "".join(out)
    if "--check" in sys.argv:
        with open(OUT, "rb") as fh:
            cur = fh.read().decode("utf-8")
        if cur != text:
            print("STALE qa_adv_ops.ax")
            return 1
        print("qa_adv_ops.ax up to date")
        return 0
    with open(OUT, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("wrote %s: %d records" % (OUT, len(recs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
