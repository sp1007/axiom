#!/usr/bin/env python3
"""Differential test generator for compiler/own_mir_verify (T082).

Assembles selfhost test bundles in tests/selfhost/own_mir_verify/ that test the
integrated compiler.own_mir_verify session pipeline against axiom0 and cdriver_drop_oracle:

  - qa_own_mir_diff_build_a.ax, qa_own_mir_diff_build_b.ax:
      9 fixtures in tests/mir/build/*.ax (pre-drop MIR vs `axiom0 inspect --emit=mir`,
      post-drop MIR vs `cdriver_drop_oracle`, plus unsafe_check, verify_mir, own_check,
      verify_mir_own, verify_mir_cap, and verify_mir_drop_flags).
  - qa_own_mir_diff_drop_a.ax, qa_own_mir_diff_drop_b.ax:
      9 fixtures in tests/selfhost/drop/fixtures/*.ax (pre-drop MIR, post-drop MIR,
      synthetic glue destructor MIR, plus full own/verify pipeline).
  - qa_own_mir_diff_diag_own_a.ax, qa_own_mir_diff_diag_own_b.ax:
      11 negative fixtures in tests/ui/own/*.ax (diagnostic codes, `moved here` labels,
      byte-for-byte human diagnostic rendering vs `axiom0 check`, and JSON rendering).
  - qa_own_mir_diff_diag_init.ax:
      7 negative fixtures in tests/ui/init/*.ax (definite-initialization & partial-init
      diagnostics vs `axiom0 check`).
  - qa_own_mir_diff_diag_cap_ptr.ax:
      7 negative fixtures in tests/ui/cap/*.ax and tests/ui/ptr/*.ax (capability conflicts,
      view escape/outlives, unsafe required vs `axiom0 check`).
  - qa_own_mir_diff_diag_verify_mir.ax:
      21 `.mir` verifier corpus fixtures in tests/verify/**/*.mir via
      `session_verify_mir_text_and_render_human`.

Usage:
  python tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py \
      [--axiom0 <path/to/axiom0.exe>] [--oracle <path/to/ct_selfhost_drop_cdriver_drop_oracle.exe>]
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REFERENCE_BUNDLE = "tests/selfhost/mir/qa_mir_builder_and_drop_a.ax"

MODULES = [
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
]

PRELUDE = """@link("kernel32")
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

MIR_BUILD_GROUPS = [
    ("build_a", "BUILD_A", [
        "calls",
        "first_mir",
    ], False),
    ("build_b", "BUILD_B", [
        "bitnot",
        "div_assert",
        "mul_assert",
        "qa_eval_order",
        "shift_assert",
        "short_circuit",
        "unary_neg_assert",
    ], True),
]

DROP_GROUPS = [
    ("drop_a", "DROP_A", [
        "d01_scope_exit",
    ], False),
    ("drop_b", "DROP_B", [
        "d02_conditional_move",
        "d03_struct_fields",
        "d04_enum_variants",
        "d05_mixed_nesting",
        "d06_control_flow",
        "d07_call_results",
        "d09_closures",
        "d10_destructor",
        "d11_qa_edges",
    ], True),
]

DIAG_GROUPS = [
    ("own_a", "OWN_A", [
        ("tests/ui/own/use_after_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/uninit.ax", ["AX_INIT_USE_UNINIT"], 0),
    ], [], False),
    ("own_b", "OWN_B", [
        ("tests/ui/own/branch_reinit_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/conditional_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/loop_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/nested_partial_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/param_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/partial_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/partial_move_struct.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/qa_drop_uam_double.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/qa_explicit_drop_uam.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/uninit.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/own/use_after_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
    ], [], True),
    ("init", "INIT", [
        ("tests/ui/init/cond_init.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/cond_reinit.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/init/loop_uninit.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/partial_init.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/qa_partial_struct_use.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/reinit_after_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/init/uninit_basic.ax", ["AX_INIT_USE_UNINIT"], 0),
    ], [], True),
    ("cap_ptr", "CAP_PTR", [
        ("tests/ui/cap/test_view.ax", [
            "AX_TYPE_STORED_VIEW_SELF_REF",
            "AX_TYPE_STORED_VIEW_ESCAPE",
            "AX_TYPE_STORED_VIEW_ESCAPE",
        ], 0),
        ("tests/ui/cap/test_view_cap.ax", [
            "AX_CAP_OUTLIVES_OWNER",
            "AX_CAP_CONFLICT_READ",
            "AX_CAP_CONFLICT_MUT",
            "AX_CAP_OUTLIVES_OWNER",
        ], 0),
        ("tests/ui/cap/test_view_qa.ax", [
            "AX_CAP_CONFLICT_MUT",
            "AX_CAP_OUTLIVES_OWNER",
        ], 0),
        ("tests/ui/ptr/addrof_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
        ("tests/ui/ptr/arith_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
        ("tests/ui/ptr/call_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
        ("tests/ui/ptr/deref_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
    ], [], True),
    ("verify_mir", "VERIFY_MIR", [], [
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
    ], False),
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
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def u32_table(name, values):
    if not values:
        return "const %s: [1]u32 = [0u32];" % name
    lines = ["const %s: [%d]u32 = [" % (name, len(values))]
    for i in range(0, len(values), 10):
        chunk = values[i:i + 10]
        lines.append("    " + ", ".join("%du32" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def code_table(name, codes):
    if not codes:
        return "const %s: [1]u32 = [0u32];" % name
    lines = ["const %s: [%d]u32 = [" % (name, len(codes))]
    for c in codes:
        lines.append("    %s," % c)
    lines.append("];")
    return "\n".join(lines)


def adapt_own_module(name, src):
    """Adapts compiler.own.* imports and keyword module names to the canonical compiler/* modules."""
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
    res = res.replace("(*cap_init_p).head = 0 as *mut ArenaChunk;", "let cap_a = arena_new(); *cap_init_p = cap_a;")
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
    for name, origin in MODULES:
        if origin == "compiler":
            src = read_bytes(files[name]).decode("utf-8").replace("\r\n", "\n")
            src = adapt_own_module(name, src)
        else:
            src = ref[name]
        if name == "compiler.mir.builder":
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
                "                            if (fty_node as usize) != 0 && (unsafe { (*fty_node).kind }) == HIR_TYPE_VIEW {\n"
                "                                let _ = unsafe { type_error(mut_view(cx), view((*f).span), AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP) };\n"
                "                            }\n",
                "",
            )
            src = src.replace(
                "        unsafe { thir_set_item_type(mut_view(*cx.thir), it, (TypeId { v: fn_ty.v })); }\n"
                "        let isym = unsafe { (*it).symbol };\n"
                "        if isym.v != 0u32 {\n"
                "            unsafe { thir_set_sym_type(mut_view(*cx.thir), (SymbolId { v: isym.v }), (TypeId { v: fn_ty.v })); }\n"
                "        }\n",
                "        unsafe { thir_set_item_type(mut_view(*cx.thir), it, (TypeId { v: fn_ty.v })); }\n",
            )
            src = src.replace(
                "    typeck_into(hir_file, mut_view(*sink), mut_view(*str_in), db, evaluator, mut_view(*thir));\n"
                "    if sink.errors == 0 {\n"
                "        unsafe_check(hir_file, view(*thir), mut_view(*sink), view(*str_in));\n"
                "    }\n",
                "    typeck_into(hir_file, mut_view(*sink), mut_view(*str_in), db, evaluator, mut_view(*thir));\n",
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


def find_exe(default_rels):
    for rel in default_rels:
        p = os.path.join(ROOT, *rel.split("/"))
        if os.path.isfile(p):
            return p
    return None


def run_oracle_drop(oracle, rel_ax):
    cmd = [os.path.abspath(oracle), "--std-root", "std", rel_ax]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise SystemExit("oracle failed on %s: %s" % (rel_ax, res.stderr.decode("utf-8", "replace")))
    out = res.stdout.replace(b"\r\n", b"\n")
    header = ("== %s\n" % rel_ax).encode("utf-8")
    if out.startswith(header):
        out = out[len(header):]
    return out


def run_axiom0_check_stderr(axiom0, rel_ax):
    cmd = [os.path.abspath(axiom0), "check", rel_ax]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0:
        raise SystemExit("expected axiom0 check to fail on %s" % rel_ax)
    return res.stderr.replace(b"\r\n", b"\n")


def build_mir_diff_bundle(modules_text, group, upper, items, native_only):
    blobs = []
    synth_flags = []
    prelude_flags = []
    for path_rel, src_bytes, pre_bytes, drop_bytes, synth_bytes, has_synth, needs_prelude in items:
        blobs.append(path_rel.encode("utf-8"))
        blobs.append(src_bytes)
        blobs.append(pre_bytes)
        blobs.append(drop_bytes)
        blobs.append(synth_bytes)
        synth_flags.append(1 if has_synth else 0)
        prelude_flags.append(1 if needs_prelude else 0)
    data = b"".join(blobs)
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_mir_diff.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@CASE_COUNT@", str(len(items)))
        .replace("@GROUP@", upper)
        .replace("@DATA_TABLE@", byte_table("CASE_DATA", data))
        .replace("@OFFSET_TABLE@", u32_table("CASE_OFF", offsets))
        .replace("@SYNTH_TABLE@", u32_table("CASE_SYNTH", synth_flags))
        .replace("@PRELUDE_TABLE@", u32_table("CASE_PRELUDE", prelude_flags))
    )
    twin_name = "qa_own_mir_diff_build_a.ax" if group.startswith("build") else "qa_own_mir_diff_drop_a.ax"
    modes_line = (
        "// modes: native\n"
        "// Reason: heavy selfhost MIR+drop batch; small interp twin is %s.\n" % twin_name
    ) if native_only else ""
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "%s"
        "// stdout: OK own_mir_verify %s (%d cases)\\n\n"
        "// Generated by tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py; do not edit.\n\n"
    ) % (modes_line, upper, len(items))
    full_text = header + PRELUDE + "\n" + modules_text + "\n" + main_src
    out_path = os.path.join(HERE, "qa_own_mir_diff_%s.ax" % group)
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def build_diag_diff_bundle(modules_text, axiom0, group, upper, ax_cases, mir_cases, native_only):
    ax_blobs = []
    ax_counts = []
    ax_code_offs = [0]
    ax_codes = []
    ax_moved_lbl = []

    for rel_path, codes, has_moved_lbl in ax_cases:
        src_bytes = read_bytes(os.path.join(ROOT, *rel_path.split("/"))).replace(b"\r\n", b"\n")
        exp_human = run_axiom0_check_stderr(axiom0, rel_path)
        ax_blobs.append(rel_path.encode("utf-8"))
        ax_blobs.append(src_bytes)
        ax_blobs.append(exp_human)
        ax_counts.append(len(codes))
        ax_codes.extend(codes)
        ax_code_offs.append(len(ax_codes))
        ax_moved_lbl.append(has_moved_lbl)

    ax_data = b"".join(ax_blobs)
    ax_offs = [0]
    for b in ax_blobs:
        ax_offs.append(ax_offs[-1] + len(b))

    mir_blobs = []
    mir_counts = []
    mir_code_offs = [0]
    mir_codes = []

    for rel_path, codes in mir_cases:
        src_bytes = read_bytes(os.path.join(ROOT, *rel_path.split("/"))).replace(b"\r\n", b"\n")
        mir_blobs.append(rel_path.encode("utf-8"))
        mir_blobs.append(src_bytes)
        mir_counts.append(len(codes))
        mir_codes.extend(codes)
        mir_code_offs.append(len(mir_codes))

    mir_data = b"".join(mir_blobs)
    mir_offs = [0]
    for b in mir_blobs:
        mir_offs.append(mir_offs[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_diag_diff.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@AX_CASE_COUNT@", str(len(ax_cases)))
        .replace("@MIR_CASE_COUNT@", str(len(mir_cases)))
        .replace("@GROUP@", upper)
        .replace("@AX_DATA_TABLE@", byte_table("AX_DATA", ax_data))
        .replace("@AX_OFFSET_TABLE@", u32_table("AX_OFF", ax_offs))
        .replace("@AX_EXP_COUNTS@", u32_table("AX_EXP_COUNTS", ax_counts))
        .replace("@AX_EXP_OFF@", u32_table("AX_EXP_OFF", ax_code_offs))
        .replace("@AX_EXP_CODES@", code_table("AX_EXP_CODES", ax_codes))
        .replace("@AX_EXP_MOVED_LBL@", u32_table("AX_EXP_MOVED_LBL", ax_moved_lbl))
        .replace("@MIR_DATA_TABLE@", byte_table("MIR_DATA", mir_data))
        .replace("@MIR_OFFSET_TABLE@", u32_table("MIR_OFF", mir_offs))
        .replace("@MIR_EXP_COUNTS@", u32_table("MIR_EXP_COUNTS", mir_counts))
        .replace("@MIR_EXP_OFF@", u32_table("MIR_EXP_OFF", mir_code_offs))
        .replace("@MIR_EXP_CODES@", code_table("MIR_EXP_CODES", mir_codes))
    )
    modes_line = (
        "// modes: native\n"
        "// Reason: heavy selfhost UI corpus batch; small interp twin is qa_own_mir_diff_diag_own_a.ax.\n"
    ) if native_only else ""
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "%s"
        "// stdout: OK own_mir_verify diag %s (%d ax + %d mir)\\n\n"
        "// Generated by tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py; do not edit.\n\n"
    ) % (modes_line, upper, len(ax_cases), len(mir_cases))
    full_text = header + PRELUDE + "\n" + modules_text + "\n" + main_src
    out_path = os.path.join(HERE, "qa_own_mir_diff_diag_%s.ax" % group)
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def main():
    axiom0 = find_exe([
        "build-snap-T082/build/axiom0.exe",
        "build/axiom0.exe",
    ])
    oracle = find_exe([
        "build-snap-T082/build/tests/ct_selfhost_drop_cdriver_drop_oracle.exe",
        "build/tests/ct_selfhost_drop_cdriver_drop_oracle.exe",
    ])
    args = sys.argv[1:]
    if "--axiom0" in args:
        axiom0 = args[args.index("--axiom0") + 1]
    if "--oracle" in args:
        oracle = args[args.index("--oracle") + 1]
    if not axiom0 or not oracle:
        raise SystemExit("could not locate axiom0.exe or ct_selfhost_drop_cdriver_drop_oracle.exe")

    modules_text = assemble_modules()

    for group, upper, names, native_only in MIR_BUILD_GROUPS:
        items = []
        for name in names:
            rel_ax = "tests/mir/build/%s.ax" % name
            rel_mir = "tests/mir/build/%s.mir" % name
            src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
            pre_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
            drop_bytes = run_oracle_drop(oracle, rel_ax)
            items.append((rel_ax, src_bytes, pre_bytes, drop_bytes, b"", False, False))
        build_mir_diff_bundle(modules_text, group, upper, items, native_only)

    prelude_drop_cases = {"d03_struct_fields", "d09_closures", "d10_destructor", "d11_qa_edges"}
    for group, upper, names, native_only in DROP_GROUPS:
        items = []
        for name in names:
            rel_ax = "tests/selfhost/drop/fixtures/%s.ax" % name
            base_dir = os.path.join(ROOT, "tests", "selfhost", "drop", "fixtures")
            src_bytes = read_bytes(os.path.join(base_dir, name + ".ax")).replace(b"\r\n", b"\n")
            pre_bytes = read_bytes(os.path.join(base_dir, name + ".pre.mir")).replace(b"\r\n", b"\n")
            drop_bytes = read_bytes(os.path.join(base_dir, name + ".drop.mir")).replace(b"\r\n", b"\n")
            synth_path = os.path.join(base_dir, name + ".synth.mir")
            has_synth = os.path.isfile(os.path.join(base_dir, name + ".impl.ax")) and os.path.isfile(synth_path)
            synth_bytes = read_bytes(synth_path).replace(b"\r\n", b"\n") if has_synth else b""
            needs_prelude = name in prelude_drop_cases
            items.append((rel_ax, src_bytes, pre_bytes, drop_bytes, synth_bytes, has_synth, needs_prelude))
        build_mir_diff_bundle(modules_text, group, upper, items, native_only)

    for group, upper, ax_cases, mir_cases, native_only in DIAG_GROUPS:
        build_diag_diff_bundle(modules_text, axiom0, group, upper, ax_cases, mir_cases, native_only)

    return 0


if __name__ == "__main__":
    sys.exit(main())
