#!/usr/bin/env python3
"""Oracle test for E15.2 (T607): Intraprocedural & interprocedural escape analysis
(NoEscape / ArgumentEscape / ReturnEscape / GlobalEscape, recursive SCC fixed-point summaries,
certainty & barrier discipline) and stack/register allocation promotion (Box SROA & stack,
NoEscape closure environment capture forwarding & direct-call devirtualization, bounded
inline buffer promotion, NRVO, disjoint stack-slot reuse, and PassManager rollback)
across --interp, -O0, -O1, and -O2 --verify-each.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "opt_escape_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_ESCAPE_LATTICE_AND_BARRIERS=OK\n"
    "PROBE_INTERPROC_SUMMARIES_AND_SCC=OK\n"
    "PROBE_LOOP_AND_DISJOINT_SLOTS=OK\n"
    "PROBE_PROMOTIONS_AND_ROLLBACK=OK\n"
    "PROBE_QA_ROUND1_REGRESSIONS=OK\n"
    "PROBE_QA_ROUND2_REGRESSIONS=OK\n"
    "PROBE_ALL=OK\n"
)

POSITIVE_FIXTURES: list[tuple[str, str, str]] = [
    (
        "box_closure_buffer_promotion",
        "box_closure_buffer_promotion.ax",
        "ESC_PROMO_BANNER=Xin chào tối ưu hóa cấp phát ngăn xếp\n"
        "BOX_NOESCAPE=158\n"
        "BOX_ARG_ESCAPE=95\n"
        "CLOSURE_PROMO=227\n"
        "BOUNDED_BUF=340\n"
        "ESC_PROMO_TOTAL=820\n",
    ),
    (
        "escape_barriers_and_retention",
        "escape_barriers_and_retention.ax",
        "ESC_BARRIER_BANNER=Xin chào rào cản thoát bộ nhớ\n"
        "RET_ESCAPE_NRVO=109\n"
        "GLOBAL_ESCAPE_SINK=91\n"
        "PTR_IDENTITY_OBS=35\n"
        "LOOP_CARRIED_HEAP=101\n"
        "OVERSIZED_BOX=46\n"
        "ESC_BARRIER_TOTAL=382\n",
    ),
    (
        "drop_order_and_scope_parity",
        "drop_order_and_scope_parity.ax",
        "ESC_DROP_BANNER=Xin chào thứ tự giải phóng tài nguyên\n"
        "DROP=102\n"
        "DROP=101\n"
        "DROP=202\n"
        "DROP=201\n"
        "DROP=300\n"
        "DROP=301\n"
        "DROP=302\n"
        "DROP=401\n"
        "DROP=402\n"
        "DROP_PARITY_SUM=1838\n",
    ),
    (
        "qa_round1_soundness_regressions",
        "qa_round1_soundness_regressions.ax",
        "ESC_QA_R1_BANNER=Xin chào kiểm chứng an toàn thoát bộ nhớ vòng một\n"
        "F1_DEREF_ESCAPE=70\n"
        "F2_UNBALANCED_FREE=93\n"
        "F3_SLOT_IDENTITY=81\n"
        "F4_INTERPROC_OBS=83\n"
        "F5_CLOSURE_SOUNDNESS=85\n"
        "F6_PTR_INT_NON_NULL=80\n"
        "F7_PARAM_PROMOTIONS=100\n"
        "F8_NRVO_TERMINATOR_READS=148\n"
        "QA_R1_TOTAL=740\n",
    ),
]

# Custom types registered by `probe_init_escape_thir` in `opt_escape_probe.ax.in`:
#   type#2  = unit, type#4 = bool, type#8 = i32, type#11 = u8, type#14 = u64, type#15 = usize
#   type#17 = view<i32>, type#18 = mut_view<i32>, type#19 = *mut i32
#   type#20 = struct Pair { i32, i32 }, type#21 = mut_view<Pair>, type#22 = view<Pair>
#   type#23 = [4]i32
#   type#24 = Box<i32> { ptr: *mut i32 }, type#25 = Box<Pair> { ptr: *mut Pair }
#   type#26 = *mut Pair, type#27 = *mut u8
#   type#28 = fn(usize, usize) -> *mut u8           (heap_alloc, sym=100)
#   type#29 = fn(*mut u8, usize, usize) -> unit     (heap_free, sym=101)
#   type#30 = fn(i32) -> Box<i32>                   (box_new<i32>, sym=102)
#   type#31 = fn(Pair) -> Box<Pair>                 (box_new<Pair>, sym=103)
#   type#32 = fn(Box<i32>) -> *mut i32              (box_into_raw<i32>, sym=104)
#   type#33 = fn(mut_view<i32>) -> i32              (spawn=105, ffi=106, opaque=107, rec_a=110, rec_b=111, leak_a=112, leak_b=113)
#   type#34 = fn(view<i32>) -> view<i32>            (passthrough_view, sym=108)
#   type#35 = TY_CLOSURE(cap=[i32], (i32)->i32, fn_sym=200, fn_type=type#36)
#   type#36 = fn(i32, i32) -> i32                   (lifted closure fn)
#   type#37 = [2048]i32 (8192B), type#38 = *mut [2048]i32, type#39 = Box<[2048]i32>, type#40 = fn([2048]i32) -> Box<[2048]i32> (sym=109)
#   type#41 = mut_view<*mut i32>, type#42 = struct SinkPtr { mv: mut_view<*mut i32> }
#   type#43 = fn(mut_view<Pair>) -> i32             (pure_borrow_pair, sym=114)

ESCAPE_PROBE_BLOBS: list[bytes] = [
    # Blob 0: `AESCAPE-26` + Non-null check `p as usize != 0` + `box_new<i32>` SROA promotion:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let _2: type#30;\n"
        b"    let _3: type#19;\n"
        b"    let _4: type#15;\n"
        b"    let _5: type#4;\n"
        b"    let _6: type#19;\n"
        b"    let _7: type#19;\n"
        b"    bb0: {\n"
        b"        _2 = const 102: type#30;\n"
        b"        _1 = copy _2(const 42: type#8) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _1.0;\n"
        b"        _4 = copy _3 as type#15 (PtrToInt);\n"
        b"        _5 = copy _4 != const 0: type#15;\n"
        b"        _6 = copy _1.0;\n"
        b"        (*_6) = const 50: type#8;\n"
        b"        _7 = copy _1.0;\n"
        b"        _0 = copy (*_7);\n"
        b"        drop(_1) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 1: Escape barriers (addr_observable usize, ptr identity ==, interior *(s.mv)=p,
    # spawn ESC_THREAD, FFI ESC_EXTERNAL, unknown call ESC_UNKNOWN, oversized >4096B,
    # @at fixed MMIO, ZeroCopyPin, volatile/atomic):
    (
        b"mir_body {\n"
        b"    let mut _0: type#15; // return\n"
        b"    let _1: type#42; // arg\n"
        b"    let mut _2: type#24;\n"
        b"    let mut _3: type#24;\n"
        b"    let mut _4: type#24;\n"
        b"    let mut _5: type#8;\n"
        b"    let mut _6: type#8;\n"
        b"    let mut _7: type#8;\n"
        b"    let mut _8: type#37;\n"
        b"    let mut _9: type#39;\n"
        b"    let mut _10: type#8;\n"
        b"    let mut _11: type#8;\n"
        b"    let mut _12: type#8;\n"
        b"    let mut _13: type#8;\n"
        b"    let _14: type#30;\n"
        b"    let _15: type#19;\n"
        b"    let _16: type#19;\n"
        b"    let _17: type#19;\n"
        b"    let _18: type#4;\n"
        b"    let _19: type#18;\n"
        b"    let _20: type#18;\n"
        b"    let _21: type#18;\n"
        b"    let _22: type#33;\n"
        b"    let _23: type#33;\n"
        b"    let _24: type#33;\n"
        b"    let _25: type#8;\n"
        b"    let _26: type#8;\n"
        b"    let _27: type#8;\n"
        b"    let _28: type#40;\n"
        b"    let _29: type#19;\n"
        b"    let _30: type#41;\n"
        b"    let _31: type#19;\n"
        b"    let _32: type#17;\n"
        b"    let _33: type#18;\n"
        b"    bb0: {\n"
        b"        _14 = const 102: type#30;\n"
        b"        _2 = copy _14(const 11: type#8) -> [return: bb1, unwind: bb8];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _14(const 22: type#8) -> [return: bb2, unwind: bb8];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4 = copy _14(const 33: type#8) -> [return: bb3, unwind: bb8];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _15 = copy _2.0;\n"
        b"        _0 = copy _15 as type#15 (PtrToInt);\n"
        b"        _16 = copy _3.0;\n"
        b"        _17 = copy _4.0;\n"
        b"        _18 = copy _16 == copy _17;\n"
        b"        _5 = const 1: type#8;\n"
        b"        _6 = const 2: type#8;\n"
        b"        _7 = const 3: type#8;\n"
        b"        _19 = &mut _5;\n"
        b"        _20 = &mut _6;\n"
        b"        _21 = &mut _7;\n"
        b"        _22 = const 105: type#33;\n"
        b"        _25 = copy _22(copy _19) -> [return: bb4, unwind: bb8];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _23 = const 106: type#33;\n"
        b"        _26 = copy _23(copy _20) -> [return: bb5, unwind: bb8];\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _24 = const 107: type#33;\n"
        b"        _27 = copy _24(copy _21) -> [return: bb6, unwind: bb8];\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        _8 = [const 0: type#8; 2048];\n"
        b"        _28 = const 109: type#40;\n"
        b"        _9 = copy _28(move _8) -> [return: bb7, unwind: bb8];\n"
        b"    }\n"
        b"    bb7: {\n"
        b"        _10 = const 10: type#8;\n"
        b"        _11 = const 11: type#8;\n"
        b"        _12 = const 12: type#8;\n"
        b"        _13 = const 13: type#8;\n"
        b"        _31 = const 4096: type#15 as type#19 (IntToPtr);\n"
        b"        _32 = &_11;\n"
        b"        _33 = &mut _12;\n"
        b"        (*_33) = const 99: type#8;\n"
        b"        _29 = &mut _13;\n"
        b"        _30 = copy _1.0;\n"
        b"        (*_30) = copy _29;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb8: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 2: Mutual recursion non-escaping SCC `rec_a` (sym=110) -> calls `rec_b` (sym=111):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#33;\n"
        b"    bb0: {\n"
        b"        _2 = const 111: type#33;\n"
        b"        _0 = copy _2(copy _1) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 3: Mutual recursion non-escaping SCC `rec_b` (sym=111) -> reads `*_1`, calls `rec_a` (sym=110):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#33;\n"
        b"    bb0: {\n"
        b"        _2 = copy (*_1);\n"
        b"        switchInt(copy _2) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = const 110: type#33;\n"
        b"        _0 = copy _3(copy _1) -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 4: Mutual recursion leaking SCC `leak_a` (sym=112) -> calls `leak_b` (sym=113):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#33;\n"
        b"    bb0: {\n"
        b"        _2 = const 113: type#33;\n"
        b"        _0 = copy _2(copy _1) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 5: Mutual recursion leaking SCC `leak_b` (sym=113) -> calls FFI (sym=106) and `leak_a` (sym=112):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#18; // arg\n"
        b"    let _2: type#33;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#33;\n"
        b"    bb0: {\n"
        b"        _2 = const 106: type#33;\n"
        b"        _3 = copy _2(copy _1) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = const 112: type#33;\n"
        b"        _0 = copy _4(copy _1) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 6: `passthrough_view` (sym=108): returns parameter `_1: view<i32>` directly:
    (
        b"mir_body {\n"
        b"    let mut _0: type#17; // return\n"
        b"    let _1: type#17; // arg\n"
        b"    bb0: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 7: Caller of `passthrough_view` that consumes returned `view<i32>` locally (`ArgumentEscape`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let _2: type#17;\n"
        b"    let _3: type#34;\n"
        b"    let _4: type#17;\n"
        b"    bb0: {\n"
        b"        _1 = const 77: type#8;\n"
        b"        _2 = &_1;\n"
        b"        _3 = const 108: type#34;\n"
        b"        _4 = copy _3(copy _2) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy (*_4);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 8: Caller of `passthrough_view` that returns returned `view<i32>` (`ReturnEscape` + `REASON_ACTIVE_VIEW_ESCAPE`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#17; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let _2: type#17;\n"
        b"    let _3: type#34;\n"
        b"    bb0: {\n"
        b"        _1 = const 88: type#8;\n"
        b"        _2 = &_1;\n"
        b"        _3 = const 108: type#34;\n"
        b"        _0 = copy _3(copy _2) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 9: Loop-carried `heap_alloc(16, 4)` inside loop `bb1 -> bb2 -> bb1` without `heap_free` (`crosses_backedge == true`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#4; // arg\n"
        b"    let _2: type#28;\n"
        b"    let _3: type#27;\n"
        b"    let _4: type#19;\n"
        b"    bb0: {\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 100: type#28;\n"
        b"        _3 = copy _2(const 16: type#15, const 4: type#15) -> [return: bb2, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4 = copy _3 as type#19 (PtrToPtr);\n"
        b"        (*_4) = const 12: type#8;\n"
        b"        switchInt(copy _1) -> [0: bb3, otherwise: bb1];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = copy (*_4);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 10: Iteration-local `heap_alloc(16, 4)` + `heap_free` inside loop (`crosses_backedge == false`)
    # + Disjoint `[StorageLive, StorageDead]` `Pair` stack locals (`_6` and `_7`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#4; // arg\n"
        b"    let _2: type#28;\n"
        b"    let _3: type#27;\n"
        b"    let _4: type#19;\n"
        b"    let _5: type#29;\n"
        b"    let mut _6: type#20;\n"
        b"    let mut _7: type#20;\n"
        b"    let _8: type#2;\n"
        b"    let mut _9: type#8;\n"
        b"    bb0: {\n"
        b"        StorageLive(_6);\n"
        b"        _6.0 = const 10: type#8;\n"
        b"        _6.1 = const 20: type#8;\n"
        b"        _9 = copy _6.0;\n"
        b"        StorageDead(_6);\n"
        b"        StorageLive(_7);\n"
        b"        _7.0 = const 30: type#8;\n"
        b"        _7.1 = const 40: type#8;\n"
        b"        _9 = wrapping_add(copy _9, copy _7.1);\n"
        b"        StorageDead(_7);\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 100: type#28;\n"
        b"        _3 = copy _2(const 16: type#15, const 4: type#15) -> [return: bb2, unwind: bb5];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4 = copy _3 as type#19 (PtrToPtr);\n"
        b"        (*_4) = const 5: type#8;\n"
        b"        _9 = wrapping_add(copy _9, copy (*_4));\n"
        b"        _5 = const 101: type#29;\n"
        b"        _8 = copy _5(copy _3, const 16: type#15, const 4: type#15) -> [return: bb3, unwind: bb5];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        switchInt(copy _1) -> [0: bb4, otherwise: bb1];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _0 = copy _9;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 11: `box_new<Pair>` passed by `mut_view<Pair>` to `pure_borrow_pair` (sym=114, `ESC_ARGUMENT`) -> `box_stack_promotions == 1`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#20;\n"
        b"    let mut _2: type#25;\n"
        b"    let _3: type#31;\n"
        b"    let _4: type#26;\n"
        b"    let _5: type#21;\n"
        b"    let _6: type#43;\n"
        b"    bb0: {\n"
        b"        _1.0 = const 15: type#8;\n"
        b"        _1.1 = const 25: type#8;\n"
        b"        _3 = const 103: type#31;\n"
        b"        _2 = copy _3(move _1) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = copy _2.0;\n"
        b"        _5 = &mut (*_4);\n"
        b"        _6 = const 114: type#43;\n"
        b"        _0 = copy _6(copy _5) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 12: `NoEscape` capturing closure (`type#35`, `fn_sym=200`, `cap=[_1: i32]`) -> `closure_env_promotions == 1`, `closure_direct_calls == 1`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#35;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 32: type#8;\n"
        b"        StorageLive(_2);\n"
        b"        _2 = aggregate(variant#0, [const 200: type#15, copy _1]);\n"
        b"        _3 = copy _2.1;\n"
        b"        _4 = copy _2(const 10: type#8) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        StorageDead(_2);\n"
        b"        _0 = wrapping_add(copy _3, copy _4);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 13: Bounded `heap_alloc(16, 4)` + `heap_free` (`inline_buffer_promotions == 1`, 0 calls left)
    # + `NRVO` aggregate `Pair` local `_5` moved into `_0` (`nrvo_promotions == 1`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#20; // return\n"
        b"    let _1: type#28;\n"
        b"    let _2: type#27;\n"
        b"    let _3: type#19;\n"
        b"    let _4: type#29;\n"
        b"    let mut _5: type#20;\n"
        b"    let _6: type#2;\n"
        b"    let _7: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 100: type#28;\n"
        b"        _2 = copy _1(const 16: type#15, const 4: type#15) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _2 as type#19 (PtrToPtr);\n"
        b"        (*_3) = const 99: type#8;\n"
        b"        _7 = copy (*_3);\n"
        b"        _4 = const 101: type#29;\n"
        b"        _6 = copy _4(copy _2, const 16: type#15, const 4: type#15) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        StorageLive(_5);\n"
        b"        _5.0 = copy _7;\n"
        b"        _5.1 = const 1: type#8;\n"
        b"        _0 = move _5;\n"
        b"        StorageDead(_5);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 14 (QA Finding 1a): Nested `Box<Box<i32>>` unboxed via `*_5` (`MIR_PROJ_DEREF`) and returned:
    (
        b"mir_body {\n"
        b"    let mut _0: type#24; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let mut _2: type#46;\n"
        b"    let _3: type#30;\n"
        b"    let _4: type#47;\n"
        b"    let _5: type#45;\n"
        b"    bb0: {\n"
        b"        _3 = const 102: type#30;\n"
        b"        _1 = copy _3(const 42: type#8) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = const 115: type#47;\n"
        b"        _2 = copy _4(move _1) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _5 = copy _2.0;\n"
        b"        _0 = move (*_5);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 15 (QA Finding 1a): `_3 = copy _1.0; _4 = &mut _3; _0 = copy (*_4); drop(_1); return`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#19; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let _2: type#30;\n"
        b"    let mut _3: type#19;\n"
        b"    let _4: type#41;\n"
        b"    bb0: {\n"
        b"        _2 = const 102: type#30;\n"
        b"        _1 = copy _2(const 42: type#8) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _1.0;\n"
        b"        _4 = &mut _3;\n"
        b"        _0 = copy (*_4);\n"
        b"        drop(_1) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 16 (QA Finding 1b): `get_inner_ptr(slot: mut_view<*mut i32>) -> *mut i32 { *slot }` (`sym=116`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#19; // return\n"
        b"    let _1: type#41; // arg\n"
        b"    bb0: {\n"
        b"        _0 = copy (*_1);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 17 (QA Finding 1b): `leak_slot_ptr(slot: mut_view<*mut i32>) -> bool { ffi_ptr(*slot) }` (`sym=121`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#4; // return\n"
        b"    let _1: type#41; // arg\n"
        b"    let _2: type#19;\n"
        b"    let _3: type#49;\n"
        b"    bb0: {\n"
        b"        _2 = copy (*_1);\n"
        b"        _3 = const 118: type#49;\n"
        b"        _0 = copy _3(copy _2) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 18 (QA Finding 2a): `box_new<i32>` moved by value (`_3 = move _2; drop(_3)`) on one branch:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#24;\n"
        b"    let mut _3: type#24;\n"
        b"    let _4: type#30;\n"
        b"    let _5: type#19;\n"
        b"    bb0: {\n"
        b"        _1 = const 1: type#8;\n"
        b"        _4 = const 102: type#30;\n"
        b"        _2 = copy _4(const 42: type#8) -> [return: bb1, unwind: bb6];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _5 = copy _2.0;\n"
        b"        _0 = copy (*_5);\n"
        b"        switchInt(copy _1) -> [0: bb2, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _3 = move _2;\n"
        b"        drop(_3) -> [return: bb4, unwind: bb6];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        drop(_2) -> [return: bb5, unwind: bb6];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 19 (QA Finding 2b): Unbalanced `heap_alloc(16, 4)` freed on `bb2` but NOT on `bb3`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let _2: type#28;\n"
        b"    let _3: type#27;\n"
        b"    let _4: type#19;\n"
        b"    let _5: type#29;\n"
        b"    let _6: type#2;\n"
        b"    bb0: {\n"
        b"        _1 = const 1: type#8;\n"
        b"        _2 = const 100: type#28;\n"
        b"        _3 = copy _2(const 16: type#15, const 4: type#15) -> [return: bb1, unwind: bb5];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = copy _3 as type#19 (PtrToPtr);\n"
        b"        (*_4) = const 7: type#8;\n"
        b"        _0 = copy (*_4);\n"
        b"        switchInt(copy _1) -> [0: bb2, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _5 = const 101: type#29;\n"
        b"        _6 = copy _5(copy _3, const 16: type#15, const 4: type#15) -> [return: bb4, unwind: bb5];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 20 (QA Finding 3): Disjoint `[StorageLive, StorageDead]` `Pair` slots whose addresses are compared/observed:
    (
        b"mir_body {\n"
        b"    let mut _0: type#15; // return\n"
        b"    let mut _1: type#20;\n"
        b"    let mut _2: type#20;\n"
        b"    let _3: type#21;\n"
        b"    let _4: type#21;\n"
        b"    let _5: type#26;\n"
        b"    let _6: type#26;\n"
        b"    let _7: type#4;\n"
        b"    bb0: {\n"
        b"        StorageLive(_1);\n"
        b"        _1.0 = const 1: type#8;\n"
        b"        _1.1 = const 2: type#8;\n"
        b"        _3 = &mut _1;\n"
        b"        _5 = copy _3 as type#26 (PtrToPtr);\n"
        b"        StorageDead(_1);\n"
        b"        StorageLive(_2);\n"
        b"        _2.0 = const 3: type#8;\n"
        b"        _2.1 = const 4: type#8;\n"
        b"        _4 = &mut _2;\n"
        b"        _6 = copy _4 as type#26 (PtrToPtr);\n"
        b"        StorageDead(_2);\n"
        b"        _7 = copy _5 == copy _6;\n"
        b"        _0 = copy _5 as type#15 (PtrToInt);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 21 (QA Finding 4): Callee `obs_ptr_fn(p: *mut i32) -> bool` (`sym=117`) observing integer address:
    (
        b"mir_body {\n"
        b"    let mut _0: type#4; // return\n"
        b"    let _1: type#19; // arg\n"
        b"    let _2: type#15;\n"
        b"    let _3: type#15;\n"
        b"    bb0: {\n"
        b"        _2 = copy _1 as type#15 (PtrToInt);\n"
        b"        _3 = wrapping_add(copy _2, const 1: type#15);\n"
        b"        _0 = copy _3 == const 0: type#15;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 22 (QA Finding 4): Callee `cmp_ptrs_fn(a: *mut i32, b: *mut i32) -> bool` (`sym=119`) comparing identity:
    (
        b"mir_body {\n"
        b"    let mut _0: type#4; // return\n"
        b"    let _1: type#19; // arg\n"
        b"    let _2: type#19; // arg\n"
        b"    bb0: {\n"
        b"        _0 = copy _1 == copy _2;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 23 (QA Finding 4): Caller passing `Box<i32>` pointers into `obs_ptr_fn` (117) and `cmp_ptrs_fn` (119):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let mut _2: type#24;\n"
        b"    let _3: type#30;\n"
        b"    let _4: type#19;\n"
        b"    let _5: type#19;\n"
        b"    let _6: type#49;\n"
        b"    let _7: type#50;\n"
        b"    let _8: type#4;\n"
        b"    let _9: type#4;\n"
        b"    let _10: type#19;\n"
        b"    bb0: {\n"
        b"        _3 = const 102: type#30;\n"
        b"        _1 = copy _3(const 10: type#8) -> [return: bb1, unwind: bb6];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = copy _3(const 20: type#8) -> [return: bb2, unwind: bb6];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4 = copy _1.0;\n"
        b"        _6 = const 117: type#49;\n"
        b"        _8 = copy _6(copy _4) -> [return: bb3, unwind: bb6];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _5 = copy _2.0;\n"
        b"        _7 = const 119: type#50;\n"
        b"        _9 = copy _7(copy _4, copy _5) -> [return: bb4, unwind: bb6];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _10 = copy _1.0;\n"
        b"        _0 = copy (*_10);\n"
        b"        drop(_2) -> [return: bb5, unwind: bb6];\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        drop(_1) -> [return: bb7, unwind: bb6];\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb7: {\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 24 (QA Finding 5a): Closure capture `_1` ends lifetime (`StorageDead(_1)`) BEFORE `_2(10)` call:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#35;\n"
        b"    let mut _3: type#8;\n"
        b"    bb0: {\n"
        b"        StorageLive(_1);\n"
        b"        _1 = const 32: type#8;\n"
        b"        StorageLive(_2);\n"
        b"        _2 = aggregate(variant#0, [const 200: type#15, copy _1]);\n"
        b"        StorageDead(_1);\n"
        b"        StorageLive(_3);\n"
        b"        _3 = const 999: type#8;\n"
        b"        _0 = copy _2(const 10: type#8) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        StorageDead(_3);\n"
        b"        StorageDead(_2);\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 25 (QA Finding 5b): Closure `_2` moved to `_3 = move _2` and passed to `spawn_clos_fn` (`sym=120`, `ESC_THREAD`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#35;\n"
        b"    let mut _3: type#35;\n"
        b"    let _4: type#51;\n"
        b"    bb0: {\n"
        b"        _1 = const 32: type#8;\n"
        b"        _2 = aggregate(variant#0, [const 200: type#15, copy _1]);\n"
        b"        _3 = move _2;\n"
        b"        _4 = const 120: type#51;\n"
        b"        _0 = copy _4(move _3) -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 26 (QA Finding 6): `p as usize` (`_4`) used in `_4 != 0` AND `_6[_4] = 99` / `&_6[_4]`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let _2: type#30;\n"
        b"    let _3: type#19;\n"
        b"    let _4: type#15;\n"
        b"    let _5: type#4;\n"
        b"    let mut _6: type#23;\n"
        b"    let _7: type#17;\n"
        b"    bb0: {\n"
        b"        _2 = const 102: type#30;\n"
        b"        _1 = copy _2(const 42: type#8) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _1.0;\n"
        b"        _4 = copy _3 as type#15 (PtrToInt);\n"
        b"        _5 = copy _4 != const 0: type#15;\n"
        b"        _6 = [const 0: type#8; 4];\n"
        b"        _6[_4] = const 99: type#8;\n"
        b"        _7 = &_6[_4];\n"
        b"        _0 = copy (*_7);\n"
        b"        drop(_1) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 27 (QA Round 2 / Finding 1a): Parameterized 2-arg function (`_1: i32 // arg`, `_2: i32 // arg`)
    # exercising `box_new<i32>` SROA + `NoEscape` closure scalarization/direct-call + bounded `heap_alloc`
    # inline buffer + `NRVO` `Pair` return under `--verify-each`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#20; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    let _2: type#8; // arg\n"
        b"    let mut _3: type#24;\n"
        b"    let _4: type#30;\n"
        b"    let _5: type#19;\n"
        b"    let _6: type#8;\n"
        b"    let mut _7: type#35;\n"
        b"    let _8: type#8;\n"
        b"    let _9: type#28;\n"
        b"    let _10: type#27;\n"
        b"    let _11: type#19;\n"
        b"    let _12: type#29;\n"
        b"    let _13: type#2;\n"
        b"    let _14: type#8;\n"
        b"    let mut _15: type#20;\n"
        b"    bb0: {\n"
        b"        _4 = const 102: type#30;\n"
        b"        _3 = copy _4(copy _1) -> [return: bb1, unwind: bb5];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _5 = copy _3.0;\n"
        b"        _6 = copy (*_5);\n"
        b"        drop(_3) -> [return: bb2, unwind: bb5];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        StorageLive(_7);\n"
        b"        _7 = aggregate(variant#0, [const 200: type#15, copy _2]);\n"
        b"        _8 = copy _7(copy _6) -> [return: bb3, unwind: bb5];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        StorageDead(_7);\n"
        b"        _9 = const 100: type#28;\n"
        b"        _10 = copy _9(const 16: type#15, const 4: type#15) -> [return: bb4, unwind: bb5];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _11 = copy _10 as type#19 (PtrToPtr);\n"
        b"        (*_11) = copy _8;\n"
        b"        _14 = copy (*_11);\n"
        b"        _12 = const 101: type#29;\n"
        b"        _13 = copy _12(copy _10, const 16: type#15, const 4: type#15) -> [return: bb6, unwind: bb5];\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        StorageLive(_15);\n"
        b"        _15.0 = copy _14;\n"
        b"        _15.1 = copy _2;\n"
        b"        _0 = move _15;\n"
        b"        StorageDead(_15);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 28 (QA Round 2 / Finding 1b): Parameterized 1-arg function (`_1: i32 // arg`)
    # exercising `Box<Pair>` `ArgumentEscape` stack promotion (`box_stack_promotions == 1`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    let mut _2: type#20;\n"
        b"    let mut _3: type#25;\n"
        b"    let _4: type#31;\n"
        b"    let _5: type#26;\n"
        b"    let _6: type#21;\n"
        b"    let _7: type#43;\n"
        b"    bb0: {\n"
        b"        _2.0 = copy _1;\n"
        b"        _2.1 = const 25: type#8;\n"
        b"        _4 = const 103: type#31;\n"
        b"        _3 = copy _4(move _2) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _5 = copy _3.0;\n"
        b"        _6 = &mut (*_5);\n"
        b"        _7 = const 114: type#43;\n"
        b"        _0 = copy _7(copy _6) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 29 (QA Round 2 / Finding 1c): Parameterized 1-arg function (`_1: i32 // arg`)
    # with an UNINITIALIZED local `_6: i32` read (`_0 = wrapping_add(copy _5, copy _6)`) to verify
    # `esc_verify_mir_definite_init` still rejects genuine uninitialized local reads when `arg_count >= 1`:
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    let mut _2: type#24;\n"
        b"    let _3: type#30;\n"
        b"    let _4: type#19;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#8;\n"
        b"    bb0: {\n"
        b"        _3 = const 102: type#30;\n"
        b"        _2 = copy _3(copy _1) -> [return: bb1, unwind: bb3];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _4 = copy _2.0;\n"
        b"        _5 = copy (*_4);\n"
        b"        _0 = wrapping_add(copy _5, copy _6);\n"
        b"        drop(_2) -> [return: bb2, unwind: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 30 (QA Round 2 / Finding 3a): Exact QA Round 1 reproducer (`box_new<i32>` + `NRVO` `Pair` `_4`
    # with `switchInt(copy _4.0)` terminator read and conditional field update `_4.1 = const 99`):
    (
        b"mir_body {\n"
        b"    let mut _0: type#20; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let _2: type#19;\n"
        b"    let _3: type#8;\n"
        b"    let mut _4: type#20;\n"
        b"    let _5: type#30;\n"
        b"    bb0: {\n"
        b"        _5 = const 102: type#30;\n"
        b"        _1 = copy _5(const 42: type#8) -> [return: bb1, unwind: bb5];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = copy _1.0;\n"
        b"        _3 = copy (*_2);\n"
        b"        _4.0 = copy _3;\n"
        b"        _4.1 = const 7: type#8;\n"
        b"        switchInt(copy _4.0) -> [0: bb2, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _4.1 = const 99: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        drop(_1) -> [return: bb4, unwind: bb5];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _0 = move _4;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 31 (QA Round 2 / Finding 3b): Parameterized 1-arg `FlagPair` (`type#52`) `NRVO` `_5`
    # whose `bb1` terminator is mutated to `MIR_TERM_ASSERT(cond = copy _5.0)` prior to promotion:
    (
        b"mir_body {\n"
        b"    let mut _0: type#52; // return\n"
        b"    let _1: type#8; // arg\n"
        b"    let mut _2: type#24;\n"
        b"    let _3: type#19;\n"
        b"    let _4: type#8;\n"
        b"    let mut _5: type#52;\n"
        b"    let _6: type#30;\n"
        b"    bb0: {\n"
        b"        _6 = const 102: type#30;\n"
        b"        _2 = copy _6(copy _1) -> [return: bb1, unwind: bb4];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _3 = copy _2.0;\n"
        b"        _4 = copy (*_3);\n"
        b"        _5.0 = const true: type#4;\n"
        b"        _5.1 = copy _4;\n"
        b"        goto -> bb2;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        drop(_2) -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = move _5;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 32 (QA Round 2 / Finding 3c): Multi-`MIR_TERM_RETURN` function (`return_term_count == 2`)
    # verifying `esc_try_promote_nrvo` safely rejects NRVO without rollback:
    (
        b"mir_body {\n"
        b"    let mut _0: type#20; // return\n"
        b"    let mut _1: type#24;\n"
        b"    let _2: type#19;\n"
        b"    let _3: type#8;\n"
        b"    let mut _4: type#20;\n"
        b"    let _5: type#30;\n"
        b"    bb0: {\n"
        b"        _5 = const 102: type#30;\n"
        b"        _1 = copy _5(const 42: type#8) -> [return: bb1, unwind: bb4];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = copy _1.0;\n"
        b"        _3 = copy (*_2);\n"
        b"        _4.0 = copy _3;\n"
        b"        _4.1 = const 7: type#8;\n"
        b"        drop(_1) -> [return: bb2, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _0 = move _4;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
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


def assemble_opt_escape_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", ESCAPE_PROBE_BLOBS))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    escape_modules = list(got.CORE_MODULES) + [
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(escape_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "opt_escape" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: opt_escape_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.opt.escape probe under -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "opt_escape_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "opt_escape_probe_bundle.ax"
    probe_bundle.write_text(assemble_opt_escape_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"opt_escape_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build opt_escape_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"opt_escape_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for opt_escape_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive/negative/drop-order fixtures across --interp, -O0, -O1, -O2 (--verify-each)
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
    inspect_src = tmp_dir / "inspect_escape_mono.ax"
    inspect_src.write_text(
        "struct Pair { a: i64, b: i64 }\n"
        "fn borrow_pair(p: mut_view<Pair>, delta: i64) -> i64 {\n"
        "    p.a = p.a + delta;\n"
        "    p.a + p.b\n"
        "}\n"
        "fn make_pair_nrvo(x: i64) -> Pair {\n"
        "    let mut local_p = Pair { a: x, b: 10 };\n"
        "    let scale: i64 = 3;\n"
        "    let f = |v: i64| -> i64 { v * scale };\n"
        "    let d = f(4);\n"
        "    let _s = borrow_pair(mut_view(local_p), d);\n"
        "    local_p\n"
        "}\n"
        "fn main() -> i32 {\n"
        "    let p = make_pair_nrvo(20);\n"
        "    if p.a + p.b == 42 { 0 } else { 1 }\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    for flag in ("-O0", "-O1", "-O2"):
        o1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        o2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        if o1.returncode != 0 or o2.returncode != 0 or o1.stdout != o2.stdout or not o1.stdout.strip():
            sys.stderr.write(f"deterministic --emit=optir {flag} failed:\n{o1.stderr}\n")
            return 1
        m1 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        m2 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        if m1.returncode != 0 or m2.returncode != 0 or m1.stdout != m2.stdout or not m1.stdout.strip():
            sys.stderr.write(f"deterministic --emit=memssa {flag} failed:\n{m1.stderr}\n")
            return 1

    sys.stdout.buffer.write(b"OPT-ESCAPE-PROMOTE-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
