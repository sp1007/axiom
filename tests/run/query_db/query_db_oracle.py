#!/usr/bin/env python3
"""Oracle and direct `compiler.query.db` probe runner for E18.1 `CompilerDB`
tables, demand-driven `QueryStack` evaluation, dependency DAG recording, and
deterministic `inspect --emit=query-graph` (`T753` / `SPEC-21` `AXS-QRY-001..013`, `INV-QRY-001`).

1. Bundles `compiler/query/db/mod.ax` with `tests/run/query_db/query_db_probe.ax.in`
   and executes the direct `CompilerDB` engine probe in `--interp` and native
   `-O0`, `-O1`, and `-O2 --verify-each` modes, verifying byte-exact
   `--emit=query-graph` and snapshot-bound diagnostic output.
2. Runs differential `.ax` tests in `tests/run/query_db/` across `--interp`,
   `-O0`, `-O1`, and `-O2 --verify-each`.
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

PROBE_TEMPLATE = HERE / "query_db_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "query_graph revision=R4 nodes=9\n"
    "node parse_module(core::math) state=Ready verified_at=R4 changed_at=R4 hits=1 misses=1\n"
    "  edge parse_module(core::math) -> source_file_input(src/math.ax)\n"
    "  edge parse_module(core::math) -> module_tree_input(core::math)\n"
    "node module_def_map(core::math) state=Ready verified_at=R4 changed_at=R4 hits=5 misses=1\n"
    "  edge module_def_map(core::math) -> parse_module(core::math)\n"
    "node resolve_module(core::math) state=Ready verified_at=R4 changed_at=R4 hits=1 misses=1\n"
    "  edge resolve_module(core::math) -> parse_module(core::math)\n"
    "  edge resolve_module(core::math) -> module_def_map(core::math)\n"
    "node item_signature(core::math.compute) state=Ready verified_at=R4 changed_at=R4 hits=1 misses=1\n"
    "  edge item_signature(core::math.compute) -> module_def_map(core::math)\n"
    "node item_signature(core::math.fact) state=Ready verified_at=R4 changed_at=R4 hits=2 misses=1\n"
    "  edge item_signature(core::math.fact) -> module_def_map(core::math)\n"
    "node item_signature(core::math.square) state=Ready verified_at=R4 changed_at=R4 hits=1 misses=1\n"
    "  edge item_signature(core::math.square) -> module_def_map(core::math)\n"
    "node item_signature(core::math.unreferenced_heavy) state=Ready verified_at=R4 changed_at=R4 hits=0 misses=1\n"
    "  edge item_signature(core::math.unreferenced_heavy) -> module_def_map(core::math)\n"
    "node typeck_body(core::math.compute) state=Ready verified_at=R4 changed_at=R4 hits=1 misses=1\n"
    "  edge typeck_body(core::math.compute) -> resolve_module(core::math)\n"
    "  edge typeck_body(core::math.compute) -> item_signature(core::math.compute)\n"
    "  edge typeck_body(core::math.compute) -> item_signature(core::math.square)\n"
    "node typeck_body(core::math.fact) state=Ready verified_at=R4 changed_at=R4 hits=0 misses=1\n"
    "  edge typeck_body(core::math.fact) -> resolve_module(core::math)\n"
    "  edge typeck_body(core::math.fact) -> item_signature(core::math.fact)\n"
    "diag[AX_CTM_CYCLE] primary=app::cycles.ALPHA trace_len=3\n"
    "diag[AX_TYP_MISMATCH] primary=app::cycles.unrelated_function_still_checked trace_len=1\n"
    "QUERY-DB-PROBE-PASS\n"
)

POSITIVE_FIXTURES = [
    ("demand_driven_firewall", "demand_driven_firewall.ax", "DEMAND-DRIVEN-FIREWALL-OK\n"),
    ("query_graph_determinism", "query_graph_determinism.ax", "QUERY-GRAPH-DETERMINISM-OK\n"),
    ("shallow_verify_backdate_edge", "shallow_verify_backdate_edge.ax", "SHALLOW-VERIFY-BACKDATE-EDGE-OK\n"),
]

QUERY_DB_BUNDLE_MODULES = [
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


def assemble_query_db_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(QUERY_DB_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "query_db" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: query_db_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.query.db probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "query_db_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "query_db_probe_bundle.ax"
    probe_bundle.write_text(assemble_query_db_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"query_db_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for query_db_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"query_db_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build query_db_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"query_db_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for query_db_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
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

    sys.stdout.buffer.write(b"QUERY-DB-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
