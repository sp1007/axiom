#!/usr/bin/env python3
"""Oracle test for E15.2 (T606): Capability-aware AliasInfo, provenance disjointness,
zero-copy pinning verification, and MemorySSA store-to-load forwarding / RLE / DSE /
memmove->memcpy / memset optimization across --interp, -O0, -O1, and -O2 --verify-each.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_alias_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_ALIAS_CAPABILITY_LATTICE=OK\n"
    "PROBE_FORWARDING_RLE_AND_DSE=OK\n"
    "PROBE_BARRIERS_ZEROCOPY_INTRINSICS=OK\n"
    "PROBE_QA_ROUND1_REGRESSIONS=OK\n"
    "PROBE_ALL=OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "cap_mut_view_forwarding_rle_dse",
        "cap_mut_view_forwarding_rle_dse.ax",
        "ALIAS_BANNER=Xin chào phân tích bí danh\nMUT_VIEW_FWD=141\nVIEW_RLE=230\nFIELD_SLICE=149\nALIAS_TOTAL=520\n",
    ),
    (
        "raw_ptr_volatile_atomic_barriers",
        "raw_ptr_volatile_atomic_barriers.ax",
        "BARRIER_BANNER=Xin chào bộ nhớ an toàn\nRAW_ALIAS=77\nPTR_COPY_ADD=176\nDROP=20\nZERO_SUM=0\nBARRIER_TOTAL=253\nDROP=10\n",
    ),
    (
        "loop_backedge_and_partial_alias_clobbers",
        "loop_backedge_and_partial_alias_clobbers.ax",
        "CLOBBER_BANNER=Xin chào kiểm chứng biên\nLOOP_BACKEDGE=125\nPARTIAL_STRUCT=55\nSEQ_REBORROW=64\nMULTI_ORIGIN=1030\nCLOBBER_TOTAL=1274\n",
    ),
    (
        "qa_boundary_alias_clobbers",
        "qa_boundary_alias_clobbers.ax",
        "QA_ALIAS_BANNER=Xin chào biên bí danh\nINTERIOR_DEREF=176\nREBORROW_LOOP=141\nINDIRECT_MUT=443\nENUM_PAYLOAD=124\nQA_ALIAS_TOTAL=884\n",
    ),
]

# Custom types registered by `probe_init_alias_thir`:
#   type#8  = i32, type#11 = u8, type#15 = usize, type#2 = unit, type#4 = bool
#   type#17 = view<i32>, type#18 = mut_view<i32>, type#19 = *mut i32
#   type#20 = struct Pair { i32, i32 }, type#21 = mut_view<Pair>, type#22 = view<Pair>
#   type#23 = [4]i32
#   type#24 = TY_BUILTIN_PTR_COPY<i32>
#   type#25 = TY_BUILTIN_PTR_COPY_NONOVERLAPPING<i32>
#   type#26 = TY_BUILTIN_PTR_WRITE_BYTES<i32>
#   type#27 = TY_BUILTIN_ADDRESS_OF_MUT<i32>
#   type#28 = fn(type#8) -> type#8
#   type#29 = *const i32

ALIAS_PROBE_BLOBS: list[bytes] = [
    # Blob 0: Lattice & projection disjointness:
    # _1: mut_view<i32> (arg), _2: mut_view<i32> (arg), _3: view<Pair> (arg), _4: mut_view<Pair> (arg),
    # _5: usize (arg, dynamic), _6: Pair, _7: [4]i32, _8: usize=0, _9: usize=2, _10: *mut i32 (int2ptr),
    # _11: view<i32>, _12: view<i32>.
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#18; // arg\n"
        b"    let _3: type#22; // arg\n"
        b"    let _4: type#21; // arg\n"
        b"    let _5: type#15; // arg\n"
        b"    let mut _6: type#20;\n"
        b"    let mut _7: type#23;\n"
        b"    let _8: type#15;\n"
        b"    let _9: type#15;\n"
        b"    let _10: type#19;\n"
        b"    let _11: type#17;\n"
        b"    let _12: type#17;\n"
        b"    let mut _13: type#8;\n"
        b"    bb0: {\n"
        b"        _6.0 = const 10: type#8;\n"
        b"        _6.1 = const 20: type#8;\n"
        b"        _7 = [const 1: type#8; 4];\n"
        b"        _8 = const 0: type#15;\n"
        b"        _9 = const 2: type#15;\n"
        b"        _10 = const 4096: type#15 as type#19 (IntToPtr);\n"
        b"        _13 = const 7: type#8;\n"
        b"        _11 = &_13;\n"
        b"        _12 = &_13;\n"
        b"        (*_1) = const 3: type#8;\n"
        b"        (*_2) = const 4: type#8;\n"
        b"        _0 = copy (*_1);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 1: Store-to-load forwarding + `view<Pair>` RLE + overwrite DSE + dead NoEscape local DSE:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#18; // arg\n"
        b"    let _3: type#22;\n"
        b"    let _4: type#21;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    let mut _8: type#8;\n"
        b"    let _9: type#17;\n"
        b"    let mut _10: type#23;\n"
        b"    let _11: type#8;\n"
        b"    let _12: type#8;\n"
        b"    let mut _13: type#20;\n"
        b"    let mut _14: type#20;\n"
        b"    let _15: type#4;\n"
        b"    bb0: {\n"
        b"        _15 = const true;\n"
        b"        switchInt(copy _15) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _13.0 = const 20: type#8;\n"
        b"        _13.1 = const 30: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _13.0 = const 40: type#8;\n"
        b"        _13.1 = const 50: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _3 = &_13;\n"
        b"        _14.0 = const 1: type#8;\n"
        b"        _14.1 = const 2: type#8;\n"
        b"        _4 = &mut _14;\n"
        b"        (*_1) = const 10: type#8;\n"
        b"        (*_1) = const 42: type#8;\n"
        b"        (*_2) = const 99: type#8;\n"
        b"        _5 = copy (*_1);\n"
        b"        _6 = copy (*_3).0;\n"
        b"        (*_4).0 = const 77: type#8;\n"
        b"        _7 = copy (*_3).0;\n"
        b"        StorageLive(_10);\n"
        b"        _10 = [const 111: type#8; 4];\n"
        b"        StorageDead(_10);\n"
        b"        _8 = const 5: type#8;\n"
        b"        _9 = &_8;\n"
        b"        _12 = copy (*_9);\n"
        b"        _11 = wrapping_add(copy _5, copy _7);\n"
        b"        _0 = wrapping_add(copy _11, copy _12);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 2: Volatile, Atomic, Zeroize, BlackBox, FFI Call, and Zero-Copy Pin barriers:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#18; // arg\n"
        b"    let _3: type#18; // arg\n"
        b"    let _4: type#17;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#28;\n"
        b"    let _9: type#8;\n"
        b"    let _10: type#8;\n"
        b"    let _11: type#8;\n"
        b"    let mut _12: type#8;\n"
        b"    bb0: {\n"
        b"        (*_1) = const 11: type#8;\n"
        b"        _9 = copy (*_1);\n"
        b"        (*_2) = const 22: type#8;\n"
        b"        _5 = copy (*_2);\n"
        b"        _6 = copy (*_2);\n"
        b"        (*_2) = const 0: type#8;\n"
        b"        _7 = const 55: type#8;\n"
        b"        (*_3) = const 300: type#8;\n"
        b"        (*_3) = const 400: type#8;\n"
        b"        _12 = const 7: type#8;\n"
        b"        _4 = &_12;\n"
        b"        _8 = const 1: type#28;\n"
        b"        _10 = copy _8(copy _7) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _11 = copy (*_3);\n"
        b"        _0 = wrapping_add(copy _10, copy _11);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 3: `ptr_copy` (`memmove`) -> `ptr_copy_nonoverlapping` (`memcpy`) on distinct stack locals
    # + `ptr_write_bytes` (`memset` zero-init):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#19;\n"
        b"    let _4: type#19;\n"
        b"    let _5: type#29;\n"
        b"    let _6: type#27;\n"
        b"    let _7: type#24;\n"
        b"    let _8: type#26;\n"
        b"    let _9: type#2;\n"
        b"    bb0: {\n"
        b"        _1 = const 90: type#8;\n"
        b"        _2 = const 0: type#8;\n"
        b"        _6 = const 0: type#27;\n"
        b"        _3 = copy _6(copy _1) -> [return: bb1, unwind: bb4];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = copy _6(copy _2) -> [return: bb2, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _5 = copy _3 as type#29 (PtrToPtr);\n"
        b"        _7 = const 0: type#24;\n"
        b"        _9 = copy _7(copy _5, copy _4, const 1: type#15) -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _8 = const 0: type#26;\n"
        b"        _9 = copy _8(copy _4, const 0: type#11, const 1: type#15) -> [return: bb5, unwind: bb4];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 4: Loop backedge clobber (`bb0 -> bb1 -> bb2 -> bb1`):
    # `(*_1)` is initialized in `bb0`, read in `bb1`, and mutated in `bb2` before jumping back to `bb1`!
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#4;\n"
        b"    bb0: {\n"
        b"        (*_1) = const 5: type#8;\n"
        b"        _2 = const 3: type#8;\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy (*_1);\n"
        b"        _4 = copy _2 > const 0: type#8;\n"
        b"        switchInt(copy _4) -> [0: bb3, otherwise: bb2];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        (*_1) = wrapping_add(copy _3, const 10: type#8);\n"
        b"        _2 = wrapping_sub(copy _2, const 1: type#8);\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = copy _3;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 5 (QA Finding 1a): Interior capability deref `((*_3).0) = 77` on `Sink { mv: mut_view<i32> }`
    # must clobber `(*_1)` and MUST NOT be DSE'd as an unescaped stack-local store!
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#18;\n"
        b"    let mut _3: type#30;\n"
        b"    bb0: {\n"
        b"        (*_1) = const 10: type#8;\n"
        b"        _2 = &mut (*_1);\n"
        b"        _3 = aggregate(variant#0, [move _2]);\n"
        b"        ((*_3).0) = const 77: type#8;\n"
        b"        _0 = copy (*_1);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 6 (QA Finding 1b): Interior raw-ptr deref `((*_3).0)` on `PtrWrap { p: *mut i32 }` +
    # field pointer update `_3.0 = copy _2` must NOT forward stale `55` or DSE `_3.0 = copy _2` / `((*_3).0) = 99`!
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#19; // arg\n"
        b"    let _2: type#19; // arg\n"
        b"    let mut _3: type#31;\n"
        b"    let _4: type#8;\n"
        b"    bb0: {\n"
        b"        (*_2) = const 11: type#8;\n"
        b"        _3 = aggregate(variant#0, [copy _1]);\n"
        b"        ((*_3).0) = const 55: type#8;\n"
        b"        _3.0 = copy _2;\n"
        b"        _4 = copy ((*_3).0);\n"
        b"        ((*_3).0) = const 99: type#8;\n"
        b"        _0 = wrapping_add(copy _4, copy (*_2));\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 7 (QA Finding 2): `mut_view` 1-hop & 2-hop reborrow chain (`_3 = &mut (*_1)`, `_4 = &mut (*_3)`),
    # sibling field sub-borrows (`_5 = &mut (*_2).0`, `_6 = &mut (*_2).1`), and sequential local borrows (`_8`, `_9`).
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#21; // arg\n"
        b"    let _3: type#18;\n"
        b"    let _4: type#18;\n"
        b"    let _5: type#18;\n"
        b"    let _6: type#18;\n"
        b"    let mut _7: type#8;\n"
        b"    let _8: type#18;\n"
        b"    let _9: type#18;\n"
        b"    let _10: type#8;\n"
        b"    bb0: {\n"
        b"        (*_1) = const 10: type#8;\n"
        b"        _3 = &mut (*_1);\n"
        b"        _4 = &mut (*_3);\n"
        b"        (*_4) = const 99: type#8;\n"
        b"        _5 = &mut (*_2).0;\n"
        b"        _6 = &mut (*_2).1;\n"
        b"        (*_5) = const 3: type#8;\n"
        b"        (*_6) = const 4: type#8;\n"
        b"        _7 = const 20: type#8;\n"
        b"        _8 = &mut _7;\n"
        b"        (*_8) = const 21: type#8;\n"
        b"        StorageDead(_8);\n"
        b"        _9 = &mut _7;\n"
        b"        (*_9) = const 22: type#8;\n"
        b"        _10 = copy (*_1);\n"
        b"        _0 = wrapping_add(copy _10, copy (*_5));\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 8 (QA Findings 3 & 4): Indirect index mutation via `_3 = &mut _2; (*_3) = 1` +
    # enum `MIR_PROJ_DOWNCAST` overlapping variants `((_4 as variant#0)).0` vs `((_4 as variant#1)).0`
    # and same-variant sibling fields `((_5 as variant#0)).0` vs `((_5 as variant#0)).1`.
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#23;\n"
        b"    let mut _2: type#15;\n"
        b"    let _3: type#32;\n"
        b"    let mut _4: type#33;\n"
        b"    let mut _5: type#34;\n"
        b"    let _6: type#15;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#8;\n"
        b"    let _9: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = [const 0: type#8; 4];\n"
        b"        _2 = const 0: type#15;\n"
        b"        _1[_2] = const 111: type#8;\n"
        b"        _3 = &mut _2;\n"
        b"        (*_3) = const 1: type#15;\n"
        b"        _1[_2] = const 222: type#8;\n"
        b"        _4 = aggregate(variant#0, [const 41: type#8]);\n"
        b"        _7 = const 44: type#8;\n"
        b"        _7 = const 88: type#8;\n"
        b"        _7 = copy _8;\n"
        b"        _5 = aggregate(variant#0, [const 5: type#8, const 6: type#8]);\n"
        b"        _8 = copy _7;\n"
        b"        _6 = const 0: type#15;\n"
        b"        _9 = wrapping_add(copy _7, copy _8);\n"
        b"        _0 = wrapping_add(copy _9, copy _1[_6]);\n"
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


def assemble_opt_alias_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", ALIAS_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    alias_modules = list(got.CORE_MODULES) + [
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(alias_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_alias" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_alias_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.alias + compiler.opt.memopt probe under -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "opt_alias_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_alias_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_alias_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"opt_alias_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build opt_alias_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt_alias_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt_alias_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive/negative/boundary fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")
        if norm_interp != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp:\nexpected:\n{exp_out}\ngot:\n{norm_interp}\n")
            return 1

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
            if norm_out != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}:\nexpected:\n{exp_out}\ngot:\n{norm_out}\n")
                return 1

    # 3. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2
    inspect_src = resolve_fixture_path(root, "cap_mut_view_forwarding_rle_dse.ax")
    for flag in ("-O0", "-O1", "-O2"):
        o1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        o2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        if o1.returncode != 0 or o2.returncode != 0 or o1.stdout != o2.stdout:
            sys.stderr.write(f"inspect --emit=optir {flag} failed or non-deterministic:\n{o1.stderr}\n")
            return 1
        m1 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        m2 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        if m1.returncode != 0 or m2.returncode != 0 or m1.stdout != m2.stdout:
            sys.stderr.write(f"inspect --emit=memssa {flag} failed or non-deterministic:\n{m1.stderr}\n")
            return 1

    sys.stdout.buffer.write(b"OPT-ALIAS-MEMOPT-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
