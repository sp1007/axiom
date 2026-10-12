
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



typedef struct DropNode {
    AxMirPlace place;
    AxLocation location;
    bool is_temp;
    struct DropNode *next;
} DropNode;

typedef struct LoopContext {
    AxMirBbId break_bb;
    AxMirBbId continue_bb;
    AxMirPlace dest;
    StrId label;
    DropNode *drop_scope;
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
    
    AxLocation current_span;
    
    struct {
        AxSymbolId sym;
        AxMirLocalId loc;
    } *var_map;
    size_t var_count;
    size_t var_cap;
    DropNode *current_drops;
} Builder;

static void push_drop(Builder *b, AxMirPlace place, TypeId ty, bool is_temp);
static bool type_needs_drop(Builder *b, TypeId ty);
static AxMirBbId build_drop_chain(Builder *b, AxMirBbId current_bb, DropNode *from, DropNode *to, AxMirBbId target_bb, AxLocation loc);
static AxMirBbId build_pat_match_inner(Builder *b, AxMirBbId current_bb, AxMirPlace place, const AxHirPat *pat, AxMirBbId bb_fail);
static AxMirBbId build_pat_match(Builder *b, AxMirBbId current_bb, AxMirPlace place, const AxHirPat *pat, AxMirBbId bb_fail);
static void build_expr_into_inner(Builder *b, const AxHirExpr *expr, AxMirPlace dest);
static void build_expr_into(Builder *b, const AxHirExpr *expr, AxMirPlace dest);
static AxMirOperand build_expr_as_operand_inner(Builder *b, const AxHirExpr *expr);
static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr);
static void build_block_into_inner(Builder *b, const AxHirBlock *block, AxMirPlace dest);
static void build_block_into(Builder *b, const AxHirBlock *block, AxMirPlace dest);

static AxMirLocalId add_local(Builder *b, AxMirLocalKind kind, TypeId ty, bool mut) {
    if (b->local_count >= b->local_cap) {
        b->local_cap = b->local_cap ? b->local_cap * 2 : 16;
        b->locals = realloc(b->locals, b->local_cap * sizeof(AxMirLocalDecl));
    }
    AxMirLocalId id = { (uint32_t)b->local_count++ };
    b->locals[id.v].kind = kind;
    b->locals[id.v].ty = ty;
    b->locals[id.v].mut = mut;
    b->locals[id.v].location = b->current_span;
    if (kind == AX_MIR_LOCAL_USER || kind == AX_MIR_LOCAL_TEMP) {
        AxMirPlace place = { id, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        push_drop(b, place, ty, kind == AX_MIR_LOCAL_TEMP);
    }
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


static void consume_local(Builder *b, AxMirPlace place) {
    if (place.proj_count > 0) return;
    DropNode **curr = &b->current_drops;
    while (*curr) {
        if ((*curr)->place.local.v == place.local.v && (*curr)->is_temp) {
            *curr = (*curr)->next;
            break;
        }
        curr = &(*curr)->next;
    }
}

static void consume_op(Builder *b, const AxMirOperand *op) {
    if (op->kind == AX_MIR_OP_MOVE) {
        consume_local(b, op->place);
    }
}

static void push_stmt(Builder *b, AxMirBbId bb, AxMirStmt stmt) {
    if (stmt.kind == AX_MIR_STMT_ASSIGN) {
        if (stmt.assign.rvalue.kind == AX_MIR_RVALUE_USE) {
            consume_op(b, &stmt.assign.rvalue.use);
        } else if (stmt.assign.rvalue.kind == AX_MIR_RVALUE_CAST) {
            consume_op(b, &stmt.assign.rvalue.cast.op);
        } else if (stmt.assign.rvalue.kind == AX_MIR_RVALUE_UNARY_OP) {
            consume_op(b, &stmt.assign.rvalue.unary_op.operand);
        } else if (stmt.assign.rvalue.kind == AX_MIR_RVALUE_BINARY_OP) {
            consume_op(b, &stmt.assign.rvalue.binary_op.lhs);
            consume_op(b, &stmt.assign.rvalue.binary_op.rhs);
        } else if (stmt.assign.rvalue.kind == AX_MIR_RVALUE_AGGREGATE) {
            for (size_t i = 0; i < stmt.assign.rvalue.aggregate.operand_count; i++) {
                consume_op(b, &stmt.assign.rvalue.aggregate.operands[i]);
            }
        }
    }

    BbData *d = &b->bbs[bb.v];
    stmt.location = b->current_span;
    if (d->stmt_count >= d->stmt_cap) {
        d->stmt_cap = d->stmt_cap ? d->stmt_cap * 2 : 8;
        d->stmts = realloc(d->stmts, d->stmt_cap * sizeof(AxMirStmt));
    }
    d->stmts[d->stmt_count++] = stmt;
}

static void set_terminator(Builder *b, AxMirBbId bb, AxMirTerminator term) {
    if (term.kind == AX_MIR_TERM_CALL) {
        consume_op(b, &term.call.func);
        for (size_t i = 0; i < term.call.arg_count; i++) {
            consume_op(b, &term.call.args[i]);
        }
    } else if (term.kind == AX_MIR_TERM_ASSERT) {
        consume_op(b, &term.assert.cond);
    } else if (term.kind == AX_MIR_TERM_SWITCH_INT) {
        consume_op(b, &term.switch_int.discr);
    }

    BbData *d = &b->bbs[bb.v];
    term.location = b->current_span;
    if (!d->is_terminated) {
        d->terminator = term;
        d->is_terminated = true;
    }
}


static bool type_needs_drop(Builder *b, TypeId ty) {
    const AxType *t = ax_type_get(&b->thir->interner, ty);
    if (!t) return false;
    if (t->kind == AX_TY_STRUCT) {
        if (t->strct.def->struct_decl.struct_fields == NULL) return true;
        for (size_t i = 0; i < t->strct.field_count; i++) {
            if (type_needs_drop(b, t->strct.fields[i])) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_TUPLE) {
        for (size_t i = 0; i < t->tuple.field_count; i++) {
            if (type_needs_drop(b, t->tuple.fields[i])) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_ENUM) {
        for (size_t v = 0; v < t->enm.variant_count; v++) {
            for (size_t i = 0; i < t->enm.variant_field_counts[v]; i++) {
                if (type_needs_drop(b, t->enm.variant_fields[v][i])) return true;
            }
        }
        return false;
    }

    return false;
}

static void push_drop(Builder *b, AxMirPlace place, TypeId ty, bool is_temp) {
    if (type_needs_drop(b, ty)) {
        DropNode *node = ax_arena_alloc_array(b->arena, 1, sizeof(DropNode), _Alignof(DropNode));
        node->place = place;
        node->location = b->current_span;
        node->is_temp = is_temp;
        node->next = b->current_drops;
        b->current_drops = node;
    }
}

static AxMirBbId build_drop_chain(Builder *b, AxMirBbId current_bb, DropNode *from, DropNode *to, AxMirBbId target_bb, AxLocation loc) {
    DropNode *curr = from;
    while (curr != to) {
        AxMirBbId next_bb = add_bb(b);
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_DROP;
        term.location = loc;
        term.drop.place = curr->place;
        term.drop.target = next_bb;
        term.drop.unwind = (AxMirBbId){0};
        set_terminator(b, current_bb, term);
        current_bb = next_bb;
        curr = curr->next;
    }
    if (target_bb.v != 0) {
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_GOTO;
        term.goto_target = target_bb;
        term.location = loc;
        set_terminator(b, current_bb, term);
    }
    return current_bb;
}
static TypeId get_expr_type(Builder *b, const AxHirExpr *expr) {
    TypeId ty = {0};
    const TypeId *res = AxExprTypeMap_get(&b->thir->expr_types, expr);
    if (res) return *res;
    return ty;
}

static TypeId get_pat_type(Builder *b, const struct AxHirPat *pat) {
    TypeId ty = {0};
    const TypeId *res = AxPatTypeMap_get(&b->thir->pat_types, pat);
    if (res) return *res;
    return ty;
}


static void declare_pat_locals(Builder *b, const AxHirPat *pat, TypeId ty) {
    if (!pat) return;
    switch (pat->kind) {
        case AX_HIR_PAT_BINDING: {
            AxMirLocalId loc = add_local(b, AX_MIR_LOCAL_USER, ty, pat->binding.is_mut);
            if (b->var_count >= b->var_cap) {
                b->var_cap = b->var_cap ? b->var_cap * 2 : 16;
                b->var_map = realloc(b->var_map, b->var_cap * sizeof(*b->var_map));
            }
            b->var_map[b->var_count].sym = pat->binding.symbol;
            b->var_map[b->var_count].loc = loc;
            b->var_count++;
            break;
        }
        case AX_HIR_PAT_TUPLE: {
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            if (t->kind != AX_TY_TUPLE) break;
            size_t i = 0;
            for (const AxHirPat *p = pat->tuple.elems; p; p = p->next, i++) {
                if (i < t->tuple.field_count) {
                    declare_pat_locals(b, p, t->tuple.fields[i]);
                }
            }
            break;
        }
        case AX_HIR_PAT_STRUCT: {
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            if (t->kind == AX_TY_STRUCT) {
                for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                    size_t idx = 0;
                    for (const AxHirFieldDecl *fd = t->strct.def->struct_decl.struct_fields; fd; fd = fd->next, idx++) {
                        if (fd->name.v == pf->name.v) break;
                    }
                    if (idx < t->strct.field_count) {
                        declare_pat_locals(b, pf->pat, t->strct.fields[idx]);
                    }
                }
            } else if (t->kind == AX_TY_ENUM && t->enm.variant_count == 1) {
                for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                    size_t idx = 0;
                    const AxHirVariantDecl *vd = t->enm.def->enum_decl.variants;
                    for (const AxHirFieldDecl *fd = vd->struct_fields; fd; fd = fd->next, idx++) {
                        if (fd->name.v == pf->name.v) break;
                    }
                    if (idx < t->enm.variant_field_counts[0]) {
                        declare_pat_locals(b, pf->pat, t->enm.variant_fields[0][idx]);
                    }
                }
            }
            break;
        }
        case AX_HIR_PAT_PATH: {
            if (pat->path.payload) {
                const AxType *t = ax_type_get(&b->thir->interner, ty);
                if (t->kind == AX_TY_ENUM && t->enm.variant_count == 1) {
                    if (pat->path.payload->kind == AX_HIR_PAT_TUPLE) {
                        size_t idx = 0;
                        for (const AxHirPat *p = pat->path.payload->tuple.elems; p; p = p->next, idx++) {
                            if (idx < t->enm.variant_field_counts[0]) {
                                declare_pat_locals(b, p, t->enm.variant_fields[0][idx]);
                            }
                        }
                    }
                }
            }
            break;
        }
        case AX_HIR_PAT_WILDCARD:
        default:
            break;
    }
}

static AxMirBbId build_pat_match_inner(Builder *b, AxMirBbId current_bb, AxMirPlace place, const AxHirPat *pat, AxMirBbId bb_fail) {
    if (!pat) return current_bb;
    
    switch (pat->kind) {
        case AX_HIR_PAT_WILDCARD:
            return current_bb;
            
        case AX_HIR_PAT_BINDING: {
            TypeId ty = get_pat_type(b, pat);
            AxMirLocalId loc = add_local(b, AX_MIR_LOCAL_USER, ty, pat->binding.is_mut);
            if (b->var_count >= b->var_cap) {
                b->var_cap = b->var_cap ? b->var_cap * 2 : 16;
                b->var_map = realloc(b->var_map, b->var_cap * sizeof(*b->var_map));
            }
            b->var_map[b->var_count].sym = pat->binding.symbol;
            b->var_map[b->var_count].loc = loc;
            b->var_count++;
            
            AxMirStmt stmt = {0};
            stmt.kind = AX_MIR_STMT_ASSIGN;
            stmt.assign.place.local = loc;
            stmt.assign.rvalue.kind = AX_MIR_RVALUE_USE;
            
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            bool is_copy = true;
            if (t && (t->kind == AX_TY_STR || t->kind == AX_TY_ARRAY)) {
                is_copy = false;
            }
            stmt.assign.rvalue.use.kind = is_copy ? AX_MIR_OP_COPY : AX_MIR_OP_MOVE;
            
            stmt.assign.rvalue.use.place = place;
            push_stmt(b, current_bb, stmt);
            return current_bb;
        }
        
        case AX_HIR_PAT_LITERAL: {
            AxMirOperand const_op = {0};
            const_op.kind = AX_MIR_OP_CONST;
            const_op.constant.ty = get_pat_type(b, pat);
            const_op.constant.kind = AX_MIR_CONST_INT;
            if (pat->literal.tok.kind == AX_TOK_KW_TRUE) const_op.constant.val = 1;
            else if (pat->literal.tok.kind == AX_TOK_KW_FALSE) const_op.constant.val = 0;
            else if (pat->literal.tok.kind == AX_TOK_INT || pat->literal.tok.kind == AX_TOK_CHAR) {
                const_op.constant.val = pat->literal.tok.val.int_val.value;
            }
            if (pat->literal.is_negated) const_op.constant.val = -(int64_t)const_op.constant.val;
            
            AxMirLocalId cmp_loc = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace cmp_place = { cmp_loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            
            AxMirStmt stmt = {0};
            stmt.kind = AX_MIR_STMT_ASSIGN;
            stmt.assign.place = cmp_place;
            stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_EQ;
            stmt.assign.rvalue.binary_op.lhs.kind = AX_MIR_OP_COPY;
            stmt.assign.rvalue.binary_op.lhs.place = place;
            stmt.assign.rvalue.binary_op.rhs = const_op;
            push_stmt(b, current_bb, stmt);
            
            AxMirBbId bb_succ = add_bb(b);
            AxMirTerminator switch_term = {0};
            switch_term.kind = AX_MIR_TERM_SWITCH_INT;
            switch_term.switch_int.discr.kind = AX_MIR_OP_COPY;
            switch_term.switch_int.discr.place = cmp_place;
            AxMirSwitchTarget *targets = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
            targets[0].value = 0;
            targets[0].target = bb_fail;
            switch_term.switch_int.targets.values = targets;
            switch_term.switch_int.targets.count = 1;
            switch_term.switch_int.targets.otherwise = bb_succ;
            set_terminator(b, current_bb, switch_term);
            
            return bb_succ;
        }
        
        case AX_HIR_PAT_RANGE: {
            AxMirConst start_c = {0}, end_c = {0};
            start_c.ty = get_pat_type(b, pat->range.start);
            end_c.ty = get_pat_type(b, pat->range.end);
            
            if (pat->range.start->kind == AX_HIR_PAT_LITERAL) {
                if (pat->range.start->literal.tok.kind == AX_TOK_INT || pat->range.start->literal.tok.kind == AX_TOK_CHAR) {
                    start_c.val = pat->range.start->literal.tok.val.int_val.value;
                }
                if (pat->range.start->literal.is_negated) start_c.val = -(int64_t)start_c.val;
            }
            if (pat->range.end->kind == AX_HIR_PAT_LITERAL) {
                if (pat->range.end->literal.tok.kind == AX_TOK_INT || pat->range.end->literal.tok.kind == AX_TOK_CHAR) {
                    end_c.val = pat->range.end->literal.tok.val.int_val.value;
                }
                if (pat->range.end->literal.is_negated) end_c.val = -(int64_t)end_c.val;
            }
            
            AxMirLocalId cmp1_loc = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace cmp1_place = { cmp1_loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt stmt1 = {0};
            stmt1.kind = AX_MIR_STMT_ASSIGN;
            stmt1.assign.place = cmp1_place;
            stmt1.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            stmt1.assign.rvalue.binary_op.op = AX_MIR_BINOP_GE;
            stmt1.assign.rvalue.binary_op.lhs.kind = AX_MIR_OP_COPY;
            stmt1.assign.rvalue.binary_op.lhs.place = place;
            stmt1.assign.rvalue.binary_op.rhs.kind = AX_MIR_OP_CONST;
            stmt1.assign.rvalue.binary_op.rhs.constant = start_c;
            push_stmt(b, current_bb, stmt1);
            
            AxMirBbId bb_check_end = add_bb(b);
            AxMirTerminator switch1 = {0};
            switch1.kind = AX_MIR_TERM_SWITCH_INT;
            switch1.switch_int.discr.kind = AX_MIR_OP_COPY;
            switch1.switch_int.discr.place = cmp1_place;
            AxMirSwitchTarget *targets1 = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
            targets1[0].value = 0;
            targets1[0].target = bb_fail;
            switch1.switch_int.targets.values = targets1;
            switch1.switch_int.targets.count = 1;
            switch1.switch_int.targets.otherwise = bb_check_end;
            set_terminator(b, current_bb, switch1);
            
            current_bb = bb_check_end;
            AxMirLocalId cmp2_loc = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace cmp2_place = { cmp2_loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt stmt2 = {0};
            stmt2.kind = AX_MIR_STMT_ASSIGN;
            stmt2.assign.place = cmp2_place;
            stmt2.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            stmt2.assign.rvalue.binary_op.op = pat->range.is_inclusive ? AX_MIR_BINOP_LE : AX_MIR_BINOP_LT;
            stmt2.assign.rvalue.binary_op.lhs.kind = AX_MIR_OP_COPY;
            stmt2.assign.rvalue.binary_op.lhs.place = place;
            stmt2.assign.rvalue.binary_op.rhs.kind = AX_MIR_OP_CONST;
            stmt2.assign.rvalue.binary_op.rhs.constant = end_c;
            push_stmt(b, current_bb, stmt2);
            
            AxMirBbId bb_succ = add_bb(b);
            AxMirTerminator switch2 = {0};
            switch2.kind = AX_MIR_TERM_SWITCH_INT;
            switch2.switch_int.discr.kind = AX_MIR_OP_COPY;
            switch2.switch_int.discr.place = cmp2_place;
            AxMirSwitchTarget *targets2 = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
            targets2[0].value = 0;
            targets2[0].target = bb_fail;
            switch2.switch_int.targets.values = targets2;
            switch2.switch_int.targets.count = 1;
            switch2.switch_int.targets.otherwise = bb_succ;
            set_terminator(b, current_bb, switch2);
            
            return bb_succ;
        }
        
        case AX_HIR_PAT_OR: {
            AxMirBbId bb_succ = add_bb(b);
            const AxHirPat *p = pat->or_pat.pats;
            while (p) {
                AxMirBbId next_or = p->next ? add_bb(b) : bb_fail;
                AxMirBbId succ = build_pat_match(b, current_bb, place, p, next_or);
                
                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = bb_succ;
                set_terminator(b, succ, term);
                
                current_bb = next_or;
                p = p->next;
            }
            return bb_succ;
        }
        
        case AX_HIR_PAT_PATH:
        case AX_HIR_PAT_STRUCT:
        case AX_HIR_PAT_TUPLE: {
            TypeId ty = get_pat_type(b, pat);
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            
            if (t->kind == AX_TY_ENUM) {
                uint32_t *vidx = AxPatVariantMap_get(&b->thir->pat_variants, pat);
                if (!vidx) return bb_fail;
                
                AxMirLocalId discr_loc = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_u32, false);
                AxMirPlace discr_place = { discr_loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                
                AxMirStmt stmt = {0};
                stmt.kind = AX_MIR_STMT_ASSIGN;
                stmt.assign.place = discr_place;
                stmt.assign.rvalue.kind = AX_MIR_RVALUE_DISCRIMINANT;
                stmt.assign.rvalue.discriminant = place;
                push_stmt(b, current_bb, stmt);
                
                AxMirBbId bb_succ = add_bb(b);
                AxMirTerminator switch_term = {0};
                switch_term.kind = AX_MIR_TERM_SWITCH_INT;
                switch_term.switch_int.discr.kind = AX_MIR_OP_COPY;
                switch_term.switch_int.discr.place = discr_place;
                AxMirSwitchTarget *targets = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
                targets[0].value = *vidx;
                targets[0].target = bb_succ;
                switch_term.switch_int.targets.values = targets;
                switch_term.switch_int.targets.count = 1;
                switch_term.switch_int.targets.otherwise = bb_fail;
                set_terminator(b, current_bb, switch_term);
                
                current_bb = bb_succ;
                
                if (pat->kind == AX_HIR_PAT_STRUCT) {
                    const AxHirVariantDecl *vd = t->enm.def->enum_decl.variants;
                    for (uint32_t i = 0; i < *vidx && vd; i++) vd = vd->next;
                    
                    for (const AxHirPatField *f = pat->struct_pat.fields; f; f = f->next) {
                        size_t idx = 0;
                        for (const AxHirFieldDecl *fd = vd->struct_fields; fd; fd = fd->next, idx++) {
                            if (fd->name.v == f->name.v) break;
                        }
                        AxMirPlace field_place = place;
                        AxMirProjection *projs = ax_arena_alloc_array(b->arena, field_place.proj_count + 2, sizeof(AxMirProjection), _Alignof(AxMirProjection));
                        for (size_t i = 0; i < field_place.proj_count; i++) projs[i] = field_place.projs[i];
                        projs[field_place.proj_count].kind = AX_MIR_PROJ_DOWNCAST;
                        projs[field_place.proj_count].variant_idx = *vidx;
                        projs[field_place.proj_count + 1].kind = AX_MIR_PROJ_FIELD;
                        projs[field_place.proj_count + 1].field_idx = idx;
                        field_place.projs = projs;
                        field_place.proj_count += 2;
                        
                        current_bb = build_pat_match(b, current_bb, field_place, f->pat, bb_fail);
                    }
                } else if (pat->kind == AX_HIR_PAT_PATH && pat->path.payload) {
                    if (pat->path.payload->kind == AX_HIR_PAT_TUPLE) {
                        size_t idx = 0;
                        for (const AxHirPat *p = pat->path.payload->tuple.elems; p; p = p->next, idx++) {
                            AxMirPlace field_place = place;
                            AxMirProjection *projs = ax_arena_alloc_array(b->arena, field_place.proj_count + 2, sizeof(AxMirProjection), _Alignof(AxMirProjection));
                            for (size_t i = 0; i < field_place.proj_count; i++) projs[i] = field_place.projs[i];
                            projs[field_place.proj_count].kind = AX_MIR_PROJ_DOWNCAST;
                            projs[field_place.proj_count].variant_idx = *vidx;
                            projs[field_place.proj_count + 1].kind = AX_MIR_PROJ_FIELD;
                            projs[field_place.proj_count + 1].field_idx = idx;
                            field_place.projs = projs;
                            field_place.proj_count += 2;
                            
                            current_bb = build_pat_match(b, current_bb, field_place, p, bb_fail);
                        }
                    }
                }
            } else if (t->kind == AX_TY_STRUCT) {
                if (pat->kind == AX_HIR_PAT_STRUCT) {
                    for (const AxHirPatField *f = pat->struct_pat.fields; f; f = f->next) {
                        size_t idx = 0;
                        for (const AxHirFieldDecl *fd = t->strct.def->struct_decl.struct_fields; fd; fd = fd->next, idx++) {
                            if (fd->name.v == f->name.v) break;
                        }
                        AxMirPlace field_place = place;
                        AxMirProjection *projs = ax_arena_alloc_array(b->arena, field_place.proj_count + 1, sizeof(AxMirProjection), _Alignof(AxMirProjection));
                        for (size_t i = 0; i < field_place.proj_count; i++) projs[i] = field_place.projs[i];
                        projs[field_place.proj_count].kind = AX_MIR_PROJ_FIELD;
                        projs[field_place.proj_count].field_idx = idx;
                        field_place.projs = projs;
                        field_place.proj_count += 1;
                        
                        current_bb = build_pat_match(b, current_bb, field_place, f->pat, bb_fail);
                    }
                } else if (pat->kind == AX_HIR_PAT_TUPLE) { // Tuple struct
                    size_t idx = 0;
                    for (const AxHirPat *p = pat->tuple.elems; p; p = p->next, idx++) {
                        AxMirPlace field_place = place;
                        AxMirProjection *projs = ax_arena_alloc_array(b->arena, field_place.proj_count + 1, sizeof(AxMirProjection), _Alignof(AxMirProjection));
                        for (size_t i = 0; i < field_place.proj_count; i++) projs[i] = field_place.projs[i];
                        projs[field_place.proj_count].kind = AX_MIR_PROJ_FIELD;
                        projs[field_place.proj_count].field_idx = idx;
                        field_place.projs = projs;
                        field_place.proj_count += 1;
                        
                        current_bb = build_pat_match(b, current_bb, field_place, p, bb_fail);
                    }
                }
            } else if (t->kind == AX_TY_TUPLE) {
                size_t idx = 0;
                for (const AxHirPat *p = pat->tuple.elems; p; p = p->next, idx++) {
                    AxMirPlace field_place = place;
                    AxMirProjection *projs = ax_arena_alloc_array(b->arena, field_place.proj_count + 1, sizeof(AxMirProjection), _Alignof(AxMirProjection));
                    for (size_t i = 0; i < field_place.proj_count; i++) projs[i] = field_place.projs[i];
                    projs[field_place.proj_count].kind = AX_MIR_PROJ_FIELD;
                    projs[field_place.proj_count].field_idx = idx;
                    field_place.projs = projs;
                    field_place.proj_count += 1;
                    
                    current_bb = build_pat_match(b, current_bb, field_place, p, bb_fail);
                }
            }
            return current_bb;
        }
        
        default:
            return current_bb;
    }
}

static void build_expr_into(Builder *b, const AxHirExpr *expr, AxMirPlace dest);

static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr);
static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr);
static AxMirPlace build_place(Builder *b, const AxHirExpr *expr) {
    if (expr->kind == AX_HIR_EXPR_PATH) {
        AxSymbolId sym = expr->path.path.symbol;
        for (size_t i = 0; i < b->var_count; i++) {
            if (b->var_map[i].sym.v == sym.v) {
                AxMirPlace p = { b->var_map[i].loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                return p;
            }
        }
    } else if (expr->kind == AX_HIR_EXPR_FIELD) {
        AxMirPlace base = build_place(b, expr->field.base);
        TypeId base_ty = *AxExprTypeMap_get(&b->thir->expr_types, expr->field.base);
        const AxType *t = ax_type_get(&b->thir->interner, base_ty);
        uint32_t idx = 0;
        if (t->kind == AX_TY_STRUCT) {
            for (const AxHirFieldDecl *fd = t->strct.def->struct_decl.struct_fields; fd; fd = fd->next, idx++) {
                if (fd->name.v == expr->field.name.v) break;
            }
        }
        
        AxMirProjection *projs = ax_arena_alloc(b->arena, sizeof(AxMirProjection) * (base.proj_count + 1), _Alignof(AxMirProjection));
        for (size_t i = 0; i < base.proj_count; i++) projs[i] = base.projs[i];
        projs[base.proj_count].kind = AX_MIR_PROJ_FIELD;
        projs[base.proj_count].field_idx = idx;
        
        base.projs = projs;
        base.proj_count++;
        return base;
        } else if (expr->kind == AX_HIR_EXPR_TUPLE_INDEX) {
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
        
        bool is_range = expr->index.arg->kind == AX_HIR_EXPR_RANGE;
        
        if (is_range) {
            AxMirLocalId start_local = {0}, end_local = {0};
            bool has_start = expr->index.arg->range.start != NULL;
            bool has_end = expr->index.arg->range.end != NULL;
            
            if (has_start) {
                AxMirOperand start_op = build_expr_as_operand(b, expr->index.arg->range.start);
                if ((start_op.kind == AX_MIR_OP_COPY || start_op.kind == AX_MIR_OP_MOVE) && start_op.place.proj_count == 0) {
                    start_local = start_op.place.local;
                } else {
                    TypeId start_ty = get_expr_type(b, expr->index.arg->range.start);
                    start_local = add_local(b, AX_MIR_LOCAL_TEMP, start_ty, false);
                    AxMirPlace temp_place = { start_local, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    AxMirStmt stmt = {0};
                    stmt.kind = AX_MIR_STMT_ASSIGN;
                    stmt.assign.place = temp_place;
                    stmt.assign.rvalue.kind = AX_MIR_RVALUE_USE;
                    stmt.assign.rvalue.use = start_op;
                    push_stmt(b, b->current_bb, stmt);
                }
            }
            
            if (has_end) {
                AxMirOperand end_op = build_expr_as_operand(b, expr->index.arg->range.end);
                if ((end_op.kind == AX_MIR_OP_COPY || end_op.kind == AX_MIR_OP_MOVE) && end_op.place.proj_count == 0) {
                    end_local = end_op.place.local;
                } else {
                    TypeId end_ty = get_expr_type(b, expr->index.arg->range.end);
                    end_local = add_local(b, AX_MIR_LOCAL_TEMP, end_ty, false);
                    AxMirPlace temp_place = { end_local, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                    AxMirStmt stmt = {0};
                    stmt.kind = AX_MIR_STMT_ASSIGN;
                    stmt.assign.place = temp_place;
                    stmt.assign.rvalue.kind = AX_MIR_RVALUE_USE;
                    stmt.assign.rvalue.use = end_op;
                    push_stmt(b, b->current_bb, stmt);
                }
            }
            
            // Note: Bounds checking for slices is done in runtime lib or we can emit MIR asserts here
            // The task implies "with checked bounds"
            
            TypeId base_ty = get_expr_type(b, expr->index.base);
            const AxType *t = ax_type_get(&b->thir->interner, base_ty);
            bool is_slice_view = (t && (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) && ax_type_get(&b->thir->interner, t->view.pointee)->kind == AX_TY_SLICE);
            
            size_t new_proj_count = base.proj_count + 1;
            if (is_slice_view) new_proj_count++;
            AxMirProjection *projs = ax_arena_alloc(b->arena, sizeof(AxMirProjection) * new_proj_count, _Alignof(AxMirProjection));
            for (size_t i = 0; i < base.proj_count; i++) projs[i] = base.projs[i];
            
            size_t pi = base.proj_count;
            if (is_slice_view) {
                projs[pi].kind = AX_MIR_PROJ_DEREF;
                pi++;
            }
            projs[pi].kind = AX_MIR_PROJ_SUB_SLICE;
            projs[pi].sub_slice.from_local = start_local;
            projs[pi].sub_slice.to_local = end_local;
            projs[pi].sub_slice.has_from = has_start;
            projs[pi].sub_slice.has_to = has_end;
            
            base.projs = projs;
            base.proj_count = new_proj_count;
            return base;
        }

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
        
        TypeId base_ty = get_expr_type(b, expr->index.base);
        const AxType *t = ax_type_get(&b->thir->interner, base_ty);
        if (t && t->kind == AX_TY_ARRAY) {
            uint64_t len = t->array.len;
            
            AxMirLocalId cond_local = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_bool, false);
            AxMirPlace cond_place = { cond_local, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt cmp_stmt = {0};
            cmp_stmt.kind = AX_MIR_STMT_ASSIGN;
            cmp_stmt.assign.place = cond_place;
            cmp_stmt.assign.rvalue.kind = AX_MIR_RVALUE_BINARY_OP;
            cmp_stmt.assign.rvalue.binary_op.op = AX_MIR_BINOP_LT;
            
            AxMirLocalId u_idx = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_usize, false);
            AxMirPlace u_idx_place = { u_idx, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            AxMirStmt cast_stmt = {0};
            cast_stmt.kind = AX_MIR_STMT_ASSIGN;
            cast_stmt.assign.place = u_idx_place;
            cast_stmt.assign.rvalue.kind = AX_MIR_RVALUE_CAST;
            cast_stmt.assign.rvalue.cast.op = (AxMirOperand){ .kind = AX_MIR_OP_COPY, .place = { idx_local, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 } };
            cast_stmt.assign.rvalue.cast.ty = b->thir->interner.t_usize;
            push_stmt(b, b->current_bb, cast_stmt);
            
            cmp_stmt.assign.rvalue.binary_op.lhs = (AxMirOperand){ .kind = AX_MIR_OP_COPY, .place = u_idx_place };
            cmp_stmt.assign.rvalue.binary_op.rhs = (AxMirOperand){ .kind = AX_MIR_OP_CONST, .constant = { .ty = b->thir->interner.t_usize, .kind = AX_MIR_CONST_INT, .val = len } };
            push_stmt(b, b->current_bb, cmp_stmt);
            
            AxMirTerminator assert_term = {0};
            assert_term.kind = AX_MIR_TERM_ASSERT;
            assert_term.assert.cond = (AxMirOperand){ .kind = AX_MIR_OP_COPY, .place = cond_place };
            assert_term.assert.expected = true;
            assert_term.assert.msg = "index out of bounds";
            assert_term.assert.target = add_bb(b);
            assert_term.assert.unwind = add_bb(b);
            set_terminator(b, b->current_bb, assert_term);
            b->current_bb = assert_term.assert.target;
        }
        
        bool is_slice_view = (t && (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) && ax_type_get(&b->thir->interner, t->view.pointee)->kind == AX_TY_SLICE);
        
        size_t new_proj_count = base.proj_count + 1;
        if (is_slice_view) new_proj_count++;
        AxMirProjection *projs = ax_arena_alloc(b->arena, sizeof(AxMirProjection) * new_proj_count, _Alignof(AxMirProjection));
        for (size_t i = 0; i < base.proj_count; i++) projs[i] = base.projs[i];
        
        size_t pi = base.proj_count;
        if (is_slice_view) {
            projs[pi].kind = AX_MIR_PROJ_DEREF;
            pi++;
        }
        projs[pi].kind = AX_MIR_PROJ_INDEX;
        projs[pi].index_local = idx_local;
        
        base.projs = projs;
        base.proj_count = new_proj_count;
        return base;
    }
    TypeId ty = get_expr_type(b, expr);
    AxMirLocalId temp = add_local(b, AX_MIR_LOCAL_TEMP, ty, false);
    AxMirPlace temp_place = { temp, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
    build_expr_into(b, expr, temp_place);
    return temp_place;
}

static void build_block_into(Builder *b, const AxHirBlock *block, AxMirPlace dest);

static AxMirOperand build_expr_as_operand_inner(Builder *b, const AxHirExpr *expr) {
    AxMirOperand op = {0};
    if (expr->kind == AX_HIR_EXPR_LITERAL) {
        op.kind = AX_MIR_OP_CONST;
        op.constant.ty = get_expr_type(b, expr);
        op.constant.kind = AX_MIR_CONST_INT;
        if (expr->literal.kind == AX_TOK_INT || expr->literal.kind == AX_TOK_CHAR) {
            op.constant.val = expr->literal.val.int_val.value;
        } else if (expr->literal.kind == AX_TOK_STR || expr->literal.kind == AX_TOK_BYTE_STR) {
            op.constant.kind = AX_MIR_CONST_STR;
            op.constant.str.bytes = expr->literal.val.str_val.bytes;
            op.constant.str.len = expr->literal.val.str_val.len;
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
            op.constant.kind = AX_MIR_CONST_INT;
            op.constant.val = sym.v;
            return op;
        } else {
            AxMirPlace p = { loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
            TypeId ty = get_expr_type(b, expr);
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            bool is_copy = true;
            if (t && (t->kind == AX_TY_STR || t->kind == AX_TY_ARRAY)) {
                is_copy = false;
            }
            op.kind = is_copy ? AX_MIR_OP_COPY : AX_MIR_OP_MOVE;
            op.place = p;
            return op;
        }
    } else if (expr->kind == AX_HIR_EXPR_FIELD || expr->kind == AX_HIR_EXPR_TUPLE_INDEX || (expr->kind == AX_HIR_EXPR_INDEX && expr->index.arg->kind != AX_HIR_EXPR_RANGE)) {
        if (AxExprVariantMap_get(&b->thir->expr_variants, expr)) {
            // It's a variant, let the default path build it into a temp
        } else {
            AxMirPlace p = build_place(b, expr);
            TypeId ty = get_expr_type(b, expr);
            const AxType *t = ax_type_get(&b->thir->interner, ty);
            bool is_copy = true;
            if (t && (t->kind == AX_TY_STR || t->kind == AX_TY_ARRAY)) {
                is_copy = false;
            }
            op.kind = is_copy ? AX_MIR_OP_COPY : AX_MIR_OP_MOVE;
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

static void build_expr_into_inner(Builder *b, const AxHirExpr *expr, AxMirPlace dest) {
    uint32_t *vidx_ptr = AxExprVariantMap_get(&b->thir->expr_variants, expr);
    if (vidx_ptr) {
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
        stmt.assign.rvalue.aggregate.variant_idx = *vidx_ptr;
        
        TypeId ty = get_expr_type(b, expr);
        const AxType *t = ax_type_get(&b->thir->interner, ty);
        uint32_t f_count = t->enm.variant_field_counts[*vidx_ptr];
        stmt.assign.rvalue.aggregate.operand_count = f_count;
        
        if (f_count > 0) {
            stmt.assign.rvalue.aggregate.operands = ax_arena_alloc(b->arena, sizeof(AxMirOperand) * f_count, _Alignof(AxMirOperand));
            if (expr->kind == AX_HIR_EXPR_METHOD_CALL) {
                uint32_t i = 0;
                for (const AxHirExpr *arg = expr->method_call.args; arg; arg = arg->next) {
                    stmt.assign.rvalue.aggregate.operands[i++] = build_expr_as_operand(b, arg);
                }
            } else if (expr->kind == AX_HIR_EXPR_CALL) {
                uint32_t i = 0;
                for (const AxHirExpr *arg = expr->call.args; arg; arg = arg->next) {
                    stmt.assign.rvalue.aggregate.operands[i++] = build_expr_as_operand(b, arg);
                }
            }
        }
        push_stmt(b, b->current_bb, stmt);
        return;
    }

    if (expr->kind == AX_HIR_EXPR_LITERAL || expr->kind == AX_HIR_EXPR_PATH || expr->kind == AX_HIR_EXPR_FIELD || expr->kind == AX_HIR_EXPR_TUPLE_INDEX || (expr->kind == AX_HIR_EXPR_INDEX && expr->index.arg->kind != AX_HIR_EXPR_RANGE)) {
        AxMirOperand op = build_expr_as_operand(b, expr);
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_USE;
        stmt.assign.rvalue.use = op;
        push_stmt(b, b->current_bb, stmt);
    } else if (expr->kind == AX_HIR_EXPR_INDEX && expr->index.arg->kind == AX_HIR_EXPR_RANGE) {
        AxMirPlace p = build_place(b, expr);
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.location = expr->span;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_REF;
        
        TypeId ty = get_expr_type(b, expr);
        const AxType *t = ax_type_get(&b->thir->interner, ty);
        stmt.assign.rvalue.ref.bk = (t && t->kind == AX_TY_MUT_VIEW) ? AX_MIR_BORROW_MUT : AX_MIR_BORROW_SHARED;
        stmt.assign.rvalue.ref.place = p;
        push_stmt(b, b->current_bb, stmt);
    } else if (expr->kind == AX_HIR_EXPR_ARRAY) {
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
        }
    } else if (expr->kind == AX_HIR_EXPR_TUPLE) {
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
        
        TypeId ty = get_expr_type(b, expr);
        const AxType *t = ax_type_get(&b->thir->interner, ty);
        uint32_t f_count = 0;
        if (t && t->kind == AX_TY_TUPLE) f_count = t->tuple.field_count;
        
        stmt.assign.rvalue.aggregate.operand_count = f_count;
        if (f_count > 0) {
            stmt.assign.rvalue.aggregate.operands = ax_arena_alloc(b->arena, sizeof(AxMirOperand) * f_count, _Alignof(AxMirOperand));
            uint32_t i = 0;
            for (const AxHirExpr *elem = expr->tuple.elems; elem && i < f_count; elem = elem->next, i++) {
                stmt.assign.rvalue.aggregate.operands[i] = build_expr_as_operand(b, elem);
            }
        }
        push_stmt(b, b->current_bb, stmt);
    } else if (expr->kind == AX_HIR_EXPR_STRUCT) {
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
        
        TypeId ty = get_expr_type(b, expr);
        const AxType *t = ax_type_get(&b->thir->interner, ty);
        uint32_t f_count = t->strct.field_count;
        
        stmt.assign.rvalue.aggregate.operand_count = f_count;
        if (f_count > 0) {
            stmt.assign.rvalue.aggregate.operands = ax_arena_alloc(b->arena, sizeof(AxMirOperand) * f_count, _Alignof(AxMirOperand));
            for (uint32_t i = 0; i < f_count; i++) {
                stmt.assign.rvalue.aggregate.operands[i].kind = AX_MIR_OP_CONST;
                stmt.assign.rvalue.aggregate.operands[i].constant.val = 0;
            }
            
            for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                uint32_t idx = 0;
                for (const AxHirFieldDecl *fd = t->strct.def->struct_decl.struct_fields; fd; fd = fd->next, idx++) {
                    if (fd->name.v == init->name.v) break;
                }
                stmt.assign.rvalue.aggregate.operands[idx] = build_expr_as_operand(b, init->expr);
            }
        }
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
            zero_op.constant.kind = AX_MIR_CONST_INT;
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
        } else if (expr->kind == AX_HIR_EXPR_TRY) {
        TypeId expr_ty = get_expr_type(b, expr->try_expr.expr);
        bool is_opt = expr->try_expr.is_opt;
        uint32_t payload_idx = expr->try_expr.payload_idx;
        uint32_t err_idx = expr->try_expr.err_idx;
        
        AxMirLocalId expr_loc = add_local(b, AX_MIR_LOCAL_TEMP, expr_ty, false);
        AxMirPlace expr_place = { expr_loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        build_expr_into(b, expr->try_expr.expr, expr_place);
        
        AxMirLocalId discr_loc = add_local(b, AX_MIR_LOCAL_TEMP, b->thir->interner.t_u32, false);
        AxMirPlace discr_place = { discr_loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = discr_place;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_DISCRIMINANT;
        stmt.assign.rvalue.discriminant = expr_place;
        push_stmt(b, b->current_bb, stmt);
        
        AxMirBbId bb_then = add_bb(b);
        AxMirBbId bb_else = add_bb(b);
        
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_SWITCH_INT;
        term.region = AX_MIR_REGION_UNKNOWN;
        term.view = AX_MIR_VIEW_UNKNOWN;
        term.drop_flag = 0;
        term.switch_int.discr.kind = AX_MIR_OP_COPY;
        term.switch_int.discr.place = discr_place;
        
        term.switch_int.targets.count = 1;
        term.switch_int.targets.values = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
        term.switch_int.targets.values[0].value = payload_idx;
        term.switch_int.targets.values[0].target = bb_then;
        term.switch_int.targets.otherwise = bb_else;
        set_terminator(b, b->current_bb, term);
        
        b->current_bb = bb_then;
        AxMirProjection proj = { .kind = AX_MIR_PROJ_DOWNCAST, .variant_idx = payload_idx };
        AxMirProjection *projs = ax_arena_alloc_array(b->arena, 2, sizeof(AxMirProjection), _Alignof(AxMirProjection));
        projs[0] = proj;
        projs[1].kind = AX_MIR_PROJ_FIELD;
        projs[1].field_idx = 0;
        AxMirPlace field_place = expr_place;
        field_place.proj_count = 2;
        field_place.projs = projs;
        
        AxMirStmt assign_dest = {0};
        assign_dest.kind = AX_MIR_STMT_ASSIGN;
        assign_dest.assign.place = dest;
        assign_dest.assign.rvalue.kind = AX_MIR_RVALUE_USE;
        assign_dest.assign.rvalue.use.kind = AX_MIR_OP_MOVE;
        assign_dest.assign.rvalue.use.place = field_place;
        push_stmt(b, b->current_bb, assign_dest);
        
        b->current_bb = bb_else;
        AxMirPlace ret_place = { {0}, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        
        if (is_opt) {
            AxMirStmt ret_assign = {0};
            ret_assign.kind = AX_MIR_STMT_ASSIGN;
            ret_assign.assign.place = ret_place;
            ret_assign.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
            ret_assign.assign.rvalue.aggregate.variant_idx = err_idx;
            ret_assign.assign.rvalue.aggregate.operands = NULL;
            ret_assign.assign.rvalue.aggregate.operand_count = 0;
            push_stmt(b, b->current_bb, ret_assign);
        } else {
            AxMirProjection *err_projs = ax_arena_alloc_array(b->arena, 2, sizeof(AxMirProjection), _Alignof(AxMirProjection));
            err_projs[0].kind = AX_MIR_PROJ_DOWNCAST;
            err_projs[0].variant_idx = err_idx;
            err_projs[1].kind = AX_MIR_PROJ_FIELD;
            err_projs[1].field_idx = 0;
            AxMirPlace err_field_place = expr_place;
            err_field_place.proj_count = 2;
            err_field_place.projs = err_projs;
            
            AxMirOperand *err_op = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirOperand), _Alignof(AxMirOperand));
            err_op[0].kind = AX_MIR_OP_MOVE;
            err_op[0].place = err_field_place;
            
            AxMirStmt ret_assign = {0};
            ret_assign.kind = AX_MIR_STMT_ASSIGN;
            ret_assign.assign.place = ret_place;
            ret_assign.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
            ret_assign.assign.rvalue.aggregate.variant_idx = err_idx;
            ret_assign.assign.rvalue.aggregate.operands = err_op;
            ret_assign.assign.rvalue.aggregate.operand_count = 1;
            push_stmt(b, b->current_bb, ret_assign);
        }
        
        b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, NULL, (AxMirBbId){0}, b->current_span);
        AxMirTerminator ret_term = {0};
        ret_term.kind = AX_MIR_TERM_RETURN;
        ret_term.region = AX_MIR_REGION_UNKNOWN;
        ret_term.view = AX_MIR_VIEW_UNKNOWN;
        ret_term.drop_flag = 0;
        set_terminator(b, b->current_bb, ret_term);
        
        b->current_bb = bb_then;
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
        
        b->current_bb = bb_end;    } else if (expr->kind == AX_HIR_EXPR_MATCH) {
        TypeId match_val_ty = get_expr_type(b, expr->match.expr);
        AxMirLocalId temp = add_local(b, AX_MIR_LOCAL_TEMP, match_val_ty, false);
        AxMirPlace temp_place = { temp, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        build_expr_into(b, expr->match.expr, temp_place);
        
        AxMirBbId bb_end = add_bb(b);
        AxMirBbId bb_current = b->current_bb;
        
        for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
            AxMirBbId bb_next_arm = arm->next ? add_bb(b) : (AxMirBbId){0};
            if (bb_next_arm.v == 0) {
                bb_next_arm = add_bb(b);
                AxMirTerminator unreach = {0};
                unreach.kind = AX_MIR_TERM_UNREACHABLE;
                set_terminator(b, bb_next_arm, unreach);
            }
            
            AxMirBbId bb_body = build_pat_match(b, bb_current, temp_place, arm->pat, bb_next_arm);
            if (arm->guard) {
                b->current_bb = bb_body;
                AxMirOperand guard_op = build_expr_as_operand(b, arm->guard);
                AxMirBbId bb_guard_pass = add_bb(b);
                AxMirTerminator switch_term = {0};
                switch_term.kind = AX_MIR_TERM_SWITCH_INT;
                switch_term.switch_int.discr = guard_op;
                AxMirSwitchTarget *targets = ax_arena_alloc_array(b->arena, 1, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
                targets[0].value = 0;
                targets[0].target = bb_next_arm;
                switch_term.switch_int.targets.values = targets;
                switch_term.switch_int.targets.count = 1;
                switch_term.switch_int.targets.otherwise = bb_guard_pass;
                set_terminator(b, b->current_bb, switch_term);
                bb_body = bb_guard_pass;
            }
            
            b->current_bb = bb_body;
            build_expr_into(b, arm->body, dest);
            if (!b->bbs[b->current_bb.v].is_terminated) {
                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = bb_end;
                set_terminator(b, b->current_bb, term);
            }
            
            bb_current = bb_next_arm;
        }
        b->current_bb = bb_end;

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
        b->loops[b->loop_count].drop_scope = b->current_drops;
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
    } else if (expr->kind == AX_HIR_EXPR_WHILE) {
        AxMirBbId cond_bb = add_bb(b);
        AxMirBbId body_bb = add_bb(b);
        AxMirBbId exit_bb = add_bb(b);
        
        AxMirTerminator goto_cond = {0};
        goto_cond.kind = AX_MIR_TERM_GOTO;
        goto_cond.goto_target = cond_bb;
        set_terminator(b, b->current_bb, goto_cond);
        
        b->current_bb = cond_bb;
        AxMirOperand cond_op = build_expr_as_operand(b, expr->while_expr.cond);
        
        AxMirTerminator switch_int = {0};
        switch_int.kind = AX_MIR_TERM_SWITCH_INT;
        switch_int.switch_int.discr = cond_op;
        switch_int.switch_int.targets.count = 1;
        switch_int.switch_int.targets.values = ax_arena_alloc((AxArena*)&b->thir->interner.arena, sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
        switch_int.switch_int.targets.values[0].value = 1;
        switch_int.switch_int.targets.values[0].target = body_bb;
        switch_int.switch_int.targets.otherwise = exit_bb;
        set_terminator(b, b->current_bb, switch_int);
        
        b->current_bb = body_bb;
        
        if (b->loop_count >= b->loop_cap) {
            b->loop_cap = b->loop_cap ? b->loop_cap * 2 : 16;
            b->loops = realloc(b->loops, b->loop_cap * sizeof(LoopContext));
        }
        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = cond_bb;
        b->loops[b->loop_count].dest = dest;
        b->loops[b->loop_count].label = expr->while_expr.label;
        b->loops[b->loop_count].drop_scope = b->current_drops;
        b->loop_count++;
        
        build_block_into(b, &expr->while_expr.block, dest);
        
        if (!b->bbs[b->current_bb.v].is_terminated) {
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_GOTO;
            term.goto_target = cond_bb;
            set_terminator(b, b->current_bb, term);
        }
        
        b->current_bb = exit_bb;
        b->loop_count--;
    } else if (expr->kind == AX_HIR_EXPR_CALL) {
        if (expr->call.callee->kind == AX_HIR_EXPR_PATH) {
            TypeId callee_ty = get_expr_type(b, expr->call.callee);
            if (!TypeId_is_none(callee_ty) && ax_type_get(&b->thir->interner, callee_ty)->kind == AX_TY_BUILTIN_DROP) {
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
                AxMirBbId next_bb = add_bb(b);
                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_DROP;
                term.location = expr->span;
                term.drop.place = arg_place;
                term.drop.target = next_bb;
                term.drop.unwind = (AxMirBbId){0};
                term.drop.is_explicit = true;
                set_terminator(b, b->current_bb, term);
                b->current_bb = next_bb;

                AxMirStmt stmt = {0};
                stmt.kind = AX_MIR_STMT_ASSIGN;
                stmt.assign.place = dest;
                stmt.assign.rvalue.kind = AX_MIR_RVALUE_AGGREGATE;
                stmt.assign.rvalue.aggregate.operands = NULL;
                stmt.assign.rvalue.aggregate.operand_count = 0;
                stmt.assign.rvalue.aggregate.variant_idx = 0;
                push_stmt(b, b->current_bb, stmt);
                return;
            }
            if (!TypeId_is_none(callee_ty) && ax_type_get(&b->thir->interner, callee_ty)->kind == AX_TY_BUILTIN_LEN) {
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
            AxMirOperand max_char = { .kind = AX_MIR_OP_CONST, .region = AX_MIR_REGION_UNKNOWN, .view = AX_MIR_VIEW_UNKNOWN, .constant = { .ty = b->thir->interner.t_u32, .kind = AX_MIR_CONST_INT, .val = 0x10FFFF } };
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
            AxMirOperand c_d800 = { .kind = AX_MIR_OP_CONST, .region = AX_MIR_REGION_UNKNOWN, .view = AX_MIR_VIEW_UNKNOWN, .constant = { .ty = b->thir->interner.t_u32, .kind = AX_MIR_CONST_INT, .val = 0xD800 } };
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
            AxMirOperand c_dfff = { .kind = AX_MIR_OP_CONST, .region = AX_MIR_REGION_UNKNOWN, .view = AX_MIR_VIEW_UNKNOWN, .constant = { .ty = b->thir->interner.t_u32, .kind = AX_MIR_CONST_INT, .val = 0xDFFF } };
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
            valid_stmt.assign.rvalue.binary_op.lhs = (AxMirOperand){ .kind = AX_MIR_OP_COPY, .place = lt_d800_place  };
            valid_stmt.assign.rvalue.binary_op.rhs = (AxMirOperand){ .kind = AX_MIR_OP_COPY, .place = gt_dfff_place  };
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
            b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, NULL, (AxMirBbId){0}, b->current_span);
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
                b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, target->drop_scope, target->break_bb, b->current_span);
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
                b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, target->drop_scope, target->continue_bb, b->current_span);
            }
        } else {
            AX_ICE("Unhandled jump kind in MIR builder");
        }
    } else if (expr->kind == AX_HIR_EXPR_VIEW) {
        AxMirPlace p = build_place(b, expr->view.expr);
        AxMirStmt stmt = {0};
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.location = expr->span;
        stmt.assign.place = dest;
        stmt.assign.rvalue.kind = AX_MIR_RVALUE_REF;
        stmt.assign.rvalue.ref.bk = expr->view.is_mut ? AX_MIR_BORROW_MUT : AX_MIR_BORROW_SHARED;
        stmt.assign.rvalue.ref.place = p;
        push_stmt(b, b->current_bb, stmt);
    } else {
        AX_ICE("Unhandled HIR expr kind in MIR builder: %d", expr->kind);
    }
}

static void build_block_into_inner(Builder *b, const AxHirBlock *block, AxMirPlace dest) {
    DropNode *old_drops = b->current_drops;
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
            }        } else if (stmt->kind == AX_HIR_STMT_LET) {
            TypeId ty = get_pat_type(b, stmt->let.pat);
            if (ty.v == 0 && stmt->let.expr) ty = get_expr_type(b, stmt->let.expr);
            
            if (stmt->let.expr) {
                AxMirLocalId loc = add_local(b, AX_MIR_LOCAL_TEMP, ty, false);
                AxMirPlace p = { loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
                build_expr_into(b, stmt->let.expr, p);
                
                b->current_bb = build_pat_match(b, b->current_bb, p, stmt->let.pat, (AxMirBbId){0});
            } else {
                declare_pat_locals(b, stmt->let.pat, ty);
            }

        } else if (stmt->kind == AX_HIR_STMT_ASSIGN) {
            AxMirPlace dest = build_place(b, stmt->assign.left);
            if (dest.local.v == 0 && dest.proj_count == 0 && stmt->assign.left->kind != AX_HIR_EXPR_PATH) {
            }
            build_expr_into(b, stmt->assign.right, dest);
        }

        // Cleanup temporaries
        DropNode *curr = b->current_drops;
        DropNode *prev = NULL;
        while (curr != old_drops) {
            if (curr->is_temp) {
                AxMirBbId next_bb = add_bb(b);
                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_DROP;
                term.location = stmt->span;
                term.drop.place = curr->place;
                term.drop.target = next_bb;
                term.drop.unwind = (AxMirBbId){0};
                set_terminator(b, b->current_bb, term);
                b->current_bb = next_bb;
                
                if (prev) {
                    prev->next = curr->next;
                    curr = curr->next;
                } else {
                    b->current_drops = curr->next;
                    curr = b->current_drops;
                }
            } else {
                prev = curr;
                curr = curr->next;
            }
        }
    }
    
    if (!b->bbs[b->current_bb.v].is_terminated) {
        b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, old_drops, (AxMirBbId){0}, b->current_span);
    }
    b->current_drops = old_drops;
}


static AxMirBbId build_pat_match(Builder *b, AxMirBbId current_bb, AxMirPlace place, const AxHirPat *pat, AxMirBbId bb_fail) {
    AxLocation old_span = b->current_span;
    if (pat) b->current_span = pat->span;

    AxMirBbId res = build_pat_match_inner(b, current_bb, place, pat, bb_fail);
    b->current_span = old_span;
    return res;
}


static void build_expr_into(Builder *b, const AxHirExpr *expr, AxMirPlace dest) {
    AxLocation old_span = b->current_span;
    if (expr) b->current_span = expr->span;

    build_expr_into_inner(b, expr, dest);
    b->current_span = old_span;
}


static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr) {
    AxLocation old_span = b->current_span;
    if (expr) b->current_span = expr->span;

    AxMirOperand res = build_expr_as_operand_inner(b, expr);
    if (expr) res.location = expr->span;
    b->current_span = old_span;
    return res;
}


static void build_block_into(Builder *b, const AxHirBlock *block, AxMirPlace dest) {
    AxLocation old_span = b->current_span;
    if (block) b->current_span = block->span;

    build_block_into_inner(b, block, dest);
    b->current_span = old_span;
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
        AxMirLocalId loc = add_local(&b, AX_MIR_LOCAL_ARG, pty, p->is_mut);
        push_drop(&b, (AxMirPlace){ loc, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 }, pty, false);
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
        b.current_bb = build_drop_chain(&b, b.current_bb, b.current_drops, NULL, (AxMirBbId){0}, b.current_span);
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
