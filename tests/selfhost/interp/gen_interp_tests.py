#!/usr/bin/env python3
"""Bundler for selfhost MIR interpreter unit and differential tests (T083a).

Combines the lightweight compiler data model and MIR modules with compiler/interp/*
plus each test harness main module into standalone selfhost test files in
tests/selfhost/interp/.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

REFERENCE_BUNDLE = "tests/selfhost/mir/qa_mir_builder_and_drop_a.ax"

UNIT_MODULES = [
    ("compiler.kernel.id", "reference"),
    ("compiler.kernel.hash", "reference"),
    ("compiler.kernel.arena", "reference"),
    ("compiler.kernel.interner", "reference"),
    ("compiler.source.span", "reference"),
    ("compiler.source.manager", "reference"),
    ("compiler.diag.code", "reference"),
    ("compiler.diag.emitter", "reference"),
    ("compiler.diag.format", "reference"),
    ("compiler.lex.token", "reference"),
    ("compiler.syntax.ast", "reference"),
    ("compiler.resolve.symtab", "reference"),
    ("compiler.hir.hir", "reference"),
    ("compiler.types.types", "reference"),
    ("compiler.types.layout", "reference"),
    ("compiler.traits.solver", "reference"),
    ("compiler.traits.mono", "reference"),
    ("compiler.mir.mir", "reference"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.mir.builder", "compiler"),
    ("compiler.mir", "compiler"),
    ("compiler.interp.value", "compiler"),
    ("compiler.interp.oracle", "compiler"),
    ("compiler.interp.frame", "compiler"),
    ("compiler.interp.interp", "compiler"),
    ("compiler.interp", "compiler"),
]

STD_SYS_WINDOWS_FILES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/io.ax",
    "std/sys/windows/fs.ax",
    "std/sys/windows/process.ax",
    "std/sys/windows/time.ax",
]


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
    if "compiler.kernel.id" in sections:
        id_src = sections["compiler.kernel.id"]
        cut = id_src.find("// RawIdTable")
        if cut != -1:
            id_src = id_src[:cut]
        for unused_line in (
            "    pub fn from_index(index: usize) -> StrId { StrId { v: (index + 1) as u32 } }\n",
            "    pub fn index(self: view<StrId>) -> usize { (self.v - 1) as usize }\n",
            "    pub fn to_raw(self: view<StrId>) -> u32 { self.v }\n",
            "    pub fn from_raw(v: u32) -> StrId { StrId { v: v } }\n",
            "    pub fn from_index(index: usize) -> FileId { FileId { v: (index + 1) as u32 } }\n",
            "    pub fn index(self: view<FileId>) -> usize { (self.v - 1) as usize }\n",
            "    pub fn to_raw(self: view<FileId>) -> u32 { self.v }\n",
            "    pub fn from_raw(v: u32) -> FileId { FileId { v: v } }\n",
            "    pub fn from_index(index: usize) -> NodeId { NodeId { v: (index + 1) as u32 } }\n",
            "    pub fn index(self: view<NodeId>) -> usize { (self.v - 1) as usize }\n",
            "    pub fn to_raw(self: view<NodeId>) -> u32 { self.v }\n",
            "    pub fn from_raw(v: u32) -> NodeId { NodeId { v: v } }\n",
            "    pub fn from_index(index: usize) -> SymbolId { SymbolId { v: (index + 1) as u32 } }\n",
            "    pub fn index(self: view<SymbolId>) -> usize { (self.v - 1) as usize }\n",
            "    pub fn to_raw(self: view<SymbolId>) -> u32 { self.v }\n",
            "    pub fn from_raw(v: u32) -> SymbolId { SymbolId { v: v } }\n",
            "    pub fn from_index(index: usize) -> TypeId { TypeId { v: (index + 1) as u32 } }\n",
            "    pub fn index(self: view<TypeId>) -> usize { (self.v - 1) as usize }\n",
            "    pub fn to_raw(self: view<TypeId>) -> u32 { self.v }\n",
            "    pub fn from_raw(v: u32) -> TypeId { TypeId { v: v } }\n",
        ):
            id_src = id_src.replace(unused_line, "")
        sections["compiler.kernel.id"] = id_src
    if "compiler.kernel.hash" in sections:
        hash_src = sections["compiler.kernel.hash"]
        hash_src = hash_src.replace(
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
        sections["compiler.kernel.hash"] = hash_src
    if "compiler.kernel.interner" in sections:
        in_src = sections["compiler.kernel.interner"]
        cut = in_src.find("fn u32_interner_grow_map(")
        if cut != -1:
            sections["compiler.kernel.interner"] = in_src[:cut]
    if "compiler.source.manager" in sections:
        sm_src = sections["compiler.source.manager"]
        u1 = sm_src.find("fn utf8_count_scalars(")
        u2 = sm_src.find("pub struct SourceFile {")
        if u1 != -1 and u2 != -1:
            sm_src = sm_src[:u1] + "fn utf8_validate(bytes: *const u8, byte_len: usize) -> bool { true }\n\n" + sm_src[u2:]
        l1 = sm_src.find("pub fn source_db_line_col(")
        if l1 != -1:
            sm_src = (
                sm_src[:l1]
                + "pub fn source_db_line_col(db: view<SourceDatabase>, span: Span) -> LineCol { LineCol.zero() }\n"
                + "pub fn source_db_line_range(db: view<SourceDatabase>, file: FileId, line: u32) -> Span { span_none() }\n"
            )
        sections["compiler.source.manager"] = sm_src
    if "compiler.diag.emitter" in sections:
        em_src = sections["compiler.diag.emitter"]
        c1 = em_src.find("    // Deep copy notes")
        c2 = em_src.find("    let sev = d.severity;")
        if c1 != -1 and c2 != -1:
            em_src = em_src[:c1] + em_src[c2:]
        s1 = em_src.find("fn diag_less(")
        s2 = em_src.find("pub fn diag_sink_has_errors(")
        if s1 != -1 and s2 != -1:
            em_src = em_src[:s1] + "pub fn diag_sink_sort(sink: mut_view<DiagSink>) {}\n" + em_src[s2:]
        sections["compiler.diag.emitter"] = em_src
    if "compiler.diag.format" in sections:
        fmt_src = sections["compiler.diag.format"]
        cut = fmt_src.find("const FMT_STRS:")
        if cut != -1:
            sections["compiler.diag.format"] = (
                fmt_src[:cut]
                + "pub fn ax_diag_render_human(sink: view<DiagSink>, db: view<SourceDatabase>, out: mut_view<DiagBuffer>) {}\n"
            )
    if "compiler.resolve.symtab" in sections:
        sym_src = sections["compiler.resolve.symtab"]
        c0 = sym_src.find("pub fn resolve_map_free(")
        if c0 != -1:
            sections["compiler.resolve.symtab"] = (
                sym_src[:c0]
                + "pub fn resolve_map_free(rmap: mut_view<ResolveMap>) {\n"
                + "    nodemap_free(mut_view(rmap.extern_nodes));\n"
                + "    nodemap_free(mut_view(rmap.module_access_nodes));\n"
                + "    nodemap_free(mut_view(rmap.node_map));\n"
                + "    rmap.naming_ctx = 0 as *mut NamingCtx;\n"
                + "}\n"
                + "pub fn record_symbol_naming(rmap: mut_view<ResolveMap>, id: SymbolId, mod_path: StrView, item_name: StrView) {}\n"
                + "pub fn resolve_symbol_module_path(rmap: view<ResolveMap>, sym: SymbolId) -> StrView { StrView { ptr: 0 as *const u8, len: 0 } }\n"
                + "pub fn resolve_symbol_canonical_name(rmap: view<ResolveMap>, sym: SymbolId) -> StrView { StrView { ptr: 0 as *const u8, len: 0 } }\n"
            )
    if "compiler.hir.hir" in sections:
        hir_src = sections["compiler.hir.hir"]
        cut = hir_src.find("struct HirDumpState {")
        if cut != -1:
            sections["compiler.hir.hir"] = (
                hir_src[:cut]
                + "pub fn emit_hir(buf: mut_view<DiagBuffer>, hf: view<HirFile>, interner: view<StrInterner>, filter_file: FileId) {}\n"
            )
    if "compiler.lex.token" in sections:
        lt_src = sections["compiler.lex.token"]
        cut = lt_src.find("pub fn ax_lex_render_tokens(")
        if cut != -1:
            sections["compiler.lex.token"] = (
                lt_src[:cut]
                + "pub fn ax_lex_render_tokens(res: view<LexResult>, interner: view<StrInterner>, out: mut_view<DiagBuffer>) {}\n"
            )
    if "compiler.types.types" in sections:
        ty_src = sections["compiler.types.types"]
        ty_src = ty_src.replace(
            "@intrinsic fn wrapping_add_u64(a: u64, b: u64) -> u64 { 0 }",
            "fn wrapping_add_u64(a: u64, b: u64) -> u64 {\n"
            "    let a_lo = a & 0xFFFFFFFFu64;\n"
            "    let a_hi = a >> 32u32;\n"
            "    let b_lo = b & 0xFFFFFFFFu64;\n"
            "    let b_hi = b >> 32u32;\n"
            "    let sum_lo = a_lo + b_lo;\n"
            "    let carry = sum_lo >> 32u32;\n"
            "    let sum_hi = (a_hi + b_hi + carry) & 0xFFFFFFFFu64;\n"
            "    (sum_hi << 32u32) | (sum_lo & 0xFFFFFFFFu64)\n"
            "}",
        )
        cut = ty_src.find("    if kind == TY_STRUCT {\n        let mut changed = false;")
        if cut != -1:
            sections["compiler.types.types"] = ty_src[:cut] + "    TypeId { v: res_v }\n}\n"
    if "compiler.traits.solver" in sections:
        sol_src = sections["compiler.traits.solver"]
        c1 = sol_src.find("pub fn emit_trait_overlap_diag(")
        c2 = sol_src.find("pub fn find_trait_item(")
        if c1 != -1 and c2 != -1:
            sol_src = (
                sol_src[:c1]
                + "pub fn emit_trait_ambiguous_diag(sink: mut_view<DiagSink>, sp: Span) {}\n"
                + "pub fn emit_trait_unsatisfied_bound_diag(sink: mut_view<DiagSink>, sp: Span) {}\n"
                + "pub fn traits_check_overlap(hir: view<HirFile>, sink: mut_view<DiagSink>) {}\n"
                + sol_src[c2:]
            )
        c3 = sol_src.find("pub fn resolve_assoc_type_in_impl(")
        if c3 != -1:
            sol_src = (
                sol_src[:c3]
                + "pub fn resolve_assoc_type(hir: view<HirFile>, thir: view<Thir>, self_ty: TypeId, assoc_name: view<StrView>, str_in: view<StrInterner>, db: view<SourceDatabase>) -> *mut HirType { 0 as *mut HirType }\n"
                + "pub fn satisfies_bound(hir: view<HirFile>, thir: view<Thir>, arg_ty: TypeId, bound: *const HirType, str_in: view<StrInterner>, db: view<SourceDatabase>) -> bool { true }\n"
                + "pub fn check_item_bounds(hir: view<HirFile>, thir: view<Thir>, callee_it: *const HirItem, args: view<GenericArgsSlice>, call_span: Span, str_in: view<StrInterner>, db: view<SourceDatabase>, sink: mut_view<DiagSink>) -> bool { true }\n"
                + "pub fn check_impl_supertraits(hir: view<HirFile>, thir: view<Thir>, str_in: view<StrInterner>, db: view<SourceDatabase>, sink: mut_view<DiagSink>) -> bool { true }\n"
            )
        sections["compiler.traits.solver"] = sol_src
    if "compiler.traits.mono" in sections:
        mono_src = sections["compiler.traits.mono"]
        c0 = mono_src.find("    if tk == TY_STRUCT {\n        let gcount")
        c0_end = mono_src.find("    TypeId { v: ty_v }\n}")
        if c0 != -1 and c0_end != -1:
            mono_src = mono_src[:c0] + mono_src[c0_end:]
        c1 = mono_src.find("pub fn deduce_args(")
        if c1 != -1:
            sections["compiler.traits.mono"] = (
                mono_src[:c1]
                + "pub fn deduce_args(gen_ty: TypeId, spec_ty: TypeId, ti: view<TypeInterner>, out_args: *mut TypeId, arg_count: usize) {}\n"
                + "pub fn mono_find_or_create_inst(eng: mut_view<MonoEngine>, str_in: mut_view<StrInterner>, orig: *mut HirItem, args: view<GenericArgsSlice>) -> *mut MonoInstance { 0 as *mut MonoInstance }\n"
                + "pub fn mono_resolve_trait_or_impl_method(hir: view<HirFile>, ti: view<TypeInterner>, str_in: view<StrInterner>, db: view<SourceDatabase>, receiver_ty: TypeId, method_name: view<StrView>) -> *mut HirItem { 0 as *mut HirItem }\n"
            )
    if "compiler.mir.mir" in sections:
        mir_src = sections["compiler.mir.mir"]
        cut = mir_src.find("// --- Region Relate")
        if cut != -1:
            sections["compiler.mir.mir"] = mir_src[:cut]
    return sections


def build_prelude_text():
    pad_variants = ", ".join("V%d" % i for i in range(195))
    parts = [
        "module __ax_sym_pad\n"
        "enum __AxSymPad { %s }\n"
        "struct __AxPtrPad { p0: *const u8, p1: *mut u8, p2: *mut *mut u8, p3: *const *const u8 }\n"
        % pad_variants
    ]
    for rel in STD_SYS_WINDOWS_FILES:
        src = read_bytes(os.path.join(ROOT, rel)).decode("utf-8")
        src = src.replace("module std.sys.windows.", "module host_sys_")
        src = src.replace("let len = GetEnvironmentVariableW", "let vlen = GetEnvironmentVariableW")
        src = src.replace("if len > 0 {", "if vlen > 0 {")
        src = src.replace("while idx < len as usize {", "while idx < vlen as usize {")
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


def build_modules_text(mod_list):
    files = compiler_module_files()
    ref = reference_sections()
    parts = []
    for name, origin in mod_list:
        src = read_bytes(files[name]).decode("utf-8") if origin == "compiler" else ref[name]
        if name == "compiler.mir":
            for trimmed in (
                "pub use compiler.mir.mir.mir_region_relate\n",
                "pub use compiler.mir.mir.mir_print\n",
                "pub use compiler.mir.mir.mir_print_ext\n",
                "pub use compiler.mir.mir.mir_parse\n",
            ):
                src = src.replace(trimmed, "")
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


def bundle_one(in_name, out_name, stdout_line, mod_list):
    in_path = os.path.join(HERE, in_name)
    if not os.path.isfile(in_path):
        return
    main_src = read_bytes(in_path).decode("utf-8")
    prelude_text = build_prelude_text()
    modules_text = build_modules_text(mod_list)
    header = (
        "// test: run\n"
        "// timeout: 600\n"
        "// stdout: %s\\n\n"
        "// Generated by tests/selfhost/interp/gen_interp_tests.py; do not edit directly.\n\n"
    ) % stdout_line
    text = header + prelude_text + "\n" + modules_text + "\n" + main_src
    out_path = os.path.join(HERE, out_name)
    write_bytes(out_path, text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def main():
    bundle_one("unit_main.ax.in", "qa_interp_unit.ax", "ALL INTERP UNIT TESTS PASSED", UNIT_MODULES)
    bundle_one("exec_a_main.ax.in", "qa_interp_exec_a.ax", "ALL INTERP EXEC A TESTS PASSED", UNIT_MODULES)
    bundle_one("exec_b_main.ax.in", "qa_interp_exec_b.ax", "ALL INTERP EXEC B TESTS PASSED", UNIT_MODULES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
