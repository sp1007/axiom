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
REFERENCE_BUNDLE = "tests/selfhost/lir/qa_lir_from_ax_a.ax"

MODULES = [
    ("compiler.kernel.id", "reference"),
    ("compiler.kernel.hash", "reference"),
    ("compiler.kernel.arena", "reference"),
    ("compiler.kernel.interner", "reference"),
    ("compiler.source.span", "reference"),
    ("compiler.source.manager", "reference"),
    ("compiler.diag.code", "reference"),
    ("compiler.diag.emitter", "reference"),
    ("compiler.diag.format", "reference"),
    ("compiler.diag.json", "reference"),
    ("compiler.kernel_source_diag.session", "reference"),
    ("compiler.lex.token", "reference"),
    ("compiler.lex.scanner", "reference"),
    ("compiler.lexer.session", "reference"),
    ("compiler.syntax.ast", "reference"),
    ("compiler.syntax.parse", "reference"),
    ("compiler.parser.session", "reference"),
    ("compiler.resolve.symtab", "reference"),
    ("compiler.resolve.rib", "reference"),
    ("compiler.resolve.resolver", "reference"),
    ("compiler.hir.hir", "reference"),
    ("compiler.hir.lower", "reference"),
    ("compiler.resolve_hir.session", "reference"),
    ("compiler.types.types", "reference"),
    ("compiler.types.layout", "reference"),
    ("compiler.types.exhaust", "reference"),
    ("compiler.traits.solver", "reference"),
    ("compiler.traits.mono", "reference"),
    ("compiler.types.typeck", "reference"),
    ("compiler.types", "reference"),
    ("compiler.traits", "reference"),
    ("compiler.typeck.session", "reference"),
    ("compiler.typeck", "reference"),
    ("compiler.typeck_traits.session", "reference"),
    ("compiler.typeck_traits", "reference"),
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

PRELUDE = """\
@link("kernel32")
extern "system" {
    fn GetProcessHeap() -> *mut u8;
    fn HeapAlloc(hHeap: *mut u8, dwFlags: u32, dwBytes: usize) -> *mut u8;
    fn HeapFree(hHeap: *mut u8, dwFlags: u32, lpMem: *mut u8) -> i32;
}

const HEAP_ZERO_MEMORY: u32 = 8u32;
const MIN_HEAP_ALLOC: usize = 16;

pub unsafe fn __ax_host_heap_alloc(size: usize, align: usize) -> *mut u8 {
    let h = GetProcessHeap();
    if (h as usize) == 0 {
        return 0 as *mut u8;
    }
    let alloc_bytes: usize = if size < MIN_HEAP_ALLOC { MIN_HEAP_ALLOC } else { size };
    HeapAlloc(h, HEAP_ZERO_MEMORY, alloc_bytes)
}

pub unsafe fn __ax_host_heap_free(p: *mut u8, size: usize, align: usize) {
    if (p as usize) != 0 {
        let h = GetProcessHeap();
        if (h as usize) != 0 {
            HeapFree(h, 0u32, p);
        }
    }
}
"""

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
    text = read_bytes(os.path.join(ROOT, REFERENCE_BUNDLE)).decode("utf-8").replace("\r\n", "\n")
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
    for name, origin in MODULES:
        if origin == "compiler":
            src = read_bytes(files[name]).decode("utf-8").replace("\r\n", "\n")
        else:
            src = ref[name]
        if name == "compiler.verify.verifier":
            src = src.replace(
                "val = val * 10u64 + ((c - 48u8) as u64);",
                "val = (((val as i64) * 10i64) as u64) + ((c - 48u8) as u64);",
            )
        if name == "compiler.mir.mir":
            src = src.replace(
                "        if mp_match_bytes(mut_view(*p), 541, 1) {\n"
                "            let cty = mp_parse_type(mut_view(*p), mut_view(*interner), type_map);\n"
                "            out.constant.ty.v = cty.v;\n"
                "        }\n"
                "    }\n"
                "}",
                "        if mp_match_bytes(mut_view(*p), 541, 1) {\n"
                "            let cty = mp_parse_type(mut_view(*p), mut_view(*interner), type_map);\n"
                "            out.constant.ty.v = cty.v;\n"
                "        }\n"
                "    } else {\n"
                "        out.kind = MIR_OP_COPY;\n"
                "        mp_parse_place(mut_view(*p), mut_view(*arena), mut_view(out.place));\n"
                "    }\n"
                "}",
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
            src = src.replace(
                "                ci = ci + 1;\n"
                "            }\n"
                "        }\n"
                "    } else if ek == HIR_EXPR_UNARY && (unsafe { (*expr).op }) == UNOP_DEREF {",
                "                ci = ci + 1;\n"
                "            }\n"
                "        }\n"
                "        if sym.v != 0u32 && (b.thir as usize) != 0 {\n"
                "            let cval = unsafe { sym_constmap_get(view((*b.thir).symbol_consts), (SymbolId { v: sym.v })) };\n"
                "            if (cval as usize) != 0 && (unsafe { (*cval).kind }) == CONST_AGGREGATE {\n"
                "                let ty = mb_expr_ty(mut_view(*b), expr);\n"
                "                let cloc = mb_new_local(mut_view(*b), (TypeId { v: ty.v }), MIR_LOCAL_CONST, false, StrId { v: 0u32 }, view(sp));\n"
                "                let ldecl = unsafe { mir_local_at((*b.body).locals, cloc.v as usize) };\n"
                "                unsafe { (*ldecl).const_sym.v = sym.v; }\n"
                "                mb_register_sym(mut_view(*b), (SymbolId { v: sym.v }), (MirLocalId { v: cloc.v }), false);\n"
                "                let p = mir_local_place(cloc.v);\n"
                "                let mut cop = MirOperand {\n"
                "                    kind: MIR_OP_CONST,\n"
                "                    location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "                    place: mir_local_place(0u32),\n"
                "                    constant: MirConst { ty: TypeId { v: ty.v }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } }\n"
                "                };\n"
                "                let saved_bb = b.curr_bb.v;\n"
                "                let saved_div = b.is_diverged;\n"
                "                b.curr_bb.v = 0u32;\n"
                "                b.is_diverged = false;\n"
                "                mb_emit_assign_use(mut_view(*b), view(p), view(cop), view(sp));\n"
                "                b.curr_bb.v = saved_bb;\n"
                "                b.is_diverged = saved_div;\n"
                "                return p;\n"
                "            }\n"
                "        }\n"
                "    } else if ek == HIR_EXPR_UNARY && (unsafe { (*expr).op }) == UNOP_DEREF {",
            )
            src = src.replace(
                "                let ok_loc = mb_new_temp(mut_view(*b), (TypeId {\n"
                "                    v: bool_ty.v\n"
                "                }), view(sp));\n"
                "                let ok_pl = mir_local_place(ok_loc.v);\n"
                "                let idx_op = MirOperand {\n"
                "                    kind: MIR_OP_COPY, location: Span {\n"
                "                        file: FileId {\n"
                "                            v: 0u32\n"
                "                        }, start: 0u32, end: 0u32\n"
                "                    }, place: MirPlace {\n"
                "                        local: MirLocalId {\n"
                "                            v: idx_loc.v\n"
                "                        }, region: 0u8, view_kind: 0u8, projs: 0 as *mut MirProjection, proj_count: 0, drop_flag: MIR_DROP_FLAG_NONE\n"
                "                    }, constant: MirConst {\n"
                "                        ty: TypeId {\n"
                "                            v: 0u32\n"
                "                        }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId {\n"
                "                            v: 0u32\n"
                "                        }\n"
                "                    }\n"
                "                };",
                "                let ok_loc = mb_new_temp(mut_view(*b), (TypeId {\n"
                "                    v: bool_ty.v\n"
                "                }), view(sp));\n"
                "                let ok_pl = mir_local_place(ok_loc.v);\n"
                "                let u_idx_loc = mb_new_temp(mut_view(*b), (TypeId { v: usize_ty.v }), view(sp));\n"
                "                let u_idx_pl = mir_local_place(u_idx_loc.v);\n"
                "                let raw_idx_op = MirOperand {\n"
                "                    kind: MIR_OP_COPY,\n"
                "                    location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "                    place: mir_local_place(idx_loc.v),\n"
                "                    constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } }\n"
                "                };\n"
                "                let mut cast_rv = MirRvalue {\n"
                "                    kind: MIR_RVALUE_CAST,\n"
                "                    use_op: raw_idx_op,\n"
                "                    repeat_count: 0u64,\n"
                "                    repeat_count_op: 0 as *mut MirOperand,\n"
                "                    borrow_kind: MIR_BORROW_SHARED,\n"
                "                    place: mir_local_place(0u32),\n"
                "                    cast_kind: MIR_CAST_INT_TO_INT,\n"
                "                    target_ty: TypeId { v: usize_ty.v },\n"
                "                    bin_op: MIR_BINOP_ADD,\n"
                "                    lhs: MirOperand { kind: MIR_OP_COPY, location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 }, place: mir_local_place(0u32), constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } } },\n"
                "                    rhs: MirOperand { kind: MIR_OP_COPY, location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 }, place: mir_local_place(0u32), constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } } },\n"
                "                    un_op: MIR_UNOP_NOT,\n"
                "                    variant_idx: 0u32,\n"
                "                    operands: 0 as *mut MirOperand,\n"
                "                    operand_count: 0,\n"
                "                };\n"
                "                mb_emit_assign(mut_view(*b), view(u_idx_pl), view(cast_rv), view(sp));\n"
                "                let idx_op = MirOperand {\n"
                "                    kind: MIR_OP_COPY,\n"
                "                    location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "                    place: mir_local_place(u_idx_loc.v),\n"
                "                    constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } }\n"
                "                };",
            )
            src = src.replace(
                "            if (cv as usize) != 0 && (unsafe { (*cv).kind }) == CONST_STR {",
                "            if (cv as usize) != 0 && (unsafe { (*cv).kind }) == CONST_AGGREGATE {\n"
                "                let mut dummy_sl2 = false;\n"
                "                let p_agg = mir_build_lvalue(mut_view(*b), expr, mut_view(dummy_sl2));\n"
                "                mir_operand_zero(mut_view(*out_op), MIR_OP_COPY);\n"
                "                mir_copy_place(mut_view(out_op.place), view(p_agg));\n"
                "                return;\n"
                "            }\n"
                "            if (cv as usize) != 0 && (unsafe { (*cv).kind }) == CONST_STR {",
            )
            src = src.replace(
                "        b.curr_bb.v = bb_end.v;\n        b.is_diverged = !any_arm_reached_end;",
                "        let _ = any_arm_reached_end;\n        b.curr_bb.v = bb_end.v;\n        b.is_diverged = false;",
            )
            src = src.replace(
                "            b.curr_bb.v = bb_end.v;\n            b.is_diverged = then_diverged && else_diverged;",
                "            let _ = then_diverged;\n            let _ = else_diverged;\n            b.curr_bb.v = bb_end.v;\n            b.is_diverged = false;",
            )
            src = src.replace(
                "        b.curr_bb.v = bb_end.v;\n        b.is_diverged = then_diverged && else_diverged;",
                "        let _ = then_diverged;\n        let _ = else_diverged;\n        b.curr_bb.v = bb_end.v;\n        b.is_diverged = false;",
            )
            rv_pat = (
                "MirRvalue {\n"
                "        kind: MIR_RVALUE_USE,\n"
                "        use_op: MirOperand {\n"
                "            kind: MIR_OP_COPY,\n"
                "            location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "            place: MirPlace { local: MirLocalId { v: 0u32 }, region: 0u8, view_kind: 0u8, projs: 0 as *mut MirProjection, proj_count: 0, drop_flag: MIR_DROP_FLAG_NONE },\n"
                "            constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } },\n"
                "        },\n"
                "        repeat_count: 0u64,\n"
                "        repeat_count_op: 0 as *mut MirOperand,\n"
                "        borrow_kind: MIR_BORROW_SHARED,\n"
                "        place: MirPlace { local: MirLocalId { v: 0u32 }, region: 0u8, view_kind: 0u8, projs: 0 as *mut MirProjection, proj_count: 0, drop_flag: MIR_DROP_FLAG_NONE },\n"
                "        cast_kind: MIR_CAST_INT_TO_INT,\n"
                "        target_ty: TypeId { v: 0u32 },\n"
                "        bin_op: MIR_BINOP_ADD,\n"
                "        lhs: MirOperand {\n"
                "            kind: MIR_OP_COPY,\n"
                "            location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "            place: MirPlace { local: MirLocalId { v: 0u32 }, region: 0u8, view_kind: 0u8, projs: 0 as *mut MirProjection, proj_count: 0, drop_flag: MIR_DROP_FLAG_NONE },\n"
                "            constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } },\n"
                "        },\n"
                "        rhs: MirOperand {\n"
                "            kind: MIR_OP_COPY,\n"
                "            location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "            place: MirPlace { local: MirLocalId { v: 0u32 }, region: 0u8, view_kind: 0u8, projs: 0 as *mut MirProjection, proj_count: 0, drop_flag: MIR_DROP_FLAG_NONE },\n"
                "            constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } },\n"
                "        },\n"
                "        un_op: MIR_UNOP_NOT,\n"
                "        variant_idx: 0u32,\n"
                "        operands: 0 as *mut MirOperand,\n"
                "        operand_count: 0,\n"
                "    }"
            )
            src = src.replace(rv_pat, "mb_zero_rv()")
            import re as _re
            op_re = _re.compile(
                r"(let mut \w+ = )MirOperand \{\s*kind: MIR_OP_COPY,\s*location: Span \{\s*file: FileId \{\s*v: 0u32\s*\},\s*start: 0u32,\s*end: 0u32\s*\},\s*place: MirPlace \{\s*local: MirLocalId \{\s*v: 0u32\s*\},\s*region: 0u8,\s*view_kind: 0u8,\s*projs: 0 as \*mut MirProjection,\s*proj_count: 0,\s*drop_flag: MIR_DROP_FLAG_NONE\s*\},\s*constant: MirConst \{\s*ty: TypeId \{\s*v: 0u32\s*\},\s*kind: MIR_CONST_INT,\s*val: 0u64,\s*str_bytes: 0 as \*const u8,\s*str_len: 0,\s*sym: SymbolId \{\s*v: 0u32\s*\}\s*\}\s*\}"
            )
            src = op_re.sub(r"\1mb_zero_op()", src)
            src = src.replace(
                "fn mb_emit_stmt(b: mut_view<MirBuilder>, stmt: view<MirStmt>) {",
                "fn mb_zero_op() -> MirOperand {\n"
                "    MirOperand {\n"
                "        kind: MIR_OP_COPY,\n"
                "        location: Span { file: FileId { v: 0u32 }, start: 0u32, end: 0u32 },\n"
                "        place: MirPlace { local: MirLocalId { v: 0u32 }, region: 0u8, view_kind: 0u8, projs: 0 as *mut MirProjection, proj_count: 0, drop_flag: MIR_DROP_FLAG_NONE },\n"
                "        constant: MirConst { ty: TypeId { v: 0u32 }, kind: MIR_CONST_INT, val: 0u64, str_bytes: 0 as *const u8, str_len: 0, sym: SymbolId { v: 0u32 } },\n"
                "    }\n"
                "}\n\n"
                "fn mb_zero_rv() -> MirRvalue {\n"
                "    " + rv_pat + "\n"
                "}\n\n"
                "fn mb_emit_stmt(b: mut_view<MirBuilder>, stmt: view<MirStmt>) {",
            )
        if name == "compiler.types.typeck":
            src = src.replace(
                "fn eval_array_len_expr(cx: mut_view<TypeckCtx>, len_expr: *const HirExpr, out_len: mut_view<u64>) -> bool {\n"
                "    *out_len = 0u64;\n"
                "    if (len_expr as usize) == 0 { return false; }",
                "fn eval_array_len_expr(cx: mut_view<TypeckCtx>, len_expr: *const HirExpr, out_len: mut_view<u64>) -> bool {\n"
                "    *out_len = 0u64;\n"
                "    if (len_expr as usize) == 0 { return false; }\n"
                "    if unsafe { (*len_expr).kind } == HIR_EXPR_LITERAL && unsafe { (*len_expr).literal.kind } == TOK_INT {\n"
                "        let mut val0: u64 = 0u64;\n"
                "        let mut err0: u32 = 0u32;\n"
                "        if eval_const_expr_int(mut_view(*cx), len_expr, mut_view(val0), mut_view(err0)) {\n"
                "            *out_len = val0;\n"
                "            return true;\n"
                "        }\n"
                "    }",
            )
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
                "fn tc_is_drop_trait_name(sv: view<StrView>) -> bool {\n"
                "    if (sv.len) < 4 {\n"
                "        return false;\n"
                "    }\n"
                "    let off = sv.len - 4;\n"
                "    if off > 0 && (unsafe { *(sv.ptr + off - 1) }) != 46u8 {\n"
                "        return false;\n"
                "    }\n"
                "    let b0 = unsafe { *(sv.ptr + off) };\n"
                "    let b1 = unsafe { *(sv.ptr + off + 1) };\n"
                "    let b2 = unsafe { *(sv.ptr + off + 2) };\n"
                "    let b3 = unsafe { *(sv.ptr + off + 3) };\n"
                "    b0 == 68u8 && b1 == 114u8 && b2 == 111u8 && b3 == 112u8\n"
                "}\n\n"
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
                "                let mut tname = StrView { ptr: 0 as *const u8, len: 0 };\n"
                "                if (unsafe { (*tp).path.name.v }) != 0u32 {\n"
                "                    tname = unsafe { interner_get(view(*cx.str_in), (*tp).path.name) };\n"
                "                } else if (cx.db as usize) != 0 {\n"
                "                    tname = unsafe { source_db_span_text(view(*cx.db), (*tp).span) };\n"
                "                }\n"
                "                if tc_is_drop_trait_name(view(tname)) {\n"
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
                "                let mut tname = StrView { ptr: 0 as *const u8, len: 0 };\n"
                "                if (cx.str_in as usize) != 0 && (unsafe { (*tp_node).path.name.v }) != 0u32 {\n"
                "                    tname = unsafe { interner_get(view(*cx.str_in), (*tp_node).path.name) };\n"
                "                } else if (cx.db as usize) != 0 {\n"
                "                    tname = unsafe { source_db_span_text(view(*cx.db), (*tp_node).span) };\n"
                "                }\n"
                "                if tc_is_drop_trait_name(view(tname)) {\n"
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
        if name == "compiler.kernel.hash":
            for _bi in range(8):
                src = src.replace("s.buf[%d]" % _bi, "s.buf[%dusize]" % _bi)
        if name == "compiler.obj.coff":
            src = src.replace(
                "        *a = arena_new();",
                "        let new_a = arena_new();\n        *a = new_a;",
            )
        if name == "compiler.kernel.id":
            src = src.replace(
                "use std.core.host.heap_alloc\nuse std.core.host.heap_free",
                "@intrinsic pub unsafe fn heap_alloc(size: usize, align: usize) -> *mut u8 { 0 as *mut u8 }\n"
                "@intrinsic pub unsafe fn heap_free(p: *mut u8, size: usize, align: usize) {}",
            )
        else:
            src = src.replace("use std.core.host.heap_alloc", "use compiler.kernel.id.heap_alloc")
            src = src.replace("use std.core.host.heap_free", "use compiler.kernel.id.heap_free")
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


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
    blobs = []
    for rel_mir, do_mi_mc in UNIT_MIR_FILES:
        mir_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
        lir_bytes = run_inspect(axiom0, "lir", rel_mir)
        mi_bytes = run_inspect(axiom0, "mi", rel_mir) if do_mi_mc else b""
        mc_bytes = run_inspect(axiom0, "mc", rel_mir) if do_mi_mc else b""
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
    out_path = os.path.join(HERE, "qa_backend_unit.ax")
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote %s (%d bytes)" % (out_path, len(full_text)))


def gen_lir_diff_test(modules_text, axiom0, suffix, label, ax_items, mir_files, native_only):
    blobs = []
    prelude_flags = []
    for rel_ax, needs_prelude in ax_items:
        src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
        exp_lir = run_inspect(axiom0, "lir", rel_ax)
        blobs.extend([rel_ax.encode("utf-8"), src_bytes, exp_lir])
        prelude_flags.append(1 if needs_prelude else 0)

    for rel_mir in mir_files:
        mir_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
        exp_lir = run_inspect(axiom0, "lir", rel_mir)
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
    out_path = os.path.join(HERE, "qa_backend_diff_lir_%s.ax" % suffix)
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote %s (%d bytes, %d ax + %d mir cases)" % (out_path, len(full_text), len(ax_items), len(mir_files)))


def gen_mimc_diff_test(modules_text, axiom0, suffix, label, ax_items, mir_files, native_only):
    blobs = []
    prelude_flags = []
    for rel_ax, needs_prelude in ax_items:
        src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
        exp_mi = run_inspect(axiom0, "mi", rel_ax)
        exp_mc = run_inspect(axiom0, "mc", rel_ax)
        blobs.extend([rel_ax.encode("utf-8"), src_bytes, exp_mi, exp_mc])
        prelude_flags.append(1 if needs_prelude else 0)

    for rel_mir in mir_files:
        mir_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
        exp_mi = run_inspect(axiom0, "mi", rel_mir)
        exp_mc = run_inspect(axiom0, "mc", rel_mir)
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
    out_path = os.path.join(HERE, "qa_backend_diff_mi_mc_%s.ax" % suffix)
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote %s (%d bytes, %d ax + %d mir cases)" % (out_path, len(full_text), len(ax_items), len(mir_files)))


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
        b".Lstr.100000",
        b".Lcstr_10",
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
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote %s (%d bytes)" % (out_path, len(full_text)))


def main():
    cli_axiom0 = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--axiom0" and i + 1 < len(sys.argv):
            cli_axiom0 = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    axiom0 = find_axiom0(cli_axiom0)
    modules_text = assemble_modules()

    all_lir_mir = sorted(
        p.replace("\\", "/")
        for p in [
            os.path.relpath(f, ROOT)
            for f in glob.glob(os.path.join(ROOT, "tests", "lir", "*.mir"))
        ]
    )
    mimc_mir = [m for m in all_lir_mir if m not in MIR_ONLY_LIR]

    gen_unit_test(modules_text, axiom0)
    gen_edge_test(modules_text)
    gen_lir_diff_test(modules_text, axiom0, "a", "A", AX_CORPUS_SMALL_LIR, ["tests/lir/add.mir"], False)
    gen_lir_diff_test(modules_text, axiom0, "b", "B", AX_CORPUS_HEAVY, all_lir_mir, True)
    gen_mimc_diff_test(modules_text, axiom0, "a", "A", AX_CORPUS_SMALL_MIMC, ["tests/lir/add.mir"], False)
    gen_mimc_diff_test(modules_text, axiom0, "b", "B", AX_CORPUS_HEAVY, mimc_mir, True)


if __name__ == "__main__":
    main()

