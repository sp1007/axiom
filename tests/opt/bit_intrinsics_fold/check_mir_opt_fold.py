#!/usr/bin/env python3
"""Verify `inspect --emit=mir-opt -O1` folds every bit intrinsic to ONE constant across widths 8..128."""
import re
import subprocess
import sys


def mask(bits: int) -> int:
    return (1 << bits) - 1


def to_u(val: int, bits: int) -> int:
    return val & mask(bits)


def rotl(val: int, n: int, bits: int) -> int:
    u = to_u(val, bits)
    k = (n & 0xFFFFFFFF) % bits
    return u if k == 0 else ((u << k) | (u >> (bits - k))) & mask(bits)


def rotr(val: int, n: int, bits: int) -> int:
    u = to_u(val, bits)
    k = (n & 0xFFFFFFFF) % bits
    return u if k == 0 else ((u >> k) | (u << (bits - k))) & mask(bits)


def clz(val: int, bits: int) -> int:
    u = to_u(val, bits)
    return bits if u == 0 else bits - u.bit_length()


def ctz(val: int, bits: int) -> int:
    u = to_u(val, bits)
    return bits if u == 0 else (u & -u).bit_length() - 1


def popcnt(val: int, bits: int) -> int:
    return bin(to_u(val, bits)).count("1")


def bswap(val: int, bits: int) -> int:
    u = to_u(val, bits)
    return int.from_bytes(u.to_bytes(bits // 8, "little"), "big")


def bitrev(val: int, bits: int) -> int:
    u = to_u(val, bits)
    return int(format(u, f"0{bits}b")[::-1], 2)


def wneg(val: int, bits: int) -> int:
    return (-to_u(val, bits)) & mask(bits)


def eval_intr(intr: str, val: int, rot_n: int, bits: int) -> int:
    if intr == "rotate_left":
        return rotl(val, rot_n, bits)
    if intr == "rotate_right":
        return rotr(val, rot_n, bits)
    if intr == "leading_zeros":
        return clz(val, bits)
    if intr == "trailing_zeros":
        return ctz(val, bits)
    if intr == "count_ones":
        return popcnt(val, bits)
    if intr == "swap_bytes":
        return bswap(val, bits)
    if intr == "reverse_bits":
        return bitrev(val, bits)
    if intr == "wrapping_neg":
        return wneg(val, bits)
    raise ValueError(intr)


UNSIGNED_TYPES = [
    ("u8", 8, 0xB4, 3),
    ("u16", 16, 0xA35C, 5),
    ("u32", 32, 0x93A5C618, 7),
    ("u64", 64, 0x8123456789ABCDE0, 13),
    ("usize", 64, 0xC0FFEE1234567898, 19),
    ("u128", 128, 0x8102030405060708090A0B0C0D0E0F70, 29),
]

SIGNED_TYPES = [
    ("i8", 8, -0x4C, 3),
    ("i16", 16, -0x5CA4, 5),
    ("i32", 32, -0x6C5A39E8, 7),
    ("i64", 64, -0x123456789ABCDEF0, 13),
    ("isize", 64, -0x0FEDCBA987654320, 19),
    ("i128", 128, -0x112233445566778899AABBCCDDEEFF00, 29),
]

INTRINSICS = [
    "rotate_left",
    "rotate_right",
    "leading_zeros",
    "trailing_zeros",
    "count_ones",
    "swap_bytes",
    "reverse_bits",
    "wrapping_neg",
]


def build_expectations():
    single_bb = []
    for ty, bits, val, rn in UNSIGNED_TYPES + SIGNED_TYPES:
        for intr in INTRINSICS:
            single_bb.append((f"fold_{intr}_{ty}", eval_intr(intr, val, rn, bits)))

    k_chain = 0x0102030405060708090A0B0C0D0E0F10
    single_bb.extend([
        ("fold_edge_clz_zero_u8", clz(0, 8)),
        ("fold_edge_ctz_zero_u8", ctz(0, 8)),
        ("fold_edge_clz_zero_u128", clz(0, 128)),
        ("fold_edge_ctz_zero_u128", ctz(0, 128)),
        ("fold_edge_clz_zero_i128", clz(0, 128)),
        ("fold_edge_ctz_zero_i128", ctz(0, 128)),
        ("fold_edge_pop_zero_u128", 0),
        ("fold_edge_wneg_zero_u8", 0),
        ("fold_edge_wneg_zero_u128", 0),
        ("fold_edge_wneg_zero_i128", 0),
        ("fold_edge_wneg_i8_min", wneg(-(1 << 7), 8)),
        ("fold_edge_wneg_i16_min", wneg(-(1 << 15), 16)),
        ("fold_edge_wneg_i32_min", wneg(-(1 << 31), 32)),
        ("fold_edge_wneg_i64_min", wneg(-(1 << 63), 64)),
        ("fold_edge_wneg_isize_min", wneg(-(1 << 63), 64)),
        ("fold_edge_wneg_i128_min", wneg(-(1 << 127), 128)),
        ("fold_edge_wneg_u8_max", wneg(0xFF, 8)),
        ("fold_edge_wneg_u128_max", wneg((1 << 128) - 1, 128)),
        ("fold_edge_wneg_one_u128", wneg(1, 128)),
        ("fold_edge_wneg_hi_only_u128", wneg(1 << 64, 128)),
        ("fold_edge_clz_i8_min", clz(-(1 << 7), 8)),
        ("fold_edge_ctz_i8_min", ctz(-(1 << 7), 8)),
        ("fold_edge_clz_i128_min", clz(-(1 << 127), 128)),
        ("fold_edge_ctz_i128_min", ctz(-(1 << 127), 128)),
        ("fold_edge_clz_i128_max", clz((1 << 127) - 1, 128)),
        ("fold_edge_pop_i128_max", popcnt((1 << 127) - 1, 128)),
        ("fold_edge_pop_u128_max", popcnt((1 << 128) - 1, 128)),
        ("fold_edge_ctz_bit64_u128", 64),
        ("fold_edge_clz_bit64_u128", 63),
        ("fold_edge_bitrev_one_u128", 1 << 127),
        ("fold_edge_bswap_seq_u128", 0x100F0E0D0C0B0A090807060504030201),
        ("fold_edge_rotl_zero_u64", rotl(0x123456789ABCDEF0, 0, 64)),
        ("fold_edge_rotr_bits_u8", rotr(0xA5, 8, 8)),
        ("fold_edge_rotl_bits_u128", rotl(k_chain, 128, 128)),
        ("fold_edge_rotl_over_u128", rotl(k_chain, 133, 128)),
        ("fold_edge_rotr_u32max_u128", rotr(k_chain, 0xFFFFFFFF, 128)),
        ("fold_direct_rotl_u128", rotl(k_chain, 17, 128)),
        ("fold_direct_bitrev_i64", bitrev(-0x123456789ABCDEF0, 64)),
        ("fold_direct_wneg_i128", wneg(-(1 << 127), 128)),
        ("fold_direct_clz_u8", clz(0x0F, 8)),
        ("fold_direct_ctz_u128", 71),
        ("fold_direct_pop_i128", popcnt(-0x112233445566778899AABBCCDDEEFF00, 128)),
        ("fold_direct_bswap_u128", 0x100F0E0D0C0B0A090807060504030201),
        ("fold_let_and_chain_u128", wneg(rotl(bitrev(bswap(k_chain, 128), 128), 13, 128), 128)),
        ("fold_chain_to_u32", clz(rotr(bswap(k_chain, 128), 9, 128), 128)),
    ])

    neg_expr = [
        ("fold_neg_expr_clz_i32", clz(-5, 32)),
        ("fold_neg_expr_bswap_i16", bswap(-0x1234, 16)),
        ("fold_neg_expr_rotl_i128", rotl(-0x123456789ABCDEF0123456789ABCDEF0, 11, 128)),
    ]
    return single_bb, neg_expr


def parse_mir_functions(ax_src: str, mir_text: str):
    fn_names = re.findall(r"(?m)^fn\s+([A-Za-z0-9_]+)\s*\(", ax_src)
    raw_bodies = mir_text.split("mir_body {")[1:]
    if len(fn_names) != len(raw_bodies):
        raise RuntimeError(
            f"mir_body count mismatch: {len(fn_names)} non-intrinsic fns in source vs {len(raw_bodies)} mir_body blocks"
        )

    bb_re = re.compile(r"^\s*(bb\d+)(?:\s*\(cleanup\))?:\s*\{\s*$")
    funcs = {}
    for fn_name, body_txt in zip(fn_names, raw_bodies):
        cur_bbs = {}
        cur_bb = None
        for raw_line in body_txt.splitlines():
            if cur_bb is None:
                m_bb = bb_re.match(raw_line)
                if m_bb:
                    cur_bb = m_bb.group(1)
                    cur_bbs[cur_bb] = []
            else:
                if raw_line.strip() == "}":
                    cur_bb = None
                else:
                    s = raw_line.strip()
                    if s:
                        cur_bbs[cur_bb].append(s)
        funcs[fn_name] = cur_bbs
    return funcs


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("usage: check_mir_opt_fold.py <compiler> <std_root> <ax_file>\n")
        return 2

    compiler, std_root, ax_file = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(ax_file, "r", encoding="utf-8") as f:
        ax_src = f.read()

    proc = subprocess.run(
        [compiler, "inspect", "--emit=mir-opt", "-O1", "--std-root", std_root, ax_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"inspect --emit=mir-opt -O1 failed (rc={proc.returncode}):\n")
        sys.stderr.write(proc.stderr.decode("utf-8", "replace"))
        return 1

    mir_text = proc.stdout.decode("utf-8", "replace")
    funcs = parse_mir_functions(ax_src, mir_text)
    single_bb, neg_expr = build_expectations()

    errors = []

    for fn_name, exp_val in single_bb:
        if fn_name not in funcs:
            errors.append(f"{fn_name}: missing from mir-opt output")
            continue
        bbs = funcs[fn_name]
        if list(bbs.keys()) != ["bb0"]:
            errors.append(f"{fn_name}: expected only ['bb0'], got {list(bbs.keys())}: {bbs}")
            continue
        lines = bbs["bb0"]
        want = [f"_0 = const {exp_val};", "return;"]
        if lines != want:
            errors.append(f"{fn_name}: expected {want}, got {lines}")

    for fn_name, exp_val in neg_expr:
        if fn_name not in funcs:
            errors.append(f"{fn_name}: missing from mir-opt output")
            continue
        bbs = funcs[fn_name]
        ret_bbs = [lines for lines in bbs.values() if lines and lines[-1] == "return;"]
        want = [f"_0 = const {exp_val};", "return;"]
        if ret_bbs != [want]:
            errors.append(f"{fn_name}: expected return block {want}, got {bbs}")

    for rt_name in ("runtime_unfolded_u128", "runtime_unfolded_rot_count"):
        if rt_name not in funcs:
            errors.append(f"{rt_name}: missing from mir-opt output")
            continue
        bbs = funcs[rt_name]
        bb0 = bbs.get("bb0", [])
        if len(bb0) <= 6 or any(l.startswith("_0 = const ") for l in bb0):
            errors.append(f"{rt_name}: runtime argument was unexpectedly folded: {bb0}")

    if errors:
        for e in errors[:25]:
            sys.stderr.write("FAIL: " + e + "\n")
        if len(errors) > 25:
            sys.stderr.write(f"... and {len(errors) - 25} more errors\n")
        return 1

    sys.stdout.buffer.write(b"OK mir-opt bit_intrinsics_fold\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
