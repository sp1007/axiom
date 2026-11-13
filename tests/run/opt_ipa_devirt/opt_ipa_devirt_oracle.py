#!/usr/bin/env python3
"""
E15.4 (T614) Live Engine + End-to-End Differential Oracle for `compiler.opt.ipa` + `compiler.opt.devirt`:
- Part A: Compiles & runs the bundled live `compiler.opt.ipa` + `compiler.opt.devirt` engine probe
          (`opt_ipa_devirt_probe.ax.in` linked with real `compiler/opt/ipa/mod.ax`,
          `compiler/opt/devirt/mod.ax`, `compiler/opt/inline/mod.ax`, `compiler/opt/sroa/mod.ax`,
          `compiler/opt/escape/mod.ax`, `compiler/opt/passmgr/mod.ax`, and frontend modules), verifying:
          1. `PassManager` `TransformationContract`s (`PASS_IPA_SPECIALIZE = 15u16`, `PASS_DEVIRT = 16u16`,
             `PASS_TAILCALL = 17u16`), canonical `SpecializationKey` hashing & equality, deterministic
             clone symbol mangling (`ipa_spec_clone_sym`), representation-equivalent code sharing with
             strict function-pointer identity preservation (`ipa_can_share_representation`, never merging
             when `address_taken_fn == true`), `SpecializationBudget` (`max_clones_per_fn`,
             `max_module_growth_pct`), post-specialization cleanup (`ConstFold` + `SROA` + `SimplifyCFG` +
             `DCE`) + `EffectSummary`/`EscapeSummary` tightening, transactional rollback, and
             deterministic `--emit=specialize` (`ipa_specialize_print`).
          2. Three-tier concrete-receiver devirtualization (`DEVIRT_TIER_EXACT`, `DEVIRT_TIER_GUARDED`,
             `DEVIRT_TIER_RETAINED_DYNAMIC`) for `DISPATCH_DYN_TRAIT`, `DISPATCH_FN_PTR`, and
             `DISPATCH_CLOSURE`, direct call rewrite + inline/SROA cascade, guarded `MIR_TERM_SWITCH_INT`
             dispatch rewrite with open/closed fallback, transactional rollback, and deterministic
             `--emit=devirt` (`devirt_print`).
          3. Tail-recursion loop lowering & sibling tail-call optimization (`TCO_LEGAL` preconditions:
             zero post-call `Drop` cleanup obligations, zero stack-borrowed `view<T>`/`mut_view<T>`
             escaping to the callee, strict tail position), self-tail-recursion loop lowering in `MirBody`
             (`out_edge_count == 0` and `loop_backedge_count >= 1`), explicit `@tailcall` legality
             verification (`TCO_DECISION_REJECTED_DIAG`), transactional rollback, and deterministic
             `--emit=inline` TCO reporting (`ipa_tailcall_print`).
- Part B: Runs differential execution across `--interp`, `-O0`, `-O1 --verify-each`, and `-O2 --verify-each`
          on the E15.4 test corpus (`callsite_const_closure_spec.ax`, `dyn_trait_and_fnptr_devirt.ax`,
          and `tailcall_loop_lowering_and_drop_guards.ax`), asserting identical exit code and stdout.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_ipa_devirt_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_IPA_CONTRACT_AND_KEY=OK\n"
    "PROBE_IPA_REP_EQUIV_AND_BUDGET=OK\n"
    "PROBE_IPA_SPECIALIZE_AND_EMIT=OK\n"
    "PROBE_DEVIRT_THREE_TIER_CLASSIFY=OK\n"
    "PROBE_DEVIRT_REWRITE_AND_INLINE_CASCADE=OK\n"
    "PROBE_DEVIRT_ROLLBACK_AND_EMIT=OK\n"
    "PROBE_TCO_LEGALITY_AND_GUARDS=OK\n"
    "PROBE_TCO_SELF_LOOP_LOWERING=OK\n"
    "PROBE_TCO_ATTR_DIAG_AND_EMIT=OK\n"
    "PROBE_IPA_DEVIRT_ALL=PASS\n"
)

POSITIVE_FIXTURES: list[tuple[str, str]] = [
    ("callsite_const_closure_spec", "callsite_const_closure_spec.ax"),
    ("dyn_trait_and_fnptr_devirt", "dyn_trait_and_fnptr_devirt.ax"),
    ("tailcall_loop_lowering_and_drop_guards", "tailcall_loop_lowering_and_drop_guards.ax"),
    ("spec_devirt_tco_boundary_seam", "spec_devirt_tco_boundary_seam.ax"),
]

IPA_DEVIRT_PROBE_BLOBS: list[bytes] = [
    b"probe_ipa_devirt_src.ax",
    (
        b"fn step_cb(v: i32) -> i32 {\n"
        b"    return v * 3 + 1;\n"
        b"}\n"
        b"fn configurable_kernel(enable_fast: bool, scale: i32, x: i32, cb: fn(i32) -> i32) -> i32 {\n"
        b"    if enable_fast {\n"
        b"        let y: i32 = cb(x);\n"
        b"        return y * scale;\n"
        b"    } else {\n"
        b"        let mut acc: i32 = x + scale;\n"
        b"        acc = acc * 2;\n"
        b"        return cb(acc) - scale;\n"
        b"    }\n"
        b"}\n"
        b"fn spec_caller_root(a: i32, b: i32) -> i32 {\n"
        b"    let r1: i32 = configurable_kernel(true, 10, a, step_cb);\n"
        b"    let r2: i32 = configurable_kernel(true, 10, b, step_cb);\n"
        b"    let r3: i32 = configurable_kernel(false, 20, a + b, step_cb);\n"
        b"    return r1 + r2 + r3;\n"
        b"}\n"
    ),
    (
        b"fn target_impl_a(x: i32) -> i32 {\n"
        b"    return x * 5 + 3;\n"
        b"}\n"
        b"fn target_impl_b(x: i32) -> i32 {\n"
        b"    return x * 7 - 2;\n"
        b"}\n"
        b"fn caller_exact_devirt(x: i32) -> i32 {\n"
        b"    let f: fn(i32) -> i32 = target_impl_a;\n"
        b"    return f(x);\n"
        b"}\n"
        b"fn caller_guarded_devirt(sel: bool, x: i32) -> i32 {\n"
        b"    let mut f: fn(i32) -> i32 = target_impl_a;\n"
        b"    if !sel {\n"
        b"        f = target_impl_b;\n"
        b"    }\n"
        b"    return f(x);\n"
        b"}\n"
        b"fn caller_open_export(f: fn(i32) -> i32, x: i32) -> i32 {\n"
        b"    return f(x);\n"
        b"}\n"
    ),
    (
        b"struct Guard {}\n"
        b"struct Slot {\n"
        b"    v: i32,\n"
        b"}\n"
        b"fn sum_self_tail(n: i32, acc: i32) -> i32 {\n"
        b"    if n <= 0 {\n"
        b"        return acc;\n"
        b"    }\n"
        b"    return sum_self_tail(n - 1, acc + n);\n"
        b"}\n"
        b"fn sibling_callee(x: i32, y: i32) -> i32 {\n"
        b"    return x * 3 + y;\n"
        b"}\n"
        b"fn sibling_caller(a: i32, b: i32) -> i32 {\n"
        b"    return sibling_callee(a + 1, b * 2);\n"
        b"}\n"
        b"fn non_tail_rec(n: i32) -> i32 {\n"
        b"    if n <= 0 {\n"
        b"        return 0;\n"
        b"    }\n"
        b"    return 1 + non_tail_rec(n - 1);\n"
        b"}\n"
        b"fn drop_guard_tail(n: i32, acc: i32) -> i32 {\n"
        b"    let g: Guard = Guard {};\n"
        b"    if n <= 0 {\n"
        b"        return acc;\n"
        b"    }\n"
        b"    return sum_self_tail(n - 1, acc + n);\n"
        b"}\n"
        b"fn view_consumer(s: view<Slot>) -> i32 {\n"
        b"    return s.v + 9;\n"
        b"}\n"
        b"fn stack_view_tail(x: i32) -> i32 {\n"
        b"    let local_slot: Slot = Slot { v: x };\n"
        b"    return view_consumer(view(local_slot));\n"
        b"}\n"
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


def assemble_opt_ipa_devirt_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", IPA_DEVIRT_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    ipa_devirt_modules = list(got.PIPELINE_MODULES) + [
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
        ("compiler.opt.sroa", "compiler"),
        ("compiler.opt.inline", "compiler"),
        ("compiler.opt.ipa", "compiler"),
        ("compiler.opt.devirt", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(ipa_devirt_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_ipa_devirt" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_ipa_devirt_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.ipa + compiler.opt.devirt probe
    probe_template = resolve_fixture_path(root, "opt_ipa_devirt_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_ipa_devirt_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_ipa_devirt_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0",):
        probe_exe = tmp_dir / f"opt_ipa_devirt_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=1500,
        )
        if bproc.returncode != 0:
            sys.stderr.write(
                f"build opt_ipa_devirt_probe {flag} failed:\n{bproc.stdout}\n{bproc.stderr}\n"
            )
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=180)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt_ipa_devirt_probe {flag} failed with exit code {rproc.returncode}:\n"
                f"{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt_ipa_devirt_probe under {flag}:\n"
                f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != norm_interp:
                sys.stderr.write(
                    f"stdout mismatch for {stem} under {flag}:\nexpected:\n{norm_interp}\ngot:\n{norm_out}\n"
                )
                return 1

    sys.stdout.buffer.write(b"OPT-IPA-DEVIRT-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
