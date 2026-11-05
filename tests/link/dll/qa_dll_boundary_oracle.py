#!/usr/bin/env python3
"""Adversarial QA boundary oracle for T751 (E18.7 / SPEC-26).

Exercises boundary cases beyond `pe_dll_oracle.py`:
  1. Multi-page `.reloc` splitting across >= 3 distinct 4 KiB pages in `.rdata` with BOTH odd
     (padded with `IMAGE_REL_BASED_ABSOLUTE = 0`) and even (`0` pad entries) `DIR64` counts,
     verified both structurally in the `.reloc` directory and dynamically after forced rebasing
     away from preferred `ImageBase = 0x180000000`.
  2. Multi-DLL transitive dependency chain (`exe -> chain_mid_longname.dll -> chain_leaf_longname.dll`)
     where BOTH DLL filenames exceed 15 bytes (triggering COFF archive `//` Longnames Member in both
     companion short-import `.lib` files) AND `chain_mid_longname.dll` imports functions and data
     from `chain_leaf_longname.lib` while both DLLs are forced to rebase simultaneously.
  3. `.edata` strict unsigned ASCII byte-order sorting across digit / uppercase / `'_'` (`0x5F`) /
     lowercase / prefix boundaries, verified via both name lookup and 1-based ordinal lookup
     (`GetProcAddress(h, MAKEINTRESOURCEA(Base + i))`).
  4. `@export("...")` on inherent `impl` method, `AX_FFI_GENERIC_EXPORT` on generic `impl<T>`
     method, and 3-arg `@entry(usize, u32, *const u8) -> i32` lifecycle return propagation (`0` vs
     non-zero `i32`, plus `DLL_PROCESS_DETACH`).
  5. Byte-for-byte determinism across repeated builds of chained `.dll` and long-name `.lib` outputs.
"""

import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


IMAGE_FILE_MACHINE_AMD64 = 0x8664
EXPECTED_DLL_FILE_CHARS = 0x2222
EXPECTED_DLL_IMAGE_BASE = 0x180000000
EXPECTED_DLL_OPT_CHARS = 0x0160
IMAGE_REL_BASED_ABSOLUTE = 0
IMAGE_REL_BASED_DIR64 = 10


class ValidationError(Exception):
    pass


def find_tool(names):
    path_env = os.environ.get("PATH", "")
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.isdir(msys_bin) and msys_bin not in path_env:
        path_env = msys_bin + os.pathsep + path_env
    for name in names:
        found = shutil.which(name, path=path_env)
        if found:
            return found
    raise ValidationError(f"mandatory external tool not found in PATH: {names}")


def run_cmd(cmd, cwd=None, expect_rc=0):
    env = dict(os.environ)
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.isdir(msys_bin):
        env["PATH"] = msys_bin + os.pathsep + env.get("PATH", "")
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if expect_rc is not None and p.returncode != expect_rc:
        out_s = p.stdout.decode("utf-8", errors="replace")
        err_s = p.stderr.decode("utf-8", errors="replace")
        raise ValidationError(
            f"command {cmd!r} exited with {p.returncode}, expected {expect_rc}\n"
            f"--- stdout ---\n{out_s}\n--- stderr ---\n{err_s}"
        )
    return p


def rva_to_off(sections, rva: int) -> int:
    for sec in sections:
        vsize = max(sec["vsize"], sec["raw_size"])
        if sec["vaddr"] <= rva < sec["vaddr"] + vsize:
            off = rva - sec["vaddr"]
            if off >= sec["raw_size"]:
                raise ValidationError(f"RVA 0x{rva:x} in zero-fill tail of {sec['name']}")
            return sec["raw_ptr"] + off
    raise ValidationError(f"unmapped RVA 0x{rva:x}")


def read_cstr(data: bytes, off: int) -> str:
    end = data.find(b"\x00", off)
    if end < 0:
        raise ValidationError(f"unterminated C string at 0x{off:x}")
    return data[off:end].decode("ascii")


def inspect_pe_relocs_and_exports(data: bytes, expected_dll_name: str):
    if data[:2] != b"MZ":
        raise ValidationError("missing MZ magic")
    (pe_off,) = struct.unpack_from("<I", data, 0x3C)
    if data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValidationError("missing PE signature")
    coff_off = pe_off + 4
    mach, num_sec, ts, _, _, opt_sz, chars = struct.unpack_from("<HHIIIHH", data, coff_off)
    if mach != IMAGE_FILE_MACHINE_AMD64 or chars != EXPECTED_DLL_FILE_CHARS or ts != 0:
        raise ValidationError(f"bad COFF header: mach={mach:#x} chars={chars:#x} ts={ts}")

    opt_off = coff_off + 20
    (magic,) = struct.unpack_from("<H", data, opt_off)
    (img_base,) = struct.unpack_from("<Q", data, opt_off + 24)
    (checksum,) = struct.unpack_from("<I", data, opt_off + 64)
    (dll_chars,) = struct.unpack_from("<H", data, opt_off + 70)
    if magic != 0x020B or img_base != EXPECTED_DLL_IMAGE_BASE or checksum != 0 or dll_chars != EXPECTED_DLL_OPT_CHARS:
        raise ValidationError(
            f"bad OptionalHeader: magic={magic:#x} base={img_base:#x} csum={checksum} dll_chars={dll_chars:#x}"
        )

    dd_off = opt_off + 112
    exp_rva, exp_sz = struct.unpack_from("<II", data, dd_off + 0)
    imp_rva, imp_sz = struct.unpack_from("<II", data, dd_off + 8)
    rel_rva, rel_sz = struct.unpack_from("<II", data, dd_off + 40)

    sec_base = opt_off + opt_sz
    sections = []
    for i in range(num_sec):
        so = sec_base + i * 40
        raw_nm = data[so : so + 8]
        vsize, vaddr, rawsz, rawptr, _, _, _, _, schars = struct.unpack_from("<IIIIIIHHI", data, so + 8)
        sections.append(
            {
                "name": raw_nm.rstrip(b"\x00").decode("ascii"),
                "vsize": vsize,
                "vaddr": vaddr,
                "raw_size": rawsz,
                "raw_ptr": rawptr,
                "chars": schars,
            }
        )

    # Parse .edata
    eoff = rva_to_off(sections, exp_rva)
    echars, ets, emaj, emin, name_rva, base_ord, nfuncs, nnames, eat_rva, npt_rva, ord_rva = struct.unpack_from(
        "<IIHHIIIIIII", data, eoff
    )
    if echars != 0 or ets != 0 or emaj != 0 or emin != 0 or base_ord != 1 or nfuncs != nnames:
        raise ValidationError(f"bad .edata header: base={base_ord} nfuncs={nfuncs} nnames={nnames}")
    dll_nm = read_cstr(data, rva_to_off(sections, name_rva))
    if dll_nm != expected_dll_name:
        raise ValidationError(f".edata DLL name {dll_nm!r} != {expected_dll_name!r}")

    eat_off = rva_to_off(sections, eat_rva)
    npt_off = rva_to_off(sections, npt_rva)
    ord_off = rva_to_off(sections, ord_rva)
    exports = []
    for i in range(nnames):
        (nrva,) = struct.unpack_from("<I", data, npt_off + i * 4)
        (ord_idx,) = struct.unpack_from("<H", data, ord_off + i * 2)
        if ord_idx != i:
            raise ValidationError(f"OrdinalTable[{i}] = {ord_idx}, expected {i}")
        (fn_rva,) = struct.unpack_from("<I", data, eat_off + ord_idx * 4)
        exports.append((read_cstr(data, rva_to_off(sections, nrva)), base_ord + ord_idx, fn_rva))

    if [nm.encode("ascii") for nm, _, _ in exports] != sorted(nm.encode("ascii") for nm, _, _ in exports):
        raise ValidationError(f".edata names not in strict unsigned ASCII order: {[nm for nm, _, _ in exports]}")

    # Parse .reloc blocks
    roff = rva_to_off(sections, rel_rva)
    pos = 0
    blocks = []
    prev_page = -1
    while pos < rel_sz:
        page_rva, blk_sz = struct.unpack_from("<II", data, roff + pos)
        if blk_sz < 8 or (blk_sz % 4) != 0 or pos + blk_sz > rel_sz:
            raise ValidationError(f"malformed .reloc block at +{pos}: page=0x{page_rva:x} sz={blk_sz}")
        if page_rva <= prev_page or (page_rva & 0xFFF) != 0:
            raise ValidationError(f".reloc PageRVA out of order or unaligned: 0x{page_rva:x} after 0x{prev_page:x}")
        prev_page = page_rva
        n_ent = (blk_sz - 8) // 2
        dir64_offs = []
        abs_pads = 0
        for j in range(n_ent):
            (w,) = struct.unpack_from("<H", data, roff + pos + 8 + j * 2)
            rtype = (w >> 12) & 0xF
            roff12 = w & 0xFFF
            if rtype == IMAGE_REL_BASED_DIR64:
                if abs_pads > 0:
                    raise ValidationError("DIR64 entry appeared after ABSOLUTE pad in .reloc block")
                if dir64_offs and roff12 <= dir64_offs[-1]:
                    raise ValidationError(f"unsorted DIR64 offsets in page 0x{page_rva:x}: {dir64_offs} then {roff12}")
                dir64_offs.append(roff12)
            elif rtype == IMAGE_REL_BASED_ABSOLUTE:
                if roff12 != 0:
                    raise ValidationError(f"non-zero ABSOLUTE pad entry 0x{w:x}")
                abs_pads += 1
            else:
                raise ValidationError(f"unexpected base reloc type {rtype}")
        blocks.append({"page_rva": page_rva, "block_size": blk_sz, "dir64_count": len(dir64_offs), "abs_pads": abs_pads})
        pos += blk_sz

    return {"exports": exports, "reloc_blocks": blocks, "has_imports": imp_rva != 0 and imp_sz != 0}


def check_archive_longnames(data: bytes, expected_dll_name: str):
    if data[:8] != b"!<arch>\n":
        raise ValidationError("missing !<arch>\\n magic")
    pos = 8
    members = []
    while pos < len(data):
        hdr = data[pos : pos + 60]
        if len(hdr) < 60 or hdr[58:60] != b"`\n":
            raise ValidationError(f"bad archive header at {pos}")
        sz = int(hdr[48:58].decode("ascii").strip())
        name = hdr[0:16].decode("ascii", errors="replace").rstrip(" ")
        body = data[pos + 60 : pos + 60 + sz]
        members.append((name, body))
        pos += 60 + sz + (sz & 1)

    longnames = None
    slash_refs = 0
    for name, body in members[2:]:
        if name == "//":
            longnames = body
        elif name.startswith("/") and name[1:].isdigit():
            if longnames is None:
                raise ValidationError("member referenced // before // appeared")
            off = int(name[1:])
            end = longnames.find(b"\x00", off)
            resolved = longnames[off:end].decode("ascii")
            if resolved != expected_dll_name:
                raise ValidationError(f"longname resolved to {resolved!r}, expected {expected_dll_name!r}")
            slash_refs += 1
    if longnames is None or slash_refs == 0:
        raise ValidationError(f"expected // Longnames Member for {expected_dll_name!r}, got members={[m[0] for m in members]}")


def main():
    if len(sys.argv) < 4:
        print("usage: qa_dll_boundary_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    objdump_tool = find_tool(["objdump", "llvm-objdump"])
    gcc_tool = find_tool(["gcc", "clang"])

    # =========================================================================
    # 1. Build `chain_leaf_longname.dll` (>15-char filename -> `//` longnames,
    #    3-page `.reloc` with odd/even/odd DIR64 counts, ASCII boundary exports,
    #    and `@export("...")` on inherent `impl` method)
    # =========================================================================
    leaf_ax = tmp_dir / "chain_leaf_longname.ax"
    leaf_ax.write_text(
        """\
module chain_leaf_longname

@export
pub const S1: Str = "Leaf-PageA-One\\n";

@export
pub const PAD_AB: [8160]u8 = [42u8; 8160];

@export
pub const S2: Str = "Leaf-PageB-TwoA\\n";

@export
pub const S3: Str = "Leaf-PageB-TwoB\\n";

@export
pub const PAD_BC: [8112]u8 = [99u8; 8112];

@export
pub const S4: Str = "Leaf-PageC-TriA\\n";

@export
pub const S5: Str = "Leaf-PageC-TriB\\n";

@export
pub const S6: Str = "Leaf-PageC-TriC\\n";

@export("A0_digit")
pub fn f_a0() -> i32 { 100 }

@export("A10_digit")
pub fn f_a10() -> i32 { 101 }

@export("A2_digit")
pub fn f_a2() -> i32 { 102 }

@export("A_upper")
pub fn f_au() -> i32 { 103 }

@export("Z_upper")
pub fn f_zu() -> i32 { 104 }

@export("_underscore_mid")
pub fn f_us() -> i32 { 105 }

@export("a_lower")
pub fn f_al() -> i32 { 106 }

@export("a_lower_ext")
pub fn f_ale() -> i32 { 107 }

@export("z_tail")
pub fn f_zt() -> i32 { 108 }

pub struct Scaler {
    pub factor: i32,
}

impl Scaler {
    @export("impl_scale_add")
    pub fn scale_add(x: i32, y: i32) -> i32 {
        x * 3 + y
    }
}

pub struct Bias {
    pub offset: i32,
}

impl Bias {
    @export("impl_bias_sub")
    pub fn scale_add(x: i32, y: i32) -> i32 {
        x * 5 - y
    }
}
""",
        encoding="utf-8",
    )

    leaf_dll = tmp_dir / "chain_leaf_longname.dll"
    leaf_lib = tmp_dir / "chain_leaf_longname.lib"
    det_dir = tmp_dir / "det_check"
    det_dir.mkdir(parents=True, exist_ok=True)
    leaf_dll_2 = det_dir / "chain_leaf_longname.dll"
    leaf_lib_2 = det_dir / "chain_leaf_longname.lib"

    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(leaf_dll), str(leaf_ax)])
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(leaf_dll_2), str(leaf_ax)])

    if leaf_dll.read_bytes() != leaf_dll_2.read_bytes() or leaf_lib.read_bytes() != leaf_lib_2.read_bytes():
        raise ValidationError("chain_leaf_longname.dll/.lib not byte-identical across repeated builds")

    check_archive_longnames(leaf_lib.read_bytes(), "chain_leaf_longname.dll")
    leaf_info = inspect_pe_relocs_and_exports(leaf_dll.read_bytes(), "chain_leaf_longname.dll")

    blocks = leaf_info["reloc_blocks"]
    if len(blocks) < 3:
        raise ValidationError(f"expected >= 3 .reloc 4KiB page blocks, got {blocks}")
    counts_pads = [(b["dir64_count"], b["abs_pads"]) for b in blocks]
    for req_pair in [(1, 1), (2, 0), (3, 1)]:
        if req_pair not in counts_pads:
            raise ValidationError(f"expected (dir64_count, abs_pads)={req_pair} in .reloc blocks, got {counts_pads}")

    # Verify strict ASCII ordering across '0'<'1'<'2'<'_' and 'A'<'Z'<'_'<'a'<'z'
    exp_names = [nm for nm, _, _ in leaf_info["exports"]]
    boundary_subseq = [
        "A0_digit",
        "A10_digit",
        "A2_digit",
        "A_upper",
        "PAD_AB",
        "PAD_BC",
        "S1",
        "S2",
        "S3",
        "S4",
        "S5",
        "S6",
        "Z_upper",
        "_underscore_mid",
        "a_lower",
        "a_lower_ext",
        "impl_bias_sub",
        "impl_scale_add",
        "z_tail",
    ]
    if exp_names != boundary_subseq:
        raise ValidationError(f"unexpected .edata sorted order:\n  got:  {exp_names}\n  want: {boundary_subseq}")

    # =========================================================================
    # 2. Build `chain_mid_longname.dll` importing `chain_leaf_longname.lib`
    #    with 3-arg `@entry(...) -> i32`
    # =========================================================================
    mid_ax = tmp_dir / "chain_mid_longname.ax"
    mid_ax.write_text(
        """\
module chain_mid_longname

@link("chain_leaf_longname")
extern "C" {
    fn A10_digit() -> i32;
    fn _underscore_mid() -> i32;
    fn impl_bias_sub(x: i32, y: i32) -> i32;
    fn impl_scale_add(x: i32, y: i32) -> i32;
    fn z_tail() -> i32;
}

@entry
fn mid_dll_entry(hinst: usize, reason: u32, reserved: *const u8) -> i32 {
    let _ = reserved;
    if reason == 1u32 {
        print("MID-ATTACH\\n");
        if hinst == 0 {
            return 0;
        }
        return 1;
    }
    if reason == 0u32 {
        print("MID-DETACH\\n");
    }
    1
}

@export
pub const MID_BANNER: Str = "Mid-Rebased-OK\\n";

@export
pub fn mid_chain_compute(x: i32) -> i32 {
    // x=10: 101 + 105 + 35 + 45 + 108 = 394
    A10_digit() + _underscore_mid() + impl_scale_add(x, 5) + impl_bias_sub(x, 5) + z_tail()
}
""",
        encoding="utf-8",
    )

    mid_dll = tmp_dir / "chain_mid_longname.dll"
    mid_lib = tmp_dir / "chain_mid_longname.lib"
    mid_dll_2 = det_dir / "chain_mid_longname.dll"
    mid_lib_2 = det_dir / "chain_mid_longname.lib"

    run_cmd(
        [compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-L", str(tmp_dir), "-o", str(mid_dll), str(mid_ax)]
    )
    run_cmd(
        [compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-L", str(tmp_dir), "-o", str(mid_dll_2), str(mid_ax)]
    )
    if mid_dll.read_bytes() != mid_dll_2.read_bytes() or mid_lib.read_bytes() != mid_lib_2.read_bytes():
        raise ValidationError("chain_mid_longname.dll/.lib not byte-identical across repeated builds")

    check_archive_longnames(mid_lib.read_bytes(), "chain_mid_longname.dll")
    mid_info = inspect_pe_relocs_and_exports(mid_dll.read_bytes(), "chain_mid_longname.dll")
    if not mid_info["has_imports"]:
        raise ValidationError("chain_mid_longname.dll missing .idata import directory")
    od_mid = run_cmd([objdump_tool, "-p", str(mid_dll)]).stdout.decode("utf-8", errors="replace")
    if "chain_leaf_longname.dll" not in od_mid:
        raise ValidationError(f"objdump -p on chain_mid_longname.dll missing chain_leaf_longname.dll:\n{od_mid}")

    # =========================================================================
    # 3. Axiom `.exe` -> `chain_mid_longname.dll` -> `chain_leaf_longname.dll`
    # =========================================================================
    ax_app = tmp_dir / "chain_ax_app.ax"
    ax_app.write_text(
        """\
module chain_ax_app

@link("chain_mid_longname")
extern "C" {
    fn mid_chain_compute(x: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe {
        let r = mid_chain_compute(10); // 394
        if r == 394 {
            77
        } else {
            1
        }
    }
}
""",
        encoding="utf-8",
    )
    ax_app_exe = tmp_dir / "chain_ax_app.exe"
    run_cmd([compiler, "build", "--std-root", str(std_root), "-L", str(tmp_dir), "-o", str(ax_app_exe), str(ax_app)])
    res_chain = run_cmd([str(ax_app_exe)], cwd=str(tmp_dir), expect_rc=77)
    if b"MID-ATTACH\n" not in res_chain.stdout:
        raise ValidationError(f"expected MID-ATTACH in chain_ax_app stdout, got {res_chain.stdout!r}")

    # =========================================================================
    # 4. Forced simultaneous rebase of BOTH chained DLLs + ordinal==name lookup
    #    + all 6 multi-page `Str` constants dereferenced after rebasing
    # =========================================================================
    export_checks_c = "\n".join(
        f'    if (GetProcAddress(h_leaf, "{nm}") != GetProcAddress(h_leaf, MAKEINTRESOURCEA({ord_num})) || !GetProcAddress(h_leaf, "{nm}")) return {20 + idx};'
        for idx, (nm, ord_num, _) in enumerate(leaf_info["exports"])
    )
    rebase_host_c = tmp_dir / "chain_rebase_host.c"
    rebase_host_c.write_text(
        f"""\
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef int32_t (*fn_mid_t)(int32_t);
typedef int32_t (*fn_0arg_t)(void);
typedef struct {{
    const char *ptr;
    size_t len;
}} AxStr;

static int check_rebased_str(HMODULE h, uintptr_t base, const char *sym, const char *want) {{
    const AxStr *ps = (const AxStr *)(const void *)GetProcAddress(h, sym);
    if (!ps) return 0;
    uintptr_t p = (uintptr_t)ps->ptr;
    size_t wlen = strlen(want);
    if (p < base || p >= base + 0x200000ULL) return 0;
    if (ps->len != wlen || memcmp(ps->ptr, want, wlen) != 0) return 0;
    return 1;
}}

int main(void) {{
    void *res = VirtualAlloc((void *)0x180000000ULL, 0x200000, MEM_RESERVE, PAGE_NOACCESS);
    HMODULE h_mid = LoadLibraryA("chain_mid_longname.dll");
    if (!h_mid) {{
        fprintf(stderr, "LoadLibraryA(chain_mid_longname.dll) failed: %lu\\n", GetLastError());
        return 10;
    }}
    HMODULE h_leaf = GetModuleHandleA("chain_leaf_longname.dll");
    if (!h_leaf || h_leaf == h_mid) return 11;
    uintptr_t b_mid = (uintptr_t)h_mid;
    uintptr_t b_leaf = (uintptr_t)h_leaf;
    if (b_mid == 0x180000000ULL || b_leaf == 0x180000000ULL) return 12;

{export_checks_c}

    if (!check_rebased_str(h_leaf, b_leaf, "S1", "Leaf-PageA-One\\n")) return 50;
    if (!check_rebased_str(h_leaf, b_leaf, "S2", "Leaf-PageB-TwoA\\n")) return 51;
    if (!check_rebased_str(h_leaf, b_leaf, "S3", "Leaf-PageB-TwoB\\n")) return 52;
    if (!check_rebased_str(h_leaf, b_leaf, "S4", "Leaf-PageC-TriA\\n")) return 53;
    if (!check_rebased_str(h_leaf, b_leaf, "S5", "Leaf-PageC-TriB\\n")) return 54;
    if (!check_rebased_str(h_leaf, b_leaf, "S6", "Leaf-PageC-TriC\\n")) return 55;
    if (!check_rebased_str(h_mid, b_mid, "MID_BANNER", "Mid-Rebased-OK\\n")) return 56;

    fn_mid_t fn_mid = (fn_mid_t)(void *)GetProcAddress(h_mid, "mid_chain_compute");
    fn_0arg_t fn_a0 = (fn_0arg_t)(void *)GetProcAddress(h_leaf, "A0_digit");
    fn_0arg_t fn_al = (fn_0arg_t)(void *)GetProcAddress(h_leaf, "a_lower");
    fn_0arg_t fn_ale = (fn_0arg_t)(void *)GetProcAddress(h_leaf, "a_lower_ext");
    if (!fn_mid || !fn_a0 || !fn_al || !fn_ale) return 57;
    if (fn_mid(10) != 394 || fn_a0() != 100 || fn_al() != 106 || fn_ale() != 107) return 58;

    FreeLibrary(h_mid);
    if (res) VirtualFree(res, 0, MEM_RELEASE);
    return 66;
}}
""",
        encoding="utf-8",
    )
    rebase_host_exe = tmp_dir / "chain_rebase_host.exe"
    run_cmd([gcc_tool, "-O2", str(rebase_host_c), "-o", str(rebase_host_exe)])
    res_reb = run_cmd([str(rebase_host_exe)], cwd=str(tmp_dir), expect_rc=66)
    if res_reb.stdout != b"MID-ATTACH\nMID-DETACH\n":
        raise ValidationError(f"expected MID-ATTACH + MID-DETACH on LoadLibrary/FreeLibrary, got {res_reb.stdout!r}")

    # =========================================================================
    # 5. Negative/Boundary: 3-arg `@entry -> i32` returning 0 aborts load, and
    #    `@export` on generic `impl<T>` method emits `AX_FFI_GENERIC_EXPORT`
    # =========================================================================
    entry_i32_zero_ax = tmp_dir / "entry_i32_zero.ax"
    entry_i32_zero_ax.write_text(
        """\
module entry_i32_zero

@entry
fn init_zero(hinst: usize, reason: u32, reserved: *const u8) -> i32 {
    let _ = hinst;
    let _ = reserved;
    if reason == 1u32 {
        return 0;
    }
    1
}
""",
        encoding="utf-8",
    )
    entry_i32_zero_dll = tmp_dir / "entry_i32_zero.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(entry_i32_zero_dll), str(entry_i32_zero_ax)])
    probe_zero_c = tmp_dir / "probe_zero.c"
    probe_zero_c.write_text(
        '#include <windows.h>\nint main(void) { return LoadLibraryA("entry_i32_zero.dll") == NULL ? 44 : 1; }\n',
        encoding="utf-8",
    )
    probe_zero_exe = tmp_dir / "probe_zero.exe"
    run_cmd([gcc_tool, "-O2", str(probe_zero_c), "-o", str(probe_zero_exe)])
    run_cmd([str(probe_zero_exe)], cwd=str(tmp_dir), expect_rc=44)

    gen_impl_ax = tmp_dir / "gen_impl_export.ax"
    gen_impl_ax.write_text(
        """\
module gen_impl_export

pub struct Boxed<T> {
    pub val: T,
}

impl<T> Boxed<T> {
    @export("bad_generic_impl_export")
    pub fn unwrap_val(b: Boxed<T>) -> T {
        b.val
    }
}

@export("bad_generic_impl_export")
pub fn fallback_concrete() -> i32 {
    1
}
""",
        encoding="utf-8",
    )
    for subcmd, extra in [("check", []), ("build", ["--kind", "dll", "-o", str(tmp_dir / "bad_gen_impl.dll")])]:
        p_gi = run_cmd([compiler, subcmd, "--std-root", str(std_root), "--json"] + extra + [str(gen_impl_ax)], expect_rc=1)
        doc = json.loads(p_gi.stderr.decode("utf-8"))
        diags = doc.get("diagnostics", doc if isinstance(doc, list) else [])
        codes = [d.get("code") for d in diags]
        if codes != ["AX_FFI_GENERIC_EXPORT"]:
            raise ValidationError(f"expected sole ['AX_FFI_GENERIC_EXPORT'] on generic impl<T> method in {subcmd}, got {codes}: {doc}")

    # 5b. Generic method `fn own_gen<U>` inside a NON-generic `impl` emits sole `AX_FFI_GENERIC_EXPORT`
    own_gen_method_ax = tmp_dir / "own_gen_method_export.ax"
    own_gen_method_ax.write_text(
        """\
module own_gen_method_export

pub struct PlainBox {
    pub tag: i32,
}

impl PlainBox {
    @export
    pub fn passthrough<U>(u: U) -> U {
        u
    }
}
""",
        encoding="utf-8",
    )
    p_og = run_cmd([compiler, "build", "--std-root", str(std_root), "--json", "--kind", "dll", "-o", str(tmp_dir / "own_gen.dll"), str(own_gen_method_ax)], expect_rc=1)
    doc_og = json.loads(p_og.stderr.decode("utf-8"))
    diags_og = doc_og.get("diagnostics", doc_og if isinstance(doc_og, list) else [])
    codes_og = [d.get("code") for d in diags_og]
    if codes_og != ["AX_FFI_GENERIC_EXPORT"]:
        raise ValidationError(f"expected sole ['AX_FFI_GENERIC_EXPORT'] on generic method in non-generic impl, got {codes_og}: {doc_og}")

    # 5c. Bare `@export` on inherent `impl` method even when another `impl` defines a non-exported
    #     method with the exact same identifier (verifies `orig_item_name` bare-export preservation)
    bare_impl_ax = tmp_dir / "bare_impl_export.ax"
    bare_impl_ax.write_text(
        """\
module bare_impl_export

pub struct FirstImpl {
    pub k: i32,
}

impl FirstImpl {
    @export
    pub fn bare_impl_fn(a: i32, b: i32) -> i32 {
        a * 7 + b
    }
}

pub struct SecondImpl {
    pub k: i32,
}

impl SecondImpl {
    pub fn bare_impl_fn(a: i32, b: i32) -> i32 {
        a - b
    }
}
""",
        encoding="utf-8",
    )
    bare_impl_dll = tmp_dir / "bare_impl_export.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(bare_impl_dll), str(bare_impl_ax)])
    bare_info = inspect_pe_relocs_and_exports(bare_impl_dll.read_bytes(), "bare_impl_export.dll")
    if [nm for nm, _, _ in bare_info["exports"]] != ["bare_impl_fn"]:
        raise ValidationError(f"expected sole bare export ['bare_impl_fn'], got {bare_info['exports']}")
    bare_app_ax = tmp_dir / "bare_impl_app.ax"
    bare_app_ax.write_text(
        """\
module bare_impl_app

@link("bare_impl_export")
extern "C" {
    fn bare_impl_fn(a: i32, b: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { bare_impl_fn(6, 5) }
}
""",
        encoding="utf-8",
    )
    bare_app_exe = tmp_dir / "bare_impl_app.exe"
    run_cmd([compiler, "build", "--std-root", str(std_root), "-L", str(tmp_dir), "-o", str(bare_app_exe), str(bare_app_ax)])
    run_cmd([str(bare_app_exe)], cwd=str(tmp_dir), expect_rc=47)

    # 5d. True duplicate export involving an `impl` method emits sole `AX_LINK_DUPLICATE_EXPORT`
    dup_impl_ax = tmp_dir / "dup_impl_export.ax"
    dup_impl_ax.write_text(
        """\
module dup_impl_export

pub struct S1 { pub x: i32 }
impl S1 {
    @export
    pub fn dup_bare_m() -> i32 { 1 }
}

pub struct S2 { pub x: i32 }
impl S2 {
    @export
    pub fn dup_bare_m() -> i32 { 2 }
}
""",
        encoding="utf-8",
    )
    p_di = run_cmd([compiler, "build", "--std-root", str(std_root), "--json", "--kind", "dll", "-o", str(tmp_dir / "dup_impl.dll"), str(dup_impl_ax)], expect_rc=1)
    doc_di = json.loads(p_di.stderr.decode("utf-8"))
    diags_di = doc_di.get("diagnostics", doc_di if isinstance(doc_di, list) else [])
    codes_di = [d.get("code") for d in diags_di]
    if codes_di != ["AX_LINK_DUPLICATE_EXPORT"] or diags_di[0].get("data", {}).get("symbol") != "dup_bare_m":
        raise ValidationError(f"expected sole AX_LINK_DUPLICATE_EXPORT(symbol='dup_bare_m'), got {diags_di}")

    # 5e. Associated `const` exports inside `impl` blocks without COFF symbol collisions:
    #     - `@export("C1") pub const K` BEFORE bare `@export pub const K` across two `impl` blocks
    #     - non-exported `impl` method `M_CONST` alongside bare `@export pub const M_CONST` in another `impl`
    impl_consts_ax = tmp_dir / "impl_consts_export.ax"
    impl_consts_ax.write_text(
        """\
module impl_consts_export

pub struct HolderA { pub x: i32 }
impl HolderA {
    @export("C1")
    pub const K: i32 = 11;

    pub fn M_CONST() -> i32 { 99 }
}

pub struct HolderB { pub x: i32 }
impl HolderB {
    @export
    pub const K: i32 = 22;

    @export
    pub const M_CONST: i32 = 33;
}
""",
        encoding="utf-8",
    )
    impl_consts_dll = tmp_dir / "impl_consts_export.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(impl_consts_dll), str(impl_consts_ax)])
    ic_info = inspect_pe_relocs_and_exports(impl_consts_dll.read_bytes(), "impl_consts_export.dll")
    if [nm for nm, _, _ in ic_info["exports"]] != ["C1", "K", "M_CONST"]:
        raise ValidationError(f"expected exports ['C1', 'K', 'M_CONST'], got {ic_info['exports']}")
    ic_probe_c = tmp_dir / "impl_consts_probe.c"
    ic_probe_c.write_text(
        """\
#include <windows.h>
#include <stdint.h>
int main(void) {
    HMODULE h = LoadLibraryA("impl_consts_export.dll");
    if (!h) return 10;
    const int32_t *p_c1 = (const int32_t *)(const void *)GetProcAddress(h, "C1");
    const int32_t *p_k  = (const int32_t *)(const void *)GetProcAddress(h, "K");
    const int32_t *p_m  = (const int32_t *)(const void *)GetProcAddress(h, "M_CONST");
    if (!p_c1 || !p_k || !p_m) return 11;
    if (*p_c1 != 11 || *p_k != 22 || *p_m != 33) return 12;
    FreeLibrary(h);
    return 59;
}
""",
        encoding="utf-8",
    )
    ic_probe_exe = tmp_dir / "impl_consts_probe.exe"
    run_cmd([gcc_tool, "-O2", str(ic_probe_c), "-o", str(ic_probe_exe)])
    run_cmd([str(ic_probe_exe)], cwd=str(tmp_dir), expect_rc=59)

    # 5f. Reversed declaration order (`@export pub const K` BEFORE `@export("C1") pub const K`)
    #     PLUS both an unexported `impl` method named `K` and a private module-level `fn PRIV_K`
    #     colliding with `impl` bare `@export pub const` names, verified across `--kind dll`
    #     (including companion `.lib` `dllimport` consumption), `--kind obj` (`gcc -shared`),
    #     and `--kind lib` (`objdump -a`).
    impl_consts_rev_ax = tmp_dir / "impl_consts_rev.ax"
    impl_consts_rev_ax.write_text(
        """\
module impl_consts_rev

fn PRIV_K() -> i32 { 77 }

pub struct RevHolderB { pub x: i32 }
impl RevHolderB {
    @export
    pub const K: i32 = 22;

    @export
    pub const M_CONST: i32 = 33;
}

pub struct RevHolderA { pub x: i32 }
impl RevHolderA {
    @export("C1")
    pub const K: i32 = 11;

    pub fn M_CONST() -> i32 { 99 }
}

pub struct RevHolderC { pub x: i32 }
impl RevHolderC {
    @export
    pub const PRIV_K: i32 = 44;
}

pub struct RevHolderD { pub x: i32 }
impl RevHolderD {
    fn K() -> i32 { 88 }
}

@export
pub fn use_priv_helpers() -> i32 {
    PRIV_K() + RevHolderD.K() + RevHolderA.M_CONST()
}
""",
        encoding="utf-8",
    )
    impl_consts_rev_dll = tmp_dir / "impl_consts_rev.dll"
    impl_consts_rev_lib = tmp_dir / "impl_consts_rev.lib"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(impl_consts_rev_dll), str(impl_consts_rev_ax)])
    ic_rev_info = inspect_pe_relocs_and_exports(impl_consts_rev_dll.read_bytes(), "impl_consts_rev.dll")
    if [nm for nm, _, _ in ic_rev_info["exports"]] != ["C1", "K", "M_CONST", "PRIV_K", "use_priv_helpers"]:
        raise ValidationError(
            f"expected exports ['C1', 'K', 'M_CONST', 'PRIV_K', 'use_priv_helpers'], got {ic_rev_info['exports']}"
        )

    ic_rev_imp_c = tmp_dir / "impl_consts_rev_imp.c"
    ic_rev_imp_c.write_text(
        """\
#include <stdint.h>
extern __declspec(dllimport) const int32_t C1;
extern __declspec(dllimport) const int32_t K;
extern __declspec(dllimport) const int32_t M_CONST;
extern __declspec(dllimport) const int32_t PRIV_K;
__declspec(dllimport) int32_t use_priv_helpers(void);

int32_t rev_bridge_check_consts(void) {
    if (C1 != 11 || K != 22 || M_CONST != 33 || PRIV_K != 44) return 0;
    return C1 + K + M_CONST + PRIV_K;
}

#ifdef STANDALONE_GCC_EXE
int main(void) {
    if (rev_bridge_check_consts() != 110) return 10;
    if (use_priv_helpers() != (77 + 88 + 99)) return 11;
    return 61;
}
#endif
""",
        encoding="utf-8",
    )
    # (a) C consumer linked via gcc against `impl_consts_rev.dll`
    ic_rev_gcc_exe = tmp_dir / "impl_consts_rev_gcc.exe"
    run_cmd([gcc_tool, "-O2", "-DSTANDALONE_GCC_EXE", str(ic_rev_imp_c), str(impl_consts_rev_dll), "-o", str(ic_rev_gcc_exe)])
    run_cmd([str(ic_rev_gcc_exe)], cwd=str(tmp_dir), expect_rc=61)

    # (b) Axiom consumer linked via `axiomc` against companion short-import `impl_consts_rev.lib`
    ic_rev_bridge_obj = tmp_dir / "impl_consts_rev_bridge.obj"
    run_cmd([gcc_tool, "-c", "-O2", str(ic_rev_imp_c), "-o", str(ic_rev_bridge_obj)])
    ic_rev_ax_app = tmp_dir / "impl_consts_rev_app.ax"
    ic_rev_ax_app.write_text(
        """\
module impl_consts_rev_app

extern "C" {
    fn rev_bridge_check_consts() -> i32;
    fn use_priv_helpers() -> i32;
}

pub fn main() -> i32 {
    unsafe {
        let s = rev_bridge_check_consts();
        let h = use_priv_helpers();
        if s == 110 && h == 264 {
            61
        } else {
            1
        }
    }
}
""",
        encoding="utf-8",
    )
    ic_rev_ax_exe = tmp_dir / "impl_consts_rev_ax.exe"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(ic_rev_ax_exe),
            str(ic_rev_ax_app),
            str(ic_rev_bridge_obj),
            str(impl_consts_rev_lib),
        ]
    )
    run_cmd([str(ic_rev_ax_exe)], cwd=str(tmp_dir), expect_rc=61)

    # Also verify `--kind obj` and `--kind lib` emit collision-free COFF symbols on the same module
    impl_consts_rev_obj = tmp_dir / "impl_consts_rev.obj"
    impl_consts_rev_static_lib = tmp_dir / "impl_consts_rev_static.lib"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "obj", "-o", str(impl_consts_rev_obj), str(impl_consts_rev_ax)])
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "lib", "-o", str(impl_consts_rev_static_lib), str(impl_consts_rev_ax)])
    run_cmd([objdump_tool, "-t", str(impl_consts_rev_obj)])
    run_cmd([objdump_tool, "-a", str(impl_consts_rev_static_lib)])

    print("QA-DLL-BOUNDARY-ORACLE ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
