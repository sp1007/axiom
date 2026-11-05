#!/usr/bin/env python3
"""End-to-end oracle for T751 (E18.7): PE32+ DLL output, .edata exports, _DllMainCRTStartup,
.reloc base relocations, companion short-import .lib, and MinGW/C DLL interop (SPEC-26).

Verifies:
  1. `axiomc build --kind dll` produces a deterministic PE32+ `.dll` (`Characteristics=0x2222`,
     `ImageBase=0x180000000`, `DllCharacteristics=0x0160`, W^X section flags, zeroed timestamps
     and checksums) plus a deterministic companion COFF short-import `.lib` (`IMPORT_OBJECT_CODE`
     for functions, `IMPORT_OBJECT_DATA` for `@export const` data).
  2. `.edata` export directory (`DataDirectory[0]`): sorted strictly ascending by ASCII name,
     `Base = 1`, `NumberOfFunctions == NumberOfNames`, `AddressOfNameOrdinals = 0..E-1`, non-`@export`
     `pub fn` excluded; validated both by binary parser and by GNU `objdump -p` / `objdump -d`.
  3. `.reloc` base relocation directory (`DataDirectory[5]`): `IMAGE_REL_BASED_DIR64` (`type = 10`)
     entries sorted by RVA in 4 KiB page blocks for `ADDR64` fixups (such as exported `Str` fat
     pointers in `.rdata`).
  4. Axiom `.exe` consumer AND C (`gcc`) `.exe` consumer linking `mathdll.lib` (via `-L/-l`,
     positional `.lib`, and `@link`), calling exported functions and reading exported scalar,
     array, and `Str` data.
  5. Axiom `.exe` consuming a third-party C DLL built with `gcc -shared -Wl,--out-implib,libcplug.dll.a`
     (traditional `.idata$2..$7` import archive) for both C functions and `__declspec(dllexport)` data.
  6. Forced OS rebasing:
     (a) Reserving `0x180000000` with `VirtualAlloc` before `LoadLibraryA("mathdll.dll")`, proving
         `hMod != 0x180000000` and verifying rebased `DLL_GREETING_STR` fat pointer + exported calls.
     (b) Loading two Axiom DLLs (`reloc_a.dll` and `reloc_b.dll`, both built at default `0x180000000`)
         into the same Axiom `.exe` simultaneously, proving relocation under base collision.
  7. `_DllMainCRTStartup` lifecycle (`AXS-WLIB-022`, `ADR-0001` sections 5-6):
     - Empty 0-function DLL and data-only DLL load cleanly via `LoadLibraryA`.
     - `@entry` 0-arg and 3-arg hooks execute on `DLL_PROCESS_ATTACH` (`fdwReason == 1`).
     - `@entry` returning `false` / `0` causes `LoadLibraryA` to fail cleanly (`NULL`).
     - `__ax_resolve_module_bindings` returning `false` on `DLL_PROCESS_ATTACH` aborts load (`NULL`).
  8. `--implib <path>`, `axiom.toml` `kind = "dll"`, C `.obj` `.drectve` `-export:` merging,
     `axiomc run` rejection on `kind = "dll"` (`AX_DRIVER_USAGE`, exit 2), `AX_LINK_DUPLICATE_EXPORT`
     (`data.symbol`), and `AX_FFI_GENERIC_EXPORT`.
"""

import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_FILE_DLL = 0x2000
EXPECTED_DLL_FILE_CHARS = 0x2222
EXPECTED_DLL_IMAGE_BASE = 0x180000000
EXPECTED_DLL_OPT_CHARS = 0x0160

IMAGE_SCN_CNT_CODE = 0x00000020
IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
IMAGE_SCN_MEM_DISCARDABLE = 0x02000000
IMAGE_SCN_MEM_EXECUTE = 0x20000000
IMAGE_SCN_MEM_READ = 0x40000000
IMAGE_SCN_MEM_WRITE = 0x80000000

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


def run_cmd(cmd, cwd=None, expect_rc=0, extra_path_dirs=()):
    env = dict(os.environ)
    msys_bin = r"C:\msys64\ucrt64\bin"
    p_entries = list(extra_path_dirs)
    if os.path.isdir(msys_bin):
        p_entries.append(msys_bin)
    if p_entries:
        env["PATH"] = os.pathsep.join(str(x) for x in p_entries) + os.pathsep + env.get("PATH", "")
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if expect_rc is not None and p.returncode != expect_rc:
        out_s = p.stdout.decode("utf-8", errors="replace")
        err_s = p.stderr.decode("utf-8", errors="replace")
        raise ValidationError(
            f"command {cmd!r} exited with {p.returncode}, expected {expect_rc}\n"
            f"--- stdout ---\n{out_s}\n--- stderr ---\n{err_s}"
        )
    return p


def rva_to_file_offset(sections, rva: int) -> int:
    for sec in sections:
        vaddr = sec["vaddr"]
        vsize = max(sec["vsize"], sec["raw_size"])
        if vaddr <= rva < vaddr + vsize:
            off_in_sec = rva - vaddr
            if off_in_sec >= sec["raw_size"]:
                raise ValidationError(f"RVA 0x{rva:x} falls in zero-fill tail of {sec['name']}")
            return sec["raw_ptr"] + off_in_sec
    raise ValidationError(f"RVA 0x{rva:x} not mapped by any section")


def read_cstr(data: bytes, off: int) -> str:
    end = data.find(b"\x00", off)
    if end < 0:
        raise ValidationError(f"unterminated C string at file offset 0x{off:x}")
    return data[off:end].decode("ascii")


def parse_and_validate_pe_dll(data: bytes, expected_dll_name: str, expect_exports: bool = True, expect_relocs: bool = False):
    """Validates PE32+ DLL headers, W^X sections, .edata export directory, and .reloc directory."""
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValidationError("missing MZ DOS header")
    (pe_off,) = struct.unpack_from("<I", data, 0x3C)
    if data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValidationError("missing PE\\0\\0 signature")

    coff_off = pe_off + 4
    machine, num_secs, timestamp, sym_ptr, num_syms, opt_size, characteristics = struct.unpack_from(
        "<HHIIIHH", data, coff_off
    )
    if machine != IMAGE_FILE_MACHINE_AMD64:
        raise ValidationError(f"unexpected Machine 0x{machine:04x}")
    if timestamp != 0:
        raise ValidationError(f"non-zero COFF TimeDateStamp: 0x{timestamp:08x}")
    if (characteristics & IMAGE_FILE_DLL) == 0 or characteristics != EXPECTED_DLL_FILE_CHARS:
        raise ValidationError(
            f"expected COFF Characteristics 0x{EXPECTED_DLL_FILE_CHARS:04x}, got 0x{characteristics:04x}"
        )
    if opt_size != 240:
        raise ValidationError(f"expected PE32+ SizeOfOptionalHeader 240, got {opt_size}")

    opt_off = coff_off + 20
    magic = struct.unpack_from("<H", data, opt_off)[0]
    if magic != 0x020B:
        raise ValidationError(f"expected PE32+ Magic 0x020B, got 0x{magic:04x}")

    entry_rva = struct.unpack_from("<I", data, opt_off + 16)[0]
    image_base = struct.unpack_from("<Q", data, opt_off + 24)[0]
    sec_align, file_align = struct.unpack_from("<II", data, opt_off + 32)
    checksum = struct.unpack_from("<I", data, opt_off + 64)[0]
    dll_chars = struct.unpack_from("<H", data, opt_off + 70)[0]
    num_rva_sizes = struct.unpack_from("<I", data, opt_off + 108)[0]

    if image_base != EXPECTED_DLL_IMAGE_BASE:
        raise ValidationError(f"expected DLL ImageBase 0x{EXPECTED_DLL_IMAGE_BASE:x}, got 0x{image_base:x}")
    if sec_align != 0x1000 or file_align != 0x200:
        raise ValidationError(f"unexpected alignments: Section=0x{sec_align:x}, File=0x{file_align:x}")
    if checksum != 0:
        raise ValidationError(f"non-zero OptionalHeader CheckSum: 0x{checksum:08x}")
    if dll_chars != EXPECTED_DLL_OPT_CHARS:
        raise ValidationError(f"expected DllCharacteristics 0x{EXPECTED_DLL_OPT_CHARS:04x}, got 0x{dll_chars:04x}")
    if num_rva_sizes != 16:
        raise ValidationError(f"expected NumberOfRvaAndSizes == 16, got {num_rva_sizes}")

    data_dirs = []
    for d in range(16):
        dd_rva, dd_size = struct.unpack_from("<II", data, opt_off + 112 + d * 8)
        data_dirs.append((dd_rva, dd_size))

    sec_table_off = opt_off + opt_size
    sections = []
    sec_by_name = {}
    for s in range(num_secs):
        sh_off = sec_table_off + s * 40
        raw_name = data[sh_off : sh_off + 8].split(b"\x00", 1)[0].decode("ascii")
        vsize, vaddr, raw_size, raw_ptr, rel_ptr, ln_ptr, nrel, nln, schars = struct.unpack_from(
            "<IIIIIIHHI", data, sh_off + 8
        )
        # W^X invariant: never both WRITE and EXECUTE
        if (schars & IMAGE_SCN_MEM_WRITE) and (schars & IMAGE_SCN_MEM_EXECUTE):
            raise ValidationError(f"section {raw_name} violates W^X: 0x{schars:08x}")
        sec_info = {
            "name": raw_name,
            "vsize": vsize,
            "vaddr": vaddr,
            "raw_size": raw_size,
            "raw_ptr": raw_ptr,
            "chars": schars,
        }
        sections.append(sec_info)
        sec_by_name[raw_name] = sec_info

    if ".text" not in sec_by_name:
        raise ValidationError("DLL missing .text section")
    tsec = sec_by_name[".text"]
    if not (tsec["vaddr"] <= entry_rva < tsec["vaddr"] + tsec["vsize"]):
        raise ValidationError(f"AddressOfEntryPoint 0x{entry_rva:x} outside .text")

    # Parse .edata (DataDirectory[0])
    exp_rva, exp_size = data_dirs[0]
    exports = []
    if expect_exports:
        if exp_rva == 0 or exp_size < 40:
            raise ValidationError(f"expected non-empty Export Directory, got rva=0x{exp_rva:x}, size={exp_size}")
        if ".edata" not in sec_by_name:
            raise ValidationError("expected .edata section")
        esec = sec_by_name[".edata"]
        if esec["chars"] & (IMAGE_SCN_MEM_WRITE | IMAGE_SCN_MEM_EXECUTE):
            raise ValidationError(f".edata must be read-only: 0x{esec['chars']:08x}")
        ed_off = rva_to_file_offset(sections, exp_rva)
        (
            ed_flags,
            ed_ts,
            ed_maj,
            ed_min,
            name_rva,
            ord_base,
            num_funcs,
            num_names,
            eat_rva,
            enpt_rva,
            eot_rva,
        ) = struct.unpack_from("<IIHHIIIIIII", data, ed_off)
        if ed_flags != 0 or ed_ts != 0:
            raise ValidationError(f"expected zeroed Export Directory flags/timestamp, got {ed_flags}/{ed_ts}")
        if ord_base != 1:
            raise ValidationError(f"expected Export Directory Base == 1, got {ord_base}")
        if num_funcs != num_names or num_names == 0:
            raise ValidationError(f"expected NumberOfFunctions == NumberOfNames > 0, got {num_funcs} vs {num_names}")
        internal_name = read_cstr(data, rva_to_file_offset(sections, name_rva))
        if internal_name != expected_dll_name:
            raise ValidationError(f"expected .edata DLL name {expected_dll_name!r}, got {internal_name!r}")

        eat_off = rva_to_file_offset(sections, eat_rva)
        enpt_off = rva_to_file_offset(sections, enpt_rva)
        eot_off = rva_to_file_offset(sections, eot_rva)

        eat = list(struct.unpack_from(f"<{num_funcs}I", data, eat_off))
        enpt = list(struct.unpack_from(f"<{num_names}I", data, enpt_off))
        eot = list(struct.unpack_from(f"<{num_names}H", data, eot_off))

        if eot != list(range(num_names)):
            raise ValidationError(f"expected identity ordinal table 0..{num_names - 1}, got {eot}")

        names = [read_cstr(data, rva_to_file_offset(sections, nrva)) for nrva in enpt]
        if names != sorted(names):
            raise ValidationError(f".edata export names not strictly sorted by ASCII: {names}")

        for idx, nm in enumerate(names):
            fn_rva = eat[eot[idx]]
            if fn_rva == 0:
                raise ValidationError(f"export {nm!r} has zero target RVA")
            # Ensure target RVA is NOT inside .edata (not a forwarder RVA) and maps to a valid section
            if exp_rva <= fn_rva < exp_rva + exp_size:
                raise ValidationError(f"export {nm!r} unexpectedly points into .edata (forwarder)")
            _ = rva_to_file_offset(sections, fn_rva)
            exports.append((nm, fn_rva))
    else:
        if exp_rva != 0 or exp_size != 0:
            raise ValidationError(f"expected empty Export Directory for 0-export DLL, got (0x{exp_rva:x}, {exp_size})")

    # Parse .reloc (DataDirectory[5])
    rel_rva, rel_size = data_dirs[5]
    reloc_rvas = []
    if expect_relocs or rel_size > 0:
        if rel_rva == 0 or rel_size < 8:
            raise ValidationError(f"expected non-empty Base Relocation Directory, got (0x{rel_rva:x}, {rel_size})")
        if ".reloc" not in sec_by_name:
            raise ValidationError("expected .reloc section")
        rsec = sec_by_name[".reloc"]
        req_reloc_chars = IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_DISCARDABLE
        if (rsec["chars"] & req_reloc_chars) != req_reloc_chars:
            raise ValidationError(f".reloc missing expected characteristics: 0x{rsec['chars']:08x}")
        if rsec["chars"] & (IMAGE_SCN_MEM_WRITE | IMAGE_SCN_MEM_EXECUTE):
            raise ValidationError(f".reloc violates W^X: 0x{rsec['chars']:08x}")

        pos = rva_to_file_offset(sections, rel_rva)
        end = pos + rel_size
        prev_page = -1
        while pos < end:
            if pos + 8 > end:
                raise ValidationError("truncated base relocation block header")
            page_rva, blk_size = struct.unpack_from("<II", data, pos)
            if blk_size < 8 or (blk_size % 4) != 0 or pos + blk_size > end:
                raise ValidationError(f"invalid base relocation SizeOfBlock {blk_size} at page 0x{page_rva:x}")
            if (page_rva & 0xFFF) != 0 or page_rva <= prev_page:
                raise ValidationError(f"unsorted or unaligned PageRVA 0x{page_rva:x} (prev 0x{prev_page:x})")
            prev_page = page_rva

            num_entries = (blk_size - 8) // 2
            entries = struct.unpack_from(f"<{num_entries}H", data, pos + 8)
            prev_off = -1
            saw_pad = False
            for ent in entries:
                rtype = (ent >> 12) & 0xF
                roff = ent & 0xFFF
                if rtype == IMAGE_REL_BASED_ABSOLUTE:
                    saw_pad = True
                elif rtype == IMAGE_REL_BASED_DIR64:
                    if saw_pad:
                        raise ValidationError("DIR64 entry appeared after ABSOLUTE alignment pad")
                    if roff <= prev_off:
                        raise ValidationError(f"unsorted DIR64 offset 0x{roff:x} <= 0x{prev_off:x}")
                    prev_off = roff
                    reloc_rvas.append(page_rva + roff)
                else:
                    raise ValidationError(f"unexpected base relocation type {rtype}")
            pos += blk_size

        if expect_relocs and not reloc_rvas:
            raise ValidationError("expected at least one IMAGE_REL_BASED_DIR64 relocation")

    return {
        "sections": sections,
        "exports": exports,
        "reloc_rvas": reloc_rvas,
        "entry_rva": entry_rva,
    }


def parse_companion_implib(data: bytes):
    """Validates a generated COFF Short-Import `.lib` archive and returns its short-import members."""
    if len(data) < 8 or data[:8] != b"!<arch>\n":
        raise ValidationError("companion .lib missing !<arch>\\n signature")

    pos = 8
    members = []
    while pos < len(data):
        hdr = data[pos : pos + 60]
        if len(hdr) < 60 or hdr[58:60] != b"`\n":
            raise ValidationError(f"invalid archive member header at {pos}")
        if hdr[16:28] != b"0           " or hdr[28:34] != b"0     " or hdr[34:40] != b"0     " or hdr[40:48] != b"0       ":
            raise ValidationError(f"non-zero archive member metadata at {pos}: {hdr[16:48]!r}")
        sz = int(hdr[48:58].decode("ascii").strip())
        body = data[pos + 60 : pos + 60 + sz]
        name = hdr[0:16].decode("ascii", errors="replace").rstrip(" ")
        members.append((pos, name, body))
        pos += 60 + sz + (sz & 1)

    if len(members) < 2 or members[0][1] != "/" or members[1][1] != "/":
        raise ValidationError("companion .lib missing First and Second Linker Members")

    # Parse Second Linker Member symbol names
    b2 = members[1][2]
    (num_mems,) = struct.unpack_from("<I", b2, 0)
    (num_syms,) = struct.unpack_from("<I", b2, 4 + num_mems * 4)
    str_start = 8 + num_mems * 4 + num_syms * 2
    raw_strs = b2[str_start:].split(b"\x00")
    if raw_strs and raw_strs[-1] == b"":
        raw_strs.pop()
    archive_syms = [s.decode("ascii") for s in raw_strs]
    if archive_syms != sorted(archive_syms):
        raise ValidationError(f"Second Linker Member symbols not sorted: {archive_syms}")

    short_imports = {}
    for _, mname, body in members[2:]:
        if mname == "//":
            continue
        if len(body) < 20:
            raise ValidationError("short import member < 20 bytes")
        sig1, sig2, ver, mach, ts, sz_data, hint, type_word = struct.unpack_from("<HHHHIIHH", body, 0)
        if sig1 != 0x0000 or sig2 != 0xFFFF or mach != IMAGE_FILE_MACHINE_AMD64 or ts != 0:
            raise ValidationError(f"bad short import header: sig=({sig1:#x},{sig2:#x}), mach={mach:#x}, ts={ts}")
        payload = body[20 : 20 + sz_data]
        parts = payload.split(b"\x00")
        sym_name = parts[0].decode("ascii")
        dll_name = parts[1].decode("ascii")
        imp_type = type_word & 0x3
        name_type = (type_word >> 2) & 0x7
        short_imports[sym_name] = {
            "dll": dll_name,
            "hint": hint,
            "imp_type": imp_type,
            "name_type": name_type,
        }

    return {"archive_syms": archive_syms, "short_imports": short_imports}


def main():
    if len(sys.argv) < 4:
        print("usage: pe_dll_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    objdump_tool = find_tool(["objdump", "llvm-objdump"])
    ar_tool = find_tool(["llvm-ar", "ar"])
    nm_tool = find_tool(["llvm-nm", "nm"])
    gcc_tool = find_tool(["gcc", "clang"])

    # =========================================================================
    # 1. Build Axiom `mathdll.dll` + `mathdll.lib` (functions + scalar/array/Str data)
    # =========================================================================
    mathdll_ax = tmp_dir / "mathdll.ax"
    mathdll_ax.write_text(
        """\
module mathdll

pub fn internal_helper(x: i32) -> i32 {
    x + 100
}

@export
pub fn dll_add(a: i32, b: i32) -> i32 {
    a + b
}

@export("dll_custom_mul")
pub fn mul_impl(a: i32, b: i32) -> i32 {
    a * b
}

@export
pub fn dll_print_hello() {
    print("Xin chào thế giới\\n");
}

@export
pub const DLL_MAGIC_I32: i32 = 1337;

@export("DLL_WEIGHTS")
pub const RAW_WEIGHTS: [4]i32 = [10, 20, 30, 40];

@export
pub const DLL_GREETING_STR: Str = "Xin chào từ DLL\\n";
""",
        encoding="utf-8",
    )

    dll_1 = tmp_dir / "mathdll.dll"
    lib_1 = tmp_dir / "mathdll.lib"
    sub_det = tmp_dir / "det_repeat"
    sub_det.mkdir(parents=True, exist_ok=True)
    dll_2 = sub_det / "mathdll.dll"
    lib_2 = sub_det / "mathdll.lib"

    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(dll_1), str(mathdll_ax)])
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(dll_2), str(mathdll_ax)])

    if not dll_1.is_file() or not lib_1.is_file():
        raise ValidationError("`build --kind dll` did not emit both mathdll.dll and companion mathdll.lib")
    if dll_1.read_bytes() != dll_2.read_bytes():
        raise ValidationError("mathdll.dll is not byte-for-byte deterministic across runs")
    if lib_1.read_bytes() != lib_2.read_bytes():
        raise ValidationError("companion mathdll.lib is not byte-for-byte deterministic across runs")

    pe_info = parse_and_validate_pe_dll(
        dll_1.read_bytes(),
        expected_dll_name="mathdll.dll",
        expect_exports=True,
        expect_relocs=True,
    )
    export_names = [nm for nm, _ in pe_info["exports"]]
    expected_exports = sorted(
        ["DLL_GREETING_STR", "DLL_MAGIC_I32", "DLL_WEIGHTS", "dll_add", "dll_custom_mul", "dll_print_hello"]
    )
    if export_names != expected_exports:
        raise ValidationError(f"expected sorted exports {expected_exports}, got {export_names}")
    if "internal_helper" in export_names:
        raise ValidationError("non-@export `pub fn internal_helper` leaked into .edata")

    # External GNU `objdump -p` & `objdump -d` verification
    od_p = run_cmd([objdump_tool, "-p", str(dll_1)]).stdout.decode("utf-8", errors="replace")
    od_d = run_cmd([objdump_tool, "-d", str(dll_1)]).stdout.decode("utf-8", errors="replace")
    if "(bad)" in od_d:
        raise ValidationError(f"objdump -d found '(bad)' instruction in mathdll.dll:\n{od_d}")
    for token in (" mathdll.dll", "DLL Name: KERNEL32.dll", "DLL_GREETING_STR", "dll_custom_mul", "DIR64"):
        if token.lower() not in od_p.lower():
            raise ValidationError(f"objdump -p missing {token!r}:\n{od_p}")
    if "internal_helper" in od_p:
        raise ValidationError(f"objdump -p unexpectedly shows non-exported internal_helper:\n{od_p}")

    # Validate companion short-import `.lib`
    imp_info = parse_companion_implib(lib_1.read_bytes())
    for fn_sym in ("dll_add", "dll_custom_mul", "dll_print_hello"):
        if imp_info["short_imports"][fn_sym]["imp_type"] != 0:
            raise ValidationError(f"expected IMPORT_OBJECT_CODE (0) for {fn_sym}")
        if fn_sym not in imp_info["archive_syms"] or f"__imp_{fn_sym}" not in imp_info["archive_syms"]:
            raise ValidationError(f"missing {fn_sym} / __imp_{fn_sym} in mathdll.lib index")
    for data_sym in ("DLL_GREETING_STR", "DLL_MAGIC_I32", "DLL_WEIGHTS"):
        if imp_info["short_imports"][data_sym]["imp_type"] != 1:
            raise ValidationError(f"expected IMPORT_OBJECT_DATA (1) for {data_sym}")
        if f"__imp_{data_sym}" not in imp_info["archive_syms"]:
            raise ValidationError(f"missing __imp_{data_sym} in mathdll.lib index")
        if data_sym in imp_info["archive_syms"]:
            raise ValidationError(f"data export {data_sym} must NOT emit bare code thunk symbol in .lib")

    run_cmd([ar_tool, "t", str(lib_1)])
    nm_out = run_cmd([nm_tool, "--print-armap", str(lib_1)]).stdout.decode("utf-8", errors="replace")
    if "__imp_DLL_MAGIC_I32" not in nm_out or "dll_custom_mul" not in nm_out:
        raise ValidationError(f"{nm_tool} --print-armap missing expected symbols:\n{nm_out}")

    # =========================================================================
    # 2. Axiom `.exe` AND C (`gcc`) `.exe` Consuming `mathdll.dll` via `mathdll.lib`
    # =========================================================================
    data_imp_bridge_c = tmp_dir / "data_imp_bridge.c"
    data_imp_bridge_c.write_text(
        """\
#include <stdint.h>
#include <stddef.h>

extern __declspec(dllimport) const int32_t DLL_MAGIC_I32;
extern __declspec(dllimport) const int32_t DLL_WEIGHTS[4];

int32_t bridge_read_imp_magic(void) {
    return DLL_MAGIC_I32;
}

int32_t bridge_read_imp_weights_sum(void) {
    return DLL_WEIGHTS[0] + DLL_WEIGHTS[1] + DLL_WEIGHTS[2] + DLL_WEIGHTS[3];
}
""",
        encoding="utf-8",
    )
    data_imp_bridge_obj = tmp_dir / "data_imp_bridge.obj"
    run_cmd([gcc_tool, "-c", "-O2", str(data_imp_bridge_c), "-o", str(data_imp_bridge_obj)])

    ax_consumer = tmp_dir / "ax_consumer.ax"
    ax_consumer.write_text(
        """\
module ax_consumer

@link("mathdll")
extern "C" {
    fn dll_add(a: i32, b: i32) -> i32;
    fn dll_custom_mul(a: i32, b: i32) -> i32;
    fn dll_print_hello();
}

extern "C" {
    fn bridge_read_imp_magic() -> i32;
    fn bridge_read_imp_weights_sum() -> i32;
}

@link("kernel32")
extern "system" {
    fn GetModuleHandleA(name: *const u8) -> usize;
    fn GetProcAddress(hmod: usize, name: *const u8) -> usize;
}

@repr(C)
struct RawStr {
    ptr: *const u8,
    len_bytes: usize,
}

@intrinsic pub unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }

unsafe fn str_cptr(s: Str) -> *const u8 {
    let rs = *(address_of(s) as *const RawStr);
    rs.ptr
}

pub fn main() -> i32 {
    unsafe {
        dll_print_hello();
        let sum = dll_add(15, 27);                  // 42
        let prod = dll_custom_mul(6, 7);            // 42
        let magic = bridge_read_imp_magic();        // 1337 via __imp_DLL_MAGIC_I32
        let wsum = bridge_read_imp_weights_sum();   // 100 via __imp_DLL_WEIGHTS

        let hmod = GetModuleHandleA(str_cptr("mathdll.dll\\0"));
        let p_greet_addr = GetProcAddress(hmod, str_cptr("DLL_GREETING_STR\\0"));
        if hmod == 0 || p_greet_addr == 0 {
            return 2;
        }
        let g = *(p_greet_addr as *const Str);
        print(g);

        if sum == 42 && prod == 42 && magic == 1337 && wsum == 100 {
            99
        } else {
            1
        }
    }
}
""",
        encoding="utf-8",
    )
    ax_consumer_exe = tmp_dir / "ax_consumer.exe"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(ax_consumer_exe),
            "-L",
            str(tmp_dir),
            "-lmathdll",
            str(ax_consumer),
            str(data_imp_bridge_obj),
        ]
    )
    res_ax = run_cmd([str(ax_consumer_exe)], cwd=str(tmp_dir), expect_rc=99)
    expected_out = "Xin chào thế giới\nXin chào từ DLL\n".encode("utf-8")
    if res_ax.stdout != expected_out:
        raise ValidationError(f"unexpected stdout from ax_consumer.exe: {res_ax.stdout!r} != {expected_out!r}")

    # Positional `mathdll.lib` consumer check
    ax_pos_exe = tmp_dir / "ax_consumer_pos.exe"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(ax_pos_exe),
            str(ax_consumer),
            str(data_imp_bridge_obj),
            str(lib_1),
        ]
    )
    run_cmd([str(ax_pos_exe)], cwd=str(tmp_dir), expect_rc=99)

    # C (`gcc`) consumer linking `mathdll.lib` directly!
    c_consumer_c = tmp_dir / "c_consumer.c"
    c_consumer_c.write_text(
        """\
#include <stdint.h>
#include <stdio.h>
#include <string.h>

__declspec(dllimport) int32_t dll_add(int32_t a, int32_t b);
__declspec(dllimport) int32_t dll_custom_mul(int32_t a, int32_t b);
__declspec(dllimport) void dll_print_hello(void);
extern __declspec(dllimport) const int32_t DLL_MAGIC_I32;
extern __declspec(dllimport) const int32_t DLL_WEIGHTS[4];

typedef struct {
    const char *ptr;
    size_t len;
} AxStr;
extern __declspec(dllimport) const AxStr DLL_GREETING_STR;

int main(void) {
    dll_print_hello();
    int32_t s = dll_add(20, 22);
    int32_t m = dll_custom_mul(9, 5);
    int32_t w = DLL_WEIGHTS[0] + DLL_WEIGHTS[3];
    if (s != 42 || m != 45 || DLL_MAGIC_I32 != 1337 || w != 50) {
        return 2;
    }
    if (DLL_GREETING_STR.len == 0 || memcmp(DLL_GREETING_STR.ptr, "Xin ", 4) != 0) {
        return 3;
    }
    return 88;
}
""",
        encoding="utf-8",
    )
    od_lib_x = run_cmd([objdump_tool, "-x", str(lib_1)]).stdout.decode("utf-8", errors="replace")
    if "__imp_DLL_MAGIC_I32" not in od_lib_x or "__imp_dll_custom_mul" not in od_lib_x:
        raise ValidationError(f"{objdump_tool} -x on mathdll.lib missing ILF symbols:\n{od_lib_x}")
    c_consumer_exe = tmp_dir / "c_consumer.exe"
    run_cmd([gcc_tool, "-O2", str(c_consumer_c), str(dll_1), "-o", str(c_consumer_exe)])
    res_c = run_cmd([str(c_consumer_exe)], cwd=str(tmp_dir), expect_rc=88)
    if res_c.stdout != "Xin chào thế giới\n".encode("utf-8"):
        raise ValidationError(f"unexpected stdout from c_consumer.exe: {res_c.stdout!r}")

    # =========================================================================
    # 3. Third-Party C DLL Built by `gcc -shared -Wl,--out-implib` Consumed by Axiom `.exe`
    # =========================================================================
    cplug_c = tmp_dir / "cplug.c"
    cplug_c.write_text(
        """\
#include <stdint.h>

__declspec(dllexport) const int32_t cplug_magic = 314;

__declspec(dllexport) int32_t cplug_compute(int32_t a, int32_t b) {
    return a * 10 + b + 3;
}

__declspec(dllexport) int64_t cplug_sum6(int64_t a, int64_t b, int64_t c, int64_t d, int64_t e, int64_t f) {
    return a + b + c + d + e + f;
}
""",
        encoding="utf-8",
    )
    cplug_dll = tmp_dir / "cplug.dll"
    cplug_implib = tmp_dir / "libcplug.dll.a"
    run_cmd([gcc_tool, "-shared", "-O2", str(cplug_c), "-o", str(cplug_dll), f"-Wl,--out-implib,{cplug_implib}"])

    cplug_bridge_c = tmp_dir / "cplug_bridge.c"
    cplug_bridge_c.write_text(
        """\
#include <stdint.h>
extern __declspec(dllimport) const int32_t cplug_magic;
int32_t read_cplug_magic(void) {
    return cplug_magic;
}
""",
        encoding="utf-8",
    )
    cplug_bridge_obj = tmp_dir / "cplug_bridge.obj"
    run_cmd([gcc_tool, "-c", "-O2", str(cplug_bridge_c), "-o", str(cplug_bridge_obj)])

    ax_use_cplug = tmp_dir / "ax_use_cplug.ax"
    ax_use_cplug.write_text(
        """\
module ax_use_cplug

extern "C" {
    fn cplug_compute(a: i32, b: i32) -> i32;
    fn cplug_sum6(a: i64, b: i64, c: i64, d: i64, e: i64, f: i64) -> i64;
    fn read_cplug_magic() -> i32;
}

pub fn main() -> i32 {
    unsafe {
        let v1 = cplug_compute(4, 5);                   // 48
        let v2 = cplug_sum6(1, 2, 3, 4, 5, 6) as i32;   // 21
        let mg = read_cplug_magic();                    // 314 via __imp_cplug_magic
        if v1 == 48 && v2 == 21 && mg == 314 {
            69
        } else {
            1
        }
    }
}
""",
        encoding="utf-8",
    )
    ax_use_cplug_exe = tmp_dir / "ax_use_cplug.exe"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(ax_use_cplug_exe),
            "-L",
            str(tmp_dir),
            "-lcplug.dll",
            str(ax_use_cplug),
            str(cplug_bridge_obj),
        ]
    )
    od_cplug_exe = run_cmd([objdump_tool, "-p", str(ax_use_cplug_exe)]).stdout.decode("utf-8", errors="replace")
    if "cplug.dll" not in od_cplug_exe.lower():
        raise ValidationError(f"ax_use_cplug.exe missing cplug.dll in Import Table:\n{od_cplug_exe}")
    run_cmd([str(ax_use_cplug_exe)], cwd=str(tmp_dir), expect_rc=69)

    # =========================================================================
    # 4. Forced Base Relocation (.reloc + DYNAMIC_BASE) Verification
    # =========================================================================
    # 4a. Deterministic forced rebase of `mathdll.dll` by reserving `0x180000000` prior to `LoadLibraryA`
    force_rebase_c = tmp_dir / "force_rebase.c"
    force_rebase_c.write_text(
        """\
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef int32_t (*fn_add_t)(int32_t, int32_t);
typedef struct {
    const char *ptr;
    size_t len;
} AxStr;

int main(void) {
    void *reserved = VirtualAlloc((void *)0x180000000ULL, 0x100000, MEM_RESERVE, PAGE_NOACCESS);
    HMODULE h = LoadLibraryA("mathdll.dll");
    if (!h) {
        fprintf(stderr, "LoadLibraryA failed: %lu\\n", GetLastError());
        return 10;
    }
    uintptr_t base = (uintptr_t)h;
    if (base == 0x180000000ULL) {
        fprintf(stderr, "DLL was NOT rebased away from 0x180000000!\\n");
        return 11;
    }
    fn_add_t p_add = (fn_add_t)(void *)GetProcAddress(h, "dll_add");
    const AxStr *p_str = (const AxStr *)(const void *)GetProcAddress(h, "DLL_GREETING_STR");
    if (!p_add || !p_str) {
        return 12;
    }
    if (p_add(19, 23) != 42) {
        return 13;
    }
    /* `p_str->ptr` came from an `IMAGE_REL_AMD64_ADDR64` fixup in `.rdata`; if `.reloc` was
       missing or wrong, `p_str->ptr` would still point near unmapped `0x180000000` and crash! */
    uintptr_t str_addr = (uintptr_t)p_str->ptr;
    if (str_addr < base || str_addr >= base + 0x100000) {
        fprintf(stderr, "DLL_GREETING_STR.ptr (%p) not rebased into module (%p)\\n", (void *)str_addr, (void *)base);
        return 14;
    }
    DWORD written = 0;
    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), p_str->ptr, (DWORD)p_str->len, &written, NULL);
    FreeLibrary(h);
    if (reserved) {
        VirtualFree(reserved, 0, MEM_RELEASE);
    }
    return 42;
}
""",
        encoding="utf-8",
    )
    force_rebase_exe = tmp_dir / "force_rebase.exe"
    run_cmd([gcc_tool, "-O2", str(force_rebase_c), "-o", str(force_rebase_exe)])
    res_reb = run_cmd([str(force_rebase_exe)], cwd=str(tmp_dir), expect_rc=42)
    if res_reb.stdout != "Xin chào từ DLL\n".encode("utf-8"):
        raise ValidationError(f"unexpected rebased DLL_GREETING_STR output: {res_reb.stdout!r}")

    # 4b. Simultaneous load of two Axiom DLLs (`reloc_a.dll` & `reloc_b.dll`, both ImageBase=0x180000000)
    for tag, msg, num in [("a", "Alpha-Rebased\\n", 17), ("b", "Beta-Rebased\\n", 25)]:
        src_p = tmp_dir / f"reloc_{tag}.ax"
        src_p.write_text(
            f"""\
module reloc_{tag}

@export
pub const BANNER_{tag.upper()}: Str = "{msg}";

@export
pub fn run_{tag}() -> i32 {{
    print(BANNER_{tag.upper()});
    {num}
}}
""",
            encoding="utf-8",
        )
        run_cmd(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                "--kind",
                "dll",
                "-o",
                str(tmp_dir / f"reloc_{tag}.dll"),
                str(src_p),
            ]
        )

    reloc_host_ax = tmp_dir / "reloc_host.ax"
    reloc_host_ax.write_text(
        """\
module reloc_host

@link("reloc_a")
extern "C" {
    fn run_a() -> i32;
}

@link("reloc_b")
extern "C" {
    fn run_b() -> i32;
}

@link("kernel32")
extern "system" {
    fn GetModuleHandleA(name: *const u8) -> usize;
}

@repr(C)
struct RawStr {
    ptr: *const u8,
    len_bytes: usize,
}

@intrinsic pub unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }

unsafe fn str_cptr(s: Str) -> *const u8 {
    let rs = *(address_of(s) as *const RawStr);
    rs.ptr
}

pub fn main() -> i32 {
    unsafe {
        let ha = GetModuleHandleA(str_cptr("reloc_a.dll\\0"));
        let hb = GetModuleHandleA(str_cptr("reloc_b.dll\\0"));
        if ha == 0 || hb == 0 || ha == hb {
            return 2;
        }
        let pref: usize = 6442450944; // 0x180000000
        if ha == pref && hb == pref {
            return 3;
        }
        run_a() + run_b() // 17 + 25 = 42
    }
}
""",
        encoding="utf-8",
    )
    reloc_host_exe = tmp_dir / "reloc_host.exe"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "-o",
            str(reloc_host_exe),
            "-L",
            str(tmp_dir),
            str(reloc_host_ax),
        ]
    )
    res_dual = run_cmd([str(reloc_host_exe)], cwd=str(tmp_dir), expect_rc=42)
    if res_dual.stdout != b"Alpha-Rebased\nBeta-Rebased\n":
        raise ValidationError(f"unexpected dual-DLL stdout: {res_dual.stdout!r}")

    # =========================================================================
    # 5. `_DllMainCRTStartup`: Empty DLL, Data-Only DLL, `@entry`, `__ax_resolve_module_bindings`
    # =========================================================================
    empty_ax = tmp_dir / "empty_dll.ax"
    empty_ax.write_text("module empty_dll\n", encoding="utf-8")
    empty_dll = tmp_dir / "empty_dll.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(empty_dll), str(empty_ax)])
    parse_and_validate_pe_dll(empty_dll.read_bytes(), "empty_dll.dll", expect_exports=False, expect_relocs=False)

    data_only_ax = tmp_dir / "data_only.ax"
    data_only_ax.write_text("module data_only\n@export\npub const ONLY_DATA: i32 = 777;\n", encoding="utf-8")
    data_only_dll = tmp_dir / "data_only.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(data_only_dll), str(data_only_ax)])
    parse_and_validate_pe_dll(data_only_dll.read_bytes(), "data_only.dll", expect_exports=True, expect_relocs=False)

    entry_ok_ax = tmp_dir / "entry_ok.ax"
    entry_ok_ax.write_text(
        """\
module entry_ok

fn __ax_resolve_module_bindings() -> bool {
    true
}

@entry
fn my_dll_entry(hinst: usize, reason: u32, reserved: *const u8) -> bool {
    let _ = reserved;
    if reason == 1u32 {
        print("ATTACH-OK\\n");
        return hinst != 0;
    }
    if reason == 0u32 {
        print("DETACH-OK\\n");
    }
    true
}

@export
pub fn ping() -> i32 {
    55
}
""",
        encoding="utf-8",
    )
    entry_ok_dll = tmp_dir / "entry_ok.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(entry_ok_dll), str(entry_ok_ax)])

    entry_fail_ax = tmp_dir / "entry_fail.ax"
    entry_fail_ax.write_text(
        """\
module entry_fail

@entry
fn fail_attach() -> bool {
    false
}

@export
pub fn never_reached() -> i32 {
    1
}
""",
        encoding="utf-8",
    )
    entry_fail_dll = tmp_dir / "entry_fail.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(entry_fail_dll), str(entry_fail_ax)])

    bind_fail_ax = tmp_dir / "bind_fail.ax"
    bind_fail_ax.write_text(
        """\
module bind_fail

fn __ax_resolve_module_bindings() -> bool {
    false
}

@entry
fn should_not_run() -> bool {
    print("MUST-NOT-RUN\\n");
    true
}
""",
        encoding="utf-8",
    )
    bind_fail_dll = tmp_dir / "bind_fail.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(bind_fail_dll), str(bind_fail_ax)])

    loader_probe_c = tmp_dir / "loader_probe.c"
    loader_probe_c.write_text(
        """\
#include <windows.h>
#include <stdint.h>

typedef int32_t (*ping_fn)(void);

int main(void) {
    HMODULE h_empty = LoadLibraryA("empty_dll.dll");
    if (!h_empty) return 21;
    FreeLibrary(h_empty);

    HMODULE h_data = LoadLibraryA("data_only.dll");
    if (!h_data) return 22;
    const int32_t *p_val = (const int32_t *)(const void *)GetProcAddress(h_data, "ONLY_DATA");
    if (!p_val || *p_val != 777) return 23;
    FreeLibrary(h_data);

    HMODULE h_ok = LoadLibraryA("entry_ok.dll");
    if (!h_ok) return 24;
    ping_fn p_ping = (ping_fn)(void *)GetProcAddress(h_ok, "ping");
    if (!p_ping || p_ping() != 55) return 25;
    FreeLibrary(h_ok);

    HMODULE h_fail = LoadLibraryA("entry_fail.dll");
    if (h_fail != NULL) return 26;

    HMODULE h_bfail = LoadLibraryA("bind_fail.dll");
    if (h_bfail != NULL) return 27;

    return 0;
}
""",
        encoding="utf-8",
    )
    loader_probe_exe = tmp_dir / "loader_probe.exe"
    run_cmd([gcc_tool, "-O2", str(loader_probe_c), "-o", str(loader_probe_exe)])
    res_lp = run_cmd([str(loader_probe_exe)], cwd=str(tmp_dir), expect_rc=0)
    if res_lp.stdout != b"ATTACH-OK\nDETACH-OK\n":
        raise ValidationError(f"unexpected lifecycle stdout: {res_lp.stdout!r}")

    # =========================================================================
    # 6. `--implib`, `axiom.toml` `kind = "dll"`, C `.obj` `.drectve`, and Diagnostics
    # =========================================================================
    # 6a. `--implib <custom_path>`
    custom_dir = tmp_dir / "custom_implib"
    custom_dir.mkdir(parents=True, exist_ok=True)
    custom_dll = custom_dir / "plug.dll"
    custom_lib = custom_dir / "my_custom_plug_imp.lib"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "--kind",
            "dll",
            "--implib",
            str(custom_lib),
            "-o",
            str(custom_dll),
            str(mathdll_ax),
        ]
    )
    if not custom_lib.is_file() or (custom_dir / "plug.lib").exists():
        raise ValidationError("--implib did not redirect companion import library exclusively to custom path")

    # 6b. `axiom.toml` with `kind = "dll"` + `axiomc run` rejection (`AX_DRIVER_USAGE`, exit 2)
    pkg_dll_dir = tmp_dir / "pkg_dll_proj"
    (pkg_dll_dir / "src").mkdir(parents=True, exist_ok=True)
    (pkg_dll_dir / "axiom.toml").write_text(
        '[package]\nname = "pkg_dll_proj"\nversion = "0.1.0"\nkind = "dll"\n',
        encoding="utf-8",
    )
    (pkg_dll_dir / "src" / "lib.ax").write_text(
        "module pkg_dll_proj\n@export\npub fn pkg_api() -> i32 { 64 }\n",
        encoding="utf-8",
    )
    pkg_out_dir = tmp_dir / "pkg_dll_out"
    pkg_out_dir.mkdir(parents=True, exist_ok=True)
    run_cmd([compiler, "build", "--std-root", str(std_root), str(pkg_dll_dir)], cwd=str(pkg_out_dir))
    if not (pkg_out_dir / "pkg_dll_proj.dll").is_file() or not (pkg_out_dir / "pkg_dll_proj.lib").is_file():
        raise ValidationError("package manifest `kind = 'dll'` did not emit pkg_dll_proj.dll + pkg_dll_proj.lib")

    p_run_pkg = run_cmd([compiler, "run", "--std-root", str(std_root), str(pkg_dll_dir)], expect_rc=2)
    if b"AX_DRIVER_USAGE" not in p_run_pkg.stderr:
        raise ValidationError(f"expected AX_DRIVER_USAGE for `axiomc run <dll_pkg>`, got:\n{p_run_pkg.stderr!r}")

    # 6c. Merging C `.obj` `.drectve` (`__declspec(dllexport)`) into `axiomc build --kind dll`
    c_part_c = tmp_dir / "c_part.c"
    c_part_c.write_text(
        "__declspec(dllexport) int c_drectve_fn(int x) { return x + 9; }\n",
        encoding="utf-8",
    )
    c_part_obj = tmp_dir / "c_part.obj"
    run_cmd([gcc_tool, "-c", "-O2", str(c_part_c), "-o", str(c_part_obj)])
    mixed_dll = tmp_dir / "mixed_c_ax.dll"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "--kind",
            "dll",
            "-o",
            str(mixed_dll),
            str(mathdll_ax),
            str(c_part_obj),
        ]
    )
    mixed_info = parse_and_validate_pe_dll(mixed_dll.read_bytes(), "mixed_c_ax.dll", expect_exports=True)
    mixed_names = [nm for nm, _ in mixed_info["exports"]]
    if "c_drectve_fn" not in mixed_names or "dll_add" not in mixed_names:
        raise ValidationError(f"expected both C .drectve and Axiom @export symbols in mixed DLL: {mixed_names}")

    # 6d. Negative diagnostic: `AX_LINK_DUPLICATE_EXPORT` (`check` and `build --json`)
    dup_exp_ax = tmp_dir / "dup_export.ax"
    dup_exp_ax.write_text(
        """\
module dup_export

@export("same_ext_name")
pub fn first_fn() -> i32 { 1 }

@export("same_ext_name")
pub fn second_fn() -> i32 { 2 }
""",
        encoding="utf-8",
    )
    for subcmd, extra in [("check", []), ("build", ["--kind", "dll", "-o", str(tmp_dir / "dup.dll")])]:
        p_dup = run_cmd(
            [compiler, subcmd, "--std-root", str(std_root), "--json"] + extra + [str(dup_exp_ax)],
            expect_rc=1,
        )
        doc = json.loads(p_dup.stderr.decode("utf-8"))
        diags = doc.get("diagnostics", doc if isinstance(doc, list) else [])
        if not any(
            d.get("code") == "AX_LINK_DUPLICATE_EXPORT" and d.get("data", {}).get("symbol") == "same_ext_name"
            for d in diags
        ):
            raise ValidationError(f"expected AX_LINK_DUPLICATE_EXPORT(symbol='same_ext_name') in {subcmd}: {doc}")

    # Duplicate export across C `.obj` `-export:c_drectve_fn` + Axiom `@export("c_drectve_fn")`
    dup_c_ax = tmp_dir / "dup_c_ax.ax"
    dup_c_ax.write_text(
        'module dup_c_ax\n@export("c_drectve_fn")\npub fn ax_impl_for_c_clash(x: i32) -> i32 { x }\n',
        encoding="utf-8",
    )
    p_dup_c = run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "--json",
            "--kind",
            "dll",
            "-o",
            str(tmp_dir / "dup_c.dll"),
            str(dup_c_ax),
            str(c_part_obj),
        ],
        expect_rc=1,
    )
    doc_c = json.loads(p_dup_c.stderr.decode("utf-8"))
    diags_c = doc_c.get("diagnostics", doc_c if isinstance(doc_c, list) else [])
    if not any(
        d.get("code") == "AX_LINK_DUPLICATE_EXPORT" and d.get("data", {}).get("symbol") == "c_drectve_fn"
        for d in diags_c
    ):
        raise ValidationError(f"expected AX_LINK_DUPLICATE_EXPORT(symbol='c_drectve_fn') for C+Ax clash: {doc_c}")

    # 6e. Negative diagnostic: `AX_FFI_GENERIC_EXPORT` (`check` and `build --json`)
    gen_exp_ax = tmp_dir / "gen_export.ax"
    gen_exp_ax.write_text(
        """\
module gen_export

@export
pub fn generic_id<T>(x: T) -> T {
    x
}

pub fn use_it() -> i32 {
    generic_id<i32>(42)
}
""",
        encoding="utf-8",
    )
    for subcmd, extra in [("check", []), ("build", ["--kind", "dll", "-o", str(tmp_dir / "gen.dll")])]:
        p_gen = run_cmd(
            [compiler, subcmd, "--std-root", str(std_root), "--json"] + extra + [str(gen_exp_ax)],
            expect_rc=1,
        )
        doc_g = json.loads(p_gen.stderr.decode("utf-8"))
        diags_g = doc_g.get("diagnostics", doc_g if isinstance(doc_g, list) else [])
        if not any(d.get("code") == "AX_FFI_GENERIC_EXPORT" for d in diags_g):
            raise ValidationError(f"expected AX_FFI_GENERIC_EXPORT in {subcmd}: {doc_g}")

    print("PE-DLL-ORACLE ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
