#!/usr/bin/env python3
"""Oracle test for E18.5 (T769 / SPEC-25): PassContract registry, 3-valued Certainty lattice,
ProofCertificate & ProofProvenance canonical Fingerprint128 caching and transitive invalidation,
multi-category EffectSummary lattices, bounded SymbolicValueDomain proofs, transactional
rollback on Possible/Unknown obligations, and --verify-pass-contracts traps across -O0, -O1, -O2.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIFF_AX = HERE / "pass_contracts_fail_closed_and_effects.ax"
EXPECTED_DIFF_STDOUT = "proven_opt=120\nfail_closed=77\ndrop_order=21\n"
PROBE_TEMPLATE = HERE / "pass_contracts_probe.ax.in"
EXPECTED_PROBE_STDOUT = (
    "PROBE_REGISTRY_CERTAINTY=OK\n"
    "PROBE_PROOF_STORE=OK\n"
    "PROBE_EFFECTS_SYMBOLIC=OK\n"
    "PROBE_TRANSACTIONAL_ENGINE=OK\n"
    "PROBE_ALL=OK\n"
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


def assemble_pass_contracts_probe(root: str, probe_template_path: pathlib.Path) -> str:
    mod_path = pathlib.Path(root) / "compiler" / "verify" / "pass_contracts" / "mod.ax"
    if not mod_path.is_file():
        sys.stderr.write(f"missing required compiler module: {mod_path}\n")
        sys.exit(1)

    selfhost_dir = os.path.join(root, "tests", "selfhost")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)

    import bundle_common as bc  # noqa: E402

    deps = bc.resolve_compiler_module_deps(
        ["compiler.mir.mir", "compiler.verify.pass_contracts"],
        root=root,
    )
    if "compiler.verify.pass_contracts" not in deps:
        deps.append("compiler.verify.pass_contracts")
    module_specs = [(m, "compiler") for m in deps]

    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    modules_src = bc.assemble_compiler_modules(module_specs, root=root)
    main_src = probe_template_path.read_text(encoding="utf-8")
    return prelude + "\n" + modules_src + "\n" + main_src


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: pass_contracts_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler, build_dir, tmp_dir_str, root = [os.path.abspath(p) for p in sys.argv[1:5]]
    axiomc = get_axiomc(compiler, build_dir, tmp_dir_str, root)
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble & execute compiler/verify/pass_contracts/mod.ax live probe across -O0, -O1, -O2
    probe_template = pathlib.Path(root) / "tests" / "run" / "pass_contracts" / "pass_contracts_probe.ax.in"
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "pass_contracts_probe_bundle.ax"
    probe_bundle.write_text(assemble_pass_contracts_probe(root, probe_template), encoding="utf-8")

    for opt_flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"pass_contracts_probe_{opt_flag[1:]}{exe_ext}"
        build_res = run_cmd(
            [axiomc, "build", opt_flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            cwd=root,
        )
        if build_res.returncode != 0:
            sys.stderr.write(
                f"build pass_contracts_probe failed ({opt_flag}):\n{build_res.stderr}\n{build_res.stdout}\n"
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
    diff_src = pathlib.Path(root) / "tests" / "run" / "pass_contracts" / "pass_contracts_fail_closed_and_effects.ax"
    if not diff_src.is_file():
        diff_src = DIFF_AX

    for opt_flag in ("-O0", "-O1", "-O2"):
        diff_exe = tmp_dir / f"pass_contracts_diff_{opt_flag[1:]}{exe_ext}"
        b_res = run_cmd(
            [axiomc, "build", opt_flag, "--verify-each", "-o", str(diff_exe), str(diff_src)],
            cwd=root,
        )
        if b_res.returncode != 0:
            sys.stderr.write(f"build diff failed ({opt_flag}):\n{b_res.stderr}\n")
            return 1
        r_res = run_cmd([str(diff_exe)], cwd=root)
        if r_res.returncode != 0 or r_res.stdout != EXPECTED_DIFF_STDOUT:
            sys.stderr.write(
                f"diff run mismatch ({opt_flag}): rc={r_res.returncode}\n"
                f"stdout:\n{r_res.stdout}\nexpected:\n{EXPECTED_DIFF_STDOUT}\n"
            )
            return 1

    sys.stdout.buffer.write(b"PASS-CONTRACTS-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
