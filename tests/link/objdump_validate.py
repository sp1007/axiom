#!/usr/bin/env python3
"""External COFF/PE oracle: GNU objdump structural validation of real .exe and .obj outputs (T142, ADR-0034).

Builds >= 20 existing native run tests across numeric, drop, str/UTF-8, FFI, std fs/io/process,
and multi-function programs with .rdata tables using `{compiler} build` and `{compiler} build --emit=obj`,
validates every resulting .exe and .obj with GNU `objdump`, runs each .exe to check its pinned
observable result, and verifies negative (corrupted) cases are rejected.

Python 3 standard library only. Missing `objdump` is an immediate FAIL (ADR-0034 section 7).
"""

import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_SCN_CNT_CODE = 0x00000020
IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080
IMAGE_SCN_MEM_EXECUTE = 0x20000000
IMAGE_SCN_MEM_READ = 0x40000000
IMAGE_SCN_MEM_WRITE = 0x80000000

IMAGE_SYM_CLASS_EXTERNAL = 2
IMAGE_SYM_CLASS_STATIC = 3

VALID_AMD64_RELOC_NAMES = {
    "IMAGE_REL_AMD64_ADDR64",
    "IMAGE_REL_AMD64_ADDR32NB",
    "IMAGE_REL_AMD64_REL32",
}
VALID_AMD64_RELOC_TYPES = {
    0x0001,  # IMAGE_REL_AMD64_ADDR64
    0x0003,  # IMAGE_REL_AMD64_ADDR32NB
    0x0004,  # IMAGE_REL_AMD64_REL32
}

# Base KERNEL32.dll imports emitted by the PE runtime startup / panic / print stubs.
BASE_KERNEL32 = (
    "ExitProcess",
    "GetStdHandle",
    "WriteFile",
    "SetConsoleOutputCP",
    "GetConsoleMode",
    "GetConsoleOutputCP",
)

HEAP_KERNEL32 = BASE_KERNEL32 + (
    "GetProcessHeap",
    "HeapAlloc",
    "HeapFree",
)


class ValidationError(Exception):
    pass


# Fixed list of 25 native run tests covering numeric, drop, str/UTF-8, FFI, std fs/io/process,
# and multi-function programs with .rdata tables. Expected KERNEL32.dll imports are pinned here
# from each program's known host/FFI calls, never read from compiler output.
TEST_CASES = [
    # --- Numeric (5) ---
    {
        "path": "tests/run/numeric/repro_u64_div_rem.ax",
        "category": "numeric",
        "exit": 122,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/numeric/repro_isize_usize_shift_40.ax",
        "category": "numeric",
        "exit": 35,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/numeric/int_sem/sem030_i32.ax",
        "category": "numeric",
        "exit": 32,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/numeric/int_sem/sem032_u64.ax",
        "category": "numeric",
        "exit": 81,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/numeric/qa_t140_edge_matrix.ax",
        "category": "numeric",
        "exit": 0,
        "stdout": (
            b"3 4611686018427387900\n"
            b"6148914691236517205 0\n"
            b"0 9223372036854775808\n"
            b"18446744071562067968 18446744073709551615\n"
            b"-1 -2 -1\n"
        ),
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    # --- Drop (4) ---
    {
        "path": "tests/run/drop/scalar_field_drop.ax",
        "category": "drop",
        "exit": 0,
        "stdout": b"0\n2\n1\n3\n",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/drop/reassign_scalar_drop.ax",
        "category": "drop",
        "exit": 0,
        "stdout": b"1\n7\n2\n8\n3\n",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/drop/qa_temp_drop_chained.ax",
        "category": "drop",
        "exit": 0,
        "stdout": b"S1 drop\nS2 drop\nafter\n",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/drop/qa_t141_field_read_then_move.ax",
        "category": "drop",
        "exit": 0,
        "stdout": b"1\n5\n1\n2\n2\n8\n2\n",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    # --- str / UTF-8 (4) ---
    {
        "path": "tests/run/str/hello.ax",
        "category": "str",
        "exit": 0,
        "stdout": "Xin chào thế giới\n".encode("utf-8"),
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/str/qa_unicode_mix.ax",
        "category": "str",
        "exit": 0,
        "stdout": "ascii, 1 byte: a, 2 bytes: é, 3 bytes: 中, 4 bytes: 😀\n".encode("utf-8"),
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/str/qa_multiple_prints.ax",
        "category": "str",
        "exit": 0,
        "stdout": b"Line 1\nLine 2\nLine 3",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/utf16/qa_utf16_roundtrip.ax",
        "category": "str",
        "exit": 0,
        "stdout": b"OK Utf16Roundtrip\n",
        "args": [],
        "env": {},
        "kernel32": HEAP_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/text/qa_utf8_validation.ax",
        "category": "str",
        "exit": 0,
        "stdout": b"OK Utf8Validation\n",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    # --- FFI (5) ---
    {
        "path": "tests/run/ffi/process_id.ax",
        "category": "ffi",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32 + ("GetCurrentProcessId",),
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/ffi/tick_count.ax",
        "category": "ffi",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32 + ("GetTickCount64",),
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/ffi/write_file.ax",
        "category": "ffi",
        "exit": 0,
        "stdout": "Xin chào thế giới\n".encode("utf-8"),
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/ffi/repr_c_struct.ax",
        "category": "ffi",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32 + ("GetSystemTime",),
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/ffi/qa_extern_c_multidll.ax",
        "category": "ffi",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32 + ("GetCurrentProcessId",),
        "other_imports": {"MSVCRT.DLL": ("abs", "labs")},
        "rdata_relocs": False,
    },
    # --- std fs / io / process / alloc (5) ---
    {
        "path": "tests/std/io/qa_io_print.ax",
        "category": "std",
        "exit": 0,
        "stdout": "Xin chào thế giới\nXin chào thế giới\n".encode("utf-8"),
        "args": [],
        "env": {},
        "kernel32": HEAP_KERNEL32 + ("WriteConsoleW",),
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/io/qa_env_process.ax",
        "category": "std",
        "exit": 0,
        "stdout": "OK env_process: 2 args, arg1=xin chào, env=tiếng Việt, exe=ok\n".encode("utf-8"),
        "args": ["xin chào"],
        "env": {"AXIOM_TEST_VN": "tiếng Việt"},
        "kernel32": HEAP_KERNEL32 + (
            "WriteConsoleW",
            "GetCommandLineW",
            "LocalFree",
            "GetEnvironmentVariableW",
            "GetModuleFileNameW",
            "GetLastError",
        ),
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/io/qa_file_roundtrip.ax",
        "category": "std",
        "exit": 0,
        "stdout": b"OK file roundtrip\n",
        "args": [],
        "env": {},
        "kernel32": HEAP_KERNEL32 + (
            "ReadFile",
            "CreateFileW",
            "CloseHandle",
            "GetFileSizeEx",
            "SetFilePointer",
            "GetEnvironmentVariableW",
            "SetEnvironmentVariableW",
            "DeleteFileA",
            "GetLastError",
        ),
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/fs/qa_binary_file_buf.ax",
        "category": "std",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": HEAP_KERNEL32 + (
            "CreateFileW",
            "CloseHandle",
            "CreateDirectoryW",
            "DeleteFileW",
            "RemoveDirectoryW",
            "FindFirstFileW",
            "FindNextFileW",
            "FindClose",
            "GetEnvironmentVariableW",
            "SetEnvironmentVariableW",
            "GetLastError",
            "ReadFile",
            "GetFileSizeEx",
        ),
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/fs/qa_time_clock.ax",
        "category": "std",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32 + (
            "QueryPerformanceCounter",
            "QueryPerformanceFrequency",
        ),
        "rdata_relocs": False,
    },
    {
        "path": "tests/std/alloc/qa_heap_ffi.ax",
        "category": "std",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": HEAP_KERNEL32 + ("HeapReAlloc",),
        "rdata_relocs": False,
    },
    # --- Multi-function programs with .rdata tables (3) ---
    {
        "path": "tests/std/core/qa_hash_vectors.ax",
        "category": "rdata_table",
        "exit": 0,
        "stdout": b"AXH64 VECTORS PASS\n",
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/native_const/table_4kb.ax",
        "category": "rdata_table",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
    {
        "path": "tests/run/native_const/qa_table_str_empty_and_multitables.ax",
        "category": "rdata_table",
        "exit": 0,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": True,
    },
    {
        "path": "tests/driver/fixtures/nontrivial_self_contained.ax",
        "category": "rdata_table",
        "exit": 42,
        "stdout": None,
        "args": [],
        "env": {},
        "kernel32": BASE_KERNEL32,
        "rdata_relocs": False,
    },
]


def run_objdump(objdump_bin, args, target_path):
    cmd = [objdump_bin] + list(args) + [str(target_path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = res.stdout.decode("utf-8", "replace")
    err = res.stderr.decode("utf-8", "replace")
    combined = (out + "\n" + err).lower()
    if res.returncode != 0:
        raise ValidationError(
            f"objdump {' '.join(args)} {target_path} exited {res.returncode}: {err.strip() or out.strip()}"
        )
    if "file format not recognized" in combined:
        raise ValidationError(
            f"objdump reported 'file format not recognized' for {target_path}"
        )
    return out


def parse_objdump_sections(text):
    """Parse the `Sections:` table from `objdump -x` output.
    Returns dict: name -> {'size': int, 'vma': int, 'file_off': int, 'flags': set[str]}.
    """
    sections = {}
    lines = text.splitlines()
    in_sections = False
    i = 0
    row_re = re.compile(
        r"^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+2\*\*\d+"
    )
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "Sections:":
            in_sections = True
            i += 1
            continue
        if in_sections:
            if ln.startswith("SYMBOL TABLE:") or ln.startswith("RELOCATION RECORDS"):
                break
            m = row_re.match(ln)
            if m:
                name = m.group(1)
                size = int(m.group(2), 16)
                vma = int(m.group(3), 16)
                file_off = int(m.group(5), 16)
                flags = set()
                if i + 1 < len(lines):
                    flag_line = lines[i + 1].strip()
                    if flag_line and not row_re.match(lines[i + 1]):
                        flags = {f.strip() for f in flag_line.split(",") if f.strip()}
                        i += 1
                sections[name] = {
                    "size": size,
                    "vma": vma,
                    "file_off": file_off,
                    "flags": flags,
                }
        i += 1
    return sections


def read_raw_section_characteristics(path, is_pe_exe):
    """Read raw IMAGE_SECTION_HEADER.Characteristics from a PE .exe or COFF .obj."""
    data = Path(path).read_bytes()
    if is_pe_exe:
        if len(data) < 64 or data[:2] != b"MZ":
            raise ValidationError(f"{path}: missing MZ header")
        pe_off = struct.unpack_from("<I", data, 0x3C)[0]
        if pe_off + 24 > len(data) or data[pe_off:pe_off + 4] != b"PE\x00\x00":
            raise ValidationError(f"{path}: missing PE\\0\\0 signature")
        coff_off = pe_off + 4
    else:
        coff_off = 0
        if len(data) < 20:
            raise ValidationError(f"{path}: file too short for COFF header")

    machine, num_sections, _ts, _sym_ptr, _num_syms, opt_hdr_size, _chars = struct.unpack_from(
        "<HHIIIHH", data, coff_off
    )
    if machine != IMAGE_FILE_MACHINE_AMD64:
        raise ValidationError(f"{path}: unexpected machine 0x{machine:04x}")

    sec_table_off = coff_off + 20 + opt_hdr_size
    result = {}
    for s in range(num_sections):
        off = sec_table_off + s * 40
        if off + 40 > len(data):
            raise ValidationError(f"{path}: truncated section header {s}")
        raw_name = data[off:off + 8]
        name = raw_name.split(b"\x00", 1)[0].decode("ascii", "replace")
        chars = struct.unpack_from("<I", data, off + 36)[0]
        result[name] = chars
    return result


def check_section_characteristics(path, sections, raw_chars, is_pe_exe):
    if ".text" not in sections or ".text" not in raw_chars:
        raise ValidationError(f"{path}: missing .text section")

    # 1. .text: CODE | EXECUTE | READ and NOT WRITE
    text_flags = sections[".text"]["flags"]
    if "CODE" not in text_flags or "READONLY" not in text_flags or "DATA" in text_flags:
        raise ValidationError(
            f"{path}: .text objdump flags invalid: {sorted(text_flags)} (expected CODE and READONLY, not DATA)"
        )
    tc = raw_chars[".text"]
    req_text = IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ
    if (tc & req_text) != req_text:
        raise ValidationError(
            f"{path}: .text Characteristics 0x{tc:08x} missing CODE|EXECUTE|READ (0x{req_text:08x})"
        )
    if tc & IMAGE_SCN_MEM_WRITE:
        raise ValidationError(
            f"{path}: .text Characteristics 0x{tc:08x} must NOT have WRITE"
        )

    # 2. .rdata (when present): READ only (not WRITE, not EXECUTE, not CODE)
    if ".rdata" in sections or ".rdata" in raw_chars:
        if ".rdata" not in sections or ".rdata" not in raw_chars:
            raise ValidationError(f"{path}: .rdata inconsistent between objdump and header")
        rdata_flags = sections[".rdata"]["flags"]
        if "READONLY" not in rdata_flags or "DATA" not in rdata_flags or "CODE" in rdata_flags:
            raise ValidationError(
                f"{path}: .rdata objdump flags invalid: {sorted(rdata_flags)} (expected READONLY and DATA, not CODE)"
            )
        rc = raw_chars[".rdata"]
        if not (rc & IMAGE_SCN_MEM_READ):
            raise ValidationError(f"{path}: .rdata Characteristics 0x{rc:08x} missing READ")
        if rc & (IMAGE_SCN_MEM_WRITE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_CNT_CODE):
            raise ValidationError(
                f"{path}: .rdata Characteristics 0x{rc:08x} must be READ only (has WRITE/EXECUTE/CODE)"
            )

    # 3. .data (when present): READ | WRITE and NOT EXECUTE (not CODE)
    if ".data" in sections or ".data" in raw_chars:
        if ".data" not in sections or ".data" not in raw_chars:
            raise ValidationError(f"{path}: .data inconsistent between objdump and header")
        data_flags = sections[".data"]["flags"]
        if "DATA" not in data_flags or "READONLY" in data_flags or "CODE" in data_flags:
            raise ValidationError(
                f"{path}: .data objdump flags invalid: {sorted(data_flags)} (expected DATA without READONLY/CODE)"
            )
        dc = raw_chars[".data"]
        req_data = IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE
        if (dc & req_data) != req_data:
            raise ValidationError(
                f"{path}: .data Characteristics 0x{dc:08x} missing READ|WRITE"
            )
        if dc & (IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_CNT_CODE):
            raise ValidationError(
                f"{path}: .data Characteristics 0x{dc:08x} must NOT have EXECUTE/CODE"
            )

    # 4. .pdata / .xdata (when present): READ only (not WRITE, not EXECUTE, not CODE)
    for ro_sec in (".pdata", ".xdata"):
        if ro_sec in sections or ro_sec in raw_chars:
            if ro_sec not in sections or ro_sec not in raw_chars:
                raise ValidationError(f"{path}: {ro_sec} inconsistent between objdump and header")
            ro_flags = sections[ro_sec]["flags"]
            if "READONLY" not in ro_flags or "DATA" not in ro_flags or "CODE" in ro_flags:
                raise ValidationError(
                    f"{path}: {ro_sec} objdump flags invalid: {sorted(ro_flags)} (expected READONLY and DATA, not CODE)"
                )
            roc = raw_chars[ro_sec]
            if not (roc & IMAGE_SCN_MEM_READ):
                raise ValidationError(f"{path}: {ro_sec} Characteristics 0x{roc:08x} missing READ")
            if roc & (IMAGE_SCN_MEM_WRITE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_CNT_CODE):
                raise ValidationError(
                    f"{path}: {ro_sec} Characteristics 0x{roc:08x} must be READ only (has WRITE/EXECUTE/CODE)"
                )


def check_disassembly_no_bad(path, text):
    if "Disassembly of section .text:" not in text:
        raise ValidationError(f"{path}: missing 'Disassembly of section .text:' in objdump -d")
    bad_lines = []
    instr_count = 0
    in_disasm = False
    for ln in text.splitlines():
        if ln.startswith("Disassembly of section "):
            in_disasm = True
            continue
        if not in_disasm:
            continue
        if "(bad)" in ln:
            bad_lines.append(ln.strip())
        if re.match(r"^\s*[0-9a-fA-F]+:\s+[0-9a-fA-F]{2}\b", ln):
            instr_count += 1
    if bad_lines:
        raise ValidationError(
            f"{path}: {len(bad_lines)} '(bad)' instruction(s) in disassembly; first: {bad_lines[0]}"
        )
    if instr_count == 0:
        raise ValidationError(f"{path}: disassembly contains 0 instructions")


def parse_pe_imports(text):
    """Parse `The Import Tables` from `objdump -p` / `objdump -x`.
    Returns dict: dll_name_upper -> set of function names.
    """
    imports = {}
    cur_dll = None
    dll_re = re.compile(r"^\s*DLL Name:\s*(\S+)\s*$", re.IGNORECASE)
    mem_re = re.compile(r"^\s*[0-9a-fA-F]+\s+<none>\s+[0-9a-fA-F]+\s+(\S+)")
    for ln in text.splitlines():
        m_dll = dll_re.match(ln)
        if m_dll:
            cur_dll = m_dll.group(1).upper()
            imports.setdefault(cur_dll, set())
            continue
        if cur_dll is not None:
            if ln.strip() == "" and imports.get(cur_dll):
                # Keep cur_dll across blank lines until next DLL Name or section table
                pass
            if ln.startswith("Sections:") or ln.startswith("SYMBOL TABLE:"):
                cur_dll = None
                continue
            m_fn = mem_re.match(ln)
            if m_fn:
                imports[cur_dll].add(m_fn.group(1))
    return imports


def validate_exe(objdump_bin, exe_path, expected_kernel32, expected_other_imports=None):
    out_x = run_objdump(objdump_bin, ["-x"], exe_path)
    out_d = run_objdump(objdump_bin, ["-d"], exe_path)
    out_p = run_objdump(objdump_bin, ["-p"], exe_path)

    if "file format pei-x86-64" not in out_x:
        raise ValidationError(f"{exe_path}: expected 'file format pei-x86-64' in objdump -x")

    # 1. Zero (bad) lines in disassembly
    check_disassembly_no_bad(exe_path, out_d)

    # 2. Sections and Characteristics
    sections = parse_objdump_sections(out_x)
    raw_chars = read_raw_section_characteristics(exe_path, is_pe_exe=True)
    check_section_characteristics(exe_path, sections, raw_chars, is_pe_exe=True)

    # 3. Entry point inside .text and PE32+ Magic
    m_magic = re.search(r"^Magic\s+([0-9a-fA-F]+)", out_p, re.MULTILINE)
    if not m_magic or int(m_magic.group(1), 16) != 0x20B:
        raise ValidationError(f"{exe_path}: missing or invalid PE32+ Magic (expected 020b)")

    m_start = re.search(r"^start address\s+0x([0-9a-fA-F]+)", out_x, re.MULTILINE)
    m_entry = re.search(r"^AddressOfEntryPoint\s+([0-9a-fA-F]+)", out_p, re.MULTILINE)
    m_base = re.search(r"^ImageBase\s+([0-9a-fA-F]+)", out_p, re.MULTILINE)
    if not m_start or not m_entry or not m_base:
        raise ValidationError(f"{exe_path}: missing start address / AddressOfEntryPoint / ImageBase")

    start_addr = int(m_start.group(1), 16)
    entry_rva = int(m_entry.group(1), 16)
    image_base = int(m_base.group(1), 16)
    if start_addr != image_base + entry_rva:
        raise ValidationError(
            f"{exe_path}: start address 0x{start_addr:x} != ImageBase 0x{image_base:x} + AddressOfEntryPoint 0x{entry_rva:x}"
        )

    text_sec = sections[".text"]
    text_vma = text_sec["vma"]
    text_size = text_sec["size"]
    if text_size <= 0:
        raise ValidationError(f"{exe_path}: .text has size 0")
    if not (text_vma <= start_addr < text_vma + text_size):
        raise ValidationError(
            f"{exe_path}: entry point 0x{start_addr:x} is outside .text [0x{text_vma:x}, 0x{text_vma + text_size:x})"
        )

    # 4. Import table check against expected KERNEL32.dll and additional DLL functions
    imports = parse_pe_imports(out_p)
    k32_imports = imports.get("KERNEL32.DLL", set())
    if not k32_imports:
        raise ValidationError(f"{exe_path}: missing KERNEL32.dll import table in objdump -p")
    missing_k32 = [fn for fn in expected_kernel32 if fn not in k32_imports]
    if missing_k32:
        raise ValidationError(
            f"{exe_path}: missing expected KERNEL32.dll import(s): {missing_k32}; actual: {sorted(k32_imports)}"
        )
    if expected_other_imports:
        for dll_name, expected_fns in expected_other_imports.items():
            dll_key = dll_name.upper()
            dll_set = imports.get(dll_key, set())
            if not dll_set:
                raise ValidationError(f"{exe_path}: missing {dll_name} import table in objdump -p")
            missing_other = [fn for fn in expected_fns if fn not in dll_set]
            if missing_other:
                raise ValidationError(
                    f"{exe_path}: missing expected {dll_name} import(s): {missing_other}; actual: {sorted(dll_set)}"
                )


def parse_obj_symbols_and_relocs(path, out_x):
    """Parse `SYMBOL TABLE:` and `RELOCATION RECORDS FOR [<sec>]:` from `objdump -x <obj>`."""
    sym_re = re.compile(
        r"^\[\s*(\d+)\]\(sec\s+(-?\d+)\)\(fl\s+0x[0-9a-fA-F]+\)\(ty\s+\d+\)\(scl\s+(\d+)\)\s*\(nx\s+(\d+)\)\s+0x([0-9a-fA-F]+)\s+(\S+)\s*$"
    )
    rel_hdr_re = re.compile(r"^RELOCATION RECORDS FOR \[([^\]]+)\]:\s*$")
    rel_row_re = re.compile(r"^([0-9a-fA-F]+)\s+(IMAGE_REL_AMD64_\S+)\s+(\S+)\s*$")

    symbols_by_name = {}
    symbols_by_idx = {}
    relocs_by_sec = {}
    cur_rel_sec = None

    for ln in out_x.splitlines():
        m_sym = sym_re.match(ln)
        if m_sym:
            idx = int(m_sym.group(1))
            sec_num = int(m_sym.group(2))
            scl = int(m_sym.group(3))
            val = int(m_sym.group(5), 16)
            name = m_sym.group(6)
            info = {"idx": idx, "sec": sec_num, "scl": scl, "val": val, "name": name}
            symbols_by_idx[idx] = info
            symbols_by_name.setdefault(name, []).append(info)
            continue

        m_rhdr = rel_hdr_re.match(ln)
        if m_rhdr:
            cur_rel_sec = m_rhdr.group(1)
            relocs_by_sec.setdefault(cur_rel_sec, [])
            continue

        if cur_rel_sec is not None:
            if ln.startswith("Disassembly of section ") or ln.startswith("Sections:"):
                cur_rel_sec = None
                continue
            m_rel = rel_row_re.match(ln)
            if m_rel:
                relocs_by_sec[cur_rel_sec].append(
                    {
                        "offset": int(m_rel.group(1), 16),
                        "type": m_rel.group(2),
                        "target": m_rel.group(3),
                    }
                )

    return symbols_by_idx, symbols_by_name, relocs_by_sec


def validate_raw_coff_relocs_and_symbols(obj_path):
    """Verify binary COFF symbol table and relocation records directly."""
    data = Path(obj_path).read_bytes()
    if len(data) < 20:
        raise ValidationError(f"{obj_path}: file too short for COFF header")
    machine, num_sections, _ts, sym_ptr, num_syms, opt_hdr_size, _chars = struct.unpack_from(
        "<HHIIIHH", data, 0
    )
    if machine != IMAGE_FILE_MACHINE_AMD64:
        raise ValidationError(f"{obj_path}: bad machine 0x{machine:04x}")
    if num_syms == 0 or sym_ptr == 0 or sym_ptr + num_syms * 18 > len(data):
        raise ValidationError(f"{obj_path}: invalid COFF symbol table bounds")

    # Parse symbols
    syms = {}
    i = 0
    while i < num_syms:
        off = sym_ptr + i * 18
        _name_raw, value, sec_num, _sym_type, storage_class, num_aux = struct.unpack_from(
            "<8sIhHBB", data, off
        )
        syms[i] = (sec_num, storage_class, value)
        i += 1 + num_aux

    # Parse section headers & relocations
    raw_reloc_counts = {}
    sec_table_off = 20 + opt_hdr_size
    for s in range(num_sections):
        sh_off = sec_table_off + s * 40
        raw_name = data[sh_off:sh_off + 8].split(b"\x00", 1)[0].decode("ascii", "replace")
        raw_size, _raw_ptr, rel_ptr, _ln_ptr, num_rels, _num_ln, _chars = struct.unpack_from(
            "<IIIIHHI", data, sh_off + 16
        )
        raw_reloc_counts[raw_name] = num_rels
        for r in range(num_rels):
            r_off = rel_ptr + r * 10
            if r_off + 10 > len(data):
                raise ValidationError(f"{obj_path}: truncated relocation {r} in {raw_name}")
            vaddr, sym_idx, rtype = struct.unpack_from("<IIH", data, r_off)
            if rtype not in VALID_AMD64_RELOC_TYPES:
                raise ValidationError(
                    f"{obj_path}: relocation in {raw_name} at 0x{vaddr:x} has unsupported COFF type 0x{rtype:04x}"
                )
            if vaddr >= raw_size:
                raise ValidationError(
                    f"{obj_path}: relocation offset 0x{vaddr:x} out of bounds for {raw_name} (size 0x{raw_size:x})"
                )
            if sym_idx not in syms:
                raise ValidationError(
                    f"{obj_path}: relocation in {raw_name} references out-of-range symbol index {sym_idx} (num_syms={num_syms})"
                )
            sec_num, storage_class, _val = syms[sym_idx]
            is_defined = 1 <= sec_num <= num_sections
            is_external = sec_num == 0 and storage_class == IMAGE_SYM_CLASS_EXTERNAL
            if not (is_defined or is_external):
                raise ValidationError(
                    f"{obj_path}: relocation target sym[{sym_idx}] in {raw_name} is neither defined (sec={sec_num}) nor external (scl={storage_class})"
                )
    return raw_reloc_counts


def validate_obj(objdump_bin, obj_path, expect_rdata_relocs=False):
    out_x = run_objdump(objdump_bin, ["-x"], obj_path)
    out_d = run_objdump(objdump_bin, ["-d"], obj_path)

    if "file format pe-x86-64" not in out_x:
        raise ValidationError(f"{obj_path}: expected 'file format pe-x86-64' in objdump -x")

    # 1. Zero (bad) lines in disassembly
    check_disassembly_no_bad(obj_path, out_d)

    # 2. Sections and Characteristics
    sections = parse_objdump_sections(out_x)
    raw_chars = read_raw_section_characteristics(obj_path, is_pe_exe=False)
    check_section_characteristics(obj_path, sections, raw_chars, is_pe_exe=False)

    # 3. Symbols and relocation targets in objdump -x
    num_sections = len(sections)
    symbols_by_idx, symbols_by_name, relocs_by_sec = parse_obj_symbols_and_relocs(obj_path, out_x)
    if not symbols_by_idx:
        raise ValidationError(f"{obj_path}: symbol table is empty")
    if "main" not in symbols_by_name or "ax_main" not in symbols_by_name:
        raise ValidationError(f"{obj_path}: missing 'main' or 'ax_main' symbol in .obj")

    for idx, sym in symbols_by_idx.items():
        sec_num = sym["sec"]
        scl = sym["scl"]
        is_defined = 1 <= sec_num <= num_sections
        is_external = sec_num == 0 and scl == IMAGE_SYM_CLASS_EXTERNAL
        if not (is_defined or is_external):
            raise ValidationError(
                f"{obj_path}: symbol [{idx}] '{sym['name']}' has invalid (sec={sec_num}, scl={scl})"
            )

    text_relocs = relocs_by_sec.get(".text", [])
    if not text_relocs:
        raise ValidationError(f"{obj_path}: expected relocation records in .text")
    if expect_rdata_relocs and not relocs_by_sec.get(".rdata"):
        raise ValidationError(f"{obj_path}: expected relocation records in .rdata")

    for sec_name, rels in relocs_by_sec.items():
        if sec_name not in sections:
            raise ValidationError(f"{obj_path}: relocations for unknown section {sec_name}")
        sec_size = sections[sec_name]["size"]
        for rel in rels:
            if rel["type"] not in VALID_AMD64_RELOC_NAMES:
                raise ValidationError(
                    f"{obj_path}: relocation in {sec_name} at 0x{rel['offset']:x} has unexpected type {rel['type']}"
                )
            if rel["offset"] >= sec_size:
                raise ValidationError(
                    f"{obj_path}: relocation at 0x{rel['offset']:x} exceeds {sec_name} size 0x{sec_size:x}"
                )
            target = rel["target"]
            base_target = re.sub(r"[-+]0x[0-9a-fA-F]+$", "", target)
            cand = symbols_by_name.get(target) or symbols_by_name.get(base_target)
            if not cand:
                raise ValidationError(
                    f"{obj_path}: relocation in {sec_name} at 0x{rel['offset']:x} targets unknown symbol '{target}'"
                )
            valid_sym = any(
                (1 <= s["sec"] <= num_sections) or (s["sec"] == 0 and s["scl"] == IMAGE_SYM_CLASS_EXTERNAL)
                for s in cand
            )
            if not valid_sym:
                raise ValidationError(
                    f"{obj_path}: relocation target '{target}' is neither defined nor external"
                )

    # 4. Raw COFF table cross-check (and verify objdump -x relocation count matches raw header)
    raw_reloc_counts = validate_raw_coff_relocs_and_symbols(obj_path)
    for sec_name, raw_cnt in raw_reloc_counts.items():
        parsed_cnt = len(relocs_by_sec.get(sec_name, []))
        if parsed_cnt != raw_cnt:
            raise ValidationError(
                f"{obj_path}: objdump -x parsed {parsed_cnt} relocation(s) in {sec_name}, raw COFF header has {raw_cnt}"
            )


def run_negative_self_tests(objdump_bin, sample_exe, sample_obj, expected_k32, tmp_dir):
    """Mutate copies of a valid .exe and .obj and prove each corruption makes validation FAIL."""
    neg_dir = Path(tmp_dir) / "negative"
    neg_dir.mkdir(parents=True, exist_ok=True)
    exe_bytes = Path(sample_exe).read_bytes()
    obj_bytes = Path(sample_obj).read_bytes()

    # 1. Corrupted format (bad magic)
    bad_fmt = neg_dir / "bad_format.exe"
    bad_fmt.write_bytes(b"NOT_A_PE_FILE" + exe_bytes[13:])
    try:
        validate_exe(objdump_bin, bad_fmt, expected_k32)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 1 failed: corrupted format .exe passed validation")

    # 2. Invalid opcode in .text -> (bad) in objdump -d (0x06 is `push es`, invalid in 64-bit mode)
    bad_op = neg_dir / "bad_opcode.exe"
    pe_off = struct.unpack_from("<I", exe_bytes, 0x3C)[0]
    num_secs = struct.unpack_from("<H", exe_bytes, pe_off + 6)[0]
    opt_sz = struct.unpack_from("<H", exe_bytes, pe_off + 20)[0]
    sec_off = pe_off + 24 + opt_sz
    mut = bytearray(exe_bytes)
    injected = False
    for s in range(num_secs):
        off = sec_off + s * 40
        name = bytes(mut[off:off + 8]).split(b"\x00", 1)[0]
        if name == b".text":
            raw_ptr = struct.unpack_from("<I", mut, off + 20)[0]
            mut[raw_ptr:raw_ptr + 8] = b"\x06\x06\x06\x06\x06\x06\x06\x06"
            injected = True
            break
    assert injected
    bad_op.write_bytes(mut)
    try:
        validate_exe(objdump_bin, bad_op, expected_k32)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 2 failed: .exe with (bad) opcode passed validation")

    # 3. Entry point outside .text
    bad_ep = neg_dir / "bad_entry.exe"
    mut = bytearray(exe_bytes)
    struct.pack_into("<I", mut, pe_off + 24 + 16, 0x00001000)  # .rdata RVA instead of .text
    bad_ep.write_bytes(mut)
    try:
        validate_exe(objdump_bin, bad_ep, expected_k32)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 3 failed: .exe with entry point outside .text passed")

    # 4. .text writable (IMAGE_SCN_MEM_WRITE set on .text)
    bad_wx = neg_dir / "bad_text_writable.exe"
    mut = bytearray(exe_bytes)
    for s in range(num_secs):
        off = sec_off + s * 40
        name = bytes(mut[off:off + 8]).split(b"\x00", 1)[0]
        if name == b".text":
            chars = struct.unpack_from("<I", mut, off + 36)[0]
            struct.pack_into("<I", mut, off + 36, chars | IMAGE_SCN_MEM_WRITE)
            break
    bad_wx.write_bytes(mut)
    try:
        validate_exe(objdump_bin, bad_wx, expected_k32)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 4 failed: writable .text passed validation")

    # 5. Missing expected KERNEL32 import
    try:
        validate_exe(objdump_bin, sample_exe, expected_k32 + ("NonExistentKernel32Api999",))
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 5 failed: missing KERNEL32 import passed validation")

    # 6. Corrupted .obj relocation symbol index (out of range)
    bad_rel = neg_dir / "bad_reloc.obj"
    mut_obj = bytearray(obj_bytes)
    obj_num_secs = struct.unpack_from("<H", mut_obj, 2)[0]
    for s in range(obj_num_secs):
        off = 20 + s * 40
        name = bytes(mut_obj[off:off + 8]).split(b"\x00", 1)[0]
        if name == b".text":
            rel_ptr = struct.unpack_from("<I", mut_obj, off + 24)[0]
            struct.pack_into("<I", mut_obj, rel_ptr + 4, 0x00FFFFFF)
            break
    bad_rel.write_bytes(mut_obj)
    try:
        validate_obj(objdump_bin, bad_rel)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 6 failed: .obj with corrupt relocation sym_idx passed")

    # 7. .rdata writable (IMAGE_SCN_MEM_WRITE set on .rdata)
    bad_rdata_wx = neg_dir / "bad_rdata_writable.exe"
    mut = bytearray(exe_bytes)
    for s in range(num_secs):
        off = sec_off + s * 40
        name = bytes(mut[off:off + 8]).split(b"\x00", 1)[0]
        if name == b".rdata":
            chars = struct.unpack_from("<I", mut, off + 36)[0]
            struct.pack_into("<I", mut, off + 36, chars | IMAGE_SCN_MEM_WRITE)
            break
    bad_rdata_wx.write_bytes(mut)
    try:
        validate_exe(objdump_bin, bad_rdata_wx, expected_k32)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 7 failed: writable .rdata passed validation")

    # 8. Corrupted .obj relocation offset out of bounds (vaddr >= raw_size)
    bad_rel_off = neg_dir / "bad_reloc_offset.obj"
    mut_obj2 = bytearray(obj_bytes)
    for s in range(obj_num_secs):
        off = 20 + s * 40
        name = bytes(mut_obj2[off:off + 8]).split(b"\x00", 1)[0]
        if name == b".text":
            rel_ptr = struct.unpack_from("<I", mut_obj2, off + 24)[0]
            struct.pack_into("<I", mut_obj2, rel_ptr, 0x00FFFFFF)
            break
    bad_rel_off.write_bytes(mut_obj2)
    try:
        validate_obj(objdump_bin, bad_rel_off)
    except ValidationError:
        pass
    else:
        raise RuntimeError("negative check 8 failed: .obj with out-of-bounds relocation offset passed")


def main():
    ap = argparse.ArgumentParser(description="Validate real .exe and .obj files with GNU objdump.")
    ap.add_argument("compiler", nargs="?", help="Path to compiler under test")
    ap.add_argument("tmp_dir", nargs="?", help="Temporary directory for build artifacts")
    ap.add_argument("root_dir", nargs="?", help="Repository root directory")
    ap.add_argument("--corrupt-check", metavar="EXE_OR_OBJ",
                    help="Validate a single .exe or .obj file and exit non-zero on failure")
    args = ap.parse_args()

    objdump_bin = shutil.which("objdump")
    if objdump_bin is None:
        sys.stderr.write("FAIL: mandatory external oracle 'objdump' not found on PATH (ADR-0034 section 7)\n")
        return 1

    if args.corrupt_check:
        target = Path(args.corrupt_check)
        try:
            if target.suffix.lower() == ".exe":
                validate_exe(objdump_bin, target, BASE_KERNEL32)
            else:
                validate_obj(objdump_bin, target)
        except ValidationError as e:
            sys.stderr.write(f"FAIL: {e}\n")
            return 1
        print("PASS")
        return 0

    if not args.compiler or not args.tmp_dir or not args.root_dir:
        ap.error("compiler, tmp_dir, and root_dir are required")

    compiler = Path(args.compiler).resolve()
    if not compiler.exists() and Path(str(compiler) + ".exe").exists():
        compiler = Path(str(compiler) + ".exe")
    if not compiler.exists():
        sys.stderr.write(f"FAIL: compiler not found: {compiler}\n")
        return 1

    root_dir = Path(args.root_dir).resolve()
    std_root = root_dir / "std"
    tmp_root = Path(args.tmp_dir).resolve()
    tmp_root.mkdir(parents=True, exist_ok=True)

    if len(TEST_CASES) < 20:
        sys.stderr.write(f"FAIL: expected >= 20 test cases, got {len(TEST_CASES)}\n")
        return 1

    categories_seen = set()
    first_exe = None
    first_obj = None
    first_k32 = None

    for idx, tc in enumerate(TEST_CASES):
        rel_path = tc["path"]
        src_path = root_dir / rel_path
        if not src_path.is_file():
            sys.stderr.write(f"FAIL: missing test source {src_path}\n")
            return 1

        categories_seen.add(tc["category"])
        case_dir = tmp_root / f"case_{idx:02d}"
        case_dir.mkdir(parents=True, exist_ok=True)
        exe_path = case_dir / "out.exe"
        obj_path = case_dir / "out.obj"

        # 1. Build .exe
        cmd_exe = [str(compiler), "build", "--std-root", str(std_root), "-o", str(exe_path), str(src_path)]
        r_exe = subprocess.run(cmd_exe, cwd=str(root_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r_exe.returncode != 0 or not exe_path.is_file():
            sys.stderr.write(
                f"FAIL [{rel_path}]: build .exe failed (rc={r_exe.returncode}): "
                f"{r_exe.stderr.decode('utf-8', 'replace')}\n"
            )
            return 1

        # 2. Build .obj
        cmd_obj = [
            str(compiler), "build", "--std-root", str(std_root),
            "--emit=obj", "-o", str(obj_path), str(src_path),
        ]
        r_obj = subprocess.run(cmd_obj, cwd=str(root_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r_obj.returncode != 0 or not obj_path.is_file():
            sys.stderr.write(
                f"FAIL [{rel_path}]: build --emit=obj failed (rc={r_obj.returncode}): "
                f"{r_obj.stderr.decode('utf-8', 'replace')}\n"
            )
            return 1

        # 3. Validate .exe and .obj with objdump
        try:
            validate_exe(
                objdump_bin,
                exe_path,
                tc["kernel32"],
                expected_other_imports=tc.get("other_imports"),
            )
            validate_obj(objdump_bin, obj_path, expect_rdata_relocs=tc["rdata_relocs"])
        except ValidationError as e:
            sys.stderr.write(f"FAIL [{rel_path}]: {e}\n")
            return 1

        # 4. Run .exe and verify pinned exit code and stdout
        run_env = dict(os.environ)
        run_env["AXIOM_STD"] = str(std_root)
        run_env.update(tc["env"])
        r_run = subprocess.run(
            [str(exe_path)] + list(tc["args"]),
            cwd=str(case_dir),
            env=run_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if r_run.returncode != tc["exit"]:
            sys.stderr.write(
                f"FAIL [{rel_path}]: .exe exited {r_run.returncode}, expected {tc['exit']}; "
                f"stderr: {r_run.stderr.decode('utf-8', 'replace')}\n"
            )
            return 1
        if tc["stdout"] is not None and r_run.stdout != tc["stdout"]:
            sys.stderr.write(
                f"FAIL [{rel_path}]: .exe stdout mismatch:\n"
                f"  expected: {tc['stdout']!r}\n"
                f"  actual:   {r_run.stdout!r}\n"
            )
            return 1

        if first_exe is None:
            first_exe = exe_path
            first_obj = obj_path
            first_k32 = tc["kernel32"]

    required_cats = {"numeric", "drop", "str", "ffi", "std", "rdata_table"}
    if categories_seen != required_cats:
        sys.stderr.write(f"FAIL: missing categories: {required_cats - categories_seen}\n")
        return 1

    # 5. Run negative self-tests on mutated copies
    try:
        run_negative_self_tests(objdump_bin, first_exe, first_obj, first_k32, tmp_root)
    except Exception as e:
        sys.stderr.write(f"FAIL [negative-self-test]: {e}\n")
        return 1

    print(f"OBJDUMP-VALIDATE ok: {len(TEST_CASES)} programs (.exe + .obj) + 8 negative checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
