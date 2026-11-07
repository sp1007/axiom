#!/usr/bin/env python3
"""E18.7 Conformance Oracle: GNU `ld` & `gcc` Cross-Linking Equivalence
(`SPEC-26` §§5-9, `ADR-0034` §4 OI-07b, `REQ-LNK-113`..`REQ-LNK-121`).

Independently verifies using GNU binutils (`ld`, `gcc`, `objdump`, `nm`) and a custom
binary COFF/PE parser that:
1. `axiomc build --rt-obj` and `axiomc compile --rt-obj` deterministically emit a valid
   x86_64 COFF runtime object (`axiom_rt.obj`) with `TimeDateStamp == 0`, defining
   `axiom_start`, `axiom_panic`, `__ax_host_print`, and `__ax_host_print_int`, and
   referencing `main` and `__imp_*` Win32 symbols with zero internal `__IAT_*` or
   `<dll>$<fn>` symbols (`AXS-WLIB-032`).
2. Both `--kind obj` and `--emit=obj` on Axiom programs with `@link("<dll>")` extern
   blocks and `@export` items emit relocatable COFF `.obj` files with standard
   `__imp_<sym>` external symbols and zero internal `__IAT_*` or `<dll>$<sym>` symbols
   (`AXS-WLIB-030`, `REQ-LNK-117`, `REQ-LNK-118`).
3. Multi-artifact cross-linking across all Windows artifact kinds (`--kind obj`,
   `--kind lib`, `--kind dll` + `.lib` + `.def`, and `gcc -c` C `.obj` with `.pdata`/`.xdata`)
   linked by:
     (a) Axiom's internal PE32+ linker (`axiomc build`),
     (b) standalone GNU `ld -m i386pep --subsystem console -e axiom_start`, and
     (c) `gcc -nostdlib -Wl,-e,axiom_start`
   produces valid PE32+ executables with identical exit codes, stdout, and stderr at
   both `-O0` and `-O2`, including `extern "C"` and `extern "system"` function pointers
   (`REQ-LNK-113`..`REQ-LNK-121`, `ADR-0034` §4 OI-07b).
4. Runnable Axiom programs across `tests/conformance/p18/e18_7_windows_artifacts/` and
   representative `tests/run/` programs compiled with `--emit=obj` / `--kind obj` and
   linked with GNU `ld` against `axiom_rt.obj` and MinGW-w64 import libraries execute
   with identical exit codes, stdout bytes, and stderr bytes as `axiomc build`.
"""

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


class ValidationError(Exception):
    pass


def require_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise ValidationError(f"required external oracle tool {name!r} not found in PATH (ADR-0034 §7)")
    return found


def run_checked(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if res.returncode != 0:
        raise ValidationError(
            f"command failed (exit {res.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{res.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{res.stderr.decode('utf-8', errors='replace')}"
        )
    return res


def find_mingw_lib_dirs(gcc_tool: str, ld_tool: str) -> list[str]:
    candidates: list[Path] = []
    res = subprocess.run(
        [gcc_tool, "-print-search-dirs"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if res.returncode == 0:
        for line in res.stdout.decode("utf-8", errors="replace").splitlines():
            if line.lower().startswith("libraries:"):
                raw = line.split(":", 1)[1].lstrip(" =")
                sep = ";" if os.name == "nt" else ":"
                for part in raw.split(sep):
                    if part.strip():
                        candidates.append(Path(part.strip()))
    ld_dir = Path(ld_tool).resolve().parent
    candidates.append(ld_dir.parent / "lib")
    candidates.append(ld_dir.parent / "x86_64-w64-mingw32" / "lib")
    candidates.append(Path("C:/msys64/ucrt64/lib"))
    candidates.append(Path("C:/msys64/mingw64/lib"))

    valid: list[str] = []
    seen: set[str] = set()
    for c in candidates:
        try:
            rc = c.resolve()
        except OSError:
            continue
        key = str(rc).lower()
        if key in seen or not rc.is_dir():
            continue
        if (rc / "libkernel32.a").is_file() or (rc / "kernel32.lib").is_file():
            seen.add(key)
            valid.append(str(rc))
    if not valid:
        raise ValidationError("could not locate MinGW-w64 import library directory containing libkernel32.a")
    return valid


def inspect_coff_symbols(obj_bytes: bytes, label: str) -> tuple[set[str], list[str]]:
    if len(obj_bytes) < 20:
        raise ValidationError(f"{label}: COFF object too small ({len(obj_bytes)} bytes)")
    machine, num_sections, timestamp, symtab_off, num_syms, opt_hdr_sz, _chars = struct.unpack_from(
        "<HHIIIHH", obj_bytes, 0
    )
    if machine != 0x8664:
        raise ValidationError(f"{label}: expected Machine=0x8664, got {machine:#06x}")
    if timestamp != 0:
        raise ValidationError(f"{label}: expected deterministic TimeDateStamp=0, got {timestamp}")
    if opt_hdr_sz != 0:
        raise ValidationError(f"{label}: relocatable .obj must have SizeOfOptionalHeader=0, got {opt_hdr_sz}")
    if num_sections == 0:
        raise ValidationError(f"{label}: expected >=1 section")

    strtab_off = symtab_off + num_syms * 18
    if strtab_off + 4 > len(obj_bytes):
        raise ValidationError(f"{label}: truncated COFF symbol/string table")
    (strtab_sz,) = struct.unpack_from("<I", obj_bytes, strtab_off)
    if strtab_off + strtab_sz > len(obj_bytes):
        raise ValidationError(f"{label}: string table exceeds object bounds")

    raw_undef: list[str] = []
    defined: set[str] = set()
    idx = 0
    while idx < num_syms:
        rec_off = symtab_off + idx * 18
        name_raw = obj_bytes[rec_off : rec_off + 8]
        _val, sec_num, _sym_type, storage_class, aux_count = struct.unpack_from("<IhHBB", obj_bytes, rec_off + 8)
        zeros, str_off = struct.unpack("<II", name_raw)
        if zeros == 0:
            end = obj_bytes.find(b"\x00", strtab_off + str_off, strtab_off + strtab_sz)
            if end < 0:
                raise ValidationError(f"{label}: unterminated symbol name at string offset {str_off}")
            sym_name = obj_bytes[strtab_off + str_off : end].decode("utf-8", errors="replace")
        else:
            sym_name = name_raw.rstrip(b"\x00").decode("utf-8", errors="replace")

        if sec_num > 0 and storage_class == 2:
            defined.add(sym_name)
        elif sec_num == 0 and storage_class == 2:
            raw_undef.append(sym_name)
        idx += 1 + aux_count

    undef = [s for s in raw_undef if s not in defined]
    for sym_name in undef:
        if "$" in sym_name:
            raise ValidationError(
                f"{label}: internal '<dll>$<fn>' symbol {sym_name!r} leaked into COFF external symbol table"
            )
        if sym_name.startswith("__IAT_"):
            raise ValidationError(
                f"{label}: internal '__IAT_*' symbol {sym_name!r} leaked into COFF external symbol table"
            )
    return defined, undef


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: e18_7_gnu_ld_crosslink_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    gcc_tool = require_tool("gcc")
    ld_tool = require_tool("ld")
    dlltool_bin = require_tool("dlltool")
    objdump_tool = require_tool("objdump")
    nm_tool = require_tool("nm")

    mingw_lib_dirs = find_mingw_lib_dirs(gcc_tool, ld_tool)
    mingw_L_args: list[str] = []
    for d in mingw_lib_dirs:
        mingw_L_args.extend(["-L", d])

    # =========================================================================
    # 1. Verify `axiom_rt.obj` (`build --rt-obj` & `compile --rt-obj`)
    # =========================================================================
    rt_obj_1 = tmp_dir / "axiom_rt.obj"
    rt_obj_2 = tmp_dir / "axiom_rt_compile.obj"
    run_checked([compiler, "build", "--rt-obj", str(rt_obj_1)])
    run_checked([compiler, "compile", "--rt-obj", str(rt_obj_2)])

    rt_bytes = rt_obj_1.read_bytes()
    if rt_bytes != rt_obj_2.read_bytes():
        raise ValidationError("axiom_rt.obj differs between `build --rt-obj` and `compile --rt-obj`")

    rt_def, rt_undef = inspect_coff_symbols(rt_bytes, "axiom_rt.obj")
    for req_def in ("axiom_start", "axiom_panic", "__ax_host_print", "__ax_host_print_int"):
        if req_def not in rt_def:
            raise ValidationError(f"axiom_rt.obj missing defined symbol {req_def!r}: {sorted(rt_def)}")
    for req_undef in ("main", "__imp_GetStdHandle", "__imp_WriteFile", "__imp_ExitProcess"):
        if req_undef not in rt_undef:
            raise ValidationError(f"axiom_rt.obj missing undefined reference {req_undef!r}: {rt_undef}")

    od_rt = run_checked([objdump_tool, "-d", str(rt_obj_1)]).stdout.decode("utf-8", errors="replace")
    if "(bad)" in od_rt:
        raise ValidationError(f"objdump -d found '(bad)' in axiom_rt.obj:\n{od_rt}")

    # =========================================================================
    # 2. Multi-Artifact Cross-Linking (`--kind dll`, `--kind lib`, `--kind obj`, C `.obj`)
    # =========================================================================
    # 2a. Build Axiom DLL (`ax_xlib.dll` + `ax_xlib.lib` + `ax_xlib.def`)
    dll_ax = tmp_dir / "ax_xlib.ax"
    dll_ax.write_text(
        """\
module ax_xlib

fn internal_scale(x: i64) -> i64 {
    x * 3
}

@export
pub fn ax_dll_transform(a: i64, b: i64) -> i64 {
    internal_scale(a) + b
}

@export
extern "C" fn ax_dll_tag(seed: i32) -> i32 {
    seed + 19
}
""",
        encoding="utf-8",
        newline="\n",
    )
    dll_path = tmp_dir / "ax_xlib.dll"
    dll_lib = tmp_dir / "ax_xlib.lib"
    run_checked([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(dll_path), str(dll_ax)])
    if not dll_path.is_file() or not dll_lib.is_file():
        raise ValidationError("failed to emit ax_xlib.dll + ax_xlib.lib")

    # 2b. Build Axiom static library (`ax_xstatic.lib`)
    static_ax = tmp_dir / "ax_xstatic.ax"
    static_ax.write_text(
        """\
module ax_xstatic

@export
pub fn ax_static_accum(x: i64, y: i64, z: i64) -> i64 {
    (x * y) + z
}
""",
        encoding="utf-8",
        newline="\n",
    )
    static_lib = tmp_dir / "ax_xstatic.lib"
    run_checked(
        [compiler, "build", "--std-root", str(std_root), "--kind", "lib", "-o", str(static_lib), str(static_ax)]
    )

    # 2c. Build C helper object (`c_xhelper.obj`) with unwind tables (`.pdata` / `.xdata`)
    c_helper_src = tmp_dir / "c_xhelper.c"
    c_helper_src.write_text(
        """\
#include <stdint.h>

extern int64_t ax_static_accum(int64_t x, int64_t y, int64_t z);
__declspec(dllimport) int64_t ax_dll_transform(int64_t a, int64_t b);
__declspec(dllimport) int32_t ax_dll_tag(int32_t seed);

int64_t c_bridge_compute(int64_t v) {
    int64_t s = ax_static_accum(v, 4, 5);
    int64_t d = ax_dll_transform(s, 7);
    int32_t t = ax_dll_tag(10);
    return d + (int64_t)t;
}
""",
        encoding="utf-8",
        newline="\n",
    )
    c_helper_obj = tmp_dir / "c_xhelper.obj"
    run_checked([gcc_tool, "-O2", "-fasynchronous-unwind-tables", "-c", str(c_helper_src), "-o", str(c_helper_obj)])

    # 2d. Main Axiom program exercising `@link`, `extern "C"`, `extern "system"` fn pointers,
    #     and UTF-8 output (`"Xin chào thế giới"`).
    main_ax = tmp_dir / "main_xprog.ax"
    main_ax.write_text(
        """\
module main_xprog

@link("ax_xlib")
extern "C" {
    fn ax_dll_transform(a: i64, b: i64) -> i64;
    fn ax_dll_tag(seed: i32) -> i32;
}

extern "C" {
    fn ax_static_accum(x: i64, y: i64, z: i64) -> i64;
    fn c_bridge_compute(v: i64) -> i64;
}

@link("kernel32")
extern "system" {
    fn GetCurrentProcessId() -> u32;
}

fn local_ax_cb(a: i64, b: i64) -> i64 {
    a - b
}

fn local_ax_scale(x: u32) -> u32 {
    x + 3u32
}

fn invoke_ax(f: fn(i64, i64) -> i64, a: i64, b: i64) -> i64 {
    f(a, b)
}

fn invoke_scale(f: fn(u32) -> u32, x: u32) -> u32 {
    f(x)
}

pub fn main() -> i32 {
    print("Xin chào thế giới\\n");
    let pid = unsafe { GetCurrentProcessId() };
    if pid == 0u32 {
        return 1;
    }
    // c_bridge_compute(5):
    //   s = 5*4 + 5 = 25
    //   d = 25*3 + 7 = 82
    //   t = 10 + 19 = 29
    //   return 82 + 29 = 111
    let c_val = unsafe { c_bridge_compute(5) };
    if c_val != 111 {
        return 2;
    }
    let direct_dll = unsafe { ax_dll_transform(6, 2) }; // 20
    let direct_lib = unsafe { ax_static_accum(3, 5, 1) }; // 16
    let direct_tag = unsafe { ax_dll_tag(4) }; // 23
    let cb_c = invoke_ax(local_ax_cb, direct_dll, direct_lib); // 4
    let cb_s = invoke_scale(local_ax_scale, 9u32) as i64; // 12
    (cb_c + cb_s + (direct_tag as i64)) as i32 // 4 + 12 + 23 = 39
}
""",
        encoding="utf-8",
        newline="\n",
    )

    for opt_label, opt_flags in [("O0", []), ("O2", ["-O2"])]:
        obj_kind = tmp_dir / f"main_kind_{opt_label}.obj"
        obj_emit = tmp_dir / f"main_emit_{opt_label}.obj"
        run_checked(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                *opt_flags,
                "--verify-each",
                "--kind",
                "obj",
                "-o",
                str(obj_kind),
                str(main_ax),
            ]
        )
        run_checked(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                *opt_flags,
                "--verify-each",
                "--emit=obj",
                "-o",
                str(obj_emit),
                str(main_ax),
            ]
        )
        if obj_kind.read_bytes() != obj_emit.read_bytes():
            raise ValidationError(f"--kind obj and --emit=obj bytes differ at {opt_label}")

        defined_syms, undef_syms = inspect_coff_symbols(obj_kind.read_bytes(), f"main_{opt_label}.obj")
        if "main" not in defined_syms:
            raise ValidationError(f"main_{opt_label}.obj missing defined 'main': {defined_syms}")
        for req_imp in ("__imp_ax_dll_transform", "__imp_ax_dll_tag", "__imp_GetCurrentProcessId"):
            if req_imp not in undef_syms:
                raise ValidationError(f"main_{opt_label}.obj missing {req_imp!r} in undefined symbols: {undef_syms}")
        for req_ext in ("ax_static_accum", "c_bridge_compute"):
            if req_ext not in undef_syms:
                raise ValidationError(f"main_{opt_label}.obj missing {req_ext!r} in undefined symbols: {undef_syms}")

        nm_out = run_checked([nm_tool, "-g", str(obj_kind)]).stdout.decode("utf-8", errors="replace")
        if "__imp_ax_dll_transform" not in nm_out or "__imp_GetCurrentProcessId" not in nm_out:
            raise ValidationError(f"nm -g missing expected __imp_* references in main_{opt_label}.obj:\n{nm_out}")

        # (a) Self-linked via `axiomc build`
        exe_self = tmp_dir / f"multi_self_{opt_label}.exe"
        run_checked(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                *opt_flags,
                "--verify-each",
                "-o",
                str(exe_self),
                str(main_ax),
                str(c_helper_obj),
                str(static_lib),
                str(dll_lib),
            ]
        )

        # (b) Linked via standalone GNU `ld`
        exe_ld = tmp_dir / f"multi_ld_{opt_label}.exe"
        run_checked(
            [
                ld_tool,
                "-m",
                "i386pep",
                "--subsystem",
                "console",
                "-e",
                "axiom_start",
                str(obj_kind),
                str(c_helper_obj),
                str(rt_obj_1),
                str(static_lib),
                str(dll_path),
                *mingw_L_args,
                "-lkernel32",
                "-o",
                str(exe_ld),
            ]
        )

        # (c) Linked via `gcc -nostdlib`
        exe_gcc = tmp_dir / f"multi_gcc_{opt_label}.exe"
        run_checked(
            [
                gcc_tool,
                "-nostdlib",
                "-Wl,-e,axiom_start",
                str(obj_kind),
                str(c_helper_obj),
                str(rt_obj_1),
                str(static_lib),
                str(dll_path),
                "-lkernel32",
                "-o",
                str(exe_gcc),
            ]
        )

        r_self = subprocess.run([str(exe_self)], cwd=tmp_dir, capture_output=True, timeout=30)
        r_ld = subprocess.run([str(exe_ld)], cwd=tmp_dir, capture_output=True, timeout=30)
        r_gcc = subprocess.run([str(exe_gcc)], cwd=tmp_dir, capture_output=True, timeout=30)

        exp_stdout = "Xin chào thế giới\n".encode("utf-8")
        for label_exe, res in [("self", r_self), ("gnu-ld", r_ld), ("gcc-nostdlib", r_gcc)]:
            if res.returncode != 39:
                raise ValidationError(f"{label_exe} ({opt_label}) exited with {res.returncode}, expected 39")
            if res.stdout != exp_stdout:
                raise ValidationError(f"{label_exe} ({opt_label}) stdout mismatch: {res.stdout!r} != {exp_stdout!r}")
            if res.stderr != b"":
                raise ValidationError(f"{label_exe} ({opt_label}) unexpected stderr: {res.stderr!r}")

    # =========================================================================
    # 3. Cross-Link E18.7 Conformance & Representative `tests/run/` Programs
    # =========================================================================
    e18_7_dir = repo_root / "tests" / "conformance" / "p18" / "e18_7_windows_artifacts"
    sample_sources: list[tuple[Path, list[str]]] = [
        (e18_7_dir / "fn_ptr_calling_conv_abi.ax", ["--verify-each"]),
        (e18_7_dir / "fn_ptr_calling_conv_abi.ax", ["-O2", "--verify-each"]),
        (e18_7_dir / "export_visibility_and_abi_layout.ax", ["--verify-each"]),
        (e18_7_dir / "export_visibility_and_abi_layout.ax", ["-O2", "--verify-each"]),
    ]

    # Add a deterministic stratified sample of native runnable tests from `tests/run/`
    run_root = repo_root / "tests" / "run"
    if run_root.is_dir():
        run_ax_files = sorted(run_root.rglob("*.ax"))
        # Pick up to 12 self-contained runnable tests with no special header requirements
        picked = 0
        for ax_p in run_ax_files:
            txt = ax_p.read_text(encoding="utf-8", errors="replace")
            if (
                "// test: run" in txt
                and "// modes:" not in txt
                and "// skip-" not in txt
                and "// xfail" not in txt
                and "// args:" not in txt
                and "// stdin" not in txt
                and "// env:" not in txt
                and "// flags:" not in txt
            ):
                sample_sources.append((ax_p, []))
                picked += 1
                if picked >= 12:
                    break

    cases_dir = tmp_dir / "cross_cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    verified_count = 0

    for idx, (src_path, extra_flags) in enumerate(sample_sources):
        cdir = cases_dir / f"case_{idx:02d}"
        cdir.mkdir(parents=True, exist_ok=True)
        self_exe = cdir / "self.exe"
        prog_obj = cdir / "prog.obj"
        gnu_exe = cdir / "gnu.exe"

        run_checked(
            [compiler, "build", "--std-root", str(std_root), *extra_flags, "-o", str(self_exe), str(src_path)],
            cwd=repo_root,
        )
        run_checked(
            [
                compiler,
                "build",
                "--std-root",
                str(std_root),
                *extra_flags,
                "--emit=obj",
                "-o",
                str(prog_obj),
                str(src_path),
            ],
            cwd=repo_root,
        )
        inspect_coff_symbols(prog_obj.read_bytes(), f"{src_path.name} ({extra_flags})")

        run_checked(
            [
                ld_tool,
                "-m",
                "i386pep",
                "--subsystem",
                "console",
                "-e",
                "axiom_start",
                str(prog_obj),
                str(rt_obj_1),
                *mingw_L_args,
                "-lkernel32",
                "-lshell32",
                "-lmsvcrt",
                "-luser32",
                "-ladvapi32",
                "-lws2_32",
                "-lbcrypt",
                "-o",
                str(gnu_exe),
            ],
            cwd=repo_root,
        )

        env = dict(os.environ)
        env.setdefault("AXIOM_STD", "std")
        r_s = subprocess.run([str(self_exe)], cwd=repo_root, env=env, capture_output=True, timeout=30)
        r_g = subprocess.run([str(gnu_exe)], cwd=repo_root, env=env, capture_output=True, timeout=30)
        if r_s.returncode != r_g.returncode:
            raise ValidationError(
                f"{src_path.name} ({extra_flags}): rc mismatch self={r_s.returncode} vs gnu={r_g.returncode}"
            )
        if r_s.stdout != r_g.stdout:
            raise ValidationError(
                f"{src_path.name} ({extra_flags}): stdout mismatch self={r_s.stdout!r} vs gnu={r_g.stdout!r}"
            )
        if r_s.stderr != r_g.stderr:
            raise ValidationError(
                f"{src_path.name} ({extra_flags}): stderr mismatch self={r_s.stderr!r} vs gnu={r_g.stderr!r}"
            )
        verified_count += 1

    print(f"E18-7-GNU-LD-CROSSLINK-CONFORMANCE ok (multi-artifact O0/O2 + {verified_count} cross-linked programs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
