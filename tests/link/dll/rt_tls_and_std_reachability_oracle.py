#!/usr/bin/env python3
"""Focused regression oracle for T431 compiler/driver & compiler/link fixes:

1. `--emit=obj` does not emit unreferenced `<std>` functions (`trace_poll`, `prelude_loaded`)
   or pull in `__ax_host_print` externals on pure non-printing modules, while still emitting
   referenced `<std>` helpers (`prelude_loaded()`) when called.
2. Zero-function `--kind dll` modules build cleanly without attempting native codegen on
   unmonomorphized generic functions (`std.future.block_on`).
3. Custom `--std-root` trees with a minimal `core/prelude.ax` lacking `Poll` compile cleanly
   even when `future/{mod,block_on}.ax` exist on disk.
4. `build --rt-obj` emits Windows x64 TLS runtime symbols (`_tls_index`, `_tls_used`) so
   `@thread_local` `--emit=obj` outputs link and execute under `gcc -nostdlib` / GNU `ld`.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> int:
    sys.stderr.write(f"FAIL: {msg}\n")
    return 1


def main() -> int:
    if len(sys.argv) < 4:
        sys.stderr.write("usage: rt_tls_and_std_reachability_oracle.py <compiler> <tmp_dir> <repo_root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    tmp_dir = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    gcc = shutil.which("gcc")
    objdump = shutil.which("objdump")
    if not gcc or not objdump:
        return fail("missing gcc or objdump")

    # 1a. Pure `--emit=obj` has zero `__ax_host_print` or `trace_poll` symbols.
    pure_ax = tmp_dir / "pure.ax"
    pure_ax.write_text("fn main() -> i32 { 0 }\n", encoding="utf-8", newline="\n")
    pure_obj = tmp_dir / "pure.obj"
    r = subprocess.run(
        [compiler, "build", "--std-root", str(std_root), "--emit=obj", "-o", str(pure_obj), str(pure_ax)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        return fail(f"pure.ax --emit=obj failed: {r.stderr}")
    syms_txt = subprocess.check_output([objdump, "-t", str(pure_obj)], text=True, timeout=20)
    for unwanted in ("__ax_host_print", "trace_poll", "prelude_loaded", "block_on"):
        if unwanted in syms_txt:
            return fail(f"pure.obj unexpectedly contains unreferenced std symbol {unwanted!r}:\n{syms_txt}")

    # 1b. Calling `prelude_loaded()` emits `prelude_loaded` and executes cleanly.
    prel_ax = tmp_dir / "uses_prel.ax"
    prel_ax.write_text(
        "fn main() -> i32 { if prelude_loaded() { 42 } else { 1 } }\n",
        encoding="utf-8",
        newline="\n",
    )
    prel_exe = tmp_dir / "uses_prel.exe"
    r = subprocess.run(
        [compiler, "build", "--std-root", str(std_root), "-o", str(prel_exe), str(prel_ax)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        return fail(f"uses_prel.ax build failed: {r.stderr}")
    rr = subprocess.run([str(prel_exe)], capture_output=True, timeout=20)
    if rr.returncode != 42:
        return fail(f"uses_prel.exe expected exit 42, got {rr.returncode}")

    # 2. Zero-function `--kind dll` builds cleanly with full std prelude + std/future.
    empty_dll_ax = tmp_dir / "empty_reg.ax"
    empty_dll_ax.write_text("module empty_reg\n", encoding="utf-8", newline="\n")
    empty_dll_out = tmp_dir / "empty_reg.dll"
    r = subprocess.run(
        [compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(empty_dll_out), str(empty_dll_ax)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0 or not empty_dll_out.is_file():
        return fail(f"0-function --kind dll failed (rc={r.returncode}): {r.stderr}")

    # 3. Minimal custom prelude without `Poll` coexisting with `future/{mod,block_on}.ax`.
    mini_std = tmp_dir / "mini_std"
    if mini_std.exists():
        shutil.rmtree(mini_std)
    shutil.copytree(std_root / "core", mini_std / "core")
    shutil.copytree(std_root / "future", mini_std / "future")
    (mini_std / "core" / "prelude.ax").write_text(
        "module std.core.prelude\npub use std.core.option.Option;\npub use std.core.result.Result;\n",
        encoding="utf-8",
        newline="\n",
    )
    mini_obj = tmp_dir / "mini.obj"
    r = subprocess.run(
        [compiler, "build", "--std-root", str(mini_std), "--kind", "obj", "-o", str(mini_obj), str(pure_ax)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0 or not mini_obj.is_file():
        return fail(f"minimal custom prelude build failed (rc={r.returncode}): {r.stderr}")

    # 4. `--rt-obj` + `@thread_local` `--emit=obj` cross-linked via `gcc -nostdlib`.
    rt_obj = tmp_dir / "axiom_rt.obj"
    r = subprocess.run([compiler, "build", "--rt-obj", str(rt_obj)], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not rt_obj.is_file():
        return fail(f"--rt-obj failed (rc={r.returncode}): {r.stderr}")
    rt_syms = subprocess.check_output([objdump, "-t", str(rt_obj)], text=True, timeout=20)
    for req_sym in ("_tls_index", "_tls_used"):
        if req_sym not in rt_syms:
            return fail(f"axiom_rt.obj missing {req_sym!r}:\n{rt_syms}")

    tls_ax = tmp_dir / "tls_cross.ax"
    tls_ax.write_text(
        "module tls_cross\n\n"
        "@thread_local\n"
        "static mut SLOT: i64 = 19i64;\n\n"
        "pub fn main() -> i32 {\n"
        "    let v = unsafe {\n"
        "        SLOT = SLOT + 23i64;\n"
        "        SLOT\n"
        "    };\n"
        "    print_int(v);\n"
        "    print(\"\\n\");\n"
        "    if v == 42i64 { 0 } else { 1 }\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    tls_obj = tmp_dir / "tls_cross.obj"
    tls_exe = tmp_dir / "tls_cross.exe"
    r = subprocess.run(
        [compiler, "build", "--std-root", str(std_root), "--emit=obj", "-o", str(tls_obj), str(tls_ax)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        return fail(f"tls_cross.ax --emit=obj failed: {r.stderr}")
    r_link = subprocess.run(
        [gcc, "-nostdlib", "-Wl,-e,axiom_start", str(tls_obj), str(rt_obj), "-lkernel32", "-o", str(tls_exe)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r_link.returncode != 0:
        return fail(f"gcc -nostdlib TLS cross-link failed: {r_link.stderr}")
    r_run = subprocess.run([str(tls_exe)], capture_output=True, text=True, timeout=20)
    if r_run.returncode != 0 or r_run.stdout.replace("\r\n", "\n") != "42\n":
        return fail(f"tls_cross.exe unexpected run: rc={r_run.returncode}, stdout={r_run.stdout!r}")

    sys.stdout.buffer.write(b"RT-TLS-AND-STD-REACHABILITY-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
