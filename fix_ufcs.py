import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

# I need to insert a helper to check if a path is a type name, or just do it inline.
# Let's do it inline where AX_HIR_EXPR_METHOD_CALL starts.

old_code = r'''        case AX_HIR_EXPR_METHOD_CALL: \{
            TypeId receiver_ty = check_expr\(cx, expr->method_call\.receiver, TypeId_none\(\)\);'''

new_code = '''        case AX_HIR_EXPR_METHOD_CALL: {
            bool is_type_name = false;
            if (expr->method_call.receiver->kind == AX_HIR_EXPR_PATH) {
                StrView name = ax_interner_get(cx->str_in, expr->method_call.receiver->path.path.symbol);
                if (ax_sv_eq_cstr(name, "u8") || ax_sv_eq_cstr(name, "u16") || ax_sv_eq_cstr(name, "u32") || ax_sv_eq_cstr(name, "u64") ||
                    ax_sv_eq_cstr(name, "i8") || ax_sv_eq_cstr(name, "i16") || ax_sv_eq_cstr(name, "i32") || ax_sv_eq_cstr(name, "i64") ||
                    ax_sv_eq_cstr(name, "bool") || ax_sv_eq_cstr(name, "f32") || ax_sv_eq_cstr(name, "f64") || ax_sv_eq_cstr(name, "char") || ax_sv_eq_cstr(name, "Str") || ax_sv_eq_cstr(name, "never") || ax_sv_eq_cstr(name, "usize") || ax_sv_eq_cstr(name, "isize")) {
                    is_type_name = true;
                } else {
                    const AxHirItem *item = lookup_path_item(cx, &expr->method_call.receiver->path.path);
                    if (item && (item->kind == AX_HIR_ITEM_STRUCT || item->kind == AX_HIR_ITEM_ENUM || item->kind == AX_HIR_ITEM_ALIAS)) {
                        is_type_name = true;
                    }
                }
            }
            TypeId receiver_ty = check_expr(cx, expr->method_call.receiver, TypeId_none());'''

code = re.sub(old_code, new_code, code)

old_code2 = r'''            size_t expected_args = fn_ty->fn\.param_count;
            bool has_self = \(method_item->fn\.params && ax_sv_eq_cstr\(ax_interner_get\(cx->str_in, method_item->fn\.params->name\), "self"\)\);
            size_t argc = has_self \? 1 : 0;
            for \(const AxHirExpr \*a = expr->method_call\.args; a; a = a->next\) argc\+\+;
            
            if \(argc != expected_args\) \{
                // Check arguments just in case, then return error
                for \(const AxHirExpr \*a = expr->method_call\.args; a; a = a->next\) \{
                    check_expr\(cx, a, TypeId_none\(\)\);
                \}
                return type_error\(cx, expr->span, AX_TYPE_ARG_COUNT\);
            \}
            
            // The receiver maps to param 0.
            // The receiver type we found \(receiver_ty\) might not match the param 0 type exactly \(due to autoref\)
            // But we let the HIR -> MIR or capability pass handle the implicit view/mut_view, OR we might need to coerce it here\?
            // "receivers by value/view/mut_view with automatic ephemeral capability, checked by T048 analysis."
            // So we don't necessarily enforce strict equality here for the receiver parameter, or maybe we do unify/coerce\?
            // Axiom's typeck.c usually requires exact types or explicit casts, except for receiver autoref.
            // We'll skip strict checking for param 0 because autoref is magic. Or wait, maybe we unify it if it doesn't need autoref.
            // Let's just do a lax check for param 0: as long as base_ty matches, it's fine. The T048 analysis will do the rest.
            
            size_t i = has_self \? 1 : 0;'''

new_code2 = '''            size_t expected_args = fn_ty->fn.param_count;
            bool has_self = (method_item->fn.params && ax_sv_eq_cstr(ax_interner_get(cx->str_in, method_item->fn.params->name), "self"));
            
            bool pass_receiver = has_self && !is_type_name;
            size_t argc = pass_receiver ? 1 : 0;
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) argc++;
            
            if (argc != expected_args) {
                for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                    check_expr(cx, a, TypeId_none());
                }
                return type_error(cx, expr->span, AX_TYPE_ARG_COUNT);
            }
            
            size_t i = pass_receiver ? 1 : 0;'''

code = re.sub(old_code2, new_code2, code)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
