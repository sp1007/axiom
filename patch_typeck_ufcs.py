import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

old_code = r'''            bool is_type_name = false;
            if \(expr->method_call\.receiver->kind == AX_HIR_EXPR_PATH\) \{
                StrView name = ax_interner_get\(cx->str_in, expr->method_call\.receiver->path\.path\.symbol\);
                if \(ax_sv_eq_cstr\(name, "u8"\) \|\| ax_sv_eq_cstr\(name, "u16"\) \|\| ax_sv_eq_cstr\(name, "u32"\) \|\| ax_sv_eq_cstr\(name, "u64"\) \|\|
                    ax_sv_eq_cstr\(name, "i8"\) \|\| ax_sv_eq_cstr\(name, "i16"\) \|\| ax_sv_eq_cstr\(name, "i32"\) \|\| ax_sv_eq_cstr\(name, "i64"\) \|\|
                    ax_sv_eq_cstr\(name, "bool"\) \|\| ax_sv_eq_cstr\(name, "f32"\) \|\| ax_sv_eq_cstr\(name, "f64"\) \|\| ax_sv_eq_cstr\(name, "char"\) \|\| ax_sv_eq_cstr\(name, "Str"\) \|\| ax_sv_eq_cstr\(name, "never"\) \|\| ax_sv_eq_cstr\(name, "usize"\) \|\| ax_sv_eq_cstr\(name, "isize"\)\) \{
                    is_type_name = true;
                \} else \{
                    const AxHirItem \*item = lookup_path_item\(cx, &expr->method_call\.receiver->path\.path\);
                    if \(item && \(item->kind == AX_HIR_ITEM_STRUCT \|\| item->kind == AX_HIR_ITEM_ENUM \|\| item->kind == AX_HIR_ITEM_ALIAS\)\) \{
                        is_type_name = true;
                    \}
                \}
            \}'''

new_code = '''            bool is_type_name = false;
            if (expr->method_call.receiver->kind == AX_HIR_EXPR_PATH) {
                is_type_name = true;
                if (expr->method_call.receiver->path.path.symbol.v != 0) {
                    for (size_t k = 0; k < cx->vars_len; k++) {
                        if (cx->vars[k].sym.v == expr->method_call.receiver->path.path.symbol.v) {
                            is_type_name = false;
                            break;
                        }
                    }
                }
            }'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
