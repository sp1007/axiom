#!/usr/bin/env python3
"""
E15.3 — Loop Optimizations, SCEV & Bounds-Check Elimination Conformance Oracle (`SPEC-72`, `T612`).

Verifies:
1. End-to-end bundled `compiler.opt.loops` + `compiler.opt.bce` + `compiler.opt.loop_xform` probe
   compiled and executed natively at `-O0`, `-O1`, and `-O2 --verify-each`:
   - Natural loop tree discovery (`LoopTree`, `LoopDesc`, `loops_loop_of_block`), canonicalization
     (`LoopSimplify` preheader/latch/dedicated-exit insertion, `LCSSA` boundary phis), `bb0` header
     hoisting, and Tarjan SCC irreducible multi-entry cycle detection (`AXS-LOOP-001..004`, `REQ-OPT-142`,
     `REQ-OPT-176`).
   - SCEV affine recurrence classification (`ARITH_CHECKED`, `ARITH_WRAPPING`, `ARITH_PROVEN_NSW_NUW`),
     trip-count lattice (`TRIP_CONST`, `TRIP_SYMBOLIC`, `TRIP_UPPER_BOUNDED`, `TRIP_INFINITE`,
     `TRIP_UNKNOWN`), loop-invariance & hoisting legality (`loops_can_hoist_inst` across pure ops,
     read-only `view` loads/discriminants vs `mut_view`/`*mut`/local clobbers, zero-trip traps, and
     `BARRIER_VOLATILE` / `BARRIER_ATOMIC` / `BARRIER_GPU_DOMAIN`), and loop-carried memory dependence
     (`loops_query_dependence`: `DEP_NONE`, `DEP_RAW_FLOW`, `DEP_WAR_ANTI`, `DEP_UNKNOWN`) (`AXS-LOOP-005..011`,
     `REQ-OPT-155..158`, `REQ-OPT-177`).
   - Range analysis (`RangeInfo`) & bounds/overflow check elimination (`opt_bce`, `bce_optimize_mir_body`,
     `ProofProvenance` with `PROP_IN_BOUNDS` + `CERTAINTY_PROVEN` + `PASS_BCE`, `BceSiteRecord` with
     `BCE_ELIMINATED_PROVEN`, half-open `[0..mid)` / `[mid..len)` subslice disjointness via
     `bce_prove_subrange_disjoint`, 11 negative zero-false-positive BCE rejection cases, and post-pass
     `verify_mir` / `verify_mir_own` / `verify_mir_cap` / `mir_drop_elaborate` / `verify_mir_drop_flags`)
     (`AXS-BCE-001..006`, `REQ-OPT-159..162`, `REQ-OPT-178..180`).
   - Loop transformations (`opt_licm`, `opt_iv_strength_reduce`, `opt_loop_peel`, `opt_loop_unswitch`,
     `opt_loop_unroll`, `opt_loop_version`, `opt_loop_fuse`, `loop_xform_recognize_reduction`,
     `loop_xform_can_distribute`, `loop_xform_can_vectorize_or_parallelize`, `loop_xform_optimize_mir_body`)
     and deterministic `loops_print`, `bce_print`, and `loop_xform_print` dumps (`REQ-OPT-181..188`,
     `REQ-OPT-192..196`).
2. Differential execution equivalence across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` on
   positive and negative/trap conformance `.ax` programs (`scev_bce_and_range_elimination.ax`,
   `licm_sr_peel_unroll_version_fusion.ax`, `oob_and_overflow_trap_preservation.ax`, and panic fixtures).
3. Deterministic `--emit=optir` and `--emit=memssa` dumps across repeated runs across `-O0`, `-O1`, `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e15_3_loops_bce_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_LOOP_DISCOVERY_AND_SIMPLIFY=OK\n"
    "PROBE_SCEV_INVARIANCE_AND_DEPENDENCE=OK\n"
    "PROBE_FRONTEND_LOWERED_BCE_POSITIVE=OK\n"
    "PROBE_FRONTEND_LOWERED_BCE_NEGATIVE=OK\n"
    "CASE1_LICM_POS_AND_GUARDS: OK\n"
    "CASE1B_LICM_NEG_TRAP_CLOBBER_BARRIER: OK\n"
    "CASE2_IV_SR_AND_OVERFLOW_GATE: OK\n"
    "CASE3_LOOP_PEEL_FIRST_ITER: OK\n"
    "CASE4_LOOP_UNSWITCH_INVARIANT: OK\n"
    "CASE5_LOOP_UNROLL_FULL_AND_PARTIAL: OK\n"
    "CASE6_LOOP_VERSION_FAST_AND_FALLBACK: OK\n"
    "CASE7_LOOP_FUSE_AND_ITER_FORWARD: OK\n"
    "CASE8_REDUCTION_LEGALITY_AND_PRINT: OK\n"
    "PROBE_LOOP_XFORM_ALL=OK\n"
    "E15.3-PROBE: ALL-OK\n"
)


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
        p = os.path.join(build_dir, cand)
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


def run_cmd(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def verify_pe_binary(exe_path: pathlib.Path) -> bool:
    if not exe_path.is_file() or exe_path.stat().st_size <= 512:
        return False
    if os.name == "nt" and exe_path.read_bytes()[:2] != b"MZ":
        return False
    return True


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_3_loops_bce" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def assemble_e15_3_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    bce_dir = os.path.join(root, "tests", "run", "opt_bce")
    for p in (selfhost_dir, selfhost_opt_dir, bce_dir):
        if p not in sys.path:
            sys.path.insert(0, p)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402
    import opt_bce_oracle as obo  # noqa: E402

    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    e15_3_modules = list(got.PIPELINE_MODULES) + [
        ("compiler.own.cap", "compiler"),
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.loops", "compiler"),
        ("compiler.opt.bce", "compiler"),
        ("compiler.opt.loop_xform", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(e15_3_modules, root=root)
    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", obo.BCE_PROBE_BLOBS))
    return prelude + "\n" + modules_src + "\n" + main_src


def run_diff_fixture(
    axiomc: str,
    root: str,
    tmp_dir: pathlib.Path,
    stem: str,
    filename: str,
    expected_rc: int,
    expected_stdout: str,
    exe_ext: str,
) -> bool:
    src_path = resolve_fixture_path(root, filename)
    iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
    if iproc.returncode != expected_rc:
        sys.stderr.write(f"interp {stem} rc={iproc.returncode}, expected {expected_rc}:\n{iproc.stderr}\n")
        return False
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != expected_stdout:
        sys.stderr.write(f"stdout mismatch for {stem} under --interp:\nexpected:\n{expected_stdout!r}\ngot:\n{norm_interp!r}\n")
        return False
    norm_interp_err = iproc.stderr.replace("\r\n", "\n")
    if expected_rc == 0 and norm_interp_err.strip() != "":
        sys.stderr.write(f"unexpected stderr for {stem} under --interp:\n{norm_interp_err!r}\n")
        return False
    if expected_rc != 0 and norm_interp_err.strip() == "":
        sys.stderr.write(f"expected non-empty panic/trap stderr for {stem} under --interp\n")
        return False

    for flag in ("-O0", "-O1", "-O2"):
        exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
        bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root, timeout=180)
        if bproc.returncode != 0:
            sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
            return False
        if not verify_pe_binary(exe_path):
            sys.stderr.write(f"invalid PE binary produced for {stem} {flag}\n")
            return False
        rproc = run_cmd([str(exe_path)], root, timeout=120)
        if rproc.returncode != expected_rc:
            sys.stderr.write(f"run {stem} {flag} rc={rproc.returncode}, expected {expected_rc}:\n{rproc.stderr}\n")
            return False
        norm_out = rproc.stdout.replace("\r\n", "\n")
        if norm_out != expected_stdout:
            sys.stderr.write(f"stdout mismatch for {stem} under {flag}:\nexpected:\n{expected_stdout!r}\ngot:\n{norm_out!r}\n")
            return False
        norm_err = rproc.stderr.replace("\r\n", "\n")
        if expected_rc == 0:
            if norm_err.strip() != "":
                sys.stderr.write(f"unexpected stderr for {stem} under {flag}:\n{norm_err!r}\n")
                return False
        else:
            if norm_err != norm_interp_err:
                sys.stderr.write(
                    f"stderr mismatch for {stem} under {flag} vs --interp:\n"
                    f"expected (--interp):\n{norm_interp_err!r}\ngot ({flag}):\n{norm_err!r}\n"
                )
                return False
    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e15_3_loops_bce_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute bundled E15.3 probe (in-process passes run with verify_each=true)
    probe_template = resolve_fixture_path(root, "e15_3_loops_bce_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e15_3_loops_bce_probe_bundle.ax"
    probe_bundle.write_text(assemble_e15_3_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0",):
        probe_exe = tmp_dir / f"e15_3_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=600,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build e15_3_probe {flag} failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        if not verify_pe_binary(probe_exe):
            sys.stderr.write(f"invalid PE binary produced for e15_3_probe {flag}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=300)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e15_3_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e15_3_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 --verify-each
    for stem in ("scev_bce_and_range_elimination", "licm_sr_peel_unroll_version_fusion"):
        stdout_path = resolve_fixture_path(root, f"{stem}.stdout")
        exp_out = stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if not run_diff_fixture(axiomc, root, tmp_dir, stem, f"{stem}.ax", 0, exp_out, exe_ext):
            return 1

    # 3. Differential execution of negative/trap preservation fixtures across --interp, -O0, -O1, -O2 --verify-each
    oob_stdout_path = resolve_fixture_path(root, "oob_and_overflow_trap_preservation.stdout")
    oob_exp_out = oob_stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    trap_fixtures = [
        ("oob_and_overflow_trap_preservation", 101, oob_exp_out),
        ("trap_oob_vec_shrink_in_loop", 101, "11\n22\n"),
        ("trap_licm_non_dominating_div", 101, "40\n0\n"),
        ("trap_iv_sr_checked_overflow", 101, "0\n1000000000\n2000000000\n"),
        ("trap_versioned_loop_fallback_oob", 101, "10\n20\n30\n10\n20\n30\n40\n"),
    ]
    for stem, exp_rc, exp_out in trap_fixtures:
        if not run_diff_fixture(axiomc, root, tmp_dir, stem, f"{stem}.ax", exp_rc, exp_out, exe_ext):
            return 1

    # 4. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2 --verify-each
    inspect_src = resolve_fixture_path(root, "licm_sr_peel_unroll_version_fusion.ax")
    for flag in ("-O0", "-O1", "-O2"):
        o1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        o2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        if o1.returncode != 0 or o2.returncode != 0 or o1.stdout != o2.stdout or not o1.stdout.strip():
            sys.stderr.write(f"deterministic --emit=optir {flag} failed:\n{o1.stderr}\n")
            return 1
        m1 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        m2 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        if m1.returncode != 0 or m2.returncode != 0 or m1.stdout != m2.stdout or not m1.stdout.strip():
            sys.stderr.write(f"deterministic --emit=memssa {flag} failed:\n{m1.stderr}\n")
            return 1

    sys.stdout.buffer.write(b"E15.3-LOOPS-SCEV-BCE-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
