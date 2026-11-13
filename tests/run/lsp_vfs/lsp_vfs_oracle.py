#!/usr/bin/env python3
"""Oracle and direct `std.editor` + `compiler.lsp.protocol` + `compiler.lsp.vfs`
probe runner for T801 (E19.1 LSP JSON-RPC transport, incremental VFS, AXEDITOR
piece-table buffer & partial-program recovery; `SPEC-100`, `INV-LSP-001`,
`REQ-TOOL-183`, `REQ-TOOL-184`, `REQ-TOOL-188`, `REQ-TOOL-191`, `REQ-TOOL-297`,
`REQ-TOOL-298`, `REQ-TOOL-299`).

1. Bundles `std/editor/mod.ax`, `compiler/query/db/mod.ax`,
   `compiler/incremental/fingerprint/mod.ax`, `compiler/lsp/protocol/mod.ax`,
   and `compiler/lsp/vfs/mod.ax` with `tests/run/lsp_vfs/lsp_vfs_probe.ax.in`
   and executes the direct engine probe in `--interp` and native `-O0`, `-O1`,
   and `-O2 --verify-each` modes.
2. Runs differential `.ax` fixtures in `tests/run/lsp_vfs/` across `--interp`,
   `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "lsp_vfs_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[jsonrpc] frame_ok=true multi_hdr_ok=true malformed_err=-32700 pre_init_err=-32002 cancel_err=-32800 supersede_err=-32800 post_shutdown_err=-32600 exit_clean=0 exit_unclean=1\n"
    "probe[utf8_utf16] vn_bytes=22 vn_utf16=17 emoji_bytes=6 emoji_utf16=4 clamp_ok=true grapheme_fwd=4 grapheme_bwd=4\n"
    "probe[axeditor] promoted=true tree_valid=true large_edits=500 tx_commit=true tx_rollback=true undo_redo_ok=true snap_lines=4\n"
    "probe[vfs_inc_gen] overlay_open=true overlay_closed=false id_stable=true stale_status=2 expected_gen=1 actual_gen=2 reused_gen=2 downstream_recomputed=false codegen_calls=0\n"
    "probe[recovery] member_pkt_own=2 member_ro_cap=1 root_diags=5 suppressed_cascades=2 indep_fn_err=true can_codegen=false\n"
    "LSP-VFS-PROBE-PASS\n"
)

POSITIVE_FIXTURES = [
    (
        "jsonrpc_lifecycle_and_cancellation",
        "jsonrpc_lifecycle_and_cancellation.ax",
        "JSONRPC-LIFECYCLE-AND-CANCELLATION-OK\n",
    ),
    (
        "utf8_utf16_vietnamese_and_axeditor_tree",
        "utf8_utf16_vietnamese_and_axeditor_tree.ax",
        "UTF8-UTF16-VIETNAMESE-AND-AXEDITOR-TREE-OK\n",
    ),
    (
        "generational_id_and_partial_recovery",
        "generational_id_and_partial_recovery.ax",
        "GENERATIONAL-ID-AND-PARTIAL-RECOVERY-OK\n",
    ),
]

LSP_VFS_BUNDLE_MODULES = [
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
    ("compiler.lsp.protocol", "compiler"),
    ("compiler.lsp.vfs", "compiler"),
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


def assemble_lsp_vfs_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    editor_path = pathlib.Path(root) / "std" / "editor" / "mod.ax"
    if not editor_path.is_file():
        editor_path = REPO_ROOT / "std" / "editor" / "mod.ax"
    editor_src = editor_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(LSP_VFS_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "lsp_vfs" / filename
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
ORACLE_BUDGET_S = 495.0


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
        sys.stderr.write("usage: lsp_vfs_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct std.editor + compiler.lsp.protocol + compiler.lsp.vfs probe
    probe_template = resolve_fixture_path(root, "lsp_vfs_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "lsp_vfs_probe_bundle.ax"
    probe_bundle.write_text(assemble_lsp_vfs_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root)
    if iproc.returncode != 0:
        sys.stderr.write(f"lsp_vfs_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for lsp_vfs_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"lsp_vfs_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build lsp_vfs_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"lsp_vfs_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for lsp_vfs_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
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
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            if rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}\n")
                return 1

    sys.stdout.buffer.write(b"LSP-VFS-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(guarded_main(main))
