#!/usr/bin/env python3
"""Oracle for E20.4 Dependency Capability-Escalation Auditor, Ed25519 Package/Toolchain
Signature Verifier, Provenance Attestation & axiomc trust CLI (T864).

Covers SPEC-113 §§1, 4, 5 (`AXS-HERM-001`..`004`, `AXS-HERM-030`..`035`, `AXS-HERM-040`,
`AXS-HERM-050`..`053`, `REQ-PKG-022`, `REQ-PKG-024`, `INV-HERM-002`):
1. Bundles real `compiler.driver.trust_cmd`, `std.pkg.trust`, `std.pkg.archive`,
   `std.pkg.lockfile`, and dependency modules with `pkg_supply_chain_probe.ax.in`,
   then executes under `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and
   `-O2 --verify-each` to verify byte-identical execution parity across all tiers.
2. Runs standalone E20.4 supply-chain fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[3]
SELFHOST_DIR = ROOT / "tests" / "selfhost"
if str(SELFHOST_DIR) not in sys.path:
    sys.path.insert(0, str(SELFHOST_DIR))

import bundle_common as bc  # noqa: E402


PKG_SUPPLY_CHAIN_BUNDLE_MODULES = [
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
    ("compiler.driver.trust_cmd", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[capabilities] audit_ok=true escalation_rejected=true undeclared_rejected=true\n"
    "probe[ed25519] keygen_ok=true sign_ok=true verify_ok=true tamper_rejected=true\n"
    "probe[trust_store] untrusted_rejected=true revoked_rejected=true rotation_ok=true\n"
    "probe[provenance_ddc] prov_emit_ok=true prov_verify_ok=true ddc_ok=true ddc_mismatch_denied=true\n"
    "probe[trust_cmd] keygen_cli_ok=true sign_cli_ok=true verify_cli_ok=true audit_cli_ok=true\n"
    "PKG-SUPPLY-CHAIN-PROBE-PASS\n"
)

FIXTURES = [
    "ed25519_sign_and_tamper_rejection",
    "transitive_capability_escalation_auditor",
    "provenance_attestation_and_ddc",
    "trust_cmd_cli_dispatch",
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


def ensure_clean_root(tmp_path: pathlib.Path) -> pathlib.Path:
    clean_root = tmp_path / "_clean_root"
    if clean_root.is_dir():
        shutil.rmtree(str(clean_root), ignore_errors=True)
    clean_root.mkdir(parents=True, exist_ok=True)
    clean_std = clean_root / "std"
    shutil.copytree(str(ROOT / "std"), str(clean_std))
    host_file = clean_std / "core" / "host.ax"
    host_txt = host_file.read_text(encoding="utf-8")
    if "thread_spawn" in host_txt:
        try:
            head_host = subprocess.check_output(
                ["git", "show", "HEAD:std/core/host.ax"],
                cwd=str(ROOT),
                text=True,
                encoding="utf-8",
                stderr=subprocess.DEVNULL,
            )
            host_file.write_text(head_host, encoding="utf-8")
        except Exception:
            idx = host_txt.find("pub unsafe fn thread_spawn")
            if idx != -1:
                intr_idx = host_txt.rfind("@intrinsic", 0, idx)
                if intr_idx != -1:
                    host_file.write_text(host_txt[:intr_idx].rstrip() + "\n", encoding="utf-8")
    clean_compiler = clean_root / "compiler"
    if not clean_compiler.is_dir():
        try:
            os.symlink(str(ROOT / "compiler"), str(clean_compiler), target_is_directory=True)
        except Exception:
            shutil.copytree(str(ROOT / "compiler"), str(clean_compiler))
    return clean_root


def verify_compiler_pkg_supply_chain_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "pkg_supply_chain_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    bundle_path = tmp_path / "pkg_supply_chain_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(PKG_SUPPLY_CHAIN_BUNDLE_MODULES, root=str(clean_root))

    lockfile_mod = clean_root / "std" / "pkg" / "lockfile" / "mod.ax"
    store_mod = clean_root / "std" / "pkg" / "store" / "mod.ax"
    archive_mod = clean_root / "std" / "pkg" / "archive" / "mod.ax"
    trust_mod = clean_root / "std" / "pkg" / "trust" / "mod.ax"

    std_pkg_text = ""
    for mod_path in [lockfile_mod, store_mod, archive_mod, trust_mod]:
        if mod_path.is_file():
            m_text = mod_path.read_text(encoding="utf-8")
            m_text = m_text.replace("use std.core.host.", "use host_intrinsics.")
            std_pkg_text += "\n" + m_text + "\n"

    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n"
        + std_pkg_text
        + "\n// ---probe: pkg_supply_chain_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    std_flags = ["--std-root", str(clean_std)]

    # 1. Interpreter execution
    r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[pkg_supply_chain_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[pkg_supply_chain_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    # 2. Native compilation across -O0, -O1, -O2 with --verify-each
    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"pkg_supply_chain_probe_bundle_{opt_label}.exe"
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
                f"[pkg_supply_chain_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[pkg_supply_chain_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[pkg_supply_chain_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
            )
            continue

    return errors


def verify_standalone_fixtures(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"
    std_flags = ["--std-root", str(clean_std)]

    for name in FIXTURES:
        ax_file = case_dir / f"{name}.ax"
        stdout_file = case_dir / f"{name}.stdout"
        if not ax_file.is_file() or not stdout_file.is_file():
            errors.append(f"missing fixture files: {ax_file} or {stdout_file}")
            continue

        expected_stdout = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n")

        # Interp
        r_interp = run_cmd([str(axiomc), "run", *std_flags, "--interp", str(ax_file)], tmp_path)
        if r_interp.returncode != 0:
            errors.append(
                f"[{name}] interp rc={r_interp.returncode} stderr={r_interp.stderr}"
            )
            continue
        if r_interp.stdout.replace("\r\n", "\n") != expected_stdout:
            errors.append(
                f"[{name}] interp stdout mismatch:\n--- got ---\n{r_interp.stdout}\n--- expected ---\n{expected_stdout}"
            )
            continue

        # Native -O0, -O1, -O2
        for opt_label, opt_flags in [
            ("O0", ["-O0"]),
            ("O1", ["-O1"]),
            ("O2", ["-O2", "--verify-each"]),
        ]:
            exe_path = tmp_path / f"{name}_{opt_label}.exe"
            build_cmd = [str(axiomc), "build", *std_flags, *opt_flags, str(ax_file), "-o", str(exe_path)]
            r_build = run_cmd(build_cmd, tmp_path)
            if r_build.returncode != 0:
                errors.append(f"[{name}] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}")
                continue
            r_run = run_cmd([str(exe_path)], tmp_path)
            if r_run.returncode != 0:
                errors.append(f"[{name}] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}")
                continue
            if r_run.stdout.replace("\r\n", "\n") != expected_stdout:
                errors.append(
                    f"[{name}] {opt_label} stdout mismatch:\n--- got ---\n{r_run.stdout}\n--- expected ---\n{expected_stdout}"
                )
                continue

    return errors


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: pkg_supply_chain_oracle.py <compiler> <build> <tmp> <root>", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent
    tmp_path = pathlib.Path(tempfile.mkdtemp(prefix="ax_pkg_supply_chain_oracle_"))

    try:
        errors = []
        errors.extend(verify_compiler_pkg_supply_chain_bundle(axiomc, case_dir, tmp_path))
        errors.extend(verify_standalone_fixtures(axiomc, case_dir, tmp_path))

        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1

        sys.stdout.buffer.write(b"PKG-SUPPLY-CHAIN-ENGINE-OK\n")
        return 0
    finally:
        shutil.rmtree(str(tmp_path), ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
