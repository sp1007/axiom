#!/usr/bin/env python3
"""End-to-end GNU `ld` / `gcc` cross-linking oracle (T751 / ADR-0034 section 4 OI-07b / T028 carry-over).

Verifies `SPEC-26` (`AXS-WLIB-032`) and `ADR-0034` section 4 (`OI-07b`):
1. `axiomc build --rt-obj <path>` (and `compile --rt-obj <path>`) deterministically emits a valid
   standalone x86_64 COFF runtime object (`axiom_rt.obj`) defining `axiom_start`, `axiom_panic`,
   `__ax_host_print`, and `__ax_host_print_int` with standard `__imp_*` Win32 references and zero
   internal `__IAT_*` symbols.
2. Every native runnable test under `tests/run/` compiled with `--emit=obj`:
   - contains valid COFF relocatable code/data with standard `__imp_<FuncName>` external symbols
     (zero `<dll>$<FuncName>` or `__IAT_*` undefined symbols),
   - links cleanly with the independent system linker GNU `ld` against `axiom_rt.obj` and MinGW-w64
     system import libraries (`-lkernel32`, `-lshell32`, `-lmsvcrt`, ...), and
   - executes with the exact same exit code, stdout bytes, and stderr bytes as the self-linked PE32+
     executable produced by `axiomc build`.
3. Cross-linking `--emit=obj` output via `gcc` (`-nostdlib -Wl,-e,axiom_start ... -lkernel32`) also
   succeeds and runs identically.
"""

import concurrent.futures
import importlib.util
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
        raise ValidationError(f"required external oracle tool {name!r} not found in PATH (ADR-0034 section 7)")
    return found


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


def inspect_coff_external_symbols(obj_bytes: bytes, label: str) -> list[str]:
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

    raw_undef_externals: list[str] = []
    defined_symbols: set[str] = set()
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

        if sec_num > 0:
            defined_symbols.add(sym_name)
        elif sec_num == 0 and storage_class == 2:  # IMAGE_SYM_UNDEFINED + IMAGE_SYM_CLASS_EXTERNAL
            raw_undef_externals.append(sym_name)
        idx += 1 + aux_count

    undef_externals = [s for s in raw_undef_externals if s not in defined_symbols]
    for sym_name in undef_externals:
        if "$" in sym_name:
            raise ValidationError(
                f"{label}: internal '<dll>$<fn>' symbol {sym_name!r} leaked into --emit=obj external table"
            )
        if sym_name.startswith("__IAT_"):
            raise ValidationError(
                f"{label}: internal '__IAT_*' symbol {sym_name!r} leaked into --emit=obj external table"
            )
    return undef_externals


def extract_ld_stack_args(flags: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(flags):
        fl = flags[i]
        if fl == "--stack-reserve" and i + 1 < len(flags):
            out = ["--stack", flags[i + 1]]
            i += 2
            continue
        if fl.startswith("--stack-reserve="):
            out = ["--stack", fl.split("=", 1)[1]]
        i += 1
    return out


def load_axtest_module(repo_root: Path):
    spec = importlib.util.spec_from_file_location("axtest_mod", str(repo_root / "tools" / "axtest.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: gnu_ld_run_oracle.py <compiler> <tmp_dir> <repo_root>", file=sys.stderr)
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    ld_tool = require_tool("ld")
    gcc_tool = require_tool("gcc")
    objdump_tool = require_tool("objdump")
    mingw_lib_dirs = find_mingw_lib_dirs(gcc_tool, ld_tool)
    mingw_L_args: list[str] = []
    for d in mingw_lib_dirs:
        mingw_L_args.extend(["-L", d])

    axtest = load_axtest_module(repo_root)

    # =========================================================================
    # 1. Emit & Validate `axiom_rt.obj` (`build --rt-obj` and `compile --rt-obj`)
    # =========================================================================
    rt_obj_1 = tmp_dir / "axiom_rt.obj"
    rt_obj_2 = tmp_dir / "axiom_rt_repeat.obj"
    for out_p, sub in [(rt_obj_1, "build"), (rt_obj_2, "compile")]:
        r = subprocess.run([compiler, sub, "--rt-obj", str(out_p)], capture_output=True, timeout=30)
        if r.returncode != 0 or not out_p.is_file():
            raise ValidationError(
                f"`{sub} --rt-obj` failed (rc={r.returncode}): {r.stderr.decode('utf-8', errors='replace')}"
            )
    rt_bytes = rt_obj_1.read_bytes()
    if rt_bytes != rt_obj_2.read_bytes():
        raise ValidationError("axiom_rt.obj emission is not byte-for-byte deterministic")
    rt_undef = inspect_coff_external_symbols(rt_bytes, "axiom_rt.obj")
    for req_imp in ("main", "__imp_GetStdHandle", "__imp_WriteFile", "__imp_ExitProcess"):
        if req_imp not in rt_undef:
            raise ValidationError(f"axiom_rt.obj missing expected external reference {req_imp!r}: {rt_undef}")

    od_rt_x = subprocess.run([objdump_tool, "-x", str(rt_obj_1)], capture_output=True, timeout=30, check=True)
    od_rt_d = subprocess.run([objdump_tool, "-d", str(rt_obj_1)], capture_output=True, timeout=30, check=True)
    rt_x_txt = od_rt_x.stdout.decode("utf-8", errors="replace")
    rt_d_txt = od_rt_d.stdout.decode("utf-8", errors="replace")
    if "(bad)" in rt_d_txt:
        raise ValidationError(f"objdump -d found '(bad)' in axiom_rt.obj:\n{rt_d_txt}")
    for def_sym in ("axiom_start", "axiom_panic", "__ax_host_print", "__ax_host_print_int"):
        if def_sym not in rt_x_txt:
            raise ValidationError(f"axiom_rt.obj symbol table missing {def_sym!r}:\n{rt_x_txt}")

    # =========================================================================
    # 2. Verify `gcc -nostdlib` Frontend Cross-Linking of `--emit=obj` + `axiom_rt.obj`
    # =========================================================================
    gcc_smoke_ax = tmp_dir / "gcc_smoke.ax"
    gcc_smoke_ax.write_text(
        """\
module gcc_smoke

@link("kernel32")
extern "system" {
    fn GetCurrentProcessId() -> u32;
}

pub fn main() -> i32 {
    print("Xin chào từ GNU ld\\n");
    let pid = unsafe { GetCurrentProcessId() };
    if pid > 0u32 { 37 } else { 1 }
}
""",
        encoding="utf-8",
    )
    gcc_smoke_obj = tmp_dir / "gcc_smoke.obj"
    gcc_smoke_exe = tmp_dir / "gcc_smoke.exe"
    r_smoke_obj = subprocess.run(
        [compiler, "build", "--std-root", str(std_root), "--emit=obj", "-o", str(gcc_smoke_obj), str(gcc_smoke_ax)],
        capture_output=True,
        timeout=30,
    )
    if r_smoke_obj.returncode != 0:
        raise ValidationError(f"failed to emit gcc_smoke.obj: {r_smoke_obj.stderr.decode('utf-8', errors='replace')}")
    smoke_undef = inspect_coff_external_symbols(gcc_smoke_obj.read_bytes(), "gcc_smoke.obj")
    if "__imp_GetCurrentProcessId" not in smoke_undef:
        raise ValidationError(f"expected __imp_GetCurrentProcessId in gcc_smoke.obj externals, got {smoke_undef}")
    r_gcc_link = subprocess.run(
        [
            gcc_tool,
            "-nostdlib",
            "-Wl,-e,axiom_start",
            str(gcc_smoke_obj),
            str(rt_obj_1),
            "-lkernel32",
            "-o",
            str(gcc_smoke_exe),
        ],
        capture_output=True,
        timeout=30,
    )
    if r_gcc_link.returncode != 0:
        raise ValidationError(f"gcc cross-link failed: {r_gcc_link.stderr.decode('utf-8', errors='replace')}")
    r_smoke_run = subprocess.run([str(gcc_smoke_exe)], capture_output=True, timeout=30)
    if r_smoke_run.returncode != 37 or r_smoke_run.stdout != "Xin chào từ GNU ld\n".encode("utf-8"):
        raise ValidationError(
            f"gcc_smoke.exe mismatch: rc={r_smoke_run.returncode}, stdout={r_smoke_run.stdout!r}"
        )

    # =========================================================================
    # 3. Discover All Native Runnable Tests in `tests/run/` & Cross-Link with GNU `ld`
    # =========================================================================
    feats = set()
    r_feat = subprocess.run([compiler, "--features"], capture_output=True, timeout=20)
    if r_feat.returncode == 0:
        for ln in r_feat.stdout.decode("utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                feats.add(ln.split()[0].rstrip(":,"))

    all_run_tests = axtest.discover(repo_root / "tests" / "run")
    selected = []
    for t in all_run_tests:
        if t.errors or t.kind != "run":
            continue
        if t.modes is not None and "native" not in t.modes:
            continue
        if t.xfail or t.native_after:
            continue
        if "axiom0-internal" in t.requires:
            continue
        skip = False
        for what, name in t.skip_unless:
            if what == "tool" and shutil.which(name) is None:
                skip = True
                break
            if what == "feature" and name not in feats:
                skip = True
                break
        if not skip:
            selected.append(t)

    if len(selected) < 500:
        raise ValidationError(f"expected >=500 native runnable tests in tests/run, found only {len(selected)}")

    # Schedule long-running tests (e.g. `write_bytes_1mb.ax`) first to avoid tail stragglers.
    selected.sort(key=lambda tc: -(float(tc.timeout) if tc.timeout else 10.0))

    cases_root = tmp_dir / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)

    def verify_test(idx_and_test) -> str | None:
        idx, t = idx_and_test
        case_dir = cases_root / f"c{idx:04d}"
        case_dir.mkdir(parents=True, exist_ok=True)
        try:
            step_timeout = max((float(t.timeout) * 2.5) if t.timeout else 30.0, 30.0)
            try:
                inp_arg = Path(t.input).resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                inp_arg = str(t.input)

            flags = ["--std-root", "std"]
            if t.target:
                flags += ["--target", t.target]
            flags += list(t.flags)

            self_exe = case_dir / "self.exe"
            prog_obj = case_dir / "prog.obj"
            gnu_exe = case_dir / "gnu.exe"

            # 1) Build self-linked PE32+ executable
            r_bself = axtest.run_proc([compiler, "build", *flags, "-o", str(self_exe), inp_arg], step_timeout, repo_root)
            if r_bself.spawn_error or r_bself.timed_out or r_bself.rc != 0 or not self_exe.is_file():
                return f"{t.id}: self build failed (rc={r_bself.rc}): {r_bself.err.decode('utf-8', 'replace')[:300]}"

            # 2) Build COFF object via `--emit=obj`
            r_bobj = axtest.run_proc(
                [compiler, "build", *flags, "--emit=obj", "-o", str(prog_obj), inp_arg], step_timeout, repo_root
            )
            if r_bobj.spawn_error or r_bobj.timed_out or r_bobj.rc != 0 or not prog_obj.is_file():
                return f"{t.id}: --emit=obj failed (rc={r_bobj.rc}): {r_bobj.err.decode('utf-8', 'replace')[:300]}"

            try:
                inspect_coff_external_symbols(prog_obj.read_bytes(), t.id)
            except ValidationError as ve:
                return str(ve)

            # 3) Link `prog.obj` + `axiom_rt.obj` with GNU `ld`
            ld_extra = extract_ld_stack_args(t.flags)
            ld_cmd = [
                ld_tool,
                "-m",
                "i386pep",
                "--subsystem",
                "console",
                "-e",
                "axiom_start",
                *ld_extra,
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
            ]
            r_ld = axtest.run_proc(ld_cmd, step_timeout, repo_root)
            if r_ld.spawn_error or r_ld.timed_out or r_ld.rc != 0 or not gnu_exe.is_file():
                return f"{t.id}: GNU ld failed (rc={r_ld.rc}): {r_ld.err.decode('utf-8', 'replace')[:400]}"

            # 4) Execute self-linked `self.exe` and GNU-linked `gnu.exe` sequentially and compare
            env = dict(os.environ)
            env.setdefault("AXIOM_STD", "std")
            if t.env:
                env.update(t.env)

            r_self = axtest.run_proc([str(self_exe), *t.args], step_timeout, repo_root, stdin=t.stdin, env=env)
            if r_self.spawn_error or r_self.timed_out:
                return f"{t.id}: self.exe abnormal run (spawn={r_self.spawn_error}, timeout={r_self.timed_out})"

            r_gnu = axtest.run_proc([str(gnu_exe), *t.args], step_timeout, repo_root, stdin=t.stdin, env=env)
            if r_gnu.spawn_error or r_gnu.timed_out:
                return f"{t.id}: gnu.exe abnormal run (spawn={r_gnu.spawn_error}, timeout={r_gnu.timed_out})"

            exp_exit = t.exit_code if t.exit_code is not None else 0
            if r_self.rc != exp_exit:
                return f"{t.id}: self.exe rc={r_self.rc} != expected {exp_exit}"
            if r_gnu.rc != r_self.rc:
                return f"{t.id}: gnu.exe rc={r_gnu.rc} != self.exe rc={r_self.rc}"
            if r_gnu.out != r_self.out:
                return (
                    f"{t.id}: stdout mismatch between gnu.exe ({len(r_gnu.out)}B) and self.exe ({len(r_self.out)}B): "
                    f"gnu={r_gnu.out[:120]!r} vs self={r_self.out[:120]!r}"
                )
            if r_gnu.err != r_self.err:
                return (
                    f"{t.id}: stderr mismatch between gnu.exe ({len(r_gnu.err)}B) and self.exe ({len(r_self.err)}B): "
                    f"gnu={r_gnu.err[:120]!r} vs self={r_self.err[:120]!r}"
                )
            return None
        finally:
            shutil.rmtree(case_dir, ignore_errors=True)

    failures: list[str] = []
    workers = min(6, max(2, (os.cpu_count() or 4) // 2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for err in pool.map(verify_test, enumerate(selected)):
            if err is not None:
                failures.append(err)

    if failures:
        preview = "\n  ".join(failures[:20])
        raise ValidationError(f"{len(failures)}/{len(selected)} GNU ld cross-linked tests failed:\n  {preview}")

    print(f"GNU-LD-RUN-ORACLE ok ({len(selected)} native run tests verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
