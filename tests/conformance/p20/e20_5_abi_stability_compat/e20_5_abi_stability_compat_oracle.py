#!/usr/bin/env python3
"""End-to-end E20.5 Conformance Oracle (`T869` / `SPEC-114` `AXS-ABI-001..053`,
`INV-SABI-001..003`, `REQ-ECO-8734`, `REQ-PKG-022`, `REQ-PKG-024`):
ABI Stability Tiers, Versioned Symbol Contracts, .axmeta Binary Compatibility,
and `axiomc abi-check` SemVer Conformance Suite.

Steps:
1. Bundles the live `compiler/abi/stability/mod.ax`, `compiler/abi/fingerprint/mod.ax`,
   `compiler/abi/compat_diff/mod.ax`, and `compiler/driver/abi_cmd/mod.ax` modules with
   `e20_5_abi_stability_compat_probe.ax.in`, executes the bundle in `--interp`, and compiles
   + executes it AT MOST ONCE at `-O0` (per <120s resource rule), verifying byte-for-byte
   identical output.
2. Differential verification (`--interp` vs native `-O1 --verify-each`) across
   all 4 standalone `.ax` conformance fixtures in `tests/conformance/p20/e20_5_abi_stability_compat/`.
3. Verifies clean production binaries without leaked `.axmeta`, `.axdb`, `.axmir`,
   `.axoracle`, or `.axlto` metadata sections or tokens.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e20_5_abi_stability_compat_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[tiers_and_opaque_evolution] tiers_ok=true opaque_ptr_ok=true opaque_layout_isolated=true opaque_by_val_rejected=true\n"
    "probe[boundary_firewall] scalars_ok=true closure_rejected=true unrepr_rejected=true generic_rejected=true missing_header_rejected=true\n"
    "probe[fingerprint_triple_and_symbols] api_fp_inv=true sem_fp_inline_track=true abi_fp_layout_shift=true mangling_ok=true pe_alias_ok=true coexistence_ok=true dup_rejected=true\n"
    "probe[abi_check_semver_matrix] struct_diff_ok=true sig_diff_ok=true policy_matrix_ok=true cli_json_ok=true\n"
    "E20-5-ABI-STABILITY-COMPAT-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "abi_tiers_and_opaque_handle_evolution",
        "abi_tiers_and_opaque_handle_evolution.ax",
        "abi_tiers_and_opaque_handle_evolution.stdout",
    ),
    (
        "boundary_type_rejection_firewall",
        "boundary_type_rejection_firewall.ax",
        "boundary_type_rejection_firewall.stdout",
    ),
    (
        "fingerprint_triple_and_symbol_versioning",
        "fingerprint_triple_and_symbol_versioning.ax",
        "fingerprint_triple_and_symbol_versioning.stdout",
    ),
    (
        "abi_check_semver_compliance_matrix",
        "abi_check_semver_compliance_matrix.ax",
        "abi_check_semver_compliance_matrix.stdout",
    ),
]

E20_5_BUNDLE_MODULES = [
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


def get_axiomc(compiler: str, build_dir: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    if os.path.isfile(compiler):
        return compiler
    cand = os.path.join(build_dir, f"axiomc{exe}")
    return cand


def run_cmd(
    cmd: list[str], cwd: str | pathlib.Path, timeout: int = 120
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


def assemble_e20_5_probe(clean_root: pathlib.Path, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(E20_5_BUNDLE_MODULES, root=str(REPO_ROOT))
    probe_body = template_path.read_text(encoding="utf-8")
    return (
        f"{prelude}\n"
        f"{modules_text}\n"
        f"// --- probe body: {template_path.name} ---\n\n"
        f"{probe_body}\n"
    )


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p20" / "e20_5_abi_stability_compat" / filename
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
        sys.stderr.write("usage: e20_5_abi_stability_compat_oracle.py <compiler> <build> <tmp> <root>\n")
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

    # 1. Bundle and execute live E20.5 ABI stability, fingerprint & diff driver probe
    probe_template = resolve_suite_file(root, "e20_5_abi_stability_compat_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e20_5_abi_stability_compat_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e20_5_probe(clean_root, probe_template), encoding="utf-8", newline="\n"
    )

    iproc = run_cmd([axiomc, "run", "--interp", "--std-root", str(clean_std), str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e20_5_abi_stability_compat_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e20_5_abi_stability_compat_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # Compile the compiler bundle AT MOST ONCE at `-O0` so the suite stays within resource limits
    probe_exe = tmp_dir / f"e20_5_abi_stability_compat_probe_O0{exe_ext}"
    bproc = run_cmd(
        [
            axiomc,
            "build",
            "--stack-reserve=67108864",
            "--std-root",
            str(clean_std),
            "-O0",
            "-o",
            str(probe_exe),
            str(probe_bundle),
        ],
        root,
        timeout=120,
    )
    if bproc.returncode != 0:
        sys.stderr.write(
            f"build e20_5_abi_stability_compat_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1

    rproc = run_cmd([str(probe_exe)], root, timeout=120)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e20_5_abi_stability_compat_probe -O0 failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_native = rproc.stdout.replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e20_5_abi_stability_compat_probe under -O0:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
        )
        return 1

    # 2. Differential verification of standalone `.ax` conformance fixtures (`--interp` vs `-O1 --verify-each`)
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

    sys.stdout.buffer.write(b"E20-5-ABI-STABILITY-COMPAT-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
