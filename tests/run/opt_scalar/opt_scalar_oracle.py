#!/usr/bin/env python3
"""Oracle test for E15.1 (T603): Unified OptIR scalar optimization engine
(SCCP, InstCombine, GVN/CSE, effect-aware DCE, and CFG pruning) across
--interp, -O0, -O1, and -O2 with --verify-each.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_scalar_probe.ax.in"
EXPECTED_PROBE_STDOUT = (
    "PROBE_INTRINSIC_CONTRACTS=OK\n"
    "PROBE_SCCP_LATTICE_AND_PRUNE=OK\n"
    "PROBE_INST_COMBINE_OVERFLOW_FP=OK\n"
    "PROBE_GVN_CSE_ALIAS_PURE_CALL=OK\n"
    "PROBE_DCE_DEAD_STORE_BARRIERS=OK\n"
    "PROBE_PIPELINE_E2E_PROFILES=OK\n"
    "PROBE_ROUND1_QA_REGRESSIONS=OK\n"
    "PROBE_ALL=OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "sccp_dead_branch_and_phi",
        "sccp_dead_branch_and_phi.ax",
        "SCCP_DIAMOND=123\nSCCP_CAST_SWITCH=354\nSCCP_LOOP_PHI=35\nSCCP_TOTAL=512\n",
    ),
    (
        "gvn_cse_and_alias_forwarding",
        "gvn_cse_and_alias_forwarding.ax",
        "GVN_CSE=604\nNOALIAS_VIEW=130\nRAW_PTR_ALIAS=110\nGVN_TOTAL=844\n",
    ),
    (
        "algebraic_checked_vs_wrapping",
        "algebraic_checked_vs_wrapping.ax",
        "WRAP_OK=4\nWRAP_REASSOC=5032704\nCHECKED_ID=105\nNONZERO_DIV=50\n",
    ),
    (
        "barriers_clone_drop_zeroize",
        "barriers_clone_drop_zeroize.ax",
        "BANNER=Xin chào bảo mật\nCLONE=1\nCLONE=2\nDROP=3\nDROP=2\nZEROED_SUM=0\nDROP=1\nDONE=42\n",
    ),
    (
        "qa_boundary_scalar_clobbers",
        "qa_boundary_scalar_clobbers.ax",
        "QA_BANNER=Xin chào biên vô hướng\nSIBLING_GVN=128\nLOOP_CLOBBER=922\nADDR_ARITH=60\nRAW_INTERVENING=73\nSUBWORD_DIV=32576\nQA_TOTAL=33759\n",
    ),
    (
        "round1_clobber_and_alias_regressions",
        "round1_clobber_and_alias_regressions.ax",
        "R1_CLOBBER=1009\nR1_ADDR_OVERWRITE=55\nR1_SUBWORD_SAFE=50900\nR1_TOTAL=51964\n",
    ),
]

TRAP_FIXTURES: list[str] = [
    "checked_overflow_trap_preserved.ax",
    "subword_div_min_neg1_trap.ax",
    "subword_div_i16_min_neg1_trap.ax",
    "subword_rem_min_neg1_trap.ax",
]
EXPECTED_TRAP_EXIT = 101

SCALAR_PROBE_BLOBS: list[bytes] = [
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
    # Blob 2: GVN/CSE dominator-scoped commutative CSE + clobbered local non-forwarding +
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
    # Blob 3: GVN/CSE EffectCallTable PureCall elimination vs explicit Clone / impure call preservation.
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
    # Blob 4: DCE dead pure chain + Move/Copy elision + MemorySSA DeadStore overwrite & unread local
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


ROUND1_REGRESSION_BLOBS: list[bytes] = [
    # Blob 7 (Finding 1): Subword signed i32/i8 MIN / -1 and MIN % -1 overflow & dead-div/rem trap preservation.
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
    # Blob 8 (Finding 2): Loop-backedge clobber on call-dest local _4 between dominating PureCall and second PureCall.
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
    # Blob 9 (Finding 3): OPT_LOCAL_MEMORY non-OPT_INST_STORE overwrite (both constant-foldable and runtime).
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
    # Blob 10 (Finding 4): Unvalidated PROP_DEAD_STORE provenance across &_2 and copy (*_3) + non-scalar DCE guard.
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
    # Blob 11 (Finding 2b): Loop-backedge clobber on call-dest _1 blocking InstCombine (x +w 1) -w 1 -> copy _1.
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


def assemble_opt_scalar_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    probe_blobs = list(SCALAR_PROBE_BLOBS) + [
        got.UNIT_MIR_SNIPPETS[17],  # Blob 5: full diamond + loop + copy/move + sroa + memphi
        got.UNIT_MIR_SNIPPETS[18],  # Blob 6: unverified MIR (uninitialized _1 read)
    ] + list(ROUND1_REGRESSION_BLOBS)
    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", probe_blobs))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    scalar_modules = list(got.CORE_MODULES) + [("compiler.opt.scalar", "compiler")]
    modules_src = bc.assemble_compiler_modules(scalar_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_scalar" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_scalar_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.scalar engine probe under -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "opt_scalar_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_scalar_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_scalar_probe(root, probe_template), encoding="utf-8")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"opt_scalar_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build opt_scalar_probe {flag} --verify-each failed:\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt_scalar_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt_scalar_probe under {flag}:\n"
                f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, and -O2 (--verify-each)
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
                sys.stderr.write(
                    f"stdout mismatch for {stem} under {flag}:\nexpected:\n{exp_out}\ngot:\n{norm_out}\n"
                )
                return 1

    # 3. Checked-overflow & signed subword MIN / -1 and MIN % -1 trap preservation across --interp, -O0, -O1, -O2
    for trap_idx, trap_fixture in enumerate(TRAP_FIXTURES):
        trap_path = resolve_fixture_path(root, trap_fixture)
        itrap = run_cmd([axiomc, "run", "--interp", str(trap_path)], root, timeout=120)
        if itrap.returncode != EXPECTED_TRAP_EXIT:
            sys.stderr.write(
                f"expected exit {EXPECTED_TRAP_EXIT} for {trap_fixture} under --interp, got {itrap.returncode}\n"
            )
            return 1
        for flag in ("-O0", "-O1", "-O2"):
            trap_exe = tmp_dir / f"checked_trap_{trap_idx}_{flag[1:]}{exe_ext}"
            btrap = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(trap_exe), str(trap_path)], root)
            if btrap.returncode != 0:
                sys.stderr.write(f"build {trap_fixture} {flag} --verify-each failed:\n{btrap.stderr}\n")
                return 1
            rtrap = run_cmd([str(trap_exe)], root)
            if rtrap.returncode != EXPECTED_TRAP_EXIT:
                sys.stderr.write(
                    f"expected exit {EXPECTED_TRAP_EXIT} for {trap_fixture} under {flag}, got {rtrap.returncode}\n"
                )
                return 1

    # 4. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2 (AXS-OPT-013)
    inspect_src = resolve_fixture_path(root, "sccp_dead_branch_and_phi.ax")
    for flag in ("-O0", "-O1", "-O2"):
        o1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        o2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        if o1.returncode != 0 or o2.returncode != 0:
            sys.stderr.write(f"inspect --emit=optir {flag} --verify-each failed:\n{o1.stderr}\n")
            return 1
        if o1.stdout != o2.stdout:
            sys.stderr.write(f"non-deterministic --emit=optir output under {flag}\n")
            return 1
        m1 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        m2 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        if m1.returncode != 0 or m2.returncode != 0:
            sys.stderr.write(f"inspect --emit=memssa {flag} --verify-each failed:\n{m1.stderr}\n")
            return 1
        if m1.stdout != m2.stdout:
            sys.stderr.write(f"non-deterministic --emit=memssa output under {flag}\n")
            return 1

    sys.stdout.buffer.write(b"OPT-SCALAR-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
