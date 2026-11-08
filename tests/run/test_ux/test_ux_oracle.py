#!/usr/bin/env python3
"""Oracle for E19.5 Test Runner UX 2.0, MIR Differential Harness, Opt Bisect & Debug/Trace Audit (T818).

Covers REQ-TOOL-002..003, REQ-TOOL-005..011, REQ-TOOL-179, REQ-TST-112:
1. Assembles the real `compiler/opt/bisect/mod.ax`, `compiler/test_runner/mod.ax`,
   and `compiler/driver/test_cmd/mod.ax` modules (plus kernel/source/diag/query/ux2
   dependencies) with `test_ux_probe.ax.in`, then executes the bundled probe under
   `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` to verify byte-identical
   execution parity across all tiers.
2. Runs the standalone E19.5 fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`,
   verifying MIR interpreter vs native backend differential equivalence and auditing
   production binaries to confirm zero leaked `.axmir` / `.axoracle` / `.axmeta` / `.axdb`
   debug or oracle sections/magics when not requested.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[3]
SELFHOST_DIR = ROOT / "tests" / "selfhost"
if str(SELFHOST_DIR) not in sys.path:
    sys.path.insert(0, str(SELFHOST_DIR))

import bundle_common as bc  # noqa: E402


TEST_UX_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.diag.ux2", "compiler"),
    ("compiler.opt.bisect", "compiler"),
    ("compiler.test_runner", "compiler"),
    ("compiler.driver.test_cmd", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[test_ux] isolation_ok=true parallel_det_ok=true filter_ok=true passed=3 ignored=1\n"
    "probe[mir_diff] diff_ok=true handoff_bisect=true oracle_zero_prod_ok=true\n"
    "probe[opt_bisect] limit_ok=true culprit_step=6 evals=4 replay_ok=true\n"
    "probe[debug_and_cli] audit_ok=true inline_frames=3 trace_zero_cost=true cli_ok=true\n"
    "TEST-UX-PROBE-PASS\n"
)

FIXTURES = [
    "test_discovery_filter_and_mir_diff",
    "opt_bisect_and_replay_isolation",
    "debug_metadata_inline_and_trace_audit",
]

FORBIDDEN_PROD_MAGICS = [
    b"AXMETA01",
    b"AXDB_IDX",
    b".axmeta",
    b".axdb",
    b".axmir",
    b".axoracle",
]


def run_cmd(cmd: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def verify_compiler_test_ux_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "test_ux_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    bundle_path = tmp_path / "test_ux_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(ROOT))
    modules_text = bc.assemble_compiler_modules(TEST_UX_BUNDLE_MODULES, root=str(ROOT))
    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n// ---probe: test_ux_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[test_ux_probe_bundle] interp rc={r_interp.returncode} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[test_ux_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"test_ux_probe_bundle_{opt_label}.exe"
        build_cmd = [
            str(axiomc),
            "build",
            "--stack-reserve=67108864",
            *opt_flags,
            str(bundle_path),
            "-o",
            str(exe_path),
        ]
        r_build = run_cmd(build_cmd, tmp_path)
        if r_build.returncode != 0:
            errors.append(
                f"[test_ux_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[test_ux_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[test_ux_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
            )

    return errors


def verify_fixture(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
    stem: str,
) -> list[str]:
    errors: list[str] = []
    ax_path = case_dir / f"{stem}.ax"
    expected_stdout_path = case_dir / f"{stem}.stdout"
    if not ax_path.is_file():
        return [f"missing fixture source: {ax_path}"]
    if not expected_stdout_path.is_file():
        return [f"missing expected stdout: {expected_stdout_path}"]

    expected_stdout = expected_stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    r_interp = run_cmd([str(axiomc), "run", "--interp", str(ax_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(f"[{stem}] interp failed rc={r_interp.returncode}: {r_interp.stderr}")
    elif r_interp.stdout.replace("\r\n", "\n") != expected_stdout:
        errors.append(
            f"[{stem}] interp stdout mismatch:\ngot:\n{r_interp.stdout}\nexpected:\n{expected_stdout}"
        )

    for opt_label, opt_flags in [
        ("O0", ["-O0"]),
        ("O1", ["-O1"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"{stem}_{opt_label}.exe"
        build_cmd = [str(axiomc), "build", *opt_flags, str(ax_path), "-o", str(exe_path)]
        r_build = run_cmd(build_cmd, tmp_path)
        if r_build.returncode != 0:
            errors.append(
                f"[{stem}] {opt_label} build failed rc={r_build.returncode}: {r_build.stderr}"
            )
            continue
        if not exe_path.is_file():
            errors.append(f"[{stem}] {opt_label} missing output executable: {exe_path}")
            continue

        pe_bytes = exe_path.read_bytes()
        for magic in FORBIDDEN_PROD_MAGICS:
            if magic in pe_bytes:
                errors.append(
                    f"[{stem}] {opt_label} leaked forbidden metadata/oracle marker {magic!r} into production executable"
                )

        r_native = run_cmd([str(exe_path)], tmp_path)
        if r_native.returncode != 0:
            errors.append(
                f"[{stem}] {opt_label} run failed rc={r_native.returncode}: {r_native.stderr}"
            )
            continue
        if r_native.stdout.replace("\r\n", "\n") != expected_stdout:
            errors.append(
                f"[{stem}] {opt_label} stdout mismatch:\ngot:\n{r_native.stdout}\nexpected:\n{expected_stdout}"
            )

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: test_ux_oracle.py <axiomc_exe> [build_dir] [tmp_dir] [root_dir]", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent
    if not axiomc.is_file():
        print(f"missing compiler binary: {axiomc}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="axiom_test_ux_") as td:
        tmp_path = pathlib.Path(td)
        all_errors.extend(verify_compiler_test_ux_bundle(axiomc, case_dir, tmp_path))
        for stem in FIXTURES:
            all_errors.extend(verify_fixture(axiomc, case_dir, tmp_path, stem))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"TEST-UX-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
