#!/usr/bin/env python3
"""Generator for the selfhost MIR verifier tests (T082e).

    python tests/selfhost/verify/gen_verify_tests.py
        Generates:
          - tests/selfhost/verify/qa_verify_mir.ax:
            Differential test over all 21 `.mir` fixtures in `tests/verify/` and `tests/verify/own/`
            plus valid `.mir` goldens and unit tests for CFG, projections, aggregates, casts,
            call signatures, return types, ownership dataflow, capabilities, and drop flags.
          - tests/selfhost/verify/qa_verify_pipeline.ax:
            End-to-end selfhost pipeline test lowering `.ax` programs through `mir_build_fn` and
            `mir_drop_elaborate` and verifying all resulting MIR bodies with `verify_mir`,
            `verify_mir_own`, `verify_mir_cap`, and `verify_mir_drop_flags`.

Run from the repository root. Files are written with LF line endings.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

CORE_MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.lex.token", "compiler"),
    ("compiler.syntax.ast", "compiler"),
    ("compiler.hir.hir", "compiler"),
    ("compiler.types.types", "compiler"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
]

PIPELINE_MODULES = [
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
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
]

PRELUDE = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=ROOT)

# All 21 `.mir` fixtures under `tests/verify/` and `tests/verify/own/`, with their expected
# diagnostic codes from `axiom0 check`.
MIR_FIXTURES = [
    ("tests/verify/bad_target.mir", ["AX_VERIFY_BAD_TARGET"]),
    ("tests/verify/call_signature.mir", ["AX_VERIFY_CALL_SIGNATURE"]),
    ("tests/verify/return_type.mir", []),
    ("tests/verify/type_mismatch.mir", ["AX_VERIFY_TYPE_MISMATCH"]),
    ("tests/verify/type_mismatch_binop.mir", ["AX_VERIFY_TYPE_MISMATCH"]),
    ("tests/verify/type_mismatch_cast.mir", ["AX_VERIFY_TYPE_MISMATCH"]),
    ("tests/verify/uninit_cond.mir", ["AX_VERIFY_UNINIT_USE"]),
    ("tests/verify/uninit_use.mir", ["AX_VERIFY_UNINIT_USE"]),
    ("tests/verify/unknown_local.mir", ["AX_VERIFY_UNKNOWN_LOCAL"]),
    ("tests/verify/unknown_local_storage.mir", ["AX_VERIFY_UNKNOWN_LOCAL"]),
    ("tests/verify/unterminated_block.mir", ["AX_VERIFY_UNTERMINATED_BLOCK"]),
    ("tests/verify/own/call_unwind_owned.mir", ["AX_VERIFY_MISSING_DROP", "AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/own/conditional_move.mir", ["AX_VERIFY_USE_AFTER_MOVE", "AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/own/double_drop.mir", ["AX_VERIFY_DOUBLE_DROP"]),
    ("tests/verify/own/missing_drop.mir", ["AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/own/missing_drop_no_unreachable.mir", ["AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/own/overwrite_owned.mir", ["AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/own/qa_conditional_double_drop.mir", ["AX_VERIFY_DOUBLE_DROP"]),
    ("tests/verify/own/qa_loop_move.mir", ["AX_VERIFY_USE_AFTER_MOVE", "AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/own/return_moved.mir", ["AX_VERIFY_USE_AFTER_MOVE"]),
    ("tests/verify/own/use_after_move.mir", [
        "AX_VERIFY_USE_AFTER_MOVE",
        "AX_VERIFY_MISSING_DROP",
        "AX_VERIFY_MISSING_DROP",
    ]),
    ("tests/verify/drop/missing_drop_branch.mir", ["AX_VERIFY_MISSING_DROP"]),
    ("tests/verify/drop/double_drop_implicit.mir", ["AX_VERIFY_DOUBLE_DROP"]),
    ("tests/verify/drop/cond_drop_flag_ok.mir", []),
    ("tests/verify/drop/raw_store_moved_ok.mir", []),
]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def assemble_modules(mod_list):
    return bc.assemble_compiler_modules(mod_list, root=ROOT)


def byte_table(name, data):
    lines = ["const %s: [%d]u8 = [" % (name, len(data))]
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def u32_table(name, values):
    lines = ["const %s: [%d]u32 = [" % (name, max(1, len(values)))]
    if not values:
        lines.append("    0u32,")
    else:
        for i in range(0, len(values), 10):
            chunk = values[i:i + 10]
            lines.append("    " + ", ".join("%du32" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


UNIT_MIR_SNIPPETS = [
    b"mir_body { bad_syntax }",
    (
        b"mir_body {\n"
        b"    let mut _0: type#2;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#4;\n"
        b"    let _4: type#12;\n"
        b"    let _5: type#8;\n"
        b"    let _6: type#4;\n"
        b"    let _7: type#10;\n"
        b"    bb0: {\n"
        b"        StorageLive(_7);\n"
        b"        _1 = const 10: type#8;\n"
        b"        _2 = const 20: type#8;\n"
        b"        _3 = copy _1 < copy _2;\n"
        b"        _4 = const 2: type#12;\n"
        b"        _5 = copy _1 << copy _4;\n"
        b"        _6 = overflows(copy _1 + copy _2);\n"
        b"        _7 = const 0;\n"
        b"        StorageDead(_7);\n"
        b"        assert(copy _3 == true, \"cmp ok\") -> [return: bb1, unwind: bb0];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        switchInt(copy _5) -> [40: bb2, otherwise: bb2];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    (
        b"mir_body {\n"
        b"    let mut _0: type#2;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 1: type#8;\n"
        b"        _2 = copy _1 == copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    (
        b"mir_body {\n"
        b"    let mut _0: type#2;\n"
        b"    let _1: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 0;\n"
        b"        switchInt(copy _1) -> [0: bb5, otherwise: bb0];\n"
        b"    }\n"
        b"}\n"
    ),
    (
        b"mir_body {\n"
        b"    let mut _0: type#2;\n"
        b"    let _1: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const true;\n"
        b"        assert(copy _1 == true, \"chk\") -> [return: bb0, unwind: bb9];\n"
        b"    }\n"
        b"}\n"
    ),
    (
        b"mir_body {\n"
        b"    type 20 = fn(type#8) -> type#2;\n"
        b"    let mut _0: type#2;\n"
        b"    let _1: type#20;\n"
        b"    let _2: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const 0;\n"
        b"        _2 = const true: type#4;\n"
        b"        _0 = copy _1(copy _2) -> [return: bb1, unwind: bb0];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    bb0: {\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
]

PIPE_BLOBS = [
    b"tests/selfhost/verify/pipeline_input.ax",
    (
        b"struct Res {}\n"
        b"fn helper(x: i32, flag: bool) -> i32 {\n"
        b"    let r = Res {};\n"
        b"    if flag { return x; }\n"
        b"    0\n"
        b"}\n"
    ),
]


def pack_blobs(blobs):
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))
    return b"".join(blobs), offsets


def build_qa_verify_mir():
    blobs = []
    offsets = [0]
    exp_counts = []
    exp_code_offs = [0]
    exp_codes = []

    for rel_path, codes in MIR_FIXTURES:
        raw = read_bytes(os.path.join(ROOT, *rel_path.split("/"))).replace(b"\r\n", b"\n")
        blobs.append(raw)
        offsets.append(offsets[-1] + len(raw))
        exp_counts.append(len(codes))
        exp_codes.extend(codes)
        exp_code_offs.append(len(exp_codes))

    data = b"".join(blobs)
    code_lines = ["const FIXTURE_EXP_CODES: [%d]u32 = [" % len(exp_codes)]
    for c in exp_codes:
        code_lines.append("    %s," % c)
    code_lines.append("];")

    unit_data, unit_offs = pack_blobs(UNIT_MIR_SNIPPETS)

    template = read_bytes(os.path.join(HERE, "harness_verify_mir.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@FIXTURE_COUNT@", str(len(MIR_FIXTURES)))
        .replace("@FIXTURE_DATA@", byte_table("FIXTURE_DATA", data))
        .replace("@FIXTURE_OFF@", u32_table("FIXTURE_OFF", offsets))
        .replace("@FIXTURE_EXP_COUNTS@", u32_table("FIXTURE_EXP_COUNTS", exp_counts))
        .replace("@FIXTURE_EXP_OFF@", u32_table("FIXTURE_EXP_OFF", exp_code_offs))
        .replace("@FIXTURE_EXP_CODES@", "\n".join(code_lines))
        .replace("@UNIT_MIR_DATA@", byte_table("UNIT_MIR_DATA", unit_data))
        .replace("@UNIT_MIR_OFF@", u32_table("UNIT_MIR_OFF", unit_offs))
    )

    header = (
        "// test: run\n"
        "// timeout: 600\n"
        "// stdout: OK verify mir (21 fixtures + unit checks)\\n\n"
        "// Generated by tests/selfhost/verify/gen_verify_tests.py; do not edit.\n\n"
    )
    full_text = header + PRELUDE + "\n" + assemble_modules(CORE_MODULES) + "\n" + main_src
    out_path = os.path.join(HERE, "qa_verify_mir.ax")
    return out_path, full_text


def build_qa_verify_pipeline():
    pipe_data, pipe_offs = pack_blobs(PIPE_BLOBS)
    template = read_bytes(os.path.join(HERE, "harness_verify_pipeline.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@PIPE_DATA@", byte_table("PIPE_DATA", pipe_data))
        .replace("@PIPE_OFF@", u32_table("PIPE_OFF", pipe_offs))
    )
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "// stdout: OK verify pipeline\\n\n"
        "// Generated by tests/selfhost/verify/gen_verify_tests.py; do not edit.\n\n"
    )
    full_text = header + PRELUDE + "\n" + assemble_modules(PIPELINE_MODULES) + "\n" + main_src
    out_path = os.path.join(HERE, "qa_verify_pipeline.ax")
    return out_path, full_text


def main():
    check_mode = "--check" in sys.argv[1:] or "check" in sys.argv[1:]
    outs = [
        build_qa_verify_mir(),
        build_qa_verify_pipeline(),
    ]
    return bc.write_or_check_bundles(outs, check_mode, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
