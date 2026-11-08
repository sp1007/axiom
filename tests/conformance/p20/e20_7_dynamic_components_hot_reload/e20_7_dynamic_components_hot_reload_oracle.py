#!/usr/bin/env python3
"""End-to-end E20.7 Conformance Oracle (T873 / SPEC-115 AXS-COMP-001..055,
INV-COMP-001..002, REQ-ECO-8734):
Dynamic Components, Plugin Discovery, Cross-Boundary Ownership/Capability Isolation,
and Hot-Reload State Migration Conformance Suite.

Steps:
1. Bundles live compiler modules (compiler.component.interface, compiler.component.verify,
   ABI stability & compiler kernel) + standard library modules (std.component.loader,
   std.component.hot_reload) with e20_7_dynamic_components_hot_reload_probe.ax.in.
2. Executes the bundled probe across:
   - `--interp`
   - `-O0 --verify-each`
   - `-O1 --verify-each`
   - `-O2 --verify-each`
   Verifying exact byte-for-byte identical output parity across all 4 modes.
3. Differential verification (--interp vs native -O1 --verify-each) across all 4
   standalone .ax conformance fixtures in tests/conformance/p20/e20_7_dynamic_components_hot_reload/.
4. Verifies clean production binaries without leaked .axmeta, .axdb, .axmir, .axoracle, or .axlto metadata.
5. Emits E20-7-DYNAMIC-COMPONENTS-HOT-RELOAD-CONFORMANCE-OK.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
SELFHOST_DIR = REPO_ROOT / "tests" / "selfhost"
if str(SELFHOST_DIR) not in sys.path:
    sys.path.insert(0, str(SELFHOST_DIR))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e20_7_dynamic_components_hot_reload_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[compiler_vtable_and_boundary] vtable_size_ok=true iface_fp_ok=true id_format_ok=true diag_taxonomy_ok=true\n"
    "probe[discovery_and_negotiation] inspect_ok=true semver_caret_ok=true abi_target_verify_ok=true duplicate_rejected=true cap_attenuation_revocation_ok=true iface_bind_ok=true\n"
    "probe[box_handles_and_epoch_leases] box_allocator_ok=true handle_stale_gen_ok=true handle_stale_epoch_ok=true handle_advance_ok=true lease_unload_blocked=true lease_drain_unload_ok=true\n"
    "probe[multi_epoch_hot_reload] fast_path_ok=true schema_migration_ok=true quiesce_timeout_rollback_ok=true mig_fail_rollback_ok=true deferred_retire_unmap_ok=true zero_state_loss=true\n"
    "E20-7-DYNAMIC-COMPONENTS-HOT-RELOAD-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "interface_negotiation_and_capabilities",
        "interface_negotiation_and_capabilities.ax",
        "interface_negotiation_and_capabilities.stdout",
    ),
    (
        "boundary_firewall_and_allocator_isolation",
        "boundary_firewall_and_allocator_isolation.ax",
        "boundary_firewall_and_allocator_isolation.stdout",
    ),
    (
        "epoch_leases_and_unload_protection",
        "epoch_leases_and_unload_protection.ax",
        "epoch_leases_and_unload_protection.stdout",
    ),
    (
        "multi_epoch_hot_reload_and_state_migration",
        "multi_epoch_hot_reload_and_state_migration.ax",
        "multi_epoch_hot_reload_and_state_migration.stdout",
    ),
    (
        "manifest_corruption_and_semver_edge_cases",
        "manifest_corruption_and_semver_edge_cases.ax",
        "manifest_corruption_and_semver_edge_cases.stdout",
    ),
]

E20_7_BUNDLE_MODULES = [
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
    ("compiler.component.interface", "compiler"),
    ("compiler.component.verify", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    if os.path.isfile(compiler):
        return compiler
    return os.path.join(build_dir, f"axiomc{exe}")


def run_cmd(
    cmd: list[str], cwd: str | pathlib.Path, timeout: int = 180
) -> subprocess.CompletedProcess[str]:
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


def ensure_clean_root(tmp_path: pathlib.Path) -> pathlib.Path:
    clean_root = tmp_path / "_clean_root"
    clean_root.mkdir(parents=True, exist_ok=True)
    clean_std = clean_root / "std"
    if not clean_std.is_dir():
        shutil.copytree(str(REPO_ROOT / "std"), str(clean_std))
        host_file = clean_std / "core" / "host.ax"
        host_txt = host_file.read_text(encoding="utf-8")
        if "thread_spawn" in host_txt:
            try:
                head_host = subprocess.check_output(
                    ["git", "show", "HEAD:std/core/host.ax"],
                    cwd=str(REPO_ROOT),
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
    return clean_root


def assemble_e20_7_probe(root: pathlib.Path, clean_root: pathlib.Path, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(E20_7_BUNDLE_MODULES, root=str(root))

    loader_path = clean_root / "std" / "component" / "loader" / "mod.ax"
    if not loader_path.is_file():
        loader_path = root / "std" / "component" / "loader" / "mod.ax"
    hot_reload_path = clean_root / "std" / "component" / "hot_reload" / "mod.ax"
    if not hot_reload_path.is_file():
        hot_reload_path = root / "std" / "component" / "hot_reload" / "mod.ax"
    loader_src = loader_path.read_text(encoding="utf-8")
    hot_reload_src = hot_reload_path.read_text(encoding="utf-8")

    probe_body = template_path.read_text(encoding="utf-8")
    return (
        f"{prelude}\n"
        f"{modules_text}\n"
        f"// --- std/component/loader/mod.ax ---\n"
        f"{loader_src}\n"
        f"// --- std/component/hot_reload/mod.ax ---\n"
        f"{hot_reload_src}\n"
        f"// --- probe body: {template_path.name} ---\n\n"
        f"{probe_body}\n"
    )


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p20" / "e20_7_dynamic_components_hot_reload" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_production_exe_clean(exe_path: pathlib.Path) -> bool:
    raw = exe_path.read_bytes()
    for forbidden in (
        b"AXMETA01",
        b"AXMI0001",
        b"AXLTO001",
        b"AXMIR001",
        b"AXDB0001",
        b".axmeta",
        b".axdb",
        b".axmir",
        b".axoracle",
        b"__ax_interp_eval",
    ):
        if forbidden in raw:
            sys.stderr.write(f"Production binary {exe_path} leaked token {forbidden!r}\n")
            return False
    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e20_7_dynamic_components_hot_reload_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    clean_root = ensure_clean_root(tmp_dir)
    clean_std = clean_root / "std"

    # 1. Assemble and execute master E20.7 probe bundle across --interp, -O0, -O1, and -O2
    probe_template = resolve_suite_file(root, "e20_7_dynamic_components_hot_reload_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e20_7_dynamic_components_hot_reload_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e20_7_probe(pathlib.Path(root), clean_root, probe_template), encoding="utf-8", newline="\n"
    )

    # 1a. Interpreter run
    iproc = run_cmd([axiomc, "run", "--interp", "--std-root", str(clean_std), str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e20_7 probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e20_7 probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # 1b. Native execution across -O0, -O1, and -O2 with --verify-each
    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        probe_exe = tmp_dir / f"e20_7_probe_{opt_label}{exe_ext}"
        bproc = run_cmd(
            [
                axiomc,
                "build",
                "--stack-reserve=67108864",
                "--std-root",
                str(clean_std),
                *opt_flags,
                "-o",
                str(probe_exe),
                str(probe_bundle),
            ],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(
                f"build e20_7 probe {opt_label} failed:\n{bproc.stdout}\n{bproc.stderr}\n"
            )
            return 1

        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e20_7 probe {opt_label} run failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_native = rproc.stdout.replace("\r\n", "\n")
        if norm_native != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e20_7 probe under {opt_label}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
            )
            return 1

        if not verify_production_exe_clean(probe_exe):
            return 1

    # 2. Differential verification of standalone .ax conformance fixtures (--interp vs native -O1 --verify-each)
    for stem, ax_name, stdout_name in CONFORMANCE_FIXTURES:
        src_path = resolve_suite_file(root, ax_name)
        out_path = resolve_suite_file(root, stdout_name)
        exp_out = out_path.read_text(encoding="utf-8").replace("\r\n", "\n")

        # Interpreter run
        f_iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=60)
        if f_iproc.returncode != 0:
            sys.stderr.write(f"fixture {stem} failed in --interp ({f_iproc.returncode}):\n{f_iproc.stderr}\n")
            return 1
        f_norm_interp = f_iproc.stdout.replace("\r\n", "\n")
        if f_norm_interp != exp_out:
            sys.stderr.write(f"fixture {stem} --interp stdout mismatch:\nexpected:\n{exp_out}\ngot:\n{f_norm_interp}\n")
            return 1

        # Native compile at -O1 --verify-each
        fix_exe = tmp_dir / f"{stem}_O1{exe_ext}"
        f_bproc = run_cmd([axiomc, "build", "-O1", "--verify-each", "-o", str(fix_exe), str(src_path)], root, timeout=60)
        if f_bproc.returncode != 0:
            sys.stderr.write(f"fixture {stem} failed native build -O1:\n{f_bproc.stderr}\n")
            return 1

        # Native run
        f_rproc = run_cmd([str(fix_exe)], root, timeout=60)
        if f_rproc.returncode != 0:
            sys.stderr.write(f"fixture {stem} failed native execution ({f_rproc.returncode}):\n{f_rproc.stderr}\n")
            return 1
        f_norm_native = f_rproc.stdout.replace("\r\n", "\n")
        if f_norm_native != exp_out:
            sys.stderr.write(f"fixture {stem} native stdout mismatch:\nexpected:\n{exp_out}\ngot:\n{f_norm_native}\n")
            return 1

        if not verify_production_exe_clean(fix_exe):
            return 1

    sys.stdout.buffer.write(b"E20-7-DYNAMIC-COMPONENTS-HOT-RELOAD-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
