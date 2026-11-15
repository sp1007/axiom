#!/usr/bin/env python3
"""QA adversarial boundary oracle for T431:

1. Custom `--std-root` prelude identifier boundary & `--dep-file` probe invariant:
   A custom `<std>/core/prelude.ax` containing near-miss identifiers (`Polling`, `PollState`,
   `MyPoll`, `poll`, `POLL`) must NOT match `pipe_sv_contains_ident(..., "Poll", 4, false)`
   and therefore must NOT auto-load `<std>/future/{mod,block_on}.ax`, while `--dep-file`
   still records `future/mod.ax` and `future/block_on.ax` as probed paths.
2. Multi-hop transitive `<std>` reachability (`MIR_OP_CONST` fixed-point worklist):
   When a custom `<std>/core/prelude.ax` defines a 3-hop chain `std_hop1 -> std_hop2 -> std_hop3`
   plus an unreferenced `std_dead_printer` (calling `print`), compiling a user `--emit=obj` module
   that calls `std_hop1()` must emit `std_hop1`, `std_hop2`, and `std_hop3` while omitting
   `std_dead_printer` and `__ax_host_print`.
3. COFF binary layout & relocation invariants of `build --rt-obj`:
   Inspect raw COFF header, section headers, symbol table, and relocations of `axiom_rt.obj`:
   - `.data` has size >= 4 and global `_tls_index` at offset 0;
   - `.tls$AAA` has local `_tls_start` at offset 0;
   - `.tls$ZZZ` has size 8 and local `_tls_end` at offset 8;
   - `.rdata` has size 48, local `__xl_a` at offset 0, global `_tls_used` at offset 8 (40 bytes)
     with `Characteristics == 0x00400000` at `.rdata+44`, and 4 `IMAGE_REL_AMD64_ADDR64` (type 1)
     relocations at `.rdata` offsets 8, 16, 24, 32 targeting `_tls_start`, `_tls_end`,
     `_tls_index`, `__xl_a`.
4. Multi-variable `@thread_local` cross-module separate compilation + GNU `ld` execution:
   Two separately compiled `.obj` units (`tls_lib.obj` and `tls_main.obj`) with distinct
   `@thread_local` statics linked together against `axiom_rt.obj` via `gcc -nostdlib`
   maintain independent non-overlapping TLS slots at runtime.
"""

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> int:
    sys.stderr.write(f"FAIL: {msg}\n")
    return 1


def parse_coff_sections_and_relocs(data: bytes):
    if len(data) < 20:
        raise ValueError("COFF too small")
    machine, num_sections, _, symtab_off, num_syms, opt_hdr_size, _ = struct.unpack_from("<HHIIIHH", data, 0)
    if machine != 0x8664:
        raise ValueError(f"unexpected COFF machine: 0x{machine:04x}")

    strtab_off = symtab_off + num_syms * 18

    def read_strtab(off: int) -> str:
        end = data.index(b"\x00", strtab_off + off)
        return data[strtab_off + off : end].decode("ascii", errors="replace")

    def decode_name(raw8: bytes) -> str:
        if raw8[:4] == b"\x00\x00\x00\x00":
            soff = struct.unpack_from("<I", raw8, 4)[0]
            return read_strtab(soff)
        return raw8.split(b"\x00", 1)[0].decode("ascii", errors="replace")

    syms = {}
    idx = 0
    while idx < num_syms:
        off = symtab_off + idx * 18
        raw_name = data[off : off + 8]
        val, sec_num, sym_type, storage_class, num_aux = struct.unpack_from("<IhHBB", data, off + 8)
        syms[idx] = {
            "name": decode_name(raw_name),
            "value": val,
            "sec_num": sec_num,
            "type": sym_type,
            "storage_class": storage_class,
        }
        idx += 1 + num_aux

    sections = {}
    sec_hdr_base = 20 + opt_hdr_size
    for sidx in range(num_sections):
        soff = sec_hdr_base + sidx * 40
        raw_name = data[soff : soff + 8]
        vsize, vaddr, raw_size, raw_ptr, reloc_ptr, _, num_relocs, _, chars = struct.unpack_from(
            "<IIIIIIHHI", data, soff + 8
        )
        sname = decode_name(raw_name)
        relocs = []
        for r_i in range(num_relocs):
            roff = reloc_ptr + r_i * 10
            r_va, r_sym, r_type = struct.unpack_from("<IIH", data, roff)
            relocs.append((r_va, syms[r_sym]["name"], r_type))
        sections[sname] = {
            "sec_num": sidx + 1,
            "raw_size": raw_size,
            "raw_data": data[raw_ptr : raw_ptr + raw_size],
            "relocs": relocs,
            "chars": chars,
        }
    return sections, syms


def main() -> int:
    if len(sys.argv) < 4:
        sys.stderr.write("usage: qa_t431_tls_and_std_reachability_bounds_oracle.py <compiler> <tmp_dir> <repo_root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    gcc = shutil.which("gcc")
    objdump = shutil.which("objdump")
    if not gcc or not objdump:
        return fail("missing gcc or objdump")

    # 1 & 2. Custom `--std-root` with near-miss `Poll*` identifiers AND 3-hop `<std>` call chain + dead printer
    custom_std = tmp_dir / "custom_std"
    if custom_std.exists():
        shutil.rmtree(custom_std)
    shutil.copytree(std_root / "core", custom_std / "core")
    shutil.copytree(std_root / "future", custom_std / "future")

    (custom_std / "core" / "prelude.ax").write_text(
        "module std.core.prelude\n"
        "pub use std.core.option.Option;\n"
        "pub use std.core.result.Result;\n"
        "// Near-miss identifiers that must NOT trigger std.future auto-loading:\n"
        "pub struct Polling { pub v: i32 }\n"
        "pub struct PollState { pub v: i32 }\n"
        "pub struct MyPoll { pub v: i32 }\n"
        "pub fn poll() -> i32 { 1 }\n"
        "pub const POLL: i32 = 2;\n"
        "pub fn std_hop3() -> i32 { 35 }\n"
        "pub fn std_hop2() -> i32 { std_hop3() + 5 }\n"
        "pub fn std_hop1() -> i32 { std_hop2() + 2 }\n"
        "pub fn std_dead_printer() {\n"
        "    print(\"dead-std-helper\\n\");\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )

    hop_ax = tmp_dir / "hop_user.ax"
    hop_ax.write_text(
        "module hop_user\n"
        "pub fn compute_answer() -> i32 {\n"
        "    let p = Polling { v: poll() + POLL };\n"
        "    if p.v == 3 { std_hop1() } else { 0 }\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    hop_obj = tmp_dir / "hop_user.obj"
    hop_dep = tmp_dir / "hop_user.d"
    r = subprocess.run(
        [
            compiler,
            "build",
            "--std-root",
            str(custom_std),
            "--emit=obj",
            "--dep-file",
            str(hop_dep),
            "-o",
            str(hop_obj),
            str(hop_ax),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0 or not hop_obj.is_file():
        return fail(f"hop_user.ax build failed (rc={r.returncode}): {r.stderr}")

    dep_txt = hop_dep.read_text(encoding="utf-8").replace("\\", "/")
    if "future/mod.ax" not in dep_txt or "future/block_on.ax" not in dep_txt:
        return fail(f"--dep-file missing probed future files:\n{dep_txt}")

    hop_syms = subprocess.check_output([objdump, "-t", str(hop_obj)], text=True, timeout=20)
    for req_fn in ("compute_answer", "poll", "std_hop1", "std_hop2", "std_hop3"):
        if req_fn not in hop_syms:
            return fail(f"hop_user.obj missing reachable symbol {req_fn!r}:\n{hop_syms}")
    for dead_sym in ("std_dead_printer", "__ax_host_print", "trace_poll", "block_on"):
        if dead_sym in hop_syms:
            return fail(f"hop_user.obj unexpectedly emitted dead symbol {dead_sym!r}:\n{hop_syms}")

    # 3. Inspect raw COFF binary layout and relocations of `axiom_rt.obj`
    rt_obj = tmp_dir / "axiom_rt.obj"
    r = subprocess.run([compiler, "build", "--rt-obj", str(rt_obj)], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not rt_obj.is_file():
        return fail(f"--rt-obj failed (rc={r.returncode}): {r.stderr}")

    sections, syms = parse_coff_sections_and_relocs(rt_obj.read_bytes())
    for req_sec in (".data", ".tls$AAA", ".tls$ZZZ", ".rdata"):
        if req_sec not in sections:
            return fail(f"axiom_rt.obj missing section {req_sec!r}: {list(sections.keys())}")

    if sections[".data"]["raw_size"] < 4:
        return fail(f".data too small: {sections['.data']['raw_size']}")
    if sections[".tls$ZZZ"]["raw_size"] != 8:
        return fail(f".tls$ZZZ expected size 8, got {sections['.tls$ZZZ']['raw_size']}")
    if sections[".rdata"]["raw_size"] != 48:
        return fail(f".rdata expected size 48, got {sections['.rdata']['raw_size']}")

    rdata_bytes = sections[".rdata"]["raw_data"]
    tls_chars = struct.unpack_from("<I", rdata_bytes, 8 + 36)[0]
    if tls_chars != 0x00400000:
        return fail(f"_tls_used Characteristics expected 0x00400000, got 0x{tls_chars:08x}")

    expected_relocs = [
        (8, "_tls_start", 1),
        (16, "_tls_end", 1),
        (24, "_tls_index", 1),
        (32, "__xl_a", 1),
    ]
    if sections[".rdata"]["relocs"] != expected_relocs:
        return fail(
            f".rdata relocs mismatch:\n  expected: {expected_relocs}\n  actual:   {sections['.rdata']['relocs']}"
        )

    # 4. Two separately compiled `.obj` modules with multiple `@thread_local` statics cross-linked via GNU ld
    tls_a_ax = tmp_dir / "tls_a.ax"
    tls_a_ax.write_text(
        "module tls_a\n\n"
        "@thread_local\n"
        "static mut TLS_A1: i64 = 100i64;\n\n"
        "@thread_local\n"
        "static mut TLS_A2: i64 = 200i64;\n\n"
        "@export\n"
        "pub fn step_a(delta: i64) -> i64 {\n"
        "    unsafe {\n"
        "        TLS_A1 = TLS_A1 + delta;\n"
        "        TLS_A2 = TLS_A2 + (delta * 2i64);\n"
        "        TLS_A1 + TLS_A2\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    tls_b_ax = tmp_dir / "tls_b.ax"
    tls_b_ax.write_text(
        "module tls_b\n\n"
        "extern \"C\" {\n"
        "    fn step_a(delta: i64) -> i64;\n"
        "}\n\n"
        "@thread_local\n"
        "static mut TLS_B1: i64 = 7i64;\n\n"
        "pub fn main() -> i32 {\n"
        "    let a_sum = unsafe { step_a(5i64) };\n"
        "    let b_val = unsafe {\n"
        "        TLS_B1 = TLS_B1 * 3i64;\n"
        "        TLS_B1\n"
        "    };\n"
        "    let total = a_sum + b_val;\n"
        "    print_int(total);\n"
        "    print(\"\\n\");\n"
        "    if total == 336i64 { 0 } else { 1 }\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    tls_a_obj = tmp_dir / "tls_a.obj"
    tls_b_obj = tmp_dir / "tls_b.obj"
    tls_ab_exe = tmp_dir / "tls_ab.exe"
    for src, obj in ((tls_a_ax, tls_a_obj), (tls_b_ax, tls_b_obj)):
        r = subprocess.run(
            [compiler, "build", "--std-root", str(std_root), "--emit=obj", "-o", str(obj), str(src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0 or not obj.is_file():
            return fail(f"{src.name} --emit=obj failed: {r.stderr}")

    r_link = subprocess.run(
        [
            gcc,
            "-nostdlib",
            "-Wl,-e,axiom_start",
            str(tls_a_obj),
            str(tls_b_obj),
            str(rt_obj),
            "-lkernel32",
            "-o",
            str(tls_ab_exe),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r_link.returncode != 0:
        return fail(f"multi-obj TLS link failed: {r_link.stderr}")

    r_run = subprocess.run([str(tls_ab_exe)], capture_output=True, text=True, timeout=20)
    if r_run.returncode != 0 or r_run.stdout.replace("\r\n", "\n") != "336\n":
        return fail(f"tls_ab.exe failed: rc={r_run.returncode}, stdout={r_run.stdout!r}")

    sys.stdout.buffer.write(b"QA-T431-TLS-AND-STD-REACHABILITY-BOUNDS-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
