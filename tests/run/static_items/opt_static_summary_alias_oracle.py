#!/usr/bin/env python3
"""T537 QA round 1 regression (findings F1 + F2) for process-wide `static mut` items in the -O2 OptIR layer.

Assembles `opt_static_summary_alias_probe.ax.in` with the current `compiler/` sources (frontend pipeline +
`compiler.opt.{alias,memopt,escape,sroa,inline}`) into a temporary bundle, builds it with the compiler under test
and checks that:
  * call-graph summaries mark functions that read/write `MIR_LOCAL_STATIC` as READS_MEM / WRITES_MEM and never
    `EFFECT_PURE` / `CERTAINTY_PROVEN` (F1), and memopt keeps a global reload after a non-inlined writer call;
  * `inline_clone_callsite_in_mir` reuses the caller's `MIR_LOCAL_STATIC` for the same global (F2.1);
  * `alias_query_places` reports MUST_ALIAS for two locals naming the same global, never NO_ALIAS for unnamed
    statics, and NO_ALIAS for distinct named globals (F2.2).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

EXPECTED_PROBE_STDOUT = (
    "PROBE_STATIC_EFFECT_SUMMARIES=OK\n"
    "PROBE_STATIC_MEMOPT_CALL_CLOBBER=OK\n"
    "PROBE_STATIC_INLINE_DEDUP=OK\n"
    "PROBE_STATIC_ALIAS_IDENTITY=OK\n"
    "PROBE_ALL=OK\n"
)

PROBE_BLOBS: list[bytes] = [
    # Blob 0: virtual file path for `session_parse_virtual_file`
    b"probe_static_opt_src.ax",
    # Blob 1: source; functions (in order) 0 pure_add .. 7 twice_g, 8 entry_root
    (
        b"static mut G: i64 = 10;\n"
        b"static mut H: i64 = 20;\n"
        b"\n"
        b"fn pure_add(a: i64, b: i64) -> i64 {\n"
        b"    if a < b { a } else { b }\n"
        b"}\n"
        b"\n"
        b"fn set_g(v: i64) {\n"
        b"    unsafe { G = v; }\n"
        b"}\n"
        b"\n"
        b"fn get_g() -> i64 {\n"
        b"    unsafe { G }\n"
        b"}\n"
        b"\n"
        b"fn bump_h() {\n"
        b"    unsafe { H = H + 1; }\n"
        b"}\n"
        b"\n"
        b"fn caller_noinl(x: i64) -> i64 {\n"
        b"    let a: i64 = unsafe { G };\n"
        b"    set_g(x);\n"
        b"    let b: i64 = unsafe { G };\n"
        b"    a + b\n"
        b"}\n"
        b"\n"
        b"fn caller_inl(x: i64) -> i64 {\n"
        b"    let a: i64 = unsafe { G };\n"
        b"    set_g(x);\n"
        b"    let b: i64 = unsafe { G };\n"
        b"    a + b\n"
        b"}\n"
        b"\n"
        b"fn alias_host() -> i64 {\n"
        b"    unsafe { G + H }\n"
        b"}\n"
        b"\n"
        b"fn twice_g() -> i64 {\n"
        b"    let a: i64 = unsafe { G };\n"
        b"    let b: i64 = unsafe { G };\n"
        b"    a + b\n"
        b"}\n"
        b"\n"
        b"fn entry_root(x: i64) -> i64 {\n"
        b"    bump_h();\n"
        b"    pure_add(1, 2) + get_g() + caller_noinl(x) + caller_inl(x) + alias_host() + twice_g()\n"
        b"}\n"
    ),
]


def run_cmd(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


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

    template = (HERE / "opt_static_summary_alias_probe.ax.in").read_text(encoding="utf-8")
    main_src = template.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    # Extra optimizer modules appended to PIPELINE_MODULES, skipping any the base list already provides (a duplicate
    # module in the bundle fails with AX_NAME_DUPLICATE; same invariant as the T430 module-list guard).
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
        sys.stderr.write("usage: opt_static_summary_alias_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir = pathlib.Path(os.path.abspath(sys.argv[3]))
    root = os.path.abspath(sys.argv[4])
    tmp_dir.mkdir(parents=True, exist_ok=True)
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    exe_ext = ".exe" if os.name == "nt" else ""

    bundle = tmp_dir / "opt_static_summary_alias_probe_bundle.ax"
    bundle.write_text(assemble_probe(root), encoding="utf-8", newline="\n")
    probe_exe = tmp_dir / f"opt_static_summary_alias_probe{exe_ext}"
    bproc = run_cmd(
        [axiomc, "build", "--stack-reserve=67108864", "-O0", "-o", str(probe_exe), str(bundle)],
        root,
        timeout=1500,
    )
    if bproc.returncode != 0:
        sys.stderr.write(f"build opt_static_summary_alias_probe failed:\n{bproc.stdout}\n{bproc.stderr}\n")
        return 1
    rproc = run_cmd([str(probe_exe)], root, timeout=180)
    out = rproc.stdout.replace("\r\n", "\n")
    if rproc.returncode != 0 or out != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"opt_static_summary_alias_probe exit={rproc.returncode}\nexpected:\n{EXPECTED_PROBE_STDOUT}\n"
            f"got:\n{out}\nstderr:\n{rproc.stderr}\n"
        )
        return 1
    sys.stdout.buffer.write(b"OPT-STATIC-SUMMARY-ALIAS-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
