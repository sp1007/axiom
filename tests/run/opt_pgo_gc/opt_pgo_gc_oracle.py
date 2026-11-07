#!/usr/bin/env python3
"""
E15.6 (T622) Live Engine + End-to-End Differential & Binary-Inspection Oracle
for `compiler.link.gc_icf` and `compiler.opt.pgo`:
- Part A: Assembles & executes the bundled live `compiler.link.gc_icf` + `compiler.opt.pgo`
          engine probe (`opt_pgo_gc_probe.ax.in` linked with real `compiler/link/gc_icf/mod.ax`,
          `compiler/opt/pgo/mod.ax`, `compiler/obj/coff.ax`, `compiler/opt/inline/mod.ax`,
          `compiler/opt/sroa/mod.ax`, `compiler/opt/passmgr/mod.ax`, and core MIR/OptIR modules),
          verifying:
          1. `COMDAT` group resolution (`COMDAT_ANY`, `COMDAT_EXACT_MATCH` mismatch detection,
             `COMDAT_NODUPLICATES` collision detection) & deterministic canonical leader selection;
             Mark-sweep section GC from formal roots (`Entry`, `Export`, `DynamicLookup`,
             `FfiCallback`, `Reflection`, `PinnedAt`, `ModuleInit`) with `COMDAT_ASSOC`
             `.pdata`/`.xdata` retention and dead code/data/unwind/import/runtime stripping.
          2. Safe Identical Code Folding (`ICF`) with non-address-taken folding, address-taken
             5-byte `0xE9` `jmp rel32` thunk emission, read-only `.rdata` constant/string merging,
             mutable/pinned preservation, `.bss` zero-data promotion, 3D binary size model
             (`file_size_bytes`, `mapped_size_bytes`, `working_set_bytes`), 128-bit cache identity,
             and deterministic `--emit=section-gc` (`section_gc_print`).
          3. `PassManager` `TransformationContract` (`PASS_PGO = 19u16`), `.axprof` binary
             serialization/deserialization (`AXPF` magic, schema v1), fail-closed rejection on
             tampered/incompatible profiles, deterministic weighted profile merging, and 4-level
             compatibility classification (`EXACT`, `COMPATIBLE`, `STALE`, `INCOMPATIBLE`) with
             graceful stale-profile fallback without aborting.
          4. Three-tier epistemic separation law (`CERTAINTY_UNKNOWN` / `CERTAINTY_POSSIBLE` never
             upgraded to `CERTAINTY_PROVEN`), PGO cost-model guidance (inlining, value-guarded
             specialization, guarded speculative devirtualization, loop unrolling, SIMD width,
             hot/cold splitting, `jcc` vs `cmovcc`, constant-time secret barriers), `PassManager`
             transactional rollback, and deterministic `--emit=pgo` (`pgo_print`).
- Part B: Runs differential execution across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`,
          and `-O2 --verify-each` on the E15.6 PGO/GC test corpus, asserting identical exit code
          and stdout AND verifying valid PE32+ headers/sections and byte-identical deterministic
          binary output across repeated builds.
"""

from __future__ import annotations

import os
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_pgo_gc_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_SECTION_GC_AND_ROOTS=OK\n"
    "PROBE_SAFE_ICF_RDATA_BSS=OK\n"
    "PROBE_SECTION_GC_EMIT_DETERMINISM=OK\n"
    "PROBE_PGO_SCHEMA_MERGE_AND_STALE=OK\n"
    "PROBE_PGO_EPISTEMIC_AND_COST_MODELS=OK\n"
    "PROBE_PGO_PASSMGR_AND_EMIT=OK\n"
    "PROBE_PGO_GC_ALL=PASS\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, int]] = [
    ("section_gc_dead_strip_and_roots", "section_gc_dead_strip_and_roots.ax", 0),
    ("safe_icf_and_fn_ptr_identity", "safe_icf_and_fn_ptr_identity.ax", 0),
    ("pgo_gen_use_and_stale_fallback", "pgo_gen_use_and_stale_fallback.ax", 0),
    ("pgo_epistemic_safety_barriers", "pgo_epistemic_safety_barriers.ax", 0),
    ("pgo_gc_icf_boundary_seam", "pgo_gc_icf_boundary_seam.ax", 0),
]

PGO_GC_PROBE_BLOBS: list[bytes] = [
    # 0: pgo_probe_target (fn#601)
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


def verify_pe32_plus_binary(exe_path: pathlib.Path) -> bytes:
    data = exe_path.read_bytes()
    if len(data) < 512 or data[:2] != b"MZ":
        raise RuntimeError(f"invalid DOS header in {exe_path}")
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_off + 24 > len(data) or data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise RuntimeError(f"invalid PE signature in {exe_path}")
    machine, num_sections = struct.unpack_from("<HH", data, pe_off + 4)
    if machine != 0x8664 or num_sections == 0:
        raise RuntimeError(f"unexpected PE machine={hex(machine)} sections={num_sections}")
    return data


def assemble_opt_pgo_gc_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", PGO_GC_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    pgo_gc_modules = list(got.CORE_MODULES) + [
        ("compiler.obj.coff", "compiler"),
        ("compiler.link.gc_icf", "compiler"),
        ("compiler.own.cap", "compiler"),
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
        ("compiler.opt.sroa", "compiler"),
        ("compiler.opt.inline", "compiler"),
        ("compiler.opt.pgo", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(pgo_gc_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_pgo_gc" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_pgo_gc_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.link.gc_icf + compiler.opt.pgo probe
    probe_template = resolve_fixture_path(root, "opt_pgo_gc_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_pgo_gc_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_pgo_gc_probe(root, probe_template), encoding="utf-8", newline="\n")

    rproc = run_cmd(
        [axiomc, "run", "--interp", str(probe_bundle)],
        root,
        timeout=600,
    )
    if rproc.returncode != 0:
        sys.stderr.write(
            f"opt_pgo_gc_probe --interp failed with exit code {rproc.returncode}:\n"
            f"{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_probe = rproc.stdout.replace("\r\n", "\n")
    if norm_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for opt_pgo_gc_probe under --interp:\n"
            f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
        )
        return 1

    # 2. Differential execution + PE32+ binary inspection & determinism across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_exit in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != exp_exit:
            sys.stderr.write(
                f"interp {stem} failed with {iproc.returncode} (expected {exp_exit}):\n{iproc.stderr}\n"
            )
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            bytes_1 = verify_pe32_plus_binary(exe_path)

            if flag == "-O2":
                exe_path_2 = tmp_dir / f"{stem}_{flag[1:]}_det{exe_ext}"
                bproc2 = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path_2), str(src_path)], root)
                if bproc2.returncode != 0:
                    sys.stderr.write(f"second build {stem} {flag} --verify-each failed:\n{bproc2.stderr}\n")
                    return 1
                bytes_2 = verify_pe32_plus_binary(exe_path_2)
                if bytes_1 != bytes_2:
                    sys.stderr.write(f"non-deterministic PE32+ binary output for {stem} under {flag}\n")
                    return 1

            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != exp_exit:
                sys.stderr.write(
                    f"run {stem} {flag} failed with {rproc.returncode} (expected {exp_exit}):\n{rproc.stderr}\n"
                )
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != norm_interp:
                sys.stderr.write(
                    f"stdout mismatch for {stem} under {flag}:\nexpected:\n{norm_interp}\ngot:\n{norm_out}\n"
                )
                return 1

    sys.stdout.buffer.write(b"OPT-PGO-GC-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
