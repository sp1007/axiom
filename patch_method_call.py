import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Add find_inherent_method before check_expr
find_method = '''
static const AxHirItem *find_inherent_method(TypeckCtx *cx, TypeId base_ty, StrView method_name) {
    if (is_error(cx, base_ty)) return NULL;
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path == NULL) {
            TypeId self_ty = hir_type_to_typeid(cx, it->impl.self_type);
            if (is_error(cx, self_ty)) continue;
            if (self_ty.v == base_ty.v) {
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        StrView mname = ax_interner_get(cx->str_in, m->fn.name);
                        if (ax_sv_eq(mname, method_name)) {
                            return m;
                        }
                    }
                }
            }
        }
    }
    return NULL;
}

static TypeId check_expr('''

code = code.replace('static TypeId check_expr(', find_method, 1)

# Now replace the AX_HIR_EXPR_METHOD_CALL branch
# Currently it starts around "case AX_HIR_EXPR_METHOD_CALL: {" and ends before "case AX_HIR_EXPR_TRY:"
method_call_old_regex = r"case AX_HIR_EXPR_METHOD_CALL: \{.*?return type_error\(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP\);\s*\}"

method_call_new = '''case AX_HIR_EXPR_METHOD_CALL: {
            TypeId receiver_ty = check_expr(cx, expr->method_call.receiver, TypeId_none());
            if (is_error(cx, receiver_ty)) return cx->thir->interner.t_error;
            
            // Strip view/mut_view to find the base type for method lookup
            TypeId base_ty = receiver_ty;
            const AxType *t = ax_type_get(&cx->thir->interner, base_ty);
            while (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW || t->kind == AX_TY_PTR) {
                base_ty = (t->kind == AX_TY_PTR) ? t->ptr.pointee : t->view.pointee;
                t = ax_type_get(&cx->thir->interner, base_ty);
            }
            
            StrView mname = ax_interner_get(cx->str_in, expr->method_call.method_name);
            const AxHirItem *method_item = find_inherent_method(cx, base_ty, mname);
            
            if (!method_item) {
                return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
            }
            
            AxExprMethodMap_insert(&cx->thir->expr_methods, expr, method_item);
            
            TypeId *fn_ty_ptr = AxItemTypeMap_get(&cx->thir->item_types, method_item);
            if (!fn_ty_ptr) AX_ICE("Method missing fn type");
            const AxType *fn_ty = ax_type_get(&cx->thir->interner, *fn_ty_ptr);
            
            size_t expected_args = fn_ty->fn.param_count;
            size_t argc = 1; // +1 for receiver
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) argc++;
            
            if (argc != expected_args) {
                // Check arguments just in case, then return error
                for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                    check_expr(cx, a, TypeId_none());
                }
                return type_error(cx, expr->span, AX_TYPE_ARG_COUNT);
            }
            
            // The receiver maps to param 0.
            // The receiver type we found (receiver_ty) might not match the param 0 type exactly (due to autoref)
            // But we let the HIR -> MIR or capability pass handle the implicit view/mut_view, OR we might need to coerce it here?
            // "receivers by value/view/mut_view with automatic ephemeral capability, checked by T048 analysis."
            // So we don't necessarily enforce strict equality here for the receiver parameter, or maybe we do unify/coerce?
            // Axiom's typeck.c usually requires exact types or explicit casts, except for receiver autoref.
            // We'll skip strict checking for param 0 because autoref is magic. Or wait, maybe we unify it if it doesn't need autoref.
            // Let's just do a lax check for param 0: as long as base_ty matches, it's fine. The T048 analysis will do the rest.
            
            size_t i = 1;
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                TypeId arg_expected = fn_ty->fn.param_types[i];
                TypeId arg_ty = check_expr(cx, a, arg_expected);
                if (!is_error(cx, arg_ty) && !unify_ty(cx, arg_ty, arg_expected)) {
                    type_error(cx, a->span, AX_TYPE_MISMATCH);
                }
                i++;
            }
            
            return fn_ty->fn.ret_type;
        }'''

code = re.sub(method_call_old_regex, method_call_new, code, flags=re.DOTALL)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
