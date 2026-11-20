#!/usr/bin/env python3
"""T453: regenerates the generated native 128-bit run tests and their expected stdout lines.

Writes tests/run/int128_native/{arith_matrix_i128,arith_matrix_u128,shifts_i128,shifts_u128,divrem_stress,casts}.ax
and tests/run/saturating_native/{i128,u128}_saturating.ax. Expected values come from exact Python integers
(reduced modulo 2^128 for wrapping operations, clamped for saturating ones). abi_calls.ax is hand-written.

Usage: python tests/run/int128_native/regen_expected.py
"""
import os
import random
import sys

out_dir = os.path.dirname(os.path.abspath(__file__))
sat_dir = os.path.join(os.path.dirname(out_dir), "saturating_native")
M128 = (1 << 128) - 1
IMIN = -(1 << 127)
IMAX = (1 << 127) - 1


def wrap(v, signed):
    v &= M128
    if signed and v >= (1 << 127):
        v -= 1 << 128
    return v


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def trem(a, b):
    return a - tdiv(a, b) * b


def lit(ty, v):
    if v == IMIN and ty == "i128":
        return f"({IMIN + 1}i128 - 1i128)"
    if v < 0:
        return f"({v}{ty})"
    return f"{v}{ty}"


def header(lines, comment):
    L = ["// test: run", "// modes: interp native", "// exit: 0"]
    for e in lines:
        L.append(f"// stdout: {e}\\n")
    for c in comment:
        L.append("// " + c)
    L.append("")
    return L


def write(name, L):
    with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


PRINT_BOOL = """fn print_bool(b: bool) {
    if b {
        print("1");
    } else {
        print("0");
    }
}
"""


# ---------------------------------------------------------------- arithmetic matrix
def arith(ty, signed, vals):
    exp = []
    for a in vals:
        for b in vals:
            row = [wrap(a + b, signed), wrap(a - b, signed), wrap(a * b, signed),
                   wrap(a & b, signed), wrap(a | b, signed), wrap(a ^ b, signed)]
            cmp = [int(a < b), int(a <= b), int(a == b), int(a != b), int(a > b), int(a >= b)]
            if b != 0 and not (signed and a == IMIN and b == -1):
                dv = f"{tdiv(a, b)} {trem(a, b)}"
            else:
                dv = "-"
            lo_b, hi_b = (IMIN, IMAX) if signed else (0, M128)
            sat = [min(max(v, lo_b), hi_b) for v in (a + b, a - b, a * b)]
            exp.append(" ".join(str(x) for x in row) + " " + "".join(str(c) for c in cmp) + " " + dv +
                       " S " + " ".join(str(x) for x in sat))
    for a in vals:
        neg = wrap(-a, signed)
        exp.append(f"U {wrap(~a, signed)} {neg}")
    L = header(exp, [
        f"T453: native {ty} register-pair arithmetic matrix (ADD/ADC, SUB/SBB, MUL+IMUL cross terms, AND/OR/XOR,",
        "128-bit compares via SUB/SBB flags, udiv128/sdiv128 division and remainder, saturating ADD/SUB/MUL",
        "clamped with CMOVcc, NOT and two's-complement negation). Expected lines: exact Python integers mod 2^128.",
    ])
    n = len(vals)
    arr = ", ".join(lit(ty, v) for v in vals)
    L.append(PRINT_BOOL)
    L.append(f"fn pair(a: {ty}, b: {ty}) {{")
    for i, op in enumerate(["a.wrapping_add(b)", "a.wrapping_sub(b)", "a.wrapping_mul(b)", "a & b", "a | b", "a ^ b"]):
        if i > 0:
            L.append('    print(" ");')
        L.append(f"    print_int({op});")
    L.append('    print(" ");')
    for c in ["a < b", "a <= b", "a == b", "a != b", "a > b", "a >= b"]:
        L.append(f"    print_bool({c});")
    L.append('    print(" ");')
    zero = lit(ty, 0)
    if signed:
        cond = f"b != {zero} && !(a == ({IMIN + 1}i128 - 1i128) && b == (-1i128))"
    else:
        cond = f"b != {zero}"
    L.append(f"    if {cond} {{")
    L.append("        print_int(a / b);")
    L.append('        print(" ");')
    L.append("        print_int(a % b);")
    L.append("    } else {")
    L.append('        print("-");')
    L.append("    }")
    L.append('    print(" S ");')
    L.append("    print_int(a.saturating_add(b));")
    L.append('    print(" ");')
    L.append("    print_int(a.saturating_sub(b));")
    L.append('    print(" ");')
    L.append("    print_int(a.saturating_mul(b));")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    L.append(f"fn unary(a: {ty}) {{")
    L.append('    print("U ");')
    L.append("    print_int(~a);")
    L.append('    print(" ");')
    L.append("    print_int(a.wrapping_neg());")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    L.append("fn main() -> i32 {")
    L.append(f"    let vals: [{n}]{ty} = [{arr}];")
    L.append("    let mut i: usize = 0;")
    L.append(f"    while i < {n} {{")
    L.append("        let mut j: usize = 0;")
    L.append(f"        while j < {n} {{")
    L.append("            pair(vals[i], vals[j]);")
    L.append("            j = j + 1;")
    L.append("        }")
    L.append("        i = i + 1;")
    L.append("    }")
    L.append("    let mut k: usize = 0;")
    L.append(f"    while k < {n} {{")
    L.append("        unary(vals[k]);")
    L.append("        k = k + 1;")
    L.append("    }")
    L.append("    0")
    L.append("}")
    write(f"arith_matrix_{ty}.ax", L)


# ---------------------------------------------------------------- shifts / rotates
def shifts(ty, signed, vals):
    exp = []
    for v in vals:
        u = v & M128
        for c in range(128):
            shl = wrap(u << c, signed)
            if signed:
                shr = wrap(v >> c, signed)
            else:
                shr = u >> c
            rl = wrap(((u << c) | (u >> ((128 - c) % 128))) & M128 if c else u, signed)
            rr = wrap(((u >> c) | (u << ((128 - c) % 128))) & M128 if c else u, signed)
            exp.append(f"{c} {shl} {shr} {rl} {rr}")
    L = header(exp, [
        f"T453: native {ty} shifts for every count 0..127 (SHLD/SHRD + SHL/SHR/SAR by CL, `test cl, 64` +",
        "CMOVcc limb select) and rotates; expected lines from exact Python integers.",
    ])
    n = len(vals)
    arr = ", ".join(lit(ty, v) for v in vals)
    L.append(f"fn row(v: {ty}, c: u32) {{")
    L.append("    print_int(c);")
    L.append('    print(" ");')
    L.append(f"    print_int(v << ({lit(ty, 0)} + (c as {ty})));")
    L.append('    print(" ");')
    L.append(f"    print_int(v >> ({lit(ty, 0)} + (c as {ty})));")
    L.append('    print(" ");')
    L.append("    print_int(v.rotate_left(c));")
    L.append('    print(" ");')
    L.append("    print_int(v.rotate_right(c));")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    L.append("fn main() -> i32 {")
    L.append(f"    let vals: [{n}]{ty} = [{arr}];")
    L.append("    let mut i: usize = 0;")
    L.append(f"    while i < {n} {{")
    L.append("        let mut c: u32 = 0u32;")
    L.append("        while c < 128u32 {")
    L.append("            row(vals[i], c);")
    L.append("            c = c + 1u32;")
    L.append("        }")
    L.append("        i = i + 1;")
    L.append("    }")
    L.append("    0")
    L.append("}")
    write(f"shifts_{ty}.ax", L)


# ---------------------------------------------------------------- division stress
def divstress():
    rnd = random.Random(453)
    pairs = []
    for _ in range(120):
        abits = rnd.choice([1, 8, 63, 64, 65, 100, 127, 128])
        bbits = rnd.choice([1, 2, 32, 63, 64, 65, 96, 127, 128])
        a = rnd.getrandbits(abits) | (1 << (abits - 1))
        b = rnd.getrandbits(bbits) | (1 << (bbits - 1))
        pairs.append((a, b))
    pairs += [(M128, 1), (M128, M128), (M128 - 1, M128), (1 << 64, (1 << 64) - 1), ((1 << 127), 3), (12345, 1 << 100)]
    exp = []
    for a, b in pairs:
        sa, sb = wrap(a, True), wrap(b, True)
        if sb == 0 or (sa == IMIN and sb == -1):
            sres = "-"
        else:
            sres = f"{tdiv(sa, sb)} {trem(sa, sb)}"
        exp.append(f"{a // b} {a % b} {sres}")
    L = header(exp, [
        "T453: udiv128 (two chained DIVs when the divisor fits in 64 bits, 128-step restoring loop otherwise) and",
        "sdiv128 (|a| / |b| with quotient sign sa^sb, remainder sign sa) over seeded random operand widths.",
        "The i128 columns reinterpret the same bit patterns as signed values.",
    ])
    n = len(pairs)
    a_arr = ", ".join(f"{a}u128" for a, _ in pairs)
    b_arr = ", ".join(f"{b}u128" for _, b in pairs)
    L.append("fn row(a: u128, b: u128) {")
    L.append("    print_int(a / b);")
    L.append('    print(" ");')
    L.append("    print_int(a % b);")
    L.append('    print(" ");')
    L.append("    let sa = a as i128;")
    L.append("    let sb = b as i128;")
    L.append("    if sb == 0i128 || (sa == (-170141183460469231731687303715884105727i128 - 1i128) && sb == (-1i128)) {")
    L.append('        print("-");')
    L.append("    } else {")
    L.append("        print_int(sa / sb);")
    L.append('        print(" ");')
    L.append("        print_int(sa % sb);")
    L.append("    }")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    L.append("fn main() -> i32 {")
    L.append(f"    let a: [{n}]u128 = [{a_arr}];")
    L.append(f"    let b: [{n}]u128 = [{b_arr}];")
    L.append("    let mut i: usize = 0;")
    L.append(f"    while i < {n} {{")
    L.append("        row(a[i], b[i]);")
    L.append("        i = i + 1;")
    L.append("    }")
    L.append("    0")
    L.append("}")
    write("divrem_stress.ax", L)


# ---------------------------------------------------------------- casts
def casts():
    narrow = [("i8", 8, True), ("i16", 16, True), ("i32", 32, True), ("i64", 64, True), ("isize", 64, True),
              ("u8", 8, False), ("u16", 16, False), ("u32", 32, False), ("u64", 64, False), ("usize", 64, False)]
    srcs = [0, 1, -1, IMIN, IMAX, (1 << 64) + 0x80, -(1 << 64) - 0x7F, 0x123456789ABCDEF0FEDCBA9876543210]
    exp = []
    for v in srcs:
        u = v & M128
        parts = []
        for ty, bits, s in narrow:
            m = u & ((1 << bits) - 1)
            if s and m >= (1 << (bits - 1)):
                m -= 1 << bits
            parts.append(str(m))
        parts.append(str(u))
        exp.append("T " + " ".join(parts))
    widen_vals = {"i8": [-128, -1, 0, 127], "i16": [-32768, -2, 32767], "i32": [-(1 << 31), -3, (1 << 31) - 1],
                  "i64": [-(1 << 63), -5, (1 << 63) - 1], "u8": [0, 200, 255], "u16": [65535, 1], "u32": [(1 << 32) - 1],
                  "u64": [(1 << 64) - 1, 1 << 63]}
    for ty, vs in widen_vals.items():
        for v in vs:
            exp.append(f"W {v} {v & M128} {wrap(v & M128, True)}")
    L = header(exp, [
        "T453: native i128/u128 TRUNC to every narrow width and SEXT/ZEXT from every narrow width.",
    ])
    L.append("fn trunc_all(v: i128) {")
    L.append('    print("T");')
    for ty, _, _ in narrow:
        L.append('    print(" ");')
        if ty in ("u64", "usize"):
            L.append(f"    print_int((v as {ty}) as u128);")
        else:
            L.append(f"    print_int(v as {ty});")
    L.append('    print(" ");')
    L.append("    print_int(v as u128);")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    for ty in widen_vals:
        L.append(f"fn widen_{ty}(v: {ty}) {{")
        L.append('    print("W ");')
        if ty == "u64":
            L.append("    print_int(v as u128);")
        else:
            L.append("    print_int(v);")
        L.append('    print(" ");')
        L.append("    print_int(v as u128);")
        L.append('    print(" ");')
        L.append("    print_int((v as u128) as i128);")
        L.append('    print("\\n");')
        L.append("}")
        L.append("")
    L.append("fn main() -> i32 {")
    n = len(srcs)
    L.append(f"    let srcs: [{n}]i128 = [{', '.join(lit('i128', v) for v in srcs)}];")
    L.append("    let mut i: usize = 0;")
    L.append(f"    while i < {n} {{")
    L.append("        trunc_all(srcs[i]);")
    L.append("        i = i + 1;")
    L.append("    }")
    for ty, vs in widen_vals.items():
        for v in vs:
            if ty.startswith("i") and v == -(1 << (int(ty[1:]) - 1)):
                vl = f"({v + 1}{ty} - 1{ty})"
            elif v < 0:
                vl = f"({v}{ty})"
            else:
                vl = f"{v}{ty}"
            L.append(f"    widen_{ty}({vl});")
    L.append("    0")
    L.append("}")
    write("casts.ax", L)


arith("i128", True, [IMIN, IMIN + 1, -(1 << 64) - 1, -(1 << 64), -(1 << 63), -7, -1, 0, 1, 3, (1 << 63), (1 << 64) - 1,
                     1 << 64, 0x0123456789ABCDEF0011223344556677, IMAX - 1, IMAX])
arith("u128", False, [0, 1, 3, 7, (1 << 63), (1 << 64) - 1, 1 << 64, (1 << 64) + 1, 0xFEDCBA98765432100123456789ABCDEF,
                      (1 << 127) - 1, 1 << 127, M128 - 1, M128])
shifts("i128", True, [-1, IMIN, 0x7EDCBA98765432100123456789ABCDEF, -0x123456789ABCDEF0123456789A])
shifts("u128", False, [1, M128, 0xFEDCBA98765432100123456789ABCDEF])
divstress()
casts()


# ---------------------------------------------------------------- saturating_native 128-bit rows
def sat_clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def sat_lit(ty, v, lo):
    if v == lo and lo < 0:
        return f"({lo + 1}{ty} - 1{ty})"
    if v < 0:
        return f"({v}{ty})"
    return f"{v}{ty}"

def gen_saturating(ty, signed):
    if signed:
        lo, hi = -(1 << 127), (1 << 127) - 1
        vals = [lo, lo + 1, -(1 << 64), -(1 << 63), -2, -1, 0, 1, 2, (1 << 63), (1 << 64) - 1, (1 << 64), hi - 1, hi]
        consts = [1, -1, 2, -(1 << 64), hi]
    else:
        lo, hi = 0, (1 << 128) - 1
        vals = [0, 1, 2, 3, (1 << 63), (1 << 64) - 1, (1 << 64), (1 << 64) + 1, (1 << 127) - 1, (1 << 127), hi - 1, hi]
        consts = [1, 2, (1 << 64), hi]
    n = len(vals)
    exp = []
    for a in vals:
        for b in vals:
            exp.append(f"{sat_clamp(a + b, lo, hi)} {sat_clamp(a - b, lo, hi)} {sat_clamp(a * b, lo, hi)}")
    for a in vals:
        row = []
        for c in consts:
            row.append(str(sat_clamp(a + c, lo, hi)))
            row.append(str(sat_clamp(a - c, lo, hi)))
            row.append(str(sat_clamp(a * c, lo, hi)))
        exp.append("C " + " ".join(row))
    L = []
    L.append("// test: run")
    L.append("// modes: interp native")
    L.append("// exit: 0")
    for e in exp:
        L.append(f"// stdout: {e}\\n")
    L.append(f"// T453: 128-bit row of the native saturating suite (T481 covers 8..64 bits). Expected lines are the")
    L.append(f"// SPEC-40 clamping oracle min(max(exact(a op b), {ty}.MIN), {ty}.MAX) computed with exact integers.")
    L.append("")
    L.append(f"fn check_pair(a: {ty}, b: {ty}) {{")
    L.append(f"    let ra: {ty} = a.saturating_add(b);")
    L.append(f"    let rs: {ty} = a.saturating_sub(b);")
    L.append(f"    let rm: {ty} = a.saturating_mul(b);")
    L.append("    print_int(ra);")
    L.append('    print(" ");')
    L.append("    print_int(rs);")
    L.append('    print(" ");')
    L.append("    print_int(rm);")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    L.append(f"fn check_consts(a: {ty}) {{")
    L.append('    print("C");')
    for c in consts:
        cl = sat_lit(ty, c, lo)
        for op in ("saturating_add", "saturating_sub", "saturating_mul"):
            L.append('    print(" ");')
            L.append(f"    print_int(a.{op}({cl}));")
    L.append('    print("\\n");')
    L.append("}")
    L.append("")
    L.append("fn main() -> i32 {")
    arr = ", ".join(sat_lit(ty, v, lo) for v in vals)
    L.append(f"    let vals: [{n}]{ty} = [{arr}];")
    L.append("    let mut i: usize = 0;")
    L.append(f"    while i < {n} {{")
    L.append("        let mut j: usize = 0;")
    L.append(f"        while j < {n} {{")
    L.append("            check_pair(vals[i], vals[j]);")
    L.append("            j = j + 1;")
    L.append("        }")
    L.append("        i = i + 1;")
    L.append("    }")
    L.append("    let mut k: usize = 0;")
    L.append(f"    while k < {n} {{")
    L.append("        check_consts(vals[k]);")
    L.append("        k = k + 1;")
    L.append("    }")
    L.append("    0")
    L.append("}")
    with open(os.path.join(sat_dir, f"{ty}_saturating.ax"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

gen_saturating("i128", True)
gen_saturating("u128", False)
print("regenerated int128_native and saturating_native 128-bit tests")
