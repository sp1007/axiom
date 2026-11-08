#!/usr/bin/env python3
"""Oracle for E20.5 ABI Compatibility Diff Engine, Versioned Symbols & SemVer CLI (T868).

Covers SPEC-114 §§4..5 (AXS-ABI-030..042, AXS-ABI-050; REQ-ECO-8734, REQ-PKG-022, REQ-PKG-024):
1. Assembles real compiler modules `compiler/abi/stability`, `compiler/abi/fingerprint`,
   `compiler/abi/compat_diff`, and `compiler/driver/abi_cmd` (plus kernel/diag dependencies)
   with `abi_compat_diff_probe.ax.in`, then executes the bundled probe under `--interp`,
   `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` to verify byte-identical
   execution parity across all optimization tiers.
2. Runs the standalone E20.5 run fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


ABI_COMPAT_DIFF_BUNDLE_MODULES = [
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
    ("compiler.abi.stability", "compiler"),
    ("compiler.abi.fingerprint", "compiler"),
    ("compiler.abi.compat_diff", "compiler"),
    ("compiler.driver.abi_cmd", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[struct_evolution] offset_break_ok=true align_break_ok=true non_extensible_break_ok=true extensible_append_ok=true\n"
    "probe[signature_breaks] call_conv_break_ok=true param_break_ok=true ret_break_ok=true cap_tightened_break_ok=true cap_relaxed_ok=true\n"
    "probe[semver_enforcement] patch_impl_only_ok=true patch_additive_reject_ok=true minor_additive_ok=true minor_breaking_reject_ok=true major_breaking_ok=true\n"
    "probe[symbol_versioning] mangling_ok=true pe_alias_ok=true coexistence_ok=true dup_rejected=true\n"
    "ABI-COMPAT-DIFF-PROBE-PASS\n"
)

FIXTURES = [
    "struct_evolution_compat",
    "signature_capability_compat",
    "semver_policy_enforcement",
    "symbol_version_coexistence",
    "abi_compat_diff_edge_cases",
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


def verify_compiler_abi_compat_diff_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "abi_compat_diff_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    bundle_path = tmp_path / "abi_compat_diff_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(ROOT))
    modules_text = bc.assemble_compiler_modules(ABI_COMPAT_DIFF_BUNDLE_MODULES, root=str(ROOT))
    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n// ---probe: abi_compat_diff_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[abi_compat_diff_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[abi_compat_diff_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"abi_compat_diff_probe_bundle_{opt_label}.exe"
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
                f"[abi_compat_diff_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[abi_compat_diff_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[abi_compat_diff_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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
        print("usage: abi_compat_diff_oracle.py <axiomc_exe> [build_dir] [tmp_dir] [root_dir]", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent
    if not axiomc.is_file():
        print(f"missing compiler binary: {axiomc}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="axiom_abi_compat_diff_") as td:
        tmp_path = pathlib.Path(td)
        all_errors.extend(verify_compiler_abi_compat_diff_bundle(axiomc, case_dir, tmp_path))
        for stem in FIXTURES:
            all_errors.extend(verify_fixture(axiomc, case_dir, tmp_path, stem))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"ABI-COMPAT-DIFF-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
