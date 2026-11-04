#!/usr/bin/env python3
"""End-to-end conformance oracle for E15.8 (T629):
Register allocation, target-specific instruction selection, non-speculative if-conversion,
and post-RA machine peephole optimization conformance across --interp, -O0, -O1, and
-O2 --verify-each (REQ-OPT-371, REQ-OPT-372, SPEC-77).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e15_8_conformance_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "E15_8_STAGE_REGALLOC_PRESSURE=OK\n"
    "E15_8_STAGE_ISEL_IFCONV=OK\n"
    "E15_8_STAGE_POSTRA_PEEPHOLE_IR=OK\n"
    "E15_8_STAGE_VERIFIER_GATE=OK\n"
    "E15_8_PROBE_ALL=OK\n"
)

SEED_MODS: list[str] = [
    "compiler.kernel.id",
    "compiler.kernel.hash",
    "compiler.kernel.arena",
    "compiler.kernel.interner",
    "compiler.source.span",
    "compiler.diag.format",
    "compiler.hir.hir",
    "compiler.types.types",
    "compiler.types.layout",
    "compiler.lir.lir",
    "compiler.abi.win64",
    "compiler.abi",
    "compiler.obj.coff",
    "compiler.target.x64.encode",
    "compiler.target.x64.isel",
    "compiler.target.x64.frame",
    "compiler.target.x64",
    "compiler.backend.peephole.peephole",
    "compiler.backend.peephole",
]

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "regalloc_extreme_pressure_spills",
        "regalloc_extreme_pressure_spills.ax",
        (
            "RA_PRESSURE_36=9644\n"
            "RA_SPILL_COLOR=5536\n"
            "RA_CALLEE_SAVED=2551\n"
            "RA_TOTAL=17731\n"
        ),
    ),
    (
        "fixed_reg_clobbers_div_shift_abi",
        "fixed_reg_clobbers_div_shift_abi.ax",
        (
            "FIXED_DIV_SHIFT=645\n"
            "PARALLEL_COPY=2460\n"
            "SUBWORD_DIV=7336\n"
            "FIXED_TOTAL=10441\n"
        ),
    ),
    (
        "isel_lea_const_divmul_casts",
        "isel_lea_const_divmul_casts.ax",
        (
            "ISEL_LEA_MUL=1229\n"
            "ISEL_CONST_DIV=6823\n"
            "ISEL_CASTS=65886\n"
            "ISEL_TOTAL=73938\n"
        ),
    ),
    (
        "if_conv_cmov_setcc_nospeculate",
        "if_conv_cmov_setcc_nospeculate.ax",
        (
            "IFCONV_CMOV_SETCC=32821\n"
            "IFCONV_XOR1_BOOL=396\n"
            "IFCONV_NOSPEC=2045\n"
            "IFCONV_TOTAL=35262\n"
        ),
    ),
    (
        "peephole_eflags_barriers_utf8_io",
        "peephole_eflags_barriers_utf8_io.ax",
        (
            "GREETING=Xin chào thế giới\n"
            "DROP=22\n"
            "DROP=21\n"
            "PEEPHOLE_EFLAGS=255\n"
            "PEEPHOLE_BARRIERS=468\n"
            "PEEPHOLE_TOTAL=723\n"
            "DROP=10\n"
        ),
    ),
]

TRAP_FIXTURES: list[str] = [
    "trap_checked_add_lea_exclusion_i64.ax",
    "trap_checked_sub_underflow_u64.ax",
    "trap_checked_mul_overflow_i64.ax",
    "trap_signed_min_div_neg1_i64.ax",
    "trap_div_by_zero_guarded_arm_taken.ax",
]
EXPECTED_TRAP_EXIT = 101

STRAIGHT_LINE_MC_SRC = (
    "module main\n"
    "@intrinsic fn wrapping_add_i64(a: i64, b: i64) -> i64 { 0i64 }\n"
    "@intrinsic fn wrapping_mul_i64(a: i64, b: i64) -> i64 { 0i64 }\n"
    "pub fn main() -> i32 {\n"
    "    let a: i64 = 14;\n"
    "    let b: i64 = wrapping_add_i64(a, wrapping_mul_i64(a, 4));\n"
    "    (b - 70) as i32\n"
    "}\n"
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
        sys.exit(1)
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


def verify_aot_native_binary(exe_path: pathlib.Path) -> tuple[bool, str]:
    """Verify native AOT standalone machine binary (PE/ELF/Mach-O), no VM."""
    if not exe_path.is_file():
        return False, f"expected native binary at {exe_path}, file missing"
    header = exe_path.read_bytes()[:4]
    if os.name == "nt":
        if header[:2] != b"MZ":
            return False, f"expected native PE MZ header in {exe_path}, got {header!r}"
    else:
        if header != b"\x7fELF" and header not in (
            b"\xcf\xfa\xed\xfe",
            b"\xfe\xed\xfa\xcf",
        ):
            return False, f"expected native ELF/Mach-O header in {exe_path}, got {header!r}"
    return True, ""


def resolve_conformance_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_8_regalloc_isel" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def assemble_conformance_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)

    import bundle_common as bc  # noqa: E402

    return bc.assemble_template_bundle(
        str(probe_template_path),
        SEED_MODS,
        include_std_sys=True,
        root=root,
    )


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e15_8_conformance_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute live E15.8 RA + ISel + If-Conv + Post-RA Peephole + Verifier probe
    #    as standalone AOT binaries across -O0, -O1, and -O2 --verify-each (REQ-OPT-371, REQ-OPT-372).
    probe_template = resolve_conformance_path(root, "e15_8_conformance_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e15_8_conformance_probe_bundle.ax"
    probe_bundle.write_text(assemble_conformance_probe(root, probe_template), encoding="utf-8")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"e15_8_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build e15_8_probe {flag} --verify-each failed:\n{bproc.stderr}\n")
            return 1
        ok_bin, bin_err = verify_aot_native_binary(probe_exe)
        if not ok_bin:
            sys.stderr.write(f"{bin_err}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e15_8_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e15_8_probe under {flag}:\n"
                f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive conformance fixtures across
    #    --interp, -O0, -O1, and -O2 (all with --verify-each) (REQ-OPT-371).
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_conformance_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", "--verify-each", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")
        if norm_interp != exp_out:
            sys.stderr.write(
                f"stdout mismatch for {stem} under --interp:\nexpected:\n{exp_out}\ngot:\n{norm_interp}\n"
            )
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            ok_bin, bin_err = verify_aot_native_binary(exe_path)
            if not ok_bin:
                sys.stderr.write(f"{bin_err}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != exp_out:
                sys.stderr.write(
                    f"stdout mismatch for {stem} under {flag}:\nexpected:\n{exp_out}\ngot:\n{norm_out}\n"
                )
                return 1

    # 3. Differential panic/trap preservation across --interp, -O0, -O1, and -O2 --verify-each.
    for trap_idx, trap_fixture in enumerate(TRAP_FIXTURES):
        trap_path = resolve_conformance_path(root, trap_fixture)
        itrap = run_cmd([axiomc, "run", "--interp", "--verify-each", str(trap_path)], root, timeout=120)
        if itrap.returncode != EXPECTED_TRAP_EXIT:
            sys.stderr.write(
                f"expected exit {EXPECTED_TRAP_EXIT} for {trap_fixture} under --interp, got {itrap.returncode}\n"
            )
            return 1
        for flag in ("-O0", "-O1", "-O2"):
            trap_exe = tmp_dir / f"e15_8_trap_{trap_idx}_{flag[1:]}{exe_ext}"
            btrap = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(trap_exe), str(trap_path)], root)
            if btrap.returncode != 0:
                sys.stderr.write(f"build {trap_fixture} {flag} --verify-each failed:\n{btrap.stderr}\n")
                return 1
            ok_bin, bin_err = verify_aot_native_binary(trap_exe)
            if not ok_bin:
                sys.stderr.write(f"{bin_err}\n")
                return 1
            rtrap = run_cmd([str(trap_exe)], root)
            if rtrap.returncode != EXPECTED_TRAP_EXIT:
                sys.stderr.write(
                    f"expected exit {EXPECTED_TRAP_EXIT} for {trap_fixture} under {flag}, got {rtrap.returncode}\n"
                )
                return 1

    # 4. Deterministic --emit=mi and --emit=mc inspection across -O0, -O1, and -O2 --verify-each,
    #    plus structural verification of -O0 baseline vs -O1/-O2 target-specific lowering (REQ-OPT-371, REQ-OPT-372).
    mi_outputs: dict[tuple[str, str], str] = {}
    for _stem, filename, _exp in POSITIVE_FIXTURES:
        inspect_src = resolve_conformance_path(root, filename)
        for flag in ("-O0", "-O1", "-O2"):
            m1 = run_cmd([axiomc, "inspect", "--emit=mi", flag, "--verify-each", str(inspect_src)], root)
            m2 = run_cmd([axiomc, "inspect", "--emit=mi", flag, "--verify-each", str(inspect_src)], root)
            if m1.returncode != 0 or m2.returncode != 0:
                sys.stderr.write(f"inspect --emit=mi {filename} {flag} failed:\n{m1.stderr}\n")
                return 1
            if m1.stdout != m2.stdout:
                sys.stderr.write(f"non-deterministic --emit=mi for {filename} under {flag}\n")
                return 1
            if "frame_req: shadow=" not in m1.stdout or "bb0:" not in m1.stdout:
                sys.stderr.write(f"malformed --emit=mi output for {filename} under {flag}\n")
                return 1
            mi_outputs[(filename, flag)] = m1.stdout

    # Verify -O0 baseline vs -O1/-O2 target-specific lowering on `isel_lea_const_divmul_casts.ax`:
    isel_o0 = mi_outputs[("isel_lea_const_divmul_casts.ax", "-O0")]
    if "  idiv " not in isel_o0 or "  mul " in isel_o0:
        sys.stderr.write("expected baseline `idiv` (no magic `mul`) in -O0 --emit=mi for isel_lea_const_divmul_casts.ax\n")
        return 1
    for opt_flag in ("-O1", "-O2"):
        isel_opt = mi_outputs[("isel_lea_const_divmul_casts.ax", opt_flag)]
        if "  lea " not in isel_opt or "  mul " not in isel_opt:
            sys.stderr.write(
                f"expected scaled `lea` and magic-multiply `mul` in {opt_flag} --emit=mi for isel_lea_const_divmul_casts.ax\n"
            )
            return 1

    # Verify -O0 branchy diamonds vs -O1/-O2 `cmovcc` + non-speculated `idiv` on `if_conv_cmov_setcc_nospeculate.ax`:
    ifc_o0 = mi_outputs[("if_conv_cmov_setcc_nospeculate.ax", "-O0")]
    if "  cmovcc " in ifc_o0:
        sys.stderr.write("unexpected `cmovcc` in -O0 --emit=mi for if_conv_cmov_setcc_nospeculate.ax\n")
        return 1
    for opt_flag in ("-O1", "-O2"):
        ifc_opt = mi_outputs[("if_conv_cmov_setcc_nospeculate.ax", opt_flag)]
        if "  cmovcc " not in ifc_opt or "  jcc " not in ifc_opt:
            sys.stderr.write(
                f"expected both `cmovcc` (pure diamonds) and preserved `jcc` (non-speculated guarded arms) in {opt_flag} --emit=mi\n"
            )
            return 1

    # Verify deterministic --emit=mc across -O0, -O1, and -O2 --verify-each (full RA + post-RA peephole + x64_verify_checked + hex dump):
    mc_probe_src = tmp_dir / "e15_8_mc_inspect_probe.ax"
    mc_probe_src.write_text(STRAIGHT_LINE_MC_SRC, encoding="utf-8")
    for flag in ("-O0", "-O1", "-O2"):
        c1 = run_cmd([axiomc, "inspect", "--emit=mc", flag, "--verify-each", str(mc_probe_src)], root)
        c2 = run_cmd([axiomc, "inspect", "--emit=mc", flag, "--verify-each", str(mc_probe_src)], root)
        if c1.returncode != 0 or c2.returncode != 0:
            sys.stderr.write(f"inspect --emit=mc {flag} failed:\n{c1.stderr}\n")
            return 1
        if c1.stdout != c2.stdout or len(c1.stdout.strip()) == 0:
            sys.stderr.write(f"non-deterministic or empty --emit=mc under {flag}\n")
            return 1
        if "55 48 89 e5" not in c1.stdout or "c3" not in c1.stdout:
            sys.stderr.write(f"missing x64 frame prologue/ret bytes in --emit=mc under {flag}: {c1.stdout!r}\n")
            return 1

    sys.stdout.buffer.write(b"E15-8-REGALLOC-ISEL-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
