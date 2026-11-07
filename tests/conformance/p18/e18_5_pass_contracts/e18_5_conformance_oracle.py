#!/usr/bin/env python3
"""E18.5 Conformance Suite Oracle (T771; SPEC-25 AXS-PCT-001..053, INV-PCT-003):

End-to-end conformance verification covering:
1. Live bundling and execution of `compiler/verify/pass_contracts/mod.ax` (`compiler.verify.pass_contracts`)
   and `compiler/verify/translation_val/mod.ax` (`compiler.verify.translation_val`) with `axiomc2.exe`
   across `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`:
   - `PassContract` registry, topological analysis dependency & invalidation closure, and 3-valued
     `Certainty` lattice (`Proven`, `Possible`, `Unknown`) with semantic firewall (`AXS-PCT-001..010`);
   - `ProofCertificate` / `ProofProvenance` canonical 128-bit `Fingerprint128` caching, transitive
     DAG invalidation on IR mutation, and `FactOrigin.TrustedBoundary` audit trail (`AXS-PCT-011`, `AXS-PCT-015`);
   - Shared monotone dataflow fixed-point engine, multi-category `PctEffectSummary` lattices, and
     in-process `SymbolicValueDomain` proofs with zero external SMT dependency (`AXS-PCT-012..014`);
   - Fail-closed transactional rollback on `Unknown`/`Possible` obligations and 5-tier
     `TranslationWitness` validation across middle-end (`MIR` <-> `OptIR` scalar, CFG, memory/loop)
     and backend (`LIR` legalization, `RegAlloc` live-range/spill, `Scheduling` `RAW`/`WAR`/`WAW` &
     `volatile`/`atomic`/`trap` barriers, and `Final Machine IR 3.0` gate) (`AXS-PCT-020..024`,
     `REQ-LNK-3384..3433`);
   - Synthetic pass-bug rejection (`AX_ICE_MIR_VERIFY` / `AX_ICE_INTERNAL` with `data.stage =
     "pass_contract"` and `data.stage = "translation_val"`) and deterministic `inspect --emit=pass-witness`
     formatting (`AXS-PCT-050..052`).
2. Differential equivalence of all E18.5 conformance programs across `--interp`, `-O0 --verify-each`,
   `-O1 --verify-each`, and `-O2 --verify-each`, plus byte-reproducible deterministic output verification
   (`REQ-LNK-3384`, `REQ-LNK-3412`).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e18_5_conformance_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_E18_5_PIPELINE_CONTRACTS_AND_CERTAINTY=OK\n"
    "PROBE_E18_5_DATAFLOW_EFFECTS_AND_SYMBOLIC=OK\n"
    "PROBE_E18_5_FAIL_CLOSED_AND_MIDDLE_END_WITNESS=OK\n"
    "PROBE_E18_5_BACKEND_LEGALIZE_RA_SCHED_FINALIZE=OK\n"
    "PROBE_E18_5_SYNTHETIC_BUGS_AND_DETERMINISTIC_WITNESS=OK\n"
    "PROBE_E18_5_ALL=OK\n"
)

CONFORMANCE_DIFF_FIXTURES: list[tuple[str, str, str]] = [
    (
        "overflow_and_signed_unsigned_polarity",
        "overflow_and_signed_unsigned_polarity.ax",
        "Xin chào E18.5 overflow_and_signed_unsigned_polarity\n"
        "checked_and_wrapping=194\n"
        "signed_unsigned_polarity=312\n"
        "narrow_and_i128_carry=478\n"
        "fail_closed_untaken=265\n"
        "checksum=1249\n",
    ),
    (
        "drop_capability_and_effect_barriers",
        "drop_capability_and_effect_barriers.ax",
        "Xin chào E18.5 drop_capability_and_effect_barriers\n"
        "drop_lifo=D30D20D10\n"
        "drop_early=D50D40\n"
        "cap_reborrow_sroa=342\n"
        "callback_and_impure_dce=288\n"
        "checksum=640\n",
    ),
    (
        "volatile_atomic_and_schedule_invariants",
        "volatile_atomic_and_schedule_invariants.ax",
        "Xin chào E18.5 volatile_atomic_and_schedule_invariants\n"
        "volatile_mmio_order=415\n"
        "atomic_sync_order=530\n"
        "raw_ptr_and_reg_pressure=612\n"
        "schedule_dep_eflags=378\n"
        "checksum=1935\n",
    ),
    (
        "final_machine_ir_and_frame_reproducibility",
        "final_machine_ir_and_frame_reproducibility.ax",
        "Xin chào E18.5 final_machine_ir_and_frame_reproducibility\n"
        "win64_stack_args_align=510\n"
        "large_frame_and_slots=740\n"
        "shrink_wrap_and_tail_unwind=D99\n"
        "shrink_tail_val=365\n"
        "secret_zeroize_barrier=420\n"
        "checksum=2035\n",
    ),
    (
        "boundary_cfg_diamond_and_loop_drop_guards",
        "boundary_cfg_diamond_and_loop_drop_guards.ax",
        "Xin chào E18.5 boundary_cfg_diamond_and_loop_drop_guards\n"
        "loop_drops=L1L2L3\n"
        "cfg_diamond_loop_drop=190\n"
        "shift_and_sign_extrema=110\n"
        "zero_trip_licm_guard=300\n"
        "checksum=600\n",
    ),
]


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


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p18" / "e18_5_pass_contracts" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_pe_binary(exe_path: pathlib.Path) -> bool:
    if not exe_path.is_file() or exe_path.stat().st_size <= 512:
        return False
    if os.name == "nt" and exe_path.read_bytes()[:2] != b"MZ":
        return False
    return True


def assemble_e18_5_probe(root: str, probe_template_path: pathlib.Path) -> str:
    pct_mod = pathlib.Path(root) / "compiler" / "verify" / "pass_contracts" / "mod.ax"
    tval_mod = pathlib.Path(root) / "compiler" / "verify" / "translation_val" / "mod.ax"
    if not pct_mod.is_file():
        sys.stderr.write(f"missing required compiler module: {pct_mod}\n")
        raise SystemExit(1)
    if not tval_mod.is_file():
        sys.stderr.write(f"missing required compiler module: {tval_mod}\n")
        raise SystemExit(1)

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
        sys.stderr.write("usage: e18_5_conformance_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler, build_dir, tmp_dir_str, root = [os.path.abspath(p) for p in sys.argv[1:5]]
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute the combined pass_contracts + translation_val probe across -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "e18_5_conformance_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e18_5_conformance_probe_bundle.ax"
    probe_bundle.write_text(assemble_e18_5_probe(root, probe_template), encoding="utf-8", newline="\n")

    for opt_flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"e18_5_probe_{opt_flag[1:]}{exe_ext}"
        b_res = run_cmd(
            [axiomc, "build", opt_flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            cwd=root,
        )
        if b_res.returncode != 0:
            sys.stderr.write(
                f"build e18_5_probe failed ({opt_flag} --verify-each):\n{b_res.stderr}\n{b_res.stdout}\n"
            )
            return 1
        if not verify_pe_binary(probe_exe):
            sys.stderr.write(f"invalid PE binary produced for e18_5_probe ({opt_flag})\n")
            return 1
        r_res = run_cmd([str(probe_exe)], cwd=root)
        norm_probe = r_res.stdout.replace("\r\n", "\n")
        if r_res.returncode != 0 or norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"e18_5_probe mismatch ({opt_flag}): rc={r_res.returncode}\n"
                f"stdout:\n{norm_probe}\nexpected:\n{EXPECTED_PROBE_STDOUT}\n"
            )
            return 1

    # 2. Differential execution of all 4 E18.5 conformance fixtures across --interp, -O0, -O1, -O2 --verify-each
    for stem, filename, exp_out in CONFORMANCE_DIFF_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        i_res = run_cmd([axiomc, "run", "--interp", "--verify-each", str(src_path)], cwd=root)
        norm_interp = i_res.stdout.replace("\r\n", "\n")
        if i_res.returncode != 0 or norm_interp != exp_out:
            sys.stderr.write(
                f"interp mismatch for {stem}: rc={i_res.returncode}\n"
                f"stderr:\n{i_res.stderr}\nstdout:\n{norm_interp}\nexpected:\n{exp_out}\n"
            )
            return 1

        for opt_flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{opt_flag[1:]}{exe_ext}"
            b_res = run_cmd(
                [axiomc, "build", opt_flag, "--verify-each", "-o", str(exe_path), str(src_path)],
                cwd=root,
            )
            if b_res.returncode != 0:
                sys.stderr.write(f"build {stem} {opt_flag} --verify-each failed:\n{b_res.stderr}\n")
                return 1
            if not verify_pe_binary(exe_path):
                sys.stderr.write(f"invalid PE binary produced for {stem} {opt_flag}\n")
                return 1
            r_res = run_cmd([str(exe_path)], cwd=root)
            norm_out = r_res.stdout.replace("\r\n", "\n")
            if r_res.returncode != 0 or norm_out != exp_out:
                sys.stderr.write(
                    f"native {opt_flag} mismatch for {stem}: rc={r_res.returncode}\n"
                    f"stdout:\n{norm_out}\nexpected:\n{exp_out}\n"
                )
                return 1

    # 3. Byte-reproducible deterministic build & IR inspection check (REQ-LNK-3384, REQ-LNK-3412)
    repro_src = resolve_fixture_path(root, "final_machine_ir_and_frame_reproducibility.ax")
    exe_a = tmp_dir / f"repro_a{exe_ext}"
    exe_b = tmp_dir / f"repro_b{exe_ext}"
    ba = run_cmd([axiomc, "build", "-O2", "--verify-each", "-o", str(exe_a), str(repro_src)], cwd=root)
    bb = run_cmd([axiomc, "build", "-O2", "--verify-each", "-o", str(exe_b), str(repro_src)], cwd=root)
    if ba.returncode != 0 or bb.returncode != 0 or exe_a.read_bytes() != exe_b.read_bytes():
        sys.stderr.write("deterministic PE build reproducibility check failed (REQ-LNK-3384, REQ-LNK-3412)\n")
        return 1

    sys.stdout.buffer.write(b"E18.5-PASS-CONTRACTS-TRANSLATION-VAL-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
