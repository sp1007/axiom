#!/usr/bin/env python3
"""
E15.6 (T621) Live Engine + End-to-End Differential Oracle for `compiler.opt.lto`:
- Part A: Compiles & runs the bundled live `compiler.opt.lto` engine probe
          (`opt_lto_probe.ax.in` linked with real `compiler/opt/lto/mod.ax`,
          `compiler/opt/devirt/mod.ax`, `compiler/opt/ipa/mod.ax`,
          `compiler/opt/inline/mod.ax`, `compiler/opt/sroa/mod.ax`,
          `compiler/opt/escape/mod.ax`, `compiler/opt/passmgr/mod.ax`, and core MIR/OptIR modules),
          verifying:
          1. `PassManager` `TransformationContract` (`PASS_LTO = 18u16`), LTO modes
             (`LTO_MODE_OFF`, `LTO_MODE_THIN`, `LTO_MODE_FAT`), `WorldScope`
             (`WORLD_CLOSED`, `WORLD_PARTIAL`, `WORLD_OPEN`), `.axmeta` `LtoModuleSummary`
             binary serialization/deserialization (`lto_serialize_module_summary`,
             `lto_deserialize_module_summary`), 64-bit/128-bit semantic digests
             (`lto_compute_module_digest`), corrupt-header/tampered-digest rejection, and
             `ThinLTO` partition invalidation (`lto_thin_partition_needs_rebuild`).
          2. Whole-program closed-world reachability (`lto_compute_reachability`),
             non-exported `pub` symbol internalization (`lto_internalize_symbols`),
             formal root preservation (`Entry`, `Export`, `FfiCallback`, `Reflection`,
             `DynamicLookup`, `PinnedAt` / `volatile` MMIO), RTA vtable liveness, and
             dead function/static/vtable pruning (`lto_prune_unreachable`).
          3. Cross-module `OptIR` optimization (`lto_run_cross_module_opt`): closed-world
             single-implementor `dyn Trait` RTA devirtualization, cross-module constant
             specialization, single-caller internalized promotion + cross-module inlining,
             cross-module `EffectSummary`/`EscapeSummary`/`AliasSummary` propagation with
             fail-closed `UnknownAlias` barrier on raw-pointer/FFI boundaries and
             `atomic`/`volatile` barrier preservation, and `PassManager` transactional
             rollback (`lto_run_pass_internal`).
          4. Cross-module generic monomorphization deduplication (`lto_deduplicate_generics`):
             exact duplicate instance merging (`LTO_DEDUP_EXACT_INSTANCE`),
             representation-equivalent code sharing (`LTO_DEDUP_REP_EQUIV_SHARED`),
             distinct function-pointer address preservation when `address_taken_fn == true`
             (`LTO_DEDUP_KEPT_ADDRESS_TAKEN`), custom drop preservation
             (`LTO_DEDUP_KEPT_CUSTOM_DROP`), and deterministic `--emit=lto` (`lto_print`).
- Part B: Runs differential execution across `--interp`, `-O0`, `-O1 --verify-each`, and
          `-O2 --verify-each` on the E15.6 test corpus
          (`closed_world_reachability_and_roots.ax`, `cross_module_inline_spec_devirt.ax`,
          and `generic_dedup_and_fn_ptr_identity.ax`), asserting identical exit code and stdout.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_lto_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_LTO_CONTRACT_AND_AXMETA=OK\n"
    "PROBE_LTO_THIN_INVALIDATION=OK\n"
    "PROBE_LTO_INTERNALIZE_AND_ROOTS=OK\n"
    "PROBE_LTO_REACHABILITY_AND_PRUNE=OK\n"
    "PROBE_LTO_SUMMARY_AND_ALIAS_BARRIERS=OK\n"
    "PROBE_LTO_CROSS_MODULE_OPT_AND_ROLLBACK=OK\n"
    "PROBE_LTO_GENERIC_DEDUP_AND_FN_PTR=OK\n"
    "PROBE_LTO_EMIT_DETERMINISM=OK\n"
    "PROBE_LTO_ALL=PASS\n"
)

POSITIVE_FIXTURES: list[tuple[str, str]] = [
    ("closed_world_reachability_and_roots", "closed_world_reachability_and_roots.ax"),
    ("cross_module_inline_spec_devirt", "cross_module_inline_spec_devirt.ax"),
    ("generic_dedup_and_fn_ptr_identity", "generic_dedup_and_fn_ptr_identity.ax"),
    ("lto_wpo_boundary_seam", "lto_wpo_boundary_seam.ax"),
]

LTO_PROBE_BLOBS: list[bytes] = [
    # 0: mod_b_leaf_scale (fn#501)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    bb0: {\n"
        b"        _0 = copy _1 * const 3: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 1: mod_b_spec_kernel (fn#502)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#4; // arg\n"
        b"    let _2: type#8; // arg\n"
        b"    let _3: type#8; // arg\n"
        b"    bb0: {\n"
        b"        switchInt(copy _1) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy _3 * copy _2;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _0 = copy _3 - copy _2;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 2: mod_b_dyn_impl (fn#503)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    bb0: {\n"
        b"        _0 = copy _1 + const 19: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 3: mod_a_entry (fn#504)
    (
        b"mir_body {\n"
        b"    type 20 = fn(type#8) -> type#8;\n"
        b"    type 21 = fn(type#4, type#8, type#8) -> type#8;\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#20;\n"
        b"    bb0: {\n"
        b"        _2 = const 0: type#20(copy _1) -> [return: bb1, unwind: bb4];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = const 0: type#21(const true: type#4, const 10: type#8, copy _2) -> [return: bb2, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4 = const 0: type#20;\n"
        b"        _0 = copy _4(copy _3) -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 4: mod_b_dead_helper (fn#505)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    bb0: {\n"
        b"        _0 = copy _1 * const 99: type#8;\n"
        b"        return;\n"
        b"    }\n"
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


def assemble_opt_lto_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", LTO_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    lto_modules = list(got.CORE_MODULES) + [
        ("compiler.own.cap", "compiler"),
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
        ("compiler.opt.sroa", "compiler"),
        ("compiler.opt.inline", "compiler"),
        ("compiler.opt.ipa", "compiler"),
        ("compiler.opt.devirt", "compiler"),
        ("compiler.opt.lto", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(lto_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_lto" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_lto_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.lto probe
    probe_template = resolve_fixture_path(root, "opt_lto_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_lto_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_lto_probe(root, probe_template), encoding="utf-8", newline="\n")

    rproc = run_cmd(
        [axiomc, "run", "--interp", str(probe_bundle)],
        root,
        timeout=600,
    )
    if rproc.returncode != 0:
        sys.stderr.write(
            f"opt_lto_probe --interp failed with exit code {rproc.returncode}:\n"
            f"{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_probe = rproc.stdout.replace("\r\n", "\n")
    if norm_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for opt_lto_probe under --interp:\n"
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

    sys.stdout.buffer.write(b"OPT-LTO-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
