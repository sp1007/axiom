#!/usr/bin/env python3
"""Oracle for E20.4 Hermetic build sandbox, filesystem/env/network/clock isolation,
--remap-path-prefix & bit-for-bit reproducibility verifier (T863).

Covers SPEC-113 §§2..3 (`AXS-HERM-010`..`023`, `REQ-PKG-022`, `REQ-PKG-024`, `INV-HERM-001`):
1. Assembles real `compiler/build/sandbox/mod.ax` and `compiler/build/repro/mod.ax` modules
   with `build_hermetic_probe.ax.in`, then executes under `--interp`, `-O0 --verify-each`,
   `-O1 --verify-each`, and `-O2 --verify-each` to verify byte-identical execution parity across all tiers.
2. Runs standalone E20.4 hermetic/repro fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


BUILD_HERMETIC_BUNDLE_MODULES = [
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
    ("compiler.build.sandbox", "compiler"),
    ("compiler.build.repro", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[sandbox_fs] valid_reads=true valid_writes=true traversal_rejected=true host_escape_rejected=true source_write_rejected=true dep_write_rejected=true violations=4\n"
    "probe[sandbox_env_net_clock] canonical_ok=true path_empty=true allowlist_ok=true env_denied=true net_denied=true process_denied=true clock_denied=true rng_denied=true\n"
    "probe[repro_remap_audit] remap_src_ok=true remap_gen_ok=true remap_out_ok=true remap_std_ok=true remap_cli_ok=true clean_audit=true leak_detected=true\n"
    "probe[repro_diff_verifier] fp_eq=true identical_ok=true diff_detected=true diff_offset=5 section_ok=true diag_reported=true verify_repro_ok=true\n"
    "BUILD-HERMETIC-PROBE-PASS\n"
)

FIXTURES = [
    "sandbox_filesystem_env_network_clock_isolation",
    "canonical_path_prefix_remapping_and_host_leak_audit",
    "double_build_differential_reproducibility_verifier",
    "hermetic_boundary_cases",
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


def verify_compiler_build_hermetic_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "build_hermetic_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    bundle_path = tmp_path / "build_hermetic_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(BUILD_HERMETIC_BUNDLE_MODULES, root=str(clean_root))
    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n// ---probe: build_hermetic_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", "--interp", "--std-root", str(clean_std), str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[build_hermetic_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[build_hermetic_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"build_hermetic_probe_bundle_{opt_label}.exe"
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
                f"[build_hermetic_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[build_hermetic_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[build_hermetic_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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

    expected_stdout = expected_stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    # 1. interp
    r_interp = run_cmd([str(axiomc), "run", "--interp", "--std-root", str(clean_std), str(ax_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(f"[{stem}] interp rc={r_interp.returncode} stderr={r_interp.stderr}")
    elif r_interp.stdout.replace("\r\n", "\n") != expected_stdout:
        errors.append(
            f"[{stem}] interp stdout mismatch:\n--- got ---\n{r_interp.stdout}\n--- expected ---\n{expected_stdout}"
        )

    # 2. native O0 / O1 / O2
    for opt_label, opt_flags in [
        ("O0", ["-O0"]),
        ("O1", ["-O1"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"{stem}_{opt_label}.exe"
        build_cmd = [
            str(axiomc),
            "build",
            "--stack-reserve=33554432",
            "--std-root",
            str(clean_std),
            *opt_flags,
            str(ax_path),
            "-o",
            str(exe_path),
        ]
        r_build = run_cmd(build_cmd, tmp_path)
        if r_build.returncode != 0:
            errors.append(f"[{stem}] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}")
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(f"[{stem}] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}")
            continue
        if r_run.stdout.replace("\r\n", "\n") != expected_stdout:
            errors.append(
                f"[{stem}] {opt_label} stdout mismatch:\n--- got ---\n{r_run.stdout}\n--- expected ---\n{expected_stdout}"
            )

    return errors


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: build_hermetic_oracle.py <axiomc> <build_dir> <tmp_dir> <root_dir>", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    tmp_path = pathlib.Path(sys.argv[3]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent

    all_errors: list[str] = []

    # Step 1: probe bundle verification
    probe_errors = verify_compiler_build_hermetic_bundle(axiomc, case_dir, tmp_path)
    all_errors.extend(probe_errors)

    # Step 2: standalone fixtures
    for fixture in FIXTURES:
        fix_errors = verify_fixture(axiomc, case_dir, tmp_path, fixture)
        all_errors.extend(fix_errors)

    if all_errors:
        print("BUILD-HERMETIC-ORACLE-FAIL", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"BUILD-HERMETIC-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
