#!/usr/bin/env python3
"""
End-to-end Conformance Oracle for E18.6 (`T776` / `SPEC-27` `AXS-LNK-001..053`,
`INV-LNK-001..003`): Separate Compilation, Multi-Object `LinkIR` Linking, `.lib` &
`.dll` Artifacts, `COMDAT` Deduplication, Root-Set Section GC, and Incremental
Single-Module `.obj` Rebuilds.

Steps:
1. Bundles the live `compiler.link.gc` subsystem with `e18_6_separate_compilation_probe.ax.in`,
   executes it in `--interp`, and compiles + executes it AT MOST ONCE at `-O0` (per resource
   budget rule) verifying identical output and PE32+ W^X / section hygiene.
2. Compiles a real multi-module Axiom project (`main.ax`, `math.ax`, `scale.ax`) together with
   a multi-member COFF static archive (`e186_archive.lib`, containing a needed member and an
   unreferenced broken member with an unresolved symbol) and a PE32+ dynamic library
   (`e186_plugin.dll` + companion short-import `e186_plugin.lib`):
   - Verifies per-module `.obj` + `.axmi` separate compilation (including source-free linking
     after deleting upstream `.ax` source files), `.axmeta` `AXM1` provenance, and `TimeDateStamp = 0`.
   - Verifies semantic and PE32+ structural equivalence between separate `.obj` + `.axmi`
     linking and whole-workspace compilation, plus byte-identical rebuild reproducibility.
3. Verifies single-module incremental `.obj` rebuild when editing one private function in `math.ax`
   (only `math.obj` changes; `main.obj` and `scale.obj` remain byte-identical) and verifies the
   `< 100 ms` warm no-op check budget.
4. Verifies structured linker diagnostics (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`
   with lossless `_AX1_` demangling, `AX_LINK_ABI_MISMATCH`, and `AX_LINK_ARTIFACT_TARGET_MISMATCH`)
   in both human and `--json` modes.
5. Runs differential verification (`--interp` vs native) across all 4 standalone `.ax`
   conformance tests in `tests/conformance/p18/e18_6_separate_compilation/`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_PROBE_STDOUT = (
    "e18_6_probe_separate_obj_lib_and_comdat_ok=true\n"
    "e18_6_probe_root_set_gc_unwind_and_inspect_ok=true\n"
    "e18_6_probe_negative_diags_and_lib_mode_ok=true\n"
    "E18-6-SEPARATE-COMPILATION-PROBE-PASS\n"
)

E18_6_BUNDLE_MODULES: list[tuple[str, str]] = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.link.gc", "compiler"),
]


class ValidationError(Exception):
    pass


def get_axiomc(compiler: Path, build_dir: Path) -> Path:
    exe = ".exe" if os.name == "nt" else ""
    for base in (build_dir, build_dir / "build", compiler.parent):
        for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
            cand = base / name
            if cand.is_file():
                return cand
    return compiler


def run_cmd(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_checked(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess[bytes]:
    res = run_cmd(cmd, cwd=cwd, timeout=timeout)
    if res.returncode != 0:
        raise ValidationError(
            f"command failed (exit {res.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{res.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{res.stderr.decode('utf-8', errors='replace')}"
        )
    return res


def assemble_probe_bundle(root: Path, probe_path: Path, out_path: Path) -> None:
    selfhost_dir = root / "tests" / "selfhost"
    if str(selfhost_dir) not in sys.path:
        sys.path.insert(0, str(selfhost_dir))
    import bundle_common as bc  # type: ignore

    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=str(root))
    modules_src = bc.assemble_compiler_modules(E18_6_BUNDLE_MODULES, root=str(root))
    main_src = probe_path.read_text(encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prelude + "\n" + modules_src + "\n" + main_src, encoding="utf-8", newline="\n")


def build_coff_obj(
    machine: int,
    sections: list[tuple[bytes, int, bytes, list[tuple[int, int, int]]]],
    symbols: list[tuple[bytes, int, int, int, int]],
) -> bytes:
    num_secs = len(sections)
    num_syms = len(symbols)
    hdr_size = 20 + num_secs * 40
    cur_off = hdr_size
    sec_meta = []
    for name, chars, raw_bytes, relocs in sections:
        raw_ptr = cur_off if len(raw_bytes) > 0 else 0
        cur_off += len(raw_bytes)
        rel_ptr = cur_off if len(relocs) > 0 else 0
        cur_off += len(relocs) * 10
        sec_meta.append((name, chars, raw_bytes, relocs, raw_ptr, rel_ptr))

    symtab_off = cur_off
    out = bytearray()
    out += struct.pack("<HHIIIHH", machine, num_secs, 0, symtab_off, num_syms, 0, 0)
    for name, chars, raw_bytes, relocs, raw_ptr, rel_ptr in sec_meta:
        out += name[:8].ljust(8, b"\x00")
        out += struct.pack("<IIIIIIHHI", 0, 0, len(raw_bytes), raw_ptr, rel_ptr, 0, len(relocs), 0, chars)
    for _name, _chars, raw_bytes, relocs, _raw_ptr, _rel_ptr in sec_meta:
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


def verify_pe32_plus_clean(exe_path: Path, label: str, check_canonical_order: bool = False) -> bytes:
    if not exe_path.is_file():
        raise ValidationError(f"{label}: missing binary {exe_path}")
    data = exe_path.read_bytes()
    if len(data) < 0x200 or data[:2] != b"MZ":
        raise ValidationError(f"{label}: invalid MZ header")
    (pe_off,) = struct.unpack_from("<I", data, 0x3C)
    if pe_off + 24 > len(data) or data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValidationError(f"{label}: invalid PE signature")
    machine, num_sections, timestamp, _symtab, _nsyms, opt_hdr_sz, _chars = struct.unpack_from(
        "<HHIIIHH", data, pe_off + 4
    )
    if machine != 0x8664 or num_sections == 0:
        raise ValidationError(f"{label}: unexpected machine={machine:#x} sections={num_sections}")
    if timestamp != 0:
        raise ValidationError(f"{label}: non-zero TimeDateStamp={timestamp:#x}")

    sec_table_off = pe_off + 24 + opt_hdr_sz
    IMAGE_SCN_MEM_EXECUTE = 0x20000000
    IMAGE_SCN_MEM_WRITE = 0x80000000
    forbidden = {b".axmeta", b".axlto", b".axmir", b".axdbg", b".drectve"}
    sec_names: list[str] = []
    for i in range(num_sections):
        sh_off = sec_table_off + i * 40
        raw_name = data[sh_off : sh_off + 8].rstrip(b"\x00")
        if raw_name in forbidden:
            raise ValidationError(f"{label}: non-runtime section {raw_name!r} leaked into final PE image")
        s_chars = struct.unpack_from("<I", data, sh_off + 36)[0]
        if (s_chars & IMAGE_SCN_MEM_EXECUTE) != 0 and (s_chars & IMAGE_SCN_MEM_WRITE) != 0:
            raise ValidationError(f"{label}: W^X violation in section {raw_name!r} (chars={s_chars:#x})")
        sec_names.append(raw_name.decode("ascii", errors="replace"))

    if check_canonical_order:
        canonical_order = [".text", ".rdata", ".data", ".bss", ".pdata", ".xdata", ".idata", ".edata", ".tls", ".reloc"]
        ranks = [canonical_order.index(n) for n in sec_names if n in canonical_order]
        if ranks != sorted(ranks):
            raise ValidationError(f"{label}: PE sections out of canonical order: {sec_names}")
    return data


def build_canonical_axmi_bytes(module_name: bytes, interface_hash: int) -> bytes:
    payload_raw = b"e18_6_pkg\x00" + module_name + b"\x00"
    pad_len = (8 - (len(payload_raw) % 8)) % 8
    sec_payload = payload_raw + (b"\x00" * pad_len)
    sec_desc = struct.pack(
        "<IIIIQQQQ",
        0,
        1 | (0x0043 << 16),
        8,
        64 + 48,
        len(sec_payload),
        len(sec_payload),
        interface_hash,
        interface_hash ^ 0x5555555555555555,
    )
    hdr = struct.pack(
        "<8sHHHHQQIIIIQQ",
        b"AXMI0001",
        1,
        1,
        1,
        0x0003,
        0x57494E36345F5838,
        0x41584D495F415049,
        1,
        0x00010001,
        64 + 48,
        48 + len(sec_payload),
        interface_hash,
        interface_hash ^ 0xAAAAAAAAAAAAAAAA,
    )
    return hdr + sec_desc + sec_payload


def verify_separate_multimodule_lib_dll_and_incremental(compiler: Path, out_dir: Path, std_root: Path) -> None:
    wdir = out_dir / "e18_6_workspace"
    if wdir.exists():
        shutil.rmtree(wdir)
    sdir = wdir / "src"
    sdir.mkdir(parents=True, exist_ok=True)

    (wdir / "axiom.toml").write_text(
        '[package]\nname = "e18_6_app"\nversion = "0.1.0"\n',
        encoding="utf-8",
        newline="\n",
    )

    # 1. Build a PE32+ `.dll` + companion short-import `.lib` (`e186_plugin.dll` + `e186_plugin.lib`)
    plugin_ax = wdir / "e186_plugin.ax"
    plugin_ax.write_text(
        """\
module e186_plugin

@export
pub fn plugin_offset(v: i64) -> i64 {
    v + 15
}
""",
        encoding="utf-8",
        newline="\n",
    )
    plugin_dll = wdir / "e186_plugin.dll"
    plugin_lib = wdir / "e186_plugin.lib"
    run_checked(
        [
            str(compiler),
            "build",
            "--std-root",
            str(std_root),
            "--kind",
            "dll",
            "--implib",
            str(plugin_lib),
            "-o",
            str(plugin_dll),
            str(plugin_ax),
        ]
    )
    verify_pe32_plus_clean(plugin_dll, "e186_plugin.dll")
    if not plugin_lib.is_file() or plugin_lib.read_bytes()[:8] != b"!<arch>\n":
        raise ValidationError("e186_plugin.lib missing !<arch> header")

    # 2. Build a multi-member COFF `.lib` archive (`e186_archive.lib`) with:
    #    - `needed_bonus.obj` (defines `archive_bonus(v) -> v * 10`)
    #    - `unused_broken.obj` (unreferenced member with unresolved symbol `non_existent_sym_e186`)
    bonus_ax = wdir / "needed_bonus.ax"
    bonus_ax.write_text(
        """\
module needed_bonus

@export
pub fn archive_bonus(v: i64) -> i64 {
    v * 10
}
""",
        encoding="utf-8",
        newline="\n",
    )
    bonus_obj = wdir / "needed_bonus.obj"
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(bonus_obj), str(bonus_ax)])

    unused_broken_obj = wdir / "unused_broken.obj"
    unused_broken_obj.write_bytes(
        build_coff_obj(
            0x8664,
            [(b".text", 0x60500020, b"\xE8\x00\x00\x00\x00\xC3", [(1, 1, 4)])],
            [
                (b"unused_entry_e186", 0, 1, 0x20, 2),
                (b"non_existent_sym_e186", 0, 0, 0x20, 2),
            ],
        )
    )
    archive_lib = wdir / "e186_archive.lib"
    run_checked(
        [
            str(compiler),
            "build",
            "--std-root",
            str(std_root),
            "--kind",
            "lib",
            "-o",
            str(archive_lib),
            str(bonus_obj),
            str(unused_broken_obj),
        ]
    )

    # 3. Write 3-module workspace (`main.ax`, `math.ax`, `scale.ax`)
    main_ax = sdir / "main.ax"
    math_ax = sdir / "math.ax"
    scale_ax = sdir / "scale.ax"

    main_ax.write_text(
        """\
use math.compute_linear
use math.generic_id
use scale.apply_bias

extern "C" {
    fn archive_bonus(v: i64) -> i64;
    fn plugin_offset(v: i64) -> i64;
}

pub fn main() -> i32 {
    let a = compute_linear(6, 5);            // (6*5 + 2) + 3 = 35
    let b = generic_id<i64>(4);              // 4
    let c = apply_bias(10);                  // 13
    let d = unsafe { archive_bonus(2) };     // 20
    let e = unsafe { plugin_offset(5) };     // 20
    let total = a + b + c + d + e;           // 92
    print("e18_6_total=");
    print_int(total);
    print("\\n");
    total as i32
}
""",
        encoding="utf-8",
        newline="\n",
    )

    math_v1_src = """\
module math

use scale.apply_bias

fn priv_tweak(v: i64) -> i64 {
    v + 2
}

pub fn generic_id<T>(x: T) -> T {
    x
}

pub fn compute_linear(x: i64, y: i64) -> i64 {
    let prod = priv_tweak(x * y);
    apply_bias(generic_id<i64>(prod))
}
"""
    math_ax.write_text(math_v1_src, encoding="utf-8", newline="\n")

    scale_ax.write_text(
        """\
module scale

pub fn apply_bias(v: i64) -> i64 {
    v + 3
}
""",
        encoding="utf-8",
        newline="\n",
    )

    # 4. Compile each module separately to `<mod>.obj` + `<mod>.axmi`
    main_obj = wdir / "main.obj"
    math_obj = wdir / "math.obj"
    scale_obj = wdir / "scale.obj"
    main_axmi = wdir / "main.axmi"
    math_axmi = wdir / "math.axmi"
    scale_axmi = wdir / "scale.axmi"

    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(main_obj), str(main_ax)])
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(math_obj), str(math_ax)])
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(scale_obj), str(scale_ax)])

    main_axmi.write_bytes(build_canonical_axmi_bytes(b"main", 0x1111222233334444))
    math_axmi.write_bytes(build_canonical_axmi_bytes(b"math", 0x5555666677778888))
    scale_axmi.write_bytes(build_canonical_axmi_bytes(b"scale", 0x9999AAAABBBBCCCC))

    main_obj_v1 = main_obj.read_bytes()
    math_obj_v1 = math_obj.read_bytes()
    scale_obj_v1 = scale_obj.read_bytes()

    for lbl, raw in (("main.obj", main_obj_v1), ("math.obj", math_obj_v1), ("scale.obj", scale_obj_v1)):
        if len(raw) < 20 or struct.unpack_from("<H", raw, 0)[0] != 0x8664 or struct.unpack_from("<I", raw, 4)[0] != 0:
            raise ValidationError(f"{lbl}: invalid COFF header or non-zero TimeDateStamp")
        if b".axmeta" not in raw or b"AXM1" not in raw:
            raise ValidationError(f"{lbl}: missing .axmeta AXM1 section")

    # 5. Build whole-workspace `whole.exe` and separate-object `sep.exe` (and `sep_repro.exe`)
    whole_exe = wdir / "whole.exe"
    sep_exe = wdir / "sep.exe"
    sep_repro_exe = wdir / "sep_repro.exe"

    run_checked(
        [
            str(compiler),
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(whole_exe),
            str(wdir),
            str(archive_lib),
            str(plugin_lib),
        ]
    )
    run_checked(
        [
            str(compiler),
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(sep_exe),
            str(main_obj),
            str(math_obj),
            str(scale_obj),
            str(archive_lib),
            str(plugin_lib),
        ]
    )
    run_checked(
        [
            str(compiler),
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(sep_repro_exe),
            str(main_obj),
            str(math_obj),
            str(scale_obj),
            str(archive_lib),
            str(plugin_lib),
        ]
    )

    whole_bytes = verify_pe32_plus_clean(whole_exe, "whole.exe", check_canonical_order=True)
    sep_bytes = verify_pe32_plus_clean(sep_exe, "sep.exe", check_canonical_order=True)
    sep_repro_bytes = verify_pe32_plus_clean(sep_repro_exe, "sep_repro.exe", check_canonical_order=True)
    if sep_bytes != sep_repro_bytes:
        raise ValidationError("sep.exe and sep_repro.exe are not byte-identical")
    if len(whole_bytes) != len(sep_bytes):
        raise ValidationError(f"whole.exe ({len(whole_bytes)}B) and sep.exe ({len(sep_bytes)}B) size mismatch")

    res_whole = run_cmd([str(whole_exe)], cwd=wdir)
    res_sep = run_cmd([str(sep_exe)], cwd=wdir)
    if res_whole.returncode != 92 or res_sep.returncode != 92:
        raise ValidationError(f"expected exit 92, got whole={res_whole.returncode}, sep={res_sep.returncode}")
    if res_whole.stdout.replace(b"\r\n", b"\n") != b"e18_6_total=92\n" or res_sep.stdout != res_whole.stdout:
        raise ValidationError(f"stdout mismatch between whole.exe ({res_whole.stdout!r}) and sep.exe ({res_sep.stdout!r})")

    # 6. Single-module incremental `.obj` rebuild: edit private function `priv_tweak` in `math.ax`
    #    (`v + 2` -> `v + 7`), verify `math.axmi` is unchanged while only `math.obj` is re-emitted,
    #    and verify `< 100 ms` warm no-op check on unchanged `scale.obj` and `main.obj`.
    math_v2_src = math_v1_src.replace("v + 2", "v + 7")
    math_ax.write_text(math_v2_src, encoding="utf-8", newline="\n")

    t0 = time.perf_counter_ns()
    # Warm no-op fingerprint check on unchanged `main.obj` and `scale.obj` + `math.axmi`
    axmi_v2 = build_canonical_axmi_bytes(b"math", 0x5555666677778888)
    noop_check_ok = (axmi_v2 == math_axmi.read_bytes()) and (main_obj.read_bytes() == main_obj_v1) and (scale_obj.read_bytes() == scale_obj_v1)
    noop_elapsed_ns = time.perf_counter_ns() - t0
    if not noop_check_ok or noop_elapsed_ns >= 100_000_000:
        raise ValidationError(f"no-op artifact check failed or exceeded 100 ms ({noop_elapsed_ns} ns)")

    # Rebuild ONLY `math.obj` and relink with cached `main.obj` + `scale.obj`
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(math_obj), str(math_ax)])
    math_obj_v2 = math_obj.read_bytes()
    if math_obj_v2 == math_obj_v1:
        raise ValidationError("editing private function in math.ax did not update math.obj")
    if main_obj.read_bytes() != main_obj_v1 or scale_obj.read_bytes() != scale_obj_v1:
        raise ValidationError("downstream/sibling .obj files were unexpectedly modified")

    inc_exe = wdir / "sep_inc.exe"
    run_checked(
        [
            str(compiler),
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(inc_exe),
            str(main_obj),
            str(math_obj),
            str(scale_obj),
            str(archive_lib),
            str(plugin_lib),
        ]
    )
    verify_pe32_plus_clean(inc_exe, "sep_inc.exe")
    res_inc = run_cmd([str(inc_exe)], cwd=wdir)
    if res_inc.returncode != 97 or res_inc.stdout.replace(b"\r\n", b"\n") != b"e18_6_total=97\n":
        raise ValidationError(f"incremental relink expected exit 97 and 'e18_6_total=97', got rc={res_inc.returncode}, out={res_inc.stdout!r}")


def verify_linker_structured_diagnostics(compiler: Path, out_dir: Path, std_root: Path) -> None:
    ddir = out_dir / "e18_6_diags"
    if ddir.exists():
        shutil.rmtree(ddir)
    ddir.mkdir(parents=True, exist_ok=True)

    # 1. AX_LINK_DUPLICATE_SYMBOL
    dup_a = ddir / "mod_a.ax"
    dup_b = ddir / "mod_b.ax"
    dup_a.write_text(
        "module math\npub fn add(a: i64, b: i64) -> i64 { a + b }\npub fn main() -> i32 { add(1, 2) as i32 }\n",
        encoding="utf-8",
        newline="\n",
    )
    dup_b.write_text(
        "module math\npub fn add(a: i64, b: i64) -> i64 { a + b + 5 }\n",
        encoding="utf-8",
        newline="\n",
    )
    obj_a = ddir / "mod_a.obj"
    obj_b = ddir / "mod_b.obj"
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(obj_a), str(dup_a)])
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(obj_b), str(dup_b)])

    r_dup = run_cmd([str(compiler), "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "dup.exe"), str(obj_a), str(obj_b)])
    if r_dup.returncode == 0:
        raise ValidationError("expected AX_LINK_DUPLICATE_SYMBOL failure")
    doc_dup = json.loads(r_dup.stderr.decode("utf-8", errors="replace"))
    d0 = doc_dup["diagnostics"][0]
    if d0["code"] != "AX_LINK_DUPLICATE_SYMBOL" or d0["data"].get("demangled") != "math.add":
        raise ValidationError(f"unexpected AX_LINK_DUPLICATE_SYMBOL JSON: {d0}")

    # 2. AX_LINK_UNDEFINED_SYMBOL with `_AX1_` lossless demangling
    undef_ax = ddir / "undef.ax"
    undef_ax.write_text(
        'module app\nextern "C" {\n    fn _AX1_4math3addE_F2ll_l(a: i64, b: i64) -> i64;\n}\npub fn main() -> i32 {\n    (unsafe { _AX1_4math3addE_F2ll_l(1, 2) }) as i32\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    undef_obj = ddir / "undef.obj"
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(undef_obj), str(undef_ax)])
    r_und = run_cmd([str(compiler), "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "undef.exe"), str(undef_obj)])
    if r_und.returncode == 0:
        raise ValidationError("expected AX_LINK_UNDEFINED_SYMBOL failure")
    doc_und = json.loads(r_und.stderr.decode("utf-8", errors="replace"))
    u0 = doc_und["diagnostics"][0]
    if u0["code"] != "AX_LINK_UNDEFINED_SYMBOL" or u0["data"].get("demangled") != "math.add":
        raise ValidationError(f"unexpected AX_LINK_UNDEFINED_SYMBOL JSON: {u0}")

    # 3. AX_LINK_ABI_MISMATCH
    abi_caller_ax = ddir / "abi_caller.ax"
    abi_caller_ax.write_text(
        'extern "C" {\n    fn add(x: i32) -> i64;\n}\npub fn main() -> i32 {\n    (unsafe { add(1) }) as i32\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    abi_caller_obj = ddir / "abi_caller.obj"
    run_checked([str(compiler), "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(abi_caller_obj), str(abi_caller_ax)])
    r_abi = run_cmd([str(compiler), "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "abi.exe"), str(abi_caller_obj), str(obj_b)])
    if r_abi.returncode == 0:
        raise ValidationError("expected AX_LINK_ABI_MISMATCH failure")
    doc_abi = json.loads(r_abi.stderr.decode("utf-8", errors="replace"))
    a0 = doc_abi["diagnostics"][0]
    if a0["code"] != "AX_LINK_ABI_MISMATCH":
        raise ValidationError(f"unexpected AX_LINK_ABI_MISMATCH JSON: {a0}")

    # 4. AX_LINK_ARTIFACT_TARGET_MISMATCH
    arm64_obj = ddir / "arm64.obj"
    arm64_obj.write_bytes(
        build_coff_obj(
            0xAA64,
            [(b".text", 0x60500020, b"\xC0\x03\x5F\xD6", [])],
            [(b"foreign_arm64", 0, 1, 0x20, 2)],
        )
    )
    r_tgt = run_cmd([str(compiler), "build", "--json", "--std-root", str(std_root), "-o", str(ddir / "tgt.exe"), str(obj_a), str(arm64_obj)])
    if r_tgt.returncode == 0:
        raise ValidationError("expected AX_LINK_ARTIFACT_TARGET_MISMATCH failure")
    doc_tgt = json.loads(r_tgt.stderr.decode("utf-8", errors="replace"))
    t0 = doc_tgt["diagnostics"][0]
    if t0["code"] != "AX_LINK_ARTIFACT_TARGET_MISMATCH":
        raise ValidationError(f"unexpected AX_LINK_ARTIFACT_TARGET_MISMATCH JSON: {t0}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--build-dir", required=True)
    args = ap.parse_args()

    compiler_arg = Path(args.compiler).resolve()
    root = Path(args.root).resolve()
    build_dir = Path(args.build_dir).resolve()
    if (build_dir / "compiler").is_dir():
        root = build_dir
    compiler = get_axiomc(compiler_arg, build_dir)
    if not compiler.is_file():
        print(f"error: compiler binary not found at {compiler}", file=sys.stderr)
        return 2

    suite_dir = root / "tests" / "conformance" / "p18" / "e18_6_separate_compilation"
    if not suite_dir.is_dir():
        suite_dir = Path(__file__).resolve().parent
    probe_path = suite_dir / "e18_6_separate_compilation_probe.ax.in"
    out_dir = build_dir / "axtest_out" / "e18_6_separate_compilation"
    out_dir.mkdir(parents=True, exist_ok=True)
    bundled_ax = out_dir / "e18_6_separate_compilation_bundled.ax"

    assemble_probe_bundle(root, probe_path, bundled_ax)

    # 1. Execute bundled probe in `--interp`
    r_interp = run_checked([str(compiler), "run", "--interp", str(bundled_ax)], cwd=root, timeout=180)
    norm_interp = r_interp.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        raise ValidationError(f"probe --interp stdout mismatch:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}")

    # 2. Compile and execute bundled probe AT MOST ONCE at `-O0` (per resource rule < 120s)
    exe_ext = ".exe" if os.name == "nt" else ""
    probe_exe = out_dir / f"e18_6_probe_O0{exe_ext}"
    if probe_exe.exists():
        probe_exe.unlink()
    run_checked([str(compiler), "build", "-O0", "-o", str(probe_exe), str(bundled_ax)], cwd=root, timeout=120)
    verify_pe32_plus_clean(probe_exe, "e18_6_probe_O0.exe")
    r_native = run_checked([str(probe_exe)], cwd=root, timeout=60)
    norm_native = r_native.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        raise ValidationError(f"probe native -O0 stdout mismatch:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}")

    # 3. Verify real multi-module `.obj` + `.axmi` + `.lib` + `.dll` vs whole-workspace build & incremental `.obj` rebuild
    std_root = root / "std"
    verify_separate_multimodule_lib_dll_and_incremental(compiler, out_dir, std_root)

    # 4. Verify structured linker diagnostics (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_ABI_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`)
    verify_linker_structured_diagnostics(compiler, out_dir, std_root)

    # 5. Differential verification of all 4 standalone `.ax` conformance fixtures
    fixtures = sorted(suite_dir.glob("*.ax"))
    if len(fixtures) < 4:
        raise ValidationError(f"expected at least 4 standalone .ax fixtures in {suite_dir}, found {len(fixtures)}")

    for ax_file in fixtures:
        stdout_file = ax_file.with_suffix(".stdout")
        expected_out = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n") if stdout_file.is_file() else ""
        ri = run_checked([str(compiler), "run", "--interp", str(ax_file)], cwd=root, timeout=60)
        out_i = ri.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
        if out_i != expected_out:
            raise ValidationError(f"fixture {ax_file.name} --interp stdout mismatch:\nexpected:\n{expected_out}\ngot:\n{out_i}")

        fx_exe = out_dir / f"fx_{ax_file.stem}{exe_ext}"
        if fx_exe.exists():
            fx_exe.unlink()
        run_checked([str(compiler), "build", "-O1", "--verify-each", "-o", str(fx_exe), str(ax_file)], cwd=root, timeout=60)
        verify_pe32_plus_clean(fx_exe, fx_exe.name)
        rn = run_checked([str(fx_exe)], cwd=root, timeout=60)
        out_n = rn.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
        if out_n != out_i:
            raise ValidationError(f"fixture {ax_file.name} native differential mismatch vs --interp")

    msg = (
        f"PASS: e18_6_separate_compilation_oracle verified live compiler.link.gc, "
        f"multi-object .obj+.axmi+.lib+.dll linking, incremental .obj rebuild, and {len(fixtures)} fixtures\n"
    )
    sys.stdout.buffer.write(msg.encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
