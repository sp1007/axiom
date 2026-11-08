#!/usr/bin/env python3
"""Oracle for E20.2 Canonical axiom.lock Serializer/Verifier, Content Store, Offline Vendoring & axiomc pkg CLI (T856).

Covers SPEC-111 §§4..5 (`AXS-PKG-030`..`033`, `AXS-PKG-040`, `AXS-PKG-050`,
`REQ-ECO-8736`, `REQ-PKG-013`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-PKG-002`):
1. Bundles real `std.pkg.lockfile`, `std.pkg.store`, `compiler.driver.pkg_cmd`, and dependency modules
   with `pkg_lockfile_probe.ax.in`, then executes under `--interp`, `-O0 --verify-each`,
   `-O1 --verify-each`, and `-O2 --verify-each` to verify byte-identical execution parity across all tiers.
2. Runs standalone E20.2 fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[3]
SELFHOST_DIR = ROOT / "tests" / "selfhost"
if str(SELFHOST_DIR) not in sys.path:
    sys.path.insert(0, str(SELFHOST_DIR))

import bundle_common as bc  # noqa: E402


PKG_LOCKFILE_BUNDLE_MODULES = [
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
    ("compiler.driver.pkg_cmd", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[lockfile] canonical_order=true graph_hash_ok=true roundtrip_ok=true drift_rejected=true\n"
    "probe[store] cache_path_ok=true sha256_verify_ok=true traversal_rejected=true quotas_enforced=true\n"
    "probe[vendor_cli] vendor_manifest_ok=true offline_missing_ok=true cli_init_ok=true cli_add_ok=true tree_ok=true\n"
    "PKG-LOCKFILE-PROBE-PASS\n"
)

FIXTURES = [
    "lockfile_canonical_and_drift",
    "store_sha256_cache_and_sandbox",
    "offline_vendor_and_cli_engine",
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
    snap_dir = ROOT / "build-snap-T856"
    if (snap_dir / "std" / "core" / "host.ax").is_file():
        return snap_dir, ["--std-root", str(snap_dir / "std")]
    return ROOT, ["--std-root", str(ROOT / "std")]


def verify_compiler_pkg_lockfile_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "pkg_lockfile_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root, std_flags = get_clean_root()
    bundle_path = tmp_path / "pkg_lockfile_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(PKG_LOCKFILE_BUNDLE_MODULES, root=str(clean_root))

    lockfile_mod = clean_root / "std" / "pkg" / "lockfile" / "mod.ax"
    store_mod = clean_root / "std" / "pkg" / "store" / "mod.ax"

    std_pkg_text = ""
    if lockfile_mod.is_file():
        l_text = lockfile_mod.read_text(encoding="utf-8")
        l_text = l_text.replace("use std.core.host.", "use host_intrinsics.")
        std_pkg_text += "\n" + l_text + "\n"
    if store_mod.is_file():
        s_text = store_mod.read_text(encoding="utf-8")
        s_text = s_text.replace("use std.core.host.", "use host_intrinsics.")
        std_pkg_text += "\n" + s_text + "\n"

    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n"
        + std_pkg_text
        + "\n// ---probe: pkg_lockfile_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[pkg_lockfile_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[pkg_lockfile_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"pkg_lockfile_probe_bundle_{opt_label}.exe"
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
                f"[pkg_lockfile_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[pkg_lockfile_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[pkg_lockfile_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
            )
            continue

    return errors


def verify_standalone_fixtures(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    clean_root, std_flags = get_clean_root()

    for fixture_name in FIXTURES:
        src_path = case_dir / f"{fixture_name}.ax"
        stdout_path = case_dir / f"{fixture_name}.stdout"
        if not src_path.is_file() or not stdout_path.is_file():
            errors.append(f"missing fixture files for {fixture_name}")
            continue

        expected_stdout = stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")

        # 1. Interpreter mode
        r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(src_path)], tmp_path)
        if r_interp.returncode != 0:
            errors.append(
                f"[{fixture_name}] interp failed rc={r_interp.returncode} stderr={r_interp.stderr}"
            )
        elif r_interp.stdout.replace("\r\n", "\n") != expected_stdout:
            errors.append(
                f"[{fixture_name}] interp stdout mismatch:\n--- got ---\n{r_interp.stdout}\n--- expected ---\n{expected_stdout}"
            )

        # 2. Native modes
        for opt_label, opt_flags in [
            ("O0", ["-O0"]),
            ("O1", ["-O1"]),
            ("O2", ["-O2", "--verify-each"]),
        ]:
            exe_path = tmp_path / f"{fixture_name}_{opt_label}.exe"
            r_build = run_cmd(
                [str(axiomc), "build", *std_flags, *opt_flags, str(src_path), "-o", str(exe_path)],
                tmp_path,
            )
            if r_build.returncode != 0:
                errors.append(
                    f"[{fixture_name}] {opt_label} build failed rc={r_build.returncode} stderr={r_build.stderr}"
                )
                continue
            r_run = run_cmd([str(exe_path)], tmp_path)
            if r_run.returncode != 0:
                errors.append(
                    f"[{fixture_name}] {opt_label} run failed rc={r_run.returncode} stderr={r_run.stderr}"
                )
                continue
            if r_run.stdout.replace("\r\n", "\n") != expected_stdout:
                errors.append(
                    f"[{fixture_name}] {opt_label} stdout mismatch:\n--- got ---\n{r_run.stdout}\n--- expected ---\n{expected_stdout}"
                )
                continue

    return errors


def main() -> int:
    if len(sys.argv) < 5:
        print(f"usage: {sys.argv[0]} <compiler> <build-dir> <tmp-dir> <root>", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    tmp_path = pathlib.Path(sys.argv[3]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent

    tmp_path.mkdir(parents=True, exist_ok=True)

    errors = []
    errors.extend(verify_compiler_pkg_lockfile_bundle(axiomc, case_dir, tmp_path))
    errors.extend(verify_standalone_fixtures(axiomc, case_dir, tmp_path))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"PKG-LOCKFILE-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
