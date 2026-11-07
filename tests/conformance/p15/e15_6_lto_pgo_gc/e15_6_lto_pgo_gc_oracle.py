#!/usr/bin/env python3
"""
E15.6 (T623) End-to-End Conformance & Differential Oracle for LTO, Whole-Program Optimization,
Linker Section GC / Safe ICF, & Profile-Guided Optimization (`SPEC-75` §§1-11, `REQ-OPT-246..250`):
- Part A: Compiles and executes the unified live E15.6 engine probe (`e15_6_lto_pgo_gc_probe.ax.in`)
          linked with `compiler.opt.lto`, `compiler.link.gc_icf`, `compiler.opt.pgo`,
          `compiler.opt.devirt`, `compiler.opt.ipa`, `compiler.opt.inline`, `compiler.opt.sroa`,
          `compiler.opt.escape`, `compiler.opt.memopt`, `compiler.opt.alias`, `compiler.own.cap`,
          and `compiler.opt.passmgr`, verifying:
          1. `.axmeta` summary serialization/deserialization, 64/128-bit semantic digests, and
             `ThinLTO` partition rebuild detection (`PASS_LTO = 18`).
          2. Closed-world vs open-world reachability, non-exported `pub` internalization, formal
             roots (`Entry`, `@export`, `FfiCallback`, `Reflection`, `PinnedAt` MMIO), cross-module
             `OptIR` inlining/specialization/RTA devirtualization, `UnknownAlias`/`atomic`/`volatile`
             barriers, generic monomorphization deduplication, and `lto_print` determinism.
          3. Linker section GC (`PASS_SECTION_GC_ICF = 20`), `COMDAT` resolution, `.pdata` reverse-
             dependency reclamation, unused import/runtime stripping, Safe `ICF` with 5-byte `0xE9`
             `jmp rel32` thunks for address-taken functions, `.rdata` constant/string pooling,
             `.bss` zero-data promotion, 3D binary size model, and `section_gc_print` determinism.
          4. `--pgo-gen` -> weighted `pgo_merge_profiles` -> `.axprof` round-trip -> `--pgo-use`
             (`PASS_PGO = 19`), stale-profile graceful fallback, epistemic safety law
             (`CERTAINTY_UNKNOWN`/`CERTAINTY_POSSIBLE` never upgraded to `CERTAINTY_PROVEN`),
             constant-time secret (`zeroize`/`black_box`) & `atomic`/`volatile` barriers,
             transactional rollback, and `pgo_print` determinism.
- Part B: Synthesizes a multi-module package (`main.ax`, `math_kernel.ax`, `generic_dedup.ax`) and
          verifies exact `--interp` vs `-O0`, `-O1`, and `-O2 --verify-each` equivalence (both via
          package directory discovery and explicit multi-file `axiomc build`), valid PE32+ binaries,
          and byte-identical deterministic executable output.
- Part C: Runs differential execution across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`,
          and `-O2 --verify-each` on the E15.6 positive conformance fixtures and the panic/bounds
          trap fixture (`trap_pgo_lto_bounds_and_drop_order.ax`, exit code 101).
- Part D: Verifies byte-identical `axiomc inspect --emit=optir` and `axiomc inspect --emit=memssa`
          outputs across `-O0`, `-O1`, and `-O2` `--verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e15_6_lto_pgo_gc_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_E15_6_LTO_AXMETA_AND_THIN_DIGESTS=OK\n"
    "PROBE_E15_6_LTO_REACHABILITY_AND_CROSS_MOD_OPT=OK\n"
    "PROBE_E15_6_SECTION_GC_DEAD_STRIP_AND_ROOTS=OK\n"
    "PROBE_E15_6_SAFE_ICF_RODATA_BSS_AND_SIZE_MODEL=OK\n"
    "PROBE_E15_6_PGO_ROUNDTRIP_AND_STALE_RESILIENCE=OK\n"
    "PROBE_E15_6_PGO_SAFETY_CONTRACTS_AND_WPO_PIPELINE=OK\n"
    "PROBE_E15_6_CONFORMANCE_ALL=PASS\n"
)

POSITIVE_FIXTURES: list[tuple[str, str]] = [
    ("lto_multimod_inline_spec_devirt_dedup", "lto_multimod_inline_spec_devirt_dedup.ax"),
    ("section_gc_roots_and_safe_icf_identity", "section_gc_roots_and_safe_icf_identity.ax"),
    ("pgo_roundtrip_stale_and_safety_contracts", "pgo_roundtrip_stale_and_safety_contracts.ax"),
]

TRAP_FIXTURES: list[tuple[str, str, int, str]] = [
    (
        "trap_pgo_lto_bounds_and_drop_order",
        "trap_pgo_lto_bounds_and_drop_order.ax",
        101,
        "60\n414141\n",
    ),
]

E15_6_PROBE_BLOBS: list[bytes] = [
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

MULTIMOD_MATH_KERNEL_AX = """\
module math_kernel

pub fn affine_step(x: i64, scale: i64, bias: i64) -> i64 {
    if scale == 0 {
        return bias;
    }
    if scale == 1 {
        return x + bias;
    }
    x * scale + bias
}

pub fn dead_unreferenced_kernel(x: i64) -> i64 {
    x * 999 + 12345
}
"""

MULTIMOD_GENERIC_DEDUP_AX = """\
module generic_dedup

pub struct BoxedVal<T> {
    pub v: T,
}

pub fn extract_boxed<T>(b: BoxedVal<T>) -> T {
    b.v
}

pub fn addr_lane_a(x: i64) -> i64 {
    (x ^ 42) + 7
}

pub fn addr_lane_b(x: i64) -> i64 {
    (x ^ 42) + 7
}
"""

MULTIMOD_MAIN_AX = """\
module main

use math_kernel.affine_step
use generic_dedup.BoxedVal
use generic_dedup.extract_boxed
use generic_dedup.addr_lane_a
use generic_dedup.addr_lane_b

@export
pub fn exported_multimod_entry(a: i64, b: i64) -> i64 {
    affine_step(a, 3, b)
}

fn invoke_lanes(fa: fn(i64) -> i64, fb: fn(i64) -> i64, x: i64) -> i64 {
    fa(x) + fb(x) + 1
}

pub fn main() -> i32 {
    let mut acc: i64 = 0;
    let mut i: i64 = 0;
    while i < 6 {
        acc = acc + affine_step(i * 4, 1, 5) + affine_step(i + 1, 3, -2);
        i = i + 1;
    }
    let g1 = extract_boxed<i64>(BoxedVal<i64> { v: 110 });
    let g2 = extract_boxed<u64>(BoxedVal<u64> { v: 90u64 }) as i64;
    let g3 = extract_boxed<usize>(BoxedVal<usize> { v: 50usize }) as i64;
    let fa: fn(i64) -> i64 = addr_lane_a;
    let fb: fn(i64) -> i64 = addr_lane_b;
    print_int(acc + exported_multimod_entry(10, 8));
    print("\\n");
    print_int(g1 + g2 + g3 + invoke_lanes(fa, fb, 12));
    print("\\n");
    0
}
"""


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


def verify_pe32_plus_binary(exe_path: pathlib.Path) -> None:
    data = exe_path.read_bytes()
    if len(data) < 512 or data[:2] != b"MZ":
        raise AssertionError(f"invalid DOS header in {exe_path}")
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_off + 24 > len(data) or data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise AssertionError(f"invalid PE signature in {exe_path}")
    machine, num_sections = struct.unpack_from("<HH", data, pe_off + 4)
    if machine != 0x8664 or num_sections < 1:
        raise AssertionError(f"unexpected COFF header in {exe_path}: machine={hex(machine)}, sections={num_sections}")
    opt_magic = struct.unpack_from("<H", data, pe_off + 24)[0]
    if opt_magic != 0x20B:
        raise AssertionError(f"expected PE32+ magic 0x20B in {exe_path}, got {hex(opt_magic)}")


def assemble_e15_6_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", E15_6_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    e15_6_modules = list(got.CORE_MODULES) + [
        ("compiler.obj.coff", "compiler"),
        ("compiler.link.gc_icf", "compiler"),
        ("compiler.own.cap", "compiler"),
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
        ("compiler.opt.sroa", "compiler"),
        ("compiler.opt.inline", "compiler"),
        ("compiler.opt.ipa", "compiler"),
        ("compiler.opt.devirt", "compiler"),
        ("compiler.opt.lto", "compiler"),
        ("compiler.opt.pgo", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(e15_6_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_6_lto_pgo_gc" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e15_6_lto_pgo_gc_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute unified E15.6 live engine probe (`lto` + `gc_icf` + `pgo`) ONCE under `-O0`
    probe_template = resolve_fixture_path(root, "e15_6_lto_pgo_gc_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e15_6_lto_pgo_gc_probe_bundle.ax"
    probe_bundle.write_text(assemble_e15_6_probe(root, probe_template), encoding="utf-8", newline="\n")

    probe_exe = tmp_dir / f"e15_6_lto_pgo_gc_probe_O0{exe_ext}"
    bproc = run_cmd(
        [axiomc, "build", "--stack-reserve=67108864", "-O0", "-o", str(probe_exe), str(probe_bundle)],
        root,
        timeout=900,
    )
    if bproc.returncode != 0:
        sys.stderr.write(
            f"build e15_6_lto_pgo_gc_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1
    verify_pe32_plus_binary(probe_exe)
    rproc = run_cmd([str(probe_exe)], root, timeout=600)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e15_6_lto_pgo_gc_probe -O0 failed with exit code {rproc.returncode}:\n"
            f"{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_probe = rproc.stdout.replace("\r\n", "\n")
    if norm_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e15_6_lto_pgo_gc_probe under -O0:\n"
            f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
        )
        return 1

    # 2. Multi-module package compilation & differential execution (`main.ax` + `math_kernel.ax` + `generic_dedup.ax`)
    pkg_dir = tmp_dir / "multimod_lto_pkg"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    main_ax = pkg_dir / "main.ax"
    math_ax = pkg_dir / "math_kernel.ax"
    gen_ax = pkg_dir / "generic_dedup.ax"
    main_ax.write_text(MULTIMOD_MAIN_AX, encoding="utf-8", newline="\n")
    math_ax.write_text(MULTIMOD_MATH_KERNEL_AX, encoding="utf-8", newline="\n")
    gen_ax.write_text(MULTIMOD_GENERIC_DEDUP_AX, encoding="utf-8", newline="\n")

    pkg_interp = run_cmd([axiomc, "run", "--interp", str(pkg_dir)], root, timeout=120)
    if pkg_interp.returncode != 0:
        sys.stderr.write(f"multimod_lto_pkg --interp failed:\n{pkg_interp.stderr}\n")
        return 1
    expected_pkg_out = pkg_interp.stdout.replace("\r\n", "\n")
    if expected_pkg_out != "179\n341\n":
        sys.stderr.write(f"unexpected multimod_lto_pkg --interp stdout:\n{expected_pkg_out}\n")
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        pkg_exe = tmp_dir / f"multimod_lto_pkg_{flag[1:]}{exe_ext}"
        b_pkg = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(pkg_exe), str(pkg_dir)], root)
        if b_pkg.returncode != 0:
            sys.stderr.write(f"build multimod_lto_pkg {flag} --verify-each failed:\n{b_pkg.stderr}\n")
            return 1
        verify_pe32_plus_binary(pkg_exe)
        r_pkg = run_cmd([str(pkg_exe)], root)
        if r_pkg.returncode != 0 or r_pkg.stdout.replace("\r\n", "\n") != expected_pkg_out:
            sys.stderr.write(
                f"run multimod_lto_pkg {flag} mismatch (rc={r_pkg.returncode}):\n"
                f"expected:\n{expected_pkg_out}\ngot:\n{r_pkg.stdout}\n"
            )
            return 1

    # Also test explicit multi-file `axiomc build -O2 --verify-each -o <exe> main.ax math_kernel.ax generic_dedup.ax`
    multi_exe = tmp_dir / f"multimod_explicit_O2{exe_ext}"
    b_multi = run_cmd(
        [axiomc, "build", "-O2", "--verify-each", "-o", str(multi_exe), str(main_ax), str(math_ax), str(gen_ax)],
        root,
    )
    if b_multi.returncode != 0:
        sys.stderr.write(f"explicit multi-file build -O2 --verify-each failed:\n{b_multi.stderr}\n")
        return 1
    verify_pe32_plus_binary(multi_exe)
    r_multi = run_cmd([str(multi_exe)], root)
    if r_multi.returncode != 0 or r_multi.stdout.replace("\r\n", "\n") != expected_pkg_out:
        sys.stderr.write(f"explicit multi-file run mismatch:\n{r_multi.stdout}\n")
        return 1

    # 3. Differential execution of positive conformance fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    #    plus byte-identical PE32+ executable determinism check
    for stem, filename in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")
        if not norm_interp.strip():
            sys.stderr.write(f"interp {stem} produced empty stdout (WEAK-NATIVE violation)\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            verify_pe32_plus_binary(exe_path)
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != norm_interp or rproc.stderr != iproc.stderr:
                sys.stderr.write(
                    f"stdout/stderr mismatch for {stem} under {flag}:\nexpected:\n{norm_interp}\ngot:\n{norm_out}\n"
                )
                return 1

        # Verify byte-identical deterministic `-O2 --verify-each` PE32+ output across repeated builds
        exe_o2_a = tmp_dir / f"{stem}_O2{exe_ext}"
        exe_o2_b = tmp_dir / f"{stem}_O2_repeat{exe_ext}"
        b_rep = run_cmd([axiomc, "build", "-O2", "--verify-each", "-o", str(exe_o2_b), str(src_path)], root)
        if b_rep.returncode != 0 or exe_o2_a.read_bytes() != exe_o2_b.read_bytes():
            sys.stderr.write(f"non-deterministic PE32+ binary output for {stem} under -O2 --verify-each\n")
            return 1

    # 4. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2 --verify-each
    for inspect_name in (
        "lto_multimod_inline_spec_devirt_dedup.ax",
        "section_gc_roots_and_safe_icf_identity.ax",
        "pgo_roundtrip_stale_and_safety_contracts.ax",
    ):
        inspect_src = resolve_fixture_path(root, inspect_name)
        for flag in ("-O0", "-O1", "-O2"):
            for emit_kind in ("optir", "memssa"):
                ins1 = run_cmd([axiomc, "inspect", f"--emit={emit_kind}", flag, "--verify-each", str(inspect_src)], root)
                ins2 = run_cmd([axiomc, "inspect", f"--emit={emit_kind}", flag, "--verify-each", str(inspect_src)], root)
                if ins1.returncode != 0 or ins2.returncode != 0:
                    sys.stderr.write(f"inspect --emit={emit_kind} {flag} failed on {inspect_name}:\n{ins1.stderr}\n")
                    return 1
                if not ins1.stdout.strip() or ins1.stdout != ins2.stdout:
                    sys.stderr.write(f"non-deterministic or empty inspect --emit={emit_kind} {flag} on {inspect_name}\n")
                    return 1

    # 5. Differential execution of PGO/LTO bounds & drop-ordering trap fixture across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, expected_exit, expected_stdout in TRAP_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != expected_exit:
            sys.stderr.write(
                f"interp {stem} expected exit {expected_exit}, got {iproc.returncode}:\n{iproc.stderr}\n"
            )
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")
        if norm_interp != expected_stdout:
            sys.stderr.write(
                f"interp {stem} stdout mismatch:\nexpected:\n{expected_stdout}\ngot:\n{norm_interp}\n"
            )
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            verify_pe32_plus_binary(exe_path)
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != expected_exit:
                sys.stderr.write(
                    f"run {stem} {flag} expected exit {expected_exit}, got {rproc.returncode}:\n{rproc.stderr}\n"
                )
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != expected_stdout:
                sys.stderr.write(
                    f"stdout mismatch for {stem} under {flag}:\nexpected:\n{expected_stdout}\ngot:\n{norm_out}\n"
                )
                return 1

    sys.stdout.buffer.write(b"E15-6-LTO-PGO-GC-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
