#!/usr/bin/env python3
"""T453 QA (gate round 0): regenerates the adversarial native 128-bit run tests qa_*.ax in this directory.

Expected stdout lines come from exact Python integers mirroring each Axiom function. Every test runs
in interp and native (-O0 and -O1 variants are added by axtest); native must agree byte for byte.

Usage: python tests/run/int128_native/qa_regen.py
"""
import os

here = os.path.dirname(os.path.abspath(__file__))
M = (1 << 128) - 1
IMIN = -(1 << 127)
IMAX = (1 << 127) - 1


def u(v):
    return v & M


def s(v):
    v &= M
    return v - (1 << 128) if v >= (1 << 127) else v


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def trem(a, b):
    return a - tdiv(a, b) * b


def write(name, head_comment, body_lines, expected):
    L = ["// test: run", "// modes: interp native", "// exit: 0"]
    for e in expected:
        L.append(f"// stdout: {e}\\n")
    for c in head_comment:
        L.append("// " + c)
    L.append("")
    L += body_lines
    with open(os.path.join(here, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


def ulit(v):
    return f"{u(v)}u128"


# ---------------------------------------------------------------- A: div/rem boundary matrix
def gen_divrem_edges():
    vals = [0, 1, 2, 3, 10, -1, -2, -3, (1 << 63) - 1, 1 << 63, (1 << 63) + 1, (1 << 64) - 1, 1 << 64,
            (1 << 64) + 1, 1 << 65, (1 << 100) + 12345, IMAX, IMAX - 1, IMIN, IMIN + 1, -(1 << 63), -(1 << 63) - 1,
            -(1 << 64), -(1 << 64) - 1, -(10 ** 30), 10 ** 30, (1 << 127) | 1, M, 0xFFFFFFFF, 1 << 32,
            0x8000000000000000FFFFFFFFFFFFFFFF, 0x00000001000000000000000000000000]
    pats = [u(v) for v in vals]
    n = len(pats)

    def mix(acc, v):
        return u(acc * 1000003 + v)

    exp = []
    for i in range(n):
        ua = 0
        sa = 0
        for j in range(n):
            a, b = pats[i], pats[j]
            if b != 0:
                ua = mix(ua, a // b)
                ua = mix(ua, a % b)
            x, y = s(a), s(b)
            if y != 0 and not (x == IMIN and y == -1):
                sa = mix(sa, u(tdiv(x, y)))
                sa = mix(sa, u(trem(x, y)))
        exp.append(f"{ua} {s(sa)}")
    body = [
        "fn mix(acc: u128, v: u128) -> u128 {",
        "    acc.wrapping_mul(1000003u128).wrapping_add(v)",
        "}",
        "",
        "fn main() -> i32 {",
        f"    let vals: [{n}]u128 = [" + ", ".join(ulit(v) for v in pats) + "];",
        "    let mut i: usize = 0;",
        f"    while i < {n} {{",
        "        let mut ua: u128 = 0u128;",
        "        let mut sa: u128 = 0u128;",
        "        let mut j: usize = 0;",
        f"        while j < {n} {{",
        "            let a = vals[i];",
        "            let b = vals[j];",
        "            if b != 0u128 {",
        "                ua = mix(ua, a / b);",
        "                ua = mix(ua, a % b);",
        "            }",
        "            let x = a as i128;",
        "            let y = b as i128;",
        "            if y != 0i128 && !(x == (-170141183460469231731687303715884105727i128 - 1i128) && y == (-1i128)) {",
        "                sa = mix(sa, (x / y) as u128);",
        "                sa = mix(sa, (x % y) as u128);",
        "            }",
        "            j = j + 1;",
        "        }",
        "        print_int(ua);",
        "        print(\" \");",
        "        print_int(sa as i128);",
        "        print(\"\\n\");",
        "        i = i + 1;",
        "    }",
        "    0",
        "}",
    ]
    write("qa_divrem_edges.ax", [
        "QA (T453 gate): full pairwise boundary matrix for udiv128/sdiv128 (zero/one/2^63/2^64/MIN/MAX/divisors with hi=1,",
        "lo=0, negative multiples). Each row folds every quotient/remainder of one dividend into a wrapping hash.",
        "i128 MIN / -1 pairs are skipped (they panic: covered by qa_panic_i128_*)."], body, exp)


# ---------------------------------------------------------------- B: register pressure / flags liveness
def gen_pressure():
    def f1(p):
        p0, p1, p2, p3, p4, p5, p6, p7 = p
        a = u(p0 + p1)
        b = u(p2 - p3)
        c = u(p4 * p5)
        d = p6 ^ p7
        lt = a < b
        slt = s(c) < s(d)
        e = u(a + c)
        f = u(b - d)
        g = (a & d) | (b & c)
        h = u(e * f)
        k = (h >> 5) ^ u(g << 77)
        m = u(k + p7) if lt else u(k - p0)
        n = (m ^ e) if slt else (m ^ f)
        sh = p3 & 127
        o = u(n << sh)
        r = u((o ^ h) + a + b + c + d)
        sg = (s(r) >> (p5 & 127))
        return u(r ^ u(sg))

    inputs = [
        (1, 2, 3, 4, 5, 6, 7, 8),
        (M, 1, 0, 1, M, M, 1 << 127, 3),
        (1 << 64, (1 << 64) - 1, 1 << 63, 1 << 63, (1 << 64) + 5, 77, 1 << 127, (1 << 127) - 1),
        (0x0123456789ABCDEF0123456789ABCDEF, 0xFEDCBA9876543210FEDCBA9876543210, 1 << 100, 127, 64, 63, 0, M),
        (123456789012345678901234567890, 987654321098765432109876543210, 5, 128, 2 ** 90 + 1, 2 ** 70 - 1, 99, 100),
    ]
    exp = [str(f1(p)) for p in inputs]

    def f2(seed):
        sv = seed
        acc = 0
        for i in range(300):
            sv = sv ^ u(sv << 13)
            sv = sv ^ (sv >> 7)
            sv = sv ^ u(sv << 17)
            t = u(sv * 0x2545F4914F6CDD1D2545F4914F6CDD1D)
            acc = u(acc + t)
            if s(t) < 0:
                r = i & 127
                acc = u(acc << r) | (acc >> ((128 - r) & 127)) if r else acc
            if t & 1:
                acc = u(acc - (t >> 64))
            if (t >> 64) < (acc & ((1 << 64) - 1)):
                acc = acc ^ t
        return acc

    seeds = [1, 0x9E3779B97F4A7C15F39CC0605CEDC835, M, 1 << 127]
    exp += [str(f2(sd)) for sd in seeds]

    body = [
        "fn f1(p0: u128, p1: u128, p2: u128, p3: u128, p4: u128, p5: u128, p6: u128, p7: u128) -> u128 {",
        "    let a = p0.wrapping_add(p1);",
        "    let b = p2.wrapping_sub(p3);",
        "    let c = p4.wrapping_mul(p5);",
        "    let d = p6 ^ p7;",
        "    let lt = a < b;",
        "    let slt = (c as i128) < (d as i128);",
        "    let e = a.wrapping_add(c);",
        "    let f = b.wrapping_sub(d);",
        "    let g = (a & d) | (b & c);",
        "    let h = e.wrapping_mul(f);",
        "    let k = (h >> 5u32) ^ (g << 77u32);",
        "    let m = if lt { k.wrapping_add(p7) } else { k.wrapping_sub(p0) };",
        "    let n = if slt { m ^ e } else { m ^ f };",
        "    let sh = p3 & 127u128;",
        "    let o = n << sh;",
        "    let r = (o ^ h).wrapping_add(a).wrapping_add(b).wrapping_add(c).wrapping_add(d);",
        "    let sg = (r as i128) >> (p5 & 127u128);",
        "    r ^ (sg as u128)",
        "}",
        "",
        "fn f2(seed: u128) -> u128 {",
        "    let mut sv: u128 = seed;",
        "    let mut acc: u128 = 0u128;",
        "    let mut i: u32 = 0u32;",
        "    while i < 300u32 {",
        "        sv = sv ^ (sv << 13u32);",
        "        sv = sv ^ (sv >> 7u32);",
        "        sv = sv ^ (sv << 17u32);",
        "        let t = sv.wrapping_mul(" + ulit(0x2545F4914F6CDD1D2545F4914F6CDD1D) + ");",
        "        acc = acc.wrapping_add(t);",
        "        if (t as i128) < 0i128 {",
        "            let r = i & 127u32;",
        "            if r != 0u32 {",
        "                acc = (acc << r) | (acc >> (128u32 - r));",
        "            }",
        "        }",
        "        if (t & 1u128) != 0u128 {",
        "            acc = acc.wrapping_sub(t >> 64u32);",
        "        }",
        "        if (t >> 64u32) < (acc & 18446744073709551615u128) {",
        "            acc = acc ^ t;",
        "        }",
        "        i = i + 1u32;",
        "    }",
        "    acc",
        "}",
        "",
        "fn main() -> i32 {",
    ]
    for p in inputs:
        body.append("    print_int(f1(" + ", ".join(ulit(x) for x in p) + "));")
        body.append("    print(\"\\n\");")
    for sd in seeds:
        body.append(f"    print_int(f2({ulit(sd)}));")
        body.append("    print(\"\\n\");")
    body += ["    0", "}"]
    write("qa_pressure_flags.ax", [
        "QA (T453 gate): register pressure (8 live pairs -> spills), flags produced early and consumed late (lt/slt),",
        "shift counts derived from the operand's own limbs, and a loop-carried xorshift/rotate hash. Targets -O1 regalloc/peephole."],
        body, exp)


# ---------------------------------------------------------------- C: calls
def gen_calls():
    exp = []
    xs = [5, -7, (1 << 100) + 3, IMIN, IMAX]
    body = [
        "struct S {",
        "    a: i128,",
        "    k: u8,",
        "    b: u128,",
        "}",
        "",
        "fn clobber(mut a: i128, b: i128) -> i128 {",
        "    a = a + 1i128;",
        "    a + b",
        "}",
        "",
        "fn id(a: i128) -> i128 {",
        "    a",
        "}",
        "",
        "fn two(a: i128, b: i128) -> i128 {",
        "    a - b",
        "}",
        "",
        "fn five(a: i128, b: i128, c: i128, d: i128, e: i128) -> i128 {",
        "    a - b + c * 2i128 - d + e",
        "}",
        "",
        "fn mixed(a: i64, x: i128, b: u8, y: u128, c: i32, z: i128) -> i128 {",
        "    (a as i128) * 3i128 + x + (b as i128) + (y as i128) + (c as i128) + z",
        "}",
        "",
        "fn mk(x: i128, k: u8) -> S {",
        "    S { a: x + 1i128, k: k, b: (x as u128) ^ 255u128 }",
        "}",
        "",
        "fn use_s(s: S, t: S) -> i128 {",
        "    s.a + (s.k as i128) + (s.b as i128) - t.a + (t.k as i128)",
        "}",
        "",
        "fn rec(n: u32, acc: i128) -> i128 {",
        "    if n == 0u32 {",
        "        acc",
        "    } else {",
        "        rec(n - 1u32, acc * 3i128 + (n as i128))",
        "    }",
        "}",
        "",
        "fn nest(a: i128, b: i128) -> i128 {",
        "    two(two(a, b), two(b, a)) + clobber(id(a), id(b))",
        "}",
        "",
        "fn main() -> i32 {",
        "    let xs: [5]i128 = [5i128, (-7i128), 1267650600228229401496703205379i128, (-170141183460469231731687303715884105727i128 - 1i128), 170141183460469231731687303715884105727i128];",
        "    let mut i: usize = 0;",
        "    while i < 4 {",
        "        let x = xs[i];",
        "        let y = xs[i + 1];",
        "        let q = x / 8i128;",
        "        let r = y / 8i128;",
        "        print_int(clobber(q, q));",
        "        print(\" \");",
        "        print_int(q);",
        "        print(\" \");",
        "        print_int(two(id(q), id(r)));",
        "        print(\" \");",
        "        print_int(nest(q, r));",
        "        print(\" \");",
        "        print_int(five(id(q), id(r), id(q), id(r), id(q)));",
        "        print(\" \");",
        "        print_int(mixed((q as i64), r, (q as u8), (r as u128), (q as i32), id(q)));",
        "        print(\" \");",
        "        let s1 = mk(q, (r as u8));",
        "        let s2 = mk(r, 9u8);",
        "        print_int(use_s(s1, s2));",
        "        print(\" \");",
        "        print_int(use_s(mk(id(r), 1u8), mk(id(q), 2u8)));",
        "        print(\" \");",
        "        print_int(s1.a);",
        "        print(\" \");",
        "        print_int(s1.b);",
        "        print(\"\\n\");",
        "        i = i + 1;",
        "    }",
        "    print_int(rec(60u32, 1i128));",
        "    print(\"\\n\");",
        "    0",
        "}",
    ]

    def trunc_i(v, bits, signed):
        v &= (1 << bits) - 1
        if signed and v >= 1 << (bits - 1):
            v -= 1 << bits
        return v

    for i in range(4):
        x, y = xs[i], xs[i + 1]
        q = tdiv(x, 8)
        r = tdiv(y, 8)

        def chk(v):
            assert IMIN <= v <= IMAX, "python mirror overflows (would panic)"
            return v
        a1 = chk(chk(q + 1) + q)
        t1 = chk(q - r)
        nest = chk(chk(q - r) - chk(r - q)) + chk(chk(q + 1) + r)
        chk(nest)
        f5 = chk(chk(chk(chk(q - r) + chk(q * 2)) - r) + q)
        mx = chk(chk(chk(chk(chk(trunc_i(q, 64, True) * 3 + r) + trunc_i(q, 8, False)) + r) + trunc_i(q, 32, True)) + q)
        # note: (r as u128) as i128 in `mixed` -> y param is u128, cast back to i128 = r again
        s1a = q + 1
        s1k = trunc_i(r, 8, False)
        s1b = u(q) ^ 255
        s2a = r + 1
        s2k = 9
        s2b = u(r) ^ 255
        us12 = chk(s1a + s1k + s(s1b) - s2a + s2k)
        s3a = chk(r + 1)
        s3k = 1
        s3b = u(r) ^ 255
        s4a = chk(q + 1)
        s4k = 2
        us34 = chk(s3a + s3k + s(s3b) - s4a + s4k)
        exp.append(f"{a1} {q} {t1} {nest} {f5} {mx} {us12} {us34} {s1a} {s1b}")
    acc = 1
    for n in range(60, 0, -1):
        acc = acc * 3 + n
    exp.append(str(acc))
    write("qa_calls.ax", [
        "QA (T453 gate): Win64 16-byte boundaries — by-reference parameters must be copies (callee mutation invisible to the",
        "caller, even when the same variable is passed twice), nested calls whose sret temporaries must not alias, 5 pair params",
        "(stack spill slots), mixed narrow/wide lists, structs with 128-bit fields passed and returned by value, deep recursion."],
        body, exp)


# ---------------------------------------------------------------- D: shifts with varied amount types / self-derived amounts
def gen_shifts():
    vals = [1, M, IMIN, IMAX, 0x8000000000000000, 0x1_0000000000000000, 0xDEADBEEFCAFEBABE0123456789ABCDEF, 3]
    amts = [0, 1, 63, 64, 65, 126, 127]
    exp = []
    L = []
    for v in vals:
        parts = []
        for c in amts:
            parts.append(str(u(u(v) << c)))
            parts.append(str(u(v) >> c))
            parts.append(str(u(s(v) >> c)))
        exp.append(" ".join(parts))
    # self derived
    for v in vals:
        sh1 = u(v) & 127
        sh2 = (u(v) >> 64) & 127
        exp.append(f"{u(u(v) << sh1)} {u(v) >> sh2} {u(s(v) >> sh1)} {u(s(v) << sh2)}")
    body = [
        "fn row(v: u128) {",
        "    let sv = v as i128;",
        "    let c0: u8 = 0u8;",
        "    let c1: u32 = 1u32;",
        "    let c63: u64 = 63u64;",
        "    let c64: i32 = 64i32;",
        "    let c65: u128 = 65u128;",
        "    let c126: i64 = 126i64;",
        "    let c127: usize = 127usize;",
    ]
    names = [("c0", 0), ("c1", 1), ("c63", 63), ("c64", 64), ("c65", 65), ("c126", 126), ("c127", 127)]
    for nm, _ in names:
        body += [
            f"    print_int(v << {nm}); print(\" \"); print_int(v >> {nm}); print(\" \"); print_int((sv >> {nm}) as u128);",
            "    print(\" \");",
        ]
    body[-1] = "    print(\"\\n\");"
    body += [
        "}",
        "",
        "fn selfrow(v: u128) {",
        "    let sv = v as i128;",
        "    let sh1 = v & 127u128;",
        "    let sh2 = (v >> 64u32) & 127u128;",
        "    print_int(v << sh1); print(\" \"); print_int(v >> sh2); print(\" \"); print_int((sv >> sh1) as u128); print(\" \"); print_int((sv << sh2) as u128);",
        "    print(\"\\n\");",
        "}",
        "",
        "fn main() -> i32 {",
        f"    let vals: [{len(vals)}]u128 = [" + ", ".join(ulit(v) for v in vals) + "];",
        "    let mut i: usize = 0;",
        f"    while i < {len(vals)} {{",
        "        row(vals[i]);",
        "        i = i + 1;",
        "    }",
        "    i = 0;",
        f"    while i < {len(vals)} {{",
        "        selfrow(vals[i]);",
        "        i = i + 1;",
        "    }",
        "    0",
        "}",
    ]
    write("qa_shift_amount_types.ax", [
        "QA (T453 gate): shifts at the limb boundaries (0/1/63/64/65/126/127) with amounts of types u8/u32/u64/i32/u128/i64/usize,",
        "and amounts derived from the shifted value's own limbs (CL/RCX register-allocation conflicts)."], body, exp)


gen_divrem_edges()
gen_pressure()
gen_calls()
gen_shifts()
print("OK")
