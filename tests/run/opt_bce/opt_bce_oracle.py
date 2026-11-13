#!/usr/bin/env python3
"""Oracle test for E15.3 (T610): Natural loop discovery, irreducible SCC detection,
canonical loop simplification & LCSSA (`opt_loop_simplify`), MemorySSA/AliasInfo/EffectInfo
loop invariance & dependence queries, overflow-faithful Scalar Evolution (`SCEV`), and
RangeInfo / Bounds-Check Elimination (`opt_bce`) across --interp, -O0, -O1, and -O2 --verify-each.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_bce_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_LOOP_DISCOVERY_AND_SIMPLIFY=OK\n"
    "PROBE_SCEV_INVARIANCE_AND_DEPENDENCE=OK\n"
    "PROBE_FRONTEND_LOWERED_BCE_POSITIVE=OK\n"
    "PROBE_FRONTEND_LOWERED_BCE_NEGATIVE=OK\n"
    "PROBE_ALL=OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "canonical_loops_and_bce_positive",
        "canonical_loops_and_bce_positive.ax",
        "BCE_BANNER=Xin chào tối ưu hóa biên vòng lặp\nITER_DROP=1\nITER_DROP=11\nARRAY_MASK=272\nSLICE_ZIP=400\nSIGNED_SUB=219\nNESTED_DROP=92\nBCE_TOTAL=983\n",
    ),
    (
        "vec_bounds_and_descending_loops",
        "vec_bounds_and_descending_loops.ax",
        "VEC_BANNER=Xin chào kiểm tra biên động\nVEC_SUM=165\nDESC_SUM=90\nCANON_CFG=150\nVEC_TOTAL=405\n",
    ),
    (
        "qa_round1_soundness_regressions",
        "qa_round1_soundness_regressions.ax",
        "QA_R1_BANNER=Kiểm chứng tính đúng đắn vòng 1\nSROA_VEC=100\nSAFE_BRANCH=30\nSUBSLICE_OVERLAP=40\nPOST_INC=19\nREBOUND_SLICE=14\nCOND_REBIND=95\nLOOP_REBIND=95\nCOND_IDX_DEP=420\nDISC_LOOP=13\nAGG_CLOBBER=427\nQA_R1_TOTAL=1253\n",
    ),
]

NEGATIVE_PANIC_FIXTURES: list[tuple[str, str]] = [
    ("oob_dynamic_index_panic", "oob_dynamic_index_panic.ax"),
    ("oob_signed_negative_index_panic", "oob_signed_negative_index_panic.ax"),
    ("oob_wrapping_stride_panic", "oob_wrapping_stride_panic.ax"),
    ("oob_indirect_mut_index_panic", "oob_indirect_mut_index_panic.ax"),
    ("oob_vec_shrink_in_loop_panic", "oob_vec_shrink_in_loop_panic.ax"),
    ("oob_sroa_vec_branch_shrink_panic", "oob_sroa_vec_branch_shrink_panic.ax"),
    ("oob_sroa_vec_loop_shrink_panic", "oob_sroa_vec_loop_shrink_panic.ax"),
]

BCE_PROBE_BLOBS: list[bytes] = [
    # Blob 0: Virtual file path for `session_parse_virtual_file`
    b"probe_bce_src.ax",

    # Blob 1: Positive Axiom source lowered via `mir_build_fn` -> `bce_optimize_mir_body`
    (
        b"@intrinsic fn assert(c: bool) {}\n"
        b"\n"
        b"struct Vec<T> {\n"
        b"    ptr: *mut T,\n"
        b"    len: usize,\n"
        b"    cap: usize,\n"
        b"}\n"
        b"\n"
        b"fn pos_fixed_array(arr: [16]i32) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 16 {\n"
        b"        acc = acc + arr[i] + arr[(i * 3 + 1) & 15];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn pos_slice_loop(s: view<[i32]>) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < len(s) {\n"
        b"        acc = acc + s[i];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn pos_zip_slices(a: view<[i32]>, b: view<[i32]>, dst: mut_view<[i32]>) -> usize {\n"
        b"    let mut i: usize = 0;\n"
        b"    while i < len(a) && i < len(b) && i < len(dst) {\n"
        b"        dst[i] = a[i] + b[i];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    i\n"
        b"}\n"
        b"\n"
        b"fn pos_vec_read(v: view<Vec<i32>>) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < v.len {\n"
        b"        assert(i < v.len);\n"
        b"        let elem: i32 = unsafe { *(v.ptr + i) };\n"
        b"        acc = acc + elem;\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn pos_signed_guarded(s: view<[i32]>) -> i32 {\n"
        b"    let mut i: i32 = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i >= 0 && i < 4 && (i as usize) < len(s) {\n"
        b"        acc = acc + s[i as usize];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn pos_descending_slice(s: view<[i32]>) -> i32 {\n"
        b"    let mut k: usize = len(s);\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while k > 0 {\n"
        b"        k = k - 1;\n"
        b"        acc = acc + s[k];\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn pos_subslice_disjoint(mv: mut_view<[i32]>, mid: usize) -> usize {\n"
        b"    let n: usize = len(mv);\n"
        b"    if mid <= n {\n"
        b"        let left = mv[0..mid];\n"
        b"        let right = mv[mid..n];\n"
        b"        let mut u: usize = 0;\n"
        b"        while u < len(left) && u < len(right) {\n"
        b"            left[u] = 1;\n"
        b"            right[u] = 2;\n"
        b"            u = u + 1;\n"
        b"        }\n"
        b"        return u;\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn pos_sroa_vec_read(v: Vec<i32>) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < v.len {\n"
        b"        assert(i < v.len);\n"
        b"        let elem: i32 = unsafe { *(v.ptr + i) };\n"
        b"        acc = acc + elem;\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
    ),

    # Blob 2: Negative Axiom source lowered via `mir_build_fn` -> ZERO eliminations allowed!
    (
        b"@intrinsic fn assert(c: bool) {}\n"
        b"@intrinsic fn wrapping_add_usize(a: usize, b: usize) -> usize { 0 }\n"
        b"@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }\n"
        b"\n"
        b"struct Vec<T> {\n"
        b"    ptr: *mut T,\n"
        b"    len: usize,\n"
        b"    cap: usize,\n"
        b"}\n"
        b"\n"
        b"fn neg_unguarded_dynamic(s: view<[i32]>, idx: usize) -> i32 {\n"
        b"    s[idx]\n"
        b"}\n"
        b"\n"
        b"fn neg_signed_missing_lower(arr: [4]i32, idx: i32) -> i32 {\n"
        b"    if idx < 4 {\n"
        b"        arr[idx as usize]\n"
        b"    } else {\n"
        b"        0\n"
        b"    }\n"
        b"}\n"
        b"\n"
        b"fn neg_off_by_one(s: view<[i32]>) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < len(s) {\n"
        b"        acc = acc + s[i + 1];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn neg_wrapping_stride(arr: [4]i32, step: usize) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 4 {\n"
        b"        acc = acc + arr[wrapping_add_usize(i, step)];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn neg_indirect_mut_iv(arr: [4]i32) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let p: mut_view<usize> = mut_view(i);\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 4 {\n"
        b"        *p = 99;\n"
        b"        acc = acc + arr[i];\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn neg_vec_len_mutated(v: mut_view<Vec<i32>>) -> i32 {\n"
        b"    let saved: usize = v.len;\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < saved {\n"
        b"        if v.len > 0 {\n"
        b"            v.len = v.len - 1;\n"
        b"        }\n"
        b"        assert(i < v.len);\n"
        b"        acc = acc + unsafe { *(v.ptr + i) };\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn neg_sroa_vec_len_branch(mut v: Vec<i32>, idx: usize, c1: bool, c2: bool) -> i32 {\n"
        b"    if c1 {\n"
        b"        v.len = 5;\n"
        b"    }\n"
        b"    if idx < v.len {\n"
        b"        if c2 {\n"
        b"            v.len = 0;\n"
        b"        }\n"
        b"        assert(idx < v.len);\n"
        b"        return unsafe { *(v.ptr + idx) };\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn neg_sroa_vec_shrink_in_loop(mut v: Vec<i32>, shrink: bool) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < v.len {\n"
        b"        if shrink {\n"
        b"            v.len = 0;\n"
        b"        }\n"
        b"        assert(i < v.len);\n"
        b"        acc = acc + unsafe { *(v.ptr + i) };\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn neg_mem_vec_len_branch(v: mut_view<Vec<i32>>, idx: usize, c2: bool) -> i32 {\n"
        b"    if idx < v.len {\n"
        b"        if c2 {\n"
        b"            v.len = 0;\n"
        b"        }\n"
        b"        assert(idx < v.len);\n"
        b"        return unsafe { *(v.ptr + idx) };\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn neg_agg_vec_clobber_via_alias(pick_a: bool, idx: usize, p: *mut i32) -> i32 {\n"
        b"    let mut a = Vec<i32> { ptr: p, len: 4, cap: 4 };\n"
        b"    let mut b = Vec<i32> { ptr: p, len: 4, cap: 4 };\n"
        b"    let vp: mut_view<Vec<i32>> = if pick_a { mut_view(a) } else { mut_view(b) };\n"
        b"    if idx < vp.len {\n"
        b"        a = Vec<i32> { ptr: p, len: 0, cap: 4 };\n"
        b"        assert(idx < vp.len);\n"
        b"        return unsafe { *(vp.ptr + idx) };\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug_bce_agg_vec(pick_a: bool, idx: usize) -> usize {\n"
        b"    let mut backing: [4]i32 = [10, 20, 30, 40];\n"
        b"    let p: *mut i32 = unsafe { address_of_mut(backing[0]) };\n"
        b"    let mut a = Vec<i32> { ptr: p, len: 4, cap: 4 };\n"
        b"    let mut b = Vec<i32> { ptr: p, len: 4, cap: 4 };\n"
        b"    let raw: *mut Vec<i32> = if pick_a {\n"
        b"        unsafe { address_of_mut(a) }\n"
        b"    } else {\n"
        b"        unsafe { address_of_mut(b) }\n"
        b"    };\n"
        b"    let vp: mut_view<Vec<i32>> = unsafe { mut_view(*raw) };\n"
        b"    if idx < vp.len {\n"
        b"        a = Vec<i32> { ptr: p, len: 0, cap: 4 };\n"
        b"        assert(idx < vp.len);\n"
        b"        return vp.len;\n"
        b"    }\n"
        b"    99\n"
        b"}\n"
    ),

    # Blob 3: Synthetic MIR — multi-preheader + multi-latch + shared-exit + LCSSA live-out
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#4;\n"
        b"    let mut _2: type#15;\n"
        b"    let mut _3: type#8;\n"
        b"    let _4: type#4;\n"
        b"    let _5: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const true;\n"
        b"        switchInt(copy _1) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 0: type#15;\n"
        b"        _3 = const 10: type#8;\n"
        b"        switchInt(copy _1) -> [0: bb7, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _2 = const 1: type#15;\n"
        b"        _3 = const 20: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _4 = copy _2 < const 8: type#15;\n"
        b"        switchInt(copy _4) -> [0: bb7, otherwise: bb4];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _5 = copy _2 == const 3: type#15;\n"
        b"        switchInt(copy _5) -> [0: bb6, otherwise: bb5];\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _3 = wrapping_add(copy _3, const 1: type#8);\n"
        b"        _2 = wrapping_add(copy _2, const 1: type#15);\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        _3 = wrapping_add(copy _3, const 2: type#8);\n"
        b"        _2 = wrapping_add(copy _2, const 1: type#15);\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb7: {\n"
        b"        _0 = copy _3;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),

    # Blob 4: Synthetic MIR — `bb0` entry block is itself the natural loop header
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#15;\n"
        b"    let _2: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const 0: type#15;\n"
        b"        _2 = copy _1 < const 5: type#15;\n"
        b"        switchInt(copy _2) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _1 = wrapping_add(copy _1, const 1: type#15);\n"
        b"        goto -> bb0;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _0 = const 42: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),

    # Blob 5: Synthetic MIR — Tarjan SCC irreducible multi-entry cycle (`bb0 -> {bb1, bb2}`, `bb1 <-> bb2`)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#4;\n"
        b"    let _2: type#15;\n"
        b"    let _3: type#4;\n"
        b"    let _4: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const true;\n"
        b"        _2 = const 0: type#15;\n"
        b"        switchInt(copy _1) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _2 == const 0: type#15;\n"
        b"        switchInt(copy _3) -> [0: bb2, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4 = copy _2 == const 1: type#15;\n"
        b"        switchInt(copy _4) -> [0: bb1, otherwise: bb3];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = const 7: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),

    # Blob 6: Synthetic MIR — loop hoisting invariance (`_7`, `_8`, `_13`), clobber (`_9`, `_14`, `_16`), zero-trip div (`_10`) & raw ptr (`_4`, `_15`)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#17;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#19;\n"
        b"    let mut _5: type#15;\n"
        b"    let _6: type#15;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#8;\n"
        b"    let _9: type#8;\n"
        b"    let _10: type#8;\n"
        b"    let _11: type#4;\n"
        b"    let mut _12: type#8;\n"
        b"    let _13: type#8;\n"
        b"    let _14: type#8;\n"
        b"    let _15: type#8;\n"
        b"    let _16: type#8;\n"
        b"    bb0: {\n"
        b"        _12 = const 10: type#8;\n"
        b"        _2 = &_12;\n"
        b"        (*_1) = const 20: type#8;\n"
        b"        _3 = copy (*_2);\n"
        b"        _4 = const 4096: type#15 as type#19 (IntToPtr);\n"
        b"        _5 = const 0: type#15;\n"
        b"        _6 = copy (*_2) as type#15 (IntToInt);\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _11 = copy _5 < copy _6;\n"
        b"        switchInt(copy _11) -> [0: bb3, otherwise: bb2];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _7 = wrapping_add(copy _3, const 5: type#8);\n"
        b"        _8 = copy (*_2);\n"
        b"        (*_1) = const 99: type#8;\n"
        b"        _9 = copy (*_1);\n"
        b"        _10 = copy _3 / copy _3;\n"
        b"        _13 = discriminant((*_2));\n"
        b"        _14 = discriminant((*_1));\n"
        b"        _15 = discriminant((*_4));\n"
        b"        _16 = discriminant(_5);\n"
        b"        _5 = wrapping_add(copy _5, const 1: type#15);\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = copy _3;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),

    # Blob 7: Frontend-lowered SCEV, nested loops, trip-count lattice & affine array dependence
    (
        b"@intrinsic fn wrapping_add_u8(a: u8, b: u8) -> u8 { 0 }\n"
        b"@intrinsic fn wrapping_add_usize(a: usize, b: usize) -> usize { 0 }\n"
        b"@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }\n"
        b"\n"
        b"enum State {\n"
        b"    Step(i32),\n"
        b"    Done,\n"
        b"}\n"
        b"\n"
        b"struct Pair {\n"
        b"    x: i32,\n"
        b"    y: i32,\n"
        b"}\n"
        b"\n"
        b"fn scev_nested_and_const() -> usize {\n"
        b"    let mut r: usize = 0;\n"
        b"    let mut acc: usize = 0;\n"
        b"    while r < 4 {\n"
        b"        let mut c: usize = 0;\n"
        b"        while c < 10 {\n"
        b"            let two_c: usize = c * 2;\n"
        b"            let plus_c: usize = c + 1;\n"
        b"            acc = acc + two_c + plus_c;\n"
        b"            c = c + 1;\n"
        b"        }\n"
        b"        r = r + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn scev_symbolic(n: usize) -> usize {\n"
        b"    let mut i: usize = 0;\n"
        b"    while i < n {\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    i\n"
        b"}\n"
        b"\n"
        b"fn scev_upper_bounded(s: view<[i32]>) -> usize {\n"
        b"    let mut i: usize = 0;\n"
        b"    while i < 8 {\n"
        b"        if s[i] < 0 {\n"
        b"            break;\n"
        b"        }\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    i\n"
        b"}\n"
        b"\n"
        b"fn scev_infinite_u8() -> i32 {\n"
        b"    let mut i: u8 = 0u8;\n"
        b"    while i <= 255u8 {\n"
        b"        i = wrapping_add_u8(i, 1u8);\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn scev_unknown_stride2_ne(n: usize) -> usize {\n"
        b"    let mut i: usize = 0;\n"
        b"    while i != n {\n"
        b"        i = wrapping_add_usize(i, 2);\n"
        b"    }\n"
        b"    i\n"
        b"}\n"
        b"\n"
        b"fn dep_array_even_odd_and_dist1() -> i32 {\n"
        b"    let mut eo: [8]i32 = [0, 0, 0, 0, 0, 0, 0, 0];\n"
        b"    let mut dep: [6]i32 = [1, 2, 3, 4, 5, 6];\n"
        b"    let mut i: usize = 0;\n"
        b"    while i < 4 {\n"
        b"        let even_idx: usize = i * 2;\n"
        b"        let odd_idx: usize = even_idx + 1;\n"
        b"        eo[even_idx] = 11;\n"
        b"        eo[odd_idx] = 22;\n"
        b"        let next_idx: usize = i + 1;\n"
        b"        let cur_val: i32 = dep[i];\n"
        b"        dep[next_idx] = cur_val + 1;\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    eo[0] + dep[4]\n"
        b"}\n"
        b"\n"
        b"fn bug3a_post_inc_dep() -> i32 {\n"
        b"    let mut dep: [6]i32 = [1, 2, 3, 4, 5, 6];\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 4 {\n"
        b"        dep[i] = 99;\n"
        b"        i = i + 1;\n"
        b"        let after_inc: i32 = dep[i];\n"
        b"        acc = acc + after_inc;\n"
        b"    }\n"
        b"    acc + dep[4]\n"
        b"}\n"
        b"\n"
        b"fn bug3b_rebound_slice_dep(buf: mut_view<[i32]>) -> i32 {\n"
        b"    if len(buf) >= 10 {\n"
        b"        let mut mv: mut_view<[i32]> = buf;\n"
        b"        let mut i: usize = 0;\n"
        b"        while i < 2 {\n"
        b"            let odd: usize = i * 2 + 1;\n"
        b"            let even: usize = i * 2;\n"
        b"            mv[odd] = 11;\n"
        b"            let cur_n: usize = len(mv);\n"
        b"            mv = mv[1..cur_n];\n"
        b"            mv[even] = 22;\n"
        b"            i = i + 1;\n"
        b"        }\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug2_rebound_subslice_overlap(buf: mut_view<[i32]>) -> i32 {\n"
        b"    if len(buf) >= 6 {\n"
        b"        let mut mv: mut_view<[i32]> = buf[1..6];\n"
        b"        let left = mv[0..2];\n"
        b"        mv = buf;\n"
        b"        let right = mv[2..4];\n"
        b"        left[1] = 10;\n"
        b"        right[0] = 20;\n"
        b"        return left[1];\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug2a_cond_rebind(buf: mut_view<[i32]>, c: bool) -> i32 {\n"
        b"    if len(buf) >= 6 {\n"
        b"        let mut mv: mut_view<[i32]> = buf[1..6];\n"
        b"        let left = mv[0..2];\n"
        b"        if c {\n"
        b"            mv = buf;\n"
        b"        }\n"
        b"        let right = mv[2..4];\n"
        b"        left[1] = 10;\n"
        b"        right[0] = 20;\n"
        b"        return left[1];\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug2b_loop_rebind(buf: mut_view<[i32]>, n: usize) -> i32 {\n"
        b"    if len(buf) >= 6 {\n"
        b"        let mut mv: mut_view<[i32]> = buf[1..6];\n"
        b"        let left = mv[0..2];\n"
        b"        let mut k: usize = 0;\n"
        b"        while k < n {\n"
        b"            mv = buf;\n"
        b"            k = k + 1;\n"
        b"        }\n"
        b"        let right = mv[2..4];\n"
        b"        left[1] = 10;\n"
        b"        right[0] = 20;\n"
        b"        return left[1];\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug2c_backedge_rebind(buf: mut_view<[i32]>, n: usize) -> i32 {\n"
        b"    if len(buf) >= 6 {\n"
        b"        let mut mv: mut_view<[i32]> = buf[1..6];\n"
        b"        let left = mv[0..2];\n"
        b"        let mut k: usize = 0;\n"
        b"        while k < n {\n"
        b"            let right = mv[2..4];\n"
        b"            left[1] = 10;\n"
        b"            right[0] = 20;\n"
        b"            mv = buf;\n"
        b"            k = k + 1;\n"
        b"        }\n"
        b"        return left[1];\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug2d_cond_rebind_lo(buf: mut_view<[i32]>, c: bool) -> i32 {\n"
        b"    if len(buf) >= 6 {\n"
        b"        let mut lo: usize = 2;\n"
        b"        let left = buf[0..2];\n"
        b"        if c {\n"
        b"            lo = 1;\n"
        b"        }\n"
        b"        let right = buf[lo..4];\n"
        b"        left[1] = 10;\n"
        b"        right[0] = 20;\n"
        b"        return left[1];\n"
        b"    }\n"
        b"    0\n"
        b"}\n"
        b"\n"
        b"fn bug_r1_f2_cond_idx_dep(c: bool) -> i32 {\n"
        b"    let mut dep: [6]i32 = [1, 2, 3, 4, 5, 6];\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 4 {\n"
        b"        let mut idx: usize = i;\n"
        b"        dep[idx] = 99;\n"
        b"        if c {\n"
        b"            idx = i + 1;\n"
        b"        }\n"
        b"        let val: i32 = dep[idx];\n"
        b"        acc = acc + val;\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc + dep[4]\n"
        b"}\n"
        b"\n"
        b"fn bug_loops_agg_clobber(pick_a: bool) -> i32 {\n"
        b"    let mut a = Pair { x: 10, y: 20 };\n"
        b"    let mut b = Pair { x: 30, y: 40 };\n"
        b"    let mv: mut_view<Pair> = if pick_a { mut_view(a) } else { mut_view(b) };\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 4 {\n"
        b"        let cur_x: i32 = mv.x;\n"
        b"        acc = acc + cur_x;\n"
        b"        a = Pair { x: 99, y: 99 };\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn bug_loops_agg_clobber_raw(pick_a: bool) -> i32 {\n"
        b"    let mut a = Pair { x: 10, y: 20 };\n"
        b"    let mut b = Pair { x: 30, y: 40 };\n"
        b"    let raw: *mut Pair = if pick_a {\n"
        b"        unsafe { address_of_mut(a) }\n"
        b"    } else {\n"
        b"        unsafe { address_of_mut(b) }\n"
        b"    };\n"
        b"    let mv: mut_view<Pair> = unsafe { mut_view(*raw) };\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 3 {\n"
        b"        let vx: i32 = mv.x;\n"
        b"        acc = acc + vx;\n"
        b"        a = Pair { x: 99, y: 99 };\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn pos_discriminant_view(sv: view<State>) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 3 {\n"
        b"        match *sv {\n"
        b"            State.Step(v) => { acc = acc + v; },\n"
        b"            State.Done => { acc = acc + 1; },\n"
        b"        }\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn bug_discriminant_local_mut() -> i32 {\n"
        b"    let mut st = State.Step(10);\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 3 {\n"
        b"        match st {\n"
        b"            State.Step(v) => { acc = acc + v; st = State.Done; },\n"
        b"            State.Done => { acc = acc + 1; },\n"
        b"        }\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn bug_discriminant_mut_view(mv: mut_view<State>) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < 3 {\n"
        b"        match *mv {\n"
        b"            State.Step(v) => { acc = acc + v; *mv = State.Done; },\n"
        b"            State.Done => { acc = acc + 1; },\n"
        b"        }\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
        b"\n"
        b"fn bug_discriminant_zero_trip_raw(raw_p: *const State, n: usize) -> i32 {\n"
        b"    let mut i: usize = 0;\n"
        b"    let mut acc: i32 = 0;\n"
        b"    while i < n {\n"
        b"        match unsafe { *raw_p } {\n"
        b"            State.Step(v) => { acc = acc + v; },\n"
        b"            State.Done => { acc = acc + 1; },\n"
        b"        }\n"
        b"        i = i + 1;\n"
        b"    }\n"
        b"    acc\n"
        b"}\n"
    ),

    # Blob 8: Synthetic MIR — pruned-SSA diamond rebind of `index_local` `_3` inside loop (`bb4.phi_count == 0`)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#4;\n"
        b"    let mut _2: type#20;\n"
        b"    let mut _3: type#15;\n"
        b"    let _4: type#15;\n"
        b"    let mut _5: type#15;\n"
        b"    let _6: type#4;\n"
        b"    let mut _7: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const true;\n"
        b"        _2 = [const 0: type#8; 4];\n"
        b"        _5 = const 0: type#15;\n"
        b"        _7 = const 0: type#8;\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _6 = copy _5 < const 3: type#15;\n"
        b"        switchInt(copy _6) -> [0: bb5, otherwise: bb2];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _3 = copy _5;\n"
        b"        _4 = wrapping_add(copy _5, const 1: type#15);\n"
        b"        _2[_3] = const 99: type#8;\n"
        b"        switchInt(copy _1) -> [0: bb4, otherwise: bb3];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _3 = copy _4;\n"
        b"        goto -> bb4;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _7 = copy _2[_3];\n"
        b"        _5 = copy _4;\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = copy _7;\n"
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


def assemble_opt_bce_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", BCE_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    bce_modules = list(got.PIPELINE_MODULES) + [
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.loops", "compiler"),
        ("compiler.opt.bce", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(bce_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_bce" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_bce_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.loops + compiler.opt.bce probe under -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "opt_bce_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_bce_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_bce_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"opt_bce_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=1500,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build opt_bce_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=180)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt_bce_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt_bce_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
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

    # 3. Differential panic preservation (exit 101) across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename in NEGATIVE_PANIC_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 101:
            sys.stderr.write(f"expected exit 101 for {stem} under --interp, got {iproc.returncode}\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build negative {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 101:
                sys.stderr.write(f"expected exit 101 for {stem} under {flag}, got {rproc.returncode}\n")
                return 1

    # 4. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2
    inspect_src = resolve_fixture_path(root, "canonical_loops_and_bce_positive.ax")
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

    sys.stdout.buffer.write(b"OPT-LOOPS-SCEV-BCE-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
