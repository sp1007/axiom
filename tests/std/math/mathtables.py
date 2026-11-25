#!/usr/bin/env python3
"""Constant tables of std.math (T461), computed with mpmath at 400 bits.

Everything here is a mathematical constant (no tuned or copied coefficient): double-double splits of pi, ln 2, ...,
the Taylor coefficients of exp / sin / cos / atan / atanh, the reduced-argument tables of log and atan, and the bits
of 2/pi for the Payne-Hanek reduction. `gen_tables.py` writes them to std/math/tables.ax; `mathproto.py`
(the algorithm prototype used for validation) imports them.
"""

import struct

import mpmath
from mpmath import mp, mpf

mp.prec = 400


def f64_bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def bits_f64(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def split_dd(v):
    """Round an mpf to a (hi, lo) pair of doubles, hi = round(v), lo = round(v - hi)."""
    hi = float(v)
    lo = float(v - mpf(hi))
    return hi, lo


def split_triple(v):
    hi = float(v)
    r = v - mpf(hi)
    mid = float(r)
    lo = float(r - mpf(mid))
    return hi, mid, lo


def round_bits(v, nbits):
    """Round v to nbits significant bits (round to nearest) and return it as a float."""
    if v == 0:
        return 0.0
    m, e = mpmath.frexp(v)  # v = m * 2^e, 0.5 <= |m| < 1
    scaled = mpmath.nint(m * (mpf(2) ** nbits))
    return float(scaled * (mpf(2) ** (e - nbits)))


# ---- constants ---------------------------------------------------------------------------------

PI = mp.pi
CONSTS = {
    "PI": PI,
    "TAU": 2 * PI,
    "FRAC_PI_2": PI / 2,
    "FRAC_PI_3": PI / 3,
    "FRAC_PI_4": PI / 4,
    "FRAC_PI_6": PI / 6,
    "FRAC_PI_8": PI / 8,
    "FRAC_1_PI": 1 / PI,
    "FRAC_2_PI": 2 / PI,
    "FRAC_2_SQRT_PI": 2 / mpmath.sqrt(PI),
    "E": mpmath.e,
    "LOG2_E": 1 / mpmath.log(2),
    "LOG10_E": 1 / mpmath.log(10),
    "LN_2": mpmath.log(2),
    "LN_10": mpmath.log(10),
    "SQRT_2": mpmath.sqrt(2),
    "FRAC_1_SQRT_2": 1 / mpmath.sqrt(2),
}


def f32_bits_of(v):
    f = struct.unpack("<f", struct.pack("<f", float(v)))[0]
    # float(v) is a double rounding in general; recompute from the exact value
    m, e = mpmath.frexp(v)
    scaled = mpmath.nint(m * (mpf(2) ** 24))
    f = float(scaled * (mpf(2) ** (e - 24)))
    return struct.unpack("<I", struct.pack("<f", f))[0]


# ---- double-double constants -------------------------------------------------------------------

def dd_consts():
    out = {}
    out["PI"] = split_dd(PI)
    out["PIO2"] = split_dd(PI / 2)
    out["PIO4"] = split_dd(PI / 4)
    out["LN2"] = split_dd(mpmath.log(2))
    out["LOG2E"] = split_dd(1 / mpmath.log(2))
    out["LOG10E"] = split_dd(1 / mpmath.log(10))
    out["LN10"] = split_dd(mpmath.log(10))
    out["TWO_OVER_SQRT_PI"] = split_dd(2 / mpmath.sqrt(PI))
    out["ONE_OVER_SQRT_PI"] = split_dd(1 / mpmath.sqrt(PI))
    out["ONE_THIRD"] = split_dd(mpf(1) / 3)
    return out


def ln2_parts():
    """ln 2 = HI + MID + LO with HI of 40 significant bits so that k * HI is exact for |k| < 2^13."""
    ln2 = mpmath.log(2)
    hi = round_bits(ln2, 40)
    r = ln2 - mpf(hi)
    mid = float(r)
    lo = float(r - mpf(mid))
    return hi, mid, lo


def pio2_parts():
    """pi/2 = HI + MID + LO (full doubles)."""
    return split_triple(PI / 2)


# ---- Taylor coefficient tables (double-double) ------------------------------------------------

def sin_coefs(n):
    """(-1)^k / (2k+1)!, k = 0..n-1."""
    return [split_dd(mpf((-1) ** k) / mpmath.factorial(2 * k + 1)) for k in range(n)]


def cos_coefs(n):
    """(-1)^k / (2k)!, k = 0..n-1."""
    return [split_dd(mpf((-1) ** k) / mpmath.factorial(2 * k)) for k in range(n)]


def expm1_coefs(n):
    """1/(k+1)!, k = 0..n-1 : expm1(w) = w * sum c_k w^k."""
    return [split_dd(mpf(1) / mpmath.factorial(k + 1)) for k in range(n)]


def atan_coefs(n):
    """(-1)^k / (2k+1), k = 0..n-1."""
    return [split_dd(mpf((-1) ** k) / (2 * k + 1)) for k in range(n)]


def atanh_coefs(n):
    """1 / (2k+1), k = 0..n-1 (log((1+s)/(1-s)) = 2 s sum c_k s^(2k))."""
    return [split_dd(mpf(1) / (2 * k + 1)) for k in range(n)]


def atan_table():
    """atan(i/16) as (hi, lo), i = 0..16."""
    return [split_dd(mpmath.atan(mpf(i) / 16)) for i in range(17)]


# ---- log reduction table ----------------------------------------------------------------------

LOG_OFF = 0x3FE6000000000000
LOG_N = 128


def log_table():
    """Per index i of the reduction (tmp = bits(x) - OFF; i = (tmp >> 45) & 127): invc, logc = -log(invc) as (hi, lo).

    The interval of m for index i is [m_lo, m_hi) from the bit pattern layout; c is its midpoint.
    """
    rows = []
    for i in range(LOG_N):
        lo_bits = LOG_OFF + (i << 45)
        hi_bits = LOG_OFF + ((i + 1) << 45)
        m_lo = bits_f64(lo_bits)
        m_hi = bits_f64(hi_bits)
        c = (mpf(m_lo) + mpf(m_hi)) / 2
        invc = float(1 / c)
        logc = -mpmath.log(mpf(invc))
        h, l = split_dd(logc)
        rows.append((invc, h, l))
    return rows


# ---- bits of 2/pi -----------------------------------------------------------------------------

TWO_OVER_PI_WORDS = 21


def two_over_pi_words():
    """Binary expansion of 2/pi = 0.b1 b2 b3 ... as u64 words: word i holds bits 64i+1 .. 64i+64."""
    old = mp.prec
    mp.prec = 64 * TWO_OVER_PI_WORDS + 200
    v = 2 / mpmath.pi
    scaled = int(mpmath.floor(v * (mpf(2) ** (64 * TWO_OVER_PI_WORDS))))
    mp.prec = old
    words = []
    for i in range(TWO_OVER_PI_WORDS):
        shift = 64 * (TWO_OVER_PI_WORDS - 1 - i)
        words.append((scaled >> shift) & 0xFFFFFFFFFFFFFFFF)
    return words


if __name__ == "__main__":
    print(ln2_parts())
    print(pio2_parts())
    print(two_over_pi_words()[:3])
