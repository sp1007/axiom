#!/usr/bin/env python3
"""End-to-end E20.4 Conformance Oracle (T865 / SPEC-113 §§1..5, INV-HERM-001..003,
REQ-PKG-022, REQ-PKG-024, INV-DET-002):
Hermetic Build Sandbox, Cross-Directory/Cross-Machine Bit-for-Bit Reproducibility,
Ed25519 Signing, Key Rotation & Supply-Chain Trust Conformance Suite.

Steps:
1. Bundles live compiler modules (compiler.build.sandbox, compiler.build.repro,
   compiler.driver.trust_cmd, plus compiler kernel and build dependencies) +
   standard library modules (std.pkg.lockfile, std.pkg.store, std.pkg.archive,
   std.pkg.trust) with e20_4_hermetic_supply_chain_probe.ax.in.
2. Executes the bundled probe across:
   - `--interp`
   - `-O0 --verify-each`
   - `-O1 --verify-each`
   - `-O2 --verify-each`
   Verifying exact byte-for-byte identical output parity across all 4 execution tiers.
3. Differential verification (--interp vs native -O1 --verify-each) across all 5
   standalone .ax conformance fixtures in tests/conformance/p20/e20_4_hermetic_supply_chain/.
4. Verifies clean production binaries without leaked .axmeta, .axdb, .axmir, .axoracle, or .axlto metadata.
5. Emits E20-4-HERMETIC-SUPPLY-CHAIN-CONFORMANCE-OK.
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

PROBE_TEMPLATE = HERE / "e20_4_hermetic_supply_chain_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[sandbox_fs_and_escape] norm_ok=true traversal_rejected=true host_escape_rejected=true source_write_rejected=true dep_write_rejected=true out_write_ok=true violations=4\n"
    "probe[sandbox_env_net_clock_process] canonical_ok=true path_empty=true allowlist_ok=true env_denied=true net_denied=true process_denied=true clock_denied=true rng_denied=true\n"
    "probe[repro_remap_leak_and_verifier] remap_ok=true clean_audit=true leak_detected=true fp_eq=true identical_ok=true diff_detected=true diff_offset=5 section_ok=true\n"
    "probe[transitive_capability_audit] audit_ok=true escalation_rejected=true undeclared_rejected=true closure_ok=true\n"
    "probe[ed25519_sign_and_tamper_guard] keygen_ok=true sign_ok=true verify_ok=true merkle_tamper_denied=true sif_tamper_denied=true sig_tamper_denied=true\n"
    "probe[trust_store_and_key_rotation] active_signer_ok=true untrusted_rejected=true revoked_rejected=true rotation_ok=true\n"
    "probe[provenance_and_ddc_fixed_point] prov_emit_ok=true prov_verify_ok=true ddc_ok=true ddc_mismatch_denied=true\n"
    "probe[trust_cmd_cli_and_diagnostics] keygen_cli_ok=true sign_cli_ok=true verify_cli_ok=true audit_cli_ok=true prov_cli_ok=true diag_mapped=true\n"
    "E20-4-HERMETIC-SUPPLY-CHAIN-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "bit_for_bit_reproducibility_and_path_remapping",
        "bit_for_bit_reproducibility_and_path_remapping.ax",
        "bit_for_bit_reproducibility_and_path_remapping.stdout",
    ),
    (
        "hermetic_sandbox_isolation_and_boundary_defense",
        "hermetic_sandbox_isolation_and_boundary_defense.ax",
        "hermetic_sandbox_isolation_and_boundary_defense.stdout",
    ),
    (
        "dependency_capability_escalation_auditor",
        "dependency_capability_escalation_auditor.ax",
        "dependency_capability_escalation_auditor.stdout",
    ),
    (
        "ed25519_signature_trust_and_provenance",
        "ed25519_signature_trust_and_provenance.ax",
        "ed25519_signature_trust_and_provenance.stdout",
    ),
    (
        "trust_cmd_cli_and_diagnostic_contract",
        "trust_cmd_cli_and_diagnostic_contract.ax",
        "trust_cmd_cli_and_diagnostic_contract.stdout",
    ),
]

E20_4_BUNDLE_MODULES = [
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
    ("compiler.driver.trust_cmd", "compiler"),
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


def assemble_e20_4_probe(root: pathlib.Path, clean_root: pathlib.Path, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(E20_4_BUNDLE_MODULES, root=str(root))

    lockfile_path = clean_root / "std" / "pkg" / "lockfile" / "mod.ax"
    if not lockfile_path.is_file():
        lockfile_path = root / "std" / "pkg" / "lockfile" / "mod.ax"
    store_path = clean_root / "std" / "pkg" / "store" / "mod.ax"
    if not store_path.is_file():
        store_path = root / "std" / "pkg" / "store" / "mod.ax"
    archive_path = clean_root / "std" / "pkg" / "archive" / "mod.ax"
    if not archive_path.is_file():
        archive_path = root / "std" / "pkg" / "archive" / "mod.ax"
    trust_path = clean_root / "std" / "pkg" / "trust" / "mod.ax"
    if not trust_path.is_file():
        trust_path = root / "std" / "pkg" / "trust" / "mod.ax"

    std_pkg_text = ""
    for p, label in [
        (lockfile_path, "std/pkg/lockfile/mod.ax"),
        (store_path, "std/pkg/store/mod.ax"),
        (archive_path, "std/pkg/archive/mod.ax"),
        (trust_path, "std/pkg/trust/mod.ax"),
    ]:
        if p.is_file():
            txt = p.read_text(encoding="utf-8")
            txt = txt.replace("use std.core.host.", "use host_intrinsics.")
            std_pkg_text += f"\n// --- {label} ---\n" + txt + "\n"

    probe_body = template_path.read_text(encoding="utf-8")
    return (
        f"{prelude}\n"
        f"{modules_text}\n"
        f"{std_pkg_text}\n"
        f"// --- probe body: {template_path.name} ---\n\n"
        f"{probe_body}\n"
    )


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p20" / "e20_4_hermetic_supply_chain" / filename
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
        sys.stderr.write("usage: e20_4_hermetic_supply_chain_oracle.py <compiler> <build> <tmp> <root>\n")
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

    # 1. Assemble and execute master E20.4 probe bundle across --interp, -O0, -O1, and -O2
    probe_template = resolve_suite_file(root, "e20_4_hermetic_supply_chain_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e20_4_hermetic_supply_chain_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e20_4_probe(pathlib.Path(root), clean_root, probe_template), encoding="utf-8", newline="\n"
    )

    # 1a. Interpreter run
    iproc = run_cmd([axiomc, "run", "--interp", "--std-root", str(clean_std), str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e20_4 probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e20_4 probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # 1b. Compiled tiers: -O0, -O1, -O2
    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        bin_path = tmp_dir / f"e20_4_probe_{opt_label}{exe_ext}"
        bproc = run_cmd(
            [
                axiomc,
                "build",
                *opt_flags,
                "--stack-reserve=67108864",
                "--std-root",
                str(clean_std),
                str(probe_bundle),
                "-o",
                str(bin_path),
            ],
            root,
            timeout=240,
        )
        if bproc.returncode != 0:
            sys.stderr.write(
                f"e20_4 probe {opt_label} build failed ({bproc.returncode}):\n{bproc.stdout}\n{bproc.stderr}\n"
            )
            return 1
        rproc = run_cmd([str(bin_path)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e20_4 probe {opt_label} run failed ({rproc.returncode}):\n{rproc.stdout}\n{rproc.stderr}\n"
            )
            return 1
        norm_native = rproc.stdout.replace("\r\n", "\n")
        if norm_native != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e20_4 probe under {opt_label}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
            )
            return 1
        if not verify_production_exe_clean(bin_path):
            return 1

    # 2. Standalone Conformance Fixtures: differential verification (--interp vs native -O1 --verify-each)
    for name, ax_name, stdout_name in CONFORMANCE_FIXTURES:
        ax_file = resolve_suite_file(root, ax_name)
        stdout_file = resolve_suite_file(root, stdout_name)
        if not ax_file.is_file():
            sys.stderr.write(f"Missing fixture file: {ax_file}\n")
            return 1
        if not stdout_file.is_file():
            sys.stderr.write(f"Missing expected stdout file: {stdout_file}\n")
            return 1
        expected_out = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n")

        # 2a. Interp run
        f_iproc = run_cmd([axiomc, "run", "--interp", "--std-root", str(clean_std), str(ax_file)], root, timeout=120)
        if f_iproc.returncode != 0:
            sys.stderr.write(
                f"Fixture {name} failed under --interp ({f_iproc.returncode}):\n{f_iproc.stdout}\n{f_iproc.stderr}\n"
            )
            return 1
        act_interp = f_iproc.stdout.replace("\r\n", "\n")
        if act_interp != expected_out:
            sys.stderr.write(
                f"Fixture {name} stdout mismatch under --interp:\nexpected:\n{expected_out}\ngot:\n{act_interp}\n"
            )
            return 1

        # 2b. Native -O1 run
        f_bin = tmp_dir / f"{name}_O1{exe_ext}"
        f_bproc = run_cmd(
            [
                axiomc,
                "build",
                "-O1",
                "--verify-each",
                "--std-root",
                str(clean_std),
                str(ax_file),
                "-o",
                str(f_bin),
            ],
            root,
            timeout=120,
        )
        if f_bproc.returncode != 0:
            sys.stderr.write(
                f"Fixture {name} native -O1 build failed ({f_bproc.returncode}):\n{f_bproc.stdout}\n{f_bproc.stderr}\n"
            )
            return 1
        f_rproc = run_cmd([str(f_bin)], root, timeout=60)
        if f_rproc.returncode != 0:
            sys.stderr.write(
                f"Fixture {name} native -O1 run failed ({f_rproc.returncode}):\n{f_rproc.stdout}\n{f_rproc.stderr}\n"
            )
            return 1
        act_native = f_rproc.stdout.replace("\r\n", "\n")
        if act_native != expected_out:
            sys.stderr.write(
                f"Fixture {name} stdout mismatch under native -O1:\nexpected:\n{expected_out}\ngot:\n{act_native}\n"
            )
            return 1
        if not verify_production_exe_clean(f_bin):
            return 1

    sys.stdout.buffer.write(b"E20-4-HERMETIC-SUPPLY-CHAIN-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
