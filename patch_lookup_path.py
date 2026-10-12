import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Add built-in type lookup to lookup_path_type
lookup_builtin_old = '''    StrView name = ax_source_db_span_text(cx->db, path->span);
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {'''

lookup_builtin_new = '''    StrView name = ax_source_db_span_text(cx->db, path->span);
    
    // Check built-in types for UFCS
    if (ax_sv_eq_cstr(name, "bool")) return cx->thir->interner.t_bool;
    if (ax_sv_eq_cstr(name, "char")) return cx->thir->interner.t_char;
    if (ax_sv_eq_cstr(name, "i8")) return cx->thir->interner.t_i8;
    if (ax_sv_eq_cstr(name, "i16")) return cx->thir->interner.t_i16;
    if (ax_sv_eq_cstr(name, "i32")) return cx->thir->interner.t_i32;
    if (ax_sv_eq_cstr(name, "i64")) return cx->thir->interner.t_i64;
    if (ax_sv_eq_cstr(name, "isize")) return cx->thir->interner.t_isize;
    if (ax_sv_eq_cstr(name, "u8")) return cx->thir->interner.t_u8;
    if (ax_sv_eq_cstr(name, "u16")) return cx->thir->interner.t_u16;
    if (ax_sv_eq_cstr(name, "u32")) return cx->thir->interner.t_u32;
    if (ax_sv_eq_cstr(name, "u64")) return cx->thir->interner.t_u64;
    if (ax_sv_eq_cstr(name, "usize")) return cx->thir->interner.t_usize;
    if (ax_sv_eq_cstr(name, "str")) return cx->thir->interner.t_str;

    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {'''

code = code.replace(lookup_builtin_old, lookup_builtin_new)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
