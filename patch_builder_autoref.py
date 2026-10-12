import re

with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    code = f.read()

old_code = r'''            if \(has_self\) \{
                args\[i\+\+\] = build_expr_as_operand\(b, expr->method_call\.receiver\);
            \}'''

new_code = '''            if (has_self) {
                TypeId self_ty = fn_ty->fn.param_types[0];
                const AxType *self_t = ax_type_get(&b->thir->interner, self_ty);
                TypeId actual_self_ty = get_expr_type(b, expr->method_call.receiver);
                const AxType *actual_self_t = ax_type_get(&b->thir->interner, actual_self_ty);
                
                if (self_t && (self_t->kind == AX_TY_VIEW || self_t->kind == AX_TY_MUT_VIEW) && 
                    actual_self_t && actual_self_t->kind != AX_TY_VIEW && actual_self_t->kind != AX_TY_MUT_VIEW) {
                    
                    AxMirPlace receiver_place = build_place(b, expr->method_call.receiver);
                    AxMirLocalId temp = add_local(b, AX_MIR_LOCAL_TEMP, self_ty, false);
                    AxMirPlace temp_place = { temp, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    
                    AxMirStmt ref_stmt = {0};
                    ref_stmt.kind = AX_MIR_STMT_ASSIGN;
                    ref_stmt.location = expr->span;
                    ref_stmt.assign.place = temp_place;
                    ref_stmt.assign.rvalue.kind = AX_MIR_RVALUE_REF;
                    ref_stmt.assign.rvalue.ref.bk = (self_t->kind == AX_TY_MUT_VIEW) ? AX_MIR_BORROW_MUT : AX_MIR_BORROW_SHARED;
                    ref_stmt.assign.rvalue.ref.place = receiver_place;
                    push_stmt(b, b->current_bb, ref_stmt);
                    
                    AxMirOperand ref_op = {0};
                    ref_op.kind = AX_MIR_OP_MOVE;
                    ref_op.place = temp_place;
                    args[i++] = ref_op;
                } else {
                    args[i++] = build_expr_as_operand(b, expr->method_call.receiver);
                }
            }'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(code)
