#!/usr/bin/env python3
"""Oracle for E20.1 CompilerDB Build Graph Planner, Host/Target Split, Content-Addressed Cache & Workspace CLI (T852).

Covers SPEC-110 §§3..6 (`AXS-BLD-020`..`053`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`,
`INV-BLD-001`..`003`):
1. Assembles the real `compiler/build/cache/mod.ax`, `compiler/build/graph/mod.ax`, and
   `compiler/driver/workspace_cmd/mod.ax` modules (plus kernel/source/diag/query/ux2/manifest/workspace
   dependencies) with `build_graph_probe.ax.in`, then executes the bundled probe under `--interp`,
   `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` to verify byte-identical
   execution parity across all tiers.
2. Runs the standalone E20.1 build-graph fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
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


BUILD_GRAPH_BUNDLE_MODULES = [
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
    ("compiler.build.cache", "compiler"),
    ("compiler.build.graph", "compiler"),
    ("compiler.driver.workspace_cmd", "compiler"),
]

EXPECTED_PROBE_STDOUT = (
    "probe[graph_split] lower_ok=true actions=14 host=6 target=8 isolation_ok=true mismatch_rejected=true code=220\n"
    "probe[sandbox_prov] sandboxes=1 provenances=1 caps_denied=true ambient_env=false access_ok=true env_ok=true\n"
    "probe[cache_cutoff] cold_exec=14 warm_cached=14 cutoff_exec=3 cutoff_cached=11 cutoff_reused=9 poison_evicted=true cancel_safe=true invariance_ok=true\n"
    "probe[workspace_cli] check_ok=true run_ambig_exit=2 run_sel_exit=0 graph_json_ok=true graph_dot_ok=true bad_fmt_exit=2 unk_opt_exit=2 clean_ok=true\n"
    "BUILD-GRAPH-PROBE-PASS\n"
)

FIXTURES = [
    "deterministic_build_graph_and_host_target_split",
    "four_tier_cache_early_cutoff_and_poison_defense",
    "workspace_cli_and_graph_introspection",
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
        return clean_root
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


def verify_compiler_build_graph_bundle(
    axiomc: pathlib.Path,
    case_dir: pathlib.Path,
    tmp_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    probe_in = case_dir / "build_graph_probe.ax.in"
    if not probe_in.is_file():
        return [f"missing probe source: {probe_in}"]

    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    bundle_path = tmp_path / "build_graph_probe_bundle.ax"
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(BUILD_GRAPH_BUNDLE_MODULES, root=str(clean_root))
    probe_text = probe_in.read_text(encoding="utf-8")
    bundle_source = (
        prelude
        + "\n"
        + modules_text
        + "\n// ---probe: build_graph_probe.ax.in---\n\n"
        + probe_text
    )
    bundle_path.write_text(bundle_source, encoding="utf-8")

    r_interp = run_cmd([str(axiomc), "run", "--interp", "--std-root", str(clean_std), str(bundle_path)], tmp_path)
    if r_interp.returncode != 0:
        errors.append(
            f"[build_graph_probe_bundle] interp rc={r_interp.returncode} stdout={r_interp.stdout!r} stderr={r_interp.stderr}"
        )
        return errors
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        errors.append(
            f"[build_graph_probe_bundle] interp stdout mismatch:\n"
            f"--- got ---\n{r_interp.stdout}\n--- expected ---\n{EXPECTED_PROBE_STDOUT}"
        )
        return errors

    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        exe_path = tmp_path / f"build_graph_probe_bundle_{opt_label}.exe"
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
                f"[build_graph_probe_bundle] {opt_label} build rc={r_build.returncode} stderr={r_build.stderr}"
            )
            continue
        r_run = run_cmd([str(exe_path)], tmp_path)
        if r_run.returncode != 0:
            errors.append(
                f"[build_graph_probe_bundle] {opt_label} run rc={r_run.returncode} stderr={r_run.stderr}"
            )
            continue
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            errors.append(
                f"[build_graph_probe_bundle] {opt_label} stdout mismatch:\n{r_run.stdout}"
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

    clean_root = ensure_clean_root(tmp_path)
    clean_std = clean_root / "std"

    expected_stdout = expected_stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    r_interp = run_cmd([str(axiomc), "run", "--interp", "--std-root", str(clean_std), str(ax_path)], tmp_path)
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
        build_cmd = [str(axiomc), "build", "--std-root", str(clean_std), *opt_flags, str(ax_path), "-o", str(exe_path)]
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
        print("usage: build_graph_oracle.py <axiomc_exe> [build_dir] [tmp_dir] [root_dir]", file=sys.stderr)
        return 2

    axiomc = pathlib.Path(sys.argv[1]).resolve()
    case_dir = pathlib.Path(__file__).resolve().parent
    if not axiomc.is_file():
        print(f"missing compiler binary: {axiomc}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="axiom_build_graph_") as td:
        tmp_path = pathlib.Path(td)
        all_errors.extend(verify_compiler_build_graph_bundle(axiomc, case_dir, tmp_path))
        for stem in FIXTURES:
            all_errors.extend(verify_fixture(axiomc, case_dir, tmp_path, stem))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(b"BUILD-GRAPH-ENGINE-OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
