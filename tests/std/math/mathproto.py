#!/usr/bin/env python3
"""Algorithm prototype of std.math (T461), written with plain IEEE double operations only.

Python floats are IEEE binary64, so every function here returns the same bits as the Axiom code in std/math, which is
a line-by-line port. The prototype is used to validate accuracy (see validate.py) against mpmath before porting and
as a differential reference afterwards (diff.py). It is not part of the library.
"""

import math
import struct

import mathtables as T

MASK64 = 0xFFFFFFFFFFFFFFFF


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def frombits(b):
    return struct.unpack("<d", struct.pack("<Q", b & MASK64))[0]


INF = math.inf
NAN = math.nan


# ------------------------------------------------------------------------------------------------
# double-double arithmetic
# ------------------------------------------------------------------------------------------------

def two_sum(a, b):
    s = a + b
    bb = s - a
    e = (a - (s - bb)) + (b - bb)
    return s, e


def fast_two_sum(a, b):
    s = a + b
    e = b - (s - a)
    return s, e


def split(a):
    c = 134217729.0 * a
    hi = c - (c - a)
    lo = a - hi
    return hi, lo


def two_prod(a, b):
    p = a * b
    ah, al = split(a)
    bh, bl = split(b)
    e = ((ah * bh - p) + ah * bl + al * bh) + al * bl
    return p, e


def dd_add(x, y):
    s, e = two_sum(x[0], y[0])
    t, f = two_sum(x[1], y[1])
    e = e + t
    s, e = fast_two_sum(s, e)
    e = e + f
    return fast_two_sum(s, e)


def dd_add_d(x, d):
    s, e = two_sum(x[0], d)
    e = e + x[1]
    return fast_two_sum(s, e)


def dd_neg(x):
    return (-x[0], -x[1])


def dd_mul(x, y):
    p, e = two_prod(x[0], y[0])
    e = e + (x[0] * y[1] + x[1] * y[0])
    return fast_two_sum(p, e)


def dd_mul_d(x, d):
    p, e = two_prod(x[0], d)
    e = e + x[1] * d
    return fast_two_sum(p, e)


def dd_sqr(x):
    p, e = two_prod(x[0], x[0])
    e = e + 2.0 * x[0] * x[1]
    return fast_two_sum(p, e)


def dd_div(x, y):
    q1 = x[0] / y[0]
    r = dd_add(x, dd_neg(dd_mul_d(y, q1)))
    q2 = r[0] / y[0]
    r = dd_add(r, dd_neg(dd_mul_d(y, q2)))
    q3 = r[0] / y[0]
    q = fast_two_sum(q1, q2)
    return dd_add_d(q, q3)


def dd_div_d(x, d):
    q1 = x[0] / d
    p, pe = two_prod(q1, d)
    r = dd_add(x, (-p, -pe))
    q2 = r[0] / d
    p, pe = two_prod(q2, d)
    r = dd_add(r, (-p, -pe))
    q3 = r[0] / d
    q = fast_two_sum(q1, q2)
    return dd_add_d(q, q3)


def dd_sqrt(x):
    if x[0] == 0.0:
        return (0.0, 0.0)
    s = math.sqrt(x[0])
    ph, pl = two_prod(s, s)
    d = ((x[0] - ph) - pl) + x[1]
    lo = d / (2.0 * s)
    return fast_two_sum(s, lo)


def dd_scale(x, p2):
    return (x[0] * p2, x[1] * p2)


# ------------------------------------------------------------------------------------------------
# bit helpers
# ------------------------------------------------------------------------------------------------

def is_nan(x):
    return x != x


def pow2(n):
    """2^n for -1022 <= n <= 1023."""
    return frombits((n + 1023) << 52)


def scale2(x, n):
    """x * 2^n with a single rounding (musl scale2)."""
    if n > 1023:
        x = x * 8.98846567431158e307
        n = n - 1023
        if n > 1023:
            x = x * 8.98846567431158e307
            n = n - 1023
            if n > 1023:
                n = 1023
    elif n < -1022:
        # 2^-1022 * 2^53 = 2^-969
        x = x * (2.2250738585072014e-308 * 9007199254740992.0)
        n = n + 1022 - 53
        if n < -1022:
            x = x * (2.2250738585072014e-308 * 9007199254740992.0)
            n = n + 1022 - 53
            if n < -1022:
                n = -1022
    return x * pow2(n)


def scale_dd(x, n):
    a = abs(x[0])
    if a == 0.0:
        return x[0]
    top = exponent_of(a) + n
    if top >= -1022:
        return scale2(x[0], n)
    neg = x[0] < 0.0
    if top < -1075:
        return -0.0 if neg else 0.0
    sh = n + 1074
    lo = -x[1] if neg else x[1]
    qh = scale2(a, sh)
    ql = scale2(lo, sh)
    t0 = float(math.floor(qh))
    fr = qh - t0
    t = int(t0)
    up = False
    if fr > 0.5:
        up = True
    elif fr == 0.5:
        if ql > 0.0:
            up = True
        elif ql == 0.0:
            up = (t & 1) != 0
    if up:
        t = t + 1
    if neg:
        return frombits(t | 0x8000000000000000)
    return frombits(t)


# ------------------------------------------------------------------------------------------------
# tables
# ------------------------------------------------------------------------------------------------

LN2_HI, LN2_MID, LN2_LO = T.ln2_parts()
PIO2_HI, PIO2_MID, PIO2_LO = T.pio2_parts()
DDC = T.dd_consts()
LN2_DD = DDC["LN2"]
LOG2E_DD = DDC["LOG2E"]
LOG10E_DD = DDC["LOG10E"]
PI_DD = DDC["PI"]
PIO2_DD = DDC["PIO2"]
ONE_THIRD_DD = DDC["ONE_THIRD"]

SIN_N = 14
COS_N = 15
SINC = T.sin_coefs(SIN_N)
COSC = T.cos_coefs(COS_N)
EXPM1_N = 11
EXPM1C = T.expm1_coefs(EXPM1_N)
ATANC = T.atan_coefs(8)
ATANHC = T.atanh_coefs(8)
ATANT = T.atan_table()
LOGT = T.log_table()
P2PI = T.two_over_pi_words()


# ------------------------------------------------------------------------------------------------
# exp family
# ------------------------------------------------------------------------------------------------

def expm1_core(z):
    """exp(z) - 1 as a double-double for |z| <= 0.35 (relative accuracy about 2^-95)."""
    w = dd_scale(z, 0.0625)
    # p = w * sum_{k} c_k w^k, Horner in dd
    acc = EXPM1C[EXPM1_N - 1]
    k = EXPM1_N - 2
    while k >= 0:
        acc = dd_add(dd_mul(acc, w), EXPM1C[k])
        k = k - 1
    p = dd_mul(acc, w)
    # four doublings: e^(2w) - 1 = p * (p + 2)
    i = 0
    while i < 4:
        p = dd_mul(p, dd_add_d(p, 2.0))
        i = i + 1
    return p


def reduce_exp(x):
    """x = k ln2 + z; returns (k, z) with z a double-double, |z| <= ~0.347."""
    kf = math.floor(x * 1.4426950408889634 + 0.5)
    a, ae = two_sum(x, -kf * LN2_HI)
    t1h, t1l = two_prod(kf, LN2_MID)
    z = dd_add((a, ae), (-t1h, -t1l))
    t2 = kf * LN2_LO
    z = dd_add_d(z, -t2)
    return int(kf), z


def exp_finish(k, p):
    """2^k * (1 + p), rounded once to double (p a double-double)."""
    s, e = two_sum(1.0, p[0])
    e = e + p[1]
    return scale_dd(fast_two_sum(s, e), k)


def exp_(x):
    if is_nan(x):
        return x
    if x > 709.782712893384:
        return INF
    if x < -745.1332191019412:
        return 0.0
    k, z = reduce_exp(x)
    p = expm1_core(z)
    return exp_finish(k, p)


def exp2_(x):
    if is_nan(x):
        return x
    if x >= 1024.0:
        return INF
    if x < -1080.0:
        return 0.0
    kf = math.floor(x + 0.5)
    f = x - kf
    z = dd_mul_d(LN2_DD, f)
    p = expm1_core(z)
    return exp_finish(int(kf), p)


def exp2_dd_(t):
    """2^t for a double-double t (|t| below ~1100); returns a double."""
    kf = math.floor(t[0] + 0.5)
    fh = t[0] - kf
    f = two_sum(fh, t[1])
    z = dd_mul(f, LN2_DD)
    p = expm1_core(z)
    return exp_finish(int(kf), p)


def exp_parts(x):
    """e^x = 2^k * (1 + p): returns (k, p) with p a double-double (|x| <= 745)."""
    k, z = reduce_exp(x)
    return k, expm1_core(z)


def expm1_dd(x):
    """e^x - 1 as a double-double for -40 <= x <= 45."""
    k, p = exp_parts(x)
    if k == 0:
        return p
    onep = dd_add_d(p, 1.0)
    big = dd_scale(onep, pow2(k))
    return dd_add_d(big, -1.0)


def expm1_(x):
    if is_nan(x):
        return x
    if x == 0.0:
        return x
    if abs(x) < 5.551115123125783e-17:
        return x
    if x > 709.782712893384:
        return INF
    if x < -40.0:
        return -1.0
    if x > 45.0:
        k, p = exp_parts(x)
        return exp_finish(k, p)
    return expm1_dd(x)[0]


# ------------------------------------------------------------------------------------------------
# log family
# ------------------------------------------------------------------------------------------------

def log1p_small(f):
    """log(1 + f) as a double-double for a double-double f with |f| <= 0.07 (relative accuracy about 2^-90)."""
    den = dd_add_d(f, 2.0)
    s = dd_div(f, den)
    t = dd_sqr(s)
    # inner = sum_k c_k t^k, c_k = 1/(2k+1)
    acc = ATANHC[7]
    k = 6
    while k >= 0:
        acc = dd_add(dd_mul(acc, t), ATANHC[k])
        k = k - 1
    r = dd_mul(acc, s)
    return (2.0 * r[0], 2.0 * r[1])


def log_dd(x):
    """log(x) for finite x > 0 as a double-double."""
    k0 = 0
    if bits(x) < 0x0010000000000000:
        x = x * 18014398509481984.0  # 2^54
        k0 = -54
    ix = bits(x)
    if 0x3FEE000000000000 <= ix < 0x3FF1000000000000:
        f = x - 1.0
        return log1p_small((f, 0.0))
    tmp = (ix - T.LOG_OFF) & MASK64
    ktop = tmp >> 52
    if ktop >= 2048:
        k = ktop - 4096
    else:
        k = ktop
    i = (tmp >> 45) & 127
    iz = (ix - (k << 52)) & MASK64
    z = frombits(iz)
    invc, lh, ll = LOGT[i]
    ph, pl = two_prod(z, invc)
    r = two_sum(ph - 1.0, pl)
    kk = k + k0
    kf = float(kk)
    hi = dd_add_d((kf * LN2_HI, 0.0), 0.0)
    kl = dd_add(two_prod(kf, LN2_MID), (kf * LN2_LO, 0.0))
    base = dd_add((kf * LN2_HI, 0.0), kl)
    base = dd_add(base, (lh, ll))
    return dd_add(base, log1p_small(r))


def ln_(x):
    if is_nan(x):
        return x
    if x < 0.0:
        return NAN
    if x == 0.0:
        return -INF
    if x == INF:
        return x
    return log_dd(x)[0]


def log2_(x):
    if is_nan(x):
        return x
    if x < 0.0:
        return NAN
    if x == 0.0:
        return -INF
    if x == INF:
        return x
    return dd_mul(log_dd(x), LOG2E_DD)[0]


def log10_(x):
    if is_nan(x):
        return x
    if x < 0.0:
        return NAN
    if x == 0.0:
        return -INF
    if x == INF:
        return x
    return dd_mul(log_dd(x), LOG10E_DD)[0]


def ln_1p_(x):
    if is_nan(x):
        return x
    if x < -1.0:
        return NAN
    if x == -1.0:
        return -INF
    if x == INF:
        return x
    if x == 0.0:
        return x
    if abs(x) < 1.0 / 134217728.0 / 134217728.0:
        return x
    if abs(x) < 0.0625:
        return log1p_small((x, 0.0))[0]
    s, e = two_sum(1.0, x)
    # log(s + e) = log(s) + log1p(e / s)
    r = log_dd(s)
    return dd_add_d(r, e / s)[0]


# ------------------------------------------------------------------------------------------------
# trigonometry
# ------------------------------------------------------------------------------------------------

def p2pi_window(j0):
    """The 192 bits of 2/pi starting at bit j0 (1-based) as three u64 words (most significant first)."""
    o = j0 - 1
    q = o >> 6
    r = o & 63
    out = []
    for kk in range(3):
        a = P2PI[q + kk]
        b = P2PI[q + kk + 1]
        if r == 0:
            w = a
        else:
            w = ((a << r) & MASK64) | (b >> (64 - r))
        out.append(w)
    return out


def reduce_pio2(x):
    """x = n * pi/2 + y, |y| <= pi/4: returns (n mod 4, y as a double-double). x finite, |x| >= pi/4."""
    b = bits(x)
    neg = (b >> 63) != 0
    field = (b >> 52) & 0x7FF
    m = (b & 0x000FFFFFFFFFFFFF) | 0x0010000000000000
    e = field - 1075
    j0 = e - 1 if e >= 2 else 1
    w0, w1, w2 = p2pi_window(j0)
    s = j0 + 191 - e  # fractional bits of the product
    # 256-bit product m * (w0 w1 w2)
    p = (m * ((w0 << 128) | (w1 << 64) | w2))
    n = (p >> s) & 3
    frac = p & ((1 << s) - 1)
    if (frac >> (s - 1)) & 1:
        n = (n + 1) & 3
        frac = (1 << s) - frac
        negf = True
    else:
        negf = False
    if frac == 0:
        yd = (0.0, 0.0)
    else:
        nb = frac.bit_length()
        # value = frac * 2^-s ; take the top 64 bits and the next 64
        sh = nb - 64
        if sh >= 0:
            a = frac >> sh
            rest = frac & ((1 << sh) - 1)
        else:
            a = frac << (-sh)
            rest = 0
        sh2 = sh - 64
        if sh2 >= 0:
            bb = rest >> sh2
        else:
            bb = (rest << (-sh2)) & MASK64
        # a has its top bit set: value = (a * 2^64 + bb) * 2^(sh + 0 - 64 - s)
        hi_i = a >> 11
        rest75 = ((a & 0x7FF) << 64) | bb
        scale_exp = sh - s  # value = a * 2^scale_exp (+ bb * 2^(scale_exp - 64))
        hi = float(hi_i) * math.ldexp(1.0, scale_exp + 11)
        lo = (float(a & 0x7FF) * 18446744073709551616.0 + float(bb)) * math.ldexp(1.0, scale_exp - 64)
        yd = fast_two_sum(hi, lo)
        if negf:
            yd = (-yd[0], -yd[1])
    y = dd_mul(yd, PIO2_DD)
    if neg:
        n = (4 - n) & 3
        y = (-y[0], -y[1])
    return n, y


def sin_k(y):
    z = dd_sqr(y)
    acc = SINC[SIN_N - 1]
    k = SIN_N - 2
    while k >= 0:
        acc = dd_add(dd_mul(acc, z), SINC[k])
        k = k - 1
    return dd_mul(acc, y)


def cos_k(y):
    z = dd_sqr(y)
    acc = COSC[COS_N - 1]
    k = COS_N - 2
    while k >= 0:
        acc = dd_add(dd_mul(acc, z), COSC[k])
        k = k - 1
    return acc


def sincos_dd(x):
    """(sin, cos) of a finite double as double-doubles."""
    ax = abs(x)
    if ax <= 0.7853981633974483:
        y = (x, 0.0)
        return sin_k(y), cos_k(y)
    n, y = reduce_pio2(x)
    s = sin_k(y)
    c = cos_k(y)
    if n == 0:
        return s, c
    if n == 1:
        return c, dd_neg(s)
    if n == 2:
        return dd_neg(s), dd_neg(c)
    return dd_neg(c), s


def sin_(x):
    if is_nan(x) or math.isinf(x):
        return NAN
    if x == 0.0:
        return x
    return sincos_dd(x)[0][0]


def cos_(x):
    if is_nan(x) or math.isinf(x):
        return NAN
    return sincos_dd(x)[1][0]


def tan_(x):
    if is_nan(x) or math.isinf(x):
        return NAN
    if x == 0.0:
        return x
    s, c = sincos_dd(x)
    return dd_div(s, c)[0]


# ------------------------------------------------------------------------------------------------
# inverse trigonometry
# ------------------------------------------------------------------------------------------------

def atan_unit(q):
    """atan(q) for a double-double 0 <= q <= 1."""
    i = int(math.floor(q[0] * 16.0 + 0.5))
    if i == 0:
        z = q
    else:
        c = float(i) / 16.0
        num = dd_add_d(q, -c)
        den = dd_add_d(dd_mul_d(q, c), 1.0)
        z = dd_div(num, den)
    w = dd_sqr(z)
    acc = ATANC[7]
    k = 6
    while k >= 0:
        acc = dd_add(dd_mul(acc, w), ATANC[k])
        k = k - 1
    r = dd_mul(acc, z)
    if i == 0:
        return r
    return dd_add(ATANT[i], r)


def atan2_core(ay, ax):
    """Angle in [0, pi/2] of the point (ax, ay), both double-doubles >= 0 (not both zero), as a double-double,
    together with a flag telling whether the pair was swapped (angle is pi/2 - atan(ax/ay))."""
    swap = ay[0] > ax[0]
    if swap:
        q = dd_div(ax, ay)
    else:
        q = dd_div(ay, ax)
    a = atan_unit(q)
    if swap:
        return dd_add(PIO2_DD, dd_neg(a))
    return a


def atan_ratio_tiny(ay, ax, xneg, t):
    """Angle (as a double) when min/max = t < 2^-60, so atan(t) == t to double-double accuracy."""
    if ay >= ax:
        if xneg:
            return dd_add_d(PIO2_DD, t)[0]
        return dd_add_d(PIO2_DD, -t)[0]
    if xneg:
        return dd_add_d(PI_DD, -t)[0]
    return t


def exponent_of(x):
    """Unbiased exponent of a positive normal double."""
    return int((bits(x) >> 52) & 0x7FF) - 1023


def atan2_(y, x):
    if is_nan(x) or is_nan(y):
        return x + y
    ay = abs(y)
    ax = abs(x)
    xneg = (bits(x) >> 63) != 0
    if y == 0.0:
        if xneg:
            return math.copysign(PI_DD[0], y)
        return y
    if x == 0.0:
        return math.copysign(PIO2_DD[0], y)
    if ax == INF:
        if ay == INF:
            if xneg:
                return math.copysign(2.356194490192345, y)
            return math.copysign(0.7853981633974483, y)
        if xneg:
            return math.copysign(PI_DD[0], y)
        return math.copysign(0.0, y)
    if ay == INF:
        return math.copysign(PIO2_DD[0], y)
    hi = max(ay, ax)
    lo = min(ay, ax)
    if lo < hi * 8.673617379884035e-19:
        t = lo / hi
        return math.copysign(atan_ratio_tiny(ay, ax, xneg, t), y)
    if hi > 1.0e150 or lo < 1.0e-150:
        e = exponent_of(hi)
        ay = scale2(ay, -e)
        ax = scale2(ax, -e)
    th = atan2_core((ay, 0.0), (ax, 0.0))
    if xneg:
        th = dd_add(PI_DD, dd_neg(th))
    return math.copysign(th[0], y)


def atan_(x):
    if is_nan(x):
        return x
    return atan2_(x, 1.0)


def asin_(x):
    if is_nan(x):
        return x
    ax = abs(x)
    if ax > 1.0:
        return NAN
    if ax == 1.0:
        return math.copysign(PIO2_DD[0], x)
    if ax < 1.4901161193847656e-08:
        return x
    a = two_sum(1.0, -ax)
    b = two_sum(1.0, ax)
    root = dd_sqrt(dd_mul(a, b))
    th = atan2_core((ax, 0.0), root)
    return math.copysign(th[0], x)


def acos_(x):
    if is_nan(x):
        return x
    ax = abs(x)
    if ax > 1.0:
        return NAN
    if x == 1.0:
        return 0.0
    if x == -1.0:
        return PI_DD[0]
    if ax == 0.0:
        return PIO2_DD[0]
    a = two_sum(1.0, -ax)
    b = two_sum(1.0, ax)
    root = dd_sqrt(dd_mul(a, b))
    th = atan2_core(root, (ax, 0.0))
    if x < 0.0:
        th = dd_add(PI_DD, dd_neg(th))
    return th[0]


# ------------------------------------------------------------------------------------------------
# powers, roots, hypot
# ------------------------------------------------------------------------------------------------

def is_integer(y):
    """y finite."""
    if abs(y) >= 9007199254740992.0:
        return True
    return y == math.floor(y)


def is_odd_integer(y):
    if abs(y) >= 9007199254740992.0:
        return False
    if y != math.floor(y):
        return False
    return (int(y) & 1) != 0


def powf_(x, y):
    if y == 0.0:
        return 1.0
    if x == 1.0:
        return 1.0
    if is_nan(x) or is_nan(y):
        return x + y
    ax = abs(x)
    xneg = (bits(x) >> 63) != 0
    if ay_inf(y):
        if ax == 1.0:
            return 1.0
        if (ax < 1.0) == (y > 0.0):
            return 0.0
        return INF
    if x == 0.0:
        odd = is_odd_integer(y)
        if y < 0.0:
            return math.copysign(INF, x) if odd else INF
        return math.copysign(0.0, x) if odd else 0.0
    if ax == INF:
        odd = is_odd_integer(y)
        if x > 0.0:
            return INF if y > 0.0 else 0.0
        if y < 0.0:
            return -0.0 if odd else 0.0
        return -INF if odd else INF
    negate = False
    if xneg:
        if not is_integer(y):
            return NAN
        negate = is_odd_integer(y)
    if ax == 1.0:
        r = 1.0
    else:
        lg = dd_mul(log_dd(ax), LOG2E_DD)
        if abs(y) > 1.0e18:
            big_pos = (lg[0] > 0.0) == (y > 0.0)
            r = INF if big_pos else 0.0
        else:
            t = dd_mul_d(lg, y)
            if t[0] > 1024.0:
                r = INF
            elif t[0] < -1080.0:
                r = 0.0
            else:
                r = exp2_dd_(t)
    return -r if negate else r


def ay_inf(y):
    return y == INF or y == -INF


def renorm(m, e):
    d = exponent_of(m[0])
    return dd_scale(m, pow2(-d)), e + d


def powi_(x, n):
    if n == 0:
        return 1.0
    if is_nan(x):
        return x
    odd = (n & 1) != 0
    xneg = (bits(x) >> 63) != 0
    neg_result = xneg and odd
    ax = abs(x)
    if ax == 0.0:
        if n < 0:
            r = INF
        else:
            r = 0.0
        return -r if neg_result else r
    if ax == INF:
        r = 0.0 if n < 0 else INF
        return -r if neg_result else r
    e = 0
    if ax < 2.2250738585072014e-308:
        ax = ax * 18014398509481984.0
        e = -54
    d0 = exponent_of(ax)
    m, e = (scale2(ax, -d0), 0.0), e + d0
    cnt = -n if n < 0 else n
    rm = (1.0, 0.0)
    re = 0
    bm = m
    be = e
    while cnt > 0:
        if (cnt & 1) != 0:
            rm = dd_mul(rm, bm)
            re = re + be
            rm, re = renorm(rm, re)
        cnt = cnt >> 1
        if cnt > 0:
            bm = dd_sqr(bm)
            be = be * 2
            bm, be = renorm(bm, be)
    if n < 0:
        rm = dd_div((1.0, 0.0), rm)
        re = -re
    if re > 4000:
        re = 4000
    if re < -4000:
        re = -4000
    r = scale_dd(rm, re)
    return -r if neg_result else r


def cbrt_(x):
    if is_nan(x) or x == 0.0 or abs(x) == INF:
        return x + x if is_nan(x) else x
    a = abs(x)
    e = 0
    if a < 2.2250738585072014e-308:
        a = a * 18014398509481984.0
        e = -54
    ex = exponent_of(a) + 0
    q = ex // 3
    a_s = scale2(a, -3 * q)  # in [1, 8)
    y = frombits(bits(a_s) // 3 + 0x2AA0000000000000)
    i = 0
    while i < 4:
        y = y - (y * y * y - a_s) / (3.0 * y * y)
        i = i + 1
    y2 = two_prod(y, y)
    y3 = dd_mul_d(y2, y)
    r = dd_add_d(dd_neg(y3), a_s)
    delta = r[0] / (3.0 * y2[0])
    yy = two_sum(y, delta)
    res = scale2(yy[0], q + e // 3)
    return math.copysign(res, x)


def hypot_(x, y):
    ax = abs(x)
    ay = abs(y)
    if ax == INF or ay == INF:
        return INF
    if is_nan(x) or is_nan(y):
        return x + y
    hi = max(ax, ay)
    lo = min(ax, ay)
    if lo == 0.0:
        return hi
    if hi > lo * 18014398509481984.0:
        return hi
    e = 0
    if hi < 2.2250738585072014e-308:
        hi = hi * 18014398509481984.0
        lo = lo * 18014398509481984.0
        e = -54
    d = exponent_of(hi)
    hs = scale2(hi, -d)
    ls = scale2(lo, -d)
    s = dd_add(dd_sqr((hs, 0.0)), dd_sqr((ls, 0.0)))
    r = dd_sqrt(s)
    return scale_dd(r, d + e)


# ------------------------------------------------------------------------------------------------
# hyperbolic functions
# ------------------------------------------------------------------------------------------------

MAX_SINH = 710.4758600739439


def sinh_(x):
    if is_nan(x) or x == 0.0:
        return x
    ax = abs(x)
    if ax == INF:
        return x
    if ax < 3.725290298461914e-09:
        return x
    if ax > MAX_SINH:
        return math.copysign(INF, x)
    if ax >= 40.0:
        k, p = exp_parts(ax)
        r = scale2(dd_add_d(p, 1.0)[0] + 0.0, k - 1)
        # exact: 0.5 * 2^k * (1 + p)
        onep = dd_add_d(p, 1.0)
        r = scale2(onep[0] + onep[1], k - 1)
        return math.copysign(r, x)
    q = expm1_dd(ax)
    e = dd_add_d(q, 1.0)
    t = dd_div(q, e)
    s = dd_add(q, t)
    return math.copysign(0.5 * s[0], x)


def cosh_(x):
    if is_nan(x):
        return x
    ax = abs(x)
    if ax == INF:
        return INF
    if ax > MAX_SINH:
        return INF
    if ax >= 40.0:
        k, p = exp_parts(ax)
        onep = dd_add_d(p, 1.0)
        return scale2(onep[0] + onep[1], k - 1)
    q = expm1_dd(ax)
    e = dd_add_d(q, 1.0)
    inv = dd_div((1.0, 0.0), e)
    s = dd_add(e, inv)
    return 0.5 * s[0]


def tanh_(x):
    if is_nan(x) or x == 0.0:
        return x
    ax = abs(x)
    if ax >= 22.0:
        return math.copysign(1.0, x)
    if ax < 3.725290298461914e-09:
        return x
    q = expm1_dd(2.0 * ax)
    t = dd_div(q, dd_add_d(q, 2.0))
    return math.copysign(t[0], x)


def log1p_dd(s):
    """log(1 + s) for a double-double s > -1."""
    if abs(s[0]) < 0.0625:
        return log1p_small(s)
    u = dd_add_d(s, 1.0)
    r = log_dd(u[0])
    return dd_add_d(r, u[1] / u[0])


def asinh_(x):
    if is_nan(x) or x == 0.0:
        return x
    ax = abs(x)
    if ax == INF:
        return x
    if ax < 3.725290298461914e-09:
        return x
    if ax >= 268435456.0:
        r = dd_add(log_dd(ax), LN2_DD)
        return math.copysign(r[0], x)
    x2 = dd_sqr((ax, 0.0))
    root = dd_sqrt(dd_add_d(x2, 1.0))
    u = dd_div(x2, dd_add_d(root, 1.0))
    s = dd_add_d(u, ax)
    r = log1p_dd(s)
    return math.copysign(r[0], x)


def acosh_(x):
    if is_nan(x):
        return x
    if x < 1.0:
        return NAN
    if x == 1.0:
        return 0.0
    if x == INF:
        return x
    if x >= 268435456.0:
        return dd_add(log_dd(x), LN2_DD)[0]
    a = two_sum(x, -1.0)
    b = two_sum(x, 1.0)
    w = dd_sqrt(dd_mul(a, b))
    s = dd_add(a, w)
    return log1p_dd(s)[0]


def atanh_(x):
    if is_nan(x) or x == 0.0:
        return x
    ax = abs(x)
    if ax > 1.0:
        return NAN
    if ax == 1.0:
        return math.copysign(INF, x)
    if ax < 3.725290298461914e-09:
        return x
    d = two_sum(1.0, -ax)
    q = dd_div((2.0 * ax, 0.0), d)
    r = log1p_dd(q)
    return math.copysign(0.5 * r[0], x)


# ------------------------------------------------------------------------------------------------
# error functions
# ------------------------------------------------------------------------------------------------

TWO_OVER_SQRT_PI_DD = DDC["TWO_OVER_SQRT_PI"]
ONE_OVER_SQRT_PI_DD = DDC["ONE_OVER_SQRT_PI"]


def exp_parts_dd(t):
    """e^t = 2^k * (1 + p) for a double-double t (|t| <= 745): returns (k, p)."""
    kf = math.floor(t[0] * 1.4426950408889634 + 0.5)
    a, ae = two_sum(t[0], -kf * LN2_HI)
    z = dd_add_d((a, ae), t[1])
    t1h, t1l = two_prod(kf, LN2_MID)
    z = dd_add(z, (-t1h, -t1l))
    z = dd_add_d(z, -(kf * LN2_LO))
    return int(kf), expm1_core(z)


def erf_series(x):
    """erf(x) as a double-double for 0 < x < 3."""
    x2 = dd_sqr((x, 0.0))
    two_x2 = (2.0 * x2[0], 2.0 * x2[1])
    term = (x, 0.0)
    s = term
    n = 0
    while True:
        term = dd_div_d(dd_mul(term, two_x2), float(2 * n + 3))
        s = dd_add(s, term)
        n = n + 1
        if term[0] < s[0] * 1.0e-33:
            break
    k, p = exp_parts_dd((-x2[0], -x2[1]))
    onep = dd_add_d(p, 1.0)
    m = dd_mul(dd_mul(TWO_OVER_SQRT_PI_DD, onep), s)
    return dd_scale(m, pow2(k))


def erfc_cf_terms(x):
    if x < 3.5:
        return 90
    if x < 4.0:
        return 72
    if x < 5.0:
        return 60
    if x < 6.0:
        return 45
    if x < 10.0:
        return 36
    return 24


def erfc_cf(x):
    """erfc(x) = 2^k * m for x >= 3 as (k, m double-double)."""
    n = erfc_cf_terms(x)
    t = (0.0, 0.0)
    while n >= 1:
        t = dd_div((float(n) * 0.5, 0.0), dd_add_d(t, x))
        n = n - 1
    cfv = dd_div((1.0, 0.0), dd_add_d(t, x))
    x2 = dd_sqr((x, 0.0))
    k, p = exp_parts_dd((-x2[0], -x2[1]))
    onep = dd_add_d(p, 1.0)
    m = dd_mul(dd_mul(ONE_OVER_SQRT_PI_DD, onep), cfv)
    return k, m


def erf_dd(ax):
    """erf(ax) as a double-double for 0 < ax < 6."""
    if ax < 3.0:
        return erf_series(ax)
    k, m = erfc_cf(ax)
    return dd_add_d(dd_neg(dd_scale(m, pow2(k))), 1.0)


def erf_(x):
    if is_nan(x) or x == 0.0:
        return x
    ax = abs(x)
    if ax >= 6.0:
        return math.copysign(1.0, x)
    if ax < 1.0e-150:
        c = dd_mul_d(TWO_OVER_SQRT_PI_DD, ax * pow2(600) if ax < 1.0e-100 else ax)
        r = scale_dd(c, -600) if ax < 1.0e-100 else c[0]
        return math.copysign(r, x)
    return math.copysign(erf_dd(ax)[0], x)


def erfc_(x):
    if is_nan(x):
        return x
    if x == INF:
        return 0.0
    if x == -INF:
        return 2.0
    if x < -6.0:
        return 2.0
    if x == 0.0:
        return 1.0
    ax = abs(x)
    if x < 0.0:
        if ax < 1.0e-20:
            return 1.0
        return dd_add_d(erf_dd(ax), 1.0)[0]
    if x > 27.3:
        return 0.0
    if x < 3.0:
        if x < 1.0e-20:
            return 1.0
        return dd_add_d(dd_neg(erf_dd(x)), 1.0)[0]
    k, m = erfc_cf(x)
    if k < -1080:
        return 0.0
    return scale_dd(m, k)
