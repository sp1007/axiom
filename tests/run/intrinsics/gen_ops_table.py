#!/usr/bin/env python3
"""Generator of tests/run/intrinsics/ops_table.ax (T134, ADR-0034 OI-03 style independent oracle).

Every expected value below is computed here, in Python, from the definition of the operation
(wrapping arithmetic modulo 2**bits, rotation by n mod bits, leading/trailing zero and one counts of the
bit pattern); nothing is derived from axiom0's interpreter or its native back end. The generated test
checks wrapping_{add,sub,mul,neg}_<w>, rotate_{left,right}_<w>, leading_zeros_<w>, trailing_zeros_<w> and
count_ones_<w> for all ten integer widths in both executors.

    python tests/run/intrinsics/gen_ops_table.py           # rewrite ops_table.ax
    python tests/run/intrinsics/gen_ops_table.py --check   # exit 1 if the file differs
"""
import os
import sys

WIDTHS = [("i8", 8, True), ("i16", 16, True), ("i32", 32, True), ("i64", 64, True), ("isize", 64, True),
          ("u8", 8, False), ("u16", 16, False), ("u32", 32, False), ("u64", 64, False), ("usize", 64, False)]


def lit(v, name, bits, signed):
    """Axiom literal of value v (already in the signed/unsigned range of the type)."""
    if v < 0:
        if v == -(1 << (bits - 1)):
            # the minimum is not the negation of a literal of its own type (the literal would overflow)
            return "(-%d%s - 1%s)" % ((1 << (bits - 1)) - 1, name, name)
        return "(-%d%s)" % (-v, name)
    return "%d%s" % (v, name)


def to_type(v, bits, signed):
    v &= (1 << bits) - 1
    if signed and v >> (bits - 1):
        v -= 1 << bits
    return v


def pattern(v, bits):
    return v & ((1 << bits) - 1)


def lcg(seed):
    while True:
        seed = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        yield seed >> 11


def values(name, bits, signed):
    mask = (1 << bits) - 1
    gen = lcg(bits * 31 + (7 if signed else 3))
    raw = [0, 1, 2, 3, mask, mask - 1, 1 << (bits - 1), (1 << (bits - 1)) - 1,
           0x5555555555555555 & mask, 0xAAAAAAAAAAAAAAAA & mask, next(gen) & mask, next(gen) & mask]
    out = []
    for r in raw:
        t = to_type(r, bits, signed)
        if t not in out:
            out.append(t)
    return out


def bin_values(vals):
    # a subset for the binary operations: every operand pair would be too many checks
    pick = [vals[i] for i in (0, 1, 4, 6, 8) if i < len(vals)]
    out = []
    for p in pick:
        if p not in out:
            out.append(p)
    return out


def clz(p, bits):
    return bits - p.bit_length()


def ctz(p, bits):
    if p == 0:
        return bits
    return (p & -p).bit_length() - 1


def rotl(p, n, bits):
    n %= bits
    return ((p << n) | (p >> (bits - n))) & ((1 << bits) - 1) if n else p


def rotr(p, n, bits):
    n %= bits
    return ((p >> n) | (p << (bits - n))) & ((1 << bits) - 1) if n else p


CHUNK = 40  # checks per generated function: the native back end allows at most 1024 blocks per function


def gen_width(name, bits, signed):
    vals = values(name, bits, signed)
    bvals = bin_values(vals)
    L = lambda v: lit(v, name, bits, signed)
    checks = []

    def check(call, expected_lit, ty):
        checks.append((call, expected_lit))

    for a in bvals:
        for b in bvals:
            pa, pb = pattern(a, bits), pattern(b, bits)
            check("wrapping_add_%s(%s, %s)" % (name, L(a), L(b)), L(to_type(pa + pb, bits, signed)), name)
            check("wrapping_sub_%s(%s, %s)" % (name, L(a), L(b)), L(to_type(pa - pb, bits, signed)), name)
            check("wrapping_mul_%s(%s, %s)" % (name, L(a), L(b)), L(to_type(pa * pb, bits, signed)), name)
    for a in vals:
        pa = pattern(a, bits)
        check("wrapping_neg_%s(%s)" % (name, L(a)), L(to_type(-pa, bits, signed)), name)
        check("leading_zeros_%s(%s)" % (name, L(a)), "%du32" % clz(pa, bits), "u32")
        check("trailing_zeros_%s(%s)" % (name, L(a)), "%du32" % ctz(pa, bits), "u32")
        check("count_ones_%s(%s)" % (name, L(a)), "%du32" % bin(pa).count("1"), "u32")
        for n in (0, 1, bits - 1, bits, bits + 1, 4294967295):
            check("rotate_left_%s(%s, %du32)" % (name, L(a), n), L(to_type(rotl(pa, n, bits), bits, signed)), name)
            check("rotate_right_%s(%s, %du32)" % (name, L(a), n), L(to_type(rotr(pa, n, bits), bits, signed)), name)
    lines = []
    chunks = [checks[k:k + CHUNK] for k in range(0, len(checks), CHUNK)]
    cid = 0
    for k, chunk in enumerate(chunks):
        lines.append("fn check_%s_%d() -> i32 {" % (name, k))
        lines.append("    let mut bad: i32 = 0;")
        for call, expected in chunk:
            cid += 1
            lines.append("    if %s != %s { bad = bad + 1; fail(\"%s\", %d); }" % (call, expected, name, cid))
        lines.append("    bad")
        lines.append("}")
        lines.append("")
    lines.append("fn check_%s() -> i32 {" % name)
    lines.append("    let mut bad: i32 = 0;")
    for k in range(len(chunks)):
        lines.append("    bad = bad + check_%s_%d();" % (name, k))
    lines.append("    bad")
    lines.append("}")
    return lines


def render():
    out = []
    out.append("// test: run")
    out.append("// modes: interp native")
    out.append("// timeout: 300")
    out.append("// stdout: INTRINSIC OPS TABLE OK\\n")
    out.append("// GENERATED by tests/run/intrinsics/gen_ops_table.py - do not edit by hand.")
    out.append("// Expected values are computed in Python from the definition of each operation (T134).")
    out.append("")
    for name, bits, signed in WIDTHS:
        T = name
        out.append("@intrinsic fn wrapping_add_%s(a: %s, b: %s) -> %s { 0 }" % (T, T, T, T))
        out.append("@intrinsic fn wrapping_sub_%s(a: %s, b: %s) -> %s { 0 }" % (T, T, T, T))
        out.append("@intrinsic fn wrapping_mul_%s(a: %s, b: %s) -> %s { 0 }" % (T, T, T, T))
        out.append("@intrinsic fn wrapping_neg_%s(a: %s) -> %s { 0 }" % (T, T, T))
        out.append("@intrinsic fn rotate_left_%s(a: %s, b: u32) -> %s { 0 }" % (T, T, T))
        out.append("@intrinsic fn rotate_right_%s(a: %s, b: u32) -> %s { 0 }" % (T, T, T))
        out.append("@intrinsic fn leading_zeros_%s(a: %s) -> u32 { 0 }" % (T, T))
        out.append("@intrinsic fn trailing_zeros_%s(a: %s) -> u32 { 0 }" % (T, T))
        out.append("@intrinsic fn count_ones_%s(a: %s) -> u32 { 0 }" % (T, T))
    out.append("")
    # print_int is not used: the native print_int prints NUL digits (an unrelated defect), so the failing
    # check ids are rendered with print() of single digits.
    out.append("fn print_digit(d: i32) {")
    out.append("    if d == 0 { print(\"0\"); } else if d == 1 { print(\"1\"); } else if d == 2 { print(\"2\"); }")
    out.append("    else if d == 3 { print(\"3\"); } else if d == 4 { print(\"4\"); } else if d == 5 { print(\"5\"); }")
    out.append("    else if d == 6 { print(\"6\"); } else if d == 7 { print(\"7\"); } else if d == 8 { print(\"8\"); }")
    out.append("    else { print(\"9\"); }")
    out.append("}")
    out.append("")
    out.append("fn print_dec(n: i32) {")
    out.append("    if n >= 10 { print_dec(n / 10); }")
    out.append("    print_digit(n % 10);")
    out.append("}")
    out.append("")
    out.append("fn fail(width: Str, id: i32) {")
    out.append("    print(width);")
    out.append("    print(\" #\");")
    out.append("    print_dec(id);")
    out.append("    print(\"\\n\");")
    out.append("}")
    out.append("")
    for name, bits, signed in WIDTHS:
        out.extend(gen_width(name, bits, signed))
        out.append("")
    out.append("fn main() -> i32 {")
    out.append("    let mut bad: i32 = 0;")
    for name, bits, signed in WIDTHS:
        out.append("    bad = bad + check_%s();" % name)
    out.append("    if bad != 0 { return 1; }")
    out.append("    print(\"INTRINSIC OPS TABLE OK\\n\");")
    out.append("    0")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ops_table.ax")
    text = render()
    if "--check" in sys.argv[1:]:
        with open(path, "r", encoding="utf-8", newline="") as f:
            ok = f.read() == text
        print("ops_table.ax " + ("up to date" if ok else "DIFFERS"))
        return 0 if ok else 1
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
