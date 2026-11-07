#!/usr/bin/env python3
"""End-to-end oracle for E18.5 (T770): Bounded Translation Validation & Witness Checker (SPEC-25 §3-§4).

Verifies:
1. `compiler/verify/translation_val/mod.ax` (`compiler.verify.translation_val`) compiles cleanly
   with `compiler/verify/pass_contracts/mod.ax` via `axiomc2.exe` across `-O0`, `-O1`, and `-O2`.
2. Five-tier Observable Semantic Equivalence hierarchy (`Level 0 Structural` .. `Level 4 Observable
   Semantic Equivalence`) and per-function `TranslationWitness` recording (`AXS-PCT-020`).
3. Middle-end translation validation (`AXS-PCT-021`) across scalar/algebraic rewrites (exact
   bit-width, signed/unsigned polarity, IEEE-754 `NaN`/`-0.0`, and checked-overflow/div-by-zero/
   shift/bounds trap preservation), CFG canonicalization (`ReachableEdge`, phi/dominance
   completeness), and memory/loop transforms (`DSE`, `LoadForward`, `SROA`, `LICM`, `BCE`,
   preserving `volatile`, `atomic`, `Drop`, and capability barriers).
4. Target legalization (`8->64` promotion, `i128` `lo:hi` pair splitting, SIMD vector splitting)
   and post-RA register allocation witness validation (`AXS-PCT-022`: zero remaining vregs,
   physical register unit `RAX`/`EAX`/`AX`/`AL` and `XMM0`/`YMM0` overlap detection with
   move-coalescing provenance, dominating spill stores, fixed-register `RCX`/`RAX:RDX`, and
   caller/callee-save contracts).
5. Instruction scheduling dependency & barrier witness validation (`AXS-PCT-023`: `RAW`/`WAR`/`WAW`
   on GPR/XMM/stack/`EFLAGS`, plus `volatile`/`MMIO`, `atomic`, `fence`, `call`, trap, and aliasing
   memory barriers) and machine code finalization gate (`AXS-PCT-024`: 6-stage mask, 16-byte Win64
   `RSP` alignment, `__chkstk` on frames >= 4096 bytes, `Secret<T>` zeroization barriers, and
   `.pdata`/`.xdata` unwind match).
6. Deterministic rejection of synthetic pass bugs (dropped overflow check, clobbered live register,
   reordered `volatile` load) with `AX_ICE_MIR_VERIFY` / `AX_ICE_INTERNAL` (`data.stage =
   "translation_val"`) and deterministic `inspect --emit=pass-witness` formatting (`AXS-PCT-050`).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EQUIV_AX = HERE / "translation_val_equivalence.ax"
EXPECTED_EQUIV_STDOUT = (
    "TVAL_SCALAR_POLARITY_AND_TRAPS=OK\n"
    "TVAL_CFG_MEMORY_AND_DROP=OK\n"
    "TVAL_REGALLOC_AND_SCHED_PRESSURE=OK\n"
)
PROBE_TEMPLATE = HERE / "translation_val_probe.ax.in"
EXPECTED_PROBE_STDOUT = (
    "PROBE_EQUIVALENCE_AND_SCALAR=OK\n"
    "PROBE_CFG_MEMORY_AND_LEGALIZE=OK\n"
    "PROBE_REGALLOC_AND_SPILLS=OK\n"
    "PROBE_SCHEDULE_FINALIZE_AND_WITNESS=OK\n"
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


def assemble_translation_val_probe(root: str, probe_template_path: pathlib.Path) -> str:
    mod_path = pathlib.Path(root) / "compiler" / "verify" / "translation_val" / "mod.ax"
    if not mod_path.is_file():
        sys.stderr.write(f"missing required compiler module: {mod_path}\n")
        sys.exit(1)

    selfhost_dir = os.path.join(root, "tests", "selfhost")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)

    import bundle_common as bc  # noqa: E402

    deps = bc.resolve_compiler_module_deps(
        [
            "compiler.mir.mir",
            "compiler.verify.pass_contracts",
            "compiler.verify.translation_val",
        ],
        root=root,
    )
    if "compiler.verify.pass_contracts" not in deps:
        deps.append("compiler.verify.pass_contracts")
    if "compiler.verify.translation_val" not in deps:
        deps.append("compiler.verify.translation_val")
    module_specs = [(m, "compiler") for m in deps]

    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    modules_src = bc.assemble_compiler_modules(module_specs, root=root)
    main_src = probe_template_path.read_text(encoding="utf-8")
    return prelude + "\n" + modules_src + "\n" + main_src


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: translation_val_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler, build_dir, tmp_dir_str, root = [os.path.abspath(p) for p in sys.argv[1:5]]
    axiomc = get_axiomc(compiler, build_dir, tmp_dir_str, root)
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble & execute compiler/verify/translation_val/mod.ax live probe across -O0, -O1, -O2
    probe_template = pathlib.Path(root) / "tests" / "run" / "translation_val" / "translation_val_probe.ax.in"
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "translation_val_probe_bundle.ax"
    probe_bundle.write_text(assemble_translation_val_probe(root, probe_template), encoding="utf-8")

    for opt_flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"translation_val_probe_{opt_flag[1:]}{exe_ext}"
        build_res = run_cmd(
            [axiomc, "build", opt_flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            cwd=root,
        )
        if build_res.returncode != 0:
            sys.stderr.write(
                f"build translation_val_probe failed ({opt_flag}):\n{build_res.stderr}\n{build_res.stdout}\n"
            )
            return 1
        run_res = run_cmd([str(probe_exe)], cwd=root)
        if run_res.returncode != 0 or run_res.stdout != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"probe run mismatch ({opt_flag}): rc={run_res.returncode}\n"
                f"stdout:\n{run_res.stdout}\nexpected:\n{EXPECTED_PROBE_STDOUT}\n"
            )
            return 1

    # 2. Verify differential test across -O0, -O1, -O2 with --verify-each
    equiv_src = pathlib.Path(root) / "tests" / "run" / "translation_val" / "translation_val_equivalence.ax"
    if not equiv_src.is_file():
        equiv_src = EQUIV_AX

    for opt_flag in ("-O0", "-O1", "-O2"):
        equiv_exe = tmp_dir / f"translation_val_equiv_{opt_flag[1:]}{exe_ext}"
        b_res = run_cmd(
            [axiomc, "build", opt_flag, "--verify-each", "-o", str(equiv_exe), str(equiv_src)],
            cwd=root,
        )
        if b_res.returncode != 0:
            sys.stderr.write(f"build equiv failed ({opt_flag}):\n{b_res.stderr}\n")
            return 1
        r_res = run_cmd([str(equiv_exe)], cwd=root)
        if r_res.returncode != 0 or r_res.stdout != EXPECTED_EQUIV_STDOUT:
            sys.stderr.write(
                f"equiv run mismatch ({opt_flag}): rc={r_res.returncode}\n"
                f"stdout:\n{r_res.stdout}\nexpected:\n{EXPECTED_EQUIV_STDOUT}\n"
            )
            return 1

    sys.stdout.buffer.write(b"TRANSLATION-VAL-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
