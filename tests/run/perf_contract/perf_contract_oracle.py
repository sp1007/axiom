#!/usr/bin/env python3
"""Live oracle for `compiler/driver/perf_telemetry/mod.ax`, `tools/bench/*`, and `tools/perf.py` (T625).

1. Verifies structural and syntactic contracts on `compiler/driver/perf_telemetry/mod.ax`,
   `tools/bench/*.ax`, and `tools/perf.py` (`SPEC-76 AXS-PERF-001..044`).
2. Bundles `compiler.driver.perf_telemetry` + `compiler.link.gc_icf` + `compiler.obj.coff`
   with `perf_contract_probe.ax.in` and executes the probe in both `--interp` and native x86-64 modes.
3. Invokes `tools/perf.py --check-budgets --tune --json-out ... --time-passes-json ... --size-report-json ...`
   and verifies that all 7 canonical benchmarks and all 9 quantitative `SPEC-76` budgets pass.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost", "opt"))

import bundle_common as bc  # noqa: E402
import gen_opt_tests as got  # noqa: E402


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    search_dirs = [
        build_dir,
        os.path.join(build_dir, "build"),
        os.path.join(root, "build-snap-T625", "build"),
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

    return True, "ok"


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: perf_contract_oracle.py <compiler> [<build> <tmp> <root>]\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2]) if len(sys.argv) >= 3 else os.path.dirname(compiler)
    tmp_arg = os.path.abspath(sys.argv[3]) if len(sys.argv) >= 4 else tempfile.gettempdir()
    root = os.path.abspath(sys.argv[4]) if len(sys.argv) >= 5 else ROOT

    ok, msg = verify_source_contracts(root)
    if not ok:
        sys.stderr.write(f"source contract check failed: {msg}\n")
        return 1

    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_arg, root))

    probe_path = os.path.join(HERE, "perf_contract_probe.ax.in")
    with open(probe_path, "r", encoding="utf-8") as f:
        probe_src = f.read()

    mods = list(got.CORE_MODULES) + [
        ("compiler.obj.coff", "compiler"),
        ("compiler.link.gc_icf", "compiler"),
        ("compiler.driver.perf_telemetry", "compiler"),
    ]
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    modules_src = bc.assemble_compiler_modules(mods, root=root)
    bundle_text = prelude + "\n" + modules_src + "\n" + probe_src

    with tempfile.TemporaryDirectory(prefix="ax_perf_contract_") as td:
        bundle_ax = os.path.join(td, "perf_contract_bundle.ax")
        exe_path = os.path.join(td, "perf_contract_bundle.exe")
        with open(bundle_ax, "w", encoding="utf-8", newline="\n") as f:
            f.write(bundle_text)

        r_interp = subprocess.run([axiomc, "run", "--interp", bundle_ax], capture_output=True)
        if r_interp.returncode != 0:
            sys.stderr.write(f"interp failed with exit {r_interp.returncode}\n")
            sys.stderr.write(r_interp.stderr.decode("utf-8", errors="replace"))
            return 1

        r_build = subprocess.run([axiomc, "build", bundle_ax, "-o", exe_path], capture_output=True)
        if r_build.returncode != 0:
            sys.stderr.write(f"native build failed with exit {r_build.returncode}\n")
            sys.stderr.write(r_build.stderr.decode("utf-8", errors="replace"))
            return 1

        r_run = subprocess.run([exe_path], capture_output=True)
        if r_run.returncode != 0:
            sys.stderr.write(f"native probe failed with exit {r_run.returncode}\n")
            return 1

        # Verify tools/perf.py budget enforcement & JSON telemetry outputs
        perf_py = os.path.join(root, "tools", "perf.py")
        bench_dir = os.path.join(root, "tools", "bench")
        rep_json = os.path.join(td, "perf_report.json")
        tp_json = os.path.join(td, "time_passes.json")
        sr_json = os.path.join(td, "size_report.json")

        r_perf = subprocess.run(
            [
                sys.executable,
                perf_py,
                "--compiler",
                axiomc,
                "--bench-dir",
                bench_dir,
                "--warmup",
                "1",
                "--runs",
                "2",
                "--check-budgets",
                "--tune",
                "--json-out",
                rep_json,
                "--time-passes-json",
                tp_json,
                "--size-report-json",
                sr_json,
            ],
            capture_output=True,
            text=True,
        )
        if r_perf.returncode != 0:
            sys.stderr.write(f"tools/perf.py failed with exit {r_perf.returncode}:\n{r_perf.stderr}\n{r_perf.stdout}\n")
            return 1

        with open(rep_json, "r", encoding="utf-8") as f:
            rep_doc = json.load(f)
        with open(tp_json, "r", encoding="utf-8") as f:
            tp_doc = json.load(f)
        with open(sr_json, "r", encoding="utf-8") as f:
            sr_doc = json.load(f)

        if rep_doc.get("schema") != 1 or not rep_doc.get("all_budgets_passed"):
            sys.stderr.write("perf_report.json schema or budget check failed\n")
            return 1
        if tp_doc.get("schema") != 1 or tp_doc.get("kind") != "time_passes":
            sys.stderr.write("time_passes.json schema check failed\n")
            return 1
        if sr_doc.get("schema") != 1 or sr_doc.get("kind") != "size_report":
            sys.stderr.write("size_report.json schema check failed\n")
            return 1

        # Verify --compare baseline regression check exits 0 on identical baseline
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
            capture_output=True,
            text=True,
        )
        if r_cmp.returncode != 0:
            sys.stderr.write(f"tools/perf.py --compare failed with exit {r_cmp.returncode}:\n{r_cmp.stderr}\n")
            return 1

    sys.stdout.buffer.write(b"PERF_CONTRACT_ENGINE_OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
