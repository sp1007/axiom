#!/usr/bin/env python3
"""Differential and accuracy probe of std.math (T461).

    python tests/std/math/probe.py --compiler build/axiomc2.exe [--mode native|interp] [--n 400] [--funcs sin,cos]

For every function a deterministic input set (random, adversarial and special values) is embedded in a generated Axiom
program, the program prints the result bits of std.math, and this script compares them

  * bit for bit with the prototype (mathproto.py, the algorithm std.math is a port of), and
  * in ulps with 300-bit mpmath references (validate.py), reporting the worst case.

Used during development and by the QA stress run; the committed tests (tests/std/math/*.ax) embed fixed vectors.
"""

import argparse
import math
import os
import random
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mpmath  # noqa: E402
from mpmath import mpf  # noqa: E402

import mathproto as P  # noqa: E402
from validate import ulp_err  # noqa: E402


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def frombits(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def gen_inputs(rng, kind, n):
    out = []
    if kind == "any":
        for _ in range(n):
            out.append(rng.choice([-1, 1]) * math.exp(rng.uniform(-60, 60)))
        out += [rng.uniform(-3, 3) for _ in range(n)]
    elif kind == "exp":
        out = [rng.uniform(-745, 710) for _ in range(n)] + [rng.uniform(-3, 3) for _ in range(n)] + [rng.uniform(-1e-3, 1e-3) for _ in range(n // 4)]
    elif kind == "expm1":
        out = [rng.uniform(-40, 710) for _ in range(n)] + [rng.uniform(-1, 1) for _ in range(n)] + [rng.uniform(-1e-3, 1e-3) for _ in range(n // 4)]
    elif kind == "exp2":
        out = [rng.uniform(-1080, 1024) for _ in range(n)] + [rng.uniform(-4, 4) for _ in range(n)]
    elif kind == "pos":
        out = [math.exp(rng.uniform(-745, 709)) for _ in range(n)] + [rng.uniform(0.5, 2) for _ in range(n)] + \
              [1 + rng.uniform(-0.1, 0.1) for _ in range(n)] + [1 + rng.uniform(-1e-5, 1e-5) for _ in range(n // 2)] + \
              [5e-324 * rng.randint(1, 1 << 40) for _ in range(n // 8)]
    elif kind == "log1p":
        out = [rng.uniform(-1, 10) for _ in range(n)] + [rng.uniform(-0.1, 0.1) for _ in range(n)] + \
              [rng.uniform(-1e-9, 1e-9) for _ in range(n // 4)] + [math.exp(rng.uniform(-3, 700)) for _ in range(n // 4)] + \
              [-1 + rng.uniform(1e-16, 0.1) for _ in range(n // 4)]
    elif kind == "trig":
        out = [rng.uniform(-1, 1) for _ in range(n)] + [rng.uniform(-100, 100) for _ in range(n)] + \
              [rng.uniform(-1e6, 1e6) for _ in range(n // 2)] + \
              [math.exp(rng.uniform(-700, 700)) * rng.choice([-1, 1]) for _ in range(n)] + \
              [k * math.pi / 2 for k in range(1, 40)] + [1e22, 5.0e22, 1e300, 1.7e308, 2.0 ** 60]
    elif kind == "unit":
        out = [rng.uniform(-1, 1) for _ in range(n)] + [rng.uniform(-1e-5, 1e-5) for _ in range(n // 4)] + \
              [1 - 2.0 ** -rng.randint(1, 53) for _ in range(n // 4)] + [-1 + 2.0 ** -rng.randint(1, 53) for _ in range(n // 4)]
    elif kind == "atan":
        out = [rng.uniform(-3, 3) for _ in range(n)] + [math.exp(rng.uniform(-700, 700)) * rng.choice([-1, 1]) for _ in range(n)] + \
              [rng.uniform(-1e-5, 1e-5) for _ in range(n // 4)]
    elif kind == "sinh":
        out = [rng.uniform(-3, 3) for _ in range(n)] + [rng.uniform(-50, 50) for _ in range(n)] + [rng.uniform(-711, 711) for _ in range(n // 2)] + \
              [rng.uniform(-1e-4, 1e-4) for _ in range(n // 4)]
    elif kind == "acosh":
        out = [1 + rng.uniform(0, 3) for _ in range(n)] + [math.exp(rng.uniform(0, 700)) for _ in range(n)] + [1 + rng.uniform(0, 1e-4) for _ in range(n // 4)]
    elif kind == "erf":
        out = [rng.uniform(-3, 3) for _ in range(n)] + [rng.uniform(-6.5, 6.5) for _ in range(n)] + [rng.uniform(-1e-3, 1e-3) for _ in range(n // 4)] + \
              [1e-200, 1e-310, 5e-324]
    elif kind == "erfc":
        out = [rng.uniform(-6.5, 6.5) for _ in range(n)] + [rng.uniform(-6, 28) for _ in range(n)] + [rng.uniform(2.5, 3.5) for _ in range(n // 2)] + \
              [rng.uniform(-1e-3, 1e-3) for _ in range(n // 4)]
    elif kind == "cbrt":
        out = [rng.uniform(-100, 100) for _ in range(n)] + [math.exp(rng.uniform(-745, 709)) * rng.choice([-1, 1]) for _ in range(n)] + \
              [5e-324 * k for k in range(1, 20)] + [1.7976931348623157e308, 8.0, 27.0, -27.0, 1000.0, 0.001]
    elif kind == "pair_pow":
        for _ in range(n):
            out.append((rng.uniform(0.01, 10), rng.uniform(-30, 30)))
        for _ in range(n):
            out.append((math.exp(rng.uniform(-700, 700)), rng.uniform(-3, 3)))
        for _ in range(n // 2):
            out.append((rng.uniform(-10, -0.1), float(rng.randint(-20, 20))))
        for _ in range(n // 2):
            out.append((1 + rng.uniform(-1e-6, 1e-6), rng.uniform(-1e9, 1e9)))
        for _ in range(n // 2):
            out.append((rng.uniform(0.5, 2), rng.uniform(-1500, 1500)))
        for _ in range(n // 2):
            out.append((float(rng.randint(1, 20)), float(rng.randint(-40, 60))))
    elif kind == "pair_hypot":
        for _ in range(n):
            out.append((rng.uniform(-10, 10), rng.uniform(-10, 10)))
        for _ in range(n):
            out.append((math.exp(rng.uniform(-745, 709)) * rng.choice([-1, 1]), math.exp(rng.uniform(-745, 709)) * rng.choice([-1, 1])))
        out += [(3.0, 4.0), (1e308, 1e308), (5e-324, 5e-324), (1e-320, 1e-320)]
    elif kind == "pair_atan2":
        for _ in range(n):
            out.append((rng.uniform(-3, 3), rng.uniform(-3, 3)))
        for _ in range(n):
            out.append((math.exp(rng.uniform(-700, 700)) * rng.choice([-1, 1]), math.exp(rng.uniform(-700, 700)) * rng.choice([-1, 1])))
        for _ in range(n // 2):
            e = rng.uniform(-30, 30)
            out.append((math.exp(e) * rng.choice([-1, 1]), rng.choice([-1, 1]) * rng.uniform(0.5, 2)))
    elif kind == "pair_powi":
        for _ in range(n):
            out.append((rng.uniform(-3, 3), rng.randint(-50, 50)))
        for _ in range(n // 2):
            out.append((math.exp(rng.uniform(-100, 100)) * rng.choice([-1, 1]), rng.randint(-8, 8)))
        for _ in range(n // 4):
            out.append((1 + rng.uniform(-1e-6, 1e-6), rng.randint(-2 ** 31, 2 ** 31 - 1)))
        for _ in range(n // 2):
            out.append((rng.uniform(0.5, 2), rng.randint(-1500, 1500)))
        out += [(2.0, 1023), (2.0, -1074), (2.0, -1075), (2.0, 1024), (10.0, 22), (10.0, -22), (0.1, 5000)]
    else:
        raise ValueError(kind)
    return out


def mp_sign_pow(x, y):
    return mpmath.power(mpf(x), mpf(y))


def mp_cbrt(x):
    return mpmath.cbrt(mpf(abs(x))) * (1 if x > 0 else -1)


# name -> (arity, kind, prototype function, mpmath reference)
FUNCS = {
    "exp": (1, "exp", P.exp_, lambda x: mpmath.exp(mpf(x))),
    "exp2": (1, "exp2", P.exp2_, lambda x: mpmath.power(2, mpf(x))),
    "expm1": (1, "expm1", P.expm1_, lambda x: mpmath.expm1(mpf(x))),
    "ln": (1, "pos", P.ln_, lambda x: mpmath.log(mpf(x))),
    "log2": (1, "pos", P.log2_, lambda x: mpmath.log(mpf(x), 2)),
    "log10": (1, "pos", P.log10_, lambda x: mpmath.log10(mpf(x))),
    "ln_1p": (1, "log1p", P.ln_1p_, lambda x: mpmath.log1p(mpf(x))),
    "sin": (1, "trig", P.sin_, lambda x: mpmath.sin(mpf(x))),
    "cos": (1, "trig", P.cos_, lambda x: mpmath.cos(mpf(x))),
    "tan": (1, "trig", P.tan_, lambda x: mpmath.tan(mpf(x))),
    "atan": (1, "atan", P.atan_, lambda x: mpmath.atan(mpf(x))),
    "asin": (1, "unit", P.asin_, lambda x: mpmath.asin(mpf(x))),
    "acos": (1, "unit", P.acos_, lambda x: mpmath.acos(mpf(x))),
    "sinh": (1, "sinh", P.sinh_, lambda x: mpmath.sinh(mpf(x))),
    "cosh": (1, "sinh", P.cosh_, lambda x: mpmath.cosh(mpf(x))),
    "tanh": (1, "sinh", P.tanh_, lambda x: mpmath.tanh(mpf(x))),
    "asinh": (1, "atan", P.asinh_, lambda x: mpmath.asinh(mpf(x))),
    "acosh": (1, "acosh", P.acosh_, lambda x: mpmath.acosh(mpf(x))),
    "atanh": (1, "unit", P.atanh_, lambda x: mpmath.atanh(mpf(x))),
    "erf": (1, "erf", P.erf_, lambda x: mpmath.erf(mpf(x))),
    "erfc": (1, "erfc", P.erfc_, lambda x: mpmath.erfc(mpf(x))),
    "cbrt": (1, "cbrt", P.cbrt_, mp_cbrt),
    "powf": (2, "pair_pow", P.powf_, mp_sign_pow),
    "hypot": (2, "pair_hypot", P.hypot_, lambda x, y: mpmath.sqrt(mpf(x) ** 2 + mpf(y) ** 2)),
    "atan2": (2, "pair_atan2", P.atan2_, lambda y, x: mpmath.atan2(mpf(y), mpf(x))),
    "powi": (2, "pair_powi", P.powi_, lambda x, n: mpmath.power(mpf(x), n)),
}


def build_program(selected, data):
    L = ["module probe", "", "use std.math", ""]
    for name in selected:
        arity = FUNCS[name][0]
        pts = data[name]
        if arity == 1:
            L.append("const IN_%s: [%d]u64 = [%s];" % (name, len(pts), ", ".join("0x%016Xu64" % bits(p) for p in pts)))
        else:
            L.append("const IN_%s: [%d]u64 = [%s];" % (name, len(pts), ", ".join("0x%016Xu64" % bits(p[0]) for p in pts)))
            if name == "powi":
                L.append("const IM_%s: [%d]i32 = [%s];" % (name, len(pts), ", ".join("%di32" % p[1] for p in pts)))
            else:
                L.append("const IM_%s: [%d]u64 = [%s];" % (name, len(pts), ", ".join("0x%016Xu64" % bits(p[1]) for p in pts)))
    L.append("")
    for name in selected:
        arity = FUNCS[name][0]
        n = len(data[name])
        L.append("fn run_%s() {" % name)
        L.append("    let mut i: usize = 0;")
        L.append("    while i < %d {" % n)
        L.append("        let x = f64.from_bits(IN_%s[i]);" % name)
        if arity == 1:
            L.append("        let r = std.math.%s(x);" % name)
        elif name == "powi":
            L.append("        let r = std.math.powi(x, IM_%s[i]);" % name)
        else:
            L.append("        let y = f64.from_bits(IM_%s[i]);" % name)
            L.append("        let r = std.math.%s(x, y);" % name)
        L.append("        print_int(r.to_bits() as i64);")
        L.append('        print("\\n");')
        L.append("        i = i + 1;")
        L.append("    }")
        L.append("}")
        L.append("")
    L.append("fn main() -> i32 {")
    for name in selected:
        L.append("    run_%s();" % name)
    L.append("    0")
    L.append("}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", required=True)
    ap.add_argument("--mode", default="native", choices=["native", "interp"])
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--funcs", default="")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--std-root", default="")
    ap.add_argument("--raw", action="store_true", help="inputs are random bit patterns (subnormals, huge, inf, nan)")
    ap.add_argument("--ulp-limit", type=float, default=0.6)
    args = ap.parse_args()
    selected = [f for f in args.funcs.split(",") if f] or list(FUNCS)
    rng = random.Random(args.seed)
    if args.raw:
        def rawf():
            r = rng.random()
            if r < 0.1:
                return frombits(rng.getrandbits(52))
            if r < 0.2:
                return -frombits(rng.getrandbits(52))
            v = frombits(rng.getrandbits(64))
            return v
        data = {}
        for name in selected:
            ar = FUNCS[name][0]
            if name == "powi":
                data[name] = [(rawf(), rng.randint(-2 ** 31, 2 ** 31 - 1)) for _ in range(args.n * 4)]
            elif ar == 2:
                data[name] = [(rawf(), rawf()) for _ in range(args.n * 4)]
            else:
                data[name] = [rawf() for _ in range(args.n * 4)]
    else:
        data = {name: gen_inputs(rng, FUNCS[name][1], args.n) for name in selected}
    prog = build_program(selected, data)
    d = tempfile.mkdtemp(prefix="probe_")
    path = os.path.join(d, "probe.ax")
    with open(path, "w") as f:
        f.write(prog)
    std = ["--std-root", args.std_root] if args.std_root else []
    if args.mode == "interp":
        cmd = [args.compiler, "run", "--interp", "--step-limit", "4000000000"] + std + [path]
        r = subprocess.run(cmd, capture_output=True, text=True)
    else:
        exe = os.path.join(d, "probe.exe")
        b = subprocess.run([args.compiler, "build"] + std + ["-o", exe, path], capture_output=True, text=True)
        if b.returncode != 0:
            print(b.stdout[-2000:])
            print(b.stderr[-4000:])
            print("build failed", b.returncode, path)
            return 1
        r = subprocess.run([exe], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-4000:])
        print("run failed", r.returncode, path)
        return 1
    lines = r.stdout.split("\n")
    pos = 0
    bad = 0
    for name in selected:
        arity, kind, proto, ref = FUNCS[name]
        pts = data[name]
        mism = 0
        worst = 0.0
        wa = None
        first = None
        for p in pts:
            got = frombits(int(lines[pos]) & 0xFFFFFFFFFFFFFFFF)
            pos += 1
            try:
                want = proto(*p) if arity == 2 else proto(p)
            except (ValueError, ZeroDivisionError, OverflowError):
                want = got
            same = (bits(got) == bits(want)) or (got != got and want != want)
            if not same:
                mism += 1
                if first is None:
                    first = (p, got, want)
            try:
                refv = ref(*p) if arity == 2 else ref(p)
                e = ulp_err(got, refv)
            except (ValueError, ZeroDivisionError, OverflowError, TypeError):
                continue
            if e > worst:
                worst, wa = e, p
        flag = "" if (mism == 0 and worst <= args.ulp_limit) else "   <-- CHECK"
        if flag:
            bad += 1
        print("%-8s n=%-5d proto-mismatch %-4d worst %.4f ulp at %r%s" % (name, len(pts), mism, worst, wa, flag))
        if first:
            print("         first mismatch: %r got %r want %r" % first)
    if not args.keep:
        pass
    print("probe dir", d)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
