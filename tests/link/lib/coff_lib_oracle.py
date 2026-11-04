#!/usr/bin/env python3
"""End-to-end oracle for T750 (E18.7): COFF archive (.lib) writer & reader, --kind lib, -L/-l (SPEC-26).

Verifies:
  1. `axiomc build --kind lib` produces a deterministic Microsoft PE/COFF archive (`!<arch>\\n`)
     with 0-filled Date/UID/GID/Mode headers, First Linker Member (big-endian), Second Linker
     Member (little-endian, sorted symbols), Longnames Member (`//` for >15-char names), and
     `0x0A` 2-byte alignment padding; accepted by `llvm-ar`/`ar` and `llvm-nm`/`nm`.
  2. Building `math.lib` from Axiom source (`pub fn`, `@export("math_triple")`, private `fn` excluded
     from public symbol directory) and linking `app.exe` via positional `math.lib`, `-L/-lmath`,
     and `@link("math")` + `-L`, then executing `app.exe` and checking stdout + exit code.
  3. Multi-member demand-driven fixed-point archive extraction: `multi.lib` containing
     `m0_unused.obj` (which references an undefined symbol), `m1_helper.obj`, and `m2_entry.obj`
     (which calls `m1_helper` defined earlier in the archive); linking `app_multi.exe` succeeds
     without pulling in `m0_unused.obj` and resolves `m1_helper.obj` on the second pass.
  4. Interoperability with C `.lib`/`.a` archives produced by `clang`/`gcc` + `llvm-ar`/`ar`
     (and `axiomc build --kind lib` from `.obj` inputs) via `extern "C" fn`, plus COFF Short
     Import Objects (`Sig1=0x0000, Sig2=0xFFFF`).
  5. Negative diagnostics: `AX_DRIVER_INVALID_ARTIFACT_KIND` (exit code 2), `AX_LINK_BAD_ARCHIVE`,
     and `AX_LINK_LIBRARY_NOT_FOUND`.
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


def find_tool(names):
    path_env = os.environ.get("PATH", "")
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.isdir(msys_bin) and msys_bin not in path_env:
        path_env = msys_bin + os.pathsep + path_env
    for name in names:
        found = shutil.which(name, path=path_env)
        if found:
            return found
    raise ValidationError(f"required tool not found in PATH: {names}")


def run_cmd(cmd, cwd=None, expect_rc=0):
    env = dict(os.environ)
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.isdir(msys_bin) and msys_bin not in env.get("PATH", ""):
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


def parse_and_validate_coff_archive(data: bytes):
    """Parses a COFF archive (.lib) and verifies SPEC-26 §3.1 invariants."""
    if len(data) < 8 or data[:8] != b"!<arch>\n":
        raise ValidationError(f"archive missing !<arch>\\n magic: {data[:8]!r}")

    pos = 8
    members = []
    longnames_data = b""

    while pos < len(data):
        if pos + 60 > len(data):
            raise ValidationError(f"truncated member header at offset {pos}")
        hdr = data[pos : pos + 60]
        raw_name = hdr[0:16]
        date_f = hdr[16:28]
        uid_f = hdr[28:34]
        gid_f = hdr[34:40]
        mode_f = hdr[40:48]
        size_f = hdr[48:58]
        end_f = hdr[58:60]

        if date_f != b"0           ":
            raise ValidationError(f"non-deterministic Date field at {pos}: {date_f!r}")
        if uid_f != b"0     ":
            raise ValidationError(f"non-deterministic UID field at {pos}: {uid_f!r}")
        if gid_f != b"0     ":
            raise ValidationError(f"non-deterministic GID field at {pos}: {gid_f!r}")
        if mode_f != b"0       ":
            raise ValidationError(f"non-deterministic Mode field at {pos}: {mode_f!r}")
        if end_f != b"`\n":
            raise ValidationError(f"invalid member header trailer at {pos}: {end_f!r}")

        try:
            body_size = int(size_f.decode("ascii").strip())
        except ValueError as exc:
            raise ValidationError(f"invalid member size field at {pos}: {size_f!r}") from exc

        body_start = pos + 60
        body_end = body_start + body_size
        if body_end > len(data):
            raise ValidationError(f"member body at {pos} exceeds archive size")
        body = data[body_start:body_end]

        name_s = raw_name.decode("ascii", errors="replace").rstrip(" ")
        if name_s == "//":
            longnames_data = body

        members.append(
            {
                "header_offset": pos,
                "raw_name": raw_name,
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

    if len(members) < 2:
        raise ValidationError(f"expected at least First and Second Linker Members, got {len(members)}")

    # 1. Validate First Linker Member ("/")
    m1 = members[0]
    if m1["name"] != "/":
        raise ValidationError(f"first member must be '/', got {m1['name']!r}")
    b1 = m1["body"]
    if len(b1) < 4:
        raise ValidationError("First Linker Member too small")
    (num_syms_be,) = struct.unpack(">I", b1[:4])
    if len(b1) < 4 + num_syms_be * 4:
        raise ValidationError("First Linker Member truncated offsets")
    offsets_be = list(struct.unpack(f">{num_syms_be}I", b1[4 : 4 + num_syms_be * 4]))
    strs_be = b1[4 + num_syms_be * 4 :].split(b"\x00")
    if strs_be and strs_be[-1] == b"":
        strs_be.pop()
    if len(strs_be) != num_syms_be:
        raise ValidationError(f"First Linker Member string count {len(strs_be)} != {num_syms_be}")

    # 2. Validate Second Linker Member ("/")
    m2 = members[1]
    if m2["name"] != "/":
        raise ValidationError(f"second member must be '/', got {m2['name']!r}")
    b2 = m2["body"]
    if len(b2) < 8:
        raise ValidationError("Second Linker Member too small")
    (num_obj_members,) = struct.unpack("<I", b2[:4])
    off_end = 4 + num_obj_members * 4
    obj_offsets = list(struct.unpack(f"<{num_obj_members}I", b2[4:off_end]))
    if obj_offsets != sorted(obj_offsets):
        raise ValidationError(f"Second Linker Member offsets not sorted: {obj_offsets}")
    (num_syms_le,) = struct.unpack("<I", b2[off_end : off_end + 4])
    if num_syms_le != num_syms_be:
        raise ValidationError(f"symbol count mismatch between linker members: {num_syms_be} vs {num_syms_le}")
    idx_start = off_end + 4
    idx_end = idx_start + num_syms_le * 2
    sym_indices = list(struct.unpack(f"<{num_syms_le}H", b2[idx_start:idx_end]))
    strs_le = b2[idx_end:].split(b"\x00")
    if strs_le and strs_le[-1] == b"":
        strs_le.pop()
    sym_names = [s.decode("utf-8") for s in strs_le]
    if sym_names != sorted(sym_names):
        raise ValidationError(f"Second Linker Member symbols not lexicographically sorted: {sym_names}")

    # Verify every offset in First and Second Linker Members points to an actual object member header
    member_by_off = {m["header_offset"]: m for m in members[2:] if m["name"] != "//"}
    for off in obj_offsets:
        if off not in member_by_off:
            raise ValidationError(f"Second Linker Member offset {off} does not point to an object member header")
    map_first = {}
    for s_bytes, off_be in zip(strs_be, offsets_be):
        if off_be not in member_by_off:
            raise ValidationError(f"First Linker Member offset {off_be} does not point to an object member header")
        map_first[s_bytes.decode("utf-8")] = off_be
    map_second = {}
    for s_name, idx1 in zip(sym_names, sym_indices):
        if idx1 < 1 or idx1 > num_obj_members:
            raise ValidationError(f"invalid 1-based member index {idx1} in Second Linker Member")
        map_second[s_name] = obj_offsets[idx1 - 1]
    if map_first != map_second:
        raise ValidationError(f"First/Second Linker Member symbol->offset map mismatch: {map_first} vs {map_second}")

    # Resolve longnames if "//" is present
    resolved_obj_names = []
    for m in members[2:]:
        if m["name"] == "//":
            continue
        nm = m["name"]
        if nm.startswith("/") and nm[1:].isdigit():
            off = int(nm[1:])
            end = longnames_data.find(b"/\n", off)
            if end == -1:
                end = longnames_data.find(b"\x00", off)
            if end == -1:
                raise ValidationError(f"unterminated longname at offset {off}")
            resolved_obj_names.append(longnames_data[off:end].decode("utf-8"))
        elif nm.endswith("/"):
            resolved_obj_names.append(nm[:-1])
        else:
            resolved_obj_names.append(nm)

    return {
        "members": members,
        "symbols": sym_names,
        "obj_names": resolved_obj_names,
        "longnames_present": any(m["name"] == "//" for m in members),
    }


def make_short_import_member(sym_name: str, dll_name: str, hint: int = 0, name_type: int = 1) -> bytes:
    """Builds a 20-byte COFF Short Import Header + sym_name\\0 + dll_name\\0."""
    payload = sym_name.encode("ascii") + b"\x00" + dll_name.encode("ascii") + b"\x00"
    type_info = (0 & 0x3) | ((name_type & 0x7) << 2)  # IMPORT_OBJECT_CODE (0)
    hdr = struct.pack(
        "<HHHHIIHH",
        0x0000,          # Sig1
        0xFFFF,          # Sig2
        0,               # Version
        0x8664,          # Machine (AMD64)
        0,               # TimeDateStamp
        len(payload),    # SizeOfData
        hint,            # Ordinal/Hint
        type_info,       # Type
    )
    return hdr + payload


def build_short_import_archive(sym_name: str, dll_name: str) -> bytes:
    """Creates a minimal COFF archive containing a First Linker Member and one Short Import Object."""
    imp_member_body = make_short_import_member(sym_name, dll_name, hint=42, name_type=1)
    imp_sym = f"__imp_{sym_name}".encode("ascii")
    bare_sym = sym_name.encode("ascii")

    # First Linker Member has 2 symbols: bare_sym and __imp_<sym>
    str_table = bare_sym + b"\x00" + imp_sym + b"\x00"
    linker_body_len = 4 + 2 * 4 + len(str_table)
    first_member_total = 60 + linker_body_len + (1 if (linker_body_len & 1) else 0)
    imp_header_off = 8 + first_member_total

    linker_body = struct.pack(">III", 2, imp_header_off, imp_header_off) + str_table

    def fmt_hdr(name: str, size: int) -> bytes:
        return (
            f"{name:<16}"
            f"{'0':<12}"
            f"{'0':<6}"
            f"{'0':<6}"
            f"{'0':<8}"
            f"{size:<10}"
            "`\n"
        ).encode("ascii")

    out = bytearray(b"!<arch>\n")
    out += fmt_hdr("/", len(linker_body))
    out += linker_body
    if len(linker_body) & 1:
        out += b"\n"
    out += fmt_hdr(f"{dll_name}/", len(imp_member_body))
    out += imp_member_body
    if len(imp_member_body) & 1:
        out += b"\n"
    return bytes(out)


def main():
    if len(sys.argv) < 4:
        print("usage: coff_lib_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    ar_tool = find_tool(["llvm-ar", "ar"])
    nm_tool = find_tool(["llvm-nm", "nm"])
    objdump_tool = find_tool(["llvm-objdump", "objdump"])
    cc_tool = find_tool(["clang", "gcc"])

    # =========================================================================
    # 1. Build `math.lib` with `--kind lib`, verify archive structure & tools
    # =========================================================================
    math_ax = tmp_dir / "math.ax"
    math_ax.write_text(
        """\
module math

fn internal_bias() -> i32 {
    7
}

pub fn add(a: i32, b: i32) -> i32 {
    a + b + internal_bias()
}

pub fn mul(a: i32, b: i32) -> i32 {
    a * b
}

@export("math_triple")
pub fn triple(x: i32) -> i32 {
    x * 3
}
""",
        encoding="utf-8",
    )

    math_lib_1 = tmp_dir / "math.lib"
    math_lib_2 = tmp_dir / "math_repeat.lib"
    run_cmd([compiler, "build", "--kind", "lib", "-o", str(math_lib_1), str(math_ax)])
    run_cmd([compiler, "build", "--kind", "lib", "-o", str(math_lib_2), str(math_ax)])

    bytes_1 = math_lib_1.read_bytes()
    bytes_2 = math_lib_2.read_bytes()
    if bytes_1 != bytes_2:
        raise ValidationError("math.lib build is not byte-for-byte deterministic")

    info = parse_and_validate_coff_archive(bytes_1)
    if "math.obj" not in info["obj_names"]:
        raise ValidationError(f"expected math.obj in archive members, got {info['obj_names']}")
    for expected_sym in ("add", "mul", "math_triple"):
        if expected_sym not in info["symbols"]:
            raise ValidationError(f"expected public symbol {expected_sym!r} in archive index {info['symbols']}")
    if "internal_bias" in info["symbols"]:
        raise ValidationError(f"private fn 'internal_bias' must not be in public archive index: {info['symbols']}")

    # External tool validation (`llvm-ar t`, `llvm-objdump -a`, and `llvm-nm --print-armap`)
    ar_res = run_cmd([ar_tool, "t", str(math_lib_1)])
    ar_out = ar_res.stdout.decode("utf-8", errors="replace")
    if "math.obj" not in ar_out:
        raise ValidationError(f"{ar_tool} t did not list math.obj:\n{ar_out}")

    od_res = run_cmd([objdump_tool, "-a", str(math_lib_1)])
    od_out = od_res.stdout.decode("utf-8", errors="replace")
    if "math.obj" not in od_out:
        raise ValidationError(f"{objdump_tool} -a did not list math.obj:\n{od_out}")

    nm_res = run_cmd([nm_tool, "--print-armap", str(math_lib_1)])
    nm_out = nm_res.stdout.decode("utf-8", errors="replace")
    for expected_sym in ("add", "mul", "math_triple"):
        if expected_sym not in nm_out:
            raise ValidationError(f"{nm_tool} --print-armap missing {expected_sym!r}:\n{nm_out}")

    # Test `compile` subcommand alias and default `<stem>.lib` output when `-o` is omitted
    def_dir = tmp_dir / "def_out_test"
    def_dir.mkdir(parents=True, exist_ok=True)
    run_cmd([compiler, "compile", "--kind", "lib", str(math_ax)], cwd=str(def_dir))
    def_math_lib = def_dir / "math.lib"
    if not def_math_lib.is_file() or def_math_lib.read_bytes() != bytes_1:
        raise ValidationError("`compile --kind lib` without -o did not produce byte-identical math.lib")

    # Test Longnames Member ("//") with >15 character module filename
    long_ax = tmp_dir / "very_long_module_name_exceeding_fifteen.ax"
    long_ax.write_text(
        """\
module very_long_module_name_exceeding_fifteen

pub fn long_fn() -> i32 {
    99
}
""",
        encoding="utf-8",
    )
    long_lib = tmp_dir / "long_test.lib"
    run_cmd([compiler, "build", "--kind", "lib", "-o", str(long_lib), str(long_ax)])
    long_info = parse_and_validate_coff_archive(long_lib.read_bytes())
    if not long_info["longnames_present"]:
        raise ValidationError("expected '//' Longnames Member for >15-char member name")
    if "very_long_module_name_exceeding_fifteen.obj" not in long_info["obj_names"]:
        raise ValidationError(f"long member name not resolved: {long_info['obj_names']}")
    ar_long = run_cmd([ar_tool, "t", str(long_lib)]).stdout.decode("utf-8", errors="replace")
    if "very_long_module_name_exceeding_fifteen.obj" not in ar_long:
        raise ValidationError(f"{ar_tool} t failed on longnames archive:\n{ar_long}")
    od_long = run_cmd([objdump_tool, "-a", str(long_lib)]).stdout.decode("utf-8", errors="replace")
    if "very_long_module_name_exceeding_fifteen.obj" not in od_long:
        raise ValidationError(f"{objdump_tool} -a failed on longnames archive:\n{od_long}")

    # Test `axiom.toml` with `kind = "lib"` and default output path derivation (without `-o`)
    pkg_dir = tmp_dir / "pkg_lib_test"
    (pkg_dir / "src").mkdir(parents=True, exist_ok=True)
    (pkg_dir / "axiom.toml").write_text(
        '[package]\nname = "pkg_lib_test"\nversion = "0.1.0"\nkind = "lib"\n',
        encoding="utf-8",
    )
    (pkg_dir / "src" / "lib.ax").write_text(
        "module pkg_lib_test\npub fn pkg_val() -> i32 { 55 }\n",
        encoding="utf-8",
    )
    run_cmd([compiler, "build", str(pkg_dir)], cwd=str(def_dir))
    pkg_out_lib = def_dir / "pkg_lib_test.lib"
    if not pkg_out_lib.is_file():
        raise ValidationError("`build <pkg_dir>` with manifest kind='lib' did not write pkg_lib_test.lib")
    pkg_info = parse_and_validate_coff_archive(pkg_out_lib.read_bytes())
    if "pkg_val" not in pkg_info["symbols"]:
        raise ValidationError(f"expected pkg_val in package .lib symbols: {pkg_info['symbols']}")

    # =========================================================================
    # 2. Link `app.exe` against `math.lib` (positional, `-L/-l`, `@link`)
    # =========================================================================
    app_ax = tmp_dir / "app.ax"
    app_ax.write_text(
        """\
module app

extern "C" {
    fn add(a: i32, b: i32) -> i32;
    fn mul(a: i32, b: i32) -> i32;
    fn math_triple(x: i32) -> i32;
}

pub fn main() -> i32 {
    print("Xin chào thế giới\\n");
    let s = unsafe { add(10, 20) };        // 10 + 20 + 7 = 37
    let p = unsafe { mul(4, 5) };          // 20
    let t = unsafe { math_triple(6) };     // 18
    let extra = 2;
    s + p + t + extra                      // 37 + 20 + 18 + 2 = 77
}
""",
        encoding="utf-8",
    )

    # (a) Positional `math.lib`
    app_pos_exe = tmp_dir / "app_pos.exe"
    run_cmd([compiler, "build", "-o", str(app_pos_exe), str(app_ax), str(math_lib_1)])
    res_pos = run_cmd([str(app_pos_exe)], expect_rc=77)
    if res_pos.stdout != "Xin chào thế giới\n".encode("utf-8"):
        raise ValidationError(f"unexpected stdout from app_pos.exe: {res_pos.stdout!r}")

    # (b) `-L <tmp_dir> -lmath`
    app_flag_exe = tmp_dir / "app_flag.exe"
    run_cmd([compiler, "build", "-o", str(app_flag_exe), "-L", str(tmp_dir), "-lmath", str(app_ax)])
    res_flag = run_cmd([str(app_flag_exe)], expect_rc=77)
    if res_flag.stdout != "Xin chào thế giới\n".encode("utf-8"):
        raise ValidationError(f"unexpected stdout from app_flag.exe: {res_flag.stdout!r}")

    # (c) `@link("math")` in source + `-L <tmp_dir>`
    app_attr_ax = tmp_dir / "app_attr.ax"
    app_attr_ax.write_text(
        """\
module app_attr

@link("math")
extern "C" {
    fn add(a: i32, b: i32) -> i32;
    fn math_triple(x: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { add(3, 4) + math_triple(5) } // (3 + 4 + 7) + 15 = 29
}
""",
        encoding="utf-8",
    )
    app_attr_exe = tmp_dir / "app_attr.exe"
    run_cmd([compiler, "build", "-o", str(app_attr_exe), "-L", str(tmp_dir), str(app_attr_ax)])
    run_cmd([str(app_attr_exe)], expect_rc=29)

    # (d) Direct `@link("qa1.lib")` and `@link("sub/qa_sub.lib")` with NO `-L` / `-l` flags
    #     (Round 1 QA Finding 2: SPEC-26 AXS-WLIB-003 items 1-2)
    qa1_dir = tmp_dir / "direct_attr_test"
    (qa1_dir / "sub").mkdir(parents=True, exist_ok=True)
    qa1_src = qa1_dir / "qa1_mod.ax"
    qa1_src.write_text(
        "module qa1_mod\npub fn mid_calc(x: i32) -> i32 { x * 4 + 3 }\n",
        encoding="utf-8",
    )
    qa1_lib = qa1_dir / "qa1.lib"
    qa_sub_lib = qa1_dir / "sub" / "qa_sub.lib"
    run_cmd([compiler, "build", "--kind", "lib", "-o", str(qa1_lib), str(qa1_src)])
    shutil.copyfile(qa1_lib, qa_sub_lib)

    direct_attr_ax = qa1_dir / "direct_attr.ax"
    direct_attr_ax.write_text(
        """\
module direct_attr

@link("qa1.lib")
extern "C" {
    fn mid_calc(x: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { mid_calc(10) } // 43
}
""",
        encoding="utf-8",
    )
    direct_attr_exe = qa1_dir / "direct_attr.exe"
    run_cmd([compiler, "build", "-o", str(direct_attr_exe), "direct_attr.ax"], cwd=str(qa1_dir))
    run_cmd([str(direct_attr_exe)], cwd=str(qa1_dir), expect_rc=43)
    od_direct = run_cmd([objdump_tool, "-p", str(direct_attr_exe)]).stdout.decode("utf-8", errors="replace")
    if "qa1.lib" in od_direct.lower() or "qa1.dll" in od_direct.lower():
        raise ValidationError(f"direct_attr.exe must statically link qa1.lib, not DLL-import it:\n{od_direct}")

    direct_sub_ax = qa1_dir / "direct_sub.ax"
    direct_sub_ax.write_text(
        """\
module direct_sub

@link("sub/qa_sub.lib")
extern "C" {
    fn mid_calc(x: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { mid_calc(12) } // 51
}
""",
        encoding="utf-8",
    )
    direct_sub_exe = qa1_dir / "direct_sub.exe"
    run_cmd([compiler, "build", "-o", str(direct_sub_exe), "direct_sub.ax"], cwd=str(qa1_dir))
    run_cmd([str(direct_sub_exe)], cwd=str(qa1_dir), expect_rc=51)

    # (e) Deterministic `-l<name>` search order `<name>.lib` -> `lib<name>.lib` -> `lib<name>.a`
    #     and `has_arch_ext` exact `<dir>/<name>` probing without spurious extension appending
    #     (Round 1 QA Finding 1: SPEC-26 AXS-WLIB-003 item 2)
    pfx_dir = tmp_dir / "pfx_order_test"
    pfx_dir.mkdir(parents=True, exist_ok=True)
    for tag, ret_val in [("bare", 11), ("libpfx_lib", 22), ("libpfx_a", 33)]:
        src_p = pfx_dir / f"src_{tag}.ax"
        src_p.write_text(
            f"module src_{tag}\npub fn pfx_probe() -> i32 {{ {ret_val} }}\n",
            encoding="utf-8",
        )
        run_cmd([compiler, "build", "--kind", "lib", "-o", str(pfx_dir / f"built_{tag}.lib"), str(src_p)])

    cand_bare_lib = pfx_dir / "qapfx.lib"
    cand_lib_lib = pfx_dir / "libqapfx.lib"
    cand_lib_a = pfx_dir / "libqapfx.a"
    shutil.copyfile(pfx_dir / "built_bare.lib", cand_bare_lib)
    shutil.copyfile(pfx_dir / "built_libpfx_lib.lib", cand_lib_lib)
    shutil.copyfile(pfx_dir / "built_libpfx_a.lib", cand_lib_a)

    pfx_consumer_ax = pfx_dir / "pfx_consumer.ax"
    pfx_consumer_ax.write_text(
        """\
module pfx_consumer

extern "C" {
    fn pfx_probe() -> i32;
}

pub fn main() -> i32 {
    unsafe { pfx_probe() }
}
""",
        encoding="utf-8",
    )

    # All 3 present -> `<name>.lib` (11) wins
    pfx_exe_1 = pfx_dir / "pfx_1.exe"
    run_cmd([compiler, "build", "-o", str(pfx_exe_1), "-L", str(pfx_dir), "-lqapfx", str(pfx_consumer_ax)])
    run_cmd([str(pfx_exe_1)], expect_rc=11)

    # Remove `qapfx.lib` -> `libqapfx.lib` (22) wins over `libqapfx.a` (33)
    cand_bare_lib.unlink()
    pfx_exe_2 = pfx_dir / "pfx_2.exe"
    run_cmd([compiler, "build", "-o", str(pfx_exe_2), "-L", str(pfx_dir), "-lqapfx", str(pfx_consumer_ax)])
    run_cmd([str(pfx_exe_2)], expect_rc=22)

    # Remove `libqapfx.lib` -> `libqapfx.a` (33) resolves
    cand_lib_lib.unlink()
    pfx_exe_3 = pfx_dir / "pfx_3.exe"
    run_cmd([compiler, "build", "-o", str(pfx_exe_3), "-L", str(pfx_dir), "-lqapfx", str(pfx_consumer_ax)])
    run_cmd([str(pfx_exe_3)], expect_rc=33)

    # When `<name>` already ends in `.lib`/`.a` (e.g. `-lexact.lib`), `dir0` containing spurious
    # `exact.lib.lib`, `libexact.lib.a`, and `exact.lib.a` MUST NOT match; `dir1/exact.lib` MUST win!
    ext_dir0 = pfx_dir / "ext_dir0"
    ext_dir1 = pfx_dir / "ext_dir1"
    ext_dir0.mkdir(parents=True, exist_ok=True)
    ext_dir1.mkdir(parents=True, exist_ok=True)
    for bad_name in ("exact.lib.lib", "libexact.lib.a", "exact.lib.a"):
        shutil.copyfile(pfx_dir / "built_libpfx_a.lib", ext_dir0 / bad_name)  # returns 33 if spuriously picked
    shutil.copyfile(pfx_dir / "built_libpfx_lib.lib", ext_dir1 / "exact.lib")  # returns 22
    ext_guard_exe = pfx_dir / "ext_guard.exe"
    run_cmd(
        [
            compiler,
            "build",
            "-o",
            str(ext_guard_exe),
            "-L",
            str(ext_dir0),
            "-L",
            str(ext_dir1),
            "-lexact.lib",
            str(pfx_consumer_ax),
        ]
    )
    run_cmd([str(ext_guard_exe)], expect_rc=22)

    # =========================================================================
    # 3. Multi-member demand-driven fixed-point extraction & dead-member omission
    # =========================================================================
    m0_ax = tmp_dir / "m0_unused.ax"
    m0_ax.write_text(
        """\
module m0_unused

extern "C" {
    fn nonexistent_unresolved_external() -> i32;
}

pub fn unused_entry() -> i32 {
    unsafe { nonexistent_unresolved_external() }
}
""",
        encoding="utf-8",
    )
    m1_ax = tmp_dir / "m1_helper.ax"
    m1_ax.write_text(
        """\
module m1_helper

pub fn helper_compute(x: i32) -> i32 {
    x * 3 + 7
}
""",
        encoding="utf-8",
    )
    m2_ax = tmp_dir / "m2_entry.ax"
    m2_ax.write_text(
        """\
module m2_entry

extern "C" {
    fn helper_compute(x: i32) -> i32;
}

pub fn entry_compute(x: i32) -> i32 {
    unsafe { helper_compute(x) }
}
""",
        encoding="utf-8",
    )

    multi_lib = tmp_dir / "multi.lib"
    # Order on CLI: m0_unused.ax, m1_helper.ax, m2_entry.ax
    # m2_entry is AFTER m1_helper in the archive and references helper_compute in m1_helper!
    run_cmd(
        [
            compiler,
            "build",
            "--kind",
            "lib",
            "-o",
            str(multi_lib),
            str(m0_ax),
            str(m1_ax),
            str(m2_ax),
        ]
    )
    multi_info = parse_and_validate_coff_archive(multi_lib.read_bytes())
    if multi_info["obj_names"] != ["m0_unused.obj", "m1_helper.obj", "m2_entry.obj"]:
        raise ValidationError(f"unexpected member list in multi.lib: {multi_info['obj_names']}")

    app_multi_ax = tmp_dir / "app_multi.ax"
    app_multi_ax.write_text(
        """\
module app_multi

extern "C" {
    fn entry_compute(x: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { entry_compute(13) } // 13 * 3 + 7 = 46
}
""",
        encoding="utf-8",
    )
    app_multi_exe = tmp_dir / "app_multi.exe"
    run_cmd([compiler, "build", "-o", str(app_multi_exe), str(app_multi_ax), str(multi_lib)])
    run_cmd([str(app_multi_exe)], expect_rc=46)

    # =========================================================================
    # 4. C `.lib`/`.a` archive & COFF Short Import Object interoperability
    # =========================================================================
    c_math_c = tmp_dir / "c_math.c"
    c_math_c.write_text(
        """\
int c_weighted_sum(int a, int b) {
    return a * 10 + b;
}
""",
        encoding="utf-8",
    )
    c_dead_c = tmp_dir / "c_dead.c"
    c_dead_c.write_text(
        """\
extern int never_defined_c_symbol(void);
int c_dead_fn(void) {
    return never_defined_c_symbol();
}
""",
        encoding="utf-8",
    )
    c_math_obj = tmp_dir / "c_math.obj"
    c_dead_obj = tmp_dir / "c_dead.obj"
    run_cmd([cc_tool, "-c", "-O2", str(c_math_c), "-o", str(c_math_obj)])
    run_cmd([cc_tool, "-c", "-O2", str(c_dead_c), "-o", str(c_dead_obj)])

    # Create C archive with external `llvm-ar` / `ar` as both `c_ext.lib` and `libc_ext_gnu.a`
    c_ext_lib = tmp_dir / "c_ext.lib"
    c_ext_gnu_a = tmp_dir / "libc_ext_gnu.a"
    run_cmd([ar_tool, "rcs", str(c_ext_lib), str(c_dead_obj), str(c_math_obj)])
    run_cmd([ar_tool, "rcs", str(c_ext_gnu_a), str(c_dead_obj), str(c_math_obj)])

    # Also create archive from `.obj` inputs using `axiomc build --kind lib`
    c_ax_lib = tmp_dir / "c_ax.lib"
    run_cmd([compiler, "build", "--kind", "lib", "-o", str(c_ax_lib), str(c_dead_obj), str(c_math_obj)])

    app_c_ax = tmp_dir / "app_c.ax"
    app_c_ax.write_text(
        """\
module app_c

extern "C" {
    fn c_weighted_sum(a: i32, b: i32) -> i32;
}

pub fn main() -> i32 {
    unsafe { c_weighted_sum(5, 8) } // 58
}
""",
        encoding="utf-8",
    )

    for suffix, extra_args in [
        ("ext_lib", [str(c_ext_lib)]),
        ("gnu_a", ["-L", str(tmp_dir), "-lc_ext_gnu"]),
        ("ax_lib", [str(c_ax_lib)]),
    ]:
        out_exe = tmp_dir / f"app_c_{suffix}.exe"
        run_cmd([compiler, "build", "-o", str(out_exe), str(app_c_ax)] + extra_args)
        run_cmd([str(out_exe)], expect_rc=58)

    # Short Import Object archive test (`Sig1=0x0000, Sig2=0xFFFF`)
    short_imp_lib = tmp_dir / "short_imp.lib"
    short_imp_lib.write_bytes(build_short_import_archive("GetCurrentProcessId", "KERNEL32.dll"))
    app_short_ax = tmp_dir / "app_short.ax"
    app_short_ax.write_text(
        """\
module app_short

extern "C" {
    fn GetCurrentProcessId() -> u32;
}

pub fn main() -> i32 {
    let pid = unsafe { GetCurrentProcessId() };
    if pid > 0u32 { 0 } else { 1 }
}
""",
        encoding="utf-8",
    )
    app_short_exe = tmp_dir / "app_short.exe"
    run_cmd([compiler, "build", "-o", str(app_short_exe), str(app_short_ax), str(short_imp_lib)])
    run_cmd([str(app_short_exe)], expect_rc=0)

    # =========================================================================
    # 5. Negative tests: AX_DRIVER_INVALID_ARTIFACT_KIND, AX_LINK_BAD_ARCHIVE,
    #    AX_LINK_LIBRARY_NOT_FOUND
    # =========================================================================
    # 5a. Invalid `--kind` on CLI -> exit code 2 + AX_DRIVER_INVALID_ARTIFACT_KIND
    p_bad_kind = run_cmd(
        [compiler, "build", "--kind", "bogus", "-o", str(tmp_dir / "bad.out"), str(app_ax)],
        expect_rc=2,
    )
    if b"AX_DRIVER_INVALID_ARTIFACT_KIND" not in p_bad_kind.stderr:
        raise ValidationError(
            f"expected AX_DRIVER_INVALID_ARTIFACT_KIND in stderr, got:\n"
            f"{p_bad_kind.stderr.decode('utf-8', errors='replace')}"
        )

    # 5b. Invalid `kind = "bogus"` in `axiom.toml` -> exit code 2 + AX_DRIVER_INVALID_ARTIFACT_KIND
    bad_pkg_dir = tmp_dir / "bad_pkg"
    (bad_pkg_dir / "src").mkdir(parents=True, exist_ok=True)
    (bad_pkg_dir / "axiom.toml").write_text(
        '[package]\nname = "bad_pkg"\nversion = "0.1.0"\nkind = "bogus"\n',
        encoding="utf-8",
    )
    (bad_pkg_dir / "src" / "main.ax").write_text("pub fn main() -> i32 { 0 }\n", encoding="utf-8")
    p_bad_manifest_kind = run_cmd(
        [compiler, "build", "-o", str(tmp_dir / "bad_pkg.exe"), str(bad_pkg_dir)],
        expect_rc=2,
    )
    if b"AX_DRIVER_INVALID_ARTIFACT_KIND" not in p_bad_manifest_kind.stderr:
        raise ValidationError(
            f"expected AX_DRIVER_INVALID_ARTIFACT_KIND for bad axiom.toml kind, got:\n"
            f"{p_bad_manifest_kind.stderr.decode('utf-8', errors='replace')}"
        )

    # 5c. Corrupt `.lib` archive -> AX_LINK_BAD_ARCHIVE
    corrupt_lib = tmp_dir / "corrupt.lib"
    corrupt_lib.write_bytes(b"!<corrupt_archive_header>\n")
    p_bad_arch = run_cmd(
        [compiler, "build", "-o", str(tmp_dir / "bad_arch.exe"), str(app_ax), str(corrupt_lib)],
        expect_rc=1,
    )
    if b"AX_LINK_BAD_ARCHIVE" not in p_bad_arch.stderr:
        raise ValidationError(
            f"expected AX_LINK_BAD_ARCHIVE in stderr, got:\n"
            f"{p_bad_arch.stderr.decode('utf-8', errors='replace')}"
        )

    # 5d. Missing `-l` library -> AX_LINK_LIBRARY_NOT_FOUND (both human and `--json` data.library)
    p_missing_lib = run_cmd(
        [
            compiler,
            "build",
            "--json",
            "-o",
            str(tmp_dir / "missing_lib.exe"),
            "-L",
            str(tmp_dir),
            "-lnonexistent_lib_xyz_987",
            str(app_ax),
        ],
        expect_rc=1,
    )
    if b"AX_LINK_LIBRARY_NOT_FOUND" not in p_missing_lib.stderr:
        raise ValidationError(
            f"expected AX_LINK_LIBRARY_NOT_FOUND in stderr, got:\n"
            f"{p_missing_lib.stderr.decode('utf-8', errors='replace')}"
        )
    diag_doc = json.loads(p_missing_lib.stderr.decode("utf-8"))
    diags = diag_doc.get("diagnostics", diag_doc if isinstance(diag_doc, list) else [])
    if not any(
        d.get("code") == "AX_LINK_LIBRARY_NOT_FOUND"
        and d.get("data", {}).get("library") == "nonexistent_lib_xyz_987"
        for d in diags
    ):
        raise ValidationError(f"expected data.library == 'nonexistent_lib_xyz_987' in JSON diag: {diag_doc}")

    # 5e. `run` with non-Executable artifact flags (`--kind lib|obj|dll`, `--emit=obj`, `--emit obj`)
    #     rejected with exit code 2 (`AX_DRIVER_USAGE`, Round 1 QA Finding 3: SPEC-26 AXS-WLIB-002 items 1 & 4)
    runnable_ax = tmp_dir / "runnable_zero.ax"
    runnable_ax.write_text("module runnable_zero\npub fn main() -> i32 { 0 }\n", encoding="utf-8")
    for bad_run_flags in [
        ["--kind", "lib"],
        ["--kind", "obj"],
        ["--kind", "dll"],
        ["--emit=obj"],
        ["--emit", "obj"],
    ]:
        p_run_bad = run_cmd([compiler, "run"] + bad_run_flags + [str(runnable_ax)], expect_rc=2)
        if b"AX_DRIVER_USAGE" not in p_run_bad.stderr:
            raise ValidationError(
                f"expected AX_DRIVER_USAGE for `run {bad_run_flags}`, got:\n"
                f"{p_run_bad.stderr.decode('utf-8', errors='replace')}"
            )

    # =========================================================================
    # 6. QA Round 1 Boundary Cross-Checks (`--emit=obj` <-> `--kind` override,
    #    per-item `@link("qa1.lib")` + mixed `@link("kernel32")`, decoy-only `-lexact.lib`)
    # =========================================================================
    # 6a. Per-item `@link("qa1.lib")` inside `extern "C"` and mixed static `.lib` + Win32 DLL import
    #     with zero `-L`/`-l` flags
    direct_mix_ax = qa1_dir / "direct_mix.ax"
    direct_mix_ax.write_text(
        """\
module direct_mix

extern "C" {
    @link("qa1.lib")
    fn mid_calc(x: i32) -> i32;
}

@link("kernel32")
extern "system" {
    fn GetCurrentProcessId() -> u32;
}

pub fn main() -> i32 {
    let pid = unsafe { GetCurrentProcessId() };
    let v = unsafe { mid_calc(9) }; // 39
    if pid > 0u32 { v } else { 1 }
}
""",
        encoding="utf-8",
    )
    direct_mix_exe = qa1_dir / "direct_mix.exe"
    run_cmd([compiler, "build", "-o", str(direct_mix_exe), "direct_mix.ax"], cwd=str(qa1_dir))
    run_cmd([str(direct_mix_exe)], cwd=str(qa1_dir), expect_rc=39)
    od_mix = run_cmd([objdump_tool, "-p", str(direct_mix_exe)]).stdout.decode("utf-8", errors="replace").lower()
    if "qa1.lib" in od_mix or "qa1.dll" in od_mix or "kernel32.dll" not in od_mix:
        raise ValidationError(f"unexpected import table in direct_mix.exe:\n{od_mix}")

    # 6b. `-lexact.lib` with ONLY decoy directory `ext_dir0` (including `libexact.lib.lib`) MUST fail
    #     with `AX_LINK_LIBRARY_NOT_FOUND` rather than matching decoys
    shutil.copyfile(pfx_dir / "built_libpfx_a.lib", ext_dir0 / "libexact.lib.lib")
    p_decoy_nf = run_cmd(
        [
            compiler,
            "build",
            "-o",
            str(pfx_dir / "decoy_nf.exe"),
            "-L",
            str(ext_dir0),
            "-lexact.lib",
            str(pfx_consumer_ax),
        ],
        expect_rc=1,
    )
    if b"AX_LINK_LIBRARY_NOT_FOUND" not in p_decoy_nf.stderr:
        raise ValidationError(
            f"expected AX_LINK_LIBRARY_NOT_FOUND when only decoy extensions exist:\n"
            f"{p_decoy_nf.stderr.decode('utf-8', errors='replace')}"
        )

    # 6c. `--emit=obj` <-> `--kind` CLI last-wins override across `run` and `build`
    p_run_late_emit = run_cmd(
        [compiler, "run", "--kind", "exe", "--emit=obj", str(runnable_ax)],
        expect_rc=2,
    )
    if b"AX_DRIVER_USAGE" not in p_run_late_emit.stderr:
        raise ValidationError("expected `run --kind exe --emit=obj` to fail with AX_DRIVER_USAGE")
    run_cmd([compiler, "run", "--emit=obj", "--kind", "exe", str(runnable_ax)], expect_rc=0)

    ov_lib = tmp_dir / "override_to_lib.lib"
    run_cmd([compiler, "build", "--emit=obj", "--kind", "lib", "-o", str(ov_lib), str(math_ax)])
    parse_and_validate_coff_archive(ov_lib.read_bytes())

    ov_obj = tmp_dir / "override_to_obj.obj"
    run_cmd([compiler, "build", "--kind", "lib", "--emit=obj", "-o", str(ov_obj), str(math_ax)])
    if ov_obj.read_bytes()[:2] != b"\x64\x86":
        raise ValidationError("expected AMD64 COFF object magic 0x8664 for `build --kind lib --emit=obj`")

    print("COFF-LIB-ORACLE ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
