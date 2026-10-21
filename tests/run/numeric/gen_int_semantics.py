#!/usr/bin/env python3
"""Independent Python reference generator for Axiom integer semantics (T140 / ADR-0034).

Computes expected results purely from SPEC-03 rules (Python 3 stdlib only, arbitrary-precision int):
  - AXS-SEM-030: checked `+`, `-`, `*`, unary `-` (trap on overflow with exit 101, `panic: arithmetic overflow`)
  - AXS-SEM-031: `wrapping_{add,sub,mul,neg}`, `rotate_{left,right}`, `{leading,trailing}_zeros`, `count_ones`
  - AXS-SEM-032: `/` and `%` truncating toward zero; `/ 0` and `% 0` trap (`panic: division by zero`);
                 signed `MIN / -1` and `MIN % -1` trap (`panic: arithmetic overflow`)
  - AXS-SEM-033: bitwise `&`, `|`, `^`, unary `~`
  - AXS-SEM-034: shifts `<<` and `>>` (logical on unsigned, arithmetic on signed); shift amount
                 `< 0` or `>= width` traps (`panic: shift amount out of range`)
  - AXS-SEM-035: comparisons `==`, `!=`, `<`, `<=`, `>`, `>=`

Covers all ten integer types (`i8`, `i16`, `i32`, `i64`, `isize`, `u8`, `u16`, `u32`, `u64`, `usize`)
on the 64-bit target (`isize`/`usize` = 64 bits), with the T140 edge operand set
`{0, 1, 2, MAX, MIN, MAX-1, MIN+1, 2^(w-1), 2^(w-1)+/-1, -1 for signed}` and shift amount set
`{0, 1, 31, 32, 33, w-1, w, w+1, negative for signed amount types}`.

Grouping (TYPE A, per T140 specification):
  - `tests/run/numeric/boundary.ax`: prints and pins `stdout:` across all 10 integer types for
    non-trapping edge values of AXS-SEM-030, AXS-SEM-032, AXS-SEM-033, AXS-SEM-034, AXS-SEM-035.
  - `tests/run/numeric/intrinsic_ops.ax`: all AXS-SEM-031 wrapping/bit-intrinsic cases across all 10
    integer types, with computed edge results printed and pinned on `stdout:`.
  - `tests/run/numeric/int_sem/sem030_<ty>.ax` .. `sem035_<ty>.ax` (50 files, one per type x op family):
    full matrix of non-trapping checks for that `(type, family)` returning a deterministic non-zero exit
    code `11..99` derived from the runtime results (and byte-identical in `axiomc_e2e`).
  - `tests/run/numeric/int_sem/trap_<ty>_<case>.ax` (125 files, one per trapping case across all 10 types):
    pinned to `exit: 101` and the exact SPEC-03 `stderr: panic: ...` line.

Usage:
  python tests/run/numeric/gen_int_semantics.py              # write generated files
  python tests/run/numeric/gen_int_semantics.py check        # verify committed files match
  python tests/run/numeric/gen_int_semantics.py --check [--tmp <dir>]
"""

import os
import shutil
import sys
import tempfile

TYPES = [
    ("i8", 8, True),
    ("i16", 16, True),
    ("i32", 32, True),
    ("i64", 64, True),
    ("isize", 64, True),
    ("u8", 8, False),
    ("u16", 16, False),
    ("u32", 32, False),
    ("u64", 64, False),
    ("usize", 64, False),
]

CHUNK = 25


def type_bounds(bits, signed):
    if signed:
        return -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    return 0, (1 << bits) - 1


def pattern(v, bits):
    """Two's-complement w-bit unsigned representation of integer v."""
    return v & ((1 << bits) - 1)


def to_type(p, bits, signed):
    """Interpret low `bits` of integer `p` as signed or unsigned value."""
    p &= (1 << bits) - 1
    if signed and (p & (1 << (bits - 1))):
        return p - (1 << bits)
    return p


def lit(v, name, bits, signed):
    """Axiom source expression for value v of type `name`.

    Values >= 2^63 on unsigned 64-bit types are emitted via bitwise complement/shift of literals < 2^63
    so they do not depend on >63-bit literal lexing in stage-1 before T155.
    """
    lo, hi = type_bounds(bits, signed)
    if v < 0:
        if v == lo:
            return "(-%d%s - 1%s)" % ((1 << (bits - 1)) - 1, name, name)
        return "(-%d%s)" % (-v, name)
    if not signed and bits == 64 and v >= (1 << 63):
        if v == hi:
            return "(~0%s)" % name
        if v == (1 << 63):
            return "(1%s << 63)" % name
        diff = hi - v
        return "((~0%s) - %d%s)" % (name, diff, name)
    return "%d%s" % (v, name)


def edge_operands(name, bits, signed):
    """Exact edge operand set from T140:
    {0, 1, 2, MAX, MIN, MAX-1, MIN+1, 2^(w-1), 2^(w-1)+/-1, -1 for signed}.
    """
    lo, hi = type_bounds(bits, signed)
    raw = [
        0,
        1,
        2,
        hi,
        lo,
        hi - 1,
        lo + 1,
        to_type(1 << (bits - 1), bits, signed),
        to_type((1 << (bits - 1)) - 1, bits, signed),
        to_type((1 << (bits - 1)) + 1, bits, signed),
    ]
    if signed:
        raw.append(-1)
    out = []
    for v in raw:
        if lo <= v <= hi and v not in out:
            out.append(v)
    return out


def shift_amounts_u32(bits):
    """Unsigned shift/rotate amounts from T140: {0, 1, 31, 32, 33, w-1, w, w+1} (+ 40 for 64-bit)."""
    cands = [0, 1, 31, 32, 33, bits - 1, bits, bits + 1]
    if bits == 64:
        cands.insert(5, 40)
    out = []
    for c in cands:
        if c >= 0 and c not in out:
            out.append(c)
    return out


def shift_amounts_i32(bits):
    """Signed shift amounts including negative values (AXS-SEM-034)."""
    cands = [-bits, -1, 0, 1, 31, 32, 33, bits - 1, bits, bits + 1]
    if bits == 64:
        cands.insert(7, 40)
    out = []
    for c in cands:
        if c not in out:
            out.append(c)
    return out


def trunc_div_rem(a, b):
    """SPEC-03 AXS-SEM-032: truncating division toward zero and remainder with sign of `a`."""
    neg_q = (a < 0) ^ (b < 0)
    q_mag = abs(a) // abs(b)
    q = -q_mag if neg_q else q_mag
    r = a - q * b
    return q, r


def clz(p, bits):
    return bits - p.bit_length()


def ctz(p, bits):
    if p == 0:
        return bits
    return (p & -p).bit_length() - 1


def rotl(p, n, bits):
    n %= bits
    if n == 0:
        return p
    return ((p << n) | (p >> (bits - n))) & ((1 << bits) - 1)


def rotr(p, n, bits):
    n %= bits
    if n == 0:
        return p
    return ((p >> n) | (p << (bits - n))) & ((1 << bits) - 1)


def to_u64_expr(expr_str, rty, name, bits, signed):
    if rty == name:
        if signed:
            u_equiv = {8: "u8", 16: "u16", 32: "u32", 64: "u64"}[bits]
            return "((%s) as %s) as u64" % (expr_str, u_equiv)
        return "(%s) as u64" % expr_str
    if rty in ("u32", "bool"):
        return "(%s) as u64" % expr_str
    raise ValueError("unexpected result type: %s" % rty)


def emit_family_file(fam_name, name, bits, signed, vals, u_shifts, s_shifts, checks, witness_exprs):
    """Emit a compact per-(type, family) .ax file with 1-line checks and non-zero witness exit code."""
    L = lambda v: lit(v, name, bits, signed)
    # Compute expected exit code in 11..99 from witness_exprs
    acc = 0
    for _e, _rty, u64_val in witness_exprs:
        acc = ((acc * 31) ^ (u64_val & 0xFFFF)) & 0x7FFFFFFF
    expected_exit = 11 + (acc % 89)

    out = []
    out.append("// test: run")
    out.append("// modes: interp native")
    out.append("// exit: %d" % expected_exit)
    out.append("// GENERATED by tests/run/numeric/gen_int_semantics.py - do not edit by hand.")
    out.append("")

    chunks = [checks[i:i + CHUNK] for i in range(0, len(checks), CHUNK)]
    for k, chunk in enumerate(chunks):
        out.append("fn chunk_%d(z: %s, zu32: u32, zi32: i32) -> i32 {" % (k, name))
        used_v = set()
        used_su = set()
        used_si = set()
        for _lhs, _rhs, v_refs, su_refs, si_refs in chunk:
            used_v.update(v_refs)
            used_su.update(su_refs)
            used_si.update(si_refs)
        for vi in sorted(used_v):
            out.append("    let v_%d: %s = %s | z;" % (vi, name, L(vals[vi])))
        for si in sorted(used_su):
            out.append("    let su_%d: u32 = %du32 | zu32;" % (si, u_shifts[si]))
        for si in sorted(used_si):
            sval = s_shifts[si]
            slit = "(-%di32)" % (-sval) if sval < 0 else "%di32" % sval
            out.append("    let si_%d: i32 = %s | zi32;" % (si, slit))
        for idx, (lhs_expr, exp_expr, _vr, _sur, _sir) in enumerate(chunk):
            out.append("    if (%s) != (%s) { return %d; }" % (lhs_expr, exp_expr, idx + 1))
        out.append("    0")
        out.append("}")
        out.append("")

    out.append("fn main() -> i32 {")
    out.append("    let z: %s = 0%s;" % (name, name))
    out.append("    let zu32: u32 = 0u32;")
    out.append("    let zi32: i32 = 0i32;")
    for k in range(len(chunks)):
        out.append("    if chunk_%d(z, zu32, zi32) != 0 { return %d; }" % (k, k + 1))
    for vi in range(len(vals)):
        out.append("    let v_%d: %s = %s | z;" % (vi, name, L(vals[vi])))
    for si in range(len(u_shifts)):
        out.append("    let su_%d: u32 = %du32 | zu32;" % (si, u_shifts[si]))
    out.append("    let mut acc: u64 = 0u64;")
    for expr_str, rty, _u64_val in witness_exprs:
        u_expr = to_u64_expr(expr_str, rty, name, bits, signed)
        out.append("    acc = ((acc * 31u64) ^ ((%s) & 65535u64)) & 2147483647u64;" % u_expr)
    out.append("    11 + ((acc % 89u64) as i32)")
    out.append("}")
    return "\n".join(out) + "\n", len(checks)


def generate_type_family_files(name, bits, signed):
    """Generate sem030_<name>.ax .. sem035_<name>.ax for type `name`."""
    lo, hi = type_bounds(bits, signed)
    vals = edge_operands(name, bits, signed)
    u_shifts = shift_amounts_u32(bits)
    s_shifts = shift_amounts_i32(bits)
    L = lambda v: lit(v, name, bits, signed)

    sem030 = []
    sem032 = []
    sem033 = []
    sem034 = []
    sem035 = []

    # AXS-SEM-030: checked +, -, *, unary -
    for ai, a in enumerate(vals):
        for bi, b in enumerate(vals):
            if lo <= a + b <= hi:
                sem030.append(("v_%d + v_%d" % (ai, bi), L(a + b), (ai, bi), (), ()))
            if lo <= a - b <= hi:
                sem030.append(("v_%d - v_%d" % (ai, bi), L(a - b), (ai, bi), (), ()))
            if lo <= a * b <= hi:
                sem030.append(("v_%d * v_%d" % (ai, bi), L(a * b), (ai, bi), (), ()))
        if signed and lo <= -a <= hi:
            sem030.append(("-v_%d" % ai, L(-a), (ai,), (), ()))

    # AXS-SEM-032: / and % (truncating toward zero)
    for ai, a in enumerate(vals):
        for bi, b in enumerate(vals):
            if b == 0:
                continue
            if signed and a == lo and b == -1:
                continue
            q, r = trunc_div_rem(a, b)
            sem032.append(("v_%d / v_%d" % (ai, bi), L(q), (ai, bi), (), ()))
            sem032.append(("v_%d %% v_%d" % (ai, bi), L(r), (ai, bi), (), ()))

    # AXS-SEM-033: bitwise &, |, ^, ~
    for ai, a in enumerate(vals):
        pa = pattern(a, bits)
        for bi, b in enumerate(vals):
            pb = pattern(b, bits)
            sem033.append(("v_%d & v_%d" % (ai, bi), L(to_type(pa & pb, bits, signed)), (ai, bi), (), ()))
            sem033.append(("v_%d | v_%d" % (ai, bi), L(to_type(pa | pb, bits, signed)), (ai, bi), (), ()))
            sem033.append(("v_%d ^ v_%d" % (ai, bi), L(to_type(pa ^ pb, bits, signed)), (ai, bi), (), ()))
        r_not = to_type((~pa) & ((1 << bits) - 1), bits, signed)
        sem033.append(("~v_%d" % ai, L(r_not), (ai,), (), ()))

    # AXS-SEM-034: << and >> for valid shift amounts (0 <= s < bits) with u32, i32, and same-type rhs
    for ai, a in enumerate(vals):
        pa = pattern(a, bits)
        for si, s in enumerate(u_shifts):
            if 0 <= s < bits:
                r_shl = to_type((pa << s) & ((1 << bits) - 1), bits, signed)
                r_shr = (a >> s) if signed else to_type(pa >> s, bits, False)
                sem034.append(("v_%d << su_%d" % (ai, si), L(r_shl), (ai,), (si,), ()))
                sem034.append(("v_%d >> su_%d" % (ai, si), L(r_shr), (ai,), (si,), ()))
                if lo <= s <= hi:
                    sem034.append(("v_%d << (%s | z)" % (ai, L(s)), L(r_shl), (ai,), (), ()))
                    sem034.append(("v_%d >> (%s | z)" % (ai, L(s)), L(r_shr), (ai,), (), ()))
        for si, s in enumerate(s_shifts):
            if 0 <= s < bits:
                r_shl = to_type((pa << s) & ((1 << bits) - 1), bits, signed)
                r_shr = (a >> s) if signed else to_type(pa >> s, bits, False)
                sem034.append(("v_%d << si_%d" % (ai, si), L(r_shl), (ai,), (), (si,)))
                sem034.append(("v_%d >> si_%d" % (ai, si), L(r_shr), (ai,), (), (si,)))

    # AXS-SEM-035: comparisons == != < <= > >= across all edge operands `a` and key boundary operands `b`
    cmp_b_indices = []
    for cand in (0, 1, hi, lo, to_type(1 << (bits - 1), bits, signed), to_type((1 << (bits - 1)) - 1, bits, signed), -1):
        if cand in vals:
            idx_c = vals.index(cand)
            if idx_c not in cmp_b_indices:
                cmp_b_indices.append(idx_c)
    for ai, a in enumerate(vals):
        for bi in cmp_b_indices:
            b = vals[bi]
            for op_str, res_bool in (
                ("==", a == b),
                ("!=", a != b),
                ("<", a < b),
                ("<=", a <= b),
                (">", a > b),
                (">=", a >= b),
            ):
                b_lit = "true" if res_bool else "false"
                sem035.append(("v_%d %s v_%d" % (ai, op_str, bi), b_lit, (ai, bi), (), ()))

    # Representative witness expressions for each family file (all guaranteed non-overflowing!)
    i_zero = vals.index(0)
    i_one = vals.index(1)
    i_two = vals.index(2)
    i_hi = vals.index(hi)
    i_lo = vals.index(lo)
    hb = to_type(1 << (bits - 1), bits, signed)
    i_hb = vals.index(hb)
    su_w1 = u_shifts.index(bits - 1)

    p030 = [
        ("v_%d - v_%d" % (i_hi, i_one), name, pattern(hi - 1, bits)),
        ("v_%d + v_%d" % (i_lo, i_one), name, pattern(lo + 1, bits)),
        ("v_%d * v_%d" % (i_two, i_two), name, pattern(4, bits)),
    ]
    q_hb2, r_hb2 = trunc_div_rem(hb, 2)
    q_hi2, r_hi2 = trunc_div_rem(hi, 2)
    p032 = [
        ("v_%d / v_%d" % (i_hb, i_two), name, pattern(q_hb2, bits)),
        ("v_%d %% v_%d" % (i_hb, i_two), name, pattern(r_hb2, bits)),
        ("v_%d / v_%d" % (i_hi, i_two), name, pattern(q_hi2, bits)),
        ("v_%d %% v_%d" % (i_hi, i_two), name, pattern(r_hi2, bits)),
    ]
    p033 = [
        ("v_%d ^ v_%d" % (i_hi, i_hb), name, pattern(hi, bits) ^ pattern(hb, bits)),
        ("~v_%d" % i_zero, name, (~0) & ((1 << bits) - 1)),
    ]
    shl_1 = to_type((1 << (bits - 1)) & ((1 << bits) - 1), bits, signed)
    shr_hb = (hb >> (bits - 1)) if signed else to_type(pattern(hb, bits) >> (bits - 1), bits, False)
    p034 = [
        ("v_%d << su_%d" % (i_one, su_w1), name, pattern(shl_1, bits)),
        ("v_%d >> su_%d" % (i_hb, su_w1), name, pattern(shr_hb, bits)),
    ]
    p035 = [
        ("v_%d < v_%d" % (i_lo, i_hi), "bool", 1 if lo < hi else 0),
        ("v_%d > v_%d" % (i_hi, i_hb), "bool", 1 if hi > hb else 0),
        ("v_%d == v_%d" % (i_hi, i_hi), "bool", 1),
        ("v_%d != v_%d" % (i_lo, i_hi), "bool", 1),
    ]

    files = {}
    total = 0
    for fam_name, checks, pexprs in (
        ("sem030", sem030, p030),
        ("sem032", sem032, p032),
        ("sem033", sem033, p033),
        ("sem034", sem034, p034),
        ("sem035", sem035, p035),
    ):
        text, n = emit_family_file(fam_name, name, bits, signed, vals, u_shifts, s_shifts, checks, pexprs)
        files["%s_%s.ax" % (fam_name, name)] = text
        total += n
    return files, total, (p030, p032, p033, p034, p035)


def generate_boundary_file():
    """Generate tests/run/numeric/boundary.ax printing and pinning `stdout:` for all 10 integer types
    across AXS-SEM-030, AXS-SEM-032, AXS-SEM-033, AXS-SEM-034, AXS-SEM-035.
    """
    stdout_lines = []
    body_lines = []
    total_cases = 0

    for name, bits, signed in TYPES:
        lo, hi = type_bounds(bits, signed)
        L = lambda v: lit(v, name, bits, signed)
        hb = to_type(1 << (bits - 1), bits, signed)
        q_hb2, r_hb2 = trunc_div_rem(hb, 2)
        q_hi2, r_hi2 = trunc_div_rem(hi, 2)
        sh_amt = bits - 1
        shl_1 = to_type((1 << sh_amt) & ((1 << bits) - 1), bits, signed)
        shr_hb = (hb >> sh_amt) if signed else to_type(pattern(hb, bits) >> sh_amt, bits, False)
        xor_hi_hb = pattern(hi, bits) ^ pattern(hb, bits)
        cmp_bits = (
            ((1 if lo < hi else 0) << 3)
            | ((1 if hi > hb else 0) << 2)
            | ((1 if hi == hi else 0) << 1)
            | (1 if lo != hi else 0)
        )
        stdout_lines.append(
            "%s %d %d %d %d %d %d %d %d %d %d"
            % (
                name,
                pattern(hi - 1, bits),
                pattern(lo + 1, bits),
                pattern(q_hb2, bits),
                pattern(r_hb2, bits),
                pattern(q_hi2, bits),
                pattern(r_hi2, bits),
                xor_hi_hb,
                pattern(shl_1, bits),
                pattern(shr_hb, bits),
                cmp_bits,
            )
        )
        total_cases += 10
        body_lines.append("fn run_%s(z: %s, zu32: u32) {" % (name, name))
        body_lines.append("    let hi: %s = %s | z;" % (name, L(hi)))
        body_lines.append("    let lo: %s = %s | z;" % (name, L(lo)))
        body_lines.append("    let hb: %s = %s | z;" % (name, L(hb)))
        body_lines.append("    let one: %s = %s | z;" % (name, L(1)))
        body_lines.append("    let two: %s = %s | z;" % (name, L(2)))
        body_lines.append("    let sh: u32 = %du32 | zu32;" % sh_amt)
        body_lines.append("    let a_sub: %s = hi - one;" % name)
        body_lines.append("    let a_add: %s = lo + one;" % name)
        body_lines.append("    let q_hb: %s = hb / two;" % name)
        body_lines.append("    let r_hb: %s = hb %% two;" % name)
        body_lines.append("    let q_hi: %s = hi / two;" % name)
        body_lines.append("    let r_hi: %s = hi %% two;" % name)
        body_lines.append("    let bxor: %s = hi ^ hb;" % name)
        body_lines.append("    let bshl: %s = one << sh;" % name)
        body_lines.append("    let bshr: %s = hb >> sh;" % name)
        body_lines.append(
            "    let cbits: u64 = (((lo < hi) as u64) << 3u32) | (((hi > hb) as u64) << 2u32) | (((hi == hi) as u64) << 1u32) | ((lo != hi) as u64);"
        )
        body_lines.append("    print(\"%s \");" % name)
        for vexpr in ("a_sub", "a_add", "q_hb", "r_hb", "q_hi", "r_hi", "bxor", "bshl", "bshr"):
            body_lines.append("    print_u64_sp(%s);" % to_u64_expr(vexpr, name, name, bits, signed))
        body_lines.append("    print_u64(cbits);")
        body_lines.append("    print(\"\\n\");")
        body_lines.append("}")
        body_lines.append("")

    out = []
    out.append("// test: run")
    out.append("// modes: interp native")
    for sl in stdout_lines:
        out.append("// stdout: %s\\n" % sl)
    out.append("// GENERATED by tests/run/numeric/gen_int_semantics.py - do not edit by hand.")
    out.append("")
    out.append("fn print_digit(d: u64) {")
    out.append("    if d == 0u64 { print(\"0\"); } else if d == 1u64 { print(\"1\"); }")
    out.append("    else if d == 2u64 { print(\"2\"); } else if d == 3u64 { print(\"3\"); }")
    out.append("    else if d == 4u64 { print(\"4\"); } else if d == 5u64 { print(\"5\"); }")
    out.append("    else if d == 6u64 { print(\"6\"); } else if d == 7u64 { print(\"7\"); }")
    out.append("    else if d == 8u64 { print(\"8\"); } else { print(\"9\"); }")
    out.append("}")
    out.append("")
    out.append("fn print_u64(n: u64) {")
    out.append("    if n >= 10u64 { print_u64(n / 10u64); }")
    out.append("    print_digit(n % 10u64);")
    out.append("}")
    out.append("")
    out.append("fn print_u64_sp(n: u64) {")
    out.append("    print_u64(n);")
    out.append("    print(\" \");")
    out.append("}")
    out.append("")
    out.extend(body_lines)
    out.append("fn main() -> i32 {")
    out.append("    let u64_max: u64 = 18446744073709551615;")
    out.append("    if u64_max + 0u64 != 18446744073709551615 { return 2; }")
    for name, _bits, _signed in TYPES:
        out.append("    run_%s(0%s, 0u32);" % (name, name))
    out.append("    0")
    out.append("}")
    return "\n".join(out) + "\n", total_cases


def generate_intrinsic_ops_file():
    """Generate tests/run/numeric/intrinsic_ops.ax covering AXS-SEM-031 across all 10 integer types."""
    out = []
    stdout_lines = []
    total_cases = 0

    per_type = []
    for name, bits, signed in TYPES:
        lo, hi = type_bounds(bits, signed)
        vals = edge_operands(name, bits, signed)
        u_shifts = shift_amounts_u32(bits)
        L = lambda v: lit(v, name, bits, signed)
        checks = []
        for ai, a in enumerate(vals):
            pa = pattern(a, bits)
            for bi, b in enumerate(vals):
                pb = pattern(b, bits)
                r_add = to_type(pa + pb, bits, signed)
                r_sub = to_type(pa - pb, bits, signed)
                r_mul = to_type(pa * pb, bits, signed)
                checks.append(("wrapping_add_%s(v_%d, v_%d)" % (name, ai, bi), L(r_add), (ai, bi), ()))
                checks.append(("wrapping_sub_%s(v_%d, v_%d)" % (name, ai, bi), L(r_sub), (ai, bi), ()))
                checks.append(("wrapping_mul_%s(v_%d, v_%d)" % (name, ai, bi), L(r_mul), (ai, bi), ()))
            r_neg = to_type(-pa, bits, signed)
            checks.append(("wrapping_neg_%s(v_%d)" % (name, ai), L(r_neg), (ai,), ()))
            checks.append(("leading_zeros_%s(v_%d)" % (name, ai), "%du32" % clz(pa, bits), (ai,), ()))
            checks.append(("trailing_zeros_%s(v_%d)" % (name, ai), "%du32" % ctz(pa, bits), (ai,), ()))
            checks.append(("count_ones_%s(v_%d)" % (name, ai), "%du32" % bin(pa).count("1"), (ai,), ()))
            for si, s in enumerate(u_shifts):
                rl = to_type(rotl(pa, s, bits), bits, signed)
                rr = to_type(rotr(pa, s, bits), bits, signed)
                checks.append(("rotate_left_%s(v_%d, su_%d)" % (name, ai, si), L(rl), (ai,), (si,)))
                checks.append(("rotate_right_%s(v_%d, su_%d)" % (name, ai, si), L(rr), (ai,), (si,)))
        total_cases += len(checks)
        p_mul = pattern(to_type(pattern(hi, bits) * 2, bits, signed), bits)
        p_ones = bin(pattern(hi, bits)).count("1")
        stdout_lines.append("sem031 %s %d %d %d" % (name, len(checks), p_mul, p_ones))
        per_type.append((name, bits, signed, hi, vals, u_shifts, checks))

    out.append("// test: run")
    out.append("// modes: interp native")
    out.append("// timeout: 120")
    for sl in stdout_lines:
        out.append("// stdout: %s\\n" % sl)
    out.append("// GENERATED by tests/run/numeric/gen_int_semantics.py - do not edit by hand.")
    out.append("")
    for name, _bits, _signed in TYPES:
        out.append("@intrinsic fn wrapping_add_%s(a: %s, b: %s) -> %s { 0 }" % (name, name, name, name))
        out.append("@intrinsic fn wrapping_sub_%s(a: %s, b: %s) -> %s { 0 }" % (name, name, name, name))
        out.append("@intrinsic fn wrapping_mul_%s(a: %s, b: %s) -> %s { 0 }" % (name, name, name, name))
        out.append("@intrinsic fn wrapping_neg_%s(a: %s) -> %s { 0 }" % (name, name, name))
        out.append("@intrinsic fn rotate_left_%s(a: %s, b: u32) -> %s { 0 }" % (name, name, name))
        out.append("@intrinsic fn rotate_right_%s(a: %s, b: u32) -> %s { 0 }" % (name, name, name))
        out.append("@intrinsic fn leading_zeros_%s(a: %s) -> u32 { 0 }" % (name, name))
        out.append("@intrinsic fn trailing_zeros_%s(a: %s) -> u32 { 0 }" % (name, name))
        out.append("@intrinsic fn count_ones_%s(a: %s) -> u32 { 0 }" % (name, name))
    out.append("")
    out.append("fn print_digit(d: u64) {")
    out.append("    if d == 0u64 { print(\"0\"); } else if d == 1u64 { print(\"1\"); }")
    out.append("    else if d == 2u64 { print(\"2\"); } else if d == 3u64 { print(\"3\"); }")
    out.append("    else if d == 4u64 { print(\"4\"); } else if d == 5u64 { print(\"5\"); }")
    out.append("    else if d == 6u64 { print(\"6\"); } else if d == 7u64 { print(\"7\"); }")
    out.append("    else if d == 8u64 { print(\"8\"); } else { print(\"9\"); }")
    out.append("}")
    out.append("")
    out.append("fn print_u64(n: u64) {")
    out.append("    if n >= 10u64 { print_u64(n / 10u64); }")
    out.append("    print_digit(n % 10u64);")
    out.append("}")
    out.append("")

    for name, bits, signed, hi, vals, u_shifts, checks in per_type:
        L = lambda v: lit(v, name, bits, signed)
        chunks = [checks[i:i + CHUNK] for i in range(0, len(checks), CHUNK)]
        for k, chunk in enumerate(chunks):
            out.append("fn sem031_%s_%d(z: %s, zu32: u32) -> i32 {" % (name, k, name))
            used_v = set()
            used_su = set()
            for _lhs, _rhs, v_refs, su_refs in chunk:
                used_v.update(v_refs)
                used_su.update(su_refs)
            for vi in sorted(used_v):
                out.append("    let v_%d: %s = %s | z;" % (vi, name, L(vals[vi])))
            for si in sorted(used_su):
                out.append("    let su_%d: u32 = %du32 | zu32;" % (si, u_shifts[si]))
            for idx, (lhs_expr, exp_expr, _vr, _sur) in enumerate(chunk):
                out.append("    if (%s) != (%s) { return %d; }" % (lhs_expr, exp_expr, idx + 1))
            out.append("    0")
            out.append("}")
            out.append("")
        out.append("fn run_sem031_%s(z: %s, zu32: u32) -> i32 {" % (name, name))
        for k in range(len(chunks)):
            out.append("    if sem031_%s_%d(z, zu32) != 0 { return %d; }" % (name, k, k + 1))
        out.append("    let hi_v: %s = %s | z;" % (name, L(hi)))
        out.append("    let two_v: %s = %s | z;" % (name, L(2)))
        out.append("    let m: %s = wrapping_mul_%s(hi_v, two_v);" % (name, name))
        out.append("    let c: u32 = count_ones_%s(hi_v);" % name)
        out.append("    print(\"sem031 %s %d \");" % (name, len(checks)))
        out.append("    print_u64(%s);" % to_u64_expr("m", name, name, bits, signed))
        out.append("    print(\" \");")
        out.append("    print_u64(c as u64);")
        out.append("    print(\"\\n\");")
        out.append("    0")
        out.append("}")
        out.append("")

    out.append("fn main() -> i32 {")
    out.append("    let max_u64_lit: u64 = 18446744073709551615;")
    out.append("    if wrapping_add_u64(max_u64_lit, 1u64) != 0u64 { return 2; }")
    for name, _bits, _signed in TYPES:
        out.append("    if run_sem031_%s(0%s, 0u32) != 0 { return 1; }" % (name, name))
    out.append("    0")
    out.append("}")
    return "\n".join(out) + "\n", total_cases


def generate_trap_files(name, bits, signed):
    """Generate trap_<name>_<tag>.ax files for every SPEC-03 trapping category of type `name`."""
    lo, hi = type_bounds(bits, signed)
    L = lambda v: lit(v, name, bits, signed)
    V = lambda v: "id_%s(%s)" % (name, L(v))
    half = 1 << (bits // 2)

    traps = []

    # AXS-SEM-030: + overflow
    assert not (lo <= hi + 1 <= hi)
    traps.append(("add_max_1", "%s + %s" % (V(hi), V(1)), "arithmetic overflow"))
    if signed:
        assert not (lo <= lo + (-1) <= hi)
        traps.append(("add_min_neg1", "%s + %s" % (V(lo), V(-1)), "arithmetic overflow"))

    # AXS-SEM-030: - overflow
    assert not (lo <= lo - 1 <= hi)
    traps.append(("sub_min_1", "%s - %s" % (V(lo), V(1)), "arithmetic overflow"))
    if signed:
        assert not (lo <= hi - (-1) <= hi)
        traps.append(("sub_max_neg1", "%s - %s" % (V(hi), V(-1)), "arithmetic overflow"))

    # AXS-SEM-030: * overflow
    assert not (lo <= hi * 2 <= hi)
    traps.append(("mul_max_2", "%s * %s" % (V(hi), V(2)), "arithmetic overflow"))
    if signed:
        assert not (lo <= lo * (-1) <= hi)
        traps.append(("mul_min_neg1", "%s * %s" % (V(lo), V(-1)), "arithmetic overflow"))
        assert not (lo <= -lo <= hi)
        traps.append(("neg_min", "-(%s)" % V(lo), "arithmetic overflow"))
    else:
        assert not (lo <= half * half <= hi)
        traps.append(("mul_half_half", "%s * %s" % (V(half), V(half)), "arithmetic overflow"))

    # AXS-SEM-032: / and % traps
    traps.append(("div_zero", "%s / %s" % (V(1), V(0)), "division by zero"))
    traps.append(("rem_zero", "%s %% %s" % (V(1), V(0)), "division by zero"))
    if signed:
        traps.append(("div_min_neg1", "%s / %s" % (V(lo), V(-1)), "arithmetic overflow"))
        traps.append(("rem_min_neg1", "%s %% %s" % (V(lo), V(-1)), "arithmetic overflow"))

    # AXS-SEM-034: shift out of range (s >= bits or s < 0)
    traps.append(("shl_w", "%s << id_u32(%du32)" % (V(1), bits), "shift amount out of range"))
    traps.append(("shr_w", "%s >> id_u32(%du32)" % (V(1), bits), "shift amount out of range"))
    traps.append(("shl_neg1", "%s << id_i32(-1i32)" % V(1), "shift amount out of range"))
    traps.append(("shr_neg1", "%s >> id_i32(-1i32)" % V(1), "shift amount out of range"))

    files = {}
    for tag, expr, panic_msg in traps:
        fname = "trap_%s_%s.ax" % (name, tag)
        lines = [
            "// test: run",
            "// modes: interp native",
            "// exit: 101",
            "// stderr: panic: %s\\n" % panic_msg,
            "// GENERATED by tests/run/numeric/gen_int_semantics.py - do not edit by hand.",
            "",
            "fn id_%s(x: %s) -> %s { x }" % (name, name, name),
        ]
        if "id_u32" in expr and name != "u32":
            lines.append("fn id_u32(x: u32) -> u32 { x }")
        if "id_i32" in expr and name != "i32":
            lines.append("fn id_i32(x: i32) -> i32 { x }")
        lines.extend([
            "",
            "fn main() -> i32 {",
            "    let x: %s = %s;" % (name, expr),
            "    if x == %s { return 1; }" % L(0),
            "    0",
            "}",
        ])
        files[fname] = "\n".join(lines) + "\n"
    return files


def generate_all():
    """Return (dict of int_sem filename -> content, boundary_text, intrinsic_ops_text, ok_cases, trap_cases)."""
    files = {}
    ok_cases = 0
    trap_cases = 0
    for name, bits, signed in TYPES:
        fam_files, n_ok, _p = generate_type_family_files(name, bits, signed)
        files.update(fam_files)
        ok_cases += n_ok
        tfiles = generate_trap_files(name, bits, signed)
        files.update(tfiles)
        trap_cases += len(tfiles)
    bnd_text, n_bnd = generate_boundary_file()
    intr_text, n_intr = generate_intrinsic_ops_file()
    ok_cases += n_bnd + n_intr
    return files, bnd_text, intr_text, ok_cases, trap_cases


def write_tree(out_dir, files, bnd_path=None, bnd_text=None, intr_path=None, intr_text=None):
    os.makedirs(out_dir, exist_ok=True)
    for old_f in os.listdir(out_dir):
        if old_f.endswith(".ax") and old_f not in files:
            os.remove(os.path.join(out_dir, old_f))
    for fname, content in sorted(files.items()):
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    if bnd_path is not None and bnd_text is not None:
        with open(bnd_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(bnd_text)
    if intr_path is not None and intr_text is not None:
        with open(intr_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(intr_text)


def check_tree(committed_dir, committed_bnd, committed_intr, tmp_dir, files, bnd_text, intr_text, ok_cases, trap_cases):
    tmp_parent = os.path.dirname(tmp_dir)
    tmp_bnd = os.path.join(tmp_parent, "boundary.ax")
    tmp_intr = os.path.join(tmp_parent, "intrinsic_ops.ax")
    write_tree(tmp_dir, files, tmp_bnd, bnd_text, tmp_intr, intr_text)
    if not os.path.isdir(committed_dir):
        print("int_sem directory missing: %s" % committed_dir)
        return 1
    committed_files = sorted(f for f in os.listdir(committed_dir) if f.endswith(".ax"))
    expected_files = sorted(files.keys())
    if committed_files != expected_files:
        print("int_sem file list DIFFERS: committed=%d expected=%d" % (len(committed_files), len(expected_files)))
        return 1
    for fname in expected_files:
        cpath = os.path.join(committed_dir, fname)
        tpath = os.path.join(tmp_dir, fname)
        with open(cpath, "rb") as fc, open(tpath, "rb") as ft:
            if fc.read() != ft.read():
                print("int_sem/%s DIFFERS" % fname)
                return 1
    for label, cfile, tfile in (("boundary.ax", committed_bnd, tmp_bnd), ("intrinsic_ops.ax", committed_intr, tmp_intr)):
        if not os.path.isfile(cfile):
            print("%s missing: %s" % (label, cfile))
            return 1
        with open(cfile, "rb") as fc, open(tfile, "rb") as ft:
            if fc.read() != ft.read():
                print("%s DIFFERS" % label)
                return 1
    print(
        "int_sem up to date (%d files, %d non-trapping cases, %d trapping cases, %d total cases)"
        % (len(expected_files) + 2, ok_cases, trap_cases, ok_cases + trap_cases)
    )
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    here = os.path.dirname(os.path.abspath(__file__))
    committed_dir = os.path.join(here, "int_sem")
    committed_bnd = os.path.join(here, "boundary.ax")
    committed_intr = os.path.join(here, "intrinsic_ops.ax")
    files, bnd_text, intr_text, ok_cases, trap_cases = generate_all()

    is_check = False
    tmp_arg = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("check", "--check"):
            is_check = True
            i += 1
        elif a == "--tmp" and i + 1 < len(args):
            tmp_arg = args[i + 1]
            i += 2
        else:
            print("unknown argument: %s" % a, file=sys.stderr)
            return 2

    if is_check:
        if tmp_arg is not None:
            out_tmp = os.path.join(tmp_arg, "int_sem")
            return check_tree(
                committed_dir, committed_bnd, committed_intr, out_tmp, files, bnd_text, intr_text, ok_cases, trap_cases
            )
        tmp_root = tempfile.mkdtemp(prefix="int-sem-check-")
        try:
            return check_tree(
                committed_dir,
                committed_bnd,
                committed_intr,
                os.path.join(tmp_root, "int_sem"),
                files,
                bnd_text,
                intr_text,
                ok_cases,
                trap_cases,
            )
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)

    write_tree(committed_dir, files, committed_bnd, bnd_text, committed_intr, intr_text)
    print(
        "wrote %d files to %s + boundary.ax + intrinsic_ops.ax (%d non-trapping cases, %d trapping cases, %d total cases)"
        % (len(files) + 2, committed_dir, ok_cases, trap_cases, ok_cases + trap_cases)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
