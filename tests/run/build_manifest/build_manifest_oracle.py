#!/usr/bin/env python3
"""Oracle for E20.1 Declarative `axiom.toml` Manifest, Workspace Discovery, `@cfg` Evaluator & Package DAG (T851).

Covers SPEC-110 §§1..3 & §5 (`AXS-BLD-001`..`006`, `AXS-BLD-010`..`016`, `AXS-BLD-020`..`021`,
`AXS-BLD-050`..`053`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-BLD-001`):
1. Assembles the real `compiler/build/manifest/mod.ax` and `compiler/build/workspace/mod.ax`
   modules (plus kernel/source/diag/query/ux2 dependencies) with `build_manifest_probe.ax.in`,
   then executes the bundled probe under `--interp`, `-O0 --verify-each`, `-O1 --verify-each`,
   and `-O2 --verify-each` to verify byte-identical execution parity across all tiers.
2. Runs the standalone E20.1 fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


BUILD_MANIFEST_BUNDLE_MODULES = [
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
    ("compiler.build.manifest", "compiler"),
    ("compiler.build.workspace", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[manifest_cfg] schema_ok=true scopes=5 script_rejected=true cfg_eval_ok=true invalid_cfg_rejected=true\n"
    'probe[workspace_dag] members_ok=true topo_det_ok=true cycle_rejected=true cycle="alpha -> beta -> alpha" intra_scc_ok=true\n'
    "probe[features_req_pkg_025] unify_ok=true unknown_feat_rejected=true conflict_rejected=true req_pkg_025_audit_ok=true\n"
    "BUILD-MANIFEST-PROBE-PASS\n"
)

FIXTURES = [
    "declarative_manifest_and_cfg_eval",
    "workspace_dag_and_cycle_rejection",
    "feature_unification_and_req_pkg_025",
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


def verify_compiler_build_manifest_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "build_manifest_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    bundle_path = tmp_path / "build_manifest_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(ROOT))
    modules_text = bc.assemble_compiler_modules(BUILD_MANIFEST_BUNDLE_MODULES, root=str(ROOT))
    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n// ---probe: build_manifest_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[build_manifest_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[build_manifest_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"build_manifest_probe_bundle_{opt_label}.exe"
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
                f"[build_manifest_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[build_manifest_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[build_manifest_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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
        print("usage: build_manifest_oracle.py <axiomc_exe> [build_dir] [tmp_dir] [root_dir]", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent
    if not axiomc.is_file():
        print(f"missing compiler binary: {axiomc}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="axiom_build_manifest_") as td:
        tmp_path = pathlib.Path(td)
        all_errors.extend(verify_compiler_build_manifest_bundle(axiomc, case_dir, tmp_path))
        for stem in FIXTURES:
            all_errors.extend(verify_fixture(axiomc, case_dir, tmp_path, stem))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"BUILD-MANIFEST-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
