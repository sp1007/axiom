import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix braces for pass 2
brace_old = '''            check_literal_ranges(&cx);
        }
    }

    ax_xfree(cx.int_vars);'''
brace_new = '''            check_literal_ranges(&cx);
                }
            }
        }
    }

    ax_xfree(cx.int_vars);'''

code = code.replace(brace_old, brace_new)

# Add enum variant constructor logic back into METHOD_CALL
method_old = '''            if (!method_item) {
                return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
            }'''

method_new = '''            if (!method_item) {
                if (t->kind == AX_TY_ENUM) {
                    size_t vidx = 0;
                    for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                        StrView vname = ax_interner_get(cx->str_in, v->name);
                        if (ax_sv_eq(vname, mname)) {
                            AxExprVariantMap_insert(&cx->thir->expr_variants, expr, vidx);
                            if (v->is_struct) {
                                return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                            }
                            size_t expected_args = t->enm.variant_field_counts[vidx];
                            size_t argc = 0;
                            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) argc++;
                            if (argc != expected_args) {
                                return type_error(cx, expr->span, AX_TYPE_ARG_COUNT);
                            }
                            const TypeId *payloads = t->enm.variant_fields[vidx];
                            size_t arg_idx = 0;
                            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                                check_expr(cx, a, payloads[arg_idx++]);
                            }
                            return receiver_ty;
                        }
                        vidx++;
                    }
                }
                return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
            }'''

code = code.replace(method_old, method_new)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
