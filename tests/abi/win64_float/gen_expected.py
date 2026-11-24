#!/usr/bin/env python3
"""T459: Python IEEE-754 oracle for abi_calls.ax (writes abi_calls.txt; `--check` verifies it).

Each expression mirrors abi_calls.ax operation by operation: f64 arithmetic is CPython binary64; f32
arithmetic is computed in binary64 and rounded once to binary32 (correct for + - * / since 53 >= 2*24+2).
"""

import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def r32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def b64(x):
    return str(struct.unpack("<q", struct.pack("<d", x))[0])


def b32(x):
    return str(struct.unpack("<i", struct.pack("<f", x))[0])


def mix(a, b, c, d, e):
    return float(a) * 1000.0 + b * 100.0 + float(c) * 10.0 + d + e / 8.0


def first_f32(x, y, z, w):
    t = r32(r32(x * 4.0) + r32(y * 2.0))
    t = r32(t + z)
    return r32(t - w)


def many(a, b, c, d, e, f, g, h, i, j):
    acc = a + float(b) * 2.0
    acc = acc + c * 3.0
    acc = acc + float(d) * 5.0
    acc = acc + e * 7.0
    acc = acc + f * 11.0
    acc = acc + float(g) * 13.0
    acc = acc + h * 17.0
    acc = acc + i * 19.0
    acc = acc + float(j) * 23.0
    return acc


def only_stack_floats(a, b, c, d, e, f, g):
    t = r32(float(a + b + c + d))
    t = r32(t + r32(e * 2.0))
    t = r32(t + r32(r32(f) * 4.0))
    return r32(t + r32(g * 8.0))


def fsum(n, acc):
    while n != 0:
        acc = acc + float(n) * 0.5
        n -= 1
    return acc


def churn(x):
    acc = x
    for _ in range(10):
        acc = acc * 1.5 - 0.25
    return acc


def expected():
    out = []
    out.append(b64(mix(3, 1.5, 7, 0.25, 0.5)))
    out.append(b64(mix(-2, -0.125, 65535, -3.5, 1024.0)))
    out.append(b32(first_f32(1.5, -2.25, 0.125, 8.0)))
    out.append(b64(many(1.0, 2, 3.5, -4, 5.25, 6.5, -7, 8.125, 9.75, 200)))
    out.append(b32(only_stack_floats(1, 2, 3, 4, 0.5, 0.75, -1.25)))
    out.append(b64(fsum(40, 0.0)))
    out.append(b64(1.25 * 4.0))
    out.append(b32(r32(-0.5 * 4.0)))
    out.append("42")
    out.append(b32(-2.5))
    out.append(b32(1.5))
    out.append(b64(mix(1, 2.0, 3, 4.0, 8.0)))
    out.append(b64(-2.5 + 1.0))
    c1 = churn(1.0)
    c2 = churn(3.75)
    out.append(b64(c1))
    out.append(b64(c2))
    out.append(b64(3.75))
    out.append(b32(-0.5))
    out.append(b64(3.75 + (-0.5) + c1))
    return "\n".join(out) + "\n"


def main():
    path = os.path.join(HERE, "abi_calls.txt")
    text = expected()
    if "--check" in sys.argv:
        with open(path, encoding="utf-8", newline="") as f:
            ok = f.read() == text
        print("GEN-ABI-EXPECTED %s" % ("up to date" if ok else "STALE"))
        return 0 if ok else 1
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
