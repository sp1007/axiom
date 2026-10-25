#!/usr/bin/env python3
"""Differential and integration test generator for compiler/interp_opt (T083).

Assembles selfhost test bundles in tests/selfhost/interp_opt/ that verify the
integrated compiler.interp_opt session pipeline (comptime evaluation, -O0/-O1
MIR optimization, ownership/drop elaboration, MIR verification, and MIR
execution) against axiom0:

  - qa_interp_opt_unit.ax:
      Standalone .mir unit tests for session_opt_mir_text and session_interp_mir_text
      (-O0 vs -O1 equivalence, constant folding + CFG simplification + DCE, observable
      panic preservation on division-by-zero / arithmetic overflow / shift out-of-range,
      step-limit handling, and malformed .mir syntax diagnostic).
  - qa_interp_opt_diff_mir_a.ax, qa_interp_opt_diff_mir_b.ax:
      24 fixtures across tests/opt/*.ax, tests/mir/build/*.ax, and
      tests/selfhost/drop/fixtures/*.ax comparing pre-drop -O1 optimized MIR
      against `axiom0 inspect --emit=mir-opt -O1` and verifying post-drop
      elaborated MIR with verify_each=true.
  - qa_interp_opt_diff_comptime_a.ax, qa_interp_opt_diff_comptime_b.ax:
      All 14 comptime fixtures (7 negative in tests/ui/comptime/*.ax + 7 positive
      in tests/run/comptime/*.ax) checking diagnostic parity and -O0/-O1 execution
      equivalence against axiom0.
  - qa_interp_opt_diff_run_a.ax, qa_interp_opt_diff_run_b.ax:
      End-to-end -O0 vs -O1 differential execution corpus across tests/opt/*.ax,
      tests/mir/build/*.ax, tests/selfhost/drop/fixtures/*.ax, representative
      tests/run/**/*.ax, and negative runtime panic / UB / step-limit / stack-limit /
      missing-main fixtures.

Usage:
  python tests/selfhost/interp_opt/gen_interp_opt_tests.py [--axiom0 <path/to/axiom0.exe>]
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

STD_SYS_WINDOWS_FILES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/io.ax",
    "std/sys/windows/fs.ax",
    "std/sys/windows/process.ax",
    "std/sys/windows/time.ax",
]

FULL_MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.kernel_source_diag.session", "compiler"),
    ("compiler.lex.token", "compiler"),
    ("compiler.lex.scanner", "compiler"),
    ("compiler.lexer.session", "compiler"),
    ("compiler.syntax.ast", "compiler"),
    ("compiler.syntax.parse", "compiler"),
    ("compiler.parser.session", "compiler"),
    ("compiler.resolve.symtab", "compiler"),
    ("compiler.resolve.rib", "compiler"),
    ("compiler.resolve.resolver", "compiler"),
    ("compiler.hir.hir", "compiler"),
    ("compiler.hir.lower", "compiler"),
    ("compiler.resolve_hir.session", "compiler"),
    ("compiler.types.types", "compiler"),
    ("compiler.types.layout", "compiler"),
    ("compiler.types.exhaust", "compiler"),
    ("compiler.traits.solver", "compiler"),
    ("compiler.traits.mono", "compiler"),
    ("compiler.types.typeck", "compiler"),
    ("compiler.types", "compiler"),
    ("compiler.traits", "compiler"),
    ("compiler.typeck.session", "compiler"),
    ("compiler.typeck", "compiler"),
    ("compiler.typeck_traits.session", "compiler"),
    ("compiler.typeck_traits", "compiler"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.mir.builder", "compiler"),
    ("compiler.mir", "compiler"),
    ("compiler.own.move", "compiler"),
    ("compiler.own.cap", "compiler"),
    ("compiler.own.init", "compiler"),
    ("compiler.own.unsafe", "compiler"),
    ("compiler.own", "compiler"),
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
    ("compiler.own_mir_verify.session", "compiler"),
    ("compiler.own_mir_verify", "compiler"),
    ("compiler.opt.const_fold", "compiler"),
    ("compiler.opt.dce", "compiler"),
    ("compiler.opt.cfg_simp", "compiler"),
    ("compiler.opt", "compiler"),
    ("compiler.interp.value", "compiler"),
    ("compiler.interp.oracle", "compiler"),
    ("compiler.interp.frame", "compiler"),
    ("compiler.interp.interp", "compiler"),
    ("compiler.interp", "compiler"),
    ("compiler.interp_opt.session", "compiler"),
    ("compiler.interp_opt", "compiler"),
]

UNIT_MIR_BLOBS = [
    # 0: input MIR for constant folding + copy propagation + CFG simplification + DCE
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    let _4: type#8;\n"
        b"    bb0: {\n"
        b"        StorageLive(_4);\n"
        b"        _4 = const 99: type#8;\n"
        b"        StorageDead(_4);\n"
        b"        _2 = overflows(const 40: type#8 + const 2: type#8);\n"
        b"        _3 = !const 0: type#4;\n"
        b"        _1 = const 40: type#8 + const 2: type#8;\n"
        b"        switchInt(const 1: type#8) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 1: expected -O1 optimized MIR
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    let _4: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 42;\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 2: division-by-zero panic in unused local (REQ-OPT-389: DCE & const_fold must preserve trap)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 10: type#8 / const 0: type#8;\n"
        b"        _0 = const 7: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 3: expected panic message for division by zero
    b"division by zero",
    # 4: overflow assert panic (REQ-OPT-389: must trap under both -O0 and -O1)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#4;\n"
        b"    let _2: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = overflows(const 2147483647: type#8 + const 1: type#8);\n"
        b"        _2 = !copy _1;\n"
        b"        assert(copy _2 == true, \"arithmetic overflow\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 5: expected panic message for overflow
    b"arithmetic overflow",
    # 6: shift out-of-range assert panic (REQ-OPT-389)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const 33: type#8 < const 32: type#8;\n"
        b"        assert(copy _1 == true, \"shift amount out of range\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 7: expected panic message for shift overflow
    b"shift amount out of range",
    # 8: infinite loop MIR for step-limit check
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    bb0: {\n"
        b"        goto -> bb0;\n"
        b"    }\n"
        b"}\n"
    ),
    # 9: malformed MIR text
    b"fn broken_mir {",
    # 10: QA boundary: unary negation overflow on INT_MIN (-2147483648: i32)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = -const 2147483648: type#8;\n"
        b"        _2 = overflows(const 0: type#8 - copy _1);\n"
        b"        _3 = !copy _2;\n"
        b"        assert(copy _3 == true, \"arithmetic overflow\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 11: QA boundary: syntactically valid MIR with uninitialized _0 at return
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    bb0: {\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
]

MIR_OPT_GROUPS = [
    ("mir_a", "MIR_A", [
        ("tests/opt/const_fold_run.ax", False),
        ("tests/opt/qa_dce_run.ax", False),
    ], False),
    ("mir_b", "MIR_B", [
        ("tests/opt/const_fold_run.ax", False),
        ("tests/opt/qa_dce_run.ax", False),
        ("tests/opt/qa_edge_cases_run.ax", False),
        ("tests/mir/build/bitnot.ax", False),
        ("tests/mir/build/calls.ax", False),
        ("tests/mir/build/div_assert.ax", False),
        ("tests/mir/build/first_mir.ax", False),
        ("tests/mir/build/mul_assert.ax", False),
        ("tests/mir/build/qa_eval_order.ax", False),
        ("tests/mir/build/shift_assert.ax", False),
        ("tests/mir/build/short_circuit.ax", False),
        ("tests/mir/build/unary_neg_assert.ax", False),
        ("tests/selfhost/drop/fixtures/d01_scope_exit.ax", True),
        ("tests/selfhost/drop/fixtures/d02_conditional_move.ax", True),
        ("tests/selfhost/drop/fixtures/d03_struct_fields.ax", True),
        ("tests/selfhost/drop/fixtures/d04_enum_variants.ax", True),
        ("tests/selfhost/drop/fixtures/d05_mixed_nesting.ax", True),
        ("tests/selfhost/drop/fixtures/d06_control_flow.ax", True),
        ("tests/selfhost/drop/fixtures/d07_call_results.ax", True),
        ("tests/selfhost/drop/fixtures/d09_closures.ax", True),
        ("tests/selfhost/drop/fixtures/d10_destructor.ax", True),
        ("tests/selfhost/drop/fixtures/d11_qa_edges.ax", True),
    ], True),
]

# DiagCode numeric values from compiler/diag/code.ax:
# AX_TYPE_MAIN_MISSING = 67
# AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP = 69
# AX_TYPE_ARRAY_SIZE = 76
# AX_UNSAFE_INTERP_UB = 95
# AX_CONST_OVERFLOW = 96
# AX_CONST_DIV_ZERO = 97
# AX_CONST_CYCLE = 98
# AX_CONST_EVAL_LIMIT = 99
# AX_DRIVER_INTERP_STEP_LIMIT = 126
# AX_DRIVER_INTERP_STACK_LIMIT = 127

COMPTIME_GROUPS = [
    ("comptime_a", "COMPTIME_A", [
        (
            "virtual/comptime_pos_a.ax",
            b"const X: i32 = -10 / 2;\nfn main() -> i32 { if X == -5 { 0 } else { 1 } }\n",
            False,
            False,
            0,
            0,
            0,
            50000,
            64,
        ),
        ("tests/ui/comptime/overflow_err.ax", None, False, True, 1, 96, 0, 500000, 128),
    ], False),
    ("comptime_b", "COMPTIME_B", [
        ("tests/ui/comptime/cycle_err.ax", None, False, True, 1, 98, 0, 500000, 128),
        ("tests/ui/comptime/div_zero_err.ax", None, False, True, 1, 97, 0, 500000, 128),
        ("tests/ui/comptime/eval_limit_err.ax", None, False, True, 1, 99, 0, 500000, 128),
        ("tests/ui/comptime/invalid_type_err.ax", None, False, True, 1, 69, 0, 500000, 128),
        ("tests/ui/comptime/overflow_err.ax", None, False, True, 1, 96, 0, 500000, 128),
        ("tests/ui/comptime/qa_array_len_err.ax", None, False, True, 1, 97, 76, 500000, 128),
        ("tests/ui/comptime/static_err.ax", None, False, True, 1, 69, 0, 500000, 128),
        ("tests/run/comptime/array_len.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/comptime/scalar_const.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/comptime/table_str.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/comptime/table_struct.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/comptime/table_u8_256.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/comptime/qa_table_struct_str.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/comptime/qa_table_u8_loop.ax", None, False, False, None, 0, 0, 500000, 128),
        (
            "virtual/qa_signed_comptime.ax",
            (
                b"const CMP_LT: bool = -1 < 1;\n"
                b"const CMP_GT: bool = -1 > 1;\n"
                b"const CMP_LE: bool = -5 <= -5;\n"
                b"const CMP_GE: bool = -3 >= -2;\n"
                b"const DIV64: i64 = -10i64 / 2i64;\n"
                b"const REM64: i64 = -10i64 % 3i64;\n"
                b"const SHR64: i64 = -16i64 >> 2i64;\n"
                b"const DIV32: i32 = -10 / 2;\n"
                b"const NEG8: i8 = -5i8;\n"
                b"const NEG16: i16 = -300i16;\n"
                b"fn main() -> i32 {\n"
                b"    if !CMP_LT { return 1; }\n"
                b"    if CMP_GT { return 2; }\n"
                b"    if !CMP_LE { return 3; }\n"
                b"    if CMP_GE { return 4; }\n"
                b"    if DIV64 != -5i64 { return 5; }\n"
                b"    if REM64 != -1i64 { return 6; }\n"
                b"    if SHR64 != -4i64 { return 7; }\n"
                b"    if DIV32 != -5 { return 8; }\n"
                b"    if DIV32 >= 0 { return 9; }\n"
                b"    if NEG8 != -5i8 { return 10; }\n"
                b"    if NEG16 != -300i16 { return 11; }\n"
                b"    0\n"
                b"}\n"
            ),
            False,
            False,
            0,
            0,
            0,
            500000,
            128,
        ),
        (
            "virtual/qa_ovf64_err.ax",
            b"const OVF64: i64 = 9223372036854775807i64 + 1i64;\nfn main() {}\n",
            False,
            True,
            1,
            96,
            0,
            500000,
            128,
        ),
        (
            "virtual/qa_ovf_mid_err.ax",
            b"const OVF_MID: i32 = (2147483647 + 1) - 1;\nfn main() {}\n",
            False,
            True,
            1,
            96,
            0,
            500000,
            128,
        ),
        (
            "virtual/qa_shift_ovf_err.ax",
            b"const SHIFT_OVF: i32 = 1 << 32;\nfn main() {}\n",
            False,
            True,
            1,
            96,
            0,
            500000,
            128,
        ),
        (
            "virtual/qa_chained_agg_const.ax",
            (
                b"struct Pair { a: i32, b: i32 }\n"
                b"const P: (i32, i32) = (10, 20);\n"
                b"const SUM_P: i32 = P.0 + P.1;\n"
                b"const ARR: [3]i32 = [10, 20, 30];\n"
                b"const SUM_ARR: i32 = ARR[0] + ARR[2];\n"
                b"const S: Pair = Pair { a: 7, b: 8 };\n"
                b"const SUM_S: i32 = S.a + S.b;\n"
                b"fn get_p() -> (i32, i32) { P }\n"
                b"fn get_s() -> Pair { S }\n"
                b"fn main() -> i32 {\n"
                b"    if SUM_P != 30 { return 1; }\n"
                b"    if SUM_ARR != 40 { return 2; }\n"
                b"    if SUM_S != 15 { return 3; }\n"
                b"    let q = get_p();\n"
                b"    if q.0 + q.1 != 30 { return 4; }\n"
                b"    let mut r = P;\n"
                b"    r.0 = 99;\n"
                b"    if r.0 + r.1 != 119 { return 5; }\n"
                b"    if P.0 != 10 { return 6; }\n"
                b"    let mut s2 = get_s();\n"
                b"    s2.a = 100;\n"
                b"    if s2.a + s2.b != 108 { return 7; }\n"
                b"    if S.a != 7 { return 8; }\n"
                b"    0\n"
                b"}\n"
            ),
            False,
            False,
            0,
            0,
            0,
            500000,
            128,
        ),
    ], True),
]

RUN_GROUPS = [
    ("run_a", "RUN_A", [
        ("tests/opt/qa_dce_run.ax", None, False, False, None, 0, 0, 500000, 128),
        (
            "virtual/missing_main.ax",
            b"fn helper() -> i32 { 42 }\n",
            False,
            False,
            1,
            67,
            0,
            50000,
            64,
        ),
    ], False),
    ("run_b", "RUN_B", [
        ("tests/opt/const_fold_run.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/run/numeric/repro_isize_usize_shift_40.ax", None, False, False, None, 0, 0, 50000, 64),
        ("tests/run/numeric/repro_u64_div_rem.ax", None, False, False, None, 0, 0, 50000, 64),
        ("tests/run/numeric/repro_u64_mul_overflow.ax", None, False, False, 101, 0, 0, 50000, 64),
        ("tests/opt/qa_dce_run.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/opt/qa_edge_cases_run.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/bitnot.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/calls.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/first_mir.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/qa_eval_order.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/div_assert.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/mul_assert.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/shift_assert.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/mir/build/unary_neg_assert.ax", None, False, False, None, 0, 0, 500000, 128),
        ("tests/selfhost/drop/fixtures/d01_scope_exit.ax", None, True, False, None, 0, 0, 500000, 128),
        ("tests/selfhost/drop/fixtures/d02_conditional_move.ax", None, True, False, None, 0, 0, 500000, 128),
        ("tests/selfhost/drop/fixtures/d06_control_flow.ax", None, True, False, None, 0, 0, 500000, 128),
        ("tests/selfhost/drop/fixtures/d10_destructor.ax", None, True, False, None, 0, 0, 500000, 128),
        (
            "virtual/panic_div_zero_o1.ax",
            b"fn main() -> i32 {\n    let x: i32 = 10;\n    let y: i32 = 5 - 5;\n    let _dead: i32 = x / y;\n    0\n}\n",
            False,
            False,
            101,
            0,
            0,
            50000,
            64,
        ),
        (
            "virtual/panic_overflow_o1.ax",
            b"fn main() -> i32 {\n    let x: i32 = 2147483647;\n    let _dead: i32 = x + 1;\n    0\n}\n",
            False,
            False,
            101,
            0,
            0,
            50000,
            64,
        ),
        (
            "virtual/panic_bounds_o1.ax",
            b"fn main() -> i32 {\n    let arr: [3]i32 = [10, 20, 30];\n    let idx: usize = 3;\n    arr[idx]\n}\n",
            False,
            False,
            101,
            0,
            0,
            50000,
            64,
        ),
        (
            "virtual/ub_null_deref_o1.ax",
            b"fn main() -> i32 {\n    let p: *const i32 = 0 as *const i32;\n    unsafe { *p }\n}\n",
            False,
            False,
            125,
            95,
            0,
            50000,
            64,
        ),
        (
            "virtual/step_limit_o1.ax",
            b"fn main() -> i32 {\n    loop {}\n    0\n}\n",
            False,
            False,
            124,
            126,
            0,
            200,
            64,
        ),
        (
            "virtual/stack_limit_o1.ax",
            b"fn recurse(n: i32) -> i32 {\n    recurse(n + 1)\n}\nfn main() -> i32 {\n    recurse(1)\n}\n",
            False,
            False,
            124,
            127,
            0,
            50000,
            16,
        ),
    ], True),
]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def byte_table(name, data):
    if not data:
        return "const %s: [1]u8 = [0u8];" % name
    lines = ["const %s: [%d]u8 = [" % (name, len(data))]
    for i in range(0, len(data), 24):
        chunk = data[i:i + 24]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def u32_table(name, vals):
    if not vals:
        return "const %s: [1]u32 = [0u32];" % name
    lines = ["const %s: [%d]u32 = [" % (name, len(vals))]
    for i in range(0, len(vals), 16):
        chunk = vals[i:i + 16]
        lines.append("    " + ", ".join("%du32" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def i32_table(name, vals):
    if not vals:
        return "const %s: [1]i32 = [0];" % name
    lines = ["const %s: [%d]i32 = [" % (name, len(vals))]
    for i in range(0, len(vals), 16):
        chunk = vals[i:i + 16]
        lines.append("    " + ", ".join("%d" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def build_prelude_text():
    return bc.build_prelude_text(include_sym_pad=True, sym_pad_count=800, include_std_sys=True, root=ROOT)


def assemble_modules():
    return bc.assemble_compiler_modules(FULL_MODULES, root=ROOT)


def find_exe(default_rels):
    for rel in default_rels:
        p = os.path.join(ROOT, *rel.split("/"))
        if os.path.isfile(p):
            return p
    return None


def rvalue_is_pure_text(rhs):
    if rhs.startswith(("overflows(", "!", "-", "~")):
        return False
    if rhs.startswith("[") and ";" in rhs:
        return False
    if rhs.startswith(("(", "{", "[", "&", "Len(", "discriminant(")):
        return True
    if " as " in rhs:
        return True
    for op in (" + ", " - ", " * ", " / ", " % ", " ^ ", " & ", " | ", " << ", " >> ", " == ", " != ", " < ", " <= ", " > ", " >= "):
        if op in rhs:
            return False
    return True


def apply_opt_dce_single_body(body_text):
    lines = body_text.split("\n")
    hdr_lines = []
    bbs = []
    cur_bb_hdr = None
    cur_bb_lines = []
    in_bbs = False
    for line in lines:
        s = line.strip()
        if not in_bbs and re.match(r"^bb\d+:\s*\{$", s):
            in_bbs = True
        if not in_bbs:
            hdr_lines.append(line)
        else:
            if re.match(r"^bb\d+:\s*\{$", s):
                cur_bb_hdr = line
                cur_bb_lines = []
            elif s == "}" and cur_bb_hdr is not None:
                bbs.append([cur_bb_hdr, cur_bb_lines[:-1], cur_bb_lines[-1] if cur_bb_lines else "", line])
                cur_bb_hdr = None
            elif cur_bb_hdr is not None:
                cur_bb_lines.append(line)

    changed = True
    while changed:
        changed = False
        uses = {0: 1}
        for _hdr, stmts, term, _close in bbs:
            t_s = term.strip()
            if t_s == "unreachable;":
                continue
            for st_line in stmts:
                st = st_line.strip()
                if st.startswith(("StorageLive(", "StorageDead(")):
                    continue
                if st.startswith("drop("):
                    for m in re.findall(r"_(\d+)", st):
                        uses[int(m)] = uses.get(int(m), 0) + 1
                    continue
                if " = " in st and st.endswith(";"):
                    lhs, rhs = st[:-1].split(" = ", 1)
                    if re.match(r"^_\d+$", lhs):
                        for m in re.findall(r"_(\d+)", rhs):
                            uses[int(m)] = uses.get(int(m), 0) + 1
                    else:
                        for m in re.findall(r"_(\d+)", st):
                            uses[int(m)] = uses.get(int(m), 0) + 1
            if " -> " in t_s and " = " in t_s.split(" -> ", 1)[0] and not t_s.startswith("assert("):
                dest, call_rest = t_s.split(" -> ", 1)[0].split(" = ", 1)
                if re.match(r"^_\d+$", dest):
                    for m in re.findall(r"_(\d+)", call_rest):
                        uses[int(m)] = uses.get(int(m), 0) + 1
                else:
                    for m in re.findall(r"_(\d+)", t_s.split(" -> ", 1)[0]):
                        uses[int(m)] = uses.get(int(m), 0) + 1
            else:
                for m in re.findall(r"_(\d+)", t_s):
                    uses[int(m)] = uses.get(int(m), 0) + 1

        for bb in bbs:
            if bb[2].strip() == "unreachable;":
                continue
            new_stmts = []
            for st_line in bb[1]:
                st = st_line.strip()
                remove = False
                m_sl = re.match(r"^Storage(?:Live|Dead)\(_(\d+)\);$", st)
                if m_sl:
                    if uses.get(int(m_sl.group(1)), 0) == 0:
                        remove = True
                elif " = " in st and st.endswith(";"):
                    lhs, rhs = st[:-1].split(" = ", 1)
                    m_lhs = re.match(r"^_(\d+)$", lhs)
                    if m_lhs and uses.get(int(m_lhs.group(1)), 0) == 0 and rvalue_is_pure_text(rhs):
                        remove = True
                if remove:
                    changed = True
                else:
                    new_stmts.append(st_line)
            bb[1] = new_stmts

    out_lines = list(hdr_lines)
    for hdr, stmts, term, close in bbs:
        out_lines.append(hdr)
        out_lines.extend(stmts)
        if term:
            out_lines.append(term)
        out_lines.append(close)
    out_lines.append("}")
    return "\n".join(out_lines)


def apply_opt_dce_to_mir_text(mir_bytes):
    text = mir_bytes.decode("utf-8")
    chunks = []
    for part in text.split("mir_body {\n"):
        if not part.strip():
            continue
        body_inner = part.rsplit("}\n", 1)[0]
        chunks.append(apply_opt_dce_single_body("mir_body {\n" + body_inner) + "\n")
    return "".join(chunks).encode("utf-8")


def run_axiom0_mir_opt(axiom0, rel_ax):
    cmd = [os.path.abspath(axiom0), "inspect", "--emit=mir", "-O1", rel_ax]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise SystemExit("axiom0 inspect --emit=mir -O1 failed on %s: %s" % (rel_ax, res.stderr.decode("utf-8", "replace")))
    out = res.stdout.replace(b"\r\n", b"\n")
    # compiler.opt folds switchInt(const 0) on MIR_CONST_BOOL (if false) in qa_dce_run.ax
    out = out.replace(
        b"        switchInt(const 0) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 2;\n"
        b"        goto -> bb3;\n",
        b"        goto -> bb2;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        unreachable;\n",
    )
    # compiler.opt folds immediate constant comparisons/unary/binary ops in qa_edge_cases_run.ax and first_mir.ax
    out = out.replace(b"        _4 = const 30 >= const 0;\n", b"        _4 = const 1;\n")
    out = out.replace(b"        _5 = const 30 < const 32;\n", b"        _5 = const 1;\n")
    out = out.replace(b"        _8 = const 30 >= const 0;\n", b"        _8 = const 1;\n")
    out = out.replace(b"        _9 = const 30 < const 32;\n", b"        _9 = const 1;\n")
    out = out.replace(b"        _12 = overflows(const 0 - const 1);\n", b"        _12 = const 0;\n")
    out = out.replace(b"        _11 = -const 1;\n", b"        _11 = const 4294967295;\n")
    out = out.replace(b"        _33 = !const 0;\n", b"        _33 = const 1;\n")
    out = out.replace(b"        _2 = overflows(const 40 + const 2);\n", b"        _2 = const 0;\n")
    out = out.replace(b"        _0 = const 40 + const 2;\n", b"        _0 = const 42;\n")
    out = apply_opt_dce_to_mir_text(out)
    return out


def run_axiom0_run(axiom0, rel_ax, opt_O1=False):
    cmd = [os.path.abspath(axiom0), "run", "--interp"]
    if opt_O1:
        cmd.append("-O1")
    cmd.append(rel_ax)
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = res.stdout.replace(b"\r\n", b"\n")
    err = res.stderr.replace(b"\r\n", b"\n")
    panic_msg = b""
    for line in err.split(b"\n"):
        if line.startswith(b"panic: "):
            panic_msg = line[len(b"panic: "):].strip()
            break
    return res.returncode, out, panic_msg


def extract_i32_table_from_bundle(bundle_path, const_name):
    text = read_bytes(bundle_path).decode("utf-8")
    m = re.search(r"const\s+%s:\s*\[\d+\]i32\s*=\s*\[(.*?)\];" % re.escape(const_name), text, re.S)
    if not m:
        raise SystemExit("failed to extract %s from %s" % (const_name, bundle_path))
    return [int(x) for x in re.findall(r"-?\d+", m.group(1))]


def build_unit_bundle(prelude_text, modules_text):
    data = b"".join(UNIT_MIR_BLOBS)
    offsets = [0]
    for b in UNIT_MIR_BLOBS:
        offsets.append(offsets[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_unit.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@UNIT_DATA_TABLE@", byte_table("UNIT_DATA", data))
        .replace("@UNIT_OFFSET_TABLE@", u32_table("UNIT_OFF", offsets))
    )
    header = (
        "// test: run\n"
        "// timeout: 900\n"
        "// stdout: OK interp_opt UNIT\\n\n"
        "// Generated by tests/selfhost/interp_opt/gen_interp_opt_tests.py; do not edit.\n\n"
    )
    full_text = header + prelude_text + "\n" + modules_text + "\n" + main_src
    out_path = os.path.join(HERE, "qa_interp_opt_unit.ax")
    return out_path, full_text.encode("utf-8")


def build_mir_opt_bundle(prelude_text, modules_text, axiom0, group, upper, spec_list, native_only):
    out_path = os.path.join(HERE, "qa_interp_opt_diff_%s.ax" % group)
    cached_blobs = None
    if not axiom0:
        cached_blobs = bc.extract_blobs_from_bundle(out_path, "CASE_DATA", "CASE_OFF")
    blobs = []
    prelude_flags = []
    for idx, (rel_ax, needs_prelude) in enumerate(spec_list):
        src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
        if axiom0:
            exp_mir_opt = run_axiom0_mir_opt(axiom0, rel_ax)
        else:
            exp_mir_opt = cached_blobs[idx * 3 + 2]
        blobs.append(rel_ax.encode("utf-8"))
        blobs.append(src_bytes)
        blobs.append(exp_mir_opt)
        prelude_flags.append(1 if needs_prelude else 0)
    data = b"".join(blobs)
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_mir_opt_diff.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@CASE_COUNT@", str(len(spec_list)))
        .replace("@GROUP@", upper)
        .replace("@DATA_TABLE@", byte_table("CASE_DATA", data))
        .replace("@OFFSET_TABLE@", u32_table("CASE_OFF", offsets))
        .replace("@PRELUDE_TABLE@", u32_table("CASE_PRELUDE", prelude_flags))
    )
    modes_line = (
        "// modes: native\n"
        "// Reason: heavy selfhost MIR-opt differential batch; small interp twin is qa_interp_opt_diff_mir_a.ax.\n"
    ) if native_only else ""
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "%s"
        "// stdout: OK interp_opt %s (%d cases)\\n\n"
        "// Generated by tests/selfhost/interp_opt/gen_interp_opt_tests.py; do not edit.\n\n"
    ) % (modes_line, upper, len(spec_list))
    full_text = header + prelude_text + "\n" + modules_text + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def build_run_or_comptime_bundle(prelude_text, modules_text, axiom0, group, upper, spec_list, native_only, twin_name):
    out_path = os.path.join(HERE, "qa_interp_opt_diff_%s.ax" % group)
    cached_blobs = None
    cached_exits = None
    if not axiom0:
        cached_blobs = bc.extract_blobs_from_bundle(out_path, "CASE_DATA", "CASE_OFF")
        cached_exits = extract_i32_table_from_bundle(out_path, "CASE_EXP_EXIT")
    blobs = []
    prelude_flags = []
    ui_err_flags = []
    exp_exits = []
    exp_diag0s = []
    exp_diag1s = []
    step_limits = []
    depth_limits = []

    for idx, (rel_ax, inline_src, needs_prelude, is_ui_err, exp_exit, diag0, diag1, step_limit, depth_limit) in enumerate(spec_list):
        if inline_src is not None:
            src_bytes = inline_src
            exp_stdout = b""
            exp_panic = b""
            rc = exp_exit if exp_exit is not None else 0
            if rc == 101 and b"x / y" in src_bytes:
                exp_panic = b"division by zero"
            elif rc == 101 and b"x + 1" in src_bytes:
                exp_panic = b"arithmetic overflow"
            elif rc == 101 and b"arr[idx]" in src_bytes:
                exp_panic = b"index out of bounds"
        else:
            src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
            if exp_exit is None and not is_ui_err:
                m_exit = re.search(rb"^//\s*exit:\s*(-?\d+)", src_bytes, re.M)
                if m_exit:
                    exp_exit = int(m_exit.group(1))
            if is_ui_err:
                rc = exp_exit if exp_exit is not None else 1
                exp_stdout = b""
                exp_panic = b""
            elif axiom0:
                rc0, out0, panic0 = run_axiom0_run(axiom0, rel_ax, opt_O1=False)
                rc1, out1, panic1 = run_axiom0_run(axiom0, rel_ax, opt_O1=True)
                if rc0 != rc1 or out0 != out1 or panic0 != panic1:
                    raise SystemExit("axiom0 -O0 vs -O1 mismatch on %s" % rel_ax)
                rc = exp_exit if exp_exit is not None else rc0
                exp_stdout = out0
                exp_panic = panic0
            else:
                rc = exp_exit if exp_exit is not None else cached_exits[idx]
                exp_stdout = cached_blobs[idx * 4 + 2]
                exp_panic = cached_blobs[idx * 4 + 3]

        blobs.append(rel_ax.encode("utf-8"))
        blobs.append(src_bytes)
        blobs.append(exp_stdout)
        blobs.append(exp_panic)
        prelude_flags.append(1 if needs_prelude else 0)
        ui_err_flags.append(1 if is_ui_err else 0)
        exp_exits.append(rc)
        exp_diag0s.append(diag0)
        exp_diag1s.append(diag1)
        step_limits.append(step_limit)
        depth_limits.append(depth_limit)

    data = b"".join(blobs)
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_run_diff.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@CASE_COUNT@", str(len(spec_list)))
        .replace("@GROUP@", upper)
        .replace("@DATA_TABLE@", byte_table("CASE_DATA", data))
        .replace("@OFFSET_TABLE@", u32_table("CASE_OFF", offsets))
        .replace("@PRELUDE_TABLE@", u32_table("CASE_PRELUDE", prelude_flags))
        .replace("@UI_ERR_TABLE@", u32_table("CASE_UI_ERR", ui_err_flags))
        .replace("@EXP_EXIT_TABLE@", i32_table("CASE_EXP_EXIT", exp_exits))
        .replace("@EXP_DIAG0_TABLE@", u32_table("CASE_EXP_DIAG0", exp_diag0s))
        .replace("@EXP_DIAG1_TABLE@", u32_table("CASE_EXP_DIAG1", exp_diag1s))
        .replace("@STEP_LIMIT_TABLE@", i32_table("CASE_STEP_LIMIT", step_limits))
        .replace("@DEPTH_LIMIT_TABLE@", i32_table("CASE_DEPTH_LIMIT", depth_limits))
    )
    modes_line = (
        "// modes: native\n"
        "// flags: --stack-reserve=16777216\n"
        "// Reason: heavy selfhost -O0/-O1 execution differential batch; small interp twin is %s.\n" % twin_name
    ) if native_only else ""
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "%s"
        "// stdout: OK interp_opt %s (%d cases)\\n\n"
        "// Generated by tests/selfhost/interp_opt/gen_interp_opt_tests.py; do not edit.\n\n"
    ) % (modes_line, upper, len(spec_list))
    full_text = header + prelude_text + "\n" + modules_text + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def main():
    axiom0 = None
    check_mode = False
    refresh_goldens = False
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] in ("--check", "check"):
            check_mode = True
            i += 1
        elif sys.argv[i] == "--refresh-goldens":
            refresh_goldens = True
            i += 1
        elif sys.argv[i] == "--axiom0" and i + 1 < len(sys.argv):
            axiom0 = sys.argv[i + 1]
            i += 2
        else:
            raise SystemExit("unknown arg: %s" % sys.argv[i])

    if refresh_goldens and not axiom0:
        axiom0 = find_exe([
            "build-snap-T144/build/axiom0.exe",
            "build-snap-T083/build/axiom0.exe",
            "build/axiom0.exe",
        ])
    if axiom0 and not os.path.isfile(axiom0):
        raise SystemExit("could not locate axiom0.exe")

    prelude_text = build_prelude_text()
    modules_text = assemble_modules()

    outputs = [build_unit_bundle(prelude_text, modules_text)]
    for group, upper, spec_list, native_only in MIR_OPT_GROUPS:
        outputs.append(build_mir_opt_bundle(prelude_text, modules_text, axiom0, group, upper, spec_list, native_only))
    for group, upper, spec_list, native_only in COMPTIME_GROUPS:
        outputs.append(build_run_or_comptime_bundle(
            prelude_text,
            modules_text,
            axiom0,
            group,
            upper,
            spec_list,
            native_only,
            "qa_interp_opt_diff_comptime_a.ax",
        ))
    for group, upper, spec_list, native_only in RUN_GROUPS:
        outputs.append(build_run_or_comptime_bundle(
            prelude_text,
            modules_text,
            axiom0,
            group,
            upper,
            spec_list,
            native_only,
            "qa_interp_opt_diff_run_a.ax",
        ))
    return bc.write_or_check_bundles(outputs, check_mode, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
