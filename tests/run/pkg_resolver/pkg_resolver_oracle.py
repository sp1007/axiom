#!/usr/bin/env python3
"""Oracle for E20.2 Deterministic SemVer 2.0 Constraint Solver, Monotonic Feature Unifier & Side-by-Side Package Version Isolation (T855).

Covers SPEC-111 §§1..4 & §6 (`AXS-PKG-001`..`005`, `AXS-PKG-010`..`013`, `AXS-PKG-020`..`024`,
`AXS-PKG-050`..`053`, `REQ-ECO-8736`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-PKG-001`):
1. Assembles the real `compiler/pkg/semver/mod.ax` and `compiler/pkg/resolver/mod.ax`
   modules (plus kernel/source/diag/query/ux2/build dependencies) with `pkg_resolver_probe.ax.in`,
   then executes the bundled probe under `--interp`, `-O0 --verify-each`, `-O1 --verify-each`,
   and `-O2 --verify-each` to verify byte-identical execution parity across all tiers.
2. Runs the standalone E20.2 fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


PKG_RESOLVER_BUNDLE_MODULES = [
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
    ("compiler.pkg.semver", "compiler"),
    ("compiler.pkg.resolver", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[semver2] parse_ok=true invalid_rejected=true precedence_ok=true constraints_ok=true prerelease_isolation_ok=true\n"
    "probe[pubgrub_resolver] backtrack_ok=true lock_pref_ok=true minimal_ok=true order_invariant=true conflict_tree_ok=true negative_edges_ok=true\n"
    "probe[isolation_features] side_by_side_ok=true mangling_disjoint=true links_singleton_ok=true nominal_type_isolation_ok=true reexport_bridge_ok=true feature_unify_ok=true invariants_ok=true\n"
    "PKG-RESOLVER-PROBE-PASS\n"
)

FIXTURES = [
    "semver2_ordering_and_constraints",
    "pubgrub_order_invariance_and_conflicts",
    "side_by_side_isolation_and_features",
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


def get_clean_root() -> tuple[pathlib.Path, list[str]]:
    snap_dir = ROOT / "build-snap-T855"
    if (snap_dir / "std" / "core" / "host.ax").is_file():
        return snap_dir, ["--std-root", str(snap_dir / "std")]
    return ROOT, ["--std-root", str(ROOT / "std")]


def verify_compiler_pkg_resolver_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "pkg_resolver_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root, std_flags = get_clean_root()
    bundle_path = tmp_path / "pkg_resolver_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(PKG_RESOLVER_BUNDLE_MODULES, root=str(ROOT))
    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n// ---probe: pkg_resolver_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[pkg_resolver_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[pkg_resolver_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"pkg_resolver_probe_bundle_{opt_label}.exe"
        build_cmd = [
            str(axiomc),
            "build",
            *std_flags,
            "--stack-reserve=67108864",
            *opt_flags,
            str(bundle_path),
            "-o",
            str(exe_path),
        ]
        r_build = run_cmd(build_cmd, tmp_path)
        if r_build.returncode != 0:
            errors.append(
                f"[pkg_resolver_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[pkg_resolver_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[pkg_resolver_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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

    clean_root, std_flags = get_clean_root()
    r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(ax_path)], tmp_path)
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
        build_cmd = [str(axiomc), "build", *std_flags, *opt_flags, str(ax_path), "-o", str(exe_path)]
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
        print("usage: pkg_resolver_oracle.py <axiomc_exe> [build_dir] [tmp_dir] [root_dir]", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent
    if not axiomc.is_file():
        print(f"missing compiler binary: {axiomc}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="axiom_pkg_resolver_") as td:
        tmp_path = pathlib.Path(td)
        all_errors.extend(verify_compiler_pkg_resolver_bundle(axiomc, case_dir, tmp_path))
        for stem in FIXTURES:
            all_errors.extend(verify_fixture(axiomc, case_dir, tmp_path, stem))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"PKG-RESOLVER-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
