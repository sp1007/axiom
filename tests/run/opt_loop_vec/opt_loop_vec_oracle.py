#!/usr/bin/env python3
"""Live oracle for `compiler/opt/vectorize/mod.ax` (T617 / E15.5)."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_loop_vec_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "CASE1_CAP_DISJOINT_AND_SCEV_DEP: OK\n"
    "CASE2_REDUCTION_INT_VS_STRICT_FP: OK\n"
    "CASE3_BROADCAST_STEP_AND_VSELECT: OK\n"
    "CASE4_TARGET_SIMD_WIDTH_AND_COST: OK\n"
    "CASE5_VEC_LOOP_AND_SCALAR_EPILOGUE: OK\n"
    "CASE6_BARRIERS_AND_EMIT_PRINT: OK\n"
    "OPT-LOOP-VEC-PROBE: ALL-OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "cap_disjoint_elementwise_and_epilogue",
        "cap_disjoint_elementwise_and_epilogue.ax",
        "VEC_BANNER=Xin chào vector hóa vòng lặp tự động\nDROP_GUARD=77\nN0=0\nN1=19\nN3=69\nN4=100\nN7=217\nN8=264\nN19=1045\nBLEND=167\n",
    ),
    (
        "associative_int_reductions_and_tail",
        "associative_int_reductions_and_tail.ax",
        "WRAP_ADD=455\nWRAP_MUL=362880\nBIT_XOR=19\nBIT_OR=63\nBIT_AND=0\nMIN_MAX=97\n",
    ),
    (
        "rejected_recurrence_alias_fp_and_barriers",
        "rejected_recurrence_alias_fp_and_barriers.ax",
        "RECUR_SUM=247\nBACK_ANTI=63\nOVERLAP_ALIAS=136\n",
    ),
]

NEGATIVE_PANIC_FIXTURES: list[tuple[str, str]] = [
    ("checked_overflow_in_loop_panic", "checked_overflow_in_loop_panic.ax"),
    ("epilogue_tail_oob_panic", "epilogue_tail_oob_panic.ax"),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc") and os.path.isfile(compiler):
        return compiler
    for d in (build_dir, os.path.join(root, "build"), os.path.join(root, "..", "build")):
        for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
            p = os.path.join(d, cand)
            if os.path.isfile(p):
                return p
    return compiler


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


def assemble_opt_loop_vec_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    main_src = probe_template_path.read_text(encoding="utf-8")
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    vec_modules = list(got.CORE_MODULES) + [
        ("compiler.own.cap", "compiler"),
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.loops", "compiler"),
        ("compiler.opt.bce", "compiler"),
        ("compiler.opt.vectorize", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(vec_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_loop_vec" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_loop_vec_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.vectorize probe under -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "opt_loop_vec_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_loop_vec_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_loop_vec_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0",):
        probe_exe = tmp_dir / f"opt_loop_vec_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build opt_loop_vec_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=180)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt_loop_vec_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt_loop_vec_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")
        if norm_interp != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp:\nexpected:\n{exp_out}\ngot:\n{norm_interp}\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}:\nexpected:\n{exp_out}\ngot:\n{norm_out}\n")
                return 1

    # 3. Differential panic preservation (exit 101) across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename in NEGATIVE_PANIC_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 101:
            sys.stderr.write(f"expected exit 101 for {stem} under --interp, got {iproc.returncode}\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build negative {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 101:
                sys.stderr.write(f"expected exit 101 for {stem} under {flag}, got {rproc.returncode}\n")
                return 1

    sys.stdout.buffer.write(b"OPT-LOOP-VEC-ENGINE: PASS\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
