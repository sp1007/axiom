#!/usr/bin/env python3
"""End-to-end conformance oracle for E15.1 (T604):
OptIR SSA/MemorySSA, EffectInfo & PassManager contract verification, and scalar
optimization differential conformance across --interp, -O0, -O1, and -O2 --verify-each
(REQ-OPT-037, REQ-OPT-038, REQ-OPT-039, REQ-OPT-040, REQ-OPT-041, REQ-OPT-343).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e15_1_conformance_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "E15_1_STAGE_OPTIR_MEMSSA=OK\n"
    "E15_1_STAGE_EFFECTS_CALLGRAPH=OK\n"
    "E15_1_STAGE_PASSMGR_ROLLBACK=OK\n"
    "E15_1_STAGE_SCALAR_BARRIERS=OK\n"
    "E15_1_PROBE_ALL=OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "memssa_phi_sroa_diamond_loop",
        "memssa_phi_sroa_diamond_loop.ax",
        "MEMSSA_SROA_CFG=368\n",
    ),
    (
        "cfg_ssa_memssa_sccp_gvn",
        "cfg_ssa_memssa_sccp_gvn.ax",
        "CFG_MEMPHI=1293\nSCCP_PRUNE=135\nGVN_ALIAS=464\nCFG_TOTAL=1892\n",
    ),
    (
        "abstraction_erasure_sroa_generics",
        "abstraction_erasure_sroa_generics.ax",
        "SROA_AFFINE=73\nGENERIC_ERASE=172\nENUM_LOOP=100\nABSTRACTION_TOTAL=345\n",
    ),
    (
        "arith_wrapping_vs_checked_identities",
        "arith_wrapping_vs_checked_identities.ax",
        "SIGNED_WRAP=15\nUNSIGNED_WRAP=15\nCHECKED_SAFE=230\nARITH_TOTAL=260\n",
    ),
    (
        "effects_drop_clone_io_barriers_zeroize",
        "effects_drop_clone_io_barriers_zeroize.ax",
        (
            "GREETING=Xin chào thế giới\n"
            "CLONE=1\n"
            "CLONE=2\n"
            "CLONE=3\n"
            "DROP=32\n"
            "DROP=31\n"
            "IO_STEP=1\n"
            "IO_STEP=2\n"
            "ZEROIZE_CHECK=0\n"
            "DROP=22\n"
            "DROP=21\n"
            "DROP=40\n"
            "DROP=41\n"
            "IO_STEP=3\n"
            "DROP=10\n"
            "EFFECTS_DONE=69\n"
        ),
    ),
]

TRAP_FIXTURES: list[str] = [
    "trap_checked_add_overflow_cancel_i32.ax",
    "trap_checked_dead_overflow_dce_i64.ax",
    "trap_checked_sub_underflow_u64.ax",
    "trap_checked_mul_overflow_i16.ax",
    "trap_div_by_zero_self_div_i32.ax",
    "trap_signed_min_div_neg1_i8.ax",
    "trap_signed_min_rem_neg1_i64.ax",
]
EXPECTED_TRAP_EXIT = 101

PROBE_MIR_BLOBS_HEAD: list[bytes] = [
    # Blob 0: SCCP Wegman-Zadeck diamond + unexecuted edge phi + dead branch pruning +
    # checked overflow / div-by-zero non-folding + black_box barrier pinning.
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let mut _3: type#8;\n"
        b"    let _4: type#4;\n"
        b"    let _5: type#6;\n"
        b"    let _6: type#6;\n"
        b"    let _7: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 10: type#8;\n"
        b"        _5 = const 127: type#6 + const 1: type#6;\n"
        b"        _6 = const 10: type#6 / const 0: type#6;\n"
        b"        _7 = const 55: type#8;\n"
        b"        switchInt(copy _1) -> [0: bb2, 10: bb1, otherwise: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 40: type#8;\n"
        b"        _3 = const 0: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _2 = const 999: type#8;\n"
        b"        _3 = const 1: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _4 = copy _3 == const 0: type#8;\n"
        b"        switchInt(move _4) -> [0: bb5, otherwise: bb4];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _0 = copy _2 + const 2: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = const 777: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 1: InstCombine canonicalization, wrapping (x +w y) -w y -> x & reassociation,
    # checked (x + y) - y fail-closed rejection, NonZero x / x gating, and fp hazard rejection.
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let mut _3: type#8;\n"
        b"    let mut _4: type#8;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#8;\n"
        b"    let _9: type#8;\n"
        b"    let _10: type#8;\n"
        b"    let _11: type#8;\n"
        b"    let _12: type#8;\n"
        b"    let _13: type#8;\n"
        b"    let _14: type#8;\n"
        b"    let _15: type#4;\n"
        b"    bb0: {\n"
        b"        _15 = const true;\n"
        b"        switchInt(copy _15) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _1 = const 0: type#8;\n"
        b"        _2 = const 1: type#8;\n"
        b"        _3 = const 2: type#8;\n"
        b"        _4 = const 5: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _1 = const 2147483647: type#8;\n"
        b"        _2 = const 10: type#8;\n"
        b"        _3 = const 20: type#8;\n"
        b"        _4 = const 10: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _5 = const 0: type#8 + copy _1;\n"
        b"        _6 = wrapping_add(copy _1, copy _2);\n"
        b"        _7 = wrapping_sub(copy _6, copy _2);\n"
        b"        _8 = copy _1 + copy _2;\n"
        b"        _9 = copy _8 - copy _2;\n"
        b"        _10 = copy _1 / copy _1;\n"
        b"        _11 = copy _4 / copy _4;\n"
        b"        _12 = wrapping_add(copy _1, const 10: type#8);\n"
        b"        _13 = wrapping_add(copy _12, const 22: type#8);\n"
        b"        _14 = copy _3 + const 0: type#8;\n"
        b"        _0 = wrapping_add(copy _7, copy _13);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 2: Dominator-scoped commutative CSE + clobbered local non-forwarding +
    # NoAlias stack/view store-to-load forwarding across disjoint writes.
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let mut _3: type#8;\n"
        b"    let _4: type#8;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#8;\n"
        b"    let mut _7: type#8;\n"
        b"    let mut _8: type#8;\n"
        b"    let _9: type#1;\n"
        b"    let _10: type#1;\n"
        b"    let _11: type#8;\n"
        b"    let _12: type#8;\n"
        b"    let _13: type#4;\n"
        b"    let _14: type#8;\n"
        b"    bb0: {\n"
        b"        _13 = const true;\n"
        b"        switchInt(copy _13) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _1 = const 3: type#8;\n"
        b"        _2 = const 12: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _1 = const 5: type#8;\n"
        b"        _2 = const 9: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _3 = copy _1 | copy _2;\n"
        b"        _3 = const 999: type#8;\n"
        b"        _4 = copy _2 | copy _1;\n"
        b"        _5 = copy _1 ^ copy _2;\n"
        b"        _6 = copy _2 ^ copy _1;\n"
        b"        _7 = const 77: type#8;\n"
        b"        _8 = const 88: type#8;\n"
        b"        _11 = copy _7;\n"
        b"        _9 = &_7;\n"
        b"        _10 = &_8;\n"
        b"        _12 = wrapping_add(copy _3, copy _4);\n"
        b"        _14 = wrapping_add(copy _6, copy _11);\n"
        b"        _0 = wrapping_add(copy _12, copy _14);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 3: EffectCallTable PureCall elimination vs explicit Clone / impure call preservation.
    (
        b"mir_body {\n"
        b"    type 20 = fn(type#8) -> type#8;\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#20;\n"
        b"    let mut _3: type#20;\n"
        b"    let _4: type#8;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 7: type#8;\n"
        b"        _2 = const 1: type#20;\n"
        b"        _3 = const 2: type#20;\n"
        b"        _4 = copy _2(copy _1) -> [return: bb1, unwind: bb5];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _5 = copy _2(copy _1) -> [return: bb2, unwind: bb5];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _6 = copy _3(copy _1) -> [return: bb3, unwind: bb5];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _7 = copy _3(copy _1) -> [return: bb4, unwind: bb5];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _0 = wrapping_add(copy _5, copy _7);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 4: DCE dead pure chain + Move/Copy elision (REQ-OPT-039..040) + MemorySSA DeadStore
    # elimination + strict retention of black_box, zeroize, volatile_load, volatile_store, atomic.
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#8;\n"
        b"    let mut _5: type#8;\n"
        b"    let _6: type#1;\n"
        b"    let mut _7: type#8;\n"
        b"    let _8: type#8;\n"
        b"    let _9: type#8;\n"
        b"    let _10: type#8;\n"
        b"    let _11: type#8;\n"
        b"    let _12: type#8;\n"
        b"    let _13: type#4;\n"
        b"    bb0: {\n"
        b"        _13 = const true;\n"
        b"        switchInt(copy _13) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _1 = const 10: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _1 = const 20: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        StorageLive(_2);\n"
        b"        _2 = copy _1;\n"
        b"        _3 = move _2;\n"
        b"        _4 = wrapping_add(copy _3, const 10: type#8);\n"
        b"        StorageDead(_2);\n"
        b"        _5 = const 100: type#8;\n"
        b"        _5 = const 200: type#8;\n"
        b"        _6 = &_5;\n"
        b"        _7 = const 333: type#8;\n"
        b"        _8 = const 11: type#8;\n"
        b"        _9 = const 22: type#8;\n"
        b"        _10 = const 33: type#8;\n"
        b"        _11 = const 44: type#8;\n"
        b"        _12 = const 55: type#8;\n"
        b"        _0 = copy _5;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
]

PROBE_MIR_BLOBS_TAIL: list[bytes] = [
    # Blob 7: Subword signed i32/i8 MIN / -1 and MIN % -1 overflow & dead-div/rem trap preservation.
    (
        b"mir_body {\n"
        b"    type 20 = fn() -> type#8;\n"
        b"    type 21 = fn() -> type#6;\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#6;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#4;\n"
        b"    let _5: type#4;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#6;\n"
        b"    let _8: type#4;\n"
        b"    let _9: type#6;\n"
        b"    let mut _10: type#20;\n"
        b"    let mut _11: type#21;\n"
        b"    bb0: {\n"
        b"        _10 = const 1: type#20;\n"
        b"        _11 = const 2: type#21;\n"
        b"        _1 = copy _10() -> [return: bb1, unwind: bb4];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = copy _11() -> [return: bb2, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _3 = -const 1: type#8;\n"
        b"        _4 = overflows(copy _1 / copy _3);\n"
        b"        _5 = !copy _4;\n"
        b"        _6 = copy _1 % copy _3;\n"
        b"        _7 = -const 1: type#6;\n"
        b"        _8 = overflows(copy _2 / copy _7);\n"
        b"        _9 = copy _2 / copy _7;\n"
        b"        assert(copy _5 == true, \"arithmetic overflow\") -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        assert(copy _8 == false, \"i8 div overflow\") -> [return: bb5, unwind: bb4];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 8: Loop-backedge clobber on call-dest local _4 between dominating PureCall and second PureCall.
    (
        b"mir_body {\n"
        b"    type 20 = fn(type#8) -> type#8;\n"
        b"    type 21 = fn() -> type#8;\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#20;\n"
        b"    let mut _3: type#8;\n"
        b"    let mut _4: type#8;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#4;\n"
        b"    let mut _7: type#21;\n"
        b"    bb0: {\n"
        b"        _1 = const 10: type#8;\n"
        b"        _2 = const 1: type#20;\n"
        b"        _7 = const 2: type#21;\n"
        b"        _3 = copy _7() -> [return: bb1, unwind: bb6];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = copy _2(copy _1) -> [return: bb2, unwind: bb6];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _6 = copy _3 > const 0: type#8;\n"
        b"        switchInt(move _6) -> [0: bb4, otherwise: bb3];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _4 = const 999: type#8;\n"
        b"        _3 = wrapping_sub(copy _3, const 1: type#8);\n"
        b"        goto -> bb2;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _5 = copy _2(copy _1) -> [return: bb5, unwind: bb6];\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = wrapping_add(copy _4, copy _5);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 9: OPT_LOCAL_MEMORY non-OPT_INST_STORE overwrite (constant-foldable & runtime).
    (
        b"mir_body {\n"
        b"    type 20 = fn() -> type#8;\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#1;\n"
        b"    let mut _4: type#8;\n"
        b"    let _5: type#1;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    let mut _8: type#20;\n"
        b"    bb0: {\n"
        b"        _8 = const 1: type#20;\n"
        b"        _1 = copy _8() -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 10: type#8;\n"
        b"        _3 = &_2;\n"
        b"        _2 = wrapping_add(const 2: type#8, const 3: type#8);\n"
        b"        _6 = copy _2;\n"
        b"        _4 = const 20: type#8;\n"
        b"        _5 = &_4;\n"
        b"        _4 = wrapping_add(copy _1, const 5: type#8);\n"
        b"        _7 = copy _4;\n"
        b"        _0 = wrapping_add(copy _6, copy _7);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 10: Unvalidated PROP_DEAD_STORE provenance across &_2 and copy (*_3) + non-scalar DCE guard.
    (
        b"mir_body {\n"
        b"    type 20 = fn() -> type#8;\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#1;\n"
        b"    let mut _4: type#20;\n"
        b"    bb0: {\n"
        b"        _4 = const 1: type#20;\n"
        b"        _1 = copy _4() -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 10: type#8;\n"
        b"        _3 = &_2;\n"
        b"        _2 = wrapping_add(copy _1, const 5: type#8);\n"
        b"        _0 = copy (*_3);\n"
        b"        _2 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 11: Loop-backedge clobber on call-dest _1 blocking InstCombine (x +w 1) -w 1 -> copy _1.
    (
        b"mir_body {\n"
        b"    type 20 = fn() -> type#8;\n"
        b"    let mut _0: type#8;\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#8;\n"
        b"    let _5: type#4;\n"
        b"    let mut _6: type#20;\n"
        b"    let mut _7: type#20;\n"
        b"    bb0: {\n"
        b"        _6 = const 1: type#20;\n"
        b"        _7 = const 2: type#20;\n"
        b"        _1 = copy _6() -> [return: bb1, unwind: bb5];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = wrapping_add(copy _1, const 1: type#8);\n"
        b"        _2 = copy _7() -> [return: bb2, unwind: bb5];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _5 = copy _2 > const 0: type#8;\n"
        b"        switchInt(move _5) -> [0: bb4, otherwise: bb3];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _1 = const 777: type#8;\n"
        b"        _2 = wrapping_sub(copy _2, const 1: type#8);\n"
        b"        goto -> bb2;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _4 = wrapping_sub(copy _3, const 1: type#8);\n"
        b"        _0 = copy _4;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
]

UNVERIFIED_MIR_TEXT = (
    "mir_body {\n"
    "    let mut _0: type#8;\n"
    "    let _1: type#8;\n"
    "    bb0: {\n"
    "        _0 = copy _1;\n"
    "        return;\n"
    "    }\n"
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
    """REQ-OPT-037, REQ-OPT-038: Verify native AOT standalone machine binary (PE/ELF/Mach-O), no VM."""
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
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_1_optir_ssa" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def assemble_conformance_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    probe_blobs = (
        list(PROBE_MIR_BLOBS_HEAD)
        + [
            got.UNIT_MIR_SNIPPETS[17],  # Blob 5: diamond + loop + copy/move + sroa + memphi
            got.UNIT_MIR_SNIPPETS[18],  # Blob 6: unverified MIR (uninitialized _1 read)
        ]
        + list(PROBE_MIR_BLOBS_TAIL)
    )
    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", probe_blobs))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    e15_1_modules = list(got.CORE_MODULES) + [("compiler.opt.scalar", "compiler")]
    modules_src = bc.assemble_compiler_modules(e15_1_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e15_1_conformance_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute live E15.1 OptIR + Effects + PassManager + Scalar probe
    #    as standalone AOT binaries across -O0, -O1, and -O2 --verify-each.
    probe_template = resolve_conformance_path(root, "e15_1_conformance_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e15_1_conformance_probe_bundle.ax"
    probe_bundle.write_text(assemble_conformance_probe(root, probe_template), encoding="utf-8")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"e15_1_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build e15_1_probe {flag} --verify-each failed:\n{bproc.stderr}\n")
            return 1
        ok_bin, bin_err = verify_aot_native_binary(probe_exe)
        if not ok_bin:
            sys.stderr.write(f"{bin_err}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e15_1_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e15_1_probe under {flag}:\n"
                f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive conformance fixtures across
    #    --interp, -O0, -O1, and -O2 (all with --verify-each) (REQ-OPT-343).
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
            trap_exe = tmp_dir / f"e15_1_trap_{trap_idx}_{flag[1:]}{exe_ext}"
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

    # 4. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2 --verify-each
    #    plus structural token verification and unverified-MIR rejection.
    for inspect_name in ("memssa_phi_sroa_diamond_loop.ax",):
        inspect_src = resolve_conformance_path(root, inspect_name)
        for flag in ("-O0", "-O1", "-O2"):
            o1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
            o2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
            if o1.returncode != 0 or o2.returncode != 0:
                sys.stderr.write(f"inspect --emit=optir {inspect_name} {flag} failed:\n{o1.stderr}\n")
                return 1
            if o1.stdout != o2.stdout:
                sys.stderr.write(f"non-deterministic --emit=optir for {inspect_name} under {flag}\n")
                return 1
            for tok in ("optir_body {", "idom: bb0", "df: [", "phi(", "proof #"):
                if tok not in o1.stdout:
                    sys.stderr.write(f"missing '{tok}' in --emit=optir for {inspect_name} under {flag}\n")
                    return 1

            m1 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
            m2 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
            if m1.returncode != 0 or m2.returncode != 0:
                sys.stderr.write(f"inspect --emit=memssa {inspect_name} {flag} failed:\n{m1.stderr}\n")
                return 1
            if m1.stdout != m2.stdout:
                sys.stderr.write(f"non-deterministic --emit=memssa for {inspect_name} under {flag}\n")
                return 1
            for tok in ("memssa_body {", "mem0 = LiveOnEntry", "MemoryPhi(", "MemoryDef(", "MemoryUse("):
                if tok not in m1.stdout:
                    sys.stderr.write(f"missing '{tok}' in --emit=memssa for {inspect_name} under {flag}\n")
                    return 1

    bad_mir_path = tmp_dir / "unverified_read.mir"
    bad_mir_path.write_text(UNVERIFIED_MIR_TEXT, encoding="utf-8")
    for emit_flag in ("--emit=optir", "--emit=memssa"):
        bad_res = run_cmd([axiomc, "inspect", emit_flag, "--verify-each", str(bad_mir_path)], root)
        if bad_res.returncode == 0 or bad_res.stdout.strip() != "":
            sys.stderr.write(
                f"expected unverified MIR rejection for {emit_flag}, got rc={bad_res.returncode}, stdout={bad_res.stdout!r}\n"
            )
            return 1

    sys.stdout.buffer.write(b"E15-1-OPTIR-SSA-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
