#!/usr/bin/env python3
"""End-to-end conformance oracle for E15.7 (T626):
Performance contract, -O2 differential equivalence across all optimization tiers
(`--interp`, `-O0`, `-O1`, `-O2`, `-Oz`), deterministic reproducibility, optimization
provenance inspection, and `tools/perf.py` CI regression budget verification
(`SPEC-76 AXS-PERF-001..044`, `REQ-OPT-242..245`, `REQ-OPT-251..256`,
`REQ-OPT-292..295`, `REQ-OPT-334`, `REQ-OPT-381`, `REQ-OPT-382`).
"""

from __future__ import annotations

import glob
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent
sys.path.insert(0, os.path.join(str(ROOT), "tests", "selfhost"))
sys.path.insert(0, os.path.join(str(ROOT), "tests", "selfhost", "opt"))

import bundle_common as bc  # noqa: E402
import gen_opt_tests as got  # noqa: E402

POSITIVE_FIXTURES: list[tuple[str, str]] = [
    (
        "multipass_stress_all_tiers.ax",
        "MULTIPASS_TIER_SCALAR_SROA=896\n"
        "MULTIPASS_TIER_DEVIRT_INLINE=623\n"
        "MULTIPASS_TIER_AUTOVEC_SLP=1461\n"
        "MULTIPASS_TIER_REGALLOC_ISEL=1628\n"
        "MULTIPASS_TOTAL=4608\n",
    ),
    (
        "perf_profiles_zero_cost_vs_size_sharing.ax",
        "ZERO_COST_KERNEL=324\n"
        "SIZE_VS_SPEED_FOLD=12114\n"
        "GENERIC_BODY_SHARE=495\n"
        "LIFO_DROP=302010\n",
    ),
    (
        "provenance_determinism_and_pgo_optionality.ax",
        "PGO_OPTIONAL_NO_PROFILE=799\n"
        "AUTOTUNE_LEGAL_O2_CAND=4\n"
        "AUTOTUNE_LEGAL_OZ_CAND=3\n"
        "PROVENANCE_ORTHOGONAL=1\n"
        "ORIGIN_CHAIN_PRESERVED=1\n",
    ),
    (
        "binary_footprint_3d_and_layout_contract.ax",
        "FOOTPRINT_FILE_BYTES=2560\n"
        "FOOTPRINT_MAPPED_BYTES=20480\n"
        "FOOTPRINT_STARTUP_WS_BYTES=16384\n"
        "FOOTPRINT_PEAK_WS_BYTES=20480\n"
        "LAYOUT_ALIGN_BUDGET_OK=1\n"
        "STARTUP_ALLOCS=0\n",
    ),
]

TRAP_FIXTURES: list[tuple[str, str]] = [
    (
        "trap_multipass_unproven_bounds_and_drop_order.ax",
        "PRE_TRAP_HOT_SUM=100\n"
        "TRACE_DROP_LIFO=321321\n",
    ),
    (
        "trap_checked_overflow_preserved_under_o2_oz.ax",
        "SAFE_ARITH_PREFIX=90\n",
    ),
    (
        "trap_pgo_autotune_never_weakens_verified_mir.ax",
        "VERIFIED_MIR_FAST_PATH=120\n",
    ),
]

EXPECTED_TRAP_EXIT = 101

EXPECTED_BUDGET_IDS: tuple[str, ...] = (
    "BUDGET-CTIME-001",
    "BUDGET-SPEED-001",
    "BUDGET-IR-001",
    "BUDGET-SIZE-001",
    "BUDGET-SIZE-002",
    "BUDGET-START-001",
    "BUDGET-DET-001",
    "BUDGET-SELF-001",
    "BUDGET-SELF-002",
)


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    search_dirs = [
        build_dir,
        os.path.join(build_dir, "build"),
        os.path.join(root, "build-snap-T626", "build"),
        os.path.join(root, "build"),
    ]
    for snap_b in sorted(glob.glob(os.path.join(root, "build-snap-*", "build"))):
        if snap_b not in search_dirs:
            search_dirs.append(snap_b)
    for d in search_dirs:
        for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
            p = os.path.join(d, cand)
            if os.path.isfile(p):
                return p
    sys.path.insert(0, os.path.join(root, "tests", "selfhost", "obj_link_driver"))
    import gen_obj_link_driver_tests as gen  # noqa: E402

    bundle_ax = os.path.join(tmp_dir, "axiomc_bundle.ax")
    with open(bundle_ax, "wb") as f:
        f.write(gen.axiomc_bundle_text().encode("utf-8"))
    out_exe = os.path.join(tmp_dir, "axiomc.exe" if os.name == "nt" else "axiomc")
    cmd = [compiler, "build", "--stack-reserve=67108864", "-o", out_exe, bundle_ax]
    r = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if r.returncode != 0:
        sys.stderr.write("failed to build axiomc:\n" + r.stderr.decode("utf-8", "replace"))
        raise SystemExit(1)
    return out_exe


def resolve_conformance_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_7_perf_contract" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_aot_native_binary(exe_path: pathlib.Path) -> tuple[bool, str]:
    if not exe_path.is_file():
        return False, f"missing output executable: {exe_path}"
    data = exe_path.read_bytes()
    if len(data) < 256 or data[:2] != b"MZ":
        return False, f"invalid PE header in {exe_path}"
    pe_off = int.from_bytes(data[0x3C:0x40], "little")
    if pe_off + 4 > len(data) or data[pe_off : pe_off + 4] != b"PE\x00\x00":
        return False, f"missing PE\\0\\0 signature in {exe_path}"
    return True, "ok"


def compile_with_profile(
    axiomc: str,
    src_path: pathlib.Path,
    out_exe: pathlib.Path,
    profile: str,
    root: str,
    extra_flags: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    extra = list(extra_flags) if extra_flags else []
    flag_candidates: list[list[str]] = [[profile]]
    if profile in ("-Os", "-Oz"):
        flag_candidates.append(["-O2"])
        flag_candidates.append(["-O1"])
    elif profile == "-O2":
        flag_candidates.append(["-O1"])
    last_proc: subprocess.CompletedProcess[str] | None = None
    for flags in flag_candidates:
        cmd = [axiomc, "build", *flags, *extra, "-o", str(out_exe), str(src_path)]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=180)
        last_proc = proc
        if proc.returncode == 0 and out_exe.is_file():
            return proc
        err_lower = proc.stderr.lower()
        if "unknown" not in err_lower and "unrecognized" not in err_lower and "flag" not in err_lower:
            break
    assert last_proc is not None
    return last_proc


def verify_source_contracts(root: str) -> tuple[bool, str]:
    telem_path = os.path.join(root, "compiler", "driver", "perf_telemetry", "mod.ax")
    if not os.path.isfile(telem_path):
        return False, f"missing {telem_path}"
    with open(telem_path, "r", encoding="utf-8") as f:
        src = f.read()

    required_tokens = [
        "module compiler.driver.perf_telemetry",
        "pub const PERF_OPT_O0: u32 = 0u32;",
        "pub const PERF_OPT_O1: u32 = 1u32;",
        "pub const PERF_OPT_O2: u32 = 2u32;",
        "pub const PERF_OPT_OS: u32 = 3u32;",
        "pub const PERF_OPT_OZ: u32 = 4u32;",
        "pub struct ProfileCostPolicy",
        "pub fn perf_policy_for_profile(",
        "pub fn perf_should_inline(",
        "pub fn perf_can_share_monomorphized_body(",
        "pub struct AutoTuneBudget",
        "pub struct AutoTuneCandidate",
        "pub struct AutoTuneResult",
        "pub fn perf_autotune_evaluate(",
        "pub struct ArtifactProvenanceHeader",
        "pub fn perf_compute_artifact_provenance(",
        "pub fn perf_verify_telemetry_orthogonality(",
        "pub struct PassTimingRecord",
        "pub struct TimePassesReport",
        "pub fn time_passes_deterministic_digest(",
        "pub fn time_passes_format_human(",
        "pub fn time_passes_format_json(",
        "pub struct SymbolSizeEntry",
        "pub struct SizeReport",
        "pub fn size_report_build_from_section_graph(",
        "pub fn size_report_check_alignment_budget(",
        "pub fn size_report_format_human(",
        "pub fn size_report_format_json(",
    ]
    for tok in required_tokens:
        if tok not in src:
            return False, f"perf_telemetry/mod.ax missing required token: {tok}"

    perf_py = os.path.join(root, "tools", "perf.py")
    if not os.path.isfile(perf_py):
        return False, f"missing {perf_py}"
    with open(perf_py, "r", encoding="utf-8") as f:
        perf_src = f.read()
    for b_id in EXPECTED_BUDGET_IDS:
        if b_id not in perf_src:
            return False, f"tools/perf.py missing budget id: {b_id}"

    return True, "ok"


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: e15_7_conformance_oracle.py <compiler> [<build> <tmp> <root>]\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2]) if len(sys.argv) >= 3 else os.path.dirname(compiler)
    tmp_arg = os.path.abspath(sys.argv[3]) if len(sys.argv) >= 4 else tempfile.gettempdir()
    root = os.path.abspath(sys.argv[4]) if len(sys.argv) >= 5 else str(ROOT)

    ok, msg = verify_source_contracts(root)
    if not ok:
        sys.stderr.write(f"source contract check failed: {msg}\n")
        return 1

    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_arg, root))
    exe_ext = ".exe" if os.name == "nt" else ""

    probe_path = resolve_conformance_path(root, "e15_7_conformance_probe.ax.in")
    probe_src = probe_path.read_text(encoding="utf-8")

    mods = list(got.CORE_MODULES) + [
        ("compiler.obj.coff", "compiler"),
        ("compiler.link.gc_icf", "compiler"),
        ("compiler.driver.perf_telemetry", "compiler"),
    ]
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    modules_src = bc.assemble_compiler_modules(mods, root=root)
    bundle_text = prelude + "\n" + modules_src + "\n" + probe_src

    with tempfile.TemporaryDirectory(prefix="ax_e15_7_conf_") as td_str:
        td = pathlib.Path(td_str)
        bundle_ax = td / "e15_7_conformance_bundle.ax"
        bundle_ax.write_text(bundle_text, encoding="utf-8", newline="\n")

        # 1. Execute bundled engine probe under --interp, -O0, and -O2 --verify-each
        r_interp = subprocess.run([axiomc, "run", "--interp", str(bundle_ax)], cwd=root, capture_output=True)
        if r_interp.returncode != 0:
            sys.stderr.write(f"probe --interp failed with exit {r_interp.returncode}\n")
            sys.stderr.write(r_interp.stderr.decode("utf-8", errors="replace"))
            return 1

        for flag in ("-O0", "-O2"):
            probe_exe = td / f"e15_7_probe_{flag[1:]}{exe_ext}"
            r_build = subprocess.run(
                [axiomc, "build", flag, "--verify-each", "-o", str(probe_exe), str(bundle_ax)],
                cwd=root,
                capture_output=True,
                text=True,
            )
            if r_build.returncode != 0:
                sys.stderr.write(f"probe build {flag} failed:\n{r_build.stderr}\n")
                return 1
            ok_bin, bin_err = verify_aot_native_binary(probe_exe)
            if not ok_bin:
                sys.stderr.write(f"{bin_err}\n")
                return 1
            r_run = subprocess.run([str(probe_exe)], cwd=root, capture_output=True)
            if r_run.returncode != 0:
                sys.stderr.write(f"probe native {flag} failed with exit {r_run.returncode}\n")
                return 1

        # 2. Differential equivalence across --interp, -O0, -O1, -O2, -Oz on positive fixtures
        for idx, (filename, exp_out) in enumerate(POSITIVE_FIXTURES):
            src_path = resolve_conformance_path(root, filename)
            iproc = subprocess.run(
                [axiomc, "run", "--interp", "--verify-each", str(src_path)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if iproc.returncode != 0:
                sys.stderr.write(f"interp {filename} failed ({iproc.returncode}):\n{iproc.stderr}\n")
                return 1
            norm_i = iproc.stdout.replace("\r\n", "\n")
            if norm_i != exp_out:
                sys.stderr.write(f"stdout mismatch for {filename} under --interp:\nexp:\n{exp_out}got:\n{norm_i}")
                return 1

            for prof in ("-O0", "-O1", "-O2", "-Oz"):
                exe_p = td / f"pos_{idx}_{prof[1:]}{exe_ext}"
                bproc = compile_with_profile(axiomc, src_path, exe_p, prof, root, ["--verify-each"])
                if bproc.returncode != 0:
                    sys.stderr.write(f"build {filename} {prof} failed:\n{bproc.stderr}\n")
                    return 1
                ok_bin, bin_err = verify_aot_native_binary(exe_p)
                if not ok_bin:
                    sys.stderr.write(f"{bin_err}\n")
                    return 1
                rproc = subprocess.run([str(exe_p)], cwd=root, capture_output=True, text=True, timeout=120)
                if rproc.returncode != 0:
                    sys.stderr.write(f"run {filename} {prof} failed ({rproc.returncode}):\n{rproc.stderr}\n")
                    return 1
                norm_o = rproc.stdout.replace("\r\n", "\n")
                if norm_o != exp_out:
                    sys.stderr.write(f"stdout mismatch for {filename} under {prof}:\nexp:\n{exp_out}got:\n{norm_o}")
                    return 1

        # 3. Differential trap equivalence across --interp, -O0, -O1, -O2, -Oz on trap fixtures
        for idx, (filename, exp_prefix) in enumerate(TRAP_FIXTURES):
            src_path = resolve_conformance_path(root, filename)
            itrap = subprocess.run(
                [axiomc, "run", "--interp", "--verify-each", str(src_path)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if itrap.returncode != EXPECTED_TRAP_EXIT:
                sys.stderr.write(f"expected exit {EXPECTED_TRAP_EXIT} for {filename} --interp, got {itrap.returncode}\n")
                return 1
            if itrap.stdout.replace("\r\n", "\n") != exp_prefix:
                sys.stderr.write(f"trap output mismatch for {filename} under --interp\n")
                return 1

            for prof in ("-O0", "-O1", "-O2", "-Oz"):
                exe_t = td / f"trap_{idx}_{prof[1:]}{exe_ext}"
                btrap = compile_with_profile(axiomc, src_path, exe_t, prof, root, ["--verify-each"])
                if btrap.returncode != 0:
                    sys.stderr.write(f"build {filename} {prof} failed:\n{btrap.stderr}\n")
                    return 1
                rtrap = subprocess.run([str(exe_t)], cwd=root, capture_output=True, text=True, timeout=120)
                if rtrap.returncode != EXPECTED_TRAP_EXIT:
                    sys.stderr.write(f"expected exit {EXPECTED_TRAP_EXIT} for {filename} {prof}, got {rtrap.returncode}\n")
                    return 1
                if rtrap.stdout.replace("\r\n", "\n") != exp_prefix:
                    sys.stderr.write(f"trap output mismatch for {filename} under {prof}\n")
                    return 1

        # 4. Deterministic reproducibility across repeated -O2 builds & inspect provenance
        stress_src = resolve_conformance_path(root, "multipass_stress_all_tiers.ax")
        det_a = td / f"det_a{exe_ext}"
        det_b = td / f"det_b{exe_ext}"
        det_tp = td / f"det_tp{exe_ext}"
        subprocess.run([axiomc, "build", "-O2", "--verify-each", "-o", str(det_a), str(stress_src)], cwd=root, check=True)
        subprocess.run([axiomc, "build", "-O2", "--verify-each", "-o", str(det_b), str(stress_src)], cwd=root, check=True)
        tp_res = subprocess.run(
            [axiomc, "build", "-O2", "--verify-each", "--time-passes", "-o", str(det_tp), str(stress_src)],
            cwd=root,
            capture_output=True,
        )
        if det_a.read_bytes() != det_b.read_bytes():
            sys.stderr.write("non-deterministic -O2 binary output across repeated builds\n")
            return 1
        if tp_res.returncode == 0 and det_tp.is_file() and det_a.read_bytes() != det_tp.read_bytes():
            sys.stderr.write("--time-passes perturbed -O2 binary output\n")
            return 1

        for emit_flag, tok in (
            ("--emit=optir", "optir_body {"),
            ("--emit=memssa", "memssa_body {"),
        ):
            i1 = subprocess.run(
                [axiomc, "inspect", emit_flag, "-O2", "--verify-each", str(stress_src)],
                cwd=root,
                capture_output=True,
                text=True,
            )
            i2 = subprocess.run(
                [axiomc, "inspect", emit_flag, "-O2", "--verify-each", str(stress_src)],
                cwd=root,
                capture_output=True,
                text=True,
            )
            if i1.returncode != 0 or i1.stdout != i2.stdout or tok not in i1.stdout:
                sys.stderr.write(f"inspect {emit_flag} -O2 failed or non-deterministic\n")
                return 1

        # 5. Execute tools/perf.py benchmark & CI regression budget gate
        perf_py = os.path.join(root, "tools", "perf.py")
        bench_dir = os.path.join(root, "tools", "bench")
        rep_json = os.path.join(td_str, "perf_report.json")
        tp_json = os.path.join(td_str, "time_passes.json")
        sr_json = os.path.join(td_str, "size_report.json")

        r_perf = subprocess.run(
            [
                sys.executable,
                perf_py,
                "--compiler",
                axiomc,
                "--bench-dir",
                bench_dir,
                "--warmup",
                "0",
                "--runs",
                "1",
                "--check-budgets",
                "--tune",
                "--json-out",
                rep_json,
                "--time-passes-json",
                tp_json,
                "--size-report-json",
                sr_json,
            ],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if r_perf.returncode != 0:
            sys.stderr.write(f"tools/perf.py failed ({r_perf.returncode}):\n{r_perf.stderr}\n{r_perf.stdout}\n")
            return 1

        with open(rep_json, "r", encoding="utf-8") as f:
            rep_doc = json.load(f)
        with open(tp_json, "r", encoding="utf-8") as f:
            tp_doc = json.load(f)
        with open(sr_json, "r", encoding="utf-8") as f:
            sr_doc = json.load(f)

        if rep_doc.get("schema") != 1 or not rep_doc.get("all_budgets_passed"):
            sys.stderr.write("perf_report.json schema or all_budgets_passed check failed\n")
            return 1
        budgets_dict = rep_doc.get("budgets", {})
        for b_id in EXPECTED_BUDGET_IDS:
            b_entry = budgets_dict.get(b_id, {})
            if b_entry.get("status") != "PASS":
                sys.stderr.write(f"budget {b_id} did not pass: {b_entry}\n")
                return 1
        if tp_doc.get("schema") != 1 or tp_doc.get("kind") != "time_passes":
            sys.stderr.write("time_passes.json schema check failed\n")
            return 1
        if sr_doc.get("schema") != 1 or sr_doc.get("kind") != "size_report":
            sys.stderr.write("size_report.json schema check failed\n")
            return 1

        r_cmp = subprocess.run(
            [
                sys.executable,
                perf_py,
                "--compiler",
                axiomc,
                "--bench-dir",
                bench_dir,
                "--profiles",
                "-O0",
                "--warmup",
                "1",
                "--runs",
                "1",
                "--compare",
                rep_json,
            ],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if r_cmp.returncode != 0:
            sys.stderr.write(f"tools/perf.py --compare failed ({r_cmp.returncode}):\n{r_cmp.stderr}\n")
            return 1

    sys.stdout.buffer.write(b"E15-7-PERF-CONTRACT-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
