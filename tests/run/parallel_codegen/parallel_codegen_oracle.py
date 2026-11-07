#!/usr/bin/env python3
"""Oracle and direct `compiler.parallel.codegen` probe runner for E18.3
parallel per-module/per-CGU codegen, hybrid incremental cache + parallel CGU
execution, post-join canonical `AXD-060` diagnostic merging, and deterministic
linker input ordering (`T762` / `SPEC-23` `AXS-PAR-020..024`, `AXS-PAR-050..053`,
`INV-PAR-002`).

1. Bundles `compiler/parallel/codegen/mod.ax` (with `compiler/query/db/mod.ax`,
   `compiler/incremental/fingerprint/mod.ax`, `compiler/incremental/cache/mod.ax`,
   and `compiler/parallel/scheduler/mod.ax`) and `tests/run/parallel_codegen/parallel_codegen_probe.ax.in`
   and executes the direct `ParallelCodegenEngine` probe in `--interp` and native
   `-O0`, `-O1`, and `-O2 --verify-each` modes, verifying byte-exact `.obj`,
   `.exe`, and diagnostic equivalence across `--jobs 1`, `--jobs 2`, `--jobs 4`,
   and `--jobs 8` as well as on-disk `.axiom-cache` persistence.
2. Runs differential `.ax` tests in `tests/run/parallel_codegen/` across
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

PROBE_TEMPLATE = HERE / "parallel_codegen_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "parallel_stats total_actions=4 executed=1 cached=3 speculative=0 cancelled=0 failed=0 retries=0 critical_path_cost=145 bottleneck=BALANCED link_barrier=PASSED obj_fp=35b0c5fa61592807aba988b5d9d48939 exe_fp=7a3364114dc9da9cbb975c2f75cb6478 diag_fp=7310b282a17003c7525a0a173eea3a86\n"
    "cgu[0] key=app_pkg::app part=0 cgu_fp=4c89f0f0f295e14e03bc971c4d8f79b6 obj_digest=d0aa44070b5e9ade13bdd11b8163ac55 obj_len=96 lir_insts=14 vregs=6 frame=48 syms=1 relocs=2 stage=PUBLISHED cached=true\n"
    "cgu[1] key=app_pkg::geom part=0 cgu_fp=bbf4f926676d801605d5bdd50d0cb16d obj_digest=f3ae4df5f4f94154b5745aa7c88f8ac6 obj_len=160 lir_insts=27 vregs=16 frame=112 syms=3 relocs=1 stage=PUBLISHED cached=true\n"
    "cgu[2] key=app_pkg::physics part=0 cgu_fp=37435e06c9a7bdcc436be90a566062bf obj_digest=a5ae12de5caaaca54cfcc4b6700b5189 obj_len=128 lir_insts=29 vregs=16 frame=112 syms=2 relocs=2 stage=PUBLISHED cached=false\n"
    "cgu[3] key=app_pkg::util part=0 cgu_fp=ca8c1ac9335ba02d9216db0994737bb3 obj_digest=b24b9d4f4eb0d6069f7b9163177cddfb obj_len=128 lir_insts=13 vregs=7 frame=64 syms=2 relocs=0 stage=PUBLISHED cached=true\n"
    "diag WARNING code=2101 file=1 offset=48 loc=2:12 item=app_pkg::geom.dot msg=unnecessary copy of Vec2 view in dot\n"
    "diag WARNING code=2102 file=2 offset=64 loc=3:9 item=app_pkg::physics.kinetic_scale msg=shadowed local scalar in kinetic_scale\n"
    "diag WARNING code=2103 file=4 offset=32 loc=2:5 item=app_pkg::util.clamp_energy msg=unused bound MAX_ENERGY in clamp_energy\n"
    "diag ERROR code=4001 file=1 offset=80 loc=3:16 item=app_pkg::geom.dot msg=expected i32, found bool in geom.dot\n"
    "diag ERROR code=4001 file=2 offset=96 loc=4:12 item=app_pkg::physics.kinetic_scale msg=expected bool, found i32 in physics.kinetic_scale\n"
    "PARALLEL-CODEGEN-PROBE-PASS\n"
)

POSITIVE_FIXTURES = [
    (
        "cgu_partition_and_jobs_obj_exe_equivalence",
        "cgu_partition_and_jobs_obj_exe_equivalence.ax",
        "CGU-PARTITION-AND-JOBS-OBJ-EXE-EQUIVALENCE-OK\n",
    ),
    (
        "post_join_diagnostic_and_linker_order",
        "post_join_diagnostic_and_linker_order.ax",
        "POST-JOIN-DIAGNOSTIC-AND-LINKER-ORDER-OK\n",
    ),
    (
        "hybrid_incremental_cache_parallel_cgu",
        "hybrid_incremental_cache_parallel_cgu.ax",
        "HYBRID-INCREMENTAL-CACHE-PARALLEL-CGU-OK\n",
    ),
]

PARALLEL_CODEGEN_BUNDLE_MODULES = [
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
    ("compiler.incremental.fingerprint", "compiler"),
    ("compiler.incremental.cache", "compiler"),
    ("compiler.parallel.scheduler", "compiler"),
    ("compiler.parallel.codegen", "compiler"),
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


def assemble_parallel_codegen_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(PARALLEL_CODEGEN_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "parallel_codegen" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_disk_cache_artifacts(cache_dir: pathlib.Path) -> tuple[bool, str]:
    index_file = cache_dir / "dep-graph.axcache"
    if not index_file.is_file():
        return False, f"missing {index_file}"
    raw = index_file.read_bytes()
    if len(raw) < 48 or raw[:8] != b"AXCACHE1":
        return False, f"invalid header magic in {index_file} (len={len(raw)})"
    tmp_index = cache_dir / "dep-graph.axcache.tmp"
    if tmp_index.exists():
        return False, f"leftover temporary file {tmp_index}"
    obj_dir = cache_dir / "objects"
    obj_files = sorted(obj_dir.glob("*.obj")) if obj_dir.is_dir() else []
    if len(obj_files) < 4:
        return False, f"expected >= 4 .obj files in {obj_dir}, found {len(obj_files)}"
    for obj_f in obj_files:
        ob = obj_f.read_bytes()
        if len(ob) < 64 or ob[0] != 0x64 or ob[1] != 0x86:
            return False, f"invalid COFF header in {obj_f}"
        if ob[4:8] != b"\x00\x00\x00\x00":
            return False, f"non-zero COFF TimeDateStamp in {obj_f}"
    return True, "ok"


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: parallel_codegen_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.parallel.codegen probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "parallel_codegen_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "parallel_codegen_probe_bundle.ax"
    probe_bundle.write_text(assemble_parallel_codegen_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"parallel_codegen_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for parallel_codegen_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"parallel_codegen_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build parallel_codegen_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        cache_dir = tmp_dir / f"axiom_par_cache_{flag[1:]}"
        rproc = run_cmd([str(probe_exe), f"--cache-dir={cache_dir}"], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"parallel_codegen_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for parallel_codegen_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1
        ok_disk, reason = verify_disk_cache_artifacts(cache_dir)
        if not ok_disk:
            sys.stderr.write(f"disk cache verification failed for {flag}: {reason}\n")
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

    sys.stdout.buffer.write(b"PARALLEL-CODEGEN-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
