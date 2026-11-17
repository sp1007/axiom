#!/usr/bin/env python3
"""Adversarial QA boundary oracle for T481 (native saturating_add/sub/mul on u8..isize).

Compiles and runs a generated multi-width Axiom program in a temporary directory
across three execution modes (--interp, native -O0, native -O1) and checks
bit-for-bit stdout equality against the SPEC-40 mathematical clamping oracle:
    sat_op_T(a, b) = min(max(exact_op(a, b), T.MIN), T.MAX)
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


UNSIGNED_TYPES = [
    ("u8", 8),
    ("u16", 16),
    ("u32", 32),
    ("u64", 64),
    ("usize", 64),
]

SIGNED_TYPES = [
    ("i8", 8),
    ("i16", 16),
    ("i32", 32),
    ("i64", 64),
    ("isize", 64),
]


def clamp(val, lo, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val


def sat_add(a, b, lo, hi):
    return clamp(a + b, lo, hi)


def sat_sub(a, b, lo, hi):
    return clamp(a - b, lo, hi)


def sat_mul(a, b, lo, hi):
    return clamp(a * b, lo, hi)


def unsigned_bounds(bits):
    return 0, (1 << bits) - 1


def signed_bounds(bits):
    return -(1 << (bits - 1)), (1 << (bits - 1)) - 1


def unsigned_test_vals(bits):
    _, hi = unsigned_bounds(bits)
    half = 1 << (bits - 1)
    qtr = 1 << (bits - 2)
    return [0, 1, 2, 3, qtr - 1, qtr, half - 1, half, half + 1, hi - 2, hi - 1, hi]


def signed_test_vals(bits):
    lo, hi = signed_bounds(bits)
    qtr = 1 << (bits - 2)
    return [lo, lo + 1, lo + 2, -qtr, -3, -2, -1, 0, 1, 2, 3, qtr, hi - 2, hi - 1, hi]


def fmt_lit(ty, bits, signed, v):
    if not signed:
        return f"{v}{ty}"
    lo, _ = signed_bounds(bits)
    if v == lo:
        return f"({lo + 1}{ty} - 1{ty})"
    if v < 0:
        return f"({v}{ty})"
    return f"{v}{ty}"


def generate_program_and_expected():
    lines = []
    expected = []

    lines.append("""
fn print_u64(v: u64) {
    if v >= 10u64 {
        print_u64(v / 10u64);
    }
    print_int((v % 10u64) as i64);
}

fn print_i64(v: i64) {
    if v < 0i64 {
        print("-");
        let mag: u64 = (0u64).wrapping_sub(v as u64);
        print_u64(mag);
    } else {
        print_u64(v as u64);
    }
}

fn opaque_id_u64(x: u64, step: usize) -> u64 {
    let mut acc: u64 = x;
    let mut i: usize = 0;
    while i < step {
        acc = acc ^ 0u64;
        i = i + 1;
    }
    acc
}
""".lstrip())

    # Generate helpers and test functions per unsigned type
    for ty, bits in UNSIGNED_TYPES:
        lo, hi = unsigned_bounds(bits)
        vals = unsigned_test_vals(bits)
        n = len(vals)
        arr_lits = ", ".join(fmt_lit(ty, bits, False, v) for v in vals)
        low_mask = (1 << bits) - 1
        high_mask = ((1 << 64) - 1) ^ low_mask
        dpat1 = 0xDEADBEEFCAFEBABE & high_mask
        dpat2 = 0xFFFFFFFFFFFFFFFF & high_mask
        dpat3 = 0x8000000080008000 & high_mask

        lines.append(f"""
fn chain_{ty}(a: {ty}, b: {ty}, c: {ty}, d: {ty}) -> {ty} {{
    let s1: {ty} = a.saturating_add(b).saturating_sub(c).saturating_mul(d);
    let s2: {ty} = a.saturating_mul(b).saturating_add(c).saturating_sub(d);
    s1.saturating_add(s2)
}}

fn dirty_{ty}(r1: u64, r2: u64, r3: u64) {{
    let a: {ty} = opaque_id_u64(r1, 1) as {ty};
    let b: {ty} = opaque_id_u64(r2, 1) as {ty};
    let c: {ty} = opaque_id_u64(r3, 1) as {ty};
    let x1: {ty} = a.saturating_add(b);
    let x2: {ty} = a.saturating_sub(b);
    let x3: {ty} = a.saturating_mul(b);
    let x4: {ty} = chain_{ty}(a, b, c, a);
    print_u64(x1 as u64);
    print(" ");
    print_u64(x2 as u64);
    print(" ");
    print_u64(x3 as u64);
    print(" ");
    print_u64(x4 as u64);
    print("\\n");
}}

fn run_{ty}() {{
    let vals: [{n}]{ty} = [{arr_lits}];
    let mut i: usize = 0;
    while i < {n} {{
        let a: {ty} = vals[i];
        let b: {ty} = vals[({n} - 1) - i];
        let c: {ty} = vals[(i * 3 + 1) % {n}];
        let d: {ty} = vals[(i * 5 + 2) % {n}];
        let ch: {ty} = chain_{ty}(a, b, c, d);
        print("U_{ty} ");
        print_u64(ch as u64);
        print(" ");
        let p1: u64 = {dpat1}u64 | ((a as u64) & {low_mask}u64);
        let p2: u64 = {dpat2}u64 | ((b as u64) & {low_mask}u64);
        let p3: u64 = {dpat3}u64 | ((c as u64) & {low_mask}u64);
        dirty_{ty}(p1, p2, p3);
        i = i + 1;
    }}
}}
""".lstrip())

        for i in range(n):
            a = vals[i]
            b = vals[(n - 1) - i]
            c = vals[(i * 3 + 1) % n]
            d = vals[(i * 5 + 2) % n]
            s1 = sat_mul(sat_sub(sat_add(a, b, lo, hi), c, lo, hi), d, lo, hi)
            s2 = sat_sub(sat_add(sat_mul(a, b, lo, hi), c, lo, hi), d, lo, hi)
            ch = sat_add(s1, s2, lo, hi)

            x1 = sat_add(a, b, lo, hi)
            x2 = sat_sub(a, b, lo, hi)
            x3 = sat_mul(a, b, lo, hi)
            ds1 = sat_mul(sat_sub(sat_add(a, b, lo, hi), c, lo, hi), a, lo, hi)
            ds2 = sat_sub(sat_add(sat_mul(a, b, lo, hi), c, lo, hi), a, lo, hi)
            x4 = sat_add(ds1, ds2, lo, hi)
            expected.append(f"U_{ty} {ch} {x1} {x2} {x3} {x4}")

    # Generate helpers and test functions per signed type
    for ty, bits in SIGNED_TYPES:
        lo, hi = signed_bounds(bits)
        vals = signed_test_vals(bits)
        n = len(vals)
        arr_lits = ", ".join(fmt_lit(ty, bits, True, v) for v in vals)
        low_mask = (1 << bits) - 1
        high_mask = ((1 << 64) - 1) ^ low_mask
        dpat1 = 0xFFFFFFFFFFFFFFFF & high_mask
        dpat2 = 0x5555AAAA5555AAAA & high_mask
        dpat3 = 0x8000000080008000 & high_mask
        min_lit = fmt_lit(ty, bits, True, lo)
        max_lit = fmt_lit(ty, bits, True, hi)
        neg1_lit = fmt_lit(ty, bits, True, -1)
        zero_lit = fmt_lit(ty, bits, True, 0)

        lines.append(f"""
fn chain_{ty}(a: {ty}, b: {ty}, c: {ty}, d: {ty}) -> {ty} {{
    let s1: {ty} = a.saturating_add(b).saturating_sub(c).saturating_mul(d);
    let s2: {ty} = a.saturating_mul(b).saturating_add(c).saturating_sub(d);
    s1.saturating_sub(s2)
}}

fn dirty_{ty}(r1: u64, r2: u64, r3: u64) {{
    let a: {ty} = opaque_id_u64(r1, 1) as {ty};
    let b: {ty} = opaque_id_u64(r2, 1) as {ty};
    let c: {ty} = opaque_id_u64(r3, 1) as {ty};
    let x1: {ty} = a.saturating_add(b);
    let x2: {ty} = a.saturating_sub(b);
    let x3: {ty} = a.saturating_mul(b);
    let x4: {ty} = chain_{ty}(a, b, c, b);
    print_i64(x1 as i64);
    print(" ");
    print_i64(x2 as i64);
    print(" ");
    print_i64(x3 as i64);
    print(" ");
    print_i64(x4 as i64);
    print("\\n");
}}

fn run_{ty}() {{
    let vmin: {ty} = opaque_id_u64({min_lit} as u64, 1) as {ty};
    let vmax: {ty} = opaque_id_u64({max_lit} as u64, 1) as {ty};
    let vneg1: {ty} = opaque_id_u64({neg1_lit} as u64, 1) as {ty};
    let vzero: {ty} = opaque_id_u64({zero_lit} as u64, 1) as {ty};
    print("S_EDGE_{ty} ");
    print_i64(vmin.saturating_mul(vneg1) as i64);
    print(" ");
    print_i64(vneg1.saturating_mul(vmin) as i64);
    print(" ");
    print_i64(vmin.saturating_mul(vmin) as i64);
    print(" ");
    print_i64(vmax.saturating_mul(vmax) as i64);
    print(" ");
    print_i64(vzero.saturating_mul(vmin) as i64);
    print(" ");
    print_i64(vmin.saturating_mul(vzero) as i64);
    print(" ");
    print_i64(vzero.saturating_sub(vmin) as i64);
    print(" ");
    print_i64(vmin.saturating_sub(vmax) as i64);
    print(" ");
    print_i64(vmax.saturating_sub(vmin) as i64);
    print("\\n");

    let vals: [{n}]{ty} = [{arr_lits}];
    let mut i: usize = 0;
    while i < {n} {{
        let a: {ty} = vals[i];
        let b: {ty} = vals[({n} - 1) - i];
        let c: {ty} = vals[(i * 4 + 1) % {n}];
        let d: {ty} = vals[(i * 7 + 3) % {n}];
        let ch: {ty} = chain_{ty}(a, b, c, d);
        print("S_{ty} ");
        print_i64(ch as i64);
        print(" ");
        let p1: u64 = {dpat1}u64 | ((a as u64) & {low_mask}u64);
        let p2: u64 = {dpat2}u64 | ((b as u64) & {low_mask}u64);
        let p3: u64 = {dpat3}u64 | ((c as u64) & {low_mask}u64);
        dirty_{ty}(p1, p2, p3);
        i = i + 1;
    }}
}}
""".lstrip())

        e1 = sat_mul(lo, -1, lo, hi)
        e2 = sat_mul(-1, lo, lo, hi)
        e3 = sat_mul(lo, lo, lo, hi)
        e4 = sat_mul(hi, hi, lo, hi)
        e5 = sat_mul(0, lo, lo, hi)
        e6 = sat_mul(lo, 0, lo, hi)
        e7 = sat_sub(0, lo, lo, hi)
        e8 = sat_sub(lo, hi, lo, hi)
        e9 = sat_sub(hi, lo, lo, hi)
        expected.append(f"S_EDGE_{ty} {e1} {e2} {e3} {e4} {e5} {e6} {e7} {e8} {e9}")

        for i in range(n):
            a = vals[i]
            b = vals[(n - 1) - i]
            c = vals[(i * 4 + 1) % n]
            d = vals[(i * 7 + 3) % n]
            s1 = sat_mul(sat_sub(sat_add(a, b, lo, hi), c, lo, hi), d, lo, hi)
            s2 = sat_sub(sat_add(sat_mul(a, b, lo, hi), c, lo, hi), d, lo, hi)
            ch = sat_sub(s1, s2, lo, hi)

            x1 = sat_add(a, b, lo, hi)
            x2 = sat_sub(a, b, lo, hi)
            x3 = sat_mul(a, b, lo, hi)
            ds1 = sat_mul(sat_sub(sat_add(a, b, lo, hi), c, lo, hi), b, lo, hi)
            ds2 = sat_sub(sat_add(sat_mul(a, b, lo, hi), c, lo, hi), b, lo, hi)
            x4 = sat_sub(ds1, ds2, lo, hi)
            expected.append(f"S_{ty} {ch} {x1} {x2} {x3} {x4}")

    calls = []
    for ty, _ in UNSIGNED_TYPES:
        calls.append(f"    run_{ty}();")
    for ty, _ in SIGNED_TYPES:
        calls.append(f"    run_{ty}();")

    lines.append("fn main() -> i32 {\n" + "\n".join(calls) + "\n    0\n}\n")
    return "\n".join(lines), "\n".join(expected) + "\n"


def run_checked(cmd, label):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        sys.stderr.write(f"FAIL [{label}] exit={res.returncode}\n")
        sys.stderr.write(res.stderr.decode("utf-8", "replace"))
        sys.exit(1)
    return res.stdout.decode("utf-8", "replace").replace("\r\n", "\n")


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: qa_t481_saturating_bounds_oracle.py <compiler> [tmpdir]\n")
        sys.exit(2)
    compiler = os.path.abspath(sys.argv[1])
    src_text, expected_out = generate_program_and_expected()
    exe_ext = ".exe" if os.name == "nt" else ""

    with tempfile.TemporaryDirectory(prefix="qa_t481_sat_") as tmpd:
        tmp_path = Path(tmpd)
        ax_file = tmp_path / "qa_sat_bounds.ax"
        ax_file.write_bytes(src_text.encode("utf-8"))

        out_interp = run_checked([compiler, "run", str(ax_file)], "interp")
        if out_interp != expected_out:
            sys.stderr.write("FAIL [interp] mismatch against SPEC-40 oracle\n")
            sys.exit(1)

        exe_o0 = tmp_path / ("qa_sat_o0" + exe_ext)
        run_checked([compiler, "build", "-O0", "-o", str(exe_o0), str(ax_file)], "build-O0")
        out_o0 = run_checked([str(exe_o0)], "run-O0")
        if out_o0 != expected_out:
            sys.stderr.write("FAIL [native-O0] mismatch against SPEC-40 oracle\n")
            for idx, (gl, el) in enumerate(zip(out_o0.splitlines(), expected_out.splitlines())):
                if gl != el:
                    sys.stderr.write(f"first diff at line {idx + 1}:\n  got: {gl}\n  exp: {el}\n")
                    break
            sys.exit(1)

        exe_o1 = tmp_path / ("qa_sat_o1" + exe_ext)
        run_checked([compiler, "build", "-O1", "-o", str(exe_o1), str(ax_file)], "build-O1")
        out_o1 = run_checked([str(exe_o1)], "run-O1")
        if out_o1 != expected_out:
            sys.stderr.write("FAIL [native-O1] mismatch against SPEC-40 oracle\n")
            for idx, (gl, el) in enumerate(zip(out_o1.splitlines(), expected_out.splitlines())):
                if gl != el:
                    sys.stderr.write(f"first diff at line {idx + 1}:\n  got: {gl}\n  exp: {el}\n")
                    break
            sys.exit(1)

    lines_cnt = len(expected_out.splitlines())
    print(f"QA-T481-SATURATING-BOUNDS PASS widths=10 lines={lines_cnt} modes=interp,native-O0,native-O1")


if __name__ == "__main__":
    main()
