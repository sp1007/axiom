
#include "mir/build/build.h"
#include <stdlib.h>
#include <string.h>

typedef struct BbData {
    AxMirStmt *stmts;
    size_t stmt_count;
    size_t stmt_cap;
    AxMirTerminator terminator;
    bool is_terminated;
} BbData;


typedef struct LoopContext {
    AxMirBbId break_bb;
    AxMirBbId continue_bb;
    AxMirPlace dest;
    StrId label;
} LoopContext;

typedef struct Builder {
    AxArena *arena;
    const AxThir *thir;
    
    AxMirLocalDecl *locals;
    size_t local_count;
    size_t local_cap;
    
    BbData *bbs;
    size_t bb_count;
    size_t bb_cap;
    
    AxMirBbId current_bb;
    
    LoopContext *loops;
    size_t loop_count;
    size_t loop_cap;
    
    struct {
        AxSymbolId sym;
        AxMirLocalId loc;
    } *var_map;
    size_t var_count;
    size_t var_cap;
} Builder;

static AxMirLocalId add_local(Builder *b, AxMirLocalKind kind, TypeId ty, bool mut) {
    if (b->local_count >= b->local_cap) {
        b->local_cap = b->local_cap ? b->local_cap * 2 : 16;
        b->locals = realloc(b->locals, b->local_cap * sizeof(AxMirLocalDecl));
    }
    AxMirLocalId id = { (uint32_t)b->local_count++ };
    b->locals[id.v].kind = kind;
    b->locals[id.v].ty = ty;
    b->locals[id.v].mut = mut;
    return id;
}

static AxMirBbId add_bb(Builder *b) {
    if (b->bb_count >= b->bb_cap) {
        b->bb_cap = b->bb_cap ? b->bb_cap * 2 : 16;
        b->bbs = realloc(b->bbs, b->bb_cap * sizeof(BbData));
    }
    AxMirBbId id = { (uint32_t)b->bb_count++ };
    b->bbs[id.v].stmts = NULL;
    b->bbs[id.v].stmt_count = 0;
    b->bbs[id.v].stmt_cap = 0;
    b->bbs[id.v].is_terminated = false;
    memset(&b->bbs[id.v].terminator, 0, sizeof(AxMirTerminator));
    b->bbs[id.v].terminator.kind = AX_MIR_TERM_UNREACHABLE;
    return id;
}

static void push_stmt(Builder *b, AxMirBbId bb, AxMirStmt stmt) {
    BbData *d = &b->bbs[bb.v];
    if (d->stmt_count >= d->stmt_cap) {
        d->stmt_cap = d->stmt_cap ? d->stmt_cap * 2 : 8;
        d->stmts = realloc(d->stmts, d->stmt_cap * sizeof(AxMirStmt));
    }
    d->stmts[d->stmt_count++] = stmt;
}

static void set_terminator(Builder *b, AxMirBbId bb, AxMirTerminator term) {
    BbData *d = &b->bbs[bb.v];
    if (!d->is_terminated) {
        d->terminator = term;
        d->is_terminated = true;
    }
}

static TypeId get_expr_type(Builder *b, const AxHirExpr *expr) {
    TypeId ty = {0};
    const TypeId *res = AxExprTypeMap_get(&b->thir->expr_types, expr);
    if (res) return *res;
    return ty;
}

static void build_expr_into(Builder *b, const AxHirExpr *expr, AxMirPlace dest);
static void build_block_into(Builder *b, const AxHirBlock *block, AxMirPlace dest);

static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr) {
    AxMirOperand op = {0};
    if (expr->kind == AX_HIR_EXPR_LITERAL) {
        op.kind = AX_MIR_OP_CONST;
        op.constant.ty = get_expr_type(b, expr);
        if (expr->literal.kind == AX_TOK_INT || expr->literal.kind == AX_TOK_CHAR) {
            op.constant.val = expr->literal.val.int_val.value;
        } else if (expr->literal.kind == AX_TOK_KW_TRUE) {
            op.constant.val = 1;
        } else if (expr->literal.kind == AX_TOK_KW_FALSE) {
            op.constant.val = 0;
        } else {
            op.constant.val = 0;
        }
        return op;
    } else if (expr->kind == AX_HIR_EXPR_PATH) {
        AxSymbolId sym = expr->path.path.symbol;
        AxMirLocalId loc = {0};
        bool found = false;
        for (size_t i = 0; i < b->var_count; i++) {
            if (b->var_map[i].sym.v == sym.v) {
                loc = b->var_map[i].loc;
                found = true;
                break;
            }
        }
        if (!found) {
            op.kind = AX_MIR_OP_CONST;
            op.constant.ty = get_expr_type(b, expr);
            op.constant.val = sym.v;
            return op;
        } else {
            op.kind = AX_MIR_OP_COPY;
            AxMirPlace p = { loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            op.place = p;
            return op;
        }
    }
    
    TypeId ty = get_expr_type(b, expr);
    AxMirLocalId temp = add_local(b, AX_MIR_LOCAL_TEMP, ty, false);
    AxMirPlace temp_place = { temp, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
    
    build_expr_into(b, expr, temp_place);
    
    op.kind = AX_MIR_OP_MOVE;
    op.place = temp_place;
    return op;
}

static void build_expr_into(Builder *b, const AxHirExpr *expr, AxMirPlace dest) {
    if (expr->kind == AX_HIR_EXPR_LITERAL || expr->kind == AX_HIR_EXPR_PATH) {
        AxMirOperand op = build_expr_as_operand(b, expr);
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_USE;
        stmt.assign.rvalue.use = op;
        push_stmt(b, b->current_bb, stmt);
    } else if (expr->kind == AX_HIR_EXPR_BINARY) {
        if (expr->binary.op == AX_BINOP_LOGAND || expr->binary.op == AX_BINOP_LOGOR) {
            // Short-circuit logic
            AxMirOperand lhs = build_expr_as_operand(b, expr->binary.left);
            
            AxMirBbId bb_rhs = add_bb(b);
            AxMirBbId bb_end = add_bb(b);
            
            AxMirTerminator switch_term = {0};
            switch_term.kind = AX_MIR_TERM_SWITCH_INT;
            switch_term.switch_int.discr = lhs;
            AxMirSwitchTarget *targets = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
            targets[0].value = 0; // false
            
            if (expr->binary.op == AX_BINOP_LOGAND) {
                targets[0].target = bb_end; // if false, skip rhs
                switch_term.switch_int.targets.otherwise = bb_rhs; // if true, eval rhs
            } else {
                targets[0].target = bb_rhs; // if false, eval rhs
                switch_term.switch_int.targets.otherwise = bb_end; // if true, skip rhs
            }
            switch_term.switch_int.targets.values = targets;
            switch_term.switch_int.targets.count = 1;
            set_terminator(b, b->current_bb, switch_term);
            
            // if skipped, dest = lhs
            // wait! if bb_end is reached directly from current_bb, dest = lhs needs to happen
            // But we can't easily put an assignment on the edge.
            // Better: just generate `dest = lhs` in current_bb before the branch.
            AxMirStmt assign_lhs = {0};
            assign_lhs.kind = AX_MIR_STMT_ASSIGN;
            assign_lhs.assign.place = dest;
            assign_lhs.assign.rvalue.kind = AX_MIR_RVALUE_USE;
            assign_lhs.assign.rvalue.use = lhs;
            push_stmt(b, b->current_bb, assign_lhs);
            
            // RHS block
            b->current_bb = bb_rhs;
            AxMirOperand rhs = build_expr_as_operand(b, expr->binary.right);
            AxMirStmt assign_rhs = {0};
            assign_rhs.kind = AX_MIR_STMT_ASSIGN;
            assign_rhs.assign.place = dest;
            assign_rhs.assign.rvalue.kind = AX_MIR_RVALUE_USE;
            assign_rhs.assign.rvalue.use = rhs;
            push_stmt(b, b->current_bb, assign_rhs);
            
            AxMirTerminator goto_end = {0};
            goto_end.kind = AX_MIR_TERM_GOTO;
            goto_end.goto_target = bb_end;
            set_terminator(b, b->current_bb, goto_end);
            
            b->current_bb = bb_end;
            return;
        }
        
        AxMirOperand lhs = build_expr_as_operand(b, expr->binary.left);
        AxMirOperand rhs = build_expr_as_operand(b, expr->binary.right);
        
        bool is_checked = false;
        AxMirBinOp binop = 0;
        switch (expr->binary.op) {
            case AX_BINOP_ADD: binop = AX_MIR_BINOP_ADD; is_checked = true; break;
            case AX_BINOP_SUB: binop = AX_MIR_BINOP_SUB; is_checked = true; break;
            case AX_BINOP_MUL: binop = AX_MIR_BINOP_MUL; is_checked = true; break;
            case AX_BINOP_DIV: binop = AX_MIR_BINOP_DIV; is_checked = true; break;
            case AX_BINOP_REM: binop = AX_MIR_BINOP_REM; is_checked = true; break;
            case AX_BINOP_SHL: binop = AX_MIR_BINOP_SHL; is_checked = true; break;
            case AX_BINOP_SHR: binop = AX_MIR_BINOP_SHR; is_checked = true; break;
            case AX_BINOP_BITAND: binop = AX_MIR_BINOP_BIT_AND; break;
            case AX_BINOP_BITOR: binop = AX_MIR_BINOP_BIT_OR; break;
            case AX_BINOP_BITXOR: binop = AX_MIR_BINOP_BIT_XOR; break;
            case AX_BINOP_EQ: binop = AX_MIR_BINOP_EQ; break;
            case AX_BINOP_NE: binop = AX_MIR_BINOP_NE; break;
            case AX_BINOP_LT: binop = AX_MIR_BINOP_LT; break;
            case AX_BINOP_LE: binop = AX_MIR_BINOP_LE; break;
            case AX_BINOP_GT: binop = AX_MIR_BINOP_GT; break;
            case AX_BINOP_GE: binop = AX_MIR_BINOP_GE; break;
            default: break;
        }

        if (is_checked) {
            if (binop == AX_MIR_BINOP_DIV || binop == AX_MIR_BINOP_REM) {
                AxMirLocalId cond_not_zero = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                AxMirPlace cond_not_zero_place = { cond_not_zero, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                AxMirStmt ne_zero_stmt = {0};
                ne_zero_stmt.kind = AX_MIR_STMT_ASSIGN;
                ne_zero_stmt.assign.place = cond_not_zero_place;
                ne_zero_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
                ne_zero_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_NE;
                ne_zero_stmt.assign.rvalue.binary_op.lhs = rhs;
                ne_zero_stmt.assign.rvalue.binary_op.rhs.kind = AX_MIR_OP_CONST;
                ne_zero_stmt.assign.rvalue.binary_op.rhs.constant.ty = get_expr_type(b, expr->binary.right);
                ne_zero_stmt.assign.rvalue.binary_op.rhs.constant.val = 0;
                push_stmt(b, b->current_bb, ne_zero_stmt);
                
                AxMirTerminator assert_z_term = {0};
                assert_z_term.kind = AX_MIR_TERM_ASSERT;
                assert_z_term.assert.cond.kind = AX_MIR_OP_COPY;
                assert_z_term.assert.cond.place = cond_not_zero_place;
                assert_z_term.assert.expected = true;
                assert_z_term.assert.msg = "division by zero";
                assert_z_term.assert.target = add_bb(b);
                assert_z_term.assert.unwind = add_bb(b);
                set_terminator(b, b->current_bb, assert_z_term);
                b->current_bb = assert_z_term.assert.target;

                if (binop == AX_MIR_BINOP_DIV || binop == AX_MIR_BINOP_REM) {
                    AxMirLocalId cond_not_ov = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                    AxMirPlace cond_not_ov_place = { cond_not_ov, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    
                    AxMirLocalId temp_ov = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                    AxMirPlace temp_ov_place = { temp_ov, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    
                    AxMirStmt ov_stmt = {0};
                    ov_stmt.kind = AX_MIR_STMT_ASSIGN;
                    ov_stmt.assign.place = temp_ov_place;
                    ov_stmt.assign.rvalue.kind = AX_MIR_RVALUE_OVERFLOWS_BINARY_OP;
                    ov_stmt.assign.rvalue.binary_op.op = binop;
                    ov_stmt.assign.rvalue.binary_op.lhs = lhs;
                    ov_stmt.assign.rvalue.binary_op.rhs = rhs;
                    push_stmt(b, b->current_bb, ov_stmt);
                    
                    AxMirStmt not_stmt = {0};
                    not_stmt.kind = AX_MIR_STMT_ASSIGN;
                    not_stmt.assign.place = cond_not_ov_place;
                    not_stmt.assign.rvalue.kind = AX_MIR_RVALUE_UNARY_OP;
                    not_stmt.assign.rvalue.unary_op.op = AX_MIR_UNOP_NOT;
                    not_stmt.assign.rvalue.unary_op.operand.kind = AX_MIR_OP_COPY;
                    not_stmt.assign.rvalue.unary_op.operand.place = temp_ov_place;
                    push_stmt(b, b->current_bb, not_stmt);
                    
                    AxMirTerminator assert_ov = {0};
                    assert_ov.kind = AX_MIR_TERM_ASSERT;
                    assert_ov.assert.cond.kind = AX_MIR_OP_COPY;
                    assert_ov.assert.cond.place = cond_not_ov_place;
                    assert_ov.assert.expected = true;
                    assert_ov.assert.msg = "arithmetic overflow";
                    assert_ov.assert.target = add_bb(b);
                    assert_ov.assert.unwind = add_bb(b);
                    set_terminator(b, b->current_bb, assert_ov);
                    b->current_bb = assert_ov.assert.target;
                }
            } else if (binop == AX_MIR_BINOP_SHL || binop == AX_MIR_BINOP_SHR) {
                AxMirLocalId cond_non_neg = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                AxMirPlace cond_non_neg_place = { cond_non_neg, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                AxMirStmt ge_zero_stmt = {0};
                ge_zero_stmt.kind = AX_MIR_STMT_ASSIGN;
                ge_zero_stmt.assign.place = cond_non_neg_place;
                ge_zero_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
                ge_zero_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_GE;
                ge_zero_stmt.assign.rvalue.binary_op.lhs = rhs;
                ge_zero_stmt.assign.rvalue.binary_op.rhs.kind = AX_MIR_OP_CONST;
                ge_zero_stmt.assign.rvalue.binary_op.rhs.constant.ty = get_expr_type(b, expr->binary.right);
                ge_zero_stmt.assign.rvalue.binary_op.rhs.constant.val = 0;
                push_stmt(b, b->current_bb, ge_zero_stmt);

                AxMirTerminator assert_n_term = {0};
                assert_n_term.kind = AX_MIR_TERM_ASSERT;
                assert_n_term.assert.cond.kind = AX_MIR_OP_COPY;
                assert_n_term.assert.cond.place = cond_non_neg_place;
                assert_n_term.assert.expected = true;
                assert_n_term.assert.msg = "shift amount out of range";
                assert_n_term.assert.target = add_bb(b);
                assert_n_term.assert.unwind = add_bb(b);
                set_terminator(b, b->current_bb, assert_n_term);
                b->current_bb = assert_n_term.assert.target;
                
                AxMirLocalId cond_less_bits = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                AxMirPlace cond_less_bits_place = { cond_less_bits, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                AxMirStmt lt_bits_stmt = {0};
                lt_bits_stmt.kind = AX_MIR_STMT_ASSIGN;
                lt_bits_stmt.assign.place = cond_less_bits_place;
                lt_bits_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
                lt_bits_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_LT;
                lt_bits_stmt.assign.rvalue.binary_op.lhs = rhs;
                lt_bits_stmt.assign.rvalue.binary_op.rhs.kind = AX_MIR_OP_CONST;
                lt_bits_stmt.assign.rvalue.binary_op.rhs.constant.ty = get_expr_type(b, expr->binary.right);
                
                TypeId lhs_ty = get_expr_type(b, expr->binary.left);
                const AxType *ty = ax_type_get(&b->thir->interner, lhs_ty);
                int bits = 32;
                if (ty) {
                    if (ty->kind == AX_TY_I8 || ty->kind == AX_TY_U8) bits = 8;
                    else if (ty->kind == AX_TY_I16 || ty->kind == AX_TY_U16) bits = 16;
                    else if (ty->kind == AX_TY_I32 || ty->kind == AX_TY_U32) bits = 32;
                    else if (ty->kind == AX_TY_I64 || ty->kind == AX_TY_U64) bits = 64;
                }
                lt_bits_stmt.assign.rvalue.binary_op.rhs.constant.val = bits;
                push_stmt(b, b->current_bb, lt_bits_stmt);

                AxMirTerminator assert_b_term = {0};
                assert_b_term.kind = AX_MIR_TERM_ASSERT;
                assert_b_term.assert.cond.kind = AX_MIR_OP_COPY;
                assert_b_term.assert.cond.place = cond_less_bits_place;
                assert_b_term.assert.expected = true;
                assert_b_term.assert.msg = "shift amount out of range";
                assert_b_term.assert.target = add_bb(b);
                assert_b_term.assert.unwind = add_bb(b);
                set_terminator(b, b->current_bb, assert_b_term);
                b->current_bb = assert_b_term.assert.target;
            } else {
                AxMirLocalId temp_bool = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                AxMirPlace temp_bool_place = { temp_bool, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                
                AxMirStmt ov_stmt = {0};
                ov_stmt.kind = AX_MIR_STMT_ASSIGN;
                ov_stmt.assign.place = temp_bool_place;
                ov_stmt.assign.rvalue.kind = AX_MIR_RVALUE_OVERFLOWS_BINARY_OP;
                ov_stmt.assign.rvalue.binary_op.op = binop;
                ov_stmt.assign.rvalue.binary_op.lhs = lhs;
                ov_stmt.assign.rvalue.binary_op.rhs = rhs;
                push_stmt(b, b->current_bb, ov_stmt);
                
                AxMirLocalId cond_bool = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
                AxMirPlace cond_bool_place = { cond_bool, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                AxMirStmt not_stmt = {0};
                not_stmt.kind = AX_MIR_STMT_ASSIGN;
                not_stmt.assign.place = cond_bool_place;
                not_stmt.assign.rvalue.kind = AX_MIR_RVALUE_UNARY_OP;
                not_stmt.assign.rvalue.unary_op.op = AX_MIR_UNOP_NOT;
                not_stmt.assign.rvalue.unary_op.operand.kind = AX_MIR_OP_COPY;
                not_stmt.assign.rvalue.unary_op.operand.place = temp_bool_place;
                push_stmt(b, b->current_bb, not_stmt);
                
                AxMirTerminator assert_term = {0};
                assert_term.kind = AX_MIR_TERM_ASSERT;
                assert_term.assert.cond.kind = AX_MIR_OP_COPY;
                assert_term.assert.cond.place = cond_bool_place;
                assert_term.assert.expected = true;
                assert_term.assert.msg = "arithmetic overflow";
                assert_term.assert.target = add_bb(b);
                assert_term.assert.unwind = add_bb(b);
                
                set_terminator(b, b->current_bb, assert_term);
                b->current_bb = assert_term.assert.target;
            }
        }
        
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
        stmt.assign.rvalue.binary_op.op = binop;
        stmt.assign.rvalue.binary_op.lhs = lhs;
        stmt.assign.rvalue.binary_op.rhs = rhs;
        push_stmt(b, b->current_bb, stmt);
    } else if (expr->kind == AX_HIR_EXPR_UNARY) {
        AxMirOperand op = build_expr_as_operand(b, expr->unary.expr);
        
        if (expr->unary.op == AX_UNOP_NEG) {
            AxMirOperand zero_op = {0};
            zero_op.kind = AX_MIR_OP_CONST;
            zero_op.constant.ty = get_expr_type(b, expr->unary.expr);
            zero_op.constant.val = 0;
            
            AxMirLocalId overflow_local = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace overflow_place = { overflow_local, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            
            AxMirStmt stmt_overflow = {0};
            stmt_overflow.kind = AX_MIR_STMT_ASSIGN;
            stmt_overflow.assign.place = overflow_place;
            stmt_overflow.assign.rvalue.kind = AX_MIR_RVALUE_OVERFLOWS_BINARY_OP;
            stmt_overflow.assign.rvalue.binary_op.op = AX_MIR_BINOP_SUB;
            stmt_overflow.assign.rvalue.binary_op.lhs = zero_op;
            stmt_overflow.assign.rvalue.binary_op.rhs = op;
            push_stmt(b, b->current_bb, stmt_overflow);
            
            AxMirLocalId cond_bool = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace cond_bool_place = { cond_bool, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt not_stmt = {0};
            not_stmt.kind = AX_MIR_STMT_ASSIGN;
            not_stmt.assign.place = cond_bool_place;
            not_stmt.assign.rvalue.kind = AX_MIR_RVALUE_UNARY_OP;
            not_stmt.assign.rvalue.unary_op.op = AX_MIR_UNOP_NOT;
            not_stmt.assign.rvalue.unary_op.operand.kind = AX_MIR_OP_COPY;
            not_stmt.assign.rvalue.unary_op.operand.place = overflow_place;
            push_stmt(b, b->current_bb, not_stmt);

            AxMirBbId next_bb = add_bb(b);
            
            AxMirTerminator assert_term = {0};
            assert_term.kind = AX_MIR_TERM_ASSERT;
            assert_term.assert.cond.kind = AX_MIR_OP_COPY;
            assert_term.assert.cond.place = cond_bool_place;
            assert_term.assert.expected = true;
            assert_term.assert.msg = "arithmetic overflow";
            assert_term.assert.target = next_bb;
            assert_term.assert.unwind = add_bb(b);
            set_terminator(b, b->current_bb, assert_term);
            
            b->current_bb = next_bb;
        }
        
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_UNARY_OP;
        stmt.assign.rvalue.unary_op.op = expr->unary.op == AX_UNOP_NOT ? AX_MIR_UNOP_NOT : (expr->unary.op == AX_UNOP_BITNOT ? AX_MIR_UNOP_BITNOT : AX_MIR_UNOP_NEG);
        stmt.assign.rvalue.unary_op.operand = op;
        push_stmt(b, b->current_bb, stmt);
    } else if (expr->kind == AX_HIR_EXPR_BLOCK) {
        build_block_into(b, &expr->block.block, dest);
    } else if (expr->kind == AX_HIR_EXPR_IF) {
        AxMirOperand cond = build_expr_as_operand(b, expr->if_expr.cond);
        AxMirBbId bb_then = add_bb(b);
        AxMirBbId bb_else = add_bb(b);
        AxMirBbId bb_end = add_bb(b);
        
        AxMirTerminator switch_term = {0};
        switch_term.kind = AX_MIR_TERM_SWITCH_INT;
        switch_term.switch_int.discr = cond;
        AxMirSwitchTarget *targets = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
        targets[0].value = 0;
        targets[0].target = bb_else;
        switch_term.switch_int.targets.values = targets;
        switch_term.switch_int.targets.count = 1;
        switch_term.switch_int.targets.otherwise = bb_then;
        set_terminator(b, b->current_bb, switch_term);
        
        b->current_bb = bb_then;
        build_block_into(b, &expr->if_expr.block, dest);
        if (!b->bbs[b->current_bb.v].is_terminated) {
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_GOTO;
            term.goto_target = bb_end;
            set_terminator(b, b->current_bb, term);
        }
        
        b->current_bb = bb_else;
        if (expr->if_expr.else_branch) {
            build_expr_into(b, expr->if_expr.else_branch, dest);
        }
        if (!b->bbs[b->current_bb.v].is_terminated) {
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_GOTO;
            term.goto_target = bb_end;
            set_terminator(b, b->current_bb, term);
        }
        
        b->current_bb = bb_end;
    } else if (expr->kind == AX_HIR_EXPR_WHILE) {
        AxMirBbId loop_bb = add_bb(b);
        AxMirBbId exit_bb = add_bb(b);
        
        AxMirTerminator goto_loop = {0};
        goto_loop.kind = AX_MIR_TERM_GOTO;
        goto_loop.goto_target = loop_bb;
        set_terminator(b, b->current_bb, goto_loop);
        
        b->current_bb = loop_bb;
        AxMirOperand cond = build_expr_as_operand(b, expr->while_expr.cond);
        
        AxMirBbId body_bb = add_bb(b);
        
        AxMirTerminator switch_term = {0};
        switch_term.kind = AX_MIR_TERM_SWITCH_INT;
        switch_term.switch_int.discr = cond;
        AxMirSwitchTarget *targets = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
        targets[0].value = 0;
        targets[0].target = exit_bb;
        switch_term.switch_int.targets.values = targets;
        switch_term.switch_int.targets.count = 1;
        switch_term.switch_int.targets.otherwise = body_bb;
        set_terminator(b, b->current_bb, switch_term);
        
        b->current_bb = body_bb;
        
        if (b->loop_count >= b->loop_cap) {
            b->loop_cap = b->loop_cap ? b->loop_cap * 2 : 16;
            b->loops = realloc(b->loops, b->loop_cap * sizeof(LoopContext));
        }
        AxMirPlace void_place = { {0}, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = loop_bb;
        b->loops[b->loop_count].dest = void_place;
        b->loops[b->loop_count].label = expr->while_expr.label;
        b->loop_count++;
        
        build_block_into(b, &expr->while_expr.block, void_place);
        
        if (!b->bbs[b->current_bb.v].is_terminated) {
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_GOTO;
            term.goto_target = loop_bb;
            set_terminator(b, b->current_bb, term);
        }
        
        b->current_bb = exit_bb;
        b->loop_count--;
    } else if (expr->kind == AX_HIR_EXPR_LOOP) {
        AxMirBbId loop_bb = add_bb(b);
        AxMirBbId exit_bb = add_bb(b);
        
        AxMirTerminator goto_loop = {0};
        goto_loop.kind = AX_MIR_TERM_GOTO;
        goto_loop.goto_target = loop_bb;
        set_terminator(b, b->current_bb, goto_loop);
        
        b->current_bb = loop_bb;
        
        if (b->loop_count >= b->loop_cap) {
            b->loop_cap = b->loop_cap ? b->loop_cap * 2 : 16;
            b->loops = realloc(b->loops, b->loop_cap * sizeof(LoopContext));
        }
        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = loop_bb;
        b->loops[b->loop_count].dest = dest;
        b->loops[b->loop_count].label = expr->loop.label;
        b->loop_count++;
        
        build_block_into(b, &expr->loop.block, dest);
        
        if (!b->bbs[b->current_bb.v].is_terminated) {
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_GOTO;
            term.goto_target = loop_bb;
            set_terminator(b, b->current_bb, term);
        }
        
        b->current_bb = exit_bb;
        b->loop_count--;
    } else if (expr->kind == AX_HIR_EXPR_CALL) {
        AxMirOperand callee = build_expr_as_operand(b, expr->call.callee);
        
        size_t arg_count = 0;
        for (const AxHirExpr *arg = expr->call.args; arg; arg = arg->next) arg_count++;
        
        AxMirOperand *args = NULL;
        if (arg_count > 0) {
            args = ax_arena_alloc_array(b->arena, arg_count, sizeof(AxMirOperand), _Alignof(AxMirOperand));
            size_t i = 0;
            for (const AxHirExpr *arg = expr->call.args; arg; arg = arg->next) {
                args[i++] = build_expr_as_operand(b, arg);
            }
        }
        
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_CALL;
        term.call.func = callee;
        term.call.args = args;
        term.call.arg_count = arg_count;
        term.call.destination = dest;
        
        AxMirBbId next_bb = add_bb(b);
        term.call.target = next_bb;
        
        set_terminator(b, b->current_bb, term);
        b->current_bb = next_bb;
    } else if (expr->kind == AX_HIR_EXPR_CAST) {
        AxMirOperand op = build_expr_as_operand(b, expr->cast.expr);
        TypeId dest_ty = get_expr_type(b, expr);
        TypeId src_ty = get_expr_type(b, expr->cast.expr);

        if (TypeId_eq(dest_ty, b->thir->interner.t_char) && TypeId_eq(src_ty, b->thir->interner.t_u32)) {
            // Check if op <= 0x10FFFF && !(0xD800 <= op && op <= 0xDFFF)
            
            // 1. op <= 0x10FFFF
            AxMirLocalId is_le_max = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace le_max_place = { is_le_max, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt le_max_stmt = {0};
            le_max_stmt.kind = AX_MIR_STMT_ASSIGN;
            le_max_stmt.assign.place = le_max_place;
            le_max_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            le_max_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_LE;
            le_max_stmt.assign.rvalue.binary_op.lhs = op;
            AxMirOperand max_char = { AX_MIR_OP_CONST, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0, { .constant = { b->thir->interner.t_u32, 0x10FFFF } } };
            le_max_stmt.assign.rvalue.binary_op.rhs = max_char;
            push_stmt(b, b->current_bb, le_max_stmt);

            AxMirTerminator assert_max = {0};
            assert_max.kind = AX_MIR_TERM_ASSERT;
            assert_max.assert.cond.kind = AX_MIR_OP_COPY;
            assert_max.assert.cond.place = le_max_place;
            assert_max.assert.expected = true;
            assert_max.assert.msg = "invalid char value";
            assert_max.assert.target = add_bb(b);
            assert_max.assert.unwind = add_bb(b);
            set_terminator(b, b->current_bb, assert_max);
            b->current_bb = assert_max.assert.target;

            // 2. !(0xD800 <= op && op <= 0xDFFF) -> !(op >= 0xD800 && op <= 0xDFFF)
            // Or simpler: assert(op < 0xD800 || op > 0xDFFF)
            // Let's do op < 0xD800
            AxMirLocalId is_lt_d800 = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace lt_d800_place = { is_lt_d800, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt lt_d800_stmt = {0};
            lt_d800_stmt.kind = AX_MIR_STMT_ASSIGN;
            lt_d800_stmt.assign.place = lt_d800_place;
            lt_d800_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            lt_d800_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_LT;
            lt_d800_stmt.assign.rvalue.binary_op.lhs = op;
            AxMirOperand c_d800 = { AX_MIR_OP_CONST, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0, { .constant = { b->thir->interner.t_u32, 0xD800 } } };
            lt_d800_stmt.assign.rvalue.binary_op.rhs = c_d800;
            push_stmt(b, b->current_bb, lt_d800_stmt);

            // op > 0xDFFF
            AxMirLocalId is_gt_dfff = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace gt_dfff_place = { is_gt_dfff, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt gt_dfff_stmt = {0};
            gt_dfff_stmt.kind = AX_MIR_STMT_ASSIGN;
            gt_dfff_stmt.assign.place = gt_dfff_place;
            gt_dfff_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            gt_dfff_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_GT;
            gt_dfff_stmt.assign.rvalue.binary_op.lhs = op;
            AxMirOperand c_dfff = { AX_MIR_OP_CONST, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0, { .constant = { b->thir->interner.t_u32, 0xDFFF } } };
            gt_dfff_stmt.assign.rvalue.binary_op.rhs = c_dfff;
            push_stmt(b, b->current_bb, gt_dfff_stmt);

            // lt || gt
            AxMirLocalId is_valid = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace valid_place = { is_valid, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt valid_stmt = {0};
            valid_stmt.kind = AX_MIR_STMT_ASSIGN;
            valid_stmt.assign.place = valid_place;
            valid_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            valid_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_BIT_OR;
            valid_stmt.assign.rvalue.binary_op.lhs = (AxMirOperand){ AX_MIR_OP_COPY, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0, { .place = lt_d800_place } };
            valid_stmt.assign.rvalue.binary_op.rhs = (AxMirOperand){ AX_MIR_OP_COPY, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0, { .place = gt_dfff_place } };
            push_stmt(b, b->current_bb, valid_stmt);

            AxMirTerminator assert_valid = {0};
            assert_valid.kind = AX_MIR_TERM_ASSERT;
            assert_valid.assert.cond.kind = AX_MIR_OP_COPY;
            assert_valid.assert.cond.place = valid_place;
            assert_valid.assert.expected = true;
            assert_valid.assert.msg = "invalid char value";
            assert_valid.assert.target = add_bb(b);
            assert_valid.assert.unwind = add_bb(b);
            set_terminator(b, b->current_bb, assert_valid);
            b->current_bb = assert_valid.assert.target;
        }

        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_CAST;
        stmt.assign.rvalue.cast.kind = AX_MIR_CAST_INT_TO_INT;
        stmt.assign.rvalue.cast.op = op;
        stmt.assign.rvalue.cast.ty = dest_ty;
        push_stmt(b, b->current_bb, stmt);

    } else if (expr->kind == AX_HIR_EXPR_JUMP) {
        if (expr->jump.jump_kind == AX_JUMP_RETURN) {
            if (expr->jump.expr) {
                AxMirPlace ret_place = { {0}, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                build_expr_into(b, expr->jump.expr, ret_place);
            }
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_RETURN;
            set_terminator(b, b->current_bb, term);
        } else if (expr->jump.jump_kind == AX_JUMP_BREAK) {
            LoopContext *target = NULL;
            if (expr->jump.label.v != 0) {
                for (size_t i = b->loop_count; i > 0; i--) {
                    if (b->loops[i-1].label.v == expr->jump.label.v) {
                        target = &b->loops[i-1];
                        break;
                    }
                }
            } else if (b->loop_count > 0) {
                target = &b->loops[b->loop_count - 1];
            }
            if (target) {
                if (expr->jump.expr) {
                    build_expr_into(b, expr->jump.expr, target->dest);
                }
                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = target->break_bb;
                set_terminator(b, b->current_bb, term);
            }
        } else if (expr->jump.jump_kind == AX_JUMP_CONTINUE) {
            LoopContext *target = NULL;
            if (expr->jump.label.v != 0) {
                for (size_t i = b->loop_count; i > 0; i--) {
                    if (b->loops[i-1].label.v == expr->jump.label.v) {
                        target = &b->loops[i-1];
                        break;
                    }
                }
            } else if (b->loop_count > 0) {
                target = &b->loops[b->loop_count - 1];
            }
            if (target) {
                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = target->continue_bb;
                set_terminator(b, b->current_bb, term);
            }
        } else {
            AX_ICE("Unhandled jump kind in MIR builder");
        }
    } else {
        AX_ICE("Unhandled HIR expr kind in MIR builder: %d", expr->kind);
    }
}

static void build_block_into(Builder *b, const AxHirBlock *block, AxMirPlace dest) {
    for (const AxHirStmt *stmt = block->stmts; stmt != NULL; stmt = stmt->next) {
        if (stmt->kind == AX_HIR_STMT_EXPR) {
            if (!stmt->expr_stmt.has_semi && stmt->next == NULL) {
                build_expr_into(b, stmt->expr_stmt.expr, dest);
            } else {
                TypeId ty = get_expr_type(b, stmt->expr_stmt.expr);
                if (ty.v != 0) {
                    AxMirLocalId temp = add_local(b, AX_MIR_LOCAL_TEMP, ty, false);
                    AxMirPlace temp_place = { temp, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    build_expr_into(b, stmt->expr_stmt.expr, temp_place);
                } else {
                    AxMirPlace void_place = { {0}, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    build_expr_into(b, stmt->expr_stmt.expr, void_place);
                }
            }
        } else if (stmt->kind == AX_HIR_STMT_LET) {
            TypeId ty = {0}; // Should compute from let... we'll use expr type
            if (stmt->let.expr) ty = get_expr_type(b, stmt->let.expr);
            
            AxMirLocalId loc = add_local(b, AX_MIR_LOCAL_USER, ty, stmt->let.pat->binding.is_mut);
            if (stmt->let.expr) {
                AxMirPlace p = { loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                build_expr_into(b, stmt->let.expr, p);
            }
            
            if (b->var_count >= b->var_cap) {
                b->var_cap = b->var_cap ? b->var_cap * 2 : 16;
                b->var_map = realloc(b->var_map, b->var_cap * sizeof(*b->var_map));
            }
            b->var_map[b->var_count].sym = stmt->let.pat->binding.symbol;
            b->var_map[b->var_count].loc = loc;
            b->var_count++;
        } else if (stmt->kind == AX_HIR_STMT_ASSIGN) {
            AxMirPlace dest = { {0}, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            if (stmt->assign.left->kind == AX_HIR_EXPR_PATH) {
                AxSymbolId sym = stmt->assign.left->path.path.symbol;
                for (size_t i = 0; i < b->var_count; i++) {
                    if (b->var_map[i].sym.v == sym.v) {
                        dest.local = b->var_map[i].loc;
                        break;
                    }
                }
            } else {
                AX_ICE("builder: unhandled assignment left hand side kind");
            }
            build_expr_into(b, stmt->assign.right, dest);
        }
    }
}

AxMirBody *ax_mir_build(const AxHirItem *func, const AxThir *thir, AxArena *arena) {
    if (!func || func->kind != AX_HIR_ITEM_FN) return NULL;
    
    Builder b = {0};
    b.arena = arena;
    b.thir = thir;
    
    TypeId func_ty = {0};
    const TypeId *fty = AxItemTypeMap_get(&thir->item_types, func);
    if (fty) func_ty = *fty;
    
    TypeId ret_ty = {0};
    if (func_ty.v != 0) {
        const AxType *ty_info = ax_type_get(&thir->interner, func_ty);
        if (ty_info && ty_info->kind == AX_TY_FN) {
            ret_ty = ty_info->fn.ret_type;
        }
    }
    
    add_local(&b, AX_MIR_LOCAL_RETURN, ret_ty, true);
    
    for (const AxHirParam *p = func->fn.params; p != NULL; p = p->next) {
        TypeId pty = {0};
        const TypeId *pty_ptr = AxParamTypeMap_get(&thir->param_types, p);
        if (pty_ptr) pty = *pty_ptr;
        AxMirLocalId loc = add_local(&b, AX_MIR_LOCAL_USER, pty, p->is_mut);
        if (b.var_count >= b.var_cap) {
            b.var_cap = b.var_cap ? b.var_cap * 2 : 16;
            b.var_map = realloc(b.var_map, b.var_cap * sizeof(*b.var_map));
        }
        b.var_map[b.var_count].sym = p->symbol;
        b.var_map[b.var_count].loc = loc;
        b.var_count++;
    }
    
    b.current_bb = add_bb(&b);
    
    AxMirPlace ret_place = { {0}, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
    build_block_into(&b, func->fn.body, ret_place);
    
    if (!b.bbs[b.current_bb.v].is_terminated) {
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_RETURN;
        set_terminator(&b, b.current_bb, term);
    }
    
    AxMirBody *body = AX_ARENA_NEW(arena, AxMirBody);
    body->arena = *arena;
    body->local_count = b.local_count;
    body->locals = AX_ARENA_NEW_ARRAY(arena, AxMirLocalDecl, b.local_count);
    memcpy(body->locals, b.locals, b.local_count * sizeof(AxMirLocalDecl));
    
    body->bb_count = b.bb_count;
    body->bbs = AX_ARENA_NEW_ARRAY(arena, AxMirBb, b.bb_count);
    for (size_t i = 0; i < b.bb_count; i++) {
        body->bbs[i].stmt_count = b.bbs[i].stmt_count;
        if (b.bbs[i].stmt_count > 0) {
            body->bbs[i].stmts = AX_ARENA_NEW_ARRAY(arena, AxMirStmt, b.bbs[i].stmt_count);
            memcpy(body->bbs[i].stmts, b.bbs[i].stmts, b.bbs[i].stmt_count * sizeof(AxMirStmt));
        } else {
            body->bbs[i].stmts = NULL;
        }
        body->bbs[i].terminator = b.bbs[i].terminator;
        free(b.bbs[i].stmts);
    }
    
    free(b.locals);
    free(b.bbs);
    free(b.var_map);
    free(b.loops);
    
    return body;
}
