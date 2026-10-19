#!/usr/bin/env python3
"""Selfhost unit & differential test generator for compiler/driver (T085c).

Assembles selfhost test bundles in tests/selfhost/driver/ that verify the
complete Axiom compiler driver and pipeline CLI (compiler.driver.opts,
compiler.driver.pipeline, compiler.driver) against axiom0:

  - qa_driver_cli_and_project.ax (modes: interp native):
      CLI option parsing (help/--help/-h, version, --features, inspect, check,
      build, run), usage/version/features/emitter formatting parity against
      axiom0, all option error paths (missing command, unknown command, unknown
      option, missing option value, boolean option with '=', unknown emitter,
      missing -o, unsupported target, missing input file), axiom.toml manifest
      parsing (valid [package] bin/lib, comments/CRLF, negative malformed cases,
      and disk manifest_parse_file), find_std_root_with discovery hierarchy
      (--std-root -> AXIOM_STD -> exe_path -> cwd), derive_module_path, and
      project_discover (single-file and multi-file nested packages).
  - qa_driver_inspect_diff_a.ax (modes: interp native):
      End-to-end differential tests of driver_run_args on `inspect --emit=<kind>`
      comparing stdout/stderr/exit-code against axiom0 across tokens, ast,
      resolved, hir, thir, mir, and mir-opt (-O1) on .ax and .mir inputs.
  - qa_driver_inspect_diff_b.ax (modes: native):
      End-to-end differential tests of driver_run_args on `inspect --emit=<kind>`
      across backend emitters (lir, mi, mc, obj at -O0 and -O1) on .ax and .mir
      inputs plus multi-file package inspection.
  - qa_driver_commands_a.ax (modes: interp native):
      End-to-end tests of driver_run_args on version, --features, help, check
      (ok, human diagnostics, --json diagnostics, --time-passes, .mir input,
      multi-file package), and run (-O0, -O1, --interp, .mir input).
  - qa_driver_commands_b.ax (modes: native):
      End-to-end tests of driver_run_args and driver_execute_build_into across
      multi-file module packages (hello, mutual, nested, prelude_implicit,
      reexport), runtime panic handling (exit 101 + "panic: " stderr), and
      native `build` (--emit=obj COFF object with ax_main symbol, default PE32+
      .exe linking, --stack-reserve override, -O1 build, multi-file package
      build, and real disk output with cleanup).

Usage:
  python tests/selfhost/driver/gen_driver_tests.py [--axiom0 <path/to/axiom0.exe>]
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REFERENCE_BUNDLE = "tests/selfhost/lir/qa_lir_from_ax_a.ax"

STD_SYS_WINDOWS_FILES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/io.ax",
    "std/sys/windows/fs.ax",
    "std/sys/windows/process.ax",
    "std/sys/windows/time.ax",
]

LIGHT_MODULES = [
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
    ("compiler.driver.opts", "compiler"),
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
    ("compiler.syntax.ast", "compiler"),
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
    ("compiler.lir.lir", "compiler"),
    ("compiler.lir.builder", "compiler"),
    ("compiler.lir", "compiler"),
    ("compiler.abi.win64", "compiler"),
    ("compiler.abi", "compiler"),
    ("compiler.obj.coff", "compiler"),
    ("compiler.obj.writer", "compiler"),
    ("compiler.obj", "compiler"),
    ("compiler.target.x64.encode", "compiler"),
    ("compiler.target.x64.isel", "compiler"),
    ("compiler.target.x64.frame", "compiler"),
    ("compiler.target.x64", "compiler"),
    ("compiler.backend.session", "compiler"),
    ("compiler.backend", "compiler"),
    ("compiler.link.pe", "compiler"),
    ("compiler.link.import", "compiler"),
    ("compiler.link.linker", "compiler"),
    ("compiler.link", "compiler"),
    ("compiler.driver.opts", "compiler"),
    ("compiler.driver.pipeline", "compiler"),
    ("compiler.driver", "compiler"),
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


def assemble_modules(mod_list):
    files = compiler_module_files()
    ref = reference_sections()
    parts = []
    for name, origin in mod_list:
        if origin == "compiler":
            src = read_bytes(files[name]).decode("utf-8").replace("\r\n", "\n")
            src = adapt_own_module(name, src)
        else:
            src = ref[name]
        if name == "compiler.syntax.ast":
            src = src.replace(
                "pub fn ax_ast_render(ast: view<Ast>,",
                "pub fn ax_ast_render(ast_root: view<Ast>,",
            ).replace(
                "d_item(mut_view(st), ast.items as *const AstItem);",
                "d_item(mut_view(st), ast_root.items as *const AstItem);",
            )
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
            op_re = re.compile(
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
        if name == "compiler.kernel.interner":
            src = src.replace(
                "    in_.bytes = arena_new();",
                "    let _a = arena_new();\n    in_.bytes = _a;",
            )
        if name == "compiler.source.manager":
            src = src.replace(
                "    db.arena = arena_new();",
                "    let _a = arena_new();\n    db.arena = _a;",
            )
        if name == "compiler.diag.emitter":
            src = src.replace(
                "    sink.arena = arena_new();",
                "    let _a = arena_new();\n    sink.arena = _a;",
            )
        if name == "compiler.kernel_source_diag.session":
            src = src.replace(
                "    s.arena = arena_new();\n"
                "    interner_init(mut_view(s.interner));\n"
                "    s.u32_pool = u32_interner_new();",
                "    let _a = arena_new();\n"
                "    s.arena = _a;\n"
                "    interner_init(mut_view(s.interner));\n"
                "    let _u = u32_interner_new();\n"
                "    s.u32_pool = _u;",
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


def run_axiom0(axiom0, args, expect_rc=None):
    cmd = [os.path.abspath(axiom0)] + list(args)
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if expect_rc is not None and res.returncode != expect_rc:
        raise SystemExit(
            "axiom0 %r returned %d (expected %d): stderr=%r"
            % (args, res.returncode, expect_rc, res.stderr)
        )
    return res.returncode, res.stdout.replace(b"\r\n", b"\n"), res.stderr.replace(b"\r\n", b"\n")


def pack_blobs(blobs):
    all_bytes = bytearray()
    offs = []
    lens = []
    for b in blobs:
        offs.append(len(all_bytes))
        lens.append(len(b))
        all_bytes.extend(b)
    return bytes(all_bytes), offs, lens


def gen_cli_and_project_bundle(prelude, light_mods, axiom0):
    _, exp_help, _ = run_axiom0(axiom0, ["help"], expect_rc=0)
    _, exp_version, _ = run_axiom0(axiom0, ["version"], expect_rc=0)
    _, exp_features, _ = run_axiom0(axiom0, ["--features"], expect_rc=0)
    _, _, exp_inspect_help = run_axiom0(axiom0, ["inspect", "--help"], expect_rc=2)
    _, _, exp_unknown_cmd = run_axiom0(axiom0, ["bogus"], expect_rc=2)
    _, _, exp_unknown_opt = run_axiom0(axiom0, ["check", "--unknown-flag", "tests/driver/test.ax"], expect_rc=2)
    _, _, exp_missing_val = run_axiom0(axiom0, ["check", "--target"], expect_rc=2)
    _, _, exp_unknown_emit = run_axiom0(axiom0, ["inspect", "--emit=bogus", "tests/driver/test.ax"], expect_rc=2)
    _, _, exp_check_no_file = run_axiom0(axiom0, ["check"], expect_rc=2)
    _, _, exp_build_no_file = run_axiom0(axiom0, ["build"], expect_rc=2)
    _, _, exp_build_no_o = run_axiom0(axiom0, ["build", "tests/driver/test.ax"], expect_rc=2)
    _, _, exp_run_no_file = run_axiom0(axiom0, ["run"], expect_rc=2)
    _, _, exp_inspect_no_file = run_axiom0(axiom0, ["inspect", "--emit=tokens"], expect_rc=2)

    blobs = [
        exp_help,              # 0: help usage
        exp_version,           # 1: version
        exp_features,          # 2: --features
        exp_inspect_help,      # 3: inspect --help stderr
        exp_unknown_cmd,       # 4: unknown command 'bogus' stderr
        exp_unknown_opt,       # 5: unknown option '--unknown-flag' stderr
        exp_missing_val,       # 6: option '--target' requires an argument stderr
        exp_unknown_emit,      # 7: unknown emitter 'bogus' stderr
        exp_check_no_file,     # 8: check needs an input file
        exp_build_no_file,     # 9: build needs an input file
        exp_build_no_o,        # 10: build needs an output file (-o)
        exp_run_no_file,       # 11: run needs an input file
        exp_inspect_no_file,   # 12: usage: axiom0 inspect --emit=tokens <file>
        # Strings for CLI, manifest, std_root, derive_module_path, project_discover:
        b"axiom0",                       # 13
        b"help",                         # 14
        b"--help",                       # 15
        b"-h",                           # 16
        b"version",                      # 17
        b"--features",                   # 18
        b"inspect",                      # 19
        b"check",                        # 20
        b"build",                        # 21
        b"run",                          # 22
        b"bogus",                        # 23
        b"--unknown-flag",               # 24
        b"tests/driver/test.ax",         # 25
        b"--target",                     # 26
        b"--emit=bogus",                 # 27
        b"--emit=tokens",                # 28
        b"--color=never",                # 29
        b"--time-passes",                # 30
        b"--json",                       # 31
        b"-O1",                          # 32
        b"--verify-each",                # 33
        b"--target=x86_64-pc-windows-msvc",  # 34
        b"--std-root=std",               # 35
        b"--interp",                     # 36
        b"--step-limit=12345",           # 37
        b"--max-call-depth=678",         # 38
        b"--",                           # 39
        b"arg1",                         # 40
        b"arg2",                         # 41
        b"x86_64-pc-windows-msvc",       # 42
        b"std",                          # 43
        b"--target=aarch64-unknown-linux-gnu",  # 44
        b"--json=true",                  # 45
        b"axiom0: option '--json' does not take an argument\n",  # 46
        b"-o",                           # 47
        b"out.exe",                      # 48
        b"--stack-reserve",              # 49
        b"2097152",                      # 50
        # Manifest test inputs:
        b"# Package manifest\r\n[package]\r\nname = \"my_pkg\" # inline comment\r\nkind = \"lib\"\r\n",  # 51
        b"my_pkg",                       # 52
        b"lib",                          # 53
        b"name = \"no_section\"\n",      # 54: missing [package]
        b"[dependencies]\nfoo = \"1\"\n", # 55: unknown section
        b"[package]\nkind = \"bin\"\n",  # 56: missing name
        b"[package]\nname = \"\"\n",     # 57: empty name
        b"[package]\nname = unquoted\n", # 58: unquoted value
        b"[package]\nname = \"ok\"\nbroken_no_eq\n",  # 59: missing '='
        b"tests/modules/hello/axiom.toml",  # 60
        b"hello",                        # 61
        b"bin",                          # 62
        # std_root & derive_module_path & project_discover inputs:
        b".",                            # 63
        b"./std",                        # 64
        b"nonexistent_std_dir_xyz",      # 65
        b"build/axiom0.exe",             # 66
        b"main",                         # 67
        b"src/main.ax",                  # 68
        b"src/math.ax",                  # 69
        b"math",                         # 70
        b"src/utils/calc.ax",            # 71
        b"utils.calc",                   # 72
        b"src/a/b/c.ax",                 # 73
        b"a.b.c",                        # 74
        b"tests/modules/hello/src/main.ax",   # 75
        b"tests/modules/nested/src/main.ax",  # 76
        b"a",                            # 77
        b"ast",                          # 78
        b"hir",                          # 79
        b"lir",                          # 80
        b"mc",                           # 81
        b"mi",                           # 82
        b"mir",                          # 83
        b"mir-opt",                      # 84
        b"obj",                          # 85
        b"resolved",                     # 86
        b"thir",                         # 87
        b"tokens",                       # 88
    ]
    blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_cli_and_project_test

use host_intrinsics.heap_alloc
use host_intrinsics.heap_free
use compiler.kernel.arena.Arena
use compiler.kernel.arena.arena_new
use compiler.kernel.arena.arena_destroy
use compiler.kernel.interner.StrView
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.diag_sink_init
use compiler.diag.emitter.diag_sink_free
use compiler.diag.emitter.diag_sink_error_count
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_USAGE
use compiler.driver.opts.CMD_NONE
use compiler.driver.opts.CMD_HELP
use compiler.driver.opts.CMD_VERSION
use compiler.driver.opts.CMD_FEATURES
use compiler.driver.opts.CMD_INSPECT
use compiler.driver.opts.CMD_CHECK
use compiler.driver.opts.CMD_BUILD
use compiler.driver.opts.CMD_RUN
use compiler.driver.opts.EMIT_NONE
use compiler.driver.opts.EMIT_AST
use compiler.driver.opts.EMIT_HIR
use compiler.driver.opts.EMIT_LIR
use compiler.driver.opts.EMIT_MC
use compiler.driver.opts.EMIT_MI
use compiler.driver.opts.EMIT_MIR
use compiler.driver.opts.EMIT_MIR_OPT
use compiler.driver.opts.EMIT_OBJ
use compiler.driver.opts.EMIT_RESOLVED
use compiler.driver.opts.EMIT_THIR
use compiler.driver.opts.EMIT_TOKENS
use compiler.driver.opts.DriverOptions
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_get
use compiler.driver.opts.sv_slot_set
use compiler.driver.opts.driver_options_alloc
use compiler.driver.opts.driver_options_dealloc
use compiler.driver.opts.driver_format_usage
use compiler.driver.opts.driver_format_version
use compiler.driver.opts.driver_format_features
use compiler.driver.opts.driver_format_emitters
use compiler.driver.opts.driver_find_command
use compiler.driver.opts.driver_find_emitter
use compiler.driver.opts.driver_parse_cli
use compiler.driver.opts.PackageManifest
use compiler.driver.opts.manifest_alloc
use compiler.driver.opts.manifest_dealloc
use compiler.driver.opts.manifest_parse_text
use compiler.driver.opts.manifest_read_file
use compiler.driver.opts.find_std_root_with
use compiler.driver.opts.derive_module_path
use compiler.driver.opts.Project
use compiler.driver.opts.ProjectFile
use compiler.driver.opts.project_alloc
use compiler.driver.opts.project_dealloc
use compiler.driver.opts.project_discover
use compiler.driver.opts.project_file_const_at
use compiler.driver.opts.pf_get_module_path

@intrinsic fn size_of<T>() -> usize { 0 }
@intrinsic fn align_of<T>() -> usize { 0 }

unsafe fn diag_sink_alloc() -> *mut DiagSink {
    let bytes = size_of<DiagSink>();
    let raw = heap_alloc(bytes, align_of<DiagSink>());
    let mut i: usize = 0;
    while i < bytes {
        *(raw + i) = 0u8;
        i = i + 1;
    }
    let p = raw as *mut DiagSink;
    diag_sink_init(mut_view(*p));
    p
}

unsafe fn diag_sink_dealloc(p: *mut DiagSink) {
    if (p as usize) == 0 { return; }
    diag_sink_free(mut_view(*p));
    heap_free(p as *mut u8, size_of<DiagSink>(), align_of<DiagSink>());
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

fn blob_sv(idx: usize) -> StrView {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    unsafe { *(buf + blen) = 0u8; }
    StrView {
        ptr: buf as *const u8,
        len: blen,
    }
}

fn alloc_argv(cap: usize) -> *mut StrView {
    let bytes = opts_mul_usize(cap, 16);
    unsafe { heap_alloc(bytes, 8) as *mut StrView }
}

fn set_arg_blob(argv: *mut StrView, idx: usize, blob_idx: usize) {
    let s = blob_sv(blob_idx);
    sv_slot_set(argv, idx, view(s));
}

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn sv_matches_blob(sv: view<StrView>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if sv.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(sv.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn check_parse_cli_case(
    argv: *const StrView,
    argc: usize,
    exp_rc: i32,
    exp_out_blob: isize,
    exp_err_blob: isize
) -> bool {
    let dopts = unsafe { driver_options_alloc() };
    let mut out_buf = diag_buf_new();
    let mut err_buf = diag_buf_new();
    let rc = unsafe { driver_parse_cli(argv, argc, mut_view(*dopts), mut_view(out_buf), mut_view(err_buf)) };
    let mut ok = rc == exp_rc;
    if ok && exp_out_blob >= 0isize {
        if !buf_matches_blob(view(out_buf), exp_out_blob as usize) {
            ok = false;
        }
    }
    if ok && exp_err_blob >= 0isize {
        if !buf_matches_blob(view(err_buf), exp_err_blob as usize) {
            ok = false;
        }
    }
    diag_buf_free(mut_view(out_buf));
    diag_buf_free(mut_view(err_buf));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

fn find_cmd_blob(blob_idx: usize) -> u32 {
    let b = blob_sv(blob_idx);
    driver_find_command(view(b))
}

fn find_emit_blob(blob_idx: usize) -> u32 {
    let b = blob_sv(blob_idx);
    driver_find_emitter(view(b))
}

fn test_cli_formatting_and_lookup() -> i32 {
    let mut b = diag_buf_new();
    driver_format_usage(mut_view(b));
    if !buf_matches_blob(view(b), 0) {
        diag_buf_free(mut_view(b));
        return 10;
    }
    diag_buf_free(mut_view(b));

    let mut b2 = diag_buf_new();
    driver_format_version(mut_view(b2));
    if !buf_matches_blob(view(b2), 1) {
        diag_buf_free(mut_view(b2));
        return 11;
    }
    diag_buf_free(mut_view(b2));

    let mut b3 = diag_buf_new();
    driver_format_features(mut_view(b3));
    if !buf_matches_blob(view(b3), 2) {
        diag_buf_free(mut_view(b3));
        return 12;
    }
    diag_buf_free(mut_view(b3));

    if find_cmd_blob(14) != CMD_HELP { return 13; }
    if find_cmd_blob(15) != CMD_HELP { return 14; }
    if find_cmd_blob(16) != CMD_HELP { return 15; }
    if find_cmd_blob(17) != CMD_VERSION { return 16; }
    if find_cmd_blob(18) != CMD_FEATURES { return 17; }
    if find_cmd_blob(19) != CMD_INSPECT { return 18; }
    if find_cmd_blob(20) != CMD_CHECK { return 19; }
    if find_cmd_blob(21) != CMD_BUILD { return 20; }
    if find_cmd_blob(22) != CMD_RUN { return 21; }
    if find_cmd_blob(23) != CMD_NONE { return 22; }

    if find_emit_blob(78) != EMIT_AST { return 23; }
    if find_emit_blob(79) != EMIT_HIR { return 24; }
    if find_emit_blob(80) != EMIT_LIR { return 25; }
    if find_emit_blob(81) != EMIT_MC { return 26; }
    if find_emit_blob(82) != EMIT_MI { return 27; }
    if find_emit_blob(83) != EMIT_MIR { return 28; }
    if find_emit_blob(84) != EMIT_MIR_OPT { return 29; }
    if find_emit_blob(85) != EMIT_OBJ { return 30; }
    if find_emit_blob(86) != EMIT_RESOLVED { return 31; }
    if find_emit_blob(87) != EMIT_THIR { return 32; }
    if find_emit_blob(88) != EMIT_TOKENS { return 33; }
    if find_emit_blob(23) != EMIT_NONE { return 34; }
    0
}

fn test_cli_parsing() -> i32 {
    let a = alloc_argv(16);
    let ap = a as *const StrView;
    set_arg_blob(a, 0, 13);

    // 1. No args -> rc 2, err == usage
    if !check_parse_cli_case(ap, 1, AX_EXIT_USAGE, -1isize, 0isize) { return 40; }

    // 2. help, --help, -h -> rc 0, out == usage
    set_arg_blob(a, 1, 14);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 0isize, -1isize) { return 41; }
    set_arg_blob(a, 1, 15);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 0isize, -1isize) { return 42; }
    set_arg_blob(a, 1, 16);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 0isize, -1isize) { return 43; }

    // 3. version, --features -> rc 0
    set_arg_blob(a, 1, 17);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 1isize, -1isize) { return 44; }
    set_arg_blob(a, 1, 18);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 2isize, -1isize) { return 45; }

    // 4. inspect --help -> rc 2, err == inspect usage + emitters
    set_arg_blob(a, 1, 19);
    set_arg_blob(a, 2, 15);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 3isize) { return 46; }

    // 5. unknown command 'bogus' -> rc 2
    set_arg_blob(a, 1, 23);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 4isize) { return 47; }

    // 6. unknown option '--unknown-flag' -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 24);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, 5isize) { return 48; }

    // 7. missing value for '--target' -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 26);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 6isize) { return 49; }

    // 8. unknown emitter '--emit=bogus' -> rc 2
    set_arg_blob(a, 1, 19);
    set_arg_blob(a, 2, 27);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, 7isize) { return 50; }

    // 9. missing input files and missing -o
    set_arg_blob(a, 1, 20);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 8isize) { return 51; }
    set_arg_blob(a, 1, 21);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 9isize) { return 52; }
    set_arg_blob(a, 1, 21);
    set_arg_blob(a, 2, 25);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 10isize) { return 53; }
    set_arg_blob(a, 1, 22);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 11isize) { return 54; }
    set_arg_blob(a, 1, 19);
    set_arg_blob(a, 2, 28);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 12isize) { return 55; }

    // 10. boolean option with '=' (--json=true) -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 45);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, 46isize) { return 56; }

    // 11. unsupported target -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 44);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, -1isize) { return 57; }

    // 12. Full flag set + `--` pass-through args
    set_arg_blob(a, 1, 22);  // run
    set_arg_blob(a, 2, 29);  // --color=never
    set_arg_blob(a, 3, 30);  // --time-passes
    set_arg_blob(a, 4, 31);  // --json
    set_arg_blob(a, 5, 32);  // -O1
    set_arg_blob(a, 6, 33);  // --verify-each
    set_arg_blob(a, 7, 34);  // --target=x86_64-pc-windows-msvc
    set_arg_blob(a, 8, 35);  // --std-root=std
    set_arg_blob(a, 9, 36);  // --interp
    set_arg_blob(a, 10, 37); // --step-limit=12345
    set_arg_blob(a, 11, 38); // --max-call-depth=678
    set_arg_blob(a, 12, 25); // tests/driver/test.ax
    set_arg_blob(a, 13, 39); // --
    set_arg_blob(a, 14, 40); // arg1
    set_arg_blob(a, 15, 41); // arg2

    let dopts = unsafe { driver_options_alloc() };
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let rc = unsafe { driver_parse_cli(ap, 16, mut_view(*dopts), mut_view(out_b), mut_view(err_b)) };
    let mut flags_ok = unsafe {
        rc == AX_EXIT_OK &&
        (*dopts).cmd == CMD_RUN &&
        (*dopts).color_never &&
        (*dopts).time_passes &&
        (*dopts).json &&
        (*dopts).opt_O1 &&
        !(*dopts).opt_O0 &&
        (*dopts).verify_each &&
        (*dopts).run_interp &&
        (*dopts).step_limit == 12345 &&
        (*dopts).max_call_depth == 678 &&
        sv_matches_blob(view((*dopts).target), 42) &&
        sv_matches_blob(view((*dopts).std_root), 43) &&
        sv_matches_blob(view((*dopts).input_file), 25) &&
        (*dopts).run_argc == 2
    };
    if flags_ok {
        let r0 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 0) };
        let r1 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 1) };
        if !sv_matches_blob(view(r0), 40) || !sv_matches_blob(view(r1), 41) {
            flags_ok = false;
        }
    }
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    if !flags_ok { return 58; }

    // 13. Space-separated build options: build -o out.exe --stack-reserve 2097152 tests/driver/test.ax
    set_arg_blob(a, 1, 21);
    set_arg_blob(a, 2, 47);
    set_arg_blob(a, 3, 48);
    set_arg_blob(a, 4, 49);
    set_arg_blob(a, 5, 50);
    set_arg_blob(a, 6, 25);
    let bopts = unsafe { driver_options_alloc() };
    let mut out_b2 = diag_buf_new();
    let mut err_b2 = diag_buf_new();
    let brc = unsafe { driver_parse_cli(ap, 7, mut_view(*bopts), mut_view(out_b2), mut_view(err_b2)) };
    let b_ok = unsafe {
        brc == AX_EXIT_OK &&
        (*bopts).cmd == CMD_BUILD &&
        sv_matches_blob(view((*bopts).output), 48) &&
        sv_matches_blob(view((*bopts).stack_reserve), 50) &&
        sv_matches_blob(view((*bopts).input_file), 25)
    };
    diag_buf_free(mut_view(out_b2));
    diag_buf_free(mut_view(err_b2));
    unsafe { driver_options_dealloc(bopts); }
    if !b_ok { return 59; }
    0
}

fn test_manifest_and_std_root() -> i32 {
    let m = unsafe { manifest_alloc() };
    let b51 = blob_sv(51);
    let ok1 = unsafe { manifest_parse_text(view(b51), mut_view(*m)) };
    let valid1 = unsafe { ok1 && sv_matches_blob(view((*m).name), 52) && sv_matches_blob(view((*m).kind), 53) };
    unsafe { manifest_dealloc(m); }
    if !valid1 { return 60; }

    // Negative manifest cases (54..59)
    let mut neg_idx: usize = 54;
    while neg_idx <= 59 {
        let nm = unsafe { manifest_alloc() };
        let bneg = blob_sv(neg_idx);
        let nok = unsafe { manifest_parse_text(view(bneg), mut_view(*nm)) };
        unsafe { manifest_dealloc(nm); }
        if nok { return (70 + (neg_idx - 54)) as i32; }
        neg_idx = neg_idx + 1;
    }

    // Disk manifest_read_file on tests/modules/hello/axiom.toml
    let dm = unsafe { manifest_alloc() };
    let b60 = blob_sv(60);
    let dok = unsafe { manifest_read_file(view(b60), mut_view(*dm)) };
    let dvalid = unsafe { dok && sv_matches_blob(view((*dm).name), 61) };
    unsafe { manifest_dealloc(dm); }
    if !dvalid { return 78; }

    // find_std_root_with hierarchy
    let mut arena = arena_new();
    let empty = StrView { ptr: 0 as *const u8, len: 0 };
    let b43 = blob_sv(43);
    let b65 = blob_sv(65);
    let b66 = blob_sv(66);
    let r1 = find_std_root_with(view(b43), view(empty), view(empty), mut_view(arena));
    if !sv_matches_blob(view(r1), 43) {
        arena_destroy(mut_view(arena));
        return 79;
    }

    let r2 = find_std_root_with(view(b65), view(b43), view(b66), mut_view(arena));
    if r2.len != 0 {
        arena_destroy(mut_view(arena));
        return 80;
    }

    let r3 = find_std_root_with(view(empty), view(b43), view(empty), mut_view(arena));
    if !sv_matches_blob(view(r3), 43) {
        arena_destroy(mut_view(arena));
        return 81;
    }

    let r4 = find_std_root_with(view(empty), view(empty), view(b66), mut_view(arena));
    if r4.len == 0 {
        arena_destroy(mut_view(arena));
        return 82;
    }

    // derive_module_path
    let b68 = blob_sv(68);
    let mp0 = derive_module_path(view(b68), mut_view(arena));
    if !sv_matches_blob(view(mp0), 67) {
        arena_destroy(mut_view(arena));
        return 84;
    }
    let b69 = blob_sv(69);
    let mp1 = derive_module_path(view(b69), mut_view(arena));
    if !sv_matches_blob(view(mp1), 70) {
        arena_destroy(mut_view(arena));
        return 85;
    }
    let b71 = blob_sv(71);
    let mp2 = derive_module_path(view(b71), mut_view(arena));
    if !sv_matches_blob(view(mp2), 72) {
        arena_destroy(mut_view(arena));
        return 86;
    }
    let b73 = blob_sv(73);
    let mp3 = derive_module_path(view(b73), mut_view(arena));
    if !sv_matches_blob(view(mp3), 74) {
        arena_destroy(mut_view(arena));
        return 87;
    }

    arena_destroy(mut_view(arena));
    0
}

fn test_project_discovery() -> i32 {
    let empty = StrView { ptr: 0 as *const u8, len: 0 };

    // 1. Single-file discovery on tests/driver/test.ax (1 user file + 3 std core files = 4)
    let sink1 = unsafe { diag_sink_alloc() };
    let p1 = unsafe { project_alloc() };
    let b25 = blob_sv(25);
    let ok1 = unsafe { project_discover(view(b25), view(empty), mut_view(*p1), mut_view(*sink1)) };
    let v1 = unsafe { ok1 && !(*p1).is_package && (*p1).file_count == 4 && diag_sink_error_count(view(*sink1)) == 0 };
    unsafe {
        project_dealloc(p1);
        diag_sink_dealloc(sink1);
    }
    if !v1 { return 90; }

    // 2. Multi-file package discovery on tests/modules/hello/src/main.ax (2 user + 3 std = 5)
    let sink2 = unsafe { diag_sink_alloc() };
    let p2 = unsafe { project_alloc() };
    let b75 = blob_sv(75);
    let ok2 = unsafe { project_discover(view(b75), view(empty), mut_view(*p2), mut_view(*sink2)) };
    let mut v2 = unsafe {
        ok2 &&
        (*p2).is_package &&
        (*p2).has_manifest &&
        sv_matches_blob(view((*p2).manifest.name), 61) &&
        (*p2).file_count == 5 &&
        diag_sink_error_count(view(*sink2)) == 0
    };
    if v2 {
        let pf0 = unsafe { project_file_const_at((*p2).files as *const ProjectFile, 0) };
        let pf1 = unsafe { project_file_const_at((*p2).files as *const ProjectFile, 1) };
        let mp0 = pf_get_module_path(pf0);
        let mp1 = pf_get_module_path(pf1);
        if !sv_matches_blob(view(mp0), 67) || !sv_matches_blob(view(mp1), 70) {
            v2 = false;
        }
    }
    unsafe {
        project_dealloc(p2);
        diag_sink_dealloc(sink2);
    }
    if !v2 { return 91; }

    // 3. Nested multi-file package discovery on tests/modules/nested/src/main.ax (2 user + 3 std = 5)
    let sink3 = unsafe { diag_sink_alloc() };
    let p3 = unsafe { project_alloc() };
    let b76 = blob_sv(76);
    let ok3 = unsafe { project_discover(view(b76), view(empty), mut_view(*p3), mut_view(*sink3)) };
    let mut v3 = unsafe { ok3 && (*p3).is_package && (*p3).file_count == 5 && diag_sink_error_count(view(*sink3)) == 0 };
    if v3 {
        let nf0 = unsafe { project_file_const_at((*p3).files as *const ProjectFile, 0) };
        let nf1 = unsafe { project_file_const_at((*p3).files as *const ProjectFile, 1) };
        let nmp0 = pf_get_module_path(nf0);
        let nmp1 = pf_get_module_path(nf1);
        // Sorted paths: src/main.ax ("main"), src/utils/calc.ax ("utils.calc")
        if !sv_matches_blob(view(nmp0), 67) || !sv_matches_blob(view(nmp1), 72) {
            v3 = false;
        }
    }
    unsafe {
        project_dealloc(p3);
        diag_sink_dealloc(sink3);
    }
    if !v3 { return 92; }
    0
}

pub fn main() -> i32 {
    let r1 = test_cli_formatting_and_lookup();
    if r1 != 0 { return r1; }
    let r2 = test_cli_parsing();
    if r2 != 0 { return r2; }
    let r3 = test_manifest_and_std_root();
    if r3 != 0 { return r3; }
    let r4 = test_project_discovery();
    if r4 != 0 { return r4; }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(blobs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: interp native\n\n"
    full_text = header + prelude + "\n" + light_mods + "\n" + main_src
    write_bytes(os.path.join(HERE, "qa_driver_cli_and_project.ax"), full_text.encode("utf-8"))


def gen_inspect_diff_bundle(filename, modes, prelude, full_mods, axiom0, cases, fast_std=False):
    blobs = [b"axiom0", b"inspect", b"-O1", b"--std-root=tests/driver"]
    case_meta = []
    for emit_flag, opt_o1, input_path in cases:
        emit_idx = len(blobs)
        blobs.append(emit_flag.encode("utf-8"))
        in_idx = len(blobs)
        blobs.append(input_path.encode("utf-8"))

        extra = ["--std-root=tests/driver"] if fast_std else []
        if emit_flag == "--emit=mir-opt" or (emit_flag == "--emit=mir" and opt_o1):
            args = ["inspect"] + extra + ["--emit=mir", "-O1", input_path]
        else:
            args = ["inspect"] + extra + [emit_flag] + (["-O1"] if opt_o1 else []) + [input_path]
        rc, out_b, err_b = run_axiom0(axiom0, args, expect_rc=0)
        out_idx = len(blobs)
        blobs.append(out_b)
        err_idx = len(blobs)
        blobs.append(err_b)
        case_meta.append((emit_idx, 1 if opt_o1 else 0, in_idx, rc, out_idx, err_idx))

    blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_inspect_diff_test

use host_intrinsics.heap_alloc
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.driver.pipeline.driver_run_args

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

const CASE_EMIT: [%(num_cases)d]usize = [%(case_emit)s];
const CASE_O1: [%(num_cases)d]u32 = [%(case_o1)s];
const CASE_IN: [%(num_cases)d]usize = [%(case_in)s];
const CASE_RC: [%(num_cases)d]i32 = [%(case_rc)s];
const CASE_OUT: [%(num_cases)d]usize = [%(case_out)s];
const CASE_ERR: [%(num_cases)d]usize = [%(case_err)s];
const USE_FAST_STD: u32 = %(use_fast_std)du32;

fn blob_sv(idx: usize) -> StrView {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    unsafe { *(buf + blen) = 0u8; }
    StrView {
        ptr: buf as *const u8,
        len: blen,
    }
}

fn alloc_argv(cap: usize) -> *mut StrView {
    let bytes = opts_mul_usize(cap, 16);
    unsafe { heap_alloc(bytes, 8) as *mut StrView }
}

fn set_arg_blob(argv: *mut StrView, idx: usize, blob_idx: usize) {
    let s = blob_sv(blob_idx);
    sv_slot_set(argv, idx, view(s));
}

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

pub fn main() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;
    let mut c: usize = 0;
    while c < %(num_cases)d {
        set_arg_blob(argv, 0, 0);
        set_arg_blob(argv, 1, 1);
        let mut argc: usize = 4;
        if USE_FAST_STD != 0u32 {
            set_arg_blob(argv, 2, 3);
            set_arg_blob(argv, 3, CASE_EMIT[c]);
            if CASE_O1[c] != 0u32 {
                set_arg_blob(argv, 4, 2);
                set_arg_blob(argv, 5, CASE_IN[c]);
                argc = 6;
            } else {
                set_arg_blob(argv, 4, CASE_IN[c]);
                argc = 5;
            }
        } else {
            set_arg_blob(argv, 2, CASE_EMIT[c]);
            if CASE_O1[c] != 0u32 {
                set_arg_blob(argv, 3, 2);
                set_arg_blob(argv, 4, CASE_IN[c]);
                argc = 5;
            } else {
                set_arg_blob(argv, 3, CASE_IN[c]);
                argc = 4;
            }
        }

        let mut out_buf = diag_buf_new();
        let mut err_buf = diag_buf_new();
        let rc = driver_run_args(ap, argc, mut_view(out_buf), mut_view(err_buf));
        let ok_rc = rc == CASE_RC[c];
        let ok_out = buf_matches_blob(view(out_buf), CASE_OUT[c]);
        let ok_err = buf_matches_blob(view(err_buf), CASE_ERR[c]);
        diag_buf_free(mut_view(out_buf));
        diag_buf_free(mut_view(err_buf));
        if !ok_rc {
            return (10 + c) as i32;
        }
        if !ok_out {
            return (40 + c) as i32;
        }
        if !ok_err {
            return (70 + c) as i32;
        }
        c = c + 1;
    }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(blobs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
        "num_cases": len(case_meta),
        "case_emit": ", ".join(str(x[0]) for x in case_meta),
        "case_o1": ", ".join("%du32" % x[1] for x in case_meta),
        "case_in": ", ".join(str(x[2]) for x in case_meta),
        "case_rc": ", ".join(str(x[3]) for x in case_meta),
        "case_out": ", ".join(str(x[4]) for x in case_meta),
        "case_err": ", ".join(str(x[5]) for x in case_meta),
        "use_fast_std": 1 if fast_std else 0,
    }

    header = "// test: run\n// timeout: 1200\n// modes: %s\n\n" % modes
    full_text = header + prelude + "\n" + full_mods + "\n" + main_src
    write_bytes(os.path.join(HERE, filename), full_text.encode("utf-8"))


def gen_commands_a_bundle(prelude, full_mods, axiom0):
    _, exp_version, _ = run_axiom0(axiom0, ["version"], expect_rc=0)
    _, exp_features, _ = run_axiom0(axiom0, ["--features"], expect_rc=0)
    _, exp_help, _ = run_axiom0(axiom0, ["help"], expect_rc=0)
    _, _, exp_check_err = run_axiom0(axiom0, ["check", "--std-root=tests/driver", "tests/driver/error.ax"], expect_rc=1)
    _, _, exp_json_err = run_axiom0(axiom0, ["check", "--std-root=tests/driver", "--json", "tests/driver/error.ax"], expect_rc=1)

    blobs = [
        b"axiom0",                           # 0
        b"version",                          # 1
        b"--features",                       # 2
        b"help",                             # 3
        b"check",                            # 4
        b"run",                              # 5
        b"--json",                           # 6
        b"--time-passes",                    # 7
        b"--interp",                         # 8
        b"-O1",                              # 9
        b"tests/driver/test.ax",             # 10
        b"tests/driver/error.ax",            # 11
        b"tests/lir/const.mir",              # 12
        b"--std-root=tests/driver",          # 13
        b"tests/opt/const_fold_run.ax",      # 14
        exp_version,                         # 15
        exp_features,                        # 16
        exp_help,                            # 17
        exp_check_err,                       # 18
        exp_json_err,                        # 19
        b"time: source    ",                 # 20
        b"time: lex       ",                 # 21
        b"time: parse     ",                 # 22
        b"time: resolve   ",                 # 23
        b"time: hir       ",                 # 24
        b"time: typeck    ",                 # 25
        b"time: own       ",                 # 26
    ]
    blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_commands_a_test

use host_intrinsics.heap_alloc
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_DIAG
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.driver.pipeline.driver_run_args

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

fn blob_sv(idx: usize) -> StrView {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    unsafe { *(buf + blen) = 0u8; }
    StrView {
        ptr: buf as *const u8,
        len: blen,
    }
}

fn alloc_argv(cap: usize) -> *mut StrView {
    let bytes = opts_mul_usize(cap, 16);
    unsafe { heap_alloc(bytes, 8) as *mut StrView }
}

fn set_arg_blob(argv: *mut StrView, idx: usize, blob_idx: usize) {
    let s = blob_sv(blob_idx);
    sv_slot_set(argv, idx, view(s));
}

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn buf_contains_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let n_len = BLOB_LENS[blob_idx];
    let b_len = buf.len;
    if n_len == 0 { return true; }
    if b_len < n_len { return false; }
    let mut i: usize = 0;
    while i + n_len <= b_len {
        let mut match_ok = true;
        let mut j: usize = 0;
        while j < n_len {
            let b = unsafe { *(buf.ptr + i + j) };
            if b != BLOBS[off + j] {
                match_ok = false;
                break;
            }
            j = j + 1;
        }
        if match_ok {
            return true;
        }
        i = i + 1;
    }
    false
}

pub fn main() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;
    set_arg_blob(argv, 0, 0);

    // 1. version
    set_arg_blob(argv, 1, 1);
    let mut out1 = diag_buf_new();
    let mut err1 = diag_buf_new();
    let rc1 = driver_run_args(ap, 2, mut_view(out1), mut_view(err1));
    let ok1 = rc1 == AX_EXIT_OK && buf_matches_blob(view(out1), 15) && err1.len == 0;
    diag_buf_free(mut_view(out1));
    diag_buf_free(mut_view(err1));
    if !ok1 { return 10; }

    // 2. --features
    set_arg_blob(argv, 1, 2);
    let mut out2 = diag_buf_new();
    let mut err2 = diag_buf_new();
    let rc2 = driver_run_args(ap, 2, mut_view(out2), mut_view(err2));
    let ok2 = rc2 == AX_EXIT_OK && buf_matches_blob(view(out2), 16) && err2.len == 0;
    diag_buf_free(mut_view(out2));
    diag_buf_free(mut_view(err2));
    if !ok2 { return 11; }

    // 3. help
    set_arg_blob(argv, 1, 3);
    let mut out3 = diag_buf_new();
    let mut err3 = diag_buf_new();
    let rc3 = driver_run_args(ap, 2, mut_view(out3), mut_view(err3));
    let ok3 = rc3 == AX_EXIT_OK && buf_matches_blob(view(out3), 17) && err3.len == 0;
    diag_buf_free(mut_view(out3));
    diag_buf_free(mut_view(err3));
    if !ok3 { return 12; }

    // 4. check --std-root=tests/driver --time-passes tests/driver/test.ax -> ok + timing lines
    set_arg_blob(argv, 1, 4);
    set_arg_blob(argv, 2, 13);
    set_arg_blob(argv, 3, 7);
    set_arg_blob(argv, 4, 10);
    let mut out4 = diag_buf_new();
    let mut err4 = diag_buf_new();
    let rc4 = driver_run_args(ap, 5, mut_view(out4), mut_view(err4));
    let ok4 = rc4 == AX_EXIT_OK &&
        err4.len == 0 &&
        buf_contains_blob(view(out4), 20) &&
        buf_contains_blob(view(out4), 21) &&
        buf_contains_blob(view(out4), 22) &&
        buf_contains_blob(view(out4), 23) &&
        buf_contains_blob(view(out4), 24) &&
        buf_contains_blob(view(out4), 25) &&
        buf_contains_blob(view(out4), 26);
    diag_buf_free(mut_view(out4));
    diag_buf_free(mut_view(err4));
    if !ok4 { return 13; }

    // 5. check --std-root=tests/driver tests/driver/error.ax -> human error matches axiom0 byte-for-byte
    set_arg_blob(argv, 1, 4);
    set_arg_blob(argv, 2, 13);
    set_arg_blob(argv, 3, 11);
    let mut out5 = diag_buf_new();
    let mut err5 = diag_buf_new();
    let rc5 = driver_run_args(ap, 4, mut_view(out5), mut_view(err5));
    let ok5 = rc5 == AX_EXIT_DIAG && out5.len == 0 && buf_matches_blob(view(err5), 18);
    diag_buf_free(mut_view(out5));
    diag_buf_free(mut_view(err5));
    if !ok5 { return 14; }

    // 6. check --std-root=tests/driver --json tests/driver/error.ax -> JSON error matches axiom0 byte-for-byte
    set_arg_blob(argv, 1, 4);
    set_arg_blob(argv, 2, 13);
    set_arg_blob(argv, 3, 6);
    set_arg_blob(argv, 4, 11);
    let mut out6 = diag_buf_new();
    let mut err6 = diag_buf_new();
    let rc6 = driver_run_args(ap, 5, mut_view(out6), mut_view(err6));
    let ok6 = rc6 == AX_EXIT_DIAG && out6.len == 0 && buf_matches_blob(view(err6), 19);
    diag_buf_free(mut_view(out6));
    diag_buf_free(mut_view(err6));
    if !ok6 { return 15; }

    // 7. run tests/lir/const.mir (standalone .mir verification + execution returns 42)
    set_arg_blob(argv, 1, 5);
    set_arg_blob(argv, 2, 12);
    let mut out7 = diag_buf_new();
    let mut err7 = diag_buf_new();
    let rc7 = driver_run_args(ap, 3, mut_view(out7), mut_view(err7));
    let ok7 = rc7 == 42 && err7.len == 0;
    diag_buf_free(mut_view(out7));
    diag_buf_free(mut_view(err7));
    if !ok7 { return 16; }

    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(blobs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: interp native\n\n"
    full_text = header + prelude + "\n" + full_mods + "\n" + main_src
    write_bytes(os.path.join(HERE, "qa_driver_commands_a.ax"), full_text.encode("utf-8"))


def gen_commands_b_bundle(prelude, full_mods, axiom0):
    # Precompute reference COFF .obj and PE32+ .exe outputs from axiom0 build
    tmp_obj = os.path.join(HERE, "_gen_tmp_ret42.obj")
    tmp_exe = os.path.join(HERE, "_gen_tmp_ret42.exe")
    tmp_exe_sr = os.path.join(HERE, "_gen_tmp_ret42_sr.exe")
    tmp_exe_pkg = os.path.join(HERE, "_gen_tmp_hello.exe")
    try:
        run_axiom0(axiom0, ["build", "--emit=obj", "-o", tmp_obj, "tests/mc/frame/main_42.ax"], expect_rc=0)
        exp_obj = read_bytes(tmp_obj)
        run_axiom0(axiom0, ["build", "-o", tmp_exe, "tests/mc/frame/main_42.ax"], expect_rc=0)
        exp_exe = read_bytes(tmp_exe)
        run_axiom0(axiom0, ["build", "--stack-reserve=2097152", "-o", tmp_exe_sr, "tests/mc/frame/main_42.ax"], expect_rc=0)
        exp_exe_sr = read_bytes(tmp_exe_sr)
        run_axiom0(axiom0, ["build", "-o", tmp_exe_pkg, "tests/modules/hello/src/main.ax"], expect_rc=0)
        exp_exe_pkg = read_bytes(tmp_exe_pkg)
    finally:
        for p in (tmp_obj, tmp_exe, tmp_exe_sr, tmp_exe_pkg):
            if os.path.exists(p):
                os.remove(p)

    blobs = [
        b"axiom0",                                     # 0
        b"check",                                      # 1
        b"run",                                        # 2
        b"build",                                      # 3
        b"--emit=obj",                                 # 4
        b"-o",                                         # 5
        b"out_mem.obj",                                # 6
        b"out_mem.exe",                                # 7
        b"--stack-reserve=2097152",                    # 8
        b"tests/mc/frame/main_42.ax",                  # 9
        b"tests/modules/hello/src/main.ax",            # 10
        b"tests/modules/mutual/src/main.ax",           # 11
        b"tests/modules/nested/src/main.ax",           # 12
        b"tests/modules/prelude_implicit/src/main.ax", # 13
        b"tests/modules/reexport/src/main.ax",         # 14
        b"tests/lir/add.mir",                          # 15: uninitialized local -> check/run rc 1
        exp_obj,                                       # 16
        exp_exe,                                       # 17
        exp_exe_sr,                                    # 18
        exp_exe_pkg,                                   # 19
        b"build/tmp_driver_test_",                     # 20
        b".exe",                                       # 21
        b"--interp",                                   # 22
        b"-O1",                                        # 23
        b"tests/opt/const_fold_run.ax",                # 24
        b"tests/driver/test.ax",                       # 25
        b"tests/lir/const.mir",                        # 26
    ]
    blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_commands_b_test

use host_intrinsics.heap_alloc
use host_intrinsics.file_size
use host_intrinsics.monotonic_ns
use host_intrinsics.open
use host_intrinsics.close
use host_intrinsics.remove
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.diag.format.diag_buf_push_bytes
use compiler.diag.format.diag_buf_push_u32
use compiler.obj.coff.CoffBuf
use compiler.obj.coff.coff_buf_with_capacity
use compiler.obj.coff.coff_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_DIAG
use compiler.driver.opts.DriverOptions
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.driver.opts.driver_options_alloc
use compiler.driver.opts.driver_options_dealloc
use compiler.driver.opts.driver_parse_cli
use compiler.driver.pipeline.driver_run_args
use compiler.driver.pipeline.driver_execute_build_into

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

unsafe fn ptr_from_mut<T>(v: mut_view<T>) -> *mut T {
    address_of_mut(*v)
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

fn blob_sv(idx: usize) -> StrView {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    unsafe { *(buf + blen) = 0u8; }
    StrView {
        ptr: buf as *const u8,
        len: blen,
    }
}

fn alloc_argv(cap: usize) -> *mut StrView {
    let bytes = opts_mul_usize(cap, 16);
    unsafe { heap_alloc(bytes, 8) as *mut StrView }
}

fn set_arg_blob(argv: *mut StrView, idx: usize, blob_idx: usize) {
    let s = blob_sv(blob_idx);
    sv_slot_set(argv, idx, view(s));
}

fn coff_buf_matches_blob(cb: view<CoffBuf>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if cb.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(cb.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn test_packages_and_mir_errors() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;
    let exp_rcs: [5]i32 = [42, 30, 84, 1, 7];

    // Check and run all 5 multi-file module packages (blobs 10..14)
    let mut pkg_idx: usize = 10;
    while pkg_idx <= 14 {
        set_arg_blob(argv, 0, 0);
        set_arg_blob(argv, 1, 1);
        set_arg_blob(argv, 2, pkg_idx);
        let mut out_c = diag_buf_new();
        let mut err_c = diag_buf_new();
        let rcc = driver_run_args(ap, 3, mut_view(out_c), mut_view(err_c));
        let okc = rcc == AX_EXIT_OK && err_c.len == 0;
        diag_buf_free(mut_view(out_c));
        diag_buf_free(mut_view(err_c));
        if !okc {
            return (10 + (pkg_idx - 10)) as i32;
        }

        set_arg_blob(argv, 0, 0);
        set_arg_blob(argv, 1, 2);
        set_arg_blob(argv, 2, pkg_idx);
        let mut out_b = diag_buf_new();
        let mut err_b = diag_buf_new();
        let rc = driver_run_args(ap, 3, mut_view(out_b), mut_view(err_b));
        let exp_rc = exp_rcs[pkg_idx - 10];
        let ok = rc == exp_rc && err_b.len == 0;
        diag_buf_free(mut_view(out_b));
        diag_buf_free(mut_view(err_b));
        if !ok {
            return (30 + (pkg_idx - 10)) as i32;
        }
        pkg_idx = pkg_idx + 1;
    }

    // Full-std check tests/driver/test.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 25);
    let mut out_t = diag_buf_new();
    let mut err_t = diag_buf_new();
    let rct = driver_run_args(ap, 3, mut_view(out_t), mut_view(err_t));
    let okt = rct == AX_EXIT_OK && out_t.len == 0 && err_t.len == 0;
    diag_buf_free(mut_view(out_t));
    diag_buf_free(mut_view(err_t));
    if !okt { return 15; }

    // Standalone .mir check tests/lir/const.mir
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 26);
    let mut out_cm = diag_buf_new();
    let mut err_cm = diag_buf_new();
    let rccm = driver_run_args(ap, 3, mut_view(out_cm), mut_view(err_cm));
    let okcm = rccm == AX_EXIT_OK && err_cm.len == 0;
    diag_buf_free(mut_view(out_cm));
    diag_buf_free(mut_view(err_cm));
    if !okcm { return 16; }

    // Full-std run --interp -O1 tests/opt/const_fold_run.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 2);
    set_arg_blob(argv, 2, 22);
    set_arg_blob(argv, 3, 23);
    set_arg_blob(argv, 4, 24);
    let mut out_cf = diag_buf_new();
    let mut err_cf = diag_buf_new();
    let rccf = driver_run_args(ap, 5, mut_view(out_cf), mut_view(err_cf));
    let okcf = rccf == AX_EXIT_OK && err_cf.len == 0;
    diag_buf_free(mut_view(out_cf));
    diag_buf_free(mut_view(err_cf));
    if !okcf { return 17; }

    // Negative check on uninitialized .mir (tests/lir/add.mir) -> AX_EXIT_DIAG
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 15);
    let mut out_m = diag_buf_new();
    let mut err_m = diag_buf_new();
    let rcm = driver_run_args(ap, 3, mut_view(out_m), mut_view(err_m));
    let okm = rcm == AX_EXIT_DIAG && err_m.len > 0;
    diag_buf_free(mut_view(out_m));
    diag_buf_free(mut_view(err_m));
    if !okm { return 18; }
    0
}

fn run_build_into_check(argv: *const StrView, argc: usize, exp_blob_idx: usize) -> bool {
    let dopts = unsafe { driver_options_alloc() };
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let prc = unsafe { driver_parse_cli(argv, argc, mut_view(*dopts), mut_view(out_b), mut_view(err_b)) };
    if prc != AX_EXIT_OK {
        diag_buf_free(mut_view(out_b));
        diag_buf_free(mut_view(err_b));
        unsafe { driver_options_dealloc(dopts); }
        return false;
    }
    let mut bin_buf = coff_buf_with_capacity(1024);
    let bin_ptr = unsafe { ptr_from_mut(mut_view(bin_buf)) };
    let brc = unsafe {
        driver_execute_build_into(
            view(*dopts),
            mut_view(out_b),
            mut_view(err_b),
            bin_ptr,
            false
        )
    };
    let ok = brc == AX_EXIT_OK && err_b.len == 0 && coff_buf_matches_blob(view(bin_buf), exp_blob_idx);
    coff_buf_free(mut_view(bin_buf));
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

fn test_build_pipeline() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;

    // 1. build --emit=obj -o out_mem.obj tests/mc/frame/main_42.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 4);
    set_arg_blob(argv, 3, 5);
    set_arg_blob(argv, 4, 6);
    set_arg_blob(argv, 5, 9);
    if !run_build_into_check(ap, 6, 16) { return 20; }

    // 2. build -o out_mem.exe tests/mc/frame/main_42.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 5);
    set_arg_blob(argv, 3, 7);
    set_arg_blob(argv, 4, 9);
    if !run_build_into_check(ap, 5, 17) { return 21; }

    // 3. build --stack-reserve=2097152 -o out_mem.exe tests/mc/frame/main_42.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 8);
    set_arg_blob(argv, 3, 5);
    set_arg_blob(argv, 4, 7);
    set_arg_blob(argv, 5, 9);
    if !run_build_into_check(ap, 6, 18) { return 22; }

    // 4. build -o out_mem.exe tests/modules/hello/src/main.ax (multi-file package native build)
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 5);
    set_arg_blob(argv, 3, 7);
    set_arg_blob(argv, 4, 10);
    if !run_build_into_check(ap, 5, 19) { return 23; }

    // 5. Real disk output via driver_run_args with unique monotonic_ns filename + cleanup
    let mut path_buf = diag_buf_new();
    let pfx = blob_sv(20);
    let sfx = blob_sv(21);
    diag_buf_push_bytes(mut_view(path_buf), pfx.ptr, pfx.len);
    let stamp = (monotonic_ns() & 0xFFFFFFFFu64) as u32;
    diag_buf_push_u32(mut_view(path_buf), stamp);
    diag_buf_push_bytes(mut_view(path_buf), sfx.ptr, sfx.len);
    let tmp_sv = StrView { ptr: path_buf.ptr as *const u8, len: path_buf.len };

    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 5);
    sv_slot_set(argv, 3, view(tmp_sv));
    set_arg_blob(argv, 4, 9);
    let mut out_d = diag_buf_new();
    let mut err_d = diag_buf_new();
    let drc = driver_run_args(ap, 5, mut_view(out_d), mut_view(err_d));
    let mut disk_ok = drc == AX_EXIT_OK && err_d.len == 0;
    if disk_ok {
        let fd = unsafe { open(tmp_sv.ptr, tmp_sv.len, 0u32) };
        if fd < 0i64 {
            disk_ok = false;
        } else {
            let fsz = file_size(fd);
            let _ = close(fd);
            if (fsz as usize) != BLOB_LENS[17] {
                disk_ok = false;
            }
        }
        let _ = unsafe { remove(tmp_sv.ptr, tmp_sv.len) };
    }
    diag_buf_free(mut_view(out_d));
    diag_buf_free(mut_view(err_d));
    diag_buf_free(mut_view(path_buf));
    if !disk_ok { return 24; }

    0
}

pub fn main() -> i32 {
    let r1 = test_packages_and_mir_errors();
    if r1 != 0 { return r1; }
    let r2 = test_build_pipeline();
    if r2 != 0 { return r2; }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(blobs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: native\n\n"
    full_text = header + prelude + "\n" + full_mods + "\n" + main_src
    write_bytes(os.path.join(HERE, "qa_driver_commands_b.ax"), full_text.encode("utf-8"))


def gen_boundary_edges_bundle(prelude, light_mods, axiom0):
    _, _, exp_ver_extra = run_axiom0(axiom0, ["version", "extra_arg"], expect_rc=2)
    _, _, exp_feat_extra = run_axiom0(axiom0, ["--features", "--all"], expect_rc=2)
    _, _, exp_emit_empty = run_axiom0(axiom0, ["inspect", "--emit=", "tests/driver/test.ax"], expect_rc=2)
    _, _, exp_inspect_two = run_axiom0(
        axiom0,
        ["inspect", "--emit=ast", "tests/driver/test.ax", "tests/driver/error.ax"],
        expect_rc=2,
    )

    blobs = [
        exp_ver_extra,                                                 # 0
        exp_feat_extra,                                                # 1
        exp_emit_empty,                                                # 2
        exp_inspect_two,                                               # 3
        b"axiom0: unknown target 'x86_64-unknown-linux-gnu' [AX_DRIVER_UNKNOWN_TARGET]\n",  # 4
        b"axiom0",                                                     # 5
        b"version",                                                    # 6
        b"extra_arg",                                                  # 7
        b"--features",                                                 # 8
        b"--all",                                                      # 9
        b"inspect",                                                    # 10
        b"--emit=",                                                    # 11
        b"--emit=ast",                                                 # 12
        b"tests/driver/test.ax",                                       # 13
        b"tests/driver/error.ax",                                      # 14
        b"check",                                                      # 15
        b"--target=x86_64-unknown-linux-gnu",                          # 16
        b"run",                                                        # 17
        b"--",                                                         # 18
        b"-O1",                                                        # 19
        b"--json",                                                     # 20
        b"--unknown-opt",                                              # 21
        b"src\\nested\\dir\\item.ax",                                  # 22
        b"nested.dir.item",                                            # 23
        b"standalone.ax",                                              # 24
        b"standalone",                                                 # 25
        b"nonexistent_input_file_xyz.ax",                              # 26
        b"nonexistent_std_dir_xyz",                                    # 27
        b"tests/modules/hello",                                        # 28
        b"hello",                                                      # 29
    ]
    blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_boundary_edges_test

use host_intrinsics.heap_alloc
use host_intrinsics.heap_free
use compiler.kernel.arena.Arena
use compiler.kernel.arena.arena_new
use compiler.kernel.arena.arena_destroy
use compiler.kernel.interner.StrView
use compiler.diag.code.AX_IO_FILE_NOT_FOUND
use compiler.diag.code.AX_DRIVER_NO_STD
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.diag_sink_init
use compiler.diag.emitter.diag_sink_free
use compiler.diag.emitter.diag_sink_error_count
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_USAGE
use compiler.driver.opts.CMD_RUN
use compiler.driver.opts.DriverOptions
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_get
use compiler.driver.opts.sv_slot_set
use compiler.driver.opts.driver_options_alloc
use compiler.driver.opts.driver_options_dealloc
use compiler.driver.opts.driver_parse_cli
use compiler.driver.opts.derive_module_path
use compiler.driver.opts.Project
use compiler.driver.opts.project_alloc
use compiler.driver.opts.project_dealloc
use compiler.driver.opts.project_discover

@intrinsic fn size_of<T>() -> usize { 0 }
@intrinsic fn align_of<T>() -> usize { 0 }

unsafe fn diag_sink_alloc() -> *mut DiagSink {
    let bytes = size_of<DiagSink>();
    let raw = heap_alloc(bytes, align_of<DiagSink>());
    let mut i: usize = 0;
    while i < bytes {
        *(raw + i) = 0u8;
        i = i + 1;
    }
    let p = raw as *mut DiagSink;
    diag_sink_init(mut_view(*p));
    p
}

unsafe fn diag_sink_dealloc(p: *mut DiagSink) {
    if (p as usize) == 0 { return; }
    diag_sink_free(mut_view(*p));
    heap_free(p as *mut u8, size_of<DiagSink>(), align_of<DiagSink>());
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

fn blob_sv(idx: usize) -> StrView {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    unsafe { *(buf + blen) = 0u8; }
    StrView {
        ptr: buf as *const u8,
        len: blen,
    }
}

fn alloc_argv(cap: usize) -> *mut StrView {
    let bytes = opts_mul_usize(cap, 16);
    unsafe { heap_alloc(bytes, 8) as *mut StrView }
}

fn set_arg_blob(argv: *mut StrView, idx: usize, blob_idx: usize) {
    let s = blob_sv(blob_idx);
    sv_slot_set(argv, idx, view(s));
}

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn sv_matches_blob(sv: view<StrView>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if sv.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(sv.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn check_err_case(argv: *const StrView, argc: usize, exp_rc: i32, exp_err_blob: usize) -> bool {
    let dopts = unsafe { driver_options_alloc() };
    let mut out_buf = diag_buf_new();
    let mut err_buf = diag_buf_new();
    let rc = unsafe { driver_parse_cli(argv, argc, mut_view(*dopts), mut_view(out_buf), mut_view(err_buf)) };
    let ok = rc == exp_rc && out_buf.len == 0 && buf_matches_blob(view(err_buf), exp_err_blob);
    diag_buf_free(mut_view(out_buf));
    diag_buf_free(mut_view(err_buf));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

fn test_cli_edge_cases() -> i32 {
    let a = alloc_argv(10);
    let ap = a as *const StrView;
    set_arg_blob(a, 0, 5); // "axiom0"

    // 1. `axiom0 version extra_arg` -> AX_EXIT_USAGE + exact stderr
    set_arg_blob(a, 1, 6);
    set_arg_blob(a, 2, 7);
    if !check_err_case(ap, 3, AX_EXIT_USAGE, 0) { return 10; }

    // 2. `axiom0 --features --all` -> AX_EXIT_USAGE + exact stderr
    set_arg_blob(a, 1, 8);
    set_arg_blob(a, 2, 9);
    if !check_err_case(ap, 3, AX_EXIT_USAGE, 1) { return 11; }

    // 3. `axiom0 inspect --emit= tests/driver/test.ax` -> AX_EXIT_USAGE + emitters list
    set_arg_blob(a, 1, 10);
    set_arg_blob(a, 2, 11);
    set_arg_blob(a, 3, 13);
    if !check_err_case(ap, 4, AX_EXIT_USAGE, 2) { return 12; }

    // 4. `axiom0 inspect --emit=ast tests/driver/test.ax tests/driver/error.ax` -> AX_EXIT_USAGE
    set_arg_blob(a, 1, 10);
    set_arg_blob(a, 2, 12);
    set_arg_blob(a, 3, 13);
    set_arg_blob(a, 4, 14);
    if !check_err_case(ap, 5, AX_EXIT_USAGE, 3) { return 13; }

    // 5. `axiom0 check --target=x86_64-unknown-linux-gnu tests/driver/test.ax` -> exact target error
    set_arg_blob(a, 1, 15);
    set_arg_blob(a, 2, 16);
    set_arg_blob(a, 3, 13);
    if !check_err_case(ap, 4, AX_EXIT_USAGE, 4) { return 14; }

    // 6. `axiom0 run tests/driver/test.ax -- -O1 --json --unknown-opt`
    // Flags after `--` must not be parsed as compiler options; they must land in `run_args`.
    set_arg_blob(a, 1, 17);
    set_arg_blob(a, 2, 13);
    set_arg_blob(a, 3, 18);
    set_arg_blob(a, 4, 19);
    set_arg_blob(a, 5, 20);
    set_arg_blob(a, 6, 21);
    let dopts = unsafe { driver_options_alloc() };
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let rc = unsafe { driver_parse_cli(ap, 7, mut_view(*dopts), mut_view(out_b), mut_view(err_b)) };
    let mut dash_ok = unsafe {
        rc == AX_EXIT_OK &&
        (*dopts).cmd == CMD_RUN &&
        !(*dopts).opt_O1 &&
        !(*dopts).json &&
        (*dopts).dash_dash &&
        (*dopts).run_argc == 3 &&
        err_b.len == 0
    };
    if dash_ok {
        let r0 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 0) };
        let r1 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 1) };
        let r2 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 2) };
        if !sv_matches_blob(view(r0), 19) || !sv_matches_blob(view(r1), 20) || !sv_matches_blob(view(r2), 21) {
            dash_ok = false;
        }
    }
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    if !dash_ok { return 15; }
    0
}

fn test_path_and_discovery_seams() -> i32 {
    let mut arena = arena_new();

    // 1. Backslash path in derive_module_path: `src\\nested\\dir\\item.ax` -> `nested.dir.item`
    let b22 = blob_sv(22);
    let mp_win = derive_module_path(view(b22), mut_view(arena));
    if !sv_matches_blob(view(mp_win), 23) {
        arena_destroy(mut_view(arena));
        return 20;
    }

    // 2. Standalone filename without `src/`: `standalone.ax` -> `standalone`
    let b24 = blob_sv(24);
    let mp_root = derive_module_path(view(b24), mut_view(arena));
    if !sv_matches_blob(view(mp_root), 25) {
        arena_destroy(mut_view(arena));
        return 21;
    }
    arena_destroy(mut_view(arena));

    let empty = StrView { ptr: 0 as *const u8, len: 0 };

    // 3. project_discover with nonexistent input file -> AX_IO_FILE_NOT_FOUND
    let sink1 = unsafe { diag_sink_alloc() };
    let p1 = unsafe { project_alloc() };
    let b26 = blob_sv(26);
    let ok1 = unsafe { project_discover(view(b26), view(empty), mut_view(*p1), mut_view(*sink1)) };
    let mut err1_ok = unsafe { !ok1 && diag_sink_error_count(view(*sink1)) == 1 };
    if err1_ok {
        let d0_code = unsafe { (*(*sink1).diags).code.v };
        if d0_code != AX_IO_FILE_NOT_FOUND {
            err1_ok = false;
        }
    }
    unsafe {
        project_dealloc(p1);
        diag_sink_dealloc(sink1);
    }
    if !err1_ok { return 22; }

    // 4. project_discover with nonexistent explicit `--std-root` -> AX_DRIVER_NO_STD
    let sink2 = unsafe { diag_sink_alloc() };
    let p2 = unsafe { project_alloc() };
    let b13 = blob_sv(13);
    let b27 = blob_sv(27);
    let ok2 = unsafe { project_discover(view(b13), view(b27), mut_view(*p2), mut_view(*sink2)) };
    let mut err2_ok = unsafe { !ok2 && diag_sink_error_count(view(*sink2)) == 1 };
    if err2_ok {
        let d0_code = unsafe { (*(*sink2).diags).code.v };
        if d0_code != AX_DRIVER_NO_STD {
            err2_ok = false;
        }
    }
    unsafe {
        project_dealloc(p2);
        diag_sink_dealloc(sink2);
    }
    if !err2_ok { return 23; }

    // 5. project_discover when given package root directory directly (`tests/modules/hello`)
    let sink3 = unsafe { diag_sink_alloc() };
    let p3 = unsafe { project_alloc() };
    let b28 = blob_sv(28);
    let ok3 = unsafe { project_discover(view(b28), view(empty), mut_view(*p3), mut_view(*sink3)) };
    let dir_ok = unsafe {
        ok3 &&
        (*p3).is_package &&
        (*p3).has_manifest &&
        sv_matches_blob(view((*p3).manifest.name), 29) &&
        (*p3).file_count == 5 &&
        diag_sink_error_count(view(*sink3)) == 0
    };
    unsafe {
        project_dealloc(p3);
        diag_sink_dealloc(sink3);
    }
    if !dir_ok { return 24; }

    0
}

pub fn main() -> i32 {
    let r1 = test_cli_edge_cases();
    if r1 != 0 { return r1; }
    let r2 = test_path_and_discovery_seams();
    if r2 != 0 { return r2; }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(blobs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: interp native\n\n"
    full_text = header + prelude + "\n" + light_mods + "\n" + main_src
    write_bytes(os.path.join(HERE, "qa_driver_boundary_edges.ax"), full_text.encode("utf-8"))


def main():
    axiom0 = find_exe(["build/axiom0.exe", "build/axiom0"])
    for i, a in enumerate(sys.argv[1:]):
        if a == "--axiom0" and i + 2 <= len(sys.argv[1:]):
            axiom0 = sys.argv[i + 2]
    if not axiom0 or not os.path.isfile(axiom0):
        raise SystemExit("Could not find axiom0 binary; pass --axiom0 <path>")

    prelude = build_prelude_text()
    light_mods = assemble_modules(LIGHT_MODULES)
    full_mods = assemble_modules(FULL_MODULES)

    gen_cli_and_project_bundle(prelude, light_mods, axiom0)
    gen_boundary_edges_bundle(prelude, light_mods, axiom0)

    inspect_cases_a = [
        ("--emit=tokens", False, "tests/driver/test.ax"),
        ("--emit=ast", False, "tests/driver/test.ax"),
        ("--emit=resolved", False, "tests/driver/test.ax"),
        ("--emit=hir", False, "tests/driver/test.ax"),
        ("--emit=thir", False, "tests/driver/test.ax"),
        ("--emit=mir", False, "tests/driver/test.ax"),
        ("--emit=mir-opt", True, "tests/driver/test.ax"),
        ("--emit=mir", False, "tests/lir/const.mir"),
    ]
    gen_inspect_diff_bundle(
        "qa_driver_inspect_diff_a.ax",
        "interp native",
        prelude,
        full_mods,
        axiom0,
        inspect_cases_a,
        fast_std=True,
    )

    inspect_cases_b = [
        ("--emit=tokens", False, "tests/mc/frame/main_42.ax"),
        ("--emit=ast", False, "tests/mc/frame/main_42.ax"),
        ("--emit=resolved", False, "tests/mc/frame/main_42.ax"),
        ("--emit=hir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=thir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=mir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=lir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=mi", False, "tests/mc/frame/main_42.ax"),
        ("--emit=mc", False, "tests/mc/frame/main_42.ax"),
        ("--emit=obj", False, "tests/mc/frame/main_42.ax"),
        ("--emit=lir", False, "tests/lir/const.mir"),
        ("--emit=mi", False, "tests/lir/const.mir"),
        ("--emit=mc", False, "tests/lir/const.mir"),
        ("--emit=hir", False, "tests/modules/hello/src/main.ax"),
    ]
    gen_inspect_diff_bundle(
        "qa_driver_inspect_diff_b.ax",
        "native",
        prelude,
        full_mods,
        axiom0,
        inspect_cases_b,
        fast_std=False,
    )

    gen_commands_a_bundle(prelude, full_mods, axiom0)
    gen_commands_b_bundle(prelude, full_mods, axiom0)
    print("Generated 6 selfhost driver test bundles in %s" % HERE)


if __name__ == "__main__":
    main()

