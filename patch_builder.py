import re

with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Add AX_HIR_EXPR_METHOD_CALL handling right before 'else if (expr->kind == AX_HIR_EXPR_CAST)'
old_code = r'    \} else if \(expr->kind == AX_HIR_EXPR_CAST\) \{'

new_code = '''    } else if (expr->kind == AX_HIR_EXPR_METHOD_CALL) {
        const AxHirItem **method_item_ptr = AxExprMethodMap_get(&b->thir->expr_methods, expr);
        const AxHirItem *method_item = method_item_ptr ? *method_item_ptr : NULL;
        
        AxMirOperand callee = {0};
        callee.kind = AX_MIR_OP_CONST;
        callee.constant.kind = AX_MIR_CONST_FUNC;
        callee.constant.func = method_item;
        callee.constant.ty = *AxItemTypeMap_get(&b->thir->item_types, method_item);
        
        bool has_self = (method_item->fn.params && ax_sv_eq_cstr(ax_interner_get(b->str_in, method_item->fn.params->name), "self"));
        
        size_t arg_count = has_self ? 1 : 0;
        for (const AxHirExpr *arg = expr->method_call.args; arg; arg = arg->next) arg_count++;
        
        AxMirOperand *args = NULL;
        if (arg_count > 0) {
            args = ax_arena_alloc(b->arena, sizeof(AxMirOperand) * arg_count, _Alignof(AxMirOperand));
            size_t i = 0;
            if (has_self) {
                args[i++] = build_expr_as_operand(b, expr->method_call.receiver);
            }
            for (const AxHirExpr *arg = expr->method_call.args; arg; arg = arg->next) {
                args[i++] = build_expr_as_operand(b, arg);
            }
        }
        
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_CALL;
        term.location = expr->span;
        term.call.func = callee;
        term.call.args = args;
        term.call.arg_count = arg_count;
        term.call.destination = dest;
        
        AxMirBbId next_bb = add_bb(b);
        term.call.target = next_bb;
        
        set_terminator(b, b->current_bb, term);
        b->current_bb = next_bb;
    } else if (expr->kind == AX_HIR_EXPR_CAST) {'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(code)
