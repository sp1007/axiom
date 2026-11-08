#!/usr/bin/env python3
"""Oracle for E20.6 Hermetic Multi-Target SDK/Sysroot & Toolchain Bundle Packager,
axiom.lock SDK Pinning & axiomc sdk/toolchain CLI (T876).

Covers SPEC-116 §§4..5 (`AXS-SDK-035`..`055`, `REQ-ECO-8736`, `REQ-PKG-022`, `INV-SDK-002`):
1. Bundles real `compiler.sdk.toolchain`, `compiler.sdk.sysroot`, `std.sdk.bundle`,
   `compiler.driver.sdk_cmd`, and dependency modules with `sdk_toolchain_cli_probe.ax.in`,
   then executes under `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and
   `-O2 --verify-each` to verify byte-identical execution parity across all optimization tiers.
2. Runs standalone E20.6 sdk_toolchain_cli fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


SDK_TOOLCHAIN_CLI_BUNDLE_MODULES = [
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
    ("compiler.sdk.toolchain", "compiler"),
    ("compiler.sdk.sysroot", "compiler"),
    ("compiler.driver.sdk_cmd", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[bundle_pack_merkle] pack_ok=true sorted=true merkle_ok=true traversal_denied=true sig_ok=true\n"
    "probe[offline_installer] cache_paths_ok=true offline_missing_handled=true atomic_layout_ok=true\n"
    "probe[lockfile_pinning] parse_ok=true serialize_ok=true pin_ok=true lock_mismatch_denied=true\n"
    "probe[sdk_toolchain_cli] sdk_list_ok=true sdk_install_ok=true sdk_verify_ok=true tc_info_ok=true tc_verify_ok=true\n"
    "SDK-TOOLCHAIN-CLI-PROBE-PASS\n"
)

FIXTURES = [
    "bundle_pack_install_offline",
    "lockfile_sdk_pinning_drift",
    "sdk_toolchain_cli_dispatch",
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


def verify_compiler_sdk_toolchain_cli_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "sdk_toolchain_cli_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    bundle_path = tmp_path / "sdk_toolchain_cli_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(SDK_TOOLCHAIN_CLI_BUNDLE_MODULES, root=str(clean_root))

    lockfile_mod = clean_root / "std" / "pkg" / "lockfile" / "mod.ax"
    store_mod = clean_root / "std" / "pkg" / "store" / "mod.ax"
    bundle_mod = clean_root / "std" / "sdk" / "bundle" / "mod.ax"

    std_sdk_text = ""
    if lockfile_mod.is_file():
        l_text = lockfile_mod.read_text(encoding="utf-8")
        l_text = l_text.replace("use std.core.host.", "use host_intrinsics.")
        std_sdk_text += "\n" + l_text + "\n"
    if store_mod.is_file():
        s_text = store_mod.read_text(encoding="utf-8")
        s_text = s_text.replace("use std.core.host.", "use host_intrinsics.")
        std_sdk_text += "\n" + s_text + "\n"
    if bundle_mod.is_file():
        b_text = bundle_mod.read_text(encoding="utf-8")
        b_text = b_text.replace("use std.core.host.", "use host_intrinsics.")
        std_sdk_text += "\n" + b_text + "\n"

    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n"
        + std_sdk_text
        + "\n// ---probe: sdk_toolchain_cli_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", "--interp", "--std-root", str(clean_std), str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[sdk_toolchain_cli_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[sdk_toolchain_cli_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"sdk_toolchain_cli_probe_bundle_{opt_label}.exe"
        build_cmd = [
            str(axiomc),
            "build",
            "--stack-reserve=67108864",
            "--std-root",
            str(clean_std),
            *opt_flags,
            str(bundle_path),
            "-o",
            str(exe_path),
        ]
        r_build = run_cmd(build_cmd, tmp_path)
        if r_build.returncode != 0:
            errors.append(
                f"[sdk_toolchain_cli_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[sdk_toolchain_cli_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[sdk_toolchain_cli_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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
        return [f"missing fixture stdout: {expected_stdout_path}"]

    expected = expected_stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    r_interp = run_cmd([str(axiomc), "run", "--interp", "--std-root", str(clean_std), str(ax_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[{stem}] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
    elif r_interp.stdout.replace("\r\n", "\n") != expected:
        errors.append(
            f"[{stem}] interp stdout mismatch:\n--- got ---\n{r_interp.stdout}\n--- expected ---\n{expected}"
        )

    for opt_label, opt_flags in [
        ("O0", ["-O0"]),
        ("O1", ["-O1"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"{stem}_{opt_label}.exe"
        build_cmd = [
            str(axiomc),
            "build",
            "--std-root",
            str(clean_std),
            *opt_flags,
            str(ax_path),
            "-o",
            str(exe_path),
        ]
        r_build = run_cmd(build_cmd, tmp_path)
        if r_build.returncode != 0:
            errors.append(
                f"[{stem}] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[{stem}] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != expected:
            errors.append(
                f"[{stem}] {opt_label} stdout mismatch:\n--- got ---\n{r_run.stdout}\n--- expected ---\n{expected}"
            )

    return errors


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: sdk_toolchain_cli_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent

    with tempfile.TemporaryDirectory(prefix="ax_sdk_toolchain_cli_oracle_") as tmp_str:
        tmp_path = pathlib.Path(tmp_str)
        all_errors: list[str] = []

        all_errors.extend(verify_compiler_sdk_toolchain_cli_bundle(axiomc, case_dir, tmp_path))

        for fixture_stem in FIXTURES:
            all_errors.extend(verify_fixture(axiomc, case_dir, tmp_path, fixture_stem))

        if all_errors:
            sys.stderr.write("E20.6 SDK Toolchain CLI Oracle Failures:\n")
            for err in all_errors:
                sys.stderr.write(f"  * {err}\n")
            return 1

    sys.stdout.buffer.write(b"SDK-TOOLCHAIN-CLI-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
