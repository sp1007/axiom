#!/usr/bin/env python3
"""T537 QA round 1 adversarial regression: interior-mutable (Atomic-containing) immutable `static` items in the
-O2 OptIR layer.

Assembles `qa_opt_static_atomic_probe.ax.in` with the current `compiler/` sources into a temporary bundle, builds
it with the compiler under test and checks that:
  * a function taking a shared borrow of an immutable `static` whose type contains `@lang("atomic")` records
    EFFECT_WRITES_MEM and is never proven pure, while a reader of a plain immutable scalar `static` records
    READS_MEM only;
  * alias analysis classifies the Atomic-containing immutable static as DOMAIN_GLOBAL_STATIC (escaped,
    raw-address-exposed), a `static mut` as DOMAIN_GLOBAL_STATIC and the plain immutable static as
    DOMAIN_CONST_RDATA.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

EXPECTED_PROBE_STDOUT = (
    "PROBE_ATOMIC_STATIC_SUMMARY=OK\n"
    "PROBE_ATOMIC_STATIC_DOMAIN=OK\n"
    "PROBE_ALL=OK\n"
)

PROBE_BLOBS: list[bytes] = [
    b"probe_static_atomic_src.ax",
    # functions (in order): 0 touch_cell, 1 read_plain, 2 host_all, 3 entry_root
    (
        b"@lang(\"atomic\")\n"
        b"pub struct Atomic<T> {\n"
        b"    pub v: T,\n"
        b"}\n"
        b"\n"
        b"pub struct Cell {\n"
        b"    pub a: Atomic<u32>,\n"
        b"    pub b: i64,\n"
        b"}\n"
        b"\n"
        b"static CELL: Cell = Cell { a: Atomic { v: 0u32 }, b: 3 };\n"
        b"static PLAIN: i64 = 5;\n"
        b"static mut M: i64 = 1;\n"
        b"\n"
        b"fn touch_cell() -> i64 {\n"
        b"    let r = view(CELL);\n"
        b"    r.b\n"
        b"}\n"
        b"\n"
        b"fn read_plain() -> i64 {\n"
        b"    PLAIN\n"
        b"}\n"
        b"\n"
        b"fn host_all() -> i64 {\n"
        b"    let r = view(CELL);\n"
        b"    r.b + PLAIN + unsafe { M }\n"
        b"}\n"
        b"\n"
        b"fn entry_root() -> i64 {\n"
        b"    touch_cell() + read_plain() + host_all()\n"
        b"}\n"
    ),
]


def run_cmd(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def get_axiomc(compiler: str, build_dir: str) -> str:
    if os.path.basename(compiler).lower().startswith("axiomc"):
        return compiler
    for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
        p = os.path.join(build_dir, cand)
        if os.path.isfile(p):
            return p
    return compiler


def assemble_probe(root: str) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    for d in (selfhost_dir, selfhost_opt_dir):
        if d not in sys.path:
            sys.path.insert(0, d)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template = (HERE / "qa_opt_static_atomic_probe.ax.in").read_text(encoding="utf-8")
    main_src = template.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    # Append the optimizer modules the probe uses, skipping any the base list already provides (a duplicate module
    # fails with AX_NAME_DUPLICATE; same invariant as the T430 module-list guard).
    modules = list(got.PIPELINE_MODULES)
    for extra in ("compiler.opt.alias", "compiler.opt.memopt", "compiler.opt.escape", "compiler.opt.sroa", "compiler.opt.inline"):
        if all(name != extra for name, _ in modules):
            modules.append((extra, "compiler"))
    names = [name for name, _ in modules]
    assert len(names) == len(set(names)), "duplicate module in probe bundle"
    modules_src = bc.assemble_compiler_modules(modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: qa_opt_static_atomic_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir = pathlib.Path(os.path.abspath(sys.argv[3]))
    root = os.path.abspath(sys.argv[4])
    tmp_dir.mkdir(parents=True, exist_ok=True)
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    exe_ext = ".exe" if os.name == "nt" else ""

    bundle = tmp_dir / "qa_opt_static_atomic_probe_bundle.ax"
    bundle.write_text(assemble_probe(root), encoding="utf-8", newline="\n")
    probe_exe = tmp_dir / f"qa_opt_static_atomic_probe{exe_ext}"
    bproc = run_cmd([axiomc, "build", "--stack-reserve=67108864", "-O0", "-o", str(probe_exe), str(bundle)],
                    root, timeout=1500)
    if bproc.returncode != 0:
        sys.stderr.write(f"build qa_opt_static_atomic_probe failed:\n{bproc.stdout}\n{bproc.stderr}\n")
        return 1
    rproc = run_cmd([str(probe_exe)], root, timeout=180)
    out = rproc.stdout.replace("\r\n", "\n")
    if rproc.returncode != 0 or out != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(f"qa_opt_static_atomic_probe exit={rproc.returncode}\nexpected:\n{EXPECTED_PROBE_STDOUT}\n"
                         f"got:\n{out}\nstderr:\n{rproc.stderr}\n")
        return 1
    sys.stdout.buffer.write(b"QA-OPT-STATIC-ATOMIC-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
