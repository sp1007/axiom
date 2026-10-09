import re
import sys

def main():
    path = r"D:\projects\compiler\new lang\bootstrap\axiom0\src\mir\build\builder.c"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. build_place: add AX_HIR_EXPR_INDEX
    if "AX_HIR_EXPR_INDEX" not in content.split("build_place(Builder *b, const AxHirExpr *expr)")[1][:1000]:
        idx_patch = """    } else if (expr->kind == AX_HIR_EXPR_TUPLE_INDEX) {
        AxMirPlace base = build_place(b, expr->tuple_index.base);
        AxMirProjection *projs = ax_arena_alloc(b->arena, sizeof(AxMirProjection) * (base.proj_count + 1), _Alignof(AxMirProjection));
        for (size_t i = 0; i < base.proj_count; i++) projs[i] = base.projs[i];
        projs[base.proj_count].kind = AX_MIR_PROJ_FIELD;
        projs[base.proj_count].field_idx = expr->tuple_index.tuple_index;
        
        base.projs = projs;
        base.proj_count++;
        return base;
    } else if (expr->kind == AX_HIR_EXPR_INDEX) {
        AxMirPlace base = build_place(b, expr->index.base);
        AxMirOperand idx_op = build_expr_as_operand(b, expr->index.arg);
        
        AxMirLocalId idx_local;
        if ((idx_op.kind == AX_MIR_OP_COPY || idx_op.kind == AX_MIR_OP_MOVE) && idx_op.place.proj_count == 0) {
            idx_local = idx_op.place.local;
        } else {
            TypeId idx_ty = get_expr_type(b, expr->index.arg);
            idx_local = add_local(b, AX_MIR_LOCAL_TEMP, idx_ty, false);
            AxMirPlace temp_place = { idx_local, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt stmt = {0};
            stmt.kind = AX_MIR_STMT_ASSIGN;
            stmt.assign.place = temp_place;
            stmt.assign.rvalue.kind = AX_MIR_RVALUE_USE;
            stmt.assign.rvalue.use = idx_op;
            push_stmt(b, b->current_bb, stmt);
        }
        
        AxMirProjection *projs = ax_arena_alloc(b->arena, sizeof(AxMirProjection) * (base.proj_count + 1), _Alignof(AxMirProjection));
        for (size_t i = 0; i < base.proj_count; i++) projs[i] = base.projs[i];
        projs[base.proj_count].kind = AX_MIR_PROJ_INDEX;
        projs[base.proj_count].index_local = idx_local;
        
        base.projs = projs;
        base.proj_count++;
        return base;
    }"""
        content = re.sub(r'\} else if \(expr->kind == AX_HIR_EXPR_TUPLE_INDEX\) \{.*?return base;\n    \}', idx_patch, content, flags=re.DOTALL)

    # 2. build_expr_as_operand: add AX_HIR_EXPR_INDEX
    content = content.replace(
        "expr->kind == AX_HIR_EXPR_FIELD || expr->kind == AX_HIR_EXPR_TUPLE_INDEX)",
        "expr->kind == AX_HIR_EXPR_FIELD || expr->kind == AX_HIR_EXPR_TUPLE_INDEX || expr->kind == AX_HIR_EXPR_INDEX)"
    )

    # 3. build_expr_into: add AX_HIR_EXPR_INDEX
    content = content.replace(
        "expr->kind == AX_HIR_EXPR_FIELD || expr->kind == AX_HIR_EXPR_TUPLE_INDEX) {",
        "expr->kind == AX_HIR_EXPR_FIELD || expr->kind == AX_HIR_EXPR_TUPLE_INDEX || expr->kind == AX_HIR_EXPR_INDEX) {"
    )

    # 4. build_expr_into: add AX_HIR_EXPR_ARRAY
    if "AX_HIR_EXPR_ARRAY" not in content:
        array_patch = """    } else if (expr->kind == AX_HIR_EXPR_ARRAY) {
        if (expr->array.count) {
            AxMirStmt stmt = {0};
            stmt.kind = AX_MIR_STMT_ASSIGN;
            stmt.assign.place = dest;
            stmt.assign.rvalue.kind = AX_MIR_RVALUE_REPEAT;
            stmt.assign.rvalue.repeat.op = build_expr_as_operand(b, expr->array.elems);
            stmt.assign.rvalue.repeat.count = build_expr_as_operand(b, expr->array.count);
            push_stmt(b, b->current_bb, stmt);
        } else {
            AxMirStmt stmt = {0};
            stmt.kind = AX_MIR_STMT_ASSIGN;
            stmt.assign.place = dest;
            stmt.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
            
            TypeId ty = get_expr_type(b, expr);
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            uint32_t len = 0;
            if (t && t->kind == AX_TY_ARRAY) len = t->array.len;
            
            stmt.assign.rvalue.aggregate.operand_count = len;
            stmt.assign.rvalue.aggregate.variant_idx = 0;
            
            if (len > 0) {
                stmt.assign.rvalue.aggregate.operands = ax_arena_alloc_array(b->arena, len, sizeof(AxMirOperand), _Alignof(AxMirOperand));
                size_t i = 0;
                for (const AxHirExpr *e = expr->array.elems; e; e = e->next) {
                    stmt.assign.rvalue.aggregate.operands[i++] = build_expr_as_operand(b, e);
                }
            } else {
                stmt.assign.rvalue.aggregate.operands = NULL;
            }
            push_stmt(b, b->current_bb, stmt);
        }"""
        content = content.replace("    } else if (expr->kind == AX_HIR_EXPR_TUPLE) {", array_patch + "\n    } else if (expr->kind == AX_HIR_EXPR_TUPLE) {")

    # 5. build_expr_into: add len call intercept
    len_patch = """    } else if (expr->kind == AX_HIR_EXPR_CALL) {
        if (expr->call.callee->kind == AX_HIR_EXPR_PATH) {
            StrView callee_name = ax_source_db_span_text(b->db, expr->call.callee->span);
            if (ax_sv_eq_cstr(callee_name, "len")) {
                AxMirOperand arg = build_expr_as_operand(b, expr->call.args);
                AxMirPlace arg_place;
                if (arg.kind == AX_MIR_OP_COPY || arg.kind == AX_MIR_OP_MOVE) {
                    arg_place = arg.place;
                } else {
                    AxMirLocalId temp = add_local(b, AX_MIR_LOCAL_TEMP, get_expr_type(b, expr->call.args), false);
                    arg_place = (AxMirPlace){ temp, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    AxMirStmt s = {0};
                    s.kind = AX_MIR_STMT_ASSIGN;
                    s.assign.place = arg_place;
                    s.assign.rvalue.kind = AX_MIR_RVALUE_USE;
                    s.assign.rvalue.use = arg;
                    push_stmt(b, b->current_bb, s);
                }
                AxMirStmt stmt = {0};
                stmt.kind = AX_MIR_STMT_ASSIGN;
                stmt.assign.place = dest;
                stmt.assign.rvalue.kind = AX_MIR_RVALUE_LEN;
                stmt.assign.rvalue.len = arg_place;
                push_stmt(b, b->current_bb, stmt);
                return;
            }
        }
        AxMirOperand callee = build_expr_as_operand(b, expr->call.callee);"""
    content = content.replace("    } else if (expr->kind == AX_HIR_EXPR_CALL) {\n        AxMirOperand callee = build_expr_as_operand(b, expr->call.callee);", len_patch)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
if __name__ == "__main__":
    main()
