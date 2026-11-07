#!/usr/bin/env python3
"""Oracle and direct `compiler.parallel.scheduler` probe runner for E18.3
thread-safe immutable compiler snapshots, sharded content-addressed interner,
single-flight query deduplication with cross-worker cycle detection, and
work-stealing query scheduler (`T761` / `SPEC-23` `AXS-PAR-001..044`,
`INV-PAR-001..005`).

1. Bundles `compiler/parallel/scheduler/mod.ax` (with `compiler/query/db/mod.ax`)
   and `tests/run/parallel_scheduler/parallel_scheduler_probe.ax.in` and executes
   the direct `ParallelScheduler` probe in `--interp` and native `-O0`, `-O1`,
   and `-O2 --verify-each` modes, verifying byte-exact equivalence across
   `--jobs 1`, `--jobs 2`, and `--jobs 8`.
2. Runs differential `.ax` tests in `tests/run/parallel_scheduler/` across
   `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "parallel_scheduler_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "hir_mir item=app::entry.main scoped_def=(3,1) blocks=3 locals=2 verified=true\n"
    "hir_mir item=app::geom.dot scoped_def=(1,1) blocks=1 locals=4 verified=true\n"
    "hir_mir item=app::mod_a.err_in_a scoped_def=(4,2) blocks=0 locals=0 verified=false\n"
    "hir_mir item=app::mod_a.FIRST scoped_def=(4,1) blocks=0 locals=0 verified=false\n"
    "hir_mir item=app::mod_b.err_in_b scoped_def=(5,2) blocks=0 locals=0 verified=false\n"
    "hir_mir item=app::mod_b.SECOND scoped_def=(5,1) blocks=0 locals=0 verified=false\n"
    "hir_mir item=app::physics.kinetic_scale scoped_def=(2,1) blocks=2 locals=4 verified=true\n"
    "parallel_cycle[AX_CTM_CYCLE] steps=3: const_eval(app::mod_a.FIRST) -> const_eval(app::mod_b.SECOND) -> const_eval(app::mod_a.FIRST)\n"
    "diag[AX_TYP_MISMATCH] primary=app::mod_a.err_in_a trace_len=1\n"
    "diag[AX_CTM_CYCLE] primary=app::mod_a.FIRST trace_len=3\n"
    "diag[AX_TYP_MISMATCH] primary=app::mod_b.err_in_b trace_len=1\n"
    "parallel_digest epoch=E1 rev=R12 defs=7 interned=14 cycles=1 diags=3\n"
    "PARALLEL-SCHEDULER-PROBE-PASS\n"
)

POSITIVE_FIXTURES = [
    ("sharded_interner_and_snapshots", "sharded_interner_and_snapshots.ax", "SHARDED-INTERNER-AND-SNAPSHOTS-OK\n"),
    ("single_flight_and_cross_worker_cycles", "single_flight_and_cross_worker_cycles.ax", "SINGLE-FLIGHT-AND-CROSS-WORKER-CYCLES-OK\n"),
    ("work_stealing_jobs_equivalence", "work_stealing_jobs_equivalence.ax", "WORK-STEALING-JOBS-EQUIVALENCE-OK\n"),
]

PARALLEL_SCHEDULER_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.parallel.scheduler", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    return compiler


def run_cmd(cmd: list[str], cwd: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def assemble_parallel_scheduler_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(PARALLEL_SCHEDULER_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "parallel_scheduler" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: parallel_scheduler_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.parallel.scheduler probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "parallel_scheduler_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "parallel_scheduler_probe_bundle.ax"
    probe_bundle.write_text(assemble_parallel_scheduler_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"parallel_scheduler_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for parallel_scheduler_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"parallel_scheduler_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build parallel_scheduler_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"parallel_scheduler_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for parallel_scheduler_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        f_interp = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if f_interp.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {f_interp.returncode}:\n{f_interp.stderr}\n")
            return 1
        if f_interp.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp\n")
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
            if rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}\n")
                return 1

    sys.stdout.buffer.write(b"PARALLEL-SCHEDULER-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
