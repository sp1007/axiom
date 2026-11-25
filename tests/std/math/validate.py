#!/usr/bin/env python3
"""Accuracy check of the prototype (and, via --bits-file, of compiled Axiom output) against mpmath."""

import math
import random
import struct
import sys

import mpmath
from mpmath import mp, mpf

mp.prec = 300


def ulp_err(got, ref):
    """Error of `got` in ulps of the correctly rounded reference value (mpf)."""
    if isinstance(ref, mpmath.mpc) or mpmath.isnan(ref):
        return 0.0 if got != got else float("inf")
    if got != got:
        return float("inf")
    if mpmath.isinf(ref):
        return 0.0 if got == (math.inf if ref > 0 else -math.inf) else float("inf")
    ovf = mpf(2) ** 1024 * (1 - mpf(2) ** -54)
    if abs(ref) >= ovf:
        return 0.0 if got == math.copysign(math.inf, float(ref)) else float("inf")
    if math.isinf(got):
        return float("inf")
    r = float(ref)
    if r == 0.0 and ref != 0:
        r = 5e-324 if ref > 0 else -5e-324
    if math.isinf(r):
        r = math.copysign(1.7976931348623157e308, r)
    m, e = math.frexp(abs(r)) if r != 0 else (0.5, -1073)
    ulp = math.ldexp(1.0, max(e - 53, -1074))
    return float(abs(mpf(got) - ref) / ulp)


def rand_args(rng, lo, hi, n, kind="uniform"):
    out = []
    for _ in range(n):
        if kind == "uniform":
            out.append(rng.uniform(lo, hi))
        else:
            # log-uniform magnitude with random sign
            s = rng.choice([-1.0, 1.0]) if lo < 0 else 1.0
            out.append(s * math.exp(rng.uniform(math.log(abs(hi) if hi else 1) - 60, math.log(abs(hi) if hi else 1))))
    return out


def check(name, fn, ref, args, report=True):
    worst = 0.0
    wa = None
    for a in args:
        try:
            got = fn(*a) if isinstance(a, tuple) else fn(a)
            want = ref(*a) if isinstance(a, tuple) else ref(a)
        except (ValueError, ZeroDivisionError, OverflowError):
            continue
        e = ulp_err(got, want)
        if e > worst:
            worst, wa = e, a
    if report:
        print("%-10s n=%-6d worst %.4f ulp at %r" % (name, len(args), worst, wa))
    return worst, wa
