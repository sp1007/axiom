#!/usr/bin/env python3
"""Oracle for E20.7 Component Loader, Lease Table & Hot-Reload Runtime (T872).

Covers SPEC-115 §§1..5 & §6 (AXS-COMP-001..006, AXS-COMP-010..015, AXS-COMP-020..025,
AXS-COMP-030..037, AXS-COMP-040..043, AXS-COMP-050; REQ-ECO-8734, INV-COMP-002):
1. Bundles `std/component/loader/mod.ax` + `std/component/hot_reload/mod.ax`
   with `component_hot_reload_probe.ax.in`, then executes the bundled probe under
   `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` to verify
   byte-identical execution parity across all tiers.
2. Runs the standalone E20.7 fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile


HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
SELFHOST_DIR = REPO_ROOT / "tests" / "selfhost"
if str(SELFHOST_DIR) not in sys.path:
    sys.path.insert(0, str(SELFHOST_DIR))

import bundle_common as bc  # noqa: E402


EXPECTED_PROBE_STDOUT = (
    "probe[loader] inspect_ok=true abi_target_verify_ok=true semver_caret_ok=true duplicate_rejected=true cap_attenuation_revocation_ok=true iface_bind_ok=true\n"
    "probe[box_handle_lease] box_allocator_ok=true handle_stale_gen_ok=true handle_stale_epoch_ok=true handle_advance_ok=true lease_unload_blocked=true lease_drain_unload_ok=true\n"
    "probe[hot_reload] fast_path_ok=true schema_migration_ok=true quiesce_timeout_rollback_ok=true mig_fail_rollback_ok=true deferred_retire_unmap_ok=true zero_state_loss=true\n"
    "COMPONENT-HOT-RELOAD-PROBE-PASS\n"
)

FIXTURES = [
    "preflight_discovery_and_negotiation",
    "component_box_and_epoch_leases",
    "multi_epoch_hot_reload_and_rollback",
]


def run_cmd(cmd: list[str], cwd: pathlib.Path, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def assemble_probe_source(root: pathlib.Path, probe_template: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(root))
    loader_path = root / "std" / "component" / "loader" / "mod.ax"
    hot_reload_path = root / "std" / "component" / "hot_reload" / "mod.ax"

    loader_src = loader_path.read_text(encoding="utf-8")
    hot_reload_src = hot_reload_path.read_text(encoding="utf-8")
    probe_src = probe_template.read_text(encoding="utf-8")

    return (
        prelude
        + "\n\n// --- std/component/loader/mod.ax ---\n"
        + loader_src
        + "\n\n// --- std/component/hot_reload/mod.ax ---\n"
        + hot_reload_src
        + "\n\n// --- component_hot_reload_probe.ax.in ---\n"
        + probe_src
    )


def verify_probe_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
    root: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "component_hot_reload_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    bundle_path = tmp_path / "component_hot_reload_probe_bundle.ax"
    bundle_source = assemble_probe_source(root, probe_in)
    bundle_path.write_text(bundle_source, encoding="utf-8")

    # 1. Interpreter mode
    r_interp = run_cmd([str(axiomc), "run", "--interp", str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        return [
            f"probe --interp returned {r_interp.returncode}\nSTDOUT:\n{r_interp.stdout}\nSTDERR:\n{r_interp.stderr}"
        ]
    norm_interp = r_interp.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        return [f"probe --interp stdout mismatch:\n--- EXPECTED ---\n{EXPECTED_PROBE_STDOUT}--- ACTUAL ---\n{norm_interp}"]

    # 2. Native tiers (-O0, -O1, -O2 with --verify-each)
    tiers = [
        ("-O0", ["-O0", "--verify-each"]),
        ("-O1", ["-O1", "--verify-each"]),
        ("-O2", ["-O2", "--verify-each"]),
    ]
    for tag, flags in tiers:
        exe_path = tmp_path / f"probe_{tag}.exe"
        compile_cmd = [str(axiomc), "build", str(bundle_path), "-o", str(exe_path)] + flags
        c_res = run_cmd(compile_cmd, tmp_path)
        if c_res.returncode != 0:
            errors.append(
                f"probe compile {tag} failed ({c_res.returncode}):\nSTDOUT:\n{c_res.stdout}\nSTDERR:\n{c_res.stderr}"
            )
            continue
        run_res = run_cmd([str(exe_path)], tmp_path)
        if run_res.returncode != 0:
            errors.append(
                f"probe run {tag} returned {run_res.returncode}:\nSTDOUT:\n{run_res.stdout}\nSTDERR:\n{run_res.stderr}"
            )
            continue
        norm_run = run_res.stdout.replace("\r\n", "\n")
        if norm_run != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"probe run {tag} stdout mismatch:\n--- EXPECTED ---\n{EXPECTED_PROBE_STDOUT}--- ACTUAL ---\n{norm_run}"
            )

    return errors


def verify_fixtures(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    tiers = [
        ("interp", None),
        ("-O0", ["-O0"]),
        ("-O1", ["-O1"]),
        ("-O2", ["-O2", "--verify-each"]),
    ]

    for fix in FIXTURES:
        ax_file = case_dir / f"{fix}.ax"
        stdout_file = case_dir / f"{fix}.stdout"
        if not ax_file.is_file() or not stdout_file.is_file():
            errors.append(f"missing fixture files for {fix}")
            continue

        expected = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n")

        for tag, flags in tiers:
            if tag == "interp":
                res = run_cmd([str(axiomc), "run", "--interp", str(ax_file)], tmp_path)
                if res.returncode != 0:
                    errors.append(
                        f"fixture {fix} [interp] returned {res.returncode}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
                    )
                    continue
                actual = res.stdout.replace("\r\n", "\n")
                if actual != expected:
                    errors.append(f"fixture {fix} [interp] stdout mismatch:\nEXP:\n{expected}ACT:\n{actual}")
            else:
                exe = tmp_path / f"{fix}_{tag}.exe"
                c_res = run_cmd([str(axiomc), "build", str(ax_file), "-o", str(exe)] + (flags or []), tmp_path)
                if c_res.returncode != 0:
                    errors.append(
                        f"fixture {fix} build {tag} failed ({c_res.returncode}):\nSTDOUT:\n{c_res.stdout}\nSTDERR:\n{c_res.stderr}"
                    )
                    continue
                r_res = run_cmd([str(exe)], tmp_path)
                if r_res.returncode != 0:
                    errors.append(
                        f"fixture {fix} run {tag} returned {r_res.returncode}:\nSTDOUT:\n{r_res.stdout}\nSTDERR:\n{r_res.stderr}"
                    )
                    continue
                actual = r_res.stdout.replace("\r\n", "\n")
                if actual != expected:
                    errors.append(f"fixture {fix} run {tag} stdout mismatch:\nEXP:\n{expected}ACT:\n{actual}")

    return errors


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: component_hot_reload_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = pathlib.Path(sys.argv[1]).resolve()
    build_dir = pathlib.Path(sys.argv[2]).resolve()
    tmp_arg = pathlib.Path(sys.argv[3]).resolve()
    root = pathlib.Path(sys.argv[4]).resolve()

    axiomc = compiler
    exe_name = "axiomc2.exe" if os.name == "nt" else "axiomc2"
    cand_axiomc2 = build_dir / exe_name
    if cand_axiomc2.is_file():
        axiomc = cand_axiomc2

    case_dir = root / "tests" / "run" / "component_hot_reload"
    if not case_dir.is_dir():
        case_dir = HERE

    with tempfile.TemporaryDirectory(prefix="ax_comp_hot_reload_oracle_") as td:
        tmp_path = pathlib.Path(td)

        probe_errs = verify_probe_bundle(axiomc, case_dir, tmp_path, root)
        if probe_errs:
            for e in probe_errs:
                sys.stderr.write(f"[PROBE ERROR] {e}\n")
            return 1

        fix_errs = verify_fixtures(axiomc, case_dir, tmp_path)
        if fix_errs:
            for e in fix_errs:
                sys.stderr.write(f"[FIXTURE ERROR] {e}\n")
            return 1

    sys.stdout.buffer.write(b"COMPONENT-HOT-RELOAD-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
