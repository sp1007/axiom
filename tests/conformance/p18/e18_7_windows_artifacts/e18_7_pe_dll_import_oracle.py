#!/usr/bin/env python3
"""E18.7 Conformance Suite — Part 2: Windows x64 PE32+ `.dll`, `.edata` Exports,
Companion Short-Import `.lib`, `.idata` Import Invariants (`REQ-LNK-113`..`119`),
`_DllMainCRTStartup` Initialization Failure, and Forced `.reloc` Base Relocation
(SPEC-26 §3–§4, REQ-OWNER-006, ADR-0001 §5–§6).

Certifies:
  1. `axiomc build --kind dll` (plus `--implib <path>` and `axiom.toml` `kind = "dll"`)
     produces byte-identical PE32+ `.dll` (`Characteristics=0x2222`, `ImageBase=0x180000000`,
     `DllCharacteristics=0x0160`, W^X sections, zeroed timestamps/checksums, zero CRT dependency)
     and byte-identical companion COFF short-import `.lib` (`Sig1=0x0000, Sig2=0xFFFF`).
  2. `.edata` export directory (`DataDirectory[0]`): `@export` and `@export("custom_name")`
     on module functions, inherent `impl` methods, associated `impl` constants, and module-level
     constants (scalars, arrays, `Str` fat pointers), strict ASCII sorting, 1-based ordinals,
     and strict exclusion of non-`@export` `pub` items.
  3. Import table invariants (`REQ-LNK-113`..`119`, `0187 §40` AIMPORT-28..34):
     - `REQ-LNK-113` (AIMPORT-28): IAT addresses in `.idata` are resolved at load time by the
       Windows OS loader (verified by comparing runtime `__imp_<sym>` slot contents against
       `GetProcAddress(hMod, sym)`, including under forced DLL rebasing).
     - `REQ-LNK-114` (AIMPORT-29): Compiler does not hard-code foreign function addresses
       (verified by binary inspection of on-disk `.text` and `.idata`: IAT slots on disk hold
       only Hint/Name RVAs `< SizeOfImage`, never `0x180000000`+ target addresses).
     - `REQ-LNK-115` & `REQ-LNK-116` (AIMPORT-30, AIMPORT-31): Explicit, deterministic DLL
       mapping and byte-identical `.idata` layout (null-terminated `IMAGE_IMPORT_DESCRIPTOR`
       array, null-terminated 64-bit ILT & 8-byte aligned IAT, `DataDirectory[1]` & `[12]`).
     - `REQ-LNK-117` (AIMPORT-32): RIP-relative IAT references (`FF 25 <disp32>` and
       `FF 15 <disp32>`) in `.text`, verified via binary inspection and `objdump -d`.
     - `REQ-LNK-118` (AIMPORT-33): Source-language-independent import metadata across Axiom
       `.exe`/`.dll` and C (`gcc`) `.exe`/`.dll` (both short-import `.lib` and traditional
       GNU `dlltool` `.idata$2..$7` `.dll.a` archives).
     - `REQ-LNK-119` (AIMPORT-34): `DataDirectory[PE_DIR_DELAY_IMPORT = 13] == (0, 0)`.
  4. `_DllMainCRTStartup` (`DllMain`) initialization (`SPEC-26 AXS-WLIB-022`):
     - `__ax_resolve_module_bindings()` returning `false` on `DLL_PROCESS_ATTACH` immediately
       returns `FALSE` (`0`) without running user `@entry`, causing `LoadLibraryA` to return `NULL`.
     - `@entry` (0-arg `-> bool` and 3-arg `-> i32`) returning `false`/`0` on `DLL_PROCESS_ATTACH`
       causes `LoadLibraryA` to fail cleanly (`NULL`).
     - `@entry` returning `true`/`1` executes on `DLL_PROCESS_ATTACH` and `DLL_PROCESS_DETACH`.
  5. Forced non-preferred base relocation (`.reloc`, `SPEC-26 AXS-WLIB-023`):
     - Multi-page `.reloc` blocks (`IMAGE_REL_BASED_DIR64`, odd & even counts with
       `IMAGE_REL_BASED_ABSOLUTE` padding) + reserving preferred `0x180000000` with
       `VirtualAlloc` prior to `LoadLibraryA`, verifying `base != 0x180000000`, calling
       exported functions, and dereferencing rebased `ADDR64` fat-pointer `Str` constants
       across multiple 4 KiB pages.
"""

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


IMAGE_FILE_MACHINE_AMD64 = 0x8664
EXPECTED_DLL_CHARS = 0x2222
EXPECTED_EXE_CHARS = 0x0222
EXPECTED_DLL_IMAGE_BASE = 0x180000000
EXPECTED_EXE_IMAGE_BASE = 0x140000000
EXPECTED_DLL_OPT_CHARS = 0x0160

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
    raise ValidationError(f"mandatory external oracle tool not found in PATH: {names}")


def run_cmd(cmd, cwd=None, expect_rc=0):
    env = dict(os.environ)
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.isdir(msys_bin) and msys_bin not in env.get("PATH", ""):
        env["PATH"] = msys_bin + os.pathsep + env.get("PATH", "")
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    if expect_rc is not None and p.returncode != expect_rc:
        out_s = p.stdout.decode("utf-8", errors="replace")
        err_s = p.stderr.decode("utf-8", errors="replace")
        raise ValidationError(
            f"command {cmd!r} exited with {p.returncode}, expected {expect_rc}\n"
            f"--- stdout ---\n{out_s}\n--- stderr ---\n{err_s}"
        )
    return p


def write_lf(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


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


def validate_short_import_lib(lib_bytes: bytes, expected_dll_name: str):
    """Validates SPEC-26 AXS-WLIB-030 companion short-import .lib (Sig1=0x0000, Sig2=0xFFFF)."""
    if lib_bytes[:8] != b"!<arch>\n":
        raise ValidationError("companion import .lib missing !<arch>\\n magic")
    pos = 8
    short_imports = {}
    while pos < len(lib_bytes):
        hdr = lib_bytes[pos : pos + 60]
        name_s = hdr[0:16].decode("ascii", errors="replace").rstrip(" ")
        body_sz = int(hdr[48:58].decode("ascii").strip())
        body = lib_bytes[pos + 60 : pos + 60 + body_sz]
        pos += 60 + body_sz + (1 if (body_sz & 1) else 0)
        if name_s in ("/", "//"):
            continue
        if len(body) < 20:
            raise ValidationError(f"short import member too small ({len(body)} bytes)")
        sig1, sig2, ver, mach, ts, sz_data, hint, typ = struct.unpack_from("<HHHHIIHH", body, 0)
        if sig1 != 0x0000 or sig2 != 0xFFFF or ver != 0 or mach != IMAGE_FILE_MACHINE_AMD64 or ts != 0:
            raise ValidationError(
                f"invalid IMPORT_OBJECT_HEADER: sig1={sig1:#x} sig2={sig2:#x} ver={ver} mach={mach:#x} ts={ts}"
            )
        payload = body[20 : 20 + sz_data].split(b"\x00")
        sym_nm = payload[0].decode("ascii")
        dll_nm = payload[1].decode("ascii")
        if dll_nm != expected_dll_name:
            raise ValidationError(f"short import DLL name {dll_nm!r} != {expected_dll_name!r}")
        short_imports[sym_nm] = {"hint": hint, "import_type": typ & 0x3, "name_type": (typ >> 2) & 0x7}
    return short_imports


def inspect_pe_image(data: bytes, is_dll: bool, expected_export_dll_name: str | None = None):
    """Validates PE32+ headers, W^X sections, .idata (REQ-LNK-113..119), .edata, and .reloc."""
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValidationError("missing MZ header")
    (pe_off,) = struct.unpack_from("<I", data, 0x3C)
    if data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValidationError("missing PE\\0\\0 signature")
    coff_off = pe_off + 4
    mach, num_sec, ts, _, _, opt_sz, chars = struct.unpack_from("<HHIIIHH", data, coff_off)
    if mach != IMAGE_FILE_MACHINE_AMD64 or ts != 0 or opt_sz != 240:
        raise ValidationError(f"bad COFF header: mach={mach:#x} ts={ts} opt_sz={opt_sz}")
    want_chars = EXPECTED_DLL_CHARS if is_dll else EXPECTED_EXE_CHARS
    if chars != want_chars:
        raise ValidationError(f"expected COFF Characteristics {want_chars:#06x}, got {chars:#06x}")

    opt_off = coff_off + 20
    (magic,) = struct.unpack_from("<H", data, opt_off)
    (entry_rva,) = struct.unpack_from("<I", data, opt_off + 16)
    (img_base,) = struct.unpack_from("<Q", data, opt_off + 24)
    sec_align, file_align = struct.unpack_from("<II", data, opt_off + 32)
    (size_of_image,) = struct.unpack_from("<I", data, opt_off + 56)
    (checksum,) = struct.unpack_from("<I", data, opt_off + 64)
    (dll_chars,) = struct.unpack_from("<H", data, opt_off + 70)
    (num_dd,) = struct.unpack_from("<I", data, opt_off + 108)

    want_base = EXPECTED_DLL_IMAGE_BASE if is_dll else EXPECTED_EXE_IMAGE_BASE
    if magic != 0x020B or img_base != want_base or sec_align != 0x1000 or file_align != 0x200 or checksum != 0 or num_dd != 16:
        raise ValidationError(
            f"bad OptionalHeader: magic={magic:#x} base={img_base:#x} align=({sec_align:#x},{file_align:#x}) csum={checksum}"
        )
    if is_dll and dll_chars != EXPECTED_DLL_OPT_CHARS:
        raise ValidationError(f"expected DLL DllCharacteristics {EXPECTED_DLL_OPT_CHARS:#06x}, got {dll_chars:#06x}")

    data_dirs = [struct.unpack_from("<II", data, opt_off + 112 + d * 8) for d in range(16)]
    # REQ-LNK-119 (AIMPORT-34): Delay-load imports are not required for MVP
    if data_dirs[13] != (0, 0):
        raise ValidationError(f"REQ-LNK-119 violated: expected empty Delay Import Directory [13], got {data_dirs[13]}")

    sec_base = opt_off + opt_sz
    sections = []
    sec_by_name = {}
    for i in range(num_sec):
        so = sec_base + i * 40
        nm = data[so : so + 8].rstrip(b"\x00").decode("ascii")
        vsize, vaddr, rawsz, rawptr, _, _, _, _, schars = struct.unpack_from("<IIIIIIHHI", data, so + 8)
        if (schars & IMAGE_SCN_MEM_WRITE) and (schars & IMAGE_SCN_MEM_EXECUTE):
            raise ValidationError(f"section {nm} violates W^X: {schars:#x}")
        s_info = {
            "name": nm,
            "vsize": vsize,
            "vaddr": vaddr,
            "raw_size": rawsz,
            "raw_ptr": rawptr,
            "chars": schars,
            "data": data[rawptr : rawptr + rawsz],
        }
        sections.append(s_info)
        sec_by_name[nm] = s_info

    # Validate .idata (DataDirectory[1] = IMPORT, DataDirectory[12] = IAT) — REQ-LNK-113..119
    imp_rva, imp_sz = data_dirs[1]
    iat_rva, iat_sz = data_dirs[12]
    if imp_rva == 0 or imp_sz < 40 or iat_rva == 0 or iat_sz == 0 or (iat_rva % 8) != 0 or (iat_sz % 8) != 0:
        raise ValidationError(
            f"invalid Import/IAT directories: IMPORT=({imp_rva:#x},{imp_sz}), IAT=({iat_rva:#x},{iat_sz})"
        )
    if ".idata" not in sec_by_name:
        raise ValidationError("missing .idata section")
    isec = sec_by_name[".idata"]
    if (isec["chars"] & (IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE)) != (IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE):
        raise ValidationError(f".idata must be READ|WRITE so OS loader can resolve IAT slots: {isec['chars']:#x}")

    imported_dlls = {}
    desc_off = rva_to_off(sections, imp_rva)
    num_descs = imp_sz // 20
    for d_idx in range(num_descs):
        ilt_rva, ts_d, fwd_d, name_rva, ft_rva = struct.unpack_from("<IIIII", data, desc_off + d_idx * 20)
        if d_idx == num_descs - 1:
            # REQ-LNK-111: Null terminator descriptor
            if (ilt_rva, ts_d, fwd_d, name_rva, ft_rva) != (0, 0, 0, 0, 0):
                raise ValidationError("Import Directory missing null terminator descriptor")
            break
        if ilt_rva == 0 or name_rva == 0 or ft_rva == 0 or (ilt_rva % 8) != 0 or (ft_rva % 8) != 0:
            raise ValidationError(f"malformed IMAGE_IMPORT_DESCRIPTOR[{d_idx}]")
        dll_name = read_cstr(data, rva_to_off(sections, name_rva))
        if dll_name.lower() in ("msvcrt.dll", "ucrtbase.dll", "vcruntime140.dll"):
            raise ValidationError(f"forbidden C runtime dependency in .idata: {dll_name}")

        # Walk 64-bit ILT & IAT (REQ-LNK-108..110, REQ-LNK-113, REQ-LNK-114)
        ilt_pos = rva_to_off(sections, ilt_rva)
        iat_pos = rva_to_off(sections, ft_rva)
        funcs = []
        while True:
            (ilt_ent,) = struct.unpack_from("<Q", data, ilt_pos)
            (iat_ent,) = struct.unpack_from("<Q", data, iat_pos)
            ilt_pos += 8
            iat_pos += 8
            if ilt_ent == 0:
                if iat_ent != 0:
                    raise ValidationError(f"IAT not null-terminated in {dll_name}")
                break
            # REQ-LNK-114: On disk before load, IAT entry must match ILT entry and be an RVA < size_of_image,
            # NEVER a hardcoded 64-bit foreign virtual address (>= 0x140000000)!
            if iat_ent != ilt_ent or iat_ent >= size_of_image:
                raise ValidationError(
                    f"REQ-LNK-114 violated in {dll_name}: on-disk IAT={iat_ent:#x}, ILT={ilt_ent:#x}, SizeOfImage={size_of_image:#x}"
                )
            hn_off = rva_to_off(sections, int(ilt_ent))
            (hint,) = struct.unpack_from("<H", data, hn_off)
            fn_name = read_cstr(data, hn_off + 2)
            funcs.append((fn_name, hint, ft_rva + (len(funcs) * 8)))
        imported_dlls[dll_name] = funcs

    # REQ-LNK-117: Verify RIP-relative `FF 25 <disp32>` / `FF 15 <disp32>` IAT references in `.text`
    tsec = sec_by_name[".text"]
    tdata = tsec["data"]
    rip_iat_refs = 0
    for off in range(len(tdata) - 6):
        b0, b1 = tdata[off], tdata[off + 1]
        if b0 == 0xFF and b1 in (0x15, 0x25):
            (disp32,) = struct.unpack_from("<i", tdata, off + 2)
            target_rva = tsec["vaddr"] + off + 6 + disp32
            if iat_rva <= target_rva < iat_rva + iat_sz and ((target_rva - iat_rva) % 8) == 0:
                rip_iat_refs += 1
    if rip_iat_refs == 0:
        raise ValidationError("REQ-LNK-117 violated: found 0 RIP-relative IAT references in .text")

    # Parse .edata if expected
    exports = []
    exp_rva, exp_sz = data_dirs[0]
    if expected_export_dll_name is not None:
        if exp_rva == 0 or exp_sz < 40:
            raise ValidationError("missing .edata Export Directory")
        eoff = rva_to_off(sections, exp_rva)
        echars, ets, emaj, emin, name_rva, base_ord, nfuncs, nnames, eat_rva, npt_rva, ord_rva = struct.unpack_from(
            "<IIHHIIIIIII", data, eoff
        )
        if echars != 0 or ets != 0 or base_ord != 1 or nfuncs != nnames:
            raise ValidationError(f"bad .edata header: base={base_ord} nfuncs={nfuncs} nnames={nnames}")
        actual_dll_name = read_cstr(data, rva_to_off(sections, name_rva))
        if actual_dll_name != expected_export_dll_name:
            raise ValidationError(f".edata Name {actual_dll_name!r} != {expected_export_dll_name!r}")
        eat_off = rva_to_off(sections, eat_rva)
        npt_off = rva_to_off(sections, npt_rva)
        ord_off = rva_to_off(sections, ord_rva)
        for i in range(nnames):
            (nrva,) = struct.unpack_from("<I", data, npt_off + i * 4)
            (oidx,) = struct.unpack_from("<H", data, ord_off + i * 2)
            if oidx != i:
                raise ValidationError(f"OrdinalTable[{i}] = {oidx} != {i}")
            (fn_rva,) = struct.unpack_from("<I", data, eat_off + oidx * 4)
            exports.append((read_cstr(data, rva_to_off(sections, nrva)), base_ord + oidx, fn_rva))
        if [nm.encode("ascii") for nm, _, _ in exports] != sorted(nm.encode("ascii") for nm, _, _ in exports):
            raise ValidationError(f".edata exports not sorted in strict ASCII order: {exports}")

    # Parse .reloc if present
    rel_rva, rel_sz = data_dirs[5]
    reloc_blocks = []
    if is_dll or rel_sz > 0:
        if rel_rva == 0 or rel_sz < 8 or ".reloc" not in sec_by_name:
            raise ValidationError("DLL missing .reloc section")
        roff = rva_to_off(sections, rel_rva)
        pos = 0
        prev_page = -1
        while pos < rel_sz:
            page_rva, blk_sz = struct.unpack_from("<II", data, roff + pos)
            if blk_sz < 8 or (blk_sz % 4) != 0 or pos + blk_sz > rel_sz or (page_rva & 0xFFF) != 0 or page_rva <= prev_page:
                raise ValidationError(f"invalid .reloc block at +{pos}: page={page_rva:#x} sz={blk_sz}")
            prev_page = page_rva
            nent = (blk_sz - 8) // 2
            d64 = []
            pads = 0
            for j in range(nent):
                (w,) = struct.unpack_from("<H", data, roff + pos + 8 + j * 2)
                rt = (w >> 12) & 0xF
                ro = w & 0xFFF
                if rt == IMAGE_REL_BASED_DIR64:
                    if pads > 0 or (d64 and ro <= d64[-1]):
                        raise ValidationError("unsorted or post-pad DIR64 entry in .reloc")
                    d64.append(ro)
                elif rt == IMAGE_REL_BASED_ABSOLUTE and ro == 0:
                    pads += 1
                else:
                    raise ValidationError(f"unexpected base reloc entry {w:#06x}")
            reloc_blocks.append({"page_rva": page_rva, "dir64_count": len(d64), "abs_pads": pads})
            pos += blk_sz

    return {
        "sections": sec_by_name,
        "imported_dlls": imported_dlls,
        "exports": exports,
        "reloc_blocks": reloc_blocks,
        "entry_rva": entry_rva,
    }


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: e18_7_pe_dll_import_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    objdump_tool = find_tool(["objdump", "llvm-objdump"])
    gcc_tool = find_tool(["gcc", "clang"])

    # =========================================================================
    # 1. Build `e187_core_lib.dll` + Companion Short-Import `e187_core_lib.lib`
    #    (Multi-page `.reloc` odd/even blocks, `@export` functions/methods/globals)
    # =========================================================================
    core_dll_ax = tmp_dir / "e187_core_lib.ax"
    write_lf(
        core_dll_ax,
        """\
module e187_core_lib

pub fn unexported_pub_fn(x: i64) -> i64 {
    x + 999
}

@export
pub const DLL_PAGE1_GREETING: Str = "Xin chào thế giới từ DLL\\n";

@export
pub const DLL_PAGE_PAD_1: [8160]u8 = [17u8; 8160];

@export
pub const DLL_PAGE2_STR_A: Str = "Rebased-Page2-Alpha\\n";

@export
pub const DLL_PAGE2_STR_B: Str = "Rebased-Page2-Beta\\n";

@export
pub const DLL_PAGE_PAD_2: [8112]u8 = [34u8; 8112];

@export
pub const DLL_PAGE3_STR_A: Str = "Rebased-Page3-One\\n";

@export
pub const DLL_PAGE3_STR_B: Str = "Rebased-Page3-Two\\n";

@export
pub const DLL_PAGE3_STR_C: Str = "Rebased-Page3-Three\\n";

@export
pub const DLL_MAGIC_SCALAR: i32 = 2026;

@export("DLL_LUT_ARRAY")
pub const INTERNAL_LUT: [4]i32 = [11, 22, 33, 44];

@export
pub fn dll_compute_6(a: i64, b: i64, c: i64, d: i64, e: i64, f: i64) -> i64 {
    a * 1 + b * 2 + c * 3 + d * 4 + e * 5 + f * 6
}

@export("dll_renamed_scale")
pub fn scale_internal(x: i32, factor: i32) -> i32 {
    x * factor + 7
}

pub struct DllEngine {
    pub tag: i32,
}

impl DllEngine {
    @export("dll_engine_step")
    pub fn step(x: i32, y: i32) -> i32 {
        x * 3 + y * 2
    }
}
""",
    )

    core_dll_1 = tmp_dir / "e187_core_lib.dll"
    core_lib_1 = tmp_dir / "e187_core_lib.lib"
    det_dir = tmp_dir / "det_repeat"
    det_dir.mkdir(parents=True, exist_ok=True)
    core_dll_2 = det_dir / "e187_core_lib.dll"
    core_lib_2 = det_dir / "e187_core_lib.lib"

    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(core_dll_1), str(core_dll_ax)])
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(core_dll_2), str(core_dll_ax)])

    if core_dll_1.read_bytes() != core_dll_2.read_bytes():
        raise ValidationError("e187_core_lib.dll is not byte-identical across repeated builds")
    if core_lib_1.read_bytes() != core_lib_2.read_bytes():
        raise ValidationError("companion e187_core_lib.lib is not byte-identical across repeated builds")

    short_imps = validate_short_import_lib(core_lib_1.read_bytes(), "e187_core_lib.dll")
    if short_imps.get("dll_compute_6", {}).get("import_type") != 0:
        raise ValidationError(f"expected IMPORT_OBJECT_CODE (0) for dll_compute_6, got {short_imps.get('dll_compute_6')}")
    if short_imps.get("DLL_MAGIC_SCALAR", {}).get("import_type") != 1:
        raise ValidationError(
            f"expected IMPORT_OBJECT_DATA (1) for DLL_MAGIC_SCALAR, got {short_imps.get('DLL_MAGIC_SCALAR')}"
        )

    # Verify `--implib <custom_path>` and `axiom.toml` `kind = "dll"`
    custom_implib = det_dir / "custom_override.lib"
    custom_dll = det_dir / "custom_override_host.dll"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "--kind",
            "dll",
            "--implib",
            str(custom_implib),
            "-o",
            str(custom_dll),
            str(core_dll_ax),
        ]
    )
    if not custom_implib.is_file() or (det_dir / "custom_override_host.lib").exists():
        raise ValidationError("--implib did not redirect companion import library exclusively to custom path")

    pkg_dll_dir = tmp_dir / "pkg_dll_e187"
    write_lf(pkg_dll_dir / "axiom.toml", '[package]\nname = "pkg_dll_e187"\nversion = "0.1.0"\nkind = "dll"\n')
    write_lf(
        pkg_dll_dir / "src" / "lib.ax",
        "module pkg_dll_e187\n@export\npub fn pkg_dll_entry(x: i32) -> i32 { x + 7 }\n",
    )
    pkg_dll_out = tmp_dir / "pkg_dll_out"
    pkg_dll_out.mkdir(parents=True, exist_ok=True)
    run_cmd([compiler, "build", "--std-root", str(std_root), str(pkg_dll_dir)], cwd=str(pkg_dll_out))
    if not (pkg_dll_out / "pkg_dll_e187.dll").is_file() or not (pkg_dll_out / "pkg_dll_e187.lib").is_file():
        raise ValidationError("package manifest `kind = 'dll'` did not emit pkg_dll_e187.dll + pkg_dll_e187.lib")

    dll_info = inspect_pe_image(core_dll_1.read_bytes(), is_dll=True, expected_export_dll_name="e187_core_lib.dll")
    exp_names = [nm for nm, _, _ in dll_info["exports"]]
    if "unexported_pub_fn" in exp_names:
        raise ValidationError("non-@export `pub fn unexported_pub_fn` leaked into .edata")
    for req_exp in (
        "DLL_LUT_ARRAY",
        "DLL_MAGIC_SCALAR",
        "DLL_PAGE1_GREETING",
        "DLL_PAGE2_STR_A",
        "DLL_PAGE3_STR_C",
        "dll_compute_6",
        "dll_engine_step",
        "dll_renamed_scale",
    ):
        if req_exp not in exp_names:
            raise ValidationError(f"missing expected export {req_exp!r} in {exp_names}")

    # Verify multi-page `.reloc` has both odd (1 pad) and even (0 pad) DIR64 blocks
    rblocks = dll_info["reloc_blocks"]
    if len(rblocks) < 3:
        raise ValidationError(f"expected >=3 .reloc page blocks, got {rblocks}")
    pads_seen = {(b["dir64_count"], b["abs_pads"]) for b in rblocks}
    if (1, 1) not in pads_seen or (2, 0) not in pads_seen or (3, 1) not in pads_seen:
        raise ValidationError(f"expected odd/even/odd DIR64 page blocks (1,1), (2,0), (3,1), got {rblocks}")

    # Disassemble with external `objdump -d` and verify RIP-relative IAT calls (`REQ-LNK-117`)
    od_d = run_cmd([objdump_tool, "-d", str(core_dll_1)]).stdout.decode("utf-8", errors="replace")
    if "(bad)" in od_d or "%rip" not in od_d and "rip" not in od_d.lower():
        raise ValidationError(f"objdump -d failed or missing RIP-relative addressing:\n{od_d[:400]}")

    # =========================================================================
    # 2. Third-Party C DLL (`gcc -shared -Wl,--out-implib`) + Axiom Consumer `.exe`
    #    Verifies `REQ-LNK-113`..`119` across BOTH Axiom Short-Import `.lib` and
    #    GNU `dlltool` `.idata$2..$7` `.dll.a` Import Archives
    # =========================================================================
    c_ext_dll_c = tmp_dir / "c_ext_dll.c"
    write_lf(
        c_ext_dll_c,
        """\
#include <stdint.h>

__declspec(dllexport) const int32_t c_dll_const_bias = 500;

__declspec(dllexport) int64_t c_dll_mix5(int64_t a, int64_t b, int64_t c, int64_t d, int64_t e) {
    return (a + b) * c - d + e;
}
""",
    )
    c_ext_dll = tmp_dir / "c_ext_dll.dll"
    c_ext_implib = tmp_dir / "libc_ext_dll.dll.a"
    run_cmd([gcc_tool, "-shared", "-O2", str(c_ext_dll_c), "-o", str(c_ext_dll), f"-Wl,--out-implib,{c_ext_implib}"])

    # C helper object that reads `__imp_DLL_MAGIC_SCALAR`, `__imp_DLL_LUT_ARRAY`, `__imp_c_dll_const_bias`,
    # and exposes the runtime IAT slot address `&__imp_dll_renamed_scale` to prove `REQ-LNK-113`!
    iat_probe_c = tmp_dir / "iat_probe.c"
    write_lf(
        iat_probe_c,
        """\
#include <stdint.h>

extern __declspec(dllimport) const int32_t DLL_MAGIC_SCALAR;
extern __declspec(dllimport) const int32_t DLL_LUT_ARRAY[4];
extern __declspec(dllimport) const int32_t c_dll_const_bias;
extern void *__imp_dll_renamed_scale;

int32_t probe_read_imported_globals(void) {
    int32_t lut_sum = DLL_LUT_ARRAY[0] + DLL_LUT_ARRAY[1] + DLL_LUT_ARRAY[2] + DLL_LUT_ARRAY[3];
    return DLL_MAGIC_SCALAR + lut_sum + c_dll_const_bias; // 2026 + 110 + 500 = 2636
}

uintptr_t probe_get_iat_resolved_addr(void) {
    return (uintptr_t)__imp_dll_renamed_scale;
}
""",
    )
    iat_probe_obj = tmp_dir / "iat_probe.obj"
    run_cmd([gcc_tool, "-c", "-O2", str(iat_probe_c), "-o", str(iat_probe_obj)])

    consumer_ax = tmp_dir / "e187_consumer.ax"
    write_lf(
        consumer_ax,
        """\
module e187_consumer

@link("e187_core_lib")
extern "C" {
    fn dll_compute_6(a: i64, b: i64, c: i64, d: i64, e: i64, f: i64) -> i64;
    fn dll_renamed_scale(x: i32, factor: i32) -> i32;
    fn dll_engine_step(x: i32, y: i32) -> i32;
}

extern "C" {
    fn c_dll_mix5(a: i64, b: i64, c: i64, d: i64, e: i64) -> i64;
    fn probe_read_imported_globals() -> i32;
    fn probe_get_iat_resolved_addr() -> usize;
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
        let hmod = GetModuleHandleA(str_cptr("e187_core_lib.dll\\0"));
        let proc_scale = GetProcAddress(hmod, str_cptr("dll_renamed_scale\\0"));
        let iat_scale = probe_get_iat_resolved_addr();
        // REQ-LNK-113: Windows loader resolved the IAT slot to the exact runtime export address
        if hmod == 0 || proc_scale == 0 || iat_scale != proc_scale {
            return 10;
        }

        let p_greet = GetProcAddress(hmod, str_cptr("DLL_PAGE1_GREETING\\0"));
        if p_greet == 0 {
            return 11;
        }
        print(*(p_greet as *const Str));

        let v6 = dll_compute_6(1, 2, 3, 4, 5, 6);           // 91
        let vs = dll_renamed_scale(8, 5);                   // 47
        let ve = dll_engine_step(10, 6);                    // 42
        let vc = c_dll_mix5(4, 6, 5, 12, 7);                // 45
        let vg = probe_read_imported_globals() as i64;      // 2636
        let total = v6 + (vs as i64) + (ve as i64) + vc + vg; // 2861
        if total == 2861 {
            93
        } else {
            12
        }
    }
}
""",
    )

    consumer_exe_1 = tmp_dir / "e187_consumer_1.exe"
    consumer_exe_2 = det_dir / "e187_consumer_2.exe"
    for out_exe in (consumer_exe_1, consumer_exe_2):
        run_cmd(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                "-L",
                str(tmp_dir),
                "-lc_ext_dll.dll",
                "-o",
                str(out_exe),
                str(consumer_ax),
                str(iat_probe_obj),
            ]
        )

    if consumer_exe_1.read_bytes() != consumer_exe_2.read_bytes():
        raise ValidationError("e187_consumer.exe is not byte-identical across repeated builds (REQ-LNK-116)")

    exe_info = inspect_pe_image(consumer_exe_1.read_bytes(), is_dll=False)
    imp_dll_names_lower = {k.lower() for k in exe_info["imported_dlls"]}
    for req_dll in ("kernel32.dll", "e187_core_lib.dll", "c_ext_dll.dll"):
        if req_dll not in imp_dll_names_lower:
            raise ValidationError(f"missing {req_dll} in e187_consumer.exe Import Directory: {imp_dll_names_lower}")

    res_cons = run_cmd([str(consumer_exe_1)], cwd=str(tmp_dir), expect_rc=93)
    if res_cons.stdout != "Xin chào thế giới từ DLL\n".encode("utf-8"):
        raise ValidationError(f"unexpected stdout from e187_consumer.exe: {res_cons.stdout!r}")

    # =========================================================================
    # 3. Forced Non-Preferred Base Relocation (`.reloc`) + `DllMain` (`_DllMainCRTStartup`)
    #    Initialization Failure Returning `FALSE`
    # =========================================================================
    bind_fail_ax = tmp_dir / "dll_bind_fail.ax"
    write_lf(
        bind_fail_ax,
        """\
module dll_bind_fail

fn __ax_resolve_module_bindings() -> bool {
    false
}

@entry
fn unreachable_entry() -> bool {
    print("ERROR_ENTRY_RAN_AFTER_BIND_FAIL\\n");
    true
}
""",
    )
    bind_fail_dll = tmp_dir / "dll_bind_fail.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(bind_fail_dll), str(bind_fail_ax)])

    entry_fail_ax = tmp_dir / "dll_entry_fail.ax"
    write_lf(
        entry_fail_ax,
        """\
module dll_entry_fail

@entry
fn init_fail(hinst: usize, reason: u32, reserved: *const u8) -> i32 {
    let _ = hinst;
    let _ = reserved;
    if reason == 1u32 {
        print("DLL_ENTRY_FAIL_EXPECTED\\n");
        return 0;
    }
    1
}
""",
    )
    entry_fail_dll = tmp_dir / "dll_entry_fail.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(entry_fail_dll), str(entry_fail_ax)])

    entry_ok_ax = tmp_dir / "dll_entry_ok.ax"
    write_lf(
        entry_ok_ax,
        """\
module dll_entry_ok

fn __ax_resolve_module_bindings() -> bool {
    true
}

@entry
fn init_ok(hinst: usize, reason: u32, reserved: *const u8) -> i32 {
    let _ = reserved;
    if reason == 1u32 {
        print("DLL_ATTACH_OK\\n");
        if hinst == 0 { return 0; }
    } else if reason == 0u32 {
        print("DLL_DETACH_OK\\n");
    }
    1
}

@export
pub fn ok_ping(x: i32) -> i32 {
    x + 40
}
""",
    )
    entry_ok_dll = tmp_dir / "dll_entry_ok.dll"
    run_cmd([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(entry_ok_dll), str(entry_ok_ax)])

    # Host C harness that:
    #  1) Occupies preferred `0x180000000` with `VirtualAlloc` before `LoadLibraryA("e187_core_lib.dll")`,
    #  2) Verifies `e187_core_lib.dll` was rebased (`actual_base != 0x180000000`),
    #  3) Verifies all 6 multi-page `Str` fat pointers in `.rdata` had their 64-bit `ptr` fields
    #     relocated into `[actual_base, actual_base + 0x200000)` via `.reloc` `IMAGE_REL_BASED_DIR64`,
    #  4) Verifies `LoadLibraryA("dll_bind_fail.dll") == NULL` (without running `@entry`) and
    #     `LoadLibraryA("dll_entry_fail.dll") == NULL`,
    #  5) Verifies `dll_entry_ok.dll` runs attach + export call + detach cleanly.
    harness_c = tmp_dir / "rebase_and_dllmain_harness.c"
    write_lf(
        harness_c,
        """\
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    const char *ptr;
    size_t len;
} AxStr;

typedef int64_t (*fn_compute6_t)(int64_t, int64_t, int64_t, int64_t, int64_t, int64_t);
typedef int32_t (*fn_ping_t)(int32_t);

static int verify_rebased_str(HMODULE h, uintptr_t base, const char *sym, const char *expected) {
    const AxStr *ps = (const AxStr *)(const void *)GetProcAddress(h, sym);
    if (!ps) return 0;
    uintptr_t p = (uintptr_t)ps->ptr;
    size_t elen = strlen(expected);
    if (p < base || p >= base + 0x200000ULL) return 0;
    if (ps->len != elen || memcmp(ps->ptr, expected, elen) != 0) return 0;
    return 1;
}

int main(void) {
    void *blocker = VirtualAlloc((void *)0x180000000ULL, 0x200000, MEM_RESERVE, PAGE_NOACCESS);
    HMODULE h_core = LoadLibraryA("e187_core_lib.dll");
    if (!h_core) return 20;
    uintptr_t base = (uintptr_t)h_core;
    if (base == 0x180000000ULL) return 21;

    if (!verify_rebased_str(h_core, base, "DLL_PAGE1_GREETING", "Xin ch\\xc3\\xa0o th\\xe1\\xba\\xbf gi\\xe1\\xbb\\x9bi t\\xe1\\xbb\\xab DLL\\n")) return 22;
    if (!verify_rebased_str(h_core, base, "DLL_PAGE2_STR_A", "Rebased-Page2-Alpha\\n")) return 23;
    if (!verify_rebased_str(h_core, base, "DLL_PAGE2_STR_B", "Rebased-Page2-Beta\\n")) return 24;
    if (!verify_rebased_str(h_core, base, "DLL_PAGE3_STR_A", "Rebased-Page3-One\\n")) return 25;
    if (!verify_rebased_str(h_core, base, "DLL_PAGE3_STR_B", "Rebased-Page3-Two\\n")) return 26;
    if (!verify_rebased_str(h_core, base, "DLL_PAGE3_STR_C", "Rebased-Page3-Three\\n")) return 27;

    fn_compute6_t f6 = (fn_compute6_t)(void *)GetProcAddress(h_core, "dll_compute_6");
    if (!f6 || f6(10, 20, 30, 40, 50, 60) != 910) return 28;

    FreeLibrary(h_core);
    if (blocker) VirtualFree(blocker, 0, MEM_RELEASE);

    /* Module-binding resolution failure must abort DllMain with FALSE before @entry */
    HMODULE h_bfail = LoadLibraryA("dll_bind_fail.dll");
    if (h_bfail != NULL) return 29;

    /* @entry returning 0 (FALSE) on DLL_PROCESS_ATTACH must abort LoadLibraryA */
    HMODULE h_efail = LoadLibraryA("dll_entry_fail.dll");
    if (h_efail != NULL) return 30;

    /* @entry returning 1 (TRUE) succeeds and runs detach on FreeLibrary */
    HMODULE h_ok = LoadLibraryA("dll_entry_ok.dll");
    if (!h_ok) return 31;
    fn_ping_t f_ping = (fn_ping_t)(void *)GetProcAddress(h_ok, "ok_ping");
    if (!f_ping || f_ping(2) != 42) return 32;
    FreeLibrary(h_ok);

    return 75;
}
""",
    )
    harness_exe = tmp_dir / "rebase_and_dllmain_harness.exe"
    run_cmd([gcc_tool, "-O2", str(harness_c), "-o", str(harness_exe)])
    res_har = run_cmd([str(harness_exe)], cwd=str(tmp_dir), expect_rc=75)
    if b"ERROR_ENTRY_RAN_AFTER_BIND_FAIL" in res_har.stdout:
        raise ValidationError("@entry ran despite __ax_resolve_module_bindings() returning false")
    if res_har.stdout != b"DLL_ENTRY_FAIL_EXPECTED\nDLL_ATTACH_OK\nDLL_DETACH_OK\n":
        raise ValidationError(f"unexpected DllMain lifecycle stdout: {res_har.stdout!r}")

    print("E18-7-PE-DLL-IMPORT-CONFORMANCE-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
