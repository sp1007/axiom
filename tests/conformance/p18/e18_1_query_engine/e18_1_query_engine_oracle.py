#!/usr/bin/env python3
"""E18.1 Conformance Suite Oracle (`T755` / `SPEC-21` `AXS-QRY-001..053`, `INV-QRY-003`):

End-to-end conformance verification covering:
1. Live bundling and execution of `compiler/query/db/mod.ax` (`compiler.query.db`) and
   `compiler/query/engine/mod.ax` (`compiler.query.engine`) with `e18_1_query_engine_probe.ax.in`
   across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`:
   - Multi-module demand-driven `CompilerDB` evaluation, session isolation, and header/body
     firewall (`item_signature` vs `typeck_body` / `mir_body`) (`AXS-QRY-001..012`);
   - Deterministic `inspect --emit=query-graph` output sorted by `(QueryKind, SemanticKey)` (`AXS-QRY-013`);
   - Order-independent cycle detection, canonical `SemanticKey` rotation, and Tarjan SCC discovery
     across all 5 diagnostic codes (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`,
     `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`) (`AXS-QRY-020..023`, `AXS-QRY-050..052`);
   - Cascading error suppression on poisoned recovery values (`AXS-QRY-031`);
   - Snapshot-bound cold vs warm diagnostic equivalence and cycle-breaking revision invalidation (`AXS-QRY-030..033`).
2. Differential execution of all E18.1 conformance `.ax` fixtures in
   `tests/conformance/p18/e18_1_query_engine/` across `--interp`, `-O0 --verify-each`,
   `-O1 --verify-each`, and `-O2 --verify-each`, plus deterministic PE build reproducibility.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e18_1_query_engine_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "query_graph revision=R6 nodes=11\n"
    "node parse_module(core::app) state=Ready verified_at=R6 changed_at=R6 hits=1 misses=1\n"
    "  edge parse_module(core::app) -> source_file_input(src/app.ax)\n"
    "  edge parse_module(core::app) -> module_tree_input(core::app)\n"
    "node parse_module(core::math) state=Ready verified_at=R6 changed_at=R6 hits=1 misses=1\n"
    "  edge parse_module(core::math) -> source_file_input(src/math.ax)\n"
    "  edge parse_module(core::math) -> module_tree_input(core::math)\n"
    "node module_def_map(core::app) state=Ready verified_at=R6 changed_at=R6 hits=1 misses=1\n"
    "  edge module_def_map(core::app) -> parse_module(core::app)\n"
    "node module_def_map(core::math) state=Ready verified_at=R6 changed_at=R6 hits=2 misses=1\n"
    "  edge module_def_map(core::math) -> parse_module(core::math)\n"
    "node resolve_module(core::app) state=Ready verified_at=R6 changed_at=R6 hits=0 misses=1\n"
    "  edge resolve_module(core::app) -> parse_module(core::app)\n"
    "  edge resolve_module(core::app) -> module_def_map(core::app)\n"
    "node resolve_module(core::math) state=Ready verified_at=R6 changed_at=R6 hits=0 misses=1\n"
    "  edge resolve_module(core::math) -> parse_module(core::math)\n"
    "  edge resolve_module(core::math) -> module_def_map(core::math)\n"
    "node item_signature(core::app.compute) state=Ready verified_at=R6 changed_at=R6 hits=0 misses=1\n"
    "  edge item_signature(core::app.compute) -> module_def_map(core::app)\n"
    "node item_signature(core::math.fact) state=Ready verified_at=R6 changed_at=R6 hits=1 misses=1\n"
    "  edge item_signature(core::math.fact) -> module_def_map(core::math)\n"
    "node item_signature(core::math.square) state=Ready verified_at=R6 changed_at=R6 hits=0 misses=1\n"
    "  edge item_signature(core::math.square) -> module_def_map(core::math)\n"
    "node typeck_body(core::app.compute) state=Ready verified_at=R6 changed_at=R6 hits=1 misses=1\n"
    "  edge typeck_body(core::app.compute) -> resolve_module(core::app)\n"
    "  edge typeck_body(core::app.compute) -> item_signature(core::app.compute)\n"
    "  edge typeck_body(core::app.compute) -> item_signature(core::math.square)\n"
    "node typeck_body(core::math.fact) state=Ready verified_at=R6 changed_at=R6 hits=0 misses=1\n"
    "  edge typeck_body(core::math.fact) -> resolve_module(core::math)\n"
    "  edge typeck_body(core::math.fact) -> item_signature(core::math.fact)\n"
    "cycle[AX_QUERY_CYCLE] rev=R8 steps=3: module_def_map(app::reex_a) -> module_def_map(app::reex_b) -> module_def_map(app::reex_a)\n"
    "cycle[AX_TYPE_CYCLE] rev=R8 steps=3: item_signature(app::cycles.AliasX) -> item_signature(app::cycles.AliasY) -> item_signature(app::cycles.AliasX)\n"
    "cycle[AX_TRAIT_CYCLE] rev=R8 steps=3: trait_solve(app::cycles.GoalA#1) -> trait_solve(app::cycles.GoalB#2) -> trait_solve(app::cycles.GoalA#1)\n"
    "cycle[AX_CTM_CYCLE] rev=R8 steps=4: const_eval(app::cycles.C1) -> const_eval(app::cycles.C2) -> const_eval(app::cycles.C3) -> const_eval(app::cycles.C1)\n"
    "cycle[AX_TYPE_CYCLE] rev=R8 steps=2: layout_of(app::cycles.BadNode) -> layout_of(app::cycles.BadNode)\n"
    "scc[AX_QUERY_CYCLE] members=2 head=module_def_map(app::reex_a)\n"
    "scc[AX_TYPE_CYCLE] members=2 head=item_signature(app::cycles.AliasX)\n"
    "scc[AX_TRAIT_CYCLE] members=2 head=trait_solve(app::cycles.GoalA#1)\n"
    "scc[AX_CTM_CYCLE] members=3 head=const_eval(app::cycles.C1)\n"
    "scc[AX_TYPE_CYCLE] members=1 head=layout_of(app::cycles.BadNode)\n"
    "diag[AX_TYPE_CYCLE] primary=app::cycles.AliasX rev=R8 trace_len=3\n"
    "diag[AX_TYPE_CYCLE] primary=app::cycles.BadNode rev=R8 trace_len=2\n"
    "diag[AX_TYP_MISMATCH] primary=app::cycles.indep_err rev=R8 trace_len=1\n"
    "diag[AX_CTM_CYCLE] primary=app::cycles.C1 rev=R8 trace_len=4\n"
    "engine_summary rev=R8 hits=10 misses=16 green=5 cycles=1 suppressed=0 replays=1 dirtied=10\n"
    "E18-1-QUERY-ENGINE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "demand_driven_isolation_and_memo",
        "demand_driven_isolation_and_memo.ax",
        "demand_driven_isolation_and_memo.stdout",
    ),
    (
        "cycle_recovery_and_cascade_suppression",
        "cycle_recovery_and_cascade_suppression.ax",
        "cycle_recovery_and_cascade_suppression.stdout",
    ),
    (
        "snapshot_diag_replay_and_invalidation",
        "snapshot_diag_replay_and_invalidation.ax",
        "snapshot_diag_replay_and_invalidation.stdout",
    ),
    (
        "lollipop_cycle_and_multihop_backdate",
        "lollipop_cycle_and_multihop_backdate.ax",
        "lollipop_cycle_and_multihop_backdate.stdout",
    ),
]

E18_1_BUNDLE_MODULES = [
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
    ("compiler.query.engine", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    return compiler


def run_cmd(cmd: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return bounded_run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def verify_pe_binary(exe_path: pathlib.Path) -> bool:
    if not exe_path.is_file() or exe_path.stat().st_size <= 512:
        return False
    if os.name == "nt" and exe_path.read_bytes()[:2] != b"MZ":
        return False
    return True


def assemble_e18_1_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(E18_1_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p18" / "e18_1_query_engine" / filename
    if cand.is_file():
        return cand
    return HERE / filename


# --- Load-aware step deadline (T440, ADR-0042 section 1) ------------------------------------------
# All subprocess steps of this oracle share ONE wall-clock budget instead of fixed per-step timeouts:
# the old fixed 180 s limit of the bundled `--interp` step was hit on the shared 4-core machine under
# `-j 2` load and surfaced as a TimeoutExpired traceback (T422-qa section 7). ORACLE_BUDGET_S is 3x the
# slowest measured wall time of the whole oracle at scale 1 (table in _workspaces/reports/T440-report.md).
# It is multiplied by AXTEST_TIMEOUT_SCALE (default 1): set that variable to the runner's
# `--timeout-scale` value when re-running a timed-out id (tools/axtest.py does not export it yet).
# A hang anywhere stops the run at the deadline with one `TIMEOUT:` line on stderr and exit 1;
# the manifest `timeout:` stays above the budget so the oracle reports first.
ORACLE_BUDGET_S = 483.0


def _timeout_scale() -> float:
    try:
        scale = float(os.environ.get("AXTEST_TIMEOUT_SCALE") or "1")
    except ValueError:
        return 1.0
    return scale if scale > 0 else 1.0


_DEADLINE = time.monotonic() + ORACLE_BUDGET_S * _timeout_scale()


class OracleTimeout(Exception):
    pass


def bounded_run(cmd, **kwargs):
    """subprocess.run with the time left of the oracle budget as its timeout."""
    left = _DEADLINE - time.monotonic()
    step = " ".join([os.path.basename(str(cmd[0]))] + [str(c) for c in cmd[1:3]])
    if left <= 0:
        raise OracleTimeout(f"budget exhausted before `{step}`")
    try:
        return subprocess.run(cmd, timeout=left, **kwargs)
    except subprocess.TimeoutExpired:
        raise OracleTimeout(
            f"`{step}` killed after {left:.0f}s (budget {ORACLE_BUDGET_S:g}s x scale {_timeout_scale():g})"
        ) from None


def guarded_main(main_fn) -> int:
    try:
        return main_fn()
    except OracleTimeout as e:
        sys.stderr.write(f"TIMEOUT: {e}\n")
        return 1


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e18_1_query_engine_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute bundled compiler.query.db + compiler.query.engine probe across --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "e18_1_query_engine_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e18_1_query_engine_probe_bundle.ax"
    probe_bundle.write_text(assemble_e18_1_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root)
    if iproc.returncode != 0:
        sys.stderr.write(f"e18_1_query_engine_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e18_1_query_engine_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"e18_1_query_engine_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build e18_1_query_engine_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        if not verify_pe_binary(probe_exe):
            sys.stderr.write(f"invalid PE binary for e18_1_query_engine_probe ({flag})\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e18_1_query_engine_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e18_1_query_engine_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of all E18.1 conformance fixtures across --interp, -O0, -O1, -O2 --verify-each
    for stem, filename, stdout_filename in CONFORMANCE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        exp_out = resolve_fixture_path(root, stdout_filename).read_text(encoding="utf-8").replace("\r\n", "\n")

        f_interp = run_cmd([axiomc, "run", "--interp", str(src_path)], root)
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
            if not verify_pe_binary(exe_path):
                sys.stderr.write(f"invalid PE binary for {stem} {flag}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            if rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}\n")
                return 1

    # 3. Deterministic PE build reproducibility check on demand_driven_isolation_and_memo.ax
    repro_src = resolve_fixture_path(root, "demand_driven_isolation_and_memo.ax")
    exe_a = tmp_dir / f"e18_1_repro_a{exe_ext}"
    exe_b = tmp_dir / f"e18_1_repro_b{exe_ext}"
    ba = run_cmd([axiomc, "build", "-O2", "--verify-each", "-o", str(exe_a), str(repro_src)], root)
    bb = run_cmd([axiomc, "build", "-O2", "--verify-each", "-o", str(exe_b), str(repro_src)], root)
    if ba.returncode != 0 or bb.returncode != 0 or exe_a.read_bytes() != exe_b.read_bytes():
        sys.stderr.write("deterministic PE build reproducibility check failed for E18.1\n")
        return 1

    sys.stdout.buffer.write(b"E18.1-QUERY-ENGINE-SEMANTIC-DB-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))
