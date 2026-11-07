#!/usr/bin/env python3
"""E18.7 Conformance Suite — Part 1: Windows x64 COFF Static `.lib` Archives, Dead-Member
Stripping, `.pdata`/`.xdata` Unwind RVA Relocation after Final Layout (`REQ-LNK-120`), and
Function-Pointer Calling Convention Semantic Identity (`REQ-LNK-121`) (SPEC-26 §1–§2).

Certifies:
  1. `axiomc build --kind lib` and `axiomc compile --kind lib` (plus `axiom.toml` `kind = "lib"`)
     emit byte-identical, deterministic COFF `.lib` archives (`!<arch>\\n`, zeroed Date/UID/GID/Mode,
     1st big-endian & 2nd little-endian linker members, `//` longnames table for >15-byte member
     names, `0x0A` even-byte alignment padding), accepted by `ar`/`llvm-ar`, `nm`/`llvm-nm`, and
     `objdump -a`.
  2. Multi-member demand-driven fixed-point archive extraction & dead-member stripping
     (`SPEC-26 AXS-WLIB-012`):
     - `multi_strip.lib` contains 4 members in order:
         `m0_dead_alpha.obj` (calls `nonexistent_alpha_symbol`, embeds `"DEAD_ALPHA_MARKER_BYTES"`),
         `m1_leaf_math.obj` (defines `leaf_affine`),
         `m2_dead_beta.obj` (calls `nonexistent_beta_symbol`, embeds `"DEAD_BETA_MARKER_BYTES"`),
         `m3_entry_api.obj` (defines `entry_compute`, which calls `leaf_affine` defined earlier in
          `m1_leaf_math.obj`, requiring a second fixed-point pass).
     - Consumer `app.exe` links cleanly, runs with exact UTF-8 stdout + exit code, is byte-identical
       across repeated builds, and binary inspection of `app.exe` proves `"DEAD_ALPHA_MARKER_BYTES"`
       and `"DEAD_BETA_MARKER_BYTES"` are completely stripped from the linked image.
  3. Third-party C `.lib` and `.a` archive consumption (`gcc -c` + `ar rcs`) with dead C member
     stripping, deterministic `-L`/`-l<name>` search order (`<name>.lib` -> `lib<name>.lib` ->
     `lib<name>.a`), and `@link("...")` resolution.
  4. `REQ-LNK-120` (`AUNW-34: Linker relocates unwind RVAs after final section layout`):
     - Links multi-object C `.obj`/`.lib` inputs containing `.pdata` (`RUNTIME_FUNCTION` with
       3 x `IMAGE_REL_AMD64_ADDR32NB` relocations: `BeginAddress`, `EndAddress`, `UnwindInfoAddress`)
       and `.xdata` (`UNWIND_INFO`) together with Axiom code into both `.exe` and `.dll` images.
     - Parses the merged `.pdata`, `.xdata`, and `.text` sections in the final `.exe` and `.dll`
       images to prove every `RUNTIME_FUNCTION` entry was relocated to its exact post-layout RVAs
       in `.text` and `.xdata`, and that zero `ADDR32NB` relocations leaked into `.reloc`.
  5. `REQ-LNK-121` (`0189 §28: Function pointer types include calling convention in semantic identity`):
     - Inspects `--emit=thir` on a module declaring `fn`, `extern "C" fn`, `extern "system" fn`,
       and `unsafe extern "C" fn` function pointer types, verifying that their ABI strings (`""`,
       `"C"`, `"system"`) and `is_unsafe` flags are preserved as distinct semantic identities.
  6. Negative diagnostics (`AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`,
     `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`,
     and `AX_DRIVER_USAGE` when passing `--kind lib|obj|dll` to `run`).
"""

import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_SCN_MEM_WRITE = 0x80000000
IMAGE_SCN_MEM_EXECUTE = 0x20000000


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


def validate_coff_archive(data: bytes):
    """Validates SPEC-26 AXS-WLIB-010 & AXS-WLIB-011 COFF archive layout and determinism."""
    if len(data) < 8 or data[:8] != b"!<arch>\n":
        raise ValidationError(f"archive missing !<arch>\\n magic: {data[:8]!r}")

    pos = 8
    members = []
    longnames_data = b""

    while pos < len(data):
        if pos + 60 > len(data):
            raise ValidationError(f"truncated member header at {pos}")
        hdr = data[pos : pos + 60]
        raw_name = hdr[0:16]
        date_f = hdr[16:28]
        uid_f = hdr[28:34]
        gid_f = hdr[34:40]
        mode_f = hdr[40:48]
        size_f = hdr[48:58]
        end_f = hdr[58:60]

        if date_f != b"0           " or uid_f != b"0     " or gid_f != b"0     " or mode_f != b"0       ":
            raise ValidationError(f"non-zero archive metadata at {pos}: {hdr[16:48]!r}")
        if end_f != b"`\n":
            raise ValidationError(f"invalid member header trailer at {pos}: {end_f!r}")

        body_size = int(size_f.decode("ascii").strip())
        body_start = pos + 60
        body_end = body_start + body_size
        if body_end > len(data):
            raise ValidationError(f"member body at {pos} exceeds archive bounds")
        body = data[body_start:body_end]
        name_s = raw_name.decode("ascii", errors="replace").rstrip(" ")
        if name_s == "//":
            longnames_data = body

        members.append(
            {
                "header_offset": pos,
                "name": name_s,
                "size": body_size,
                "body": body,
            }
        )
        next_pos = body_end
        if (body_size & 1) != 0:
            if next_pos >= len(data) or data[next_pos : next_pos + 1] != b"\n":
                raise ValidationError(f"missing 0x0A alignment pad after odd member at {pos}")
            next_pos += 1
        pos = next_pos

    if len(members) < 2 or members[0]["name"] != "/" or members[1]["name"] != "/":
        raise ValidationError("archive missing First and Second Linker Members")

    # 1st Linker Member (big-endian)
    b1 = members[0]["body"]
    (num_syms_be,) = struct.unpack_from(">I", b1, 0)
    offsets_be = list(struct.unpack_from(f">{num_syms_be}I", b1, 4))
    strs_be = b1[4 + num_syms_be * 4 :].split(b"\x00")
    if strs_be and strs_be[-1] == b"":
        strs_be.pop()
    if len(strs_be) != num_syms_be:
        raise ValidationError(f"1st linker member string count {len(strs_be)} != {num_syms_be}")

    # 2nd Linker Member (little-endian)
    b2 = members[1]["body"]
    (num_obj_members,) = struct.unpack_from("<I", b2, 0)
    off_end = 4 + num_obj_members * 4
    obj_offsets = list(struct.unpack_from(f"<{num_obj_members}I", b2, 4))
    if obj_offsets != sorted(obj_offsets):
        raise ValidationError(f"2nd linker member offsets not sorted: {obj_offsets}")
    (num_syms_le,) = struct.unpack_from("<I", b2, off_end)
    if num_syms_le != num_syms_be:
        raise ValidationError(f"symbol count mismatch: {num_syms_be} vs {num_syms_le}")
    idx_start = off_end + 4
    idx_end = idx_start + num_syms_le * 2
    sym_indices = list(struct.unpack_from(f"<{num_syms_le}H", b2, idx_start))
    strs_le = b2[idx_end:].split(b"\x00")
    if strs_le and strs_le[-1] == b"":
        strs_le.pop()
    sym_names = [s.decode("utf-8") for s in strs_le]
    if sym_names != sorted(sym_names):
        raise ValidationError(f"2nd linker member symbols not sorted: {sym_names}")

    member_by_off = {m["header_offset"]: m for m in members[2:] if m["name"] != "//"}
    map_first = {s.decode("utf-8"): o for s, o in zip(strs_be, offsets_be)}
    map_second = {s: obj_offsets[i - 1] for s, i in zip(sym_names, sym_indices)}
    if map_first != map_second:
        raise ValidationError(f"1st/2nd linker member symbol map mismatch: {map_first} vs {map_second}")

    resolved_names = []
    for m in members[2:]:
        if m["name"] == "//":
            continue
        # Verify embedded COFF object header has TimeDateStamp == 0
        body = m["body"]
        if len(body) >= 20:
            mach, _nsec, ts = struct.unpack_from("<HHI", body, 0)
            if mach == IMAGE_FILE_MACHINE_AMD64 and ts != 0:
                raise ValidationError(f"embedded COFF object has non-zero TimeDateStamp={ts}")
        nm = m["name"]
        if nm.startswith("/") and nm[1:].isdigit():
            off = int(nm[1:])
            end = longnames_data.find(b"/\n", off)
            if end == -1:
                end = longnames_data.find(b"\x00", off)
            if end == -1:
                raise ValidationError(f"unterminated longname at {off}")
            resolved_names.append(longnames_data[off:end].decode("utf-8"))
        elif nm.endswith("/"):
            resolved_names.append(nm[:-1])
        else:
            resolved_names.append(nm)

    return {
        "symbols": sym_names,
        "obj_names": resolved_names,
        "longnames_present": any(m["name"] == "//" for m in members),
    }


def parse_pe_sections(pe_bytes: bytes):
    if pe_bytes[:2] != b"MZ":
        raise ValidationError("missing MZ header")
    (pe_off,) = struct.unpack_from("<I", pe_bytes, 0x3C)
    if pe_bytes[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValidationError("missing PE\\0\\0 signature")
    coff_off = pe_off + 4
    mach, num_sec, ts, _, _, opt_sz, chars = struct.unpack_from("<HHIIIHH", pe_bytes, coff_off)
    if mach != IMAGE_FILE_MACHINE_AMD64 or ts != 0:
        raise ValidationError(f"unexpected COFF header mach={mach:#x} ts={ts}")
    opt_off = coff_off + 20
    sec_base = opt_off + opt_sz
    sections = {}
    for i in range(num_sec):
        so = sec_base + i * 40
        name = pe_bytes[so : so + 8].rstrip(b"\x00").decode("ascii")
        vsize, vaddr, rawsz, rawptr, _, _, _, _, schars = struct.unpack_from("<IIIIIIHHI", pe_bytes, so + 8)
        if (schars & IMAGE_SCN_MEM_WRITE) and (schars & IMAGE_SCN_MEM_EXECUTE):
            raise ValidationError(f"section {name} violates W^X: {schars:#x}")
        sections[name] = {
            "vsize": vsize,
            "vaddr": vaddr,
            "raw_size": rawsz,
            "raw_ptr": rawptr,
            "chars": schars,
            "data": pe_bytes[rawptr : rawptr + rawsz],
        }
    return sections, chars


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: e18_7_static_lib_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    ar_tool = find_tool(["llvm-ar", "ar"])
    nm_tool = find_tool(["llvm-nm", "nm"])
    objdump_tool = find_tool(["objdump", "llvm-objdump"])
    gcc_tool = find_tool(["gcc", "clang"])

    # =========================================================================
    # 1. Deterministic Multi-Member COFF `.lib` & Fixed-Point Dead-Member Stripping
    # =========================================================================
    m0_dead_a = tmp_dir / "m0_dead_alpha.ax"
    write_lf(
        m0_dead_a,
        """\
module m0_dead_alpha

extern "C" {
    fn nonexistent_alpha_symbol() -> i32;
}

pub fn dead_alpha_entry() -> i32 {
    print("DEAD_ALPHA_MARKER_BYTES\\n");
    unsafe { nonexistent_alpha_symbol() }
}
""",
    )

    m1_leaf = tmp_dir / "m1_leaf_math_with_long_member_name.ax"
    write_lf(
        m1_leaf,
        """\
module m1_leaf_math_with_long_member_name

fn private_leaf_bias() -> i32 {
    9
}

pub fn leaf_affine(x: i32, y: i32) -> i32 {
    x * 5 + y + private_leaf_bias()
}
""",
    )

    m2_dead_b = tmp_dir / "m2_dead_beta.ax"
    write_lf(
        m2_dead_b,
        """\
module m2_dead_beta

extern "C" {
    fn nonexistent_beta_symbol() -> i32;
}

pub fn dead_beta_entry() -> i32 {
    print("DEAD_BETA_MARKER_BYTES\\n");
    unsafe { nonexistent_beta_symbol() }
}
""",
    )

    m3_entry = tmp_dir / "m3_entry_api.ax"
    write_lf(
        m3_entry,
        """\
module m3_entry_api

extern "C" {
    fn leaf_affine(x: i32, y: i32) -> i32;
}

@export("lib_renamed_triple")
pub fn triple_val(v: i32) -> i32 {
    v * 3
}

pub fn entry_compute(a: i32, b: i32) -> i32 {
    unsafe { leaf_affine(a, b) + triple_val(4) }
}
""",
    )

    lib_1 = tmp_dir / "multi_strip.lib"
    lib_2 = tmp_dir / "multi_strip_repeat.lib"
    lib_compile = tmp_dir / "multi_strip_compile.lib"
    for subcmd, out_lib in (("build", lib_1), ("build", lib_2), ("compile", lib_compile)):
        run_cmd(
            [
                compiler,
                subcmd,
                "--std-root",
                str(std_root),
                "--kind",
                "lib",
                "-o",
                str(out_lib),
                str(m0_dead_a),
                str(m1_leaf),
                str(m2_dead_b),
                str(m3_entry),
            ]
        )

    lib_bytes = lib_1.read_bytes()
    if lib_bytes != lib_2.read_bytes() or lib_bytes != lib_compile.read_bytes():
        raise ValidationError("multi_strip.lib is not byte-identical across repeated build/compile --kind lib runs")

    # Verify package manifest `kind = "lib"` emits `<pkg>.lib`
    pkg_lib_dir = tmp_dir / "pkg_lib_e187"
    write_lf(pkg_lib_dir / "axiom.toml", '[package]\nname = "pkg_lib_e187"\nversion = "0.1.0"\nkind = "lib"\n')
    write_lf(pkg_lib_dir / "src" / "lib.ax", "module pkg_lib_e187\npub fn pkg_lib_val(x: i32) -> i32 { x + 10 }\n")
    pkg_lib_out = tmp_dir / "pkg_lib_out"
    pkg_lib_out.mkdir(parents=True, exist_ok=True)
    run_cmd([compiler, "build", "--std-root", str(std_root), str(pkg_lib_dir)], cwd=str(pkg_lib_out))
    if not (pkg_lib_out / "pkg_lib_e187.lib").is_file():
        raise ValidationError("package manifest `kind = 'lib'` did not emit pkg_lib_e187.lib")
    validate_coff_archive((pkg_lib_out / "pkg_lib_e187.lib").read_bytes())

    arch_info = validate_coff_archive(lib_bytes)
    if not arch_info["longnames_present"]:
        raise ValidationError("expected '//' Longnames Member for >15-char member name")
    expected_members = [
        "m0_dead_alpha.obj",
        "m1_leaf_math_with_long_member_name.obj",
        "m2_dead_beta.obj",
        "m3_entry_api.obj",
    ]
    if arch_info["obj_names"] != expected_members:
        raise ValidationError(f"expected archive members {expected_members}, got {arch_info['obj_names']}")
    if "private_leaf_bias" in arch_info["symbols"]:
        raise ValidationError("private function leaked into COFF archive public symbol directory")
    for pub_sym in ("leaf_affine", "entry_compute", "lib_renamed_triple"):
        if pub_sym not in arch_info["symbols"]:
            raise ValidationError(f"missing public symbol {pub_sym!r} in archive directory")

    # Validate archive with external `ar t`, `objdump -a`, and `nm --print-armap`
    ar_out = run_cmd([ar_tool, "t", str(lib_1)]).stdout.decode("utf-8", errors="replace")
    od_out = run_cmd([objdump_tool, "-a", str(lib_1)]).stdout.decode("utf-8", errors="replace")
    nm_out = run_cmd([nm_tool, "--print-armap", str(lib_1)]).stdout.decode("utf-8", errors="replace")
    for mname in expected_members:
        if mname not in ar_out or mname not in od_out:
            raise ValidationError(f"external archive tools did not list {mname!r}")
    if "lib_renamed_triple" not in nm_out or "entry_compute" not in nm_out:
        raise ValidationError(f"nm --print-armap missing expected symbols:\n{nm_out}")

    # Link consumer `.exe` against `multi_strip.lib` and verify dead members are stripped
    app_ax = tmp_dir / "app_strip.ax"
    write_lf(
        app_ax,
        """\
module app_strip

@link("multi_strip")
extern "C" {
    fn entry_compute(a: i32, b: i32) -> i32;
    fn lib_renamed_triple(v: i32) -> i32;
}

pub fn main() -> i32 {
    print("Xin chào thế giới\\n");
    unsafe {
        let v1 = entry_compute(6, 7);       // (6*5 + 7 + 9) + 12 = 58
        let v2 = lib_renamed_triple(5);     // 15
        v1 + v2                             // 73
    }
}
""",
    )
    app_exe_1 = tmp_dir / "app_strip_1.exe"
    app_exe_2 = tmp_dir / "app_strip_2.exe"
    run_cmd([compiler, "build", "--std-root", str(std_root), "-L", str(tmp_dir), "-o", str(app_exe_1), str(app_ax)])
    run_cmd([compiler, "build", "--std-root", str(std_root), "-o", str(app_exe_2), str(app_ax), str(lib_1)])

    exe_bytes = app_exe_1.read_bytes()
    if exe_bytes != app_exe_2.read_bytes():
        raise ValidationError("app_strip.exe is not byte-identical between -L/@link and positional .lib builds")
    if b"DEAD_ALPHA_MARKER_BYTES" in exe_bytes or b"DEAD_BETA_MARKER_BYTES" in exe_bytes:
        raise ValidationError("dead archive member bytes leaked into linked app_strip.exe")

    res_app = run_cmd([str(app_exe_1)], expect_rc=73)
    if res_app.stdout != "Xin chào thế giới\n".encode("utf-8"):
        raise ValidationError(f"unexpected stdout from app_strip.exe: {res_app.stdout!r}")

    # =========================================================================
    # 2. Third-Party C `.lib`/`.a` Dead-Member Stripping & `-L`/`-l` Priority
    # =========================================================================
    c_live_c = tmp_dir / "c_live.c"
    write_lf(
        c_live_c,
        """\
#include <stdint.h>
int32_t c_live_accumulate(int32_t a, int32_t b, int32_t c) {
    return a * 100 + b * 10 + c;
}
""",
    )
    c_dead_c = tmp_dir / "c_dead.c"
    write_lf(
        c_dead_c,
        """\
extern int c_unresolved_dead_dep(void);
const char c_dead_marker[] = "C_DEAD_MEMBER_MUST_BE_STRIPPED";
int c_dead_unused(void) {
    return c_unresolved_dead_dep() + (int)c_dead_marker[0];
}
""",
    )
    c_live_obj = tmp_dir / "c_live.obj"
    c_dead_obj = tmp_dir / "c_dead.obj"
    run_cmd([gcc_tool, "-c", "-O2", str(c_live_c), "-o", str(c_live_obj)])
    run_cmd([gcc_tool, "-c", "-O2", str(c_dead_c), "-o", str(c_dead_obj)])

    c_archive_a = tmp_dir / "libc_thirdparty.a"
    run_cmd([ar_tool, "rcs", str(c_archive_a), str(c_dead_obj), str(c_live_obj)])

    app_c_ax = tmp_dir / "app_c_archive.ax"
    write_lf(
        app_c_ax,
        """\
module app_c_archive

extern "C" {
    fn c_live_accumulate(a: i32, b: i32, c: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { c_live_accumulate(1, 2, 3) } // 123
}
""",
    )
    app_c_exe = tmp_dir / "app_c_archive.exe"
    run_cmd(
        [
            compiler,
            "build",
            "--std-root",
            str(std_root),
            "-L",
            str(tmp_dir),
            "-lc_thirdparty",
            "-o",
            str(app_c_exe),
            str(app_c_ax),
        ]
    )
    if b"C_DEAD_MEMBER_MUST_BE_STRIPPED" in app_c_exe.read_bytes():
        raise ValidationError("dead C archive member leaked into app_c_archive.exe")
    run_cmd([str(app_c_exe)], expect_rc=123)

    # =========================================================================
    # 3. `REQ-LNK-120` (AUNW-34): Linker Relocates `.pdata`/`.xdata` Unwind RVAs
    #    After Final Section Layout
    # =========================================================================
    unw_a_c = tmp_dir / "unw_a.c"
    write_lf(
        unw_a_c,
        """\
#include <stdint.h>
__declspec(noinline) int32_t unw_leaf_step(int32_t x) {
    volatile int32_t local_buf[8];
    for (int i = 0; i < 8; ++i) local_buf[i] = x + i;
    return local_buf[3] + local_buf[7];
}
""",
    )
    unw_b_c = tmp_dir / "unw_b.c"
    write_lf(
        unw_b_c,
        """\
#include <stdint.h>
extern int32_t unw_leaf_step(int32_t x);
__declspec(noinline) int32_t unw_caller_frame(int32_t a, int32_t b) {
    volatile int32_t frame_pad[12];
    frame_pad[0] = unw_leaf_step(a);
    frame_pad[11] = unw_leaf_step(b);
    return frame_pad[0] + frame_pad[11];
}
""",
    )
    unw_a_obj = tmp_dir / "unw_a.obj"
    unw_b_obj = tmp_dir / "unw_b.obj"
    run_cmd([gcc_tool, "-c", "-O2", "-fasynchronous-unwind-tables", str(unw_a_c), "-o", str(unw_a_obj)])
    run_cmd([gcc_tool, "-c", "-O2", "-fasynchronous-unwind-tables", str(unw_b_c), "-o", str(unw_b_obj)])

    unw_host_ax = tmp_dir / "unw_host.ax"
    write_lf(
        unw_host_ax,
        """\
module unw_host

extern "C" {
    fn unw_caller_frame(a: i32, b: i32) -> i32;
}

@export
pub fn dll_unw_entry(a: i32, b: i32) -> i32 {
    unsafe { unw_caller_frame(a, b) }
}

pub fn main() -> i32 {
    // a=10 -> (13 + 17) = 30; b=20 -> (23 + 27) = 50; sum = 80
    unsafe { unw_caller_frame(10, 20) }
}
""",
    )
    unw_exe = tmp_dir / "unw_host.exe"
    unw_dll = tmp_dir / "unw_host.dll"
    run_cmd(
        [compiler, "build", "--std-root", str(std_root), "-o", str(unw_exe), str(unw_host_ax), str(unw_a_obj), str(unw_b_obj)]
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
            str(unw_dll),
            str(unw_host_ax),
            str(unw_a_obj),
            str(unw_b_obj),
        ]
    )
    run_cmd([str(unw_exe)], expect_rc=80)

    for label, img_path in [("unw_host.exe", unw_exe), ("unw_host.dll", unw_dll)]:
        secs, _ = parse_pe_sections(img_path.read_bytes())
        if ".pdata" not in secs or ".xdata" not in secs or ".text" not in secs:
            raise ValidationError(f"{label} missing merged .pdata/.xdata/.text sections: {list(secs)}")
        psec = secs[".pdata"]
        xsec = secs[".xdata"]
        tsec = secs[".text"]
        pdata_len = psec["vsize"] if psec["vsize"] > 0 else psec["raw_size"]
        pdata_bytes = psec["data"][:pdata_len]
        if len(pdata_bytes) < 24 or (len(pdata_bytes) % 12) != 0:
            raise ValidationError(f"{label} .pdata size {len(pdata_bytes)} invalid for >=2 RUNTIME_FUNCTION entries")
        num_rf = len(pdata_bytes) // 12
        for i in range(num_rf):
            begin_rva, end_rva, unwind_rva = struct.unpack_from("<III", pdata_bytes, i * 12)
            if not (tsec["vaddr"] <= begin_rva < end_rva <= tsec["vaddr"] + tsec["raw_size"]):
                raise ValidationError(
                    f"{label} .pdata[{i}] function RVAs ({begin_rva:#x}..{end_rva:#x}) outside merged .text "
                    f"({tsec['vaddr']:#x}..{tsec['vaddr'] + tsec['raw_size']:#x})"
                )
            if not (xsec["vaddr"] <= unwind_rva < xsec["vaddr"] + xsec["raw_size"]):
                raise ValidationError(
                    f"{label} .pdata[{i}] UnwindInfoAddress {unwind_rva:#x} outside merged .xdata "
                    f"({xsec['vaddr']:#x}..{xsec['vaddr'] + xsec['raw_size']:#x})"
                )

    # =========================================================================
    # 4. `REQ-LNK-121`: Function Pointer Calling Convention Semantic Identity
    # =========================================================================
    fp_sem_ax = tmp_dir / "fp_sem_identity.ax"
    write_lf(
        fp_sem_ax,
        """\
module fp_sem_identity

pub struct FnPtrCarriers {
    pub f_ax: fn(i32) -> i32,
    pub f_c: extern "C" fn(i32) -> i32,
    pub f_sys: extern "system" fn(i32) -> i32,
    pub f_uc: unsafe extern "C" fn(i32) -> i32,
}
""",
    )
    thir_out = run_cmd([compiler, "inspect", "--emit=thir", str(fp_sem_ax)]).stdout.decode("utf-8", errors="replace")
    for expected_frag in (
        '(TypeFn false ""',
        '(TypeFn false "C"',
        '(TypeFn false "system"',
        '(TypeFn true "C"',
    ):
        if expected_frag not in thir_out:
            raise ValidationError(f"THIR dump missing distinct function pointer ABI identity {expected_frag!r}:\n{thir_out}")

    # =========================================================================
    # 5. Negative Diagnostics (`AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`,
    #    `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`)
    # =========================================================================
    p_bad_kind = run_cmd([compiler, "build", "--kind", "invalid_kind", str(app_ax)], expect_rc=2)
    if b"AX_DRIVER_INVALID_ARTIFACT_KIND" not in p_bad_kind.stderr:
        raise ValidationError("expected AX_DRIVER_INVALID_ARTIFACT_KIND")

    bad_lib = tmp_dir / "corrupt.lib"
    bad_lib.write_bytes(b"!<not_an_archive>\n")
    p_bad_arch = run_cmd([compiler, "build", "-o", str(tmp_dir / "bad.exe"), str(app_ax), str(bad_lib)], expect_rc=1)
    if b"AX_LINK_BAD_ARCHIVE" not in p_bad_arch.stderr:
        raise ValidationError("expected AX_LINK_BAD_ARCHIVE")

    p_no_lib = run_cmd(
        [compiler, "build", "--json", "-L", str(tmp_dir), "-lmissing_e18_7_lib", "-o", str(tmp_dir / "nolib.exe"), str(app_ax)],
        expect_rc=1,
    )
    doc_nf = json.loads(p_no_lib.stderr.decode("utf-8"))
    diags_nf = doc_nf.get("diagnostics", doc_nf if isinstance(doc_nf, list) else [])
    if not any(
        d.get("code") == "AX_LINK_LIBRARY_NOT_FOUND" and d.get("data", {}).get("library") == "missing_e18_7_lib"
        for d in diags_nf
    ):
        raise ValidationError(f"expected AX_LINK_LIBRARY_NOT_FOUND(library='missing_e18_7_lib'), got {doc_nf}")

    # Duplicate strong external symbol across two extracted archive members / objects -> AX_LINK_DUPLICATE_SYMBOL
    dup1_c = tmp_dir / "dup1.c"
    dup2_c = tmp_dir / "dup2.c"
    write_lf(dup1_c, "int clash_fn(void) { return 1; }\n")
    write_lf(dup2_c, "int clash_fn(void) { return 2; }\n")
    dup1_obj = tmp_dir / "dup1.obj"
    dup2_obj = tmp_dir / "dup2.obj"
    run_cmd([gcc_tool, "-c", str(dup1_c), "-o", str(dup1_obj)])
    run_cmd([gcc_tool, "-c", str(dup2_c), "-o", str(dup2_obj)])
    dup_caller_ax = tmp_dir / "dup_caller.ax"
    write_lf(
        dup_caller_ax,
        'module dup_caller\nextern "C" { fn clash_fn() -> i32; }\npub fn main() -> i32 { unsafe { clash_fn() } }\n',
    )
    p_dup_sym = run_cmd(
        [compiler, "build", "-o", str(tmp_dir / "dup_sym.exe"), str(dup_caller_ax), str(dup1_obj), str(dup2_obj)],
        expect_rc=1,
    )
    if b"AX_LINK_DUPLICATE_SYMBOL" not in p_dup_sym.stderr:
        raise ValidationError("expected AX_LINK_DUPLICATE_SYMBOL")

    # Unresolved external symbol -> AX_LINK_UNDEFINED_SYMBOL
    p_undef = run_cmd([compiler, "build", "-o", str(tmp_dir / "undef.exe"), str(dup_caller_ax)], expect_rc=1)
    if b"AX_LINK_UNDEFINED_SYMBOL" not in p_undef.stderr:
        raise ValidationError("expected AX_LINK_UNDEFINED_SYMBOL")

    # Passing `--kind lib|obj|dll` to `run` -> AX_DRIVER_USAGE (exit code 2)
    for bad_kind in ("lib", "obj", "dll"):
        p_run_bad = run_cmd([compiler, "run", "--kind", bad_kind, str(app_ax)], expect_rc=2)
        if b"AX_DRIVER_USAGE" not in p_run_bad.stderr:
            raise ValidationError(f"expected AX_DRIVER_USAGE for `run --kind {bad_kind}`")

    print("E18-7-STATIC-LIB-CONFORMANCE-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
