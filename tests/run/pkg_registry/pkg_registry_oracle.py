#!/usr/bin/env python3
"""Oracle for E20.3 Deterministic .axpkg Archive Packer/Unpacker, SHA-256 Merkle Verifier & Sparse Registry Client (T859).

Covers SPEC-112 §§1..4 (`AXS-REG-010`..`013`, `AXS-REG-030`..`034`,
`REQ-ECO-8736`, `REQ-PKG-024`, `INV-REG-001`, `INV-DET-001`):
1. Bundles real `std.pkg.lockfile`, `std.pkg.store`, `std.pkg.archive`, and `std.pkg.registry`
   with `pkg_registry_probe.ax.in`, then executes under `--interp`, `-O0 --verify-each`,
   `-O1 --verify-each`, and `-O2 --verify-each` to verify byte-identical execution parity across all tiers.
2. Runs standalone E20.3 fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


EXPECTED_PROBE_STDOUT = (
    "probe[archive] packing_ok=true merkle_verify_ok=true traversal_rejected=true case_collision_rejected=true\n"
    "probe[registry] sparse_index_ok=true query_ok=true immutable_enforced=true paths_ok=true\n"
    "probe[rollback] journal_staged_ok=true abort_rollback_ok=true generation_commit_ok=true generation_rollback_ok=true\n"
    "PKG-REGISTRY-PROBE-PASS\n"
)

FIXTURES = [
    "archive_deterministic_and_merkle",
    "registry_sparse_and_immutable",
    "transactional_rollback_and_journal",
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
    snap_dir = ROOT / "build-snap-T859"
    if (snap_dir / "std" / "core" / "host.ax").is_file():
        return snap_dir, ["--std-root", str(snap_dir / "std")]
    return ROOT, ["--std-root", str(ROOT / "std")]


def verify_compiler_pkg_registry_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "pkg_registry_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root, std_flags = get_clean_root()
    bundle_path = tmp_path / "pkg_registry_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))

    lockfile_mod = clean_root / "std" / "pkg" / "lockfile" / "mod.ax"
    store_mod = clean_root / "std" / "pkg" / "store" / "mod.ax"
    archive_mod = clean_root / "std" / "pkg" / "archive" / "mod.ax"
    registry_mod = clean_root / "std" / "pkg" / "registry" / "mod.ax"

    std_pkg_text = ""
    for mod_path in [lockfile_mod, store_mod, archive_mod, registry_mod]:
        if mod_path.is_file():
            m_text = mod_path.read_text(encoding="utf-8")
            m_text = m_text.replace("use std.core.host.", "use host_intrinsics.")
            std_pkg_text += "\n" + m_text + "\n"

    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + std_pkg_text
        + "\n// ---probe: pkg_registry_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[pkg_registry_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[pkg_registry_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"pkg_registry_probe_bundle_{opt_label}.exe"
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
                f"[pkg_registry_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[pkg_registry_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[pkg_registry_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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
                [
                    str(axiomc),
                    "build",
                    *std_flags,
                    "--stack-reserve=67108864",
                    *opt_flags,
                    str(src_path),
                    "-o",
                    str(exe_path),
                ],
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
                    f"[{fixture_name}] {opt_label} run stdout mismatch:\n--- got ---\n{r_run.stdout}\n--- expected ---\n{expected_stdout}"
                )

    return errors


def main() -> int:
    if len(sys.argv) < 5:
        print(f"usage: {sys.argv[0]} <compiler> <build> <tmp> <root>", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    tmp_path = pathlib.Path(sys.argv[3]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent

    bundle_errors = verify_compiler_pkg_registry_bundle(axiomc, case_dir, tmp_path)
    if bundle_errors:
        for err in bundle_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    fixture_errors = verify_standalone_fixtures(axiomc, case_dir, tmp_path)
    if fixture_errors:
        for err in fixture_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"PKG-REGISTRY-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
