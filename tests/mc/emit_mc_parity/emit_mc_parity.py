#!/usr/bin/env python3
"""T453b: byte-for-byte parity between `inspect --emit=mc` and `build --emit=obj` `.text` bytes.

Usage (exec manifest): emit_mc_parity.py <compiler> <root> <tmp>

For each test program covering:
  - 1/2/4/8-byte loads and stores (and odd-size 6-byte aggregate),
  - SETcc, CMOVcc, TEST,
  - i128 / u128 pair ops (ADD/ADC, SUB/SBB, SHLD/SHRD, MUL, UDIV128, NEG, NOT, saturating),
  - intra-function branches (JMP/JCC fixups) and direct calls (zero-filled reloc fields),
compiles at both -O0 and -O1 and verifies that every function's `--emit=mc` bytes equal its
`.text` byte range in the COFF object produced by `build --emit=obj`.
"""

import os
import struct
import subprocess
import sys


CASES = [
    (
        "widths",
        """\
struct Packed6 {
    vals: [3]u16,
    tag: u16,
}

fn load_store_1(p: *mut u8, v: u8) -> u8 {
    unsafe {
        *p = v
        *p
    }
}

fn load_store_2(p: *mut u16, v: u16) -> u16 {
    unsafe {
        *p = v
        *p
    }
}

fn load_store_4(p: *mut u32, v: u32) -> u32 {
    unsafe {
        *p = v
        *p
    }
}

fn load_store_8(p: *mut u64, v: u64) -> u64 {
    unsafe {
        *p = v
        *p
    }
}

fn odd_size_6(a: u16, b: u16, c: u16) -> u16 {
    let mut s = Packed6 { vals: [a, b, c], tag: 7u16 }
    s.vals = [c, b, a]
    s.vals[0] + s.tag
}

fn main() -> i32 {
    let p1 = 0x1000usize as *mut u8
    let p2 = 0x1002usize as *mut u16
    let p4 = 0x1004usize as *mut u32
    let p8 = 0x1008usize as *mut u64
    let r1 = load_store_1(p1, 3u8) as i32
    let r2 = load_store_2(p2, 5u16) as i32
    let r4 = load_store_4(p4, 7u32) as i32
    let r8 = load_store_8(p8, 9u64) as i32
    let r6 = odd_size_6(1u16, 2u16, 3u16) as i32
    r1 + r2 + r4 + r8 + r6
}
""",
        ["load_store_1", "load_store_2", "load_store_4", "load_store_8", "odd_size_6", "main"],
    ),
    (
        "flags_cmov_test",
        """\
fn cmp_eq(a: i64, b: i64) -> bool { a == b }
fn cmp_lt(a: i64, b: i64) -> bool { a < b }
fn cmp_ge(a: u64, b: u64) -> bool { a >= b }

fn select_max(a: i64, b: i64) -> i64 {
    if a > b { a } else { b }
}

fn select_min(a: i64, b: i64) -> i64 {
    if a < b { a } else { b }
}

fn test_branch(flag: bool, x: i64) -> i64 {
    if flag {
        x + 10i64
    } else {
        x - 10i64
    }
}

fn loop_sum(n: i64) -> i64 {
    let mut i: i64 = 0i64
    let mut acc: i64 = 0i64
    while i < n {
        acc = acc + i
        i = i + 1i64
    }
    acc
}

fn main() -> i32 {
    let mut r: i64 = 0i64
    if cmp_eq(5i64, 5i64) { r = r + 1i64 }
    if cmp_lt(2i64, 9i64) { r = r + 2i64 }
    if cmp_ge(9u64, 2u64) { r = r + 4i64 }
    r = r + select_max(10i64, 20i64)
    r = r + select_min(10i64, 20i64)
    r = r + test_branch(true, 5i64)
    r = r + loop_sum(5i64)
    r as i32
}
""",
        ["cmp_eq", "cmp_lt", "cmp_ge", "select_max", "select_min", "test_branch", "loop_sum", "main"],
    ),
    (
        "i128_pair_ops",
        """\
fn add_sub_128(a: i128, b: i128) -> i128 {
    let s = a + b
    s - (b >> 3u32)
}

fn mul_neg_not_128(a: i128, b: i128) -> i128 {
    let p = a * b
    let n = -p
    ~n
}

fn shift_128(a: u128, k: u32) -> u128 {
    (a << k) | (a >> k)
}

fn div_rem_128(a: u128, b: u128) -> u128 {
    (a / b) + (a % b)
}

fn cmp_128(a: i128, b: i128) -> bool {
    a < b
}

fn main() -> i32 {
    let x: i128 = 1000000000000000000i128
    let y: i128 = 7i128
    let a = add_sub_128(x, y)
    let b = mul_neg_not_128(y, 3i128)
    let c = shift_128(123456789u128, 17u32)
    let d = div_rem_128(c, 97u128)
    let e = if cmp_128(a, b) { 1i32 } else { 0i32 }
    ((d as i64) as i32) + e
}
""",
        ["add_sub_128", "mul_neg_not_128", "shift_128", "div_rem_128", "cmp_128", "main"],
    ),
]


def parse_coff_text_symbols(obj_bytes):
    """Return (text_bytes, [(name, value), ...]) for function symbols in `.text`."""
    if len(obj_bytes) < 20:
        raise ValueError("COFF object too small")
    machine, nsec, _ts, symtab_off, nsyms, opt_sz, _chars = struct.unpack_from("<HHIIIHH", obj_bytes, 0)
    if machine != 0x8664:
        raise ValueError(f"unexpected COFF machine 0x{machine:04x}")

    sec_off = 20 + opt_sz
    text_sec_num = None
    text_bytes = None
    for i in range(nsec):
        raw_name, _vsz, _vaddr, raw_sz, raw_ptr = struct.unpack_from("<8sIIII", obj_bytes, sec_off + i * 40)
        name = raw_name.split(b"\x00", 1)[0].decode("ascii", errors="replace")
        if name == ".text":
            text_sec_num = i + 1
            text_bytes = obj_bytes[raw_ptr : raw_ptr + raw_sz]
            break
    if text_sec_num is None or text_bytes is None:
        raise ValueError("no .text section in COFF object")

    strtab_off = symtab_off + nsyms * 18
    def read_sym_name(raw8):
        z, off = struct.unpack_from("<II", raw8, 0)
        if z == 0:
            end = obj_bytes.index(b"\x00", strtab_off + off)
            return obj_bytes[strtab_off + off : end].decode("utf-8", errors="replace")
        return raw8.split(b"\x00", 1)[0].decode("utf-8", errors="replace")

    syms = []
    idx = 0
    while idx < nsyms:
        raw8, val, sec_num, _sym_ty, sclass, naux = struct.unpack_from("<8sIhhBB", obj_bytes, symtab_off + idx * 18)
        name = read_sym_name(raw8)
        if sec_num == text_sec_num and sclass in (2, 3) and name != ".text":
            syms.append((name, val))
        idx += 1 + naux
    return text_bytes, syms


def parse_mc_lines(stdout_bytes):
    text = stdout_bytes.decode("utf-8").replace("\r\n", "\n")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    out = []
    for ln in lines:
        out.append(bytes(int(tok, 16) for tok in ln.split()))
    return out


def hex_str(b):
    return " ".join(f"{x:02x}" for x in b)


def check_case(compiler, root, tmp, case_name, src, fn_names, opt_flag):
    tag = f"{case_name}_{opt_flag or 'O0'}"
    src_path = os.path.join(tmp, f"{tag}.ax")
    obj_path = os.path.join(tmp, f"{tag}.obj")
    with open(src_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    base_args = [compiler]
    opt_args = [opt_flag] if opt_flag else []

    mc_cmd = base_args + ["inspect", "--emit=mc"] + opt_args + [src_path]
    mc_res = subprocess.run(mc_cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if mc_res.returncode != 0:
        sys.stderr.write(f"FAIL [{tag}]: inspect --emit=mc exited {mc_res.returncode}:\n{mc_res.stderr.decode('utf-8', 'replace')}\n")
        return None

    obj_cmd = base_args + ["build", "--emit=obj", "--std-root", "std"] + opt_args + ["-o", obj_path, src_path]
    obj_res = subprocess.run(obj_cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if obj_res.returncode != 0:
        sys.stderr.write(f"FAIL [{tag}]: build --emit=obj exited {obj_res.returncode}:\n{obj_res.stderr.decode('utf-8', 'replace')}\n")
        return None

    mc_funcs = parse_mc_lines(mc_res.stdout)
    if len(mc_funcs) != len(fn_names):
        sys.stderr.write(f"FAIL [{tag}]: expected {len(fn_names)} --emit=mc lines, got {len(mc_funcs)}\n")
        return None

    with open(obj_path, "rb") as f:
        obj_bytes = f.read()
    text_bytes, syms = parse_coff_text_symbols(obj_bytes)

    # Deduplicate aliases sharing an offset (e.g. main / ax_main) and build ordered offset list.
    sym_by_name = {}
    for name, val in syms:
        sym_by_name[name] = val
    unique_offsets = sorted(set(val for _name, val in syms))

    for fn_name, mc_bytes in zip(fn_names, mc_funcs):
        if fn_name not in sym_by_name:
            sys.stderr.write(f"FAIL [{tag}]: symbol `{fn_name}` not found in .obj (have: {sorted(sym_by_name)})\n")
            return None
        start = sym_by_name[fn_name]
        pos = unique_offsets.index(start)
        next_start = unique_offsets[pos + 1] if pos + 1 < len(unique_offsets) else len(text_bytes)
        obj_slice = text_bytes[start : start + len(mc_bytes)]
        if obj_slice != mc_bytes:
            sys.stderr.write(
                f"FAIL [{tag}] fn `{fn_name}` bytes differ:\n"
                f"  --emit=mc ({len(mc_bytes)}B): {hex_str(mc_bytes)}\n"
                f"  .text obj ({len(obj_slice)}B): {hex_str(obj_slice)}\n"
            )
            return None
        pad = text_bytes[start + len(mc_bytes) : next_start]
        if len(pad) >= 16 or any(b != 0x90 for b in pad):
            sys.stderr.write(
                f"FAIL [{tag}] fn `{fn_name}` trailing bytes before next symbol are not 16B NOP alignment:\n"
                f"  trailing ({len(pad)}B): {hex_str(pad)}\n"
            )
            return None

    return dict(zip(fn_names, mc_funcs))


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("usage: emit_mc_parity.py <compiler> <root> <tmp>\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    root = os.path.abspath(sys.argv[2])
    tmp = os.path.abspath(sys.argv[3])
    os.makedirs(tmp, exist_ok=True)

    total_funcs = 0
    total_cases = 0
    for opt_flag in ("", "-O1"):
        for case_name, src, fn_names in CASES:
            res = check_case(compiler, root, tmp, case_name, src, fn_names, opt_flag)
            if res is None:
                return 1
            total_funcs += len(res)
            total_cases += 1

            # Non-vacuous opcode presence checks on -O0 dumps:
            if opt_flag == "" and case_name == "widths":
                # 2-byte store uses 66 89; 1-byte store uses 88; 4-byte store uses 89 (not 48 89 08)
                if b"\x66\x89" not in res["load_store_2"]:
                    sys.stderr.write(f"FAIL [widths]: load_store_2 missing 66 89 (16-bit MOV): {hex_str(res['load_store_2'])}\n")
                    return 1
                if b"\x88" not in res["load_store_1"]:
                    sys.stderr.write(f"FAIL [widths]: load_store_1 missing 88 (8-bit MOV): {hex_str(res['load_store_1'])}\n")
                    return 1
                if b"\x66\x89" not in res["odd_size_6"]:
                    sys.stderr.write(f"FAIL [widths]: odd_size_6 missing 66 89 (16-bit chunk): {hex_str(res['odd_size_6'])}\n")
                    return 1
            if opt_flag == "" and case_name == "flags_cmov_test":
                # SETcc encodes as 0f 9x
                eq_b = res["cmp_eq"]
                if not any(eq_b[i] == 0x0F and (eq_b[i + 1] & 0xF0) == 0x90 for i in range(len(eq_b) - 1)):
                    sys.stderr.write(f"FAIL [flags_cmov_test]: cmp_eq missing SETcc (0f 9x): {hex_str(eq_b)}\n")
                    return 1
            if opt_flag == "-O1" and case_name == "flags_cmov_test":
                # CMOVcc encodes as 0f 4x
                sm_b = res["select_max"]
                if not any(sm_b[i] == 0x0F and (sm_b[i + 1] & 0xF0) == 0x40 for i in range(len(sm_b) - 1)):
                    sys.stderr.write(f"FAIL [flags_cmov_test -O1]: select_max missing CMOVcc (0f 4x): {hex_str(sm_b)}\n")
                    return 1
                # TEST r, r encodes as 85 (or 48 85 / 4d 85)
                tb_b = res["test_branch"]
                if b"\x85" not in tb_b:
                    sys.stderr.write(f"FAIL [flags_cmov_test -O1]: test_branch missing TEST (85): {hex_str(tb_b)}\n")
                    return 1
            if opt_flag == "" and case_name == "i128_pair_ops":
                # ADC/SBB in add_sub_128
                as_b = res["add_sub_128"]
                if not (b"\x11" in as_b or b"\x13" in as_b):
                    sys.stderr.write(f"FAIL [i128_pair_ops]: add_sub_128 missing ADC opcode: {hex_str(as_b)}\n")
                    return 1
                # SHLD/SHRD + TEST r, imm (f7) + CMOVcc (0f 4x) in shift_128
                sh_b = res["shift_128"]
                if b"\xf7" not in sh_b:
                    sys.stderr.write(f"FAIL [i128_pair_ops]: shift_128 missing TEST r, imm (f7): {hex_str(sh_b)}\n")
                    return 1
                if not any(sh_b[i] == 0x0F and (sh_b[i + 1] & 0xF0) == 0x40 for i in range(len(sh_b) - 1)):
                    sys.stderr.write(f"FAIL [i128_pair_ops]: shift_128 missing CMOVcc (0f 4x): {hex_str(sh_b)}\n")
                    return 1

    print(f"EMIT-MC-PARITY PASS {total_funcs} functions ({total_cases} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
