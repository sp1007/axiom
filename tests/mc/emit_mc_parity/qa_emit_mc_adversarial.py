#!/usr/bin/env python3
"""QA T453b adversarial parity test: `inspect --emit=mc` vs `build --emit=obj` `.text` bytes.

Usage (exec manifest): qa_emit_mc_adversarial.py <compiler> <root> <tmp>

Covers instruction forms beyond emit_mc_parity.py:
  - TLS (`@thread_local static mut` -> X64_MI_TLS_ADDR 26-byte Win64 sequence with zeroed relocs)
  - Direct call (e8 00 00 00 00 zeroed reloc) and indirect function-pointer call (call reg)
  - `assert(...)` (X64_MI_ASSERT je + inline x64_emit_panic_sequence with zeroed relocs)
  - Signed 1/2/4/8-byte loads/stores (i8/i16/i32/i64), mul/div/rem, shifts, multi-branch match
  - Global static LEA (RIP-relative zeroed reloc), extern "C" call, 6-arg Win64 stack call, u64 div/rem
At both -O0 and -O1.
"""

import os
import struct
import subprocess
import sys


CASES = [
    (
        "tls_calls_assert",
        """\
@intrinsic fn assert(c: bool) {}

@thread_local
static mut TLS_ACC: i64 = 0i64;

fn helper_inc(x: i64) -> i64 {
    x + 1i64
}

fn tls_add(delta: i64) -> i64 {
    unsafe {
        TLS_ACC = TLS_ACC + delta
        TLS_ACC
    }
}

fn call_direct(x: i64) -> i64 {
    helper_inc(x) + helper_inc(x + 2i64)
}

fn call_indirect(f: fn(i64) -> i64, x: i64) -> i64 {
    f(x)
}

fn assert_pos(x: i64) -> i64 {
    assert(x > 0i64)
    x * 2i64
}

fn main() -> i32 {
    let a = tls_add(5i64)
    let b = call_direct(a)
    let c = call_indirect(helper_inc, b)
    let d = assert_pos(c)
    d as i32
}
""",
        ["helper_inc", "tls_add", "call_direct", "call_indirect", "assert_pos", "main"],
    ),
    (
        "signed_widths_div_match",
        """\
fn signed_rw_1(p: *mut i8, v: i8) -> i8 {
    unsafe {
        *p = v
        *p
    }
}

fn signed_rw_2(p: *mut i16, v: i16) -> i16 {
    unsafe {
        *p = v
        *p
    }
}

fn signed_rw_4(p: *mut i32, v: i32) -> i32 {
    unsafe {
        *p = v
        *p
    }
}

fn signed_rw_8(p: *mut i64, v: i64) -> i64 {
    unsafe {
        *p = v
        *p
    }
}

fn div_rem_shift(a: i64, b: i64, k: u32) -> i64 {
    let q = a / b
    let r = a % b
    let m = q * 3i64
    let s1 = (m << k) ^ (r >> k)
    ~s1
}

fn multi_match(x: i32) -> i32 {
    match x {
        0 => 10,
        1 => 20,
        2 => 30,
        3 => 40,
        4 => 50,
        _ => x + 100,
    }
}

fn main() -> i32 {
    let p1 = 0x2000usize as *mut i8
    let p2 = 0x2002usize as *mut i16
    let p4 = 0x2004usize as *mut i32
    let p8 = 0x2008usize as *mut i64
    let r1 = signed_rw_1(p1, -3i8) as i32
    let r2 = signed_rw_2(p2, -5i16) as i32
    let r4 = signed_rw_4(p4, -7i32)
    let r8 = signed_rw_8(p8, -9i64) as i32
    let d = div_rem_shift(100i64, 7i64, 2u32) as i32
    let m = multi_match(3i32)
    r1 + r2 + r4 + r8 + d + m
}
""",
        ["signed_rw_1", "signed_rw_2", "signed_rw_4", "signed_rw_8", "div_rem_shift", "multi_match", "main"],
    ),
    (
        "globals_extern_6args",
        """\
extern "C" {
    fn ext_combine(a: i64, b: i64) -> i64;
}

const GLOBAL_TABLE: [4]i64 = [10i64, 20i64, 30i64, 40i64];

fn touch_global(idx: usize) -> i64 {
    GLOBAL_TABLE[idx]
}

fn call_extern_fn(a: i64, b: i64) -> i64 {
    unsafe { ext_combine(a, b) }
}

fn sum6(a: i64, b: i64, c: i64, d: i64, e: i64, f: i64) -> i64 {
    (a + b) + (c + d) + (e + f)
}

fn u64_div_rem_loop(mut n: u64, d: u64) -> u64 {
    let mut acc: u64 = 0u64
    while n > 0u64 {
        acc = acc + (n / d) + (n % d)
        if acc > 1000u64 {
            break
        }
        n = n >> 1u32
    }
    acc
}

fn main() -> i32 {
    let g = touch_global(2usize)
    let e = call_extern_fn(g, 2i64)
    let s = sum6(1i64, 2i64, 3i64, 4i64, 5i64, e)
    let u = u64_div_rem_loop(100u64, 7u64) as i64
    (s + u) as i32
}
""",
        ["touch_global", "call_extern_fn", "sum6", "u64_div_rem_loop", "main"],
    ),
]


def parse_coff_text_symbols(obj_bytes):
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
    return [bytes(int(tok, 16) for tok in ln.split()) for ln in lines]


def hex_str(b):
    return " ".join(f"{x:02x}" for x in b)


def check_case(compiler, root, tmp, case_name, src, fn_names, opt_flag):
    tag = f"{case_name}_{opt_flag or 'O0'}"
    src_path = os.path.join(tmp, f"{tag}.ax")
    obj_path = os.path.join(tmp, f"{tag}.obj")
    with open(src_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    opt_args = [opt_flag] if opt_flag else []

    mc_cmd = [compiler, "inspect", "--emit=mc"] + opt_args + [src_path]
    mc_res = subprocess.run(mc_cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if mc_res.returncode != 0:
        sys.stderr.write(f"FAIL [{tag}]: inspect --emit=mc exited {mc_res.returncode}:\n{mc_res.stderr.decode('utf-8', 'replace')}\n")
        return None

    obj_cmd = [compiler, "build", "--emit=obj", "--std-root", "std"] + opt_args + ["-o", obj_path, src_path]
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

    sym_by_name = {name: val for name, val in syms}
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
        sys.stderr.write("usage: qa_emit_mc_adversarial.py <compiler> <root> <tmp>\n")
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

            if opt_flag == "" and case_name == "tls_calls_assert":
                tls_seq = b"\x65\x48\x8b\x04\x25\x58\x00\x00\x00"
                if tls_seq not in res["tls_add"]:
                    sys.stderr.write(f"FAIL [tls_calls_assert]: tls_add missing GS:[0x58] TLS sequence: {hex_str(res['tls_add'])}\n")
                    return 1
                if b"\xe8\x00\x00\x00\x00" not in res["call_direct"]:
                    sys.stderr.write(f"FAIL [tls_calls_assert]: call_direct missing zeroed e8 reloc: {hex_str(res['call_direct'])}\n")
                    return 1
                ci = res["call_indirect"]
                if not any(ci[i] == 0xFF and (ci[i + 1] & 0xF8) == 0xD0 for i in range(len(ci) - 1)):
                    sys.stderr.write(f"FAIL [tls_calls_assert]: call_indirect missing indirect call (ff d0..d7): {hex_str(ci)}\n")
                    return 1
                if b"\xe8\x00\x00\x00\x00" not in res["assert_pos"]:
                    sys.stderr.write(f"FAIL [tls_calls_assert]: assert_pos missing zeroed panic call reloc: {hex_str(res['assert_pos'])}\n")
                    return 1
            if opt_flag == "" and case_name == "signed_widths_div_match":
                if b"\x88" not in res["signed_rw_1"]:
                    sys.stderr.write(f"FAIL [signed_widths_div_match]: signed_rw_1 missing 8-bit MOV (88): {hex_str(res['signed_rw_1'])}\n")
                    return 1
                if b"\x66\x89" not in res["signed_rw_2"]:
                    sys.stderr.write(f"FAIL [signed_widths_div_match]: signed_rw_2 missing 16-bit MOV (66 89): {hex_str(res['signed_rw_2'])}\n")
                    return 1
                if b"\xf7" not in res["div_rem_shift"]:
                    sys.stderr.write(f"FAIL [signed_widths_div_match]: div_rem_shift missing IDIV/NOT (f7): {hex_str(res['div_rem_shift'])}\n")
                    return 1
            if opt_flag == "" and case_name == "globals_extern_6args":
                # RIP-relative LEA with zeroed disp32 reloc: 48 8d <modrm> 00 00 00 00
                if b"\x48\x8d" not in res["touch_global"] or b"\x00\x00\x00\x00" not in res["touch_global"]:
                    sys.stderr.write(f"FAIL [globals_extern_6args]: touch_global missing RIP-rel LEA: {hex_str(res['touch_global'])}\n")
                    return 1
                if b"\xe8\x00\x00\x00\x00" not in res["call_extern_fn"]:
                    sys.stderr.write(f"FAIL [globals_extern_6args]: call_extern_fn missing zeroed extern call reloc: {hex_str(res['call_extern_fn'])}\n")
                    return 1

    print(f"QA-EMIT-MC-ADVERSARIAL PASS {total_funcs} functions ({total_cases} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
