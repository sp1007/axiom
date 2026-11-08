#!/usr/bin/env python3
"""End-to-end E19.4 Conformance Oracle (`T815` / `SPEC-103` `AXS-DIAG-001..022`,
`AXS-AI-001..021`, `AXS-DIAG-050..053`; `INV-DIAG-009..011`; `REQ-TOOL-004`,
`REQ-TOOL-180..182`, `REQ-TOOL-185..187`, `REQ-TOOL-190`, `REQ-TOOL-298`):
Diagnostics UX 2.0 Causal Provenance, `DiagnosticFingerprint`, `PoisonTaint`
Cascade Suppression, Transactional `axiomc fix`, `axiomc explain` Encyclopedia,
`axiomc inspect layout`, `.axmeta` Container & `std.meta_effects` Contracts,
`AXCP v1` AI Semantic Fact Protocol, AI Patch Gate, and Production Binary Separation.

Steps:
1. Bundles the live `std/meta_effects/mod.ax`, `compiler/diag/ux2/mod.ax`,
   `compiler/diag/explain/mod.ax`, `compiler/driver/explain_cmd/mod.ax`,
   `compiler/ai_query/mod.ax`, and `compiler/driver/query_cmd/mod.ax` modules
   with `e19_4_diagnostics_ai_probe.ax.in`, executes the bundle in `--interp`,
   and compiles + executes it AT MOST ONCE at `-O0` (per <120s resource rule),
   verifying byte-for-byte identical output and zero backend codegen during
   diagnostics/fix/explain/query operations.
2. Runs differential verification (`--interp` vs native `-O1 --verify-each`) across
   all 4 standalone `.ax` conformance fixtures in `tests/conformance/p19/e19_4_diagnostics_ai/`
   and inspects the linked production `.exe` images to certify zero leaked
   `.axmeta`, `.axmi`, `.axlto`, `.axmir`, or `.axdb` sections or magic bytes.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e19_4_diagnostics_ai_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[ux2_causal_fp_taint] move_ok=true cap_ok=true conc_ok=true async_ok=true fp_stable=true render_ok=true vn_cols=8 emitted=4 suppressed=3 reinit_ok=true\n"
    "probe[fix_and_explain] safety_ok=true converged_ok=true rollback_ok=true codegen_invoked=false areas_ok=true entries=37 alias_ok=true unknown_exit2=true\n"
    "probe[layout_and_meta] domain_ok=true layout_human=true layout_json=true layout_wasm=true containers=8 effects=12 axmeta_ok=true\n"
    "probe[ai_queries_and_gates] queries_ok=true patch_reloc_rej=true patch_bypass_rej=true patch_uam_rej=true patch_clean_ok=true pe_clean_ok=true pe_dirty_rej=true\n"
    "E19-4-DIAGNOSTICS-AI-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "causal_provenance_fingerprints_and_cascade_suppression",
        "causal_provenance_fingerprints_and_cascade_suppression.ax",
        "causal_provenance_fingerprints_and_cascade_suppression.stdout",
    ),
    (
        "explain_registry_and_transactional_fix_convergence",
        "explain_registry_and_transactional_fix_convergence.ax",
        "explain_registry_and_transactional_fix_convergence.stdout",
    ),
    (
        "layout_inspector_container_contracts_and_std_effects",
        "layout_inspector_container_contracts_and_std_effects.ax",
        "layout_inspector_container_contracts_and_std_effects.stdout",
    ),
    (
        "ai_fact_protocol_patch_gate_and_binary_separation",
        "ai_fact_protocol_patch_gate_and_binary_separation.ax",
        "ai_fact_protocol_patch_gate_and_binary_separation.stdout",
    ),
]

E19_4_BUNDLE_MODULES = [
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
    ("compiler.diag.explain", "compiler"),
    ("compiler.driver.explain_cmd", "compiler"),
    ("compiler.ai_query", "compiler"),
    ("compiler.driver.query_cmd", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    return compiler


def run_cmd(cmd: list[str], cwd: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def assemble_e19_4_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    meta_effects_path = pathlib.Path(root) / "std" / "meta_effects" / "mod.ax"
    if not meta_effects_path.is_file():
        meta_effects_path = REPO_ROOT / "std" / "meta_effects" / "mod.ax"
    meta_effects_src = meta_effects_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(E19_4_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + meta_effects_src + "\n" + modules_src + "\n" + main_src


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p19" / "e19_4_diagnostics_ai" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_production_exe_clean(exe_path: pathlib.Path) -> bool:
    raw = exe_path.read_bytes()
    for forbidden in (b"AXMETA01", b"AXMI0001", b"AXLTO001", b"AXMIR001", b"AXDB0001", b".axmeta", b".axdb"):
        if forbidden in raw:
            sys.stderr.write(f"Production binary {exe_path} leaked metadata token {forbidden!r}\n")
            return False
    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e19_4_diagnostics_ai_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Bundle and execute live E19.4 diagnostics + explain + fix + AI query probe (`--interp` and single `-O0` build)
    probe_template = resolve_suite_file(root, "e19_4_diagnostics_ai_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e19_4_diagnostics_ai_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e19_4_probe(root, probe_template), encoding="utf-8", newline="\n"
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e19_4_diagnostics_ai_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_4_diagnostics_ai_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # Compile the compiler bundle AT MOST ONCE at `-O0` so the test completes in <120s
    probe_exe = tmp_dir / f"e19_4_diagnostics_ai_probe_O0{exe_ext}"
    bproc = run_cmd(
        [
            axiomc,
            "build",
            "--stack-reserve=67108864",
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
            f"build e19_4_diagnostics_ai_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1

    rproc = run_cmd([str(probe_exe)], root, timeout=120)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e19_4_diagnostics_ai_probe -O0 failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_native = rproc.stdout.replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_4_diagnostics_ai_probe under -O0:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
        )
        return 1

    # 2. Differential verification of standalone `.ax` conformance fixtures (`--interp` vs `-O1 --verify-each`)
    for stem, ax_name, stdout_name in CONFORMANCE_FIXTURES:
        src_path = resolve_suite_file(root, ax_name)
        out_path = resolve_suite_file(root, stdout_name)
        exp_out = out_path.read_text(encoding="utf-8").replace("\r\n", "\n")

        f_interp = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if f_interp.returncode != 0:
            sys.stderr.write(f"interp {stem} failed ({f_interp.returncode}):\n{f_interp.stderr}\n")
            return 1
        if f_interp.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp\n")
            return 1

        fx_exe = tmp_dir / f"{stem}_O1{exe_ext}"
        fb = run_cmd(
            [axiomc, "build", "-O1", "--verify-each", "-o", str(fx_exe), str(src_path)],
            root,
            timeout=120,
        )
        if fb.returncode != 0:
            sys.stderr.write(f"build {stem} -O1 --verify-each failed:\n{fb.stderr}\n")
            return 1
        fr = run_cmd([str(fx_exe)], root, timeout=120)
        if fr.returncode != 0:
            sys.stderr.write(f"run {stem} -O1 failed ({fr.returncode}):\n{fr.stderr}\n")
            return 1
        if fr.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under -O1\n")
            return 1
        if not verify_production_exe_clean(fx_exe):
            return 1

    sys.stdout.buffer.write(b"E19-4-DIAGNOSTICS-AI-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
