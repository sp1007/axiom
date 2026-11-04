#!/usr/bin/env python3
"""Oracle test for E15.1 (T602): PassManager, EffectInfo summaries, and --verify-each
transformation contract verifier across -O0, -O1, and -O2.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC_AX = HERE / "effect_preserve_io_volatile_panic.ax"
EXPECTED_STDOUT = "STAGE_1=10\nSTAGE_2=35\nSTAGE_3=77\nFINAL=122\n"
DROP_AX = HERE / "drop_raw_ptr_io_order.ax"
EXPECTED_DROP_STDOUT = "ENTER=25\nDROP=3\nDROP=2\nMID=40\nDROP=1\nDONE=40\n"
PROBE_TEMPLATE = HERE / "passmgr_contract_probe.ax.in"
EXPECTED_PROBE_STDOUT = "PROBE_EFFECTS_CG=OK\nPROBE_PASSMGR_CONTRACTS=OK\nPROBE_ALL=OK\n"


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
        p = os.path.join(build_dir, cand)
        if os.path.isfile(p):
            return p
    sys.path.insert(0, os.path.join(root, "tests", "selfhost", "obj_link_driver"))
    import gen_obj_link_driver_tests as gen  # noqa: E402

    bundle_ax = os.path.join(tmp_dir, "axiomc_bundle.ax")
    with open(bundle_ax, "wb") as f:
        f.write(gen.axiomc_bundle_text().encode("utf-8"))
    out_exe = os.path.join(tmp_dir, "axiomc.exe" if os.name == "nt" else "axiomc")
    cmd = [compiler, "build", "--stack-reserve=67108864", "-o", out_exe, bundle_ax]
    r = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if r.returncode != 0:
        sys.stderr.write("failed to build axiomc:\n" + r.stderr.decode("utf-8", "replace"))
        sys.exit(1)
    return out_exe


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


def assemble_passmgr_contract_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    probe_blobs = [
        got.UNIT_MIR_SNIPPETS[17],
        got.UNIT_MIR_SNIPPETS[19],
        got.UNIT_MIR_SNIPPETS[20],
        got.UNIT_MIR_SNIPPETS[21],
        got.UNIT_MIR_SNIPPETS[22],
        got.UNIT_MIR_SNIPPETS[23],
    ]
    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", probe_blobs))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    modules_src = bc.assemble_compiler_modules(got.CORE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: passmgr_verify_each_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler, build_dir, tmp_dir_str, root = sys.argv[1:5]
    axiomc = get_axiomc(compiler, build_dir, tmp_dir_str, root)
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble & directly execute compiler/opt/effects + compiler/opt/passmgr contract probe
    # compiled with --verify-each across -O0, -O1, and -O2.
    probe_template = pathlib.Path(root) / "tests" / "run" / "opt_passmgr" / "passmgr_contract_probe.ax.in"
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "passmgr_contract_probe_bundle.ax"
    probe_bundle.write_text(assemble_passmgr_contract_probe(root, probe_template), encoding="utf-8")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"passmgr_contract_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build passmgr_contract_probe {flag} --verify-each failed:\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"passmgr_contract_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for passmgr_contract_probe under {flag}:\n"
                f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Verify build + execution of end-to-end Axiom fixtures with --verify-each across -O0, -O1, -O2
    # preserves exact observable I/O ordering, deterministic Drop order, raw-pointer stores, and capabilities.
    src_ax = pathlib.Path(root) / "tests" / "run" / "opt_passmgr" / "effect_preserve_io_volatile_panic.ax"
    drop_ax = pathlib.Path(root) / "tests" / "run" / "opt_passmgr" / "drop_raw_ptr_io_order.ax"
    if not src_ax.is_file():
        src_ax = SRC_AX
    if not drop_ax.is_file():
        drop_ax = DROP_AX

    for stem, src_path, exp_out in (
        ("effect_preserve", src_ax, EXPECTED_STDOUT),
        ("drop_raw_ptr", drop_ax, EXPECTED_DROP_STDOUT),
    ):
        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            build_proc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if build_proc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{build_proc.stderr}\n")
                return 1
            run_proc = run_cmd([str(exe_path)], root)
            if run_proc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {run_proc.returncode}:\n{run_proc.stderr}\n")
                return 1
            norm_out = run_proc.stdout.replace("\r\n", "\n")
            if norm_out != exp_out:
                sys.stderr.write(
                    f"stdout mismatch for {stem} under {flag}:\nexpected:\n{exp_out}\ngot:\n{norm_out}\n"
                )
                return 1

    # 3. Verify inspect --emit=optir and --emit=memssa with --verify-each across -O0, -O1, -O2
    for flag in ("-O0", "-O1", "-O2"):
        r1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(src_ax)], root)
        r2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(src_ax)], root)
        if r1.returncode != 0 or r2.returncode != 0:
            sys.stderr.write(f"inspect --emit=optir {flag} --verify-each failed:\n{r1.stderr}\n")
            return 1
        if r1.stdout != r2.stdout:
            sys.stderr.write(f"non-deterministic --emit=optir output under {flag}\n")
            return 1
        for token in (
            "optir_body",
            "idom: bb0",
            "proof #",
            "prop=Reachable certainty=Proven analysis=CFG",
            "prop=NoOverflow",
        ):
            if token not in r1.stdout:
                sys.stderr.write(f"missing token {token!r} in --emit=optir under {flag}:\n{r1.stdout}\n")
                return 1

    m1 = run_cmd([axiomc, "inspect", "--emit=memssa", "-O2", "--verify-each", str(src_ax)], root)
    if m1.returncode != 0:
        sys.stderr.write(f"inspect --emit=memssa -O2 --verify-each failed:\n{m1.stderr}\n")
        return 1
    for token in (
        "memssa_body",
        "mem0 = LiveOnEntry",
        "MemoryDef(",
        "barrier: true",
    ):
        if token not in m1.stdout:
            sys.stderr.write(f"missing token {token!r} in --emit=memssa output:\n{m1.stdout}\n")
            return 1

    # 4. Verify MIR entry gate using valid `mir_body { ... }` syntax:
    # (a) Verified MIR succeeds cleanly.
    ok_mir = tmp_dir / "verified_ok.mir"
    ok_mir.write_text(
        "mir_body {\n"
        "    let mut _0: type#8;\n"
        "    let _1: type#8;\n"
        "    bb0: {\n"
        "        _1 = const 42: type#8;\n"
        "        _0 = copy _1;\n"
        "        return;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    r_ok = run_cmd([axiomc, "inspect", "--emit=optir", "--verify-each", str(ok_mir)], root)
    if r_ok.returncode != 0 or "optir_body" not in r_ok.stdout:
        sys.stderr.write(f"expected verified mir_body to succeed under --emit=optir --verify-each:\n{r_ok.stderr}\n")
        return 1

    # (b) Syntactically valid MIR reading an uninitialized local fails verify_mir before OptIR/PassManager.
    bad_uninit_mir = tmp_dir / "unverified_uninit.mir"
    bad_uninit_mir.write_text(
        "mir_body {\n"
        "    let mut _0: type#8;\n"
        "    let _1: type#8;\n"
        "    bb0: {\n"
        "        _0 = copy _1;\n"
        "        return;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    # (c) Syntactically valid MIR with ill-typed bool-to-i32 copy fails verify_mir before OptIR/PassManager.
    bad_type_mir = tmp_dir / "unverified_ill_typed.mir"
    bad_type_mir.write_text(
        "mir_body {\n"
        "    let mut _0: type#8;\n"
        "    let _1: type#4;\n"
        "    bb0: {\n"
        "        _1 = const true;\n"
        "        _0 = copy _1;\n"
        "        return;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    for label, bad_mir in (("uninit", bad_uninit_mir), ("ill-typed", bad_type_mir)):
        for emit_flag in ("--emit=optir", "--emit=memssa"):
            r_bad = run_cmd([axiomc, "inspect", emit_flag, "--verify-each", str(bad_mir)], root)
            if r_bad.returncode == 0 or len(r_bad.stdout) != 0:
                sys.stderr.write(
                    f"expected {label} mir_body to fail closed under {emit_flag} --verify-each "
                    f"(rc={r_bad.returncode}, stdout_len={len(r_bad.stdout)})\n"
                )
                return 1

    sys.stdout.buffer.write(b"PASSMGR-VERIFY-EACH-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
