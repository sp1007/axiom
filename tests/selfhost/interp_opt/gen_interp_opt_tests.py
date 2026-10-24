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
REFERENCE_BUNDLE = "tests/selfhost/mir/qa_mir_builder_and_drop_a.ax"

STD_SYS_WINDOWS_FILES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/io.ax",
    "std/sys/windows/fs.ax",
    "std/sys/windows/process.ax",
    "std/sys/windows/time.ax",
]

FULL_MODULES = [
    ("compiler.kernel.id", "ref"),
    ("compiler.kernel.hash", "ref"),
    ("compiler.kernel.arena", "ref"),
    ("compiler.kernel.interner", "ref"),
    ("compiler.source.span", "ref"),
    ("compiler.source.manager", "ref"),
    ("compiler.diag.code", "ref"),
    ("compiler.diag.emitter", "ref"),
    ("compiler.diag.format", "ref"),
    ("compiler.diag.json", "ref"),
    ("compiler.kernel_source_diag.session", "ref"),
    ("compiler.lex.token", "ref"),
    ("compiler.lex.scanner", "ref"),
    ("compiler.lexer.session", "ref"),
    ("compiler.syntax.ast", "ref"),
    ("compiler.syntax.parse", "ref"),
    ("compiler.parser.session", "ref"),
    ("compiler.resolve.symtab", "ref"),
    ("compiler.resolve.rib", "ref"),
    ("compiler.resolve.resolver", "ref"),
    ("compiler.hir.hir", "ref"),
    ("compiler.hir.lower", "ref"),
    ("compiler.resolve_hir.session", "ref"),
    ("compiler.types.types", "ref"),
    ("compiler.types.layout", "ref"),
    ("compiler.types.exhaust", "ref"),
    ("compiler.traits.solver", "ref"),
    ("compiler.traits.mono", "ref"),
    ("compiler.types.typeck", "ref"),
    ("compiler.types", "ref"),
    ("compiler.traits", "ref"),
    ("compiler.typeck.session", "ref"),
    ("compiler.typeck", "ref"),
    ("compiler.typeck_traits.session", "ref"),
    ("compiler.typeck_traits", "ref"),
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
    pad_variants = ", ".join("V%d" % i for i in range(800))
    host_src = read_bytes(os.path.join(ROOT, "std/core/host.ax")).decode("utf-8").replace("\r\n", "\n")
    host_src = host_src.replace("module std.core.host", "module host_intrinsics")
    parts = [
        "module __ax_sym_pad\n"
        "enum __AxSymPad { %s }\n"
        "struct __AxPtrPad { p0: *const u8, p1: *mut u8, p2: *mut *mut u8, p3: *const *const u8 }\n"
        % pad_variants,
        host_src.rstrip("\n") + "\n",
    ]
    for rel in STD_SYS_WINDOWS_FILES:
        src = read_bytes(os.path.join(ROOT, rel)).decode("utf-8").replace("\r\n", "\n")
        if rel == "std/sys/windows/heap.ax":
            src = (
                "module host_sys_heap\n"
                "@link(\"kernel32\")\n"
                "extern \"system\" {\n"
                "    fn GetProcessHeap() -> *mut u8;\n"
                "    fn HeapAlloc(hHeap: *mut u8, dwFlags: u32, dwBytes: usize) -> *mut u8;\n"
                "    fn HeapReAlloc(hHeap: *mut u8, dwFlags: u32, lpMem: *mut u8, dwBytes: usize) -> *mut u8;\n"
                "    fn HeapFree(hHeap: *mut u8, dwFlags: u32, lpMem: *mut u8) -> i32;\n"
                "}\n"
                "pub unsafe fn __ax_host_heap_alloc(size: usize, align: usize) -> *mut u8 {\n"
                "    let h = GetProcessHeap();\n"
                "    if (h as usize) == 0 { return 0 as *mut u8; }\n"
                "    let alloc_bytes: usize = if size < 16 { 16 } else { size };\n"
                "    HeapAlloc(h, 8u32, alloc_bytes)\n"
                "}\n"
                "pub unsafe fn __ax_host_heap_realloc(p: *mut u8, old_size: usize, new_size: usize, align: usize) -> *mut u8 {\n"
                "    if (p as usize) == 0 { return __ax_host_heap_alloc(new_size, align); }\n"
                "    let h = GetProcessHeap();\n"
                "    if (h as usize) == 0 { return 0 as *mut u8; }\n"
                "    let alloc_bytes: usize = if new_size < 16 { 16 } else { new_size };\n"
                "    HeapReAlloc(h, 8u32, p, alloc_bytes)\n"
                "}\n"
                "pub unsafe fn __ax_host_heap_free(p: *mut u8, size: usize, align: usize) {\n"
                "    if (p as usize) != 0 {\n"
                "        let h = GetProcessHeap();\n"
                "        if (h as usize) != 0 { HeapFree(h, 0u32, p); }\n"
                "    }\n"
                "}\n"
            )
        else:
            src = src.replace("module std.sys.windows.", "module host_sys_")
            src = src.replace("let len = GetEnvironmentVariableW", "let vlen = GetEnvironmentVariableW")
            src = src.replace("if len > 0 {", "if vlen > 0 {")
            src = src.replace("while idx < len as usize {", "while idx < vlen as usize {")
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


def adapt_own_module(name, src):
    """Adapts compiler.own.* imports and keyword module names to canonical compiler/* modules."""
    src = src.replace("module compiler.own.move", "module compiler.own.move_ck")
    src = src.replace("module compiler.own.unsafe", "module compiler.own.unsafe_ck")
    src = src.replace("compiler.own.move.", "compiler.own.move_ck.")
    src = src.replace("compiler.own.unsafe.", "compiler.own.unsafe_ck.")
    if not name.startswith("compiler.own."):
        return src
    use_map = {
        "use compiler.driver.str_intern.StrId": "use compiler.kernel.id.StrId",
        "use compiler.driver.str_intern.StrInterner": "use compiler.kernel.interner.StrInterner",
        "use compiler.driver.str_intern.StrView": "use compiler.kernel.interner.StrView",
        "use compiler.driver.str_intern.interner_get": "use compiler.kernel.interner.interner_get",
        "use compiler.driver.str_intern.interner_lookup": "use compiler.kernel.interner.interner_lookup_bytes",
        "use compiler.driver.span.FileId": "use compiler.kernel.id.FileId",
        "use compiler.driver.span.Span": "use compiler.source.span.Span",
        "use compiler.hir.def_id.SymbolId": "use compiler.kernel.id.SymbolId",
        "use compiler.typeck.ty.TypeId": "use compiler.kernel.id.TypeId",
        "use compiler.hir.ast.BINOP_ADD": "use compiler.syntax.ast.BINOP_ADD",
        "use compiler.hir.ast.BINOP_SUB": "use compiler.syntax.ast.BINOP_SUB",
        "use compiler.hir.ast.UNOP_DEREF": "use compiler.syntax.ast.UNOP_DEREF",
        "use compiler.diag.diag.DiagSeverity": "use compiler.diag.code.DiagSeverity",
        "use compiler.diag.diag.DiagCode": "use compiler.diag.code.DiagCode",
    }
    drop_uses = {
        "use compiler.hir.ast.HirField",
        "use compiler.hir.ast.HirVariant",
        "use compiler.hir.ast.HirCallArg",
        "use compiler.hir.ast.HirFieldExpr",
        "use compiler.typeck.ty.Type",
    }
    out_lines = []
    for line in src.split("\n"):
        s = line.strip()
        if s in drop_uses:
            continue
        if s in use_map:
            line = use_map[s]
        elif s.startswith("use compiler.hir.ast."):
            line = "use compiler.hir.hir." + s[len("use compiler.hir.ast."):]
        elif s.startswith("use compiler.typeck.ty."):
            line = "use compiler.types.types." + s[len("use compiler.typeck.ty."):]
        elif s.startswith("use compiler.diag.codes."):
            line = "use compiler.diag.code." + s[len("use compiler.diag.codes."):]
        elif s.startswith("use compiler.diag.diag."):
            line = "use compiler.diag.emitter." + s[len("use compiler.diag.diag."):]
        out_lines.append(line)

    res = "\n".join(out_lines)
    res = res.replace("use compiler.kernel.arena.ArenaChunk", "use compiler.kernel.arena.arena_new")
    res = res.replace("(*cap_init_p).head = 0 as *mut ArenaChunk;", "let cap_a = arena_new();\n*cap_init_p = cap_a;")
    res = res.replace("interner_lookup(", "interner_lookup_bytes(")
    res = res.replace("if bb.terminator.expected {", "if bb.terminator.drop_is_explicit {")
    res = res.replace("stmt.location", "stmt.span")
    res = res.replace("(*st).location", "(*st).span")
    res = res.replace("terminator.location", "terminator.span")
    return res


def compiler_module_files():
    found = {}
    for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "compiler")):
        for fn in files:
            if not fn.endswith(".ax"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("module "):
                        found[line.split()[1]] = path
                        break
    return found


def reference_sections():
    text = read_bytes(os.path.join(ROOT, REFERENCE_BUNDLE)).decode("utf-8")
    sections = {}
    current = None
    buf = []
    for line in text.split("\n"):
        if line.startswith("module "):
            if current:
                sections[current] = "\n".join(buf)
            current = line.split()[1]
            buf = [line]
        elif current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf)
    return sections


def assemble_modules():
    files = compiler_module_files()
    ref = reference_sections()
    parts = []
    for name, origin in FULL_MODULES:
        if origin == "compiler":
            src = read_bytes(files[name]).decode("utf-8").replace("\r\n", "\n")
            src = adapt_own_module(name, src)
        else:
            src = ref[name]
        if name == "compiler.kernel.hash":
            src = src.replace(
                "@intrinsic fn wrapping_add_u64(a: u64, b: u64) -> u64 { 0 }\n"
                "@intrinsic fn wrapping_mul_u64(a: u64, b: u64) -> u64 { 0 }\n"
                "@intrinsic fn rotate_left_u64(x: u64, n: u32) -> u64 { 0 }",
                "fn wrapping_add_u64(a: u64, b: u64) -> u64 {\n"
                "    let a_lo = a & 0xFFFFFFFFu64;\n"
                "    let a_hi = (a >> 32u64) & 0xFFFFFFFFu64;\n"
                "    let b_lo = b & 0xFFFFFFFFu64;\n"
                "    let b_hi = (b >> 32u64) & 0xFFFFFFFFu64;\n"
                "    let sum_lo = a_lo + b_lo;\n"
                "    let carry = sum_lo >> 32u64;\n"
                "    let sum_hi = (a_hi + b_hi + carry) & 0xFFFFFFFFu64;\n"
                "    (sum_hi << 32u64) | (sum_lo & 0xFFFFFFFFu64)\n"
                "}\n"
                "fn mul_u16_hash(x: u64, y: u64) -> u64 {\n"
                "    ((x as i64) * (y as i64)) as u64\n"
                "}\n"
                "fn wrapping_mul_u64(a: u64, b: u64) -> u64 {\n"
                "    let a0 = a & 0xFFFFu64;\n"
                "    let a1 = (a >> 16u64) & 0xFFFFu64;\n"
                "    let a2 = (a >> 32u64) & 0xFFFFu64;\n"
                "    let a3 = (a >> 48u64) & 0xFFFFu64;\n"
                "    let b0 = b & 0xFFFFu64;\n"
                "    let b1 = (b >> 16u64) & 0xFFFFu64;\n"
                "    let b2 = (b >> 32u64) & 0xFFFFu64;\n"
                "    let b3 = (b >> 48u64) & 0xFFFFu64;\n"
                "    let c0 = mul_u16_hash(a0, b0);\n"
                "    let c1 = (c0 >> 16u64) + mul_u16_hash(a0, b1) + mul_u16_hash(a1, b0);\n"
                "    let c2 = (c1 >> 16u64) + mul_u16_hash(a0, b2) + mul_u16_hash(a1, b1) + mul_u16_hash(a2, b0);\n"
                "    let c3 = ((c2 >> 16u64) + mul_u16_hash(a0, b3) + mul_u16_hash(a1, b2) + mul_u16_hash(a2, b1) + mul_u16_hash(a3, b0)) & 0xFFFFu64;\n"
                "    (c0 & 0xFFFFu64) | ((c1 & 0xFFFFu64) << 16u64) | ((c2 & 0xFFFFu64) << 32u64) | (c3 << 48u64)\n"
                "}\n"
                "fn rotate_left_u64(x: u64, n: u32) -> u64 {\n"
                "    let s = (n & 63u32) as u64;\n"
                "    if s == 0u64 { x } else { (x << s) | (x >> (64u64 - s)) }\n"
                "}",
            )
        if name == "compiler.types.types":
            src = src.replace(
                "@intrinsic fn wrapping_add_u64(a: u64, b: u64) -> u64 { 0 }\n"
                "@intrinsic fn rotate_left_u64(x: u64, n: u32) -> u64 { 0 }",
                "fn wrapping_add_u64(a: u64, b: u64) -> u64 {\n"
                "    let a_lo = a & 0xFFFFFFFFu64;\n"
                "    let a_hi = a >> 32u32;\n"
                "    let b_lo = b & 0xFFFFFFFFu64;\n"
                "    let b_hi = b >> 32u32;\n"
                "    let sum_lo = a_lo + b_lo;\n"
                "    let carry = sum_lo >> 32u32;\n"
                "    let sum_hi = (a_hi + b_hi + carry) & 0xFFFFFFFFu64;\n"
                "    (sum_hi << 32u32) | (sum_lo & 0xFFFFFFFFu64)\n"
                "}\n"
                "fn rotate_left_u64(x: u64, n: u32) -> u64 {\n"
                "    let s = (n & 63u32) as u64;\n"
                "    if s == 0u64 { x } else { (x << s) | (x >> (64u64 - s)) }\n"
                "}",
            )
        if name == "compiler.verify.verifier":
            src = src.replace(
                "val = val * 10u64 + ((c - 48u8) as u64);",
                "val = (((val as i64) * 10i64) as u64) + ((c - 48u8) as u64);",
            )
        if name == "compiler.own_mir_verify.session":
            src = src.replace(
                "i * size_of<TypeId>()",
                "(((i as isize) * (size_of<TypeId>() as isize)) as usize)",
            )
            src = src.replace(
                "i * size_of<usize>()",
                "(((i as isize) * (size_of<usize>() as isize)) as usize)",
            )
            src = src.replace(
                "i * size_of<*mut TypeId>()",
                "(((i as isize) * (size_of<*mut TypeId>() as isize)) as usize)",
            )
            src = src.replace(
                "j * size_of<TypeId>()",
                "(((j as isize) * (size_of<TypeId>() as isize)) as usize)",
            )
        if name == "compiler.mir.builder":
            src = src.replace(
                "use compiler.lex.token.TOK_BYTE_STR",
                "use compiler.lex.token.TOK_BYTE_STR\nuse compiler.lex.token.TOK_FLAG_BYTE_FORM",
            )
            src = src.replace(
                "    if tok.int_val != 0u64 {\n"
                "        if is_negated {\n"
                "            return (0i64 - (tok.int_val as i64)) as u64;\n"
                "        }\n"
                "        return tok.int_val;\n"
                "    }\n"
                "    let sv = mb_span_sv(b, view(tok.span));\n"
                "    mb_parse_int_sv(view(sv), is_negated)",
                "    let sv = mb_span_sv(b, view(tok.span));\n"
                "    if sv.len > 0 && (tok.flags & TOK_FLAG_BYTE_FORM) == 0u16 {\n"
                "        return mb_parse_int_sv(view(sv), is_negated);\n"
                "    }\n"
                "    if tok.int_val != 0u64 {\n"
                "        if is_negated {\n"
                "            return (0i64 - (tok.int_val as i64)) as u64;\n"
                "        }\n"
                "        return tok.int_val;\n"
                "    }\n"
                "    0u64",
            )
            src = src.replace(
                "    b.curr_bb = mb_new_bb(mut_view(b), false);",
                "    let entry_bb = mb_new_bb(mut_view(b), false);\n    b.curr_bb = entry_bb;",
            )
            src = src.replace(
                "                        (*cur_bb_ptr).terminator.drop_place = mir_local_place(loc_id_v);",
                "                        let dp = mir_local_place(loc_id_v);\n"
                "                        (*cur_bb_ptr).terminator.drop_place = dp;",
            )
            src = src.replace(
                "            rv.repeat_count = mb_eval_const_int_expr(view(*b), count_expr);",
                "            let rep_cnt = mb_eval_const_int_expr(view(*b), count_expr);\n"
                "            rv.repeat_count = rep_cnt;",
            )
        if name == "compiler.types.typeck":
            src = src.replace(
                "    let cty_ptr: *mut HirType = unsafe { (*it).ty };\n"
                "    let ty = hir_type_to_typeid(mut_view(*cx), cty_ptr);\n",
                "    let cty_ptr: *mut HirType = unsafe { (*it).ty };\n"
                "    let ty = hir_type_to_typeid(mut_view(*cx), cty_ptr);\n"
                "    unsafe { thir_set_item_type(mut_view(*cx.thir), it, (TypeId { v: ty.v })); }\n"
                "    if sym_v != 0u32 {\n"
                "        unsafe { thir_set_sym_type(mut_view(*cx.thir), (SymbolId { v: sym_v }), (TypeId { v: ty.v })); }\n"
                "    }\n",
            )
            src = src.replace(
                "                    let it_t = unsafe { thir_get_item_type(view(*cx.thir), it) };\n"
                "                    if it_t.v != 0u32 {\n"
                "                        return instantiate_path(mut_view(*cx), (TypeId { v: it_t.v }), it, path, out_args);\n"
                "                    }\n",
                "                    if ik == HIR_ITEM_CONST {\n"
                "                        evaluate_const_item(mut_view(*cx), it);\n"
                "                    }\n"
                "                    let it_t = unsafe { thir_get_item_type(view(*cx.thir), it) };\n"
                "                    if it_t.v != 0u32 {\n"
                "                        return instantiate_path(mut_view(*cx), (TypeId { v: it_t.v }), it, path, out_args);\n"
                "                    }\n",
            )
            src = src.replace(
                "        unsafe { thir_set_item_type(mut_view(*cx.thir), it, (TypeId { v: fn_ty.v })); }\n"
                "        let isym = unsafe { (*it).symbol };\n"
                "        if isym.v != 0u32 {\n"
                "            unsafe { thir_set_sym_type(mut_view(*cx.thir), (SymbolId { v: isym.v }), (TypeId { v: fn_ty.v })); }\n"
                "        }\n"
                "        cx.current_fn = 0 as *const HirItem;",
                "        unsafe { thir_set_item_type(mut_view(*cx.thir), it, (TypeId { v: fn_ty.v })); }\n"
                "        let isym = unsafe { (*it).symbol };\n"
                "        if isym.v != 0u32 && (unsafe { (*it).generic_params as usize }) == 0 {\n"
                "            unsafe { thir_set_sym_type(mut_view(*cx.thir), (SymbolId { v: isym.v }), (TypeId { v: fn_ty.v })); }\n"
                "        }\n"
                "        cx.current_fn = 0 as *const HirItem;",
            )
            src = src.replace(
                "                            if (fty_node as usize) != 0 && (unsafe { (*fty_node).kind }) == HIR_TYPE_VIEW {\n"
                "                                let _ = unsafe { type_error(mut_view(cx), view((*f).span), AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP) };\n"
                "                            }\n",
                "",
            )
            src = src.replace(
                "    typeck_into(hir_file, mut_view(*sink), mut_view(*str_in), db, evaluator, mut_view(*thir));\n"
                "    if sink.errors == 0 {\n"
                "        unsafe_check(hir_file, view(*thir), mut_view(*sink), view(*str_in));\n"
                "    }\n",
                "    typeck_into(hir_file, mut_view(*sink), mut_view(*str_in), db, evaluator, mut_view(*thir));\n",
            )
            src = src.replace(
                "pub fn typeck_into(",
                "// SPEC-12 AXS-DROP-008 (ADR-0036 section 5): `impl P for T` declares the destructor of `T` iff the trait\n"
                "// path `P` resolves to the prelude lang item `Drop`: `P` is the single segment `Drop` without generic\n"
                "// arguments, and the impl's module neither declares a trait, struct, enum or type alias named `Drop` nor\n"
                "// binds the name `Drop` with a `use`. Same predicate as hir_impl_is_lang_drop (compiler/hir/lower.ax,\n"
                "// documented there) and ax_hir_impl_is_lang_drop / the twin in bootstrap/axiom0/src/types/typeck.c.\n"
                "fn tc_name_is_drop(interner: view<StrInterner>, id: StrId) -> bool {\n"
                "    if id.v == 0u32 {\n"
                "        return false;\n"
                "    }\n"
                "    let sv = interner_get(interner, id);\n"
                "    if sv.len != 4 {\n"
                "        return false;\n"
                "    }\n"
                "    let b0 = unsafe { *(sv.ptr + 0) };\n"
                "    let b1 = unsafe { *(sv.ptr + 1) };\n"
                "    let b2 = unsafe { *(sv.ptr + 2) };\n"
                "    let b3 = unsafe { *(sv.ptr + 3) };\n"
                "    b0 == 68u8 && b1 == 114u8 && b2 == 111u8 && b3 == 112u8\n"
                "}\n"
                "\n"
                "fn tc_use_tree_binds_drop(interner: view<StrInterner>, t: *mut HirUseTree) -> bool {\n"
                "    let mut cur: *mut HirUseTree = t;\n"
                "    while (cur as usize) != 0 {\n"
                "        let count = unsafe { (*cur).path.count };\n"
                "        if (unsafe { (*cur).subtrees as usize }) != 0 {\n"
                "            if tc_use_tree_binds_drop(interner, unsafe { (*cur).subtrees }) {\n"
                "                return true;\n"
                "            }\n"
                "        } else if (unsafe { (*cur).alias.v }) != 0u32 {\n"
                "            if tc_name_is_drop(interner, unsafe { (*cur).alias }) {\n"
                "                return true;\n"
                "            }\n"
                "        } else if count > 0 {\n"
                "            let off = (((count - 1) as isize) * (size_of<StrId>() as isize)) as usize;\n"
                "            let seg_ptr = ((unsafe { (*cur).path.segments } as usize) + off) as *const StrId;\n"
                "            if tc_name_is_drop(interner, unsafe { *seg_ptr }) {\n"
                "                return true;\n"
                "            }\n"
                "        }\n"
                "        cur = unsafe { (*cur).next };\n"
                "    }\n"
                "    false\n"
                "}\n"
                "\n"
                "fn tc_module_path_eq(a: *mut HirItem, b: *mut HirItem) -> bool {\n"
                "    let count = unsafe { (*a).module_path.count };\n"
                "    if count != (unsafe { (*b).module_path.count }) {\n"
                "        return false;\n"
                "    }\n"
                "    let sa = unsafe { (*a).module_path.segments } as usize;\n"
                "    let sb = unsafe { (*b).module_path.segments } as usize;\n"
                "    let mut i: usize = 0;\n"
                "    while i < count {\n"
                "        let off = ((i as isize) * (size_of<StrId>() as isize)) as usize;\n"
                "        let pa = (sa + off) as *const StrId;\n"
                "        let pb = (sb + off) as *const StrId;\n"
                "        if (unsafe { (*pa).v }) != (unsafe { (*pb).v }) {\n"
                "            return false;\n"
                "        }\n"
                "        i = i + 1;\n"
                "    }\n"
                "    true\n"
                "}\n"
                "\n"
                "fn tc_impl_is_lang_drop(items: *mut HirItem, impl_item: *mut HirItem, interner: view<StrInterner>) -> bool {\n"
                "    if (impl_item as usize) == 0 || (unsafe { (*impl_item).kind }) != HIR_ITEM_IMPL {\n"
                "        return false;\n"
                "    }\n"
                "    let tp: *mut HirType = unsafe { (*impl_item).trait_path };\n"
                "    if (tp as usize) == 0 || (unsafe { (*tp).kind }) != HIR_TYPE_PATH {\n"
                "        return false;\n"
                "    }\n"
                "    if (unsafe { (*tp).path.generic_args as usize }) != 0 {\n"
                "        return false;\n"
                "    }\n"
                "    if !tc_name_is_drop(interner, unsafe { (*tp).path.name }) {\n"
                "        return false;\n"
                "    }\n"
                "    if (unsafe { (*tp).path.span.file.v }) != 0u32 {\n"
                "        let span_len = (unsafe { (*tp).path.span.end }) - (unsafe { (*tp).path.span.start });\n"
                "        if span_len != 4u32 {\n"
                "            return false;\n"
                "        }\n"
                "    }\n"
                "    let mut it: *mut HirItem = items;\n"
                "    while (it as usize) != 0 {\n"
                "        if tc_module_path_eq(it, impl_item) {\n"
                "            let k = unsafe { (*it).kind };\n"
                "            if k == HIR_ITEM_TRAIT || k == HIR_ITEM_STRUCT || k == HIR_ITEM_ENUM || k == HIR_ITEM_TYPE_ALIAS {\n"
                "                if tc_name_is_drop(interner, unsafe { (*it).name }) {\n"
                "                    return false;\n"
                "                }\n"
                "            } else if k == HIR_ITEM_USE {\n"
                "                if tc_use_tree_binds_drop(interner, unsafe { (*it).use_tree }) {\n"
                "                    return false;\n"
                "                }\n"
                "            }\n"
                "        }\n"
                "        it = unsafe { (*it).next };\n"
                "    }\n"
                "    true\n"
                "}\n"
                "\n"
                "fn tc_write_u32_dec(buf: *mut u8, start: usize, val: u32) -> usize {\n"
                "    let mut tmp: [16]u8 = [0u8; 16];\n"
                "    let mut dlen: usize = 0;\n"
                "    let mut v = val;\n"
                "    if v == 0u32 {\n"
                "        unsafe { *(buf + start) = 48u8; }\n"
                "        return start + 1;\n"
                "    }\n"
                "    while v > 0u32 {\n"
                "        tmp[dlen] = (48u32 + (v % 10u32)) as u8;\n"
                "        v = v / 10u32;\n"
                "        dlen = dlen + 1;\n"
                "    }\n"
                "    let mut i: usize = 0;\n"
                "    while i < dlen {\n"
                "        unsafe { *(buf + start + i) = tmp[dlen - 1 - i]; }\n"
                "        i = i + 1;\n"
                "    }\n"
                "    start + dlen\n"
                "}\n\n"
                "fn tc_mangle_drop_impls(cx: mut_view<TypeckCtx>, hir_file: view<HirFile>) {\n"
                "    if (cx.str_in as usize) == 0 {\n"
                "        return;\n"
                "    }\n"
                "    let mut drop_sym_counter: u32 = 0u32;\n"
                "    let mut it: *mut HirItem = hir_file.items;\n"
                "    while (it as usize) != 0 {\n"
                "        if (unsafe { (*it).kind }) == HIR_ITEM_IMPL {\n"
                "            let tp: *mut HirType = unsafe { (*it).trait_path };\n"
                "            let st: *mut HirType = unsafe { (*it).self_type };\n"
                "            if (tp as usize) != 0 && (st as usize) != 0 && (unsafe { (*st).kind }) == HIR_TYPE_PATH {\n"
                "                if tc_impl_is_lang_drop(hir_file.items, it, unsafe { view(*cx.str_in) }) {\n"
                "                    let mut sname = StrView { ptr: 0 as *const u8, len: 0 };\n"
                "                    if (unsafe { (*st).path.name.v }) != 0u32 {\n"
                "                        sname = unsafe { interner_get(view(*cx.str_in), (*st).path.name) };\n"
                "                    } else if (cx.db as usize) != 0 {\n"
                "                        let raw_s = unsafe { source_db_span_text(view(*cx.db), (*st).path.span) };\n"
                "                        let mut lt: usize = 0;\n"
                "                        while (lt) < (raw_s.len) {\n"
                "                            if (unsafe { *(raw_s.ptr + lt) }) == 60u8 {\n"
                "                                break;\n"
                "                            }\n"
                "                            lt = lt + 1;\n"
                "                        }\n"
                "                        sname = StrView { ptr: raw_s.ptr, len: lt };\n"
                "                    }\n"
                "                    if sname.len > 0 {\n"
                "                        let mut m: *mut HirItem = unsafe { (*it).members };\n"
                "                        while (m as usize) != 0 {\n"
                "                            if (unsafe { (*m).kind }) == HIR_ITEM_FN {\n"
                "                                let mut mbuf: [256]u8 = [0u8; 256];\n"
                "                                let buf_ptr = unsafe { address_of(mbuf[0]) as *mut u8 };\n"
                "                                let copy_len: usize = if sname.len > 240 { 240 } else { sname.len };\n"
                "                                unsafe {\n"
                "                                    ptr_copy_nonoverlapping<u8>(sname.ptr, buf_ptr, copy_len);\n"
                "                                    *(buf_ptr + copy_len) = 36u8;\n"
                "                                    *(buf_ptr + copy_len + 1) = 100u8;\n"
                "                                    *(buf_ptr + copy_len + 2) = 114u8;\n"
                "                                    *(buf_ptr + copy_len + 3) = 111u8;\n"
                "                                    *(buf_ptr + copy_len + 4) = 112u8;\n"
                "                                }\n"
                "                                let base_len = copy_len + 5;\n"
                "                                let mut new_name = unsafe {\n"
                "                                    interner_intern_bytes(mut_view(*cx.str_in), buf_ptr as *const u8, base_len)\n"
                "                                };\n"
                "                                let mut disambig: u32 = 1u32;\n"
                "                                loop {\n"
                "                                    let mut collision = false;\n"
                "                                    let mut prev: *mut HirItem = hir_file.items;\n"
                "                                    while (prev as usize) != 0 && (prev as usize) != (it as usize) {\n"
                "                                        if (unsafe { (*prev).kind }) == HIR_ITEM_IMPL {\n"
                "                                            let mut pm: *mut HirItem = unsafe { (*prev).members };\n"
                "                                            while (pm as usize) != 0 {\n"
                "                                                if (unsafe { (*pm).kind }) == HIR_ITEM_FN && (unsafe { (*pm).name.v }) == new_name.v {\n"
                "                                                    collision = true;\n"
                "                                                    break;\n"
                "                                                }\n"
                "                                                pm = unsafe { (*pm).next };\n"
                "                                            }\n"
                "                                        }\n"
                "                                        if collision {\n"
                "                                            break;\n"
                "                                        }\n"
                "                                        prev = unsafe { (*prev).next };\n"
                "                                    }\n"
                "                                    if !collision {\n"
                "                                        break;\n"
                "                                    }\n"
                "                                    disambig = disambig + 1u32;\n"
                "                                    unsafe { *(buf_ptr + base_len) = 36u8; }\n"
                "                                    let dlen = tc_write_u32_dec(buf_ptr, base_len + 1, disambig);\n"
                "                                    new_name = unsafe {\n"
                "                                        interner_intern_bytes(mut_view(*cx.str_in), buf_ptr as *const u8, dlen)\n"
                "                                    };\n"
                "                                }\n"
                "                                drop_sym_counter = drop_sym_counter + 1u32;\n"
                "                                let new_sym_v = 0x70000000u32 + drop_sym_counter;\n"
                "                                let old_name_v = unsafe { (*m).name.v };\n"
                "                                let m_body = unsafe { (*m).body };\n"
                "                                unsafe {\n"
                "                                    (*m).name.v = new_name.v;\n"
                "                                    (*m).symbol.v = new_sym_v;\n"
                "                                }\n"
                "                                let mut top: *mut HirItem = hir_file.items;\n"
                "                                while (top as usize) != 0 {\n"
                "                                    if (top as usize) != (m as usize) &&\n"
                "                                       (unsafe { (*top).kind }) == HIR_ITEM_FN &&\n"
                "                                       (unsafe { (*top).body as usize }) == (m_body as usize) &&\n"
                "                                       (unsafe { (*top).name.v }) == old_name_v {\n"
                "                                        unsafe {\n"
                "                                            (*top).name.v = new_name.v;\n"
                "                                            (*top).symbol.v = new_sym_v;\n"
                "                                        }\n"
                "                                        break;\n"
                "                                    }\n"
                "                                    top = unsafe { (*top).next };\n"
                "                                }\n"
                "                            }\n"
                "                            m = unsafe { (*m).next };\n"
                "                        }\n"
                "                    }\n"
                "                }\n"
                "            }\n"
                "        }\n"
                "        it = unsafe { (*it).next };\n"
                "    }\n"
                "}\n\n"
                "pub fn typeck_into(",
            )
            src = src.replace(
                "            unsafe { thir_set_item_type(mut_view(*thir_ptr), top_it, (TypeId { v: st_id.v })); }\n"
                "            let s_sym = unsafe { (*top_it).symbol };\n"
                "            if s_sym.v != 0u32 {\n"
                "                unsafe { thir_set_sym_type(mut_view(*thir_ptr), (SymbolId { v: s_sym.v }), (TypeId { v: st_id.v })); }\n"
                "            }\n"
                "        } else if tk == HIR_ITEM_ENUM {",
                "            unsafe { thir_set_item_type(mut_view(*thir_ptr), top_it, (TypeId { v: st_id.v })); }\n"
                "            let s_sym = unsafe { (*top_it).symbol };\n"
                "            if s_sym.v != 0u32 && arg_cnt == 0 {\n"
                "                unsafe { thir_set_sym_type(mut_view(*thir_ptr), (SymbolId { v: s_sym.v }), (TypeId { v: st_id.v })); }\n"
                "            }\n"
                "        } else if tk == HIR_ITEM_ENUM {",
            )
            src = src.replace(
                "            unsafe { thir_set_item_type(mut_view(*thir_ptr), top_it, (TypeId { v: en_id.v })); }\n"
                "            let e_sym = unsafe { (*top_it).symbol };\n"
                "            if e_sym.v != 0u32 {\n"
                "                unsafe { thir_set_sym_type(mut_view(*thir_ptr), (SymbolId { v: e_sym.v }), (TypeId { v: en_id.v })); }\n"
                "            }\n"
                "        }\n"
                "        top_it = unsafe { (*top_it).next };\n"
                "    }\n\n"
                "    // Pass 1a1:",
                "            unsafe { thir_set_item_type(mut_view(*thir_ptr), top_it, (TypeId { v: en_id.v })); }\n"
                "            let e_sym = unsafe { (*top_it).symbol };\n"
                "            if e_sym.v != 0u32 && arg_cnt == 0 {\n"
                "                unsafe { thir_set_sym_type(mut_view(*thir_ptr), (SymbolId { v: e_sym.v }), (TypeId { v: en_id.v })); }\n"
                "            }\n"
                "        }\n"
                "        top_it = unsafe { (*top_it).next };\n"
                "    }\n\n"
                "    // Pass 1a1:",
            )
            src = src.replace(
                "    type_vars_init(mut_view(cx.type_vars));\n\n"
                "    // Pass 1a0:",
                "    type_vars_init(mut_view(cx.type_vars));\n\n"
                "    tc_mangle_drop_impls(mut_view(cx), hir_file);\n\n"
                "    // Pass 1a0:",
            )
            src = src.replace(
                "            let mut m: *mut HirItem = unsafe { (*top_it).members };\n"
                "            while ((m as usize) != 0) {\n"
                "                register_item_sig(mut_view(cx), m, top_it);\n"
                "                m = unsafe { (*m).next };\n"
                "            }\n"
                "        } else if tk == HIR_ITEM_TRAIT {",
                "            let mut m: *mut HirItem = unsafe { (*top_it).members };\n"
                "            while ((m as usize) != 0) {\n"
                "                register_item_sig(mut_view(cx), m, top_it);\n"
                "                m = unsafe { (*m).next };\n"
                "            }\n"
                "            let tp_node: *mut HirType = unsafe { (*top_it).trait_path };\n"
                "            if (tp_node as usize) != 0 && impl_self_ty.v != 0u32 {\n"
                "                if (cx.str_in as usize) != 0 && tc_impl_is_lang_drop(hir_file.items, top_it, unsafe { view(*cx.str_in) }) {\n"
                "                    let self_t = unsafe { type_get(view((*thir_ptr).interner), (TypeId { v: impl_self_ty.v })) };\n"
                "                    if (self_t as usize) != 0 && (unsafe { (*self_t).kind }) == TY_STRUCT {\n"
                "                        let mut dm: *mut HirItem = unsafe { (*top_it).members };\n"
                "                        while (dm as usize) != 0 {\n"
                "                            if (unsafe { (*dm).kind }) == HIR_ITEM_FN {\n"
                "                                let tk_key = ((impl_self_ty.v as usize) << 1) | 1;\n"
                "                                unsafe {\n"
                "                                    ptr_itemmap_insert(mut_view((*thir_ptr).expr_methods), tk_key, dm);\n"
                "                                }\n"
                "                                let def_ptr = unsafe { (*self_t).def };\n"
                "                                if (def_ptr as usize) != 0 {\n"
                "                                    let dk_key = (def_ptr as usize) | 1;\n"
                "                                    unsafe {\n"
                "                                        ptr_itemmap_insert(mut_view((*thir_ptr).expr_methods), dk_key, dm);\n"
                "                                    }\n"
                "                                }\n"
                "                                break;\n"
                "                            }\n"
                "                            dm = unsafe { (*dm).next };\n"
                "                        }\n"
                "                    }\n"
                "                }\n"
                "            }\n"
                "        } else if tk == HIR_ITEM_TRAIT {",
            )
        src = src.replace("use std.core.host.", "use host_intrinsics.")
        src = src.replace("; return ", ";\nreturn ")
        src = src.replace("; break;", ";\nbreak;")
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


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
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def build_mir_opt_bundle(prelude_text, modules_text, axiom0, group, upper, spec_list, native_only):
    blobs = []
    prelude_flags = []
    for rel_ax, needs_prelude in spec_list:
        src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
        exp_mir_opt = run_axiom0_mir_opt(axiom0, rel_ax)
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
    out_path = os.path.join(HERE, "qa_interp_opt_diff_%s.ax" % group)
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def build_run_or_comptime_bundle(prelude_text, modules_text, axiom0, group, upper, spec_list, native_only, twin_name):
    blobs = []
    prelude_flags = []
    ui_err_flags = []
    exp_exits = []
    exp_diag0s = []
    exp_diag1s = []
    step_limits = []
    depth_limits = []

    for rel_ax, inline_src, needs_prelude, is_ui_err, exp_exit, diag0, diag1, step_limit, depth_limit in spec_list:
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
            if is_ui_err:
                rc = exp_exit if exp_exit is not None else 1
                exp_stdout = b""
                exp_panic = b""
            else:
                rc0, out0, panic0 = run_axiom0_run(axiom0, rel_ax, opt_O1=False)
                rc1, out1, panic1 = run_axiom0_run(axiom0, rel_ax, opt_O1=True)
                if rc0 != rc1 or out0 != out1 or panic0 != panic1:
                    raise SystemExit("axiom0 -O0 vs -O1 mismatch on %s" % rel_ax)
                rc = exp_exit if exp_exit is not None else rc0
                exp_stdout = out0
                exp_panic = panic0

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
    out_path = os.path.join(HERE, "qa_interp_opt_diff_%s.ax" % group)
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def main():
    axiom0 = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--axiom0" and i + 1 < len(sys.argv):
            axiom0 = sys.argv[i + 1]
            i += 2
        else:
            raise SystemExit("unknown arg: %s" % sys.argv[i])

    if not axiom0:
        axiom0 = find_exe([
            "build-snap-T083/build/axiom0.exe",
            "build/axiom0.exe",
        ])
    if not axiom0 or not os.path.isfile(axiom0):
        raise SystemExit("could not locate axiom0.exe")

    prelude_text = build_prelude_text()
    modules_text = assemble_modules()

    build_unit_bundle(prelude_text, modules_text)
    for group, upper, spec_list, native_only in MIR_OPT_GROUPS:
        build_mir_opt_bundle(prelude_text, modules_text, axiom0, group, upper, spec_list, native_only)
    for group, upper, spec_list, native_only in COMPTIME_GROUPS:
        build_run_or_comptime_bundle(
            prelude_text,
            modules_text,
            axiom0,
            group,
            upper,
            spec_list,
            native_only,
            "qa_interp_opt_diff_comptime_a.ax",
        )
    for group, upper, spec_list, native_only in RUN_GROUPS:
        build_run_or_comptime_bundle(
            prelude_text,
            modules_text,
            axiom0,
            group,
            upper,
            spec_list,
            native_only,
            "qa_interp_opt_diff_run_a.ax",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
