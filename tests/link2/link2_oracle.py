#!/usr/bin/env python3
"""E18.6 Verification Suite: Linker v2 — Separate Compilation, Multiple Objects & Archives
(`spec/SPEC-27-separate-compilation-linker-v2.md`, `REQ-LNK-200`..`REQ-LNK-214`).
"""

import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


class ValidationError(Exception):
    pass


def run_cmd(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
        check=False,
    )


def run_checked(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    res = run_cmd(cmd, cwd=cwd)
    if res.returncode != 0:
        raise ValidationError(
            f"command failed (exit {res.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{res.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{res.stderr.decode('utf-8', errors='replace')}"
        )
    return res


def parse_coff_obj(data: bytes, label: str) -> dict:
    if len(data) < 20:
        raise ValidationError(f"{label}: COFF object too short ({len(data)} bytes)")
    machine, num_sections, timestamp, symtab_off, num_syms, opt_hdr_sz, chars = struct.unpack_from(
        "<HHIIIHH", data, 0
    )
    if machine != 0x8664:
        raise ValidationError(f"{label}: expected Machine=0x8664, got {machine:#06x}")
    if timestamp != 0:
        raise ValidationError(f"{label}: expected TimeDateStamp=0, got {timestamp}")
    if opt_hdr_sz != 0:
        raise ValidationError(f"{label}: expected SizeOfOptionalHeader=0, got {opt_hdr_sz}")

    sections: list[dict] = []
    for i in range(num_sections):
        sh_off = 20 + i * 40
        raw_name = data[sh_off : sh_off + 8]
        vsize, va, raw_sz, raw_ptr, reloc_ptr, lineno_ptr, num_relocs, num_lineno, s_chars = struct.unpack_from(
            "<IIIIIIHHI", data, sh_off + 8
        )
        name = raw_name.rstrip(b"\x00").decode("ascii", errors="replace")
        sec_bytes = data[raw_ptr : raw_ptr + raw_sz] if raw_sz > 0 and raw_ptr > 0 else b""
        sections.append(
            {
                "index": i + 1,
                "name": name,
                "raw_size": raw_sz,
                "raw_ptr": raw_ptr,
                "num_relocs": num_relocs,
                "characteristics": s_chars,
                "data": sec_bytes,
            }
        )

    strtab_off = symtab_off + num_syms * 18
    (strtab_sz,) = struct.unpack_from("<I", data, strtab_off)
    symbols: list[dict] = []
    idx = 0
    while idx < num_syms:
        rec_off = symtab_off + idx * 18
        name_raw = data[rec_off : rec_off + 8]
        val, sec_num, sym_type, scl, aux_cnt = struct.unpack_from("<IhHBB", data, rec_off + 8)
        z0, s_off = struct.unpack("<II", name_raw)
        if z0 == 0:
            end = data.find(b"\x00", strtab_off + s_off, strtab_off + strtab_sz)
            sym_name = data[strtab_off + s_off : end].decode("utf-8", errors="replace")
        else:
            sym_name = name_raw.rstrip(b"\x00").decode("utf-8", errors="replace")
        symbols.append(
            {
                "index": idx,
                "name": sym_name,
                "value": val,
                "section_number": sec_num,
                "sym_type": sym_type,
                "storage_class": scl,
            }
        )
        idx += 1 + aux_cnt

    return {
        "machine": machine,
        "timestamp": timestamp,
        "characteristics": chars,
        "sections": sections,
        "symbols": symbols,
    }


def parse_pe_image(data: bytes, label: str) -> dict:
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValidationError(f"{label}: invalid MZ header")
    (pe_off,) = struct.unpack_from("<I", data, 0x3C)
    if data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValidationError(f"{label}: invalid PE signature")
    machine, num_sections, timestamp, symtab_off, num_syms, opt_hdr_sz, chars = struct.unpack_from(
        "<HHIIIHH", data, pe_off + 4
    )
    if machine != 0x8664:
        raise ValidationError(f"{label}: expected PE Machine=0x8664, got {machine:#06x}")
    if timestamp != 0:
        raise ValidationError(f"{label}: expected PE TimeDateStamp=0, got {timestamp}")

    sec_table_off = pe_off + 24 + opt_hdr_sz
    sections: list[dict] = []
    for i in range(num_sections):
        sh_off = sec_table_off + i * 40
        raw_name = data[sh_off : sh_off + 8]
        vsize, rva, raw_sz, raw_ptr, reloc_ptr, lineno_ptr, num_relocs, num_lineno, s_chars = struct.unpack_from(
            "<IIIIIIHHI", data, sh_off + 8
        )
        name = raw_name.rstrip(b"\x00").decode("ascii", errors="replace")
        sec_data = data[raw_ptr : raw_ptr + raw_sz] if raw_sz > 0 and raw_ptr > 0 else b""
        sections.append(
            {
                "index": i + 1,
                "name": name,
                "virtual_size": vsize,
                "rva": rva,
                "raw_size": raw_sz,
                "raw_ptr": raw_ptr,
                "characteristics": s_chars,
                "data": sec_data,
            }
        )
    return {
        "timestamp": timestamp,
        "sections": sections,
    }


def build_coff_obj(
    machine: int,
    sections: list[tuple[bytes, int, bytes, list[tuple[int, int, int]]]],
    symbols: list[tuple[bytes, int, int, int, int]],
) -> bytes:
    """Builds a minimal deterministic COFF .obj binary from (name, chars, raw_bytes, relocs)
    and (sym_name, value, sec_num, sym_type, storage_class)."""
    num_secs = len(sections)
    num_syms = len(symbols)
    hdr_size = 20 + num_secs * 40
    cur_off = hdr_size
    sec_Meta = []
    for name, chars, raw_bytes, relocs in sections:
        raw_ptr = cur_off if len(raw_bytes) > 0 else 0
        cur_off += len(raw_bytes)
        rel_ptr = cur_off if len(relocs) > 0 else 0
        cur_off += len(relocs) * 10
        sec_Meta.append((name, chars, raw_bytes, relocs, raw_ptr, rel_ptr))

    symtab_off = cur_off
    out = bytearray()
    out += struct.pack("<HHIIIHH", machine, num_secs, 0, symtab_off, num_syms, 0, 0)
    for name, chars, raw_bytes, relocs, raw_ptr, rel_ptr in sec_Meta:
        padded_name = name[:8].ljust(8, b"\x00")
        out += padded_name
        out += struct.pack(
            "<IIIIIIHHI",
            0,
            0,
            len(raw_bytes),
            raw_ptr,
            rel_ptr,
            0,
            len(relocs),
            0,
            chars,
        )
    for _name, _chars, raw_bytes, relocs, _raw_ptr, _rel_ptr in sec_Meta:
        out += raw_bytes
        for r_off, r_sym, r_type in relocs:
            out += struct.pack("<IIH", r_off, r_sym, r_type)

    strtab = bytearray(b"\x00\x00\x00\x00")
    for sym_name, val, sec_num, sym_type, scl in symbols:
        if len(sym_name) <= 8:
            out += sym_name.ljust(8, b"\x00")
        else:
            s_off = len(strtab)
            strtab += sym_name + b"\x00"
            out += struct.pack("<II", 0, s_off)
        out += struct.pack("<IhHBB", val, sec_num, sym_type, scl, 0)

    struct.pack_into("<I", strtab, 0, len(strtab))
    out += strtab
    return bytes(out)


def test_1_separate_compilation_and_repro(compiler: str, tmp_dir: Path, std_root: Path) -> None:
    """REQ-LNK-200, REQ-LNK-201, REQ-LNK-203, REQ-LNK-209, REQ-LNK-210, REQ-LNK-213:
    Multi-module separate `.obj` + `.lib` archive compilation, canonical section layout,
    `.text` 0xCC padding, `.axmeta` stripping, and byte-identical rebuilds."""
    for run_id in ("run_a", "run_b"):
        pdir = tmp_dir / f"sep_{run_id}"
        sdir = pdir / "src"
        sdir.mkdir(parents=True, exist_ok=True)
        (pdir / "axiom.toml").write_text(
            '[package]\nname = "sep_app"\nversion = "0.1.0"\n',
            encoding="utf-8",
            newline="\n",
        )
        (sdir / "main.ax").write_text(
            """\
use math.compute_linear
use math.generic_id
use scale.apply_bias

extern "C" {
    fn archive_bonus(v: i64) -> i64;
}

pub fn main() -> i32 {
    let a = compute_linear(7, 5); // 7*5 + 3 = 38
    let b = generic_id<i64>(4);   // 4
    let c = apply_bias(10);       // 13
    let d = unsafe { archive_bonus(2) }; // 20
    let res = a + b + c + d;      // 75
    print("sep_app=");
    print_int(res);
    res as i32
}
""",
            encoding="utf-8",
            newline="\n",
        )
        (sdir / "math.ax").write_text(
            """\
module math

use scale.apply_bias

pub fn generic_id<T>(x: T) -> T {
    x
}

pub fn compute_linear(x: i64, y: i64) -> i64 {
    let prod = x * y;
    apply_bias(generic_id<i64>(prod))
}
""",
            encoding="utf-8",
            newline="\n",
        )
        (sdir / "scale.ax").write_text(
            """\
module scale

pub fn apply_bias(v: i64) -> i64 {
    v + 3
}
""",
            encoding="utf-8",
            newline="\n",
        )
        arch_ax = pdir / "bonus_lib.ax"
        arch_ax.write_text(
            """\
module bonus_lib

@export
pub fn archive_bonus(v: i64) -> i64 {
    v * 10
}
""",
            encoding="utf-8",
            newline="\n",
        )

        # Build static archive `.lib`
        bonus_lib = pdir / "bonus_lib.lib"
        run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "lib", "-o", str(bonus_lib), str(arch_ax)])

        # Build each module separately to `.obj`
        main_obj = pdir / "main.obj"
        math_obj = pdir / "math.obj"
        scale_obj = pdir / "scale.obj"
        run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(main_obj), str(sdir / "main.ax")])
        run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(math_obj), str(sdir / "math.ax")])
        run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(scale_obj), str(sdir / "scale.ax")])

        # Verify each `.obj` has `.axmeta` and only its own strong module functions
        main_coff = parse_coff_obj(main_obj.read_bytes(), "main.obj")
        math_coff = parse_coff_obj(math_obj.read_bytes(), "math.obj")
        scale_coff = parse_coff_obj(scale_obj.read_bytes(), "scale.obj")

        for label, coff_info, expected_def, forbidden_def in [
            ("main.obj", main_coff, "main", "apply_bias"),
            ("math.obj", math_coff, "compute_linear", "main"),
            ("scale.obj", scale_coff, "apply_bias", "compute_linear"),
        ]:
            sec_names = [s["name"] for s in coff_info["sections"]]
            if ".axmeta" not in sec_names:
                raise ValidationError(f"{label}: missing .axmeta section in {sec_names}")
            axm_sec = next(s for s in coff_info["sections"] if s["name"] == ".axmeta")
            if axm_sec["data"][:4] != b"AXM1":
                raise ValidationError(f"{label}: .axmeta section missing AXM1 magic")
            def_syms = {s["name"] for s in coff_info["symbols"] if s["section_number"] > 0 and s["storage_class"] == 2}
            if expected_def not in def_syms:
                raise ValidationError(f"{label}: expected defined symbol {expected_def!r} in {def_syms}")
            if forbidden_def in def_syms:
                raise ValidationError(f"{label}: unexpected symbol {forbidden_def!r} leaked into {label} ({def_syms})")

        # Link all separate `.obj`s + `bonus_lib.lib` into `sep.exe`
        sep_exe = pdir / "sep.exe"
        run_checked(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                "-o",
                str(sep_exe),
                str(main_obj),
                str(math_obj),
                str(scale_obj),
                str(bonus_lib),
            ]
        )

        # Also build multi-module project directly + `bonus_lib.lib` into `direct.exe`
        direct_exe = pdir / "direct.exe"
        run_checked(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                "-o",
                str(direct_exe),
                str(pdir),
                str(bonus_lib),
            ]
        )

        # Execute both and verify identical behavior
        res_sep = run_cmd([str(sep_exe)])
        res_dir = run_cmd([str(direct_exe)])
        if res_sep.returncode != 75 or res_dir.returncode != 75:
            raise ValidationError(f"expected exit 75, got sep={res_sep.returncode}, direct={res_dir.returncode}")
        if res_sep.stdout != b"sep_app=75" or res_dir.stdout != b"sep_app=75":
            raise ValidationError(f"unexpected stdout: sep={res_sep.stdout!r}, direct={res_dir.stdout!r}")

        # Inspect PE32+ image: verify `.axmeta` stripped, canonical section order, and 0xCC padding
        pe_info = parse_pe_image(sep_exe.read_bytes(), "sep.exe")
        pe_sec_names = [s["name"] for s in pe_info["sections"]]
        for meta_name in (".axmeta", ".axmir", ".axlto", ".drectve"):
            if meta_name in pe_sec_names:
                raise ValidationError(f"sep.exe leaked non-runtime section {meta_name!r}: {pe_sec_names}")
        canonical_order = [".text", ".rdata", ".data", ".bss", ".pdata", ".xdata", ".idata", ".edata", ".tls", ".reloc"]
        ranks = [canonical_order.index(n) for n in pe_sec_names if n in canonical_order]
        if ranks != sorted(ranks):
            raise ValidationError(f"sep.exe sections out of canonical order: {pe_sec_names}")
        text_sec = next(s for s in pe_info["sections"] if s["name"] == ".text")
        if b"\xcc" not in text_sec["data"]:
            raise ValidationError("sep.exe .text section missing 0xCC (int3) inter-object alignment padding")

    # Verify byte-identical rebuilds across `run_a` and `run_b`
    for artifact_name in ("main.obj", "math.obj", "scale.obj", "bonus_lib.lib", "sep.exe", "direct.exe"):
        bytes_a = (tmp_dir / "sep_run_a" / artifact_name).read_bytes()
        bytes_b = (tmp_dir / "sep_run_b" / artifact_name).read_bytes()
        if bytes_a != bytes_b:
            raise ValidationError(f"non-deterministic build output for {artifact_name} across sep_run_a and sep_run_b")


def test_2_cross_object_relocations_and_unwind(compiler: str, tmp_dir: Path, std_root: Path) -> None:
    """REQ-LNK-206, REQ-LNK-207, REQ-LNK-208:
    Verifies cross-object `IMAGE_REL_AMD64_ADDR64` (1), `IMAGE_REL_AMD64_ADDR32NB` (3),
    `IMAGE_REL_AMD64_REL32` (4), `IMAGE_REL_AMD64_SECTION` (10), and `IMAGE_REL_AMD64_SECREL` (11)
    across `.text`, `.rdata`, `.pdata`, and `.xdata`."""
    rdir = tmp_dir / "reloc_v2"
    rdir.mkdir(parents=True, exist_ok=True)

    # Object 1: defines `ext_target_fn` (returns 55) in `.text` and `ext_const_val` (12) in `.rdata`
    # Object 2: defines `asm_bridge` in `.text` which calls `ext_target_fn` via `REL32`,
    #           reads `ext_const_val` via `ADDR64` pointer in `.rdata`, and has `.pdata`/`.xdata`
    #           entries with `ADDR32NB`, `SECREL`, and `SECTION` relocations targeting `ext_target_fn`.
    #
    # `ext_target_fn` machine code: `mov eax, 55; ret` -> `B8 37 00 00 00 C3` (6 bytes)
    obj1_text = bytes([0xB8, 55, 0x00, 0x00, 0x00, 0xC3])
    obj1_rdata = struct.pack("<Q", 12)
    obj1_bytes = build_coff_obj(
        0x8664,
        [
            (b".text", 0x60500020, obj1_text, []),
            (b".rdata", 0x40400040, obj1_rdata, []),
        ],
        [
            (b"ext_target_fn", 0, 1, 0x20, 2),
            (b"ext_const_val", 0, 2, 0x00, 2),
        ],
    )
    obj1_path = rdir / "reloc_defs.obj"
    obj1_path.write_bytes(obj1_bytes)

    # `asm_bridge` machine code:
    #   sub rsp, 40                 ; 48 83 EC 28
    #   call ext_target_fn          ; E8 00 00 00 00  (reloc @ offset 5, REL32 -> sym 0 `ext_target_fn`)
    #   mov rcx, [rip + ptr_slot]   ; 48 8B 0D 00 00 00 00 (reloc @ offset 12, REL32 -> sym 2 `ptr_slot`)
    #   add rax, [rcx]              ; 48 03 01
    #   add rsp, 40                 ; 48 83 C4 28
    #   ret                         ; C3
    obj2_text = bytes(
        [
            0x48, 0x83, 0xEC, 0x28,
            0xE8, 0x00, 0x00, 0x00, 0x00,
            0x48, 0x8B, 0x0D, 0x00, 0x00, 0x00, 0x00,
            0x48, 0x03, 0x01,
            0x48, 0x83, 0xC4, 0x28,
            0xC3,
        ]
    )
    # `.rdata` in obj2:
    #   offset 0..8: 8-byte pointer `ptr_slot` with `IMAGE_REL_AMD64_ADDR64` (1) -> `ext_const_val`
    #   offset 8..12: 4-byte `IMAGE_REL_AMD64_SECREL` (11) -> `ext_const_val`
    #   offset 12..14: 2-byte `IMAGE_REL_AMD64_SECTION` (10) -> `ext_const_val`
    #   offset 14..16: 2-byte zero pad
    obj2_rdata = b"\x00" * 16
    # `.pdata` in obj2: 12-byte `RUNTIME_FUNCTION` with `ADDR32NB` (3) relocations
    obj2_pdata = struct.pack("<III", 0, 24, 0)
    # `.xdata` in obj2: 8-byte unwind info + `SECREL` (11) & `SECTION` (10)
    obj2_xdata = bytes([0x01, 0x04, 0x01, 0x00, 0x04, 0x42, 0x00, 0x00]) + b"\x00" * 8

    IMAGE_REL_AMD64_ADDR64 = 1
    IMAGE_REL_AMD64_ADDR32NB = 3
    IMAGE_REL_AMD64_REL32 = 4
    IMAGE_REL_AMD64_SECTION = 10
    IMAGE_REL_AMD64_SECREL = 11

    obj2_bytes = build_coff_obj(
        0x8664,
        [
            (
                b".text",
                0x60500020,
                obj2_text,
                [
                    (5, 0, IMAGE_REL_AMD64_REL32),   # call ext_target_fn
                    (12, 2, IMAGE_REL_AMD64_REL32),  # mov rcx, [rip + ptr_slot]
                ],
            ),
            (
                b".rdata",
                0x40400040,
                obj2_rdata,
                [
                    (0, 1, IMAGE_REL_AMD64_ADDR64),   # 64-bit VA of ext_const_val
                    (8, 1, IMAGE_REL_AMD64_SECREL),   # 32-bit section-relative offset of ext_const_val
                    (12, 1, IMAGE_REL_AMD64_SECTION), # 16-bit section index of .rdata
                ],
            ),
            (
                b".pdata",
                0x40300040,
                obj2_pdata,
                [
                    (0, 3, IMAGE_REL_AMD64_ADDR32NB), # BeginAddress -> asm_bridge
                    (4, 3, IMAGE_REL_AMD64_ADDR32NB), # EndAddress -> asm_bridge + 24
                    (8, 4, IMAGE_REL_AMD64_ADDR32NB), # UnwindInfoAddress -> .xdata
                ],
            ),
            (
                b".xdata",
                0x40300040,
                obj2_xdata,
                [
                    (8, 0, IMAGE_REL_AMD64_SECREL),   # SECREL of ext_target_fn in .text
                    (12, 0, IMAGE_REL_AMD64_SECTION), # SECTION index of .text (1)
                ],
            ),
        ],
        [
            (b"ext_target_fn", 0, 0, 0x20, 2), # sym 0: external
            (b"ext_const_val", 0, 0, 0x00, 2), # sym 1: external
            (b"ptr_slot", 0, 2, 0x00, 3),      # sym 2: local .rdata+0
            (b"asm_bridge", 0, 1, 0x20, 2),    # sym 3: global .text+0
            (b"$unwind$bridge", 0, 4, 0x00, 3),# sym 4: local .xdata+0
        ],
    )
    obj2_path = rdir / "reloc_bridge.obj"
    obj2_path.write_bytes(obj2_bytes)

    caller_ax = rdir / "caller.ax"
    caller_ax.write_text(
        """\
extern "C" {
    fn asm_bridge() -> i64;
}

pub fn main() -> i32 {
    let v = unsafe { asm_bridge() };
    v as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    reloc_exe = rdir / "reloc.exe"
    run_checked([compiler, "build", "--std-root", str(std_root), "-o", str(reloc_exe), str(caller_ax), str(obj1_path), str(obj2_path)])

    res = run_cmd([str(reloc_exe)])
    if res.returncode != 67:  # 55 + 12 = 67
        raise ValidationError(f"reloc.exe expected exit 67, got {res.returncode}")

    pe_info = parse_pe_image(reloc_exe.read_bytes(), "reloc.exe")
    sec_by_name = {s["name"]: s for s in pe_info["sections"]}
    if ".pdata" not in sec_by_name or ".xdata" not in sec_by_name:
        raise ValidationError(f"reloc.exe missing .pdata/.xdata sections: {list(sec_by_name)}")
    xdata_bytes = sec_by_name[".xdata"]["data"]
    # Last 4 bytes of our 16-byte .xdata have SECTION=1 (for .text) at offset 12..14
    (_secrel_val, sec_idx_val) = struct.unpack_from("<IH", xdata_bytes, 8)
    if sec_idx_val != sec_by_name[".text"]["index"]:
        raise ValidationError(
            f"IMAGE_REL_AMD64_SECTION in .xdata expected .text index {sec_by_name['.text']['index']}, got {sec_idx_val}"
        )


def test_3_symbol_precedence_and_archives(compiler: str, tmp_dir: Path, std_root: Path) -> None:
    """REQ-LNK-202, REQ-LNK-204, REQ-LNK-205:
    Verifies Strong+Weak (both orders), Weak+Weak (first wins), Local+Local isolation,
    and demand-driven `.lib` archive member extraction."""
    sdir = tmp_dir / "sym_prec"
    sdir.mkdir(parents=True, exist_ok=True)

    main_ax = sdir / "main_hook.ax"
    main_ax.write_text(
        """\
extern "C" {
    fn hook_val() -> i64;
}

pub fn main() -> i32 {
    let v = unsafe { hook_val() };
    v as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    main_obj = sdir / "main_hook.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(main_obj), str(main_ax)])

    weak1_ax = sdir / "weak1.ax"
    weak1_ax.write_text(
        """\
@weak
pub fn hook_val() -> i64 {
    19
}
""",
        encoding="utf-8",
        newline="\n",
    )
    weak2_ax = sdir / "weak2.ax"
    weak2_ax.write_text(
        """\
@weak
pub fn hook_val() -> i64 {
    29
}
""",
        encoding="utf-8",
        newline="\n",
    )
    strong_ax = sdir / "strong.ax"
    strong_ax.write_text(
        """\
pub fn hook_val() -> i64 {
    83
}
""",
        encoding="utf-8",
        newline="\n",
    )
    weak1_obj = sdir / "weak1.obj"
    weak2_obj = sdir / "weak2.obj"
    strong_obj = sdir / "strong.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(weak1_obj), str(weak1_ax)])
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(weak2_obj), str(weak2_ax)])
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(strong_obj), str(strong_ax)])

    # 3a. Strong + Weak -> Strong Wins (both orders: [weak1, strong] and [strong, weak1])
    sw_exe1 = sdir / "sw1.exe"
    sw_exe2 = sdir / "sw2.exe"
    run_checked([compiler, "build", "--std-root", str(std_root), "-o", str(sw_exe1), str(main_obj), str(weak1_obj), str(strong_obj)])
    run_checked([compiler, "build", "--std-root", str(std_root), "-o", str(sw_exe2), str(main_obj), str(strong_obj), str(weak1_obj)])
    if run_cmd([str(sw_exe1)]).returncode != 83:
        raise ValidationError("Strong+Weak [weak1, strong] did not select Strong (83)")
    if run_cmd([str(sw_exe2)]).returncode != 83:
        raise ValidationError("Strong+Weak [strong, weak1] did not select Strong (83)")

    # 3b. Weak + Weak -> First Wins ([weak1, weak2] -> 19, [weak2, weak1] -> 29)
    ww_exe1 = sdir / "ww1.exe"
    ww_exe2 = sdir / "ww2.exe"
    run_checked([compiler, "build", "--std-root", str(std_root), "-o", str(ww_exe1), str(main_obj), str(weak1_obj), str(weak2_obj)])
    run_checked([compiler, "build", "--std-root", str(std_root), "-o", str(ww_exe2), str(main_obj), str(weak2_obj), str(weak1_obj)])
    if run_cmd([str(ww_exe1)]).returncode != 19:
        raise ValidationError("Weak+Weak [weak1, weak2] did not select first Weak (19)")
    if run_cmd([str(ww_exe2)]).returncode != 29:
        raise ValidationError("Weak+Weak [weak2, weak1] did not select first Weak (29)")

    # 3c. Demand-driven `.lib` archive extraction:
    # Build an archive with `needed.obj` (defines `needed_fn` -> 61) and `unused_broken.obj`
    # (references undefined `non_existent_symbol_xyz` and defines duplicate strong `main`).
    needed_ax = sdir / "needed.ax"
    needed_ax.write_text(
        """\
@export
pub fn needed_fn() -> i64 {
    61
}
""",
        encoding="utf-8",
        newline="\n",
    )
    needed_obj = sdir / "needed.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(needed_obj), str(needed_ax)])

    unused_broken_obj = sdir / "unused_broken.obj"
    unused_broken_obj.write_bytes(
        build_coff_obj(
            0x8664,
            [(b".text", 0x60500020, b"\xE8\x00\x00\x00\x00\xC3", [(1, 1, 4)])],
            [
                (b"unused_entry", 0, 1, 0x20, 2),
                (b"non_existent_symbol_xyz", 0, 0, 0x20, 2),
            ],
        )
    )
    selective_lib = sdir / "selective.lib"
    run_checked(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "--kind",
            "lib",
            "-o",
            str(selective_lib),
            str(needed_obj),
            str(unused_broken_obj),
        ]
    )

    use_lib_ax = sdir / "use_lib.ax"
    use_lib_ax.write_text(
        """\
extern "C" {
    fn needed_fn() -> i64;
}

pub fn main() -> i32 {
    let v = unsafe { needed_fn() };
    v as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    use_lib_exe = sdir / "use_lib.exe"
    run_checked([compiler, "build", "--std-root", str(std_root), "-o", str(use_lib_exe), str(use_lib_ax), str(selective_lib)])
    if run_cmd([str(use_lib_exe)]).returncode != 61:
        raise ValidationError("demand-driven archive link expected exit 61")


def test_4_structured_diagnostics(compiler: str, tmp_dir: Path, std_root: Path) -> None:
    """REQ-LNK-211, REQ-LNK-212, REQ-LNK-214:
    Verifies structured diagnostics (both human and `--json`) for:
    - `AX_LINK_DUPLICATE_SYMBOL`
    - `AX_LINK_UNDEFINED_SYMBOL` (including `_AX1_` lossless demangling)
    - `AX_LINK_ABI_MISMATCH` (signature mismatch, calling convention mismatch, FUNC vs DATA mismatch)
    - `AX_LINK_ARTIFACT_TARGET_MISMATCH`"""
    ddir = tmp_dir / "diags_v2"
    ddir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 4a. AX_LINK_DUPLICATE_SYMBOL
    # -------------------------------------------------------------------------
    dup_a_ax = ddir / "math_a.ax"
    dup_a_ax.write_text(
        """\
module math

pub fn add(a: i64, b: i64) -> i64 {
    a + b
}

pub fn main() -> i32 {
    add(1, 2) as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    dup_b_ax = ddir / "math_b.ax"
    dup_b_ax.write_text(
        """\
module math

pub fn add(a: i64, b: i64) -> i64 {
    a + b + 10
}
""",
        encoding="utf-8",
        newline="\n",
    )
    dup_a_obj = ddir / "math_a.obj"
    dup_b_obj = ddir / "math_b.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(dup_a_obj), str(dup_a_ax)])
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(dup_b_obj), str(dup_b_ax)])

    res_dup_h = run_cmd([compiler, "build", "--std-root", str(std_root), "-o", str(ddir / "dup.exe"), str(dup_a_obj), str(dup_b_obj)])
    err_dup_h = res_dup_h.stderr.decode("utf-8", errors="replace")
    if res_dup_h.returncode == 0 or "AX_LINK_DUPLICATE_SYMBOL" not in err_dup_h:
        raise ValidationError(f"expected AX_LINK_DUPLICATE_SYMBOL in human output, got:\n{err_dup_h}")
    if "math.add" not in err_dup_h or "math_a.obj" not in err_dup_h or "math_b.obj" not in err_dup_h:
        raise ValidationError(f"AX_LINK_DUPLICATE_SYMBOL missing demangled name or object names:\n{err_dup_h}")

    res_dup_j = run_cmd([compiler, "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "dup.exe"), str(dup_a_obj), str(dup_b_obj)])
    doc_dup = json.loads(res_dup_j.stderr.decode("utf-8", errors="replace"))
    d0 = doc_dup["diagnostics"][0]
    if d0["code"] != "AX_LINK_DUPLICATE_SYMBOL":
        raise ValidationError(f"expected JSON code AX_LINK_DUPLICATE_SYMBOL, got {d0}")
    if d0["data"].get("demangled") != "math.add" or d0["data"].get("symbol") != "add":
        raise ValidationError(f"expected JSON data.demangled == 'math.add' and data.symbol == 'add', got {d0['data']}")
    if "math_a.obj" not in d0["data"].get("first_object", "") or "math_b.obj" not in d0["data"].get("second_object", ""):
        raise ValidationError(f"unexpected first_object/second_object in {d0['data']}")

    # -------------------------------------------------------------------------
    # 4b. AX_LINK_UNDEFINED_SYMBOL (with `_AX1_` mangled symbol demangling)
    # -------------------------------------------------------------------------
    undef_ax = ddir / "undef_caller.ax"
    undef_ax.write_text(
        """\
module app

extern "C" {
    fn _AX1_4math3addE_F2ll_l(a: i64, b: i64) -> i64;
}

pub fn main() -> i32 {
    let v = unsafe { _AX1_4math3addE_F2ll_l(3, 4) };
    v as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    undef_obj = ddir / "undef_caller.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(undef_obj), str(undef_ax)])

    res_und_h = run_cmd([compiler, "build", "--std-root", str(std_root), "-o", str(ddir / "undef.exe"), str(undef_obj)])
    err_und_h = res_und_h.stderr.decode("utf-8", errors="replace")
    if res_und_h.returncode == 0 or "AX_LINK_UNDEFINED_SYMBOL" not in err_und_h:
        raise ValidationError(f"expected AX_LINK_UNDEFINED_SYMBOL, got:\n{err_und_h}")
    if "math.add" not in err_und_h or "_AX1_4math3addE_F2ll_l" not in err_und_h:
        raise ValidationError(f"AX_LINK_UNDEFINED_SYMBOL missing demangled 'math.add' or raw symbol:\n{err_und_h}")

    res_und_j = run_cmd([compiler, "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "undef.exe"), str(undef_obj)])
    doc_und = json.loads(res_und_j.stderr.decode("utf-8", errors="replace"))
    u0 = doc_und["diagnostics"][0]
    if u0["code"] != "AX_LINK_UNDEFINED_SYMBOL":
        raise ValidationError(f"expected JSON code AX_LINK_UNDEFINED_SYMBOL, got {u0}")
    if u0["data"].get("demangled") != "math.add" or u0["data"].get("symbol") != "_AX1_4math3addE_F2ll_l":
        raise ValidationError(f"unexpected JSON data for AX_LINK_UNDEFINED_SYMBOL: {u0['data']}")

    # -------------------------------------------------------------------------
    # 4c. AX_LINK_ABI_MISMATCH (parameter/return signature, calling conv, FUNC vs DATA)
    # -------------------------------------------------------------------------
    abi_def_ax = ddir / "abi_def.ax"
    abi_def_ax.write_text(
        """\
module math

pub fn compute(x: i64) -> i64 {
    x * 2
}

@cc("sysv64")
pub fn sysv_op(x: i64) -> i64 {
    x + 1
}

@export
pub const SHARED_CONST: i64 = 123;
""",
        encoding="utf-8",
        newline="\n",
    )
    abi_def_obj = ddir / "abi_def.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(abi_def_obj), str(abi_def_ax)])

    # Case 1: Parameter count/type mismatch (`fn(i32, i32) -> i64` vs `fn(i64) -> i64`)
    abi_call1_ax = ddir / "abi_call1.ax"
    abi_call1_ax.write_text(
        """\
extern "C" {
    fn compute(a: i32, b: i32) -> i64;
}

pub fn main() -> i32 {
    (unsafe { compute(1, 2) }) as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    abi_call1_obj = ddir / "abi_call1.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(abi_call1_obj), str(abi_call1_ax)])

    res_abi1 = run_cmd([compiler, "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "abi1.exe"), str(abi_call1_obj), str(abi_def_obj)])
    if res_abi1.returncode == 0:
        raise ValidationError("expected AX_LINK_ABI_MISMATCH for parameter signature mismatch")
    doc_abi1 = json.loads(res_abi1.stderr.decode("utf-8", errors="replace"))
    a1 = doc_abi1["diagnostics"][0]
    if a1["code"] != "AX_LINK_ABI_MISMATCH":
        raise ValidationError(f"expected AX_LINK_ABI_MISMATCH, got {a1}")
    if "fn(i32, i32) -> i64" not in a1["data"].get("expected_abi", "") or "fn(i64) -> i64" not in a1["data"].get("found_abi", ""):
        raise ValidationError(f"unexpected expected_abi/found_abi in {a1['data']}")

    # Case 2: Calling convention mismatch (`win64` vs `sysv64`)
    abi_call2_ax = ddir / "abi_call2.ax"
    abi_call2_ax.write_text(
        """\
extern "C" {
    fn sysv_op(x: i64) -> i64;
}

pub fn main() -> i32 {
    (unsafe { sysv_op(5) }) as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    abi_call2_obj = ddir / "abi_call2.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(abi_call2_obj), str(abi_call2_ax)])

    res_abi2 = run_cmd([compiler, "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "abi2.exe"), str(abi_call2_obj), str(abi_def_obj)])
    if res_abi2.returncode == 0:
        raise ValidationError("expected AX_LINK_ABI_MISMATCH for calling convention mismatch")
    doc_abi2 = json.loads(res_abi2.stderr.decode("utf-8", errors="replace"))
    if doc_abi2["diagnostics"][0]["code"] != "AX_LINK_ABI_MISMATCH":
        raise ValidationError(f"expected AX_LINK_ABI_MISMATCH for cc mismatch, got {doc_abi2}")

    # Case 3: Symbol kind mismatch (`FUNC` vs `DATA`)
    abi_call3_ax = ddir / "abi_call3.ax"
    abi_call3_ax.write_text(
        """\
extern "C" {
    fn SHARED_CONST() -> i64;
}

pub fn main() -> i32 {
    (unsafe { SHARED_CONST() }) as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )
    abi_call3_obj = ddir / "abi_call3.obj"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(abi_call3_obj), str(abi_call3_ax)])

    res_abi3 = run_cmd([compiler, "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "abi3.exe"), str(abi_call3_obj), str(abi_def_obj)])
    if res_abi3.returncode == 0:
        raise ValidationError("expected AX_LINK_ABI_MISMATCH for FUNC vs DATA kind mismatch")
    doc_abi3 = json.loads(res_abi3.stderr.decode("utf-8", errors="replace"))
    if doc_abi3["diagnostics"][0]["code"] != "AX_LINK_ABI_MISMATCH":
        raise ValidationError(f"expected AX_LINK_ABI_MISMATCH for kind mismatch, got {doc_abi3}")

    # -------------------------------------------------------------------------
    # 4d. AX_LINK_ARTIFACT_TARGET_MISMATCH (non-AMD64 COFF object)
    # -------------------------------------------------------------------------
    arm64_obj = ddir / "arm64_foreign.obj"
    arm64_obj.write_bytes(
        build_coff_obj(
            0xAA64,  # IMAGE_FILE_MACHINE_ARM64
            [(b".text", 0x60500020, b"\xC0\x03\x5F\xD6", [])],
            [(b"foreign_fn", 0, 1, 0x20, 2)],
        )
    )
    res_tgt = run_cmd([compiler, "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "tgt.exe"), str(dup_a_obj), str(arm64_obj)])
    if res_tgt.returncode == 0:
        raise ValidationError("expected AX_LINK_ARTIFACT_TARGET_MISMATCH for ARM64 object")
    doc_tgt = json.loads(res_tgt.stderr.decode("utf-8", errors="replace"))
    t0 = doc_tgt["diagnostics"][0]
    if t0["code"] != "AX_LINK_ARTIFACT_TARGET_MISMATCH":
        raise ValidationError(f"expected AX_LINK_ARTIFACT_TARGET_MISMATCH, got {t0}")
    if t0["data"].get("expected_target") != "x86_64-pc-windows-msvc" or t0["data"].get("found_target") != "aarch64-pc-windows-msvc":
        raise ValidationError(f"unexpected target mismatch data: {t0['data']}")


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: link2_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    test_1_separate_compilation_and_repro(compiler, tmp_dir, std_root)
    test_2_cross_object_relocations_and_unwind(compiler, tmp_dir, std_root)
    test_3_symbol_precedence_and_archives(compiler, tmp_dir, std_root)
    test_4_structured_diagnostics(compiler, tmp_dir, std_root)

    print("LINK2-ORACLE ok")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as exc:
        print(f"LINK2-ORACLE FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
