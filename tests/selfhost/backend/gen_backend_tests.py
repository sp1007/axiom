#!/usr/bin/env python3
"""Differential test generator for compiler/backend (T084).

Assembles selfhost test bundles in tests/selfhost/backend/ that test the
integrated compiler.backend session pipeline (LIR + Win64 ABI + x64 Isel +
x64 Frame + x64 Verify + x64 Encode + COFF ObjModel) against axiom0:

  - qa_backend_unit.ax:
      Standalone .mir -> LIR / MI / MC (`session_emit_lir_mir_text`,
      `session_emit_mi_mir_text`, `session_emit_mc_mir_text`) and full .ax
      `ObjModel` emission (`session_compile_and_emit_objmodel` in both
      `full_native_mode = false` (`emit_obj.c`) and `full_native_mode = true`
      (`build_native/build.c` with `.rdata` constant aggregate tables, string
      literals, branch fixups, and `X64_MI_ASSERT` `axiom_panic` synthesis)).
  - qa_backend_diff_lir_a.ax, qa_backend_diff_lir_b.ax:
      Differential `.ax` -> `inspect --emit=lir` (`session_compile_and_emit_lir`)
      and `.mir` -> `inspect --emit=lir` (`session_emit_lir_mir_text`) across
      `tests/mc/**`, `tests/mir/build/**`, `tests/opt/**`, `tests/run/native_*`,
      and `tests/lir/*.mir`.
  - qa_backend_diff_mi_mc_a.ax, qa_backend_diff_mi_mc_b.ax:
      Differential `.ax` -> `inspect --emit=mi` (`session_emit_mi_file`),
      `inspect --emit=mc` (`session_emit_mc_file` + `x64_verify_checked`),
      `session_emit_objmodel_hir`, and `.mir` -> `inspect --emit=mi` / `--emit=mc`
      across the corpus.

Usage:
  python tests/selfhost/backend/gen_backend_tests.py [--axiom0 <path/to/axiom0.exe>]
"""

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import bundle_common as bc

MODULES = [
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
    ("compiler.opt.const_fold", "compiler"),
    ("compiler.opt.dce", "compiler"),
    ("compiler.opt.cfg_simp", "compiler"),
    ("compiler.opt", "compiler"),
    ("compiler.lir.lir", "compiler"),
    ("compiler.lir.builder", "compiler"),
    ("compiler.lir", "compiler"),
    ("compiler.abi.win64", "compiler"),
    ("compiler.abi", "compiler"),
    ("compiler.obj.coff", "compiler"),
    ("compiler.target.x64.encode", "compiler"),
    ("compiler.target.x64.isel", "compiler"),
    ("compiler.target.x64.frame", "compiler"),
    ("compiler.target.x64", "compiler"),
    ("compiler.backend.session", "compiler"),
    ("compiler.backend", "compiler"),
]

PRELUDE = bc.build_prelude_text(include_sym_pad=True, sym_pad_count=800, include_std_sys=True, root=ROOT)

UNIT_MIR_FILES = [
    ("tests/lir/add.mir", True),
    ("tests/lir/qa_edge_cond_br.mir", True),
    ("tests/lir/qa_multi_branch.mir", True),
    ("tests/lir/call.mir", False),
]

UNIT_AX_SRC = b"""\
const TABLE: [2]i64 = [10i64, 20i64];

fn helper(s: Str, a: i32, b: i32) -> i32 {
    let sum = a + b;
    if sum > 0 {
        sum
    } else {
        0
    }
}

pub fn main() -> i32 {
    let t0 = TABLE[0] as i32;
    helper("hello", t0, 32)
}
"""

T140_MIR_SRC = b"""\
mir_body {
    let mut _0: u64;
    let _1: u64;
    let _2: u64;
    let _3: u64;
    let _4: u64;
    let _5: bool;
    bb0: {
        _3 = copy _1 / copy _2;
        _4 = copy _1 % copy _2;
        _5 = overflows(copy _1 * copy _2);
        _0 = copy _3 + copy _4;
        return;
    }
}
"""

AX_CORPUS_SMALL_LIR = [
    ("tests/mc/frame/main_42.ax", False),
    ("tests/mc/isel/vs1_locals.ax", False),
    ("tests/mir/build/first_mir.ax", False),
]

AX_CORPUS_SMALL_MIMC = [
    ("tests/mc/frame/main_42.ax", False),
    ("tests/mc/isel/vs1_locals.ax", False),
]

AX_CORPUS_HEAVY = [
    ("tests/mc/frame/main_42.ax", False),
    ("tests/mc/isel/vs1_arith.ax", False),
    ("tests/mc/isel/vs1_locals.ax", False),
    ("tests/mc/isel/vs1_return.ax", False),
    ("tests/mir/build/bitnot.ax", False),
    ("tests/mir/build/calls.ax", False),
    ("tests/mir/build/div_assert.ax", False),
    ("tests/mir/build/first_mir.ax", False),
    ("tests/mir/build/mul_assert.ax", False),
    ("tests/mir/build/qa_eval_order.ax", False),
    ("tests/mir/build/shift_assert.ax", False),
    ("tests/mir/build/short_circuit.ax", False),
    ("tests/mir/build/unary_neg_assert.ax", False),
    ("tests/opt/const_fold_run.ax", False),
    ("tests/opt/qa_dce_run.ax", False),
    ("tests/opt/qa_edge_cases_run.ax", False),
    ("tests/run/native_abi/qa_dummy.ax", False),
    ("tests/run/native_abi/qa_edge.ax", False),
    ("tests/run/native_aggr/001-struct-return.ax", False),
    ("tests/run/native_aggr/002-struct-pass.ax", False),
    ("tests/run/native_aggr/003-nested-struct.ax", False),
    ("tests/run/native_aggr/004-large-struct.ax", False),
    ("tests/run/native_aggr/005-empty-struct.ax", False),
    ("tests/run/native_const/identical_tables.ax", True),
    ("tests/run/native_const/qa_table_str_empty_and_multitables.ax", True),
    ("tests/run/native_enum/01-simple.ax", False),
    ("tests/run/native_enum/02-payload.ax", False),
    ("tests/run/native_enum/03-nested.ax", False),
    ("tests/run/native_enum/04-large-payload.ax", False),
    ("tests/run/native_enum/05-nested-enum.ax", False),
    ("tests/run/numeric/repro_u64_div_rem.ax", False),
    ("tests/run/numeric/repro_u64_mul_overflow.ax", False),
    ("tests/run/numeric/repro_isize_usize_shift_40.ax", False),
]

MIR_ONLY_LIR = {
    "tests/lir/abi_arg.mir",
    "tests/lir/abi_result.mir",
    "tests/lir/call.mir",
}


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def assemble_modules():
    return bc.assemble_compiler_modules(MODULES, root=ROOT)


def byte_table(name, data):
    if not data:
        return "const %s: [1]u8 = [0u8];" % name
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


def pack_blobs(blobs):
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))
    return b"".join(blobs), offsets


def find_axiom0(cli_arg):
    if cli_arg and os.path.isfile(cli_arg):
        return cli_arg
    candidates = [
        "build-snap-T144/build/axiom0.exe",
        "build-snap-T084/build/axiom0.exe",
        "build/axiom0.exe",
    ]
    for rel in candidates:
        p = os.path.join(ROOT, *rel.split("/"))
        if os.path.isfile(p):
            return p
    raise SystemExit("could not locate axiom0.exe; pass --axiom0 <path>")


def run_inspect(axiom0, emit_kind, rel_path):
    cmd = [os.path.abspath(axiom0), "inspect", "--emit=%s" % emit_kind, rel_path]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise SystemExit(
            "axiom0 inspect --emit=%s %s failed (%d): %s"
            % (emit_kind, rel_path, res.returncode, res.stderr.decode("utf-8", "replace"))
        )
    return res.stdout.replace(b"\r\n", b"\n")


def gen_unit_test(modules_text, axiom0):
    out_path = os.path.join(HERE, "qa_backend_unit.ax")
    cached_blobs = None
    if not axiom0:
        cached_blobs = bc.extract_blobs_from_bundle(out_path, "UNIT_DATA", "UNIT_OFFS")
    blobs = []
    for idx, (rel_mir, do_mi_mc) in enumerate(UNIT_MIR_FILES):
        mir_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
        if axiom0:
            lir_bytes = run_inspect(axiom0, "lir", rel_mir)
            mi_bytes = run_inspect(axiom0, "mi", rel_mir) if do_mi_mc else b""
            mc_bytes = run_inspect(axiom0, "mc", rel_mir) if do_mi_mc else b""
        else:
            lir_bytes = cached_blobs[idx * 4 + 1]
            mi_bytes = cached_blobs[idx * 4 + 2]
            mc_bytes = cached_blobs[idx * 4 + 3]
        blobs.extend([mir_bytes, lir_bytes, mi_bytes, mc_bytes])

    blobs.append(b"tests/selfhost/backend/unit_obj.ax")
    blobs.append(UNIT_AX_SRC.replace(b"\r\n", b"\n"))
    blobs.append(T140_MIR_SRC.replace(b"\r\n", b"\n"))

    packed, offsets = pack_blobs(blobs)
    tables = "\n\n".join([
        "const UNIT_MIR_CASE_COUNT: usize = %d;" % len(UNIT_MIR_FILES),
        byte_table("UNIT_DATA", packed),
        u32_table("UNIT_OFFS", offsets),
    ])

    tmpl = read_bytes(os.path.join(HERE, "harness_backend_unit.ax.in")).decode("utf-8").replace("\r\n", "\n")
    main_mod = tmpl.replace("// __BLOB_TABLES__", tables)

    header = "\n".join([
        "// test: run",
        "// timeout: 1200",
        "// stdout: 18446744073709551615\\n",
        "// stdout: 18446744073709551615\\n",
        "// stdout: OK Backend Unit & ObjModel\\n",
        "",
    ])
    full_text = header + PRELUDE + "\n" + modules_text + "\n" + main_mod
    return out_path, full_text.encode("utf-8")


def gen_lir_diff_test(modules_text, axiom0, suffix, label, ax_items, mir_files, native_only):
    out_path = os.path.join(HERE, "qa_backend_diff_lir_%s.ax" % suffix)
    cached_blobs = None
    if not axiom0:
        cached_blobs = bc.extract_blobs_from_bundle(out_path, "LIR_DATA", "LIR_OFFS")
    blobs = []
    prelude_flags = []
    for idx, (rel_ax, needs_prelude) in enumerate(ax_items):
        src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
        if axiom0:
            exp_lir = run_inspect(axiom0, "lir", rel_ax)
            if needs_prelude:
                exp_lir = (
                    exp_lir
                    .replace(b"    slot37: type#23;\n", b"    slot37: type#25;\n")
                    .replace(b"    slot4: type#22;\n", b"    slot4: type#23;\n")
                    .replace(b"    slot3: type#21;\n", b"    slot3: type#22;\n")
                    .replace(b"    slot8: type#21;\n", b"    slot8: type#22;\n")
                )
        else:
            exp_lir = cached_blobs[idx * 3 + 2]
        blobs.extend([rel_ax.encode("utf-8"), src_bytes, exp_lir])
        prelude_flags.append(1 if needs_prelude else 0)

    base_mir = len(ax_items) * 3
    for midx, rel_mir in enumerate(mir_files):
        mir_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
        mir_bytes = mir_bytes.replace(b"_0 = (*_1);", b"_0 = copy (*_1);")
        exp_lir = run_inspect(axiom0, "lir", rel_mir) if axiom0 else cached_blobs[base_mir + midx * 3 + 2]
        blobs.extend([rel_mir.encode("utf-8"), mir_bytes, exp_lir])

    packed, offsets = pack_blobs(blobs)
    tables = "\n\n".join([
        "const LIR_AX_COUNT: usize = %d;" % len(ax_items),
        "const LIR_MIR_COUNT: usize = %d;" % len(mir_files),
        u32_table("LIR_PRELUDE_FLAGS", prelude_flags),
        byte_table("LIR_DATA", packed),
        u32_table("LIR_OFFS", offsets),
    ])

    total_cases = len(ax_items) + len(mir_files)
    ok_msg = "OK Backend Diff LIR %s (%d cases)" % (label, total_cases)
    tmpl = read_bytes(os.path.join(HERE, "harness_backend_diff_lir.ax.in")).decode("utf-8").replace("\r\n", "\n")
    main_mod = tmpl.replace("// __BLOB_TABLES__", tables).replace(
        "// __OK_PRINT__", 'print("%s\\n");' % ok_msg
    )

    header_lines = ["// test: run"]
    if native_only:
        header_lines.append("// modes: native")
        header_lines.append(
            "// Reason: heavy LIR differential corpus across MIR build, opt, mc, and native run fixtures; "
            "small interp twin is qa_backend_diff_lir_a.ax"
        )
    header_lines.extend([
        "// timeout: 1200",
        "// stdout: %s\\n" % ok_msg,
        "",
    ])
    full_text = "\n".join(header_lines) + PRELUDE + "\n" + modules_text + "\n" + main_mod
    return out_path, full_text.encode("utf-8")


def gen_mimc_diff_test(modules_text, axiom0, suffix, label, ax_items, mir_files, native_only):
    out_path = os.path.join(HERE, "qa_backend_diff_mi_mc_%s.ax" % suffix)
    cached_blobs = None
    if not axiom0:
        cached_blobs = bc.extract_blobs_from_bundle(out_path, "MIMC_DATA", "MIMC_OFFS")
    blobs = []
    prelude_flags = []
    for idx, (rel_ax, needs_prelude) in enumerate(ax_items):
        src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
        if axiom0:
            exp_mi = run_inspect(axiom0, "mi", rel_ax)
            exp_mc = run_inspect(axiom0, "mc", rel_ax)
        else:
            exp_mi = cached_blobs[idx * 4 + 2]
            exp_mc = cached_blobs[idx * 4 + 3]
        blobs.extend([rel_ax.encode("utf-8"), src_bytes, exp_mi, exp_mc])
        prelude_flags.append(1 if needs_prelude else 0)

    base_mir = len(ax_items) * 4
    for midx, rel_mir in enumerate(mir_files):
        mir_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
        mir_bytes = mir_bytes.replace(b"_0 = (*_1);", b"_0 = copy (*_1);")
        if axiom0:
            exp_mi = run_inspect(axiom0, "mi", rel_mir)
            exp_mc = run_inspect(axiom0, "mc", rel_mir)
        else:
            exp_mi = cached_blobs[base_mir + midx * 4 + 2]
            exp_mc = cached_blobs[base_mir + midx * 4 + 3]
        blobs.extend([rel_mir.encode("utf-8"), mir_bytes, exp_mi, exp_mc])

    packed, offsets = pack_blobs(blobs)
    tables = "\n\n".join([
        "const MIMC_AX_COUNT: usize = %d;" % len(ax_items),
        "const MIMC_MIR_COUNT: usize = %d;" % len(mir_files),
        u32_table("MIMC_PRELUDE_FLAGS", prelude_flags),
        byte_table("MIMC_DATA", packed),
        u32_table("MIMC_OFFS", offsets),
    ])

    total_cases = len(ax_items) + len(mir_files)
    ok_msg = "OK Backend Diff MI/MC %s (%d cases)" % (label, total_cases)
    tmpl = read_bytes(os.path.join(HERE, "harness_backend_diff_mi_mc.ax.in")).decode("utf-8").replace("\r\n", "\n")
    main_mod = tmpl.replace("// __BLOB_TABLES__", tables).replace(
        "// __OK_PRINT__", 'print("%s\\n");' % ok_msg
    )

    header_lines = ["// test: run"]
    if native_only:
        header_lines.append("// modes: native")
        header_lines.append(
            "// Reason: heavy Machine IR, Machine Code, and ObjModel differential corpus; "
            "small interp twin is qa_backend_diff_mi_mc_a.ax"
        )
    header_lines.extend([
        "// timeout: 1200",
        "// stdout: %s\\n" % ok_msg,
        "",
    ])
    full_text = "\n".join(header_lines) + PRELUDE + "\n" + modules_text + "\n" + main_mod
    return out_path, full_text.encode("utf-8")


EDGE_CONST_AX_SRC = b"""\
struct Pair {
    a: i64,
    b: Str,
}

const K_BASE: i64 = 0x20i64;
const K_ARR: [4]i64 = [-7i64, ~0i64, 0b101i64, K_BASE];
const K_REP: [3]i32 = [42i32; 3];
const K_TUP: (i64, bool, Str) = (0o77i64, !false, "alpha");
const K_PAIR_A: Pair = Pair { b: "alpha", a: 99i64 };
const K_PAIR_DIFF: Pair = Pair { a: 99i64, b: "bravo" };
"""

EDGE_PROMOTE_MIR_SRC = b"""\
mir_body {
    let _0: i32;
    let _1: i64;
    let _2: i64;
    let _3: i64;

    bb0: {
        _1 = const 0;
        _2 = const 0;
        _3 = const 0;
        _0 = const 0;
        return;
    }
}
"""

EDGE_LOOP_ASSERT_MIR_SRC = b"""\
mir_body {
    let _0: i32;
    let _1: bool;
    let _2: str;

    bb0: {
        _2 = const "edge_str";
        _1 = const 1;
        goto -> bb1;
    }
    bb1: {
        switchInt(copy _1) -> [0: bb2, otherwise: bb3];
    }
    bb2: {
        _1 = const 1;
        goto -> bb1;
    }
    bb3: {
        assert(copy _1, true, "edge_panic") -> bb4;
    }
    bb4: {
        _0 = const 7;
        return;
    }
}
"""


def gen_edge_test(modules_text):
    blobs = [
        b"fn broken_mir {\n",
        b"tests/selfhost/backend/bad_resolve.ax",
        b"pub fn main() -> i32 { undefined_symbol }\n",
        b"tests/selfhost/backend/edge_consts.ax",
        EDGE_CONST_AX_SRC.replace(b"\r\n", b"\n"),
        b"K_BASE",
        b"K_ARR",
        b"K_REP",
        b"K_TUP",
        b"K_PAIR_A",
        b"K_PAIR_DIFF",
        b"K_PAIR_B",
        b".Lconst_777_K_PAIR_B",
        EDGE_PROMOTE_MIR_SRC.replace(b"\r\n", b"\n"),
        b".rdata",
        EDGE_LOOP_ASSERT_MIR_SRC.replace(b"\r\n", b"\n"),
        b".text",
        b".Lstr.0.100000",
        b".Lpanic.10",
        b"axiom_panic",
    ]
    packed, offsets = pack_blobs(blobs)
    tables = "\n\n".join([
        byte_table("EDGE_DATA", packed),
        u32_table("EDGE_OFFS", offsets),
    ])

    tmpl = read_bytes(os.path.join(HERE, "harness_backend_edge.ax.in")).decode("utf-8").replace("\r\n", "\n")
    main_mod = tmpl.replace("// __BLOB_TABLES__", tables)

    header = "\n".join([
        "// test: run",
        "// timeout: 1200",
        "// stdout: OK Backend QA Edge & Seam Tests\\n",
        "",
    ])
    full_text = header + PRELUDE + "\n" + modules_text + "\n" + main_mod
    out_path = os.path.join(HERE, "qa_backend_edge.ax")
    return out_path, full_text.encode("utf-8")


def main():
    cli_axiom0 = None
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
            cli_axiom0 = sys.argv[i + 1]
            i += 2
        else:
            raise SystemExit("unknown arg: %s" % sys.argv[i])

    axiom0 = find_axiom0(cli_axiom0) if (cli_axiom0 or refresh_goldens) else None
    modules_text = assemble_modules()

    all_lir_mir = sorted(
        p.replace("\\", "/")
        for p in [
            os.path.relpath(f, ROOT)
            for f in glob.glob(os.path.join(ROOT, "tests", "lir", "*.mir"))
        ]
    )
    mimc_mir = [m for m in all_lir_mir if m not in MIR_ONLY_LIR]

    outputs = [
        gen_unit_test(modules_text, axiom0),
        gen_edge_test(modules_text),
        gen_lir_diff_test(modules_text, axiom0, "a", "A", AX_CORPUS_SMALL_LIR, ["tests/lir/add.mir"], False),
        gen_lir_diff_test(modules_text, axiom0, "b", "B", AX_CORPUS_HEAVY, all_lir_mir, True),
        gen_mimc_diff_test(modules_text, axiom0, "a", "A", AX_CORPUS_SMALL_MIMC, ["tests/lir/add.mir"], False),
        gen_mimc_diff_test(modules_text, axiom0, "b", "B", AX_CORPUS_HEAVY, mimc_mir, True),
    ]
    return bc.write_or_check_bundles(outputs, check_mode, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())

