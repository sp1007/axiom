#!/usr/bin/env python3
"""
E15.5 — Loop & SLP Auto-Vectorization Conformance Oracle (`SPEC-74`, `T619`).

Verifies:
1. End-to-end bundled `compiler.opt.vectorize` + `compiler.opt.slp` + `compiler.lir.vec_lower` probe
   compiled and executed natively with `--verify-each`:
   - Loop auto-vectorization capability-disjoint (`VEC_ALIAS_CAP_DISJOINT`), SCEV anti-dependence
     (`VEC_ALIAS_SCEV_DISJOINT`), runtime alias guard (`VEC_ALIAS_RUNTIME_GUARD`), and conservative
     rejection on forward recurrence (`REASON_LOOP_CARRIED_DEP`) and unguarded `MayAlias` raw pointers
     (`REASON_UNKNOWN_ALIAS`) (`REQ-OPT-201..203`, `REQ-OPT-219`, `REQ-OPT-220`).
   - Reduction legality across wrapping/bitwise/proven-NSW integer reductions vs strict IEEE-754
     floating-point reduction rejection (`REASON_STRICT_FP_REDUCTION` under `FP_MODE_STRICT`, allowed
     under `FP_MODE_RELAXED`), broadcast/step/predicated `VSelect` if-conversion, SSE2/AVX/AVX2 lane
     width selection (`u8x16`, `i16x8`, `i32x4`, `i64x2`, `f64x2`, `f32x8`, `i32x8`), `-Os` code-size
     rejection (`REASON_SIZE_PROFILE_GROWTH`), scalar remainder epilogue (`EPILOGUE_SCALAR_REMAINDER`)
     vs exact-multiple omission (`EPILOGUE_NONE_EXACT_MULTIPLE`), and `PASS_LOOP_VEC` provenance
     (`REQ-OPT-204..212`, `REQ-OPT-219..221`).
   - SLP basic-block vectorization across 4-lane struct fields & 8-lane AVX2 arrays (`SLP_SEED_ADJACENT_STORES`),
     commuted operand swapping, post-unroll relative indexing, 4-lane horizontal dot-product reduction
     (`SLP_SEED_HORIZ_REDUCTION`), strict vs relaxed FP reduction, broadcast + external scalar lane
     extract cost model, unprofitable gather rejection (`REASON_COST_NOT_PROFITABLE`), `MayAlias` clobber
     rejection, checked overflow trap rejection (`REASON_CHECKED_OVERFLOW_TRAP`), volatile barrier
     rejection (`REASON_VOLATILE_BARRIER`), and `PASS_SLP_VEC` provenance (`REQ-OPT-213..215`, `REQ-OPT-219..221`).
   - OptIR vector to LIR `Vec128`/`Vec256` lowering (`vec_lower_legalize_type`, `vec_lower_select_mem_flags`,
     64-bit `LIR_INST_VMOVQ_64` promotion, 256->2x128 splitting on SSE2, integer division lane
     scalarization `LIR_INST_SCALAR_LANE_OP`, AVX2 `YMM` 32-byte frame alignment and `LIR_INST_VZEROUPPER`
     hygiene, and `vec_lower_verify_body`) (`REQ-OPT-216..218`).
   - Inspectable vectorization remarks and deterministic cost/lowering formatters (`loop_vec_print`,
     `loop_vec_cost_print`, `slp_vec_print`, `slp_vec_cost_print`, `vec_lower_print`) (`REQ-OPT-221`, `REQ-OPT-222`).
2. Differential execution equivalence across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` on
   positive and negative/trap conformance `.ax` programs (`loop_vec_all_widths_and_epilogues.ax`,
   `loop_vec_reductions_and_barriers.ax`, `slp_pack_trees_and_fallbacks.ax`, and 4 trap fixtures).
3. Deterministic `--emit=optir`, `--emit=memssa`, `--emit=mi`, and `--emit=mc` dumps across repeated runs
   across `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e15_5_conformance_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_LOOP_VEC_CAP_SCEV_AND_GUARDS=OK\n"
    "PROBE_LOOP_VEC_REDUCTIONS_AND_FP_LEGALITY=OK\n"
    "PROBE_LOOP_VEC_WIDTHS_EPILOGUES_AND_PROVENANCE=OK\n"
    "PROBE_SLP_PACK_TREES_REDUCTIONS_AND_BARRIERS=OK\n"
    "PROBE_SLP_HORIZ_AND_SAFETY_BARRIERS=OK\n"
    "PROBE_LIR_VEC_LOWER_128_256_MOVQ_AND_VZEROUPPER=OK\n"
    "PROBE_VECTOR_REMARKS_AND_EMIT_DETERMINISM=OK\n"
    "E15.5-PROBE: ALL-OK\n"
)


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc") and os.path.isfile(compiler):
        return compiler
    for d in (build_dir, os.path.join(root, "build"), os.path.join(root, "..", "build")):
        for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
            p = os.path.join(d, cand)
            if os.path.isfile(p):
                return p
    return compiler


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
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_5_autovec" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def get_std_root_args(axiomc: str, root: str, tmp_dir: pathlib.Path, probe_src: pathlib.Path) -> list[str]:
    """Return `--std-root <dir>` if `axiomc` needs a clean `std` snapshot free of in-progress concurrent edits."""
    check = run_cmd([axiomc, "run", "--interp", str(probe_src)], root, timeout=60)
    if "AX_CONC_INVALID_ATOMIC_TYPE" not in check.stderr and "AX_CONC_ATOMIC_MUT_VIEW" not in check.stderr:
        return []
    std_clean = tmp_dir / "std_clean"
    if not std_clean.exists():
        shutil.copytree(pathlib.Path(root) / "std", std_clean)
        prelude_p = std_clean / "core" / "prelude.ax"
        if prelude_p.is_file():
            txt = prelude_p.read_text(encoding="utf-8")
            marker = '@lang("poll")'
            idx = txt.find(marker)
            if idx != -1:
                # Trim trailing in-progress @lang("poll")/@lang("waker") additions when running pre-rebuild axiomc2
                cut = txt.rfind("@must_use", 0, idx)
                prelude_p.write_text(txt[: cut if cut != -1 else idx].rstrip() + "\n", encoding="utf-8", newline="\n")
    return ["--std-root", str(std_clean)]


def assemble_e15_5_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    for p in (selfhost_dir, selfhost_opt_dir):
        if p not in sys.path:
            sys.path.insert(0, p)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    e15_5_modules = list(got.CORE_MODULES) + [
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.loops", "compiler"),
        ("compiler.opt.bce", "compiler"),
        ("compiler.opt.vectorize", "compiler"),
        ("compiler.opt.slp", "compiler"),
        ("compiler.lir.vec_lower", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(e15_5_modules, root=root)
    main_src = probe_template_path.read_text(encoding="utf-8")
    return prelude + "\n" + modules_src + "\n" + main_src


def run_diff_fixture(
    axiomc: str,
    std_args: list[str],
    root: str,
    tmp_dir: pathlib.Path,
    stem: str,
    filename: str,
    expected_rc: int,
    expected_stdout: str,
    exe_ext: str,
) -> bool:
    src_path = resolve_fixture_path(root, filename)
    iproc = run_cmd([axiomc, "run", "--interp", *std_args, str(src_path)], root, timeout=120)
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
        bproc = run_cmd(
            [axiomc, "build", flag, "--verify-each", *std_args, "-o", str(exe_path), str(src_path)],
            root,
            timeout=180,
        )
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
        sys.stderr.write("usage: e15_5_conformance_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    first_pos_src = resolve_fixture_path(root, "loop_vec_all_widths_and_epilogues.ax")
    std_args = get_std_root_args(axiomc, root, tmp_dir, first_pos_src)

    # 1. Assemble and execute bundled E15.5 probe (`compiler.opt.vectorize` + `compiler.opt.slp` + `compiler.lir.vec_lower`)
    probe_template = resolve_fixture_path(root, "e15_5_conformance_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e15_5_conformance_probe_bundle.ax"
    probe_bundle.write_text(assemble_e15_5_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0",):
        probe_exe = tmp_dir / f"e15_5_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", *std_args, "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=600,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build e15_5_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        if not verify_pe_binary(probe_exe):
            sys.stderr.write(f"invalid PE binary produced for e15_5_probe {flag}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=300)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e15_5_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e15_5_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 --verify-each
    positive_stems = (
        "loop_vec_all_widths_and_epilogues",
        "loop_vec_reductions_and_barriers",
        "slp_pack_trees_and_fallbacks",
    )
    for stem in positive_stems:
        stdout_path = resolve_fixture_path(root, f"{stem}.stdout")
        exp_out = stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if not run_diff_fixture(axiomc, std_args, root, tmp_dir, stem, f"{stem}.ax", 0, exp_out, exe_ext):
            return 1

    # 3. Differential execution of negative/trap preservation fixtures across --interp, -O0, -O1, -O2 --verify-each
    trap_fixtures = [
        ("trap_loop_checked_add_overflow", 101, "100\n200\n"),
        ("trap_loop_epilogue_tail_oob", 101, "44\n"),
        ("trap_slp_lane_checked_overflow", 101, "30\n"),
        ("trap_slp_lane_bounds_oob", 101, "11\n22\n33\n"),
    ]
    for stem, exp_rc, exp_out in trap_fixtures:
        if not run_diff_fixture(axiomc, std_args, root, tmp_dir, stem, f"{stem}.ax", exp_rc, exp_out, exe_ext):
            return 1

    # 4. Deterministic --emit=optir, --emit=memssa, --emit=mi, and --emit=mc inspection across -O0, -O1, -O2 --verify-each
    inspect_src = resolve_fixture_path(root, "slp_pack_trees_and_fallbacks.ax")
    for flag in ("-O0", "-O1", "-O2"):
        for emit_kind in ("optir", "memssa", "mi", "mc"):
            d1 = run_cmd([axiomc, "inspect", f"--emit={emit_kind}", flag, "--verify-each", *std_args, str(inspect_src)], root)
            d2 = run_cmd([axiomc, "inspect", f"--emit={emit_kind}", flag, "--verify-each", *std_args, str(inspect_src)], root)
            if d1.returncode != 0 or d2.returncode != 0 or d1.stdout != d2.stdout or not d1.stdout.strip():
                sys.stderr.write(f"deterministic --emit={emit_kind} {flag} failed:\n{d1.stderr}\n")
                return 1

    sys.stdout.buffer.write(b"E15.5-AUTOVEC-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
