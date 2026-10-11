#include "mir/drop/drop.h"
#include "types/types.h"
#include <string.h>
#include <stdlib.h>

static bool needs_drop(TypeId ty, const AxThir *thir, const StrInterner *interner) {
    const AxType *t = ax_type_get(&thir->interner, ty);
    if (!t) return false;
    
    if (t->kind == AX_TY_STRUCT) {
        if (t->strct.def->struct_decl.struct_fields == NULL) return true;
        
        for (size_t i = 0; i < t->strct.field_count; i++) {
            if (needs_drop(t->strct.fields[i], thir, interner)) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_TUPLE) {
        for (size_t i = 0; i < t->tuple.field_count; i++) {
            if (needs_drop(t->tuple.fields[i], thir, interner)) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_ENUM) {
        for (size_t v = 0; v < t->enm.variant_count; v++) {
            for (size_t i = 0; i < t->enm.variant_field_counts[v]; i++) {
                if (needs_drop(t->enm.variant_fields[v][i], thir, interner)) return true;
            }
        }
        return false;
    }
    return false;
}

static AxMirLocalId add_drop_flag(AxMirBody *body, const AxThir *thir) {
    AxMirLocalDecl *new_locals = ax_arena_alloc(&body->arena, (body->local_count + 1) * sizeof(AxMirLocalDecl), _Alignof(AxMirLocalDecl));
    memcpy(new_locals, body->locals, body->local_count * sizeof(AxMirLocalDecl));
    body->locals = new_locals;
    
    AxMirLocalId id = { (uint32_t)body->local_count };
    
    AxMirLocalDecl *decl = &body->locals[id.v];
    decl->kind = AX_MIR_LOCAL_TEMP;
    decl->ty = thir->interner.t_bool;
    decl->mut = true;
    decl->location = (AxLocation){0};
    
    body->local_count++;
    return id;
}

static AxMirStmt make_flag_assign(AxMirLocalId flag_id, bool val, const AxThir *thir) {
    AxMirStmt s = {0};
    s.kind = AX_MIR_STMT_ASSIGN;
    s.assign.place.local = flag_id;
    s.assign.rvalue.kind = AX_MIR_RVALUE_USE;
    s.assign.rvalue.use.kind = AX_MIR_OP_CONST;
    s.assign.rvalue.use.constant.ty = thir->interner.t_bool;
    s.assign.rvalue.use.constant.val = val ? 1 : 0;
    return s;
}

static void visit_op(const AxMirOperand *op, uint32_t *local_flags, size_t orig_local_count, AxMirStmt *out_stmts, size_t *out_idx, const AxThir *thir) {
    if (op->kind == AX_MIR_OP_MOVE || op->kind == AX_MIR_OP_COPY) {
        AxMirPlace src = op->place;
        if (src.local.v < orig_local_count && local_flags[src.local.v]) {
            out_stmts[(*out_idx)++] = make_flag_assign((AxMirLocalId){local_flags[src.local.v]}, false, thir);
        }
    }
}

static void visit_rvalue(const AxMirRvalue *rv, uint32_t *local_flags, size_t orig_local_count, AxMirStmt *out_stmts, size_t *out_idx, const AxThir *thir) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE: visit_op(&rv->use, local_flags, orig_local_count, out_stmts, out_idx, thir); break;
        case AX_MIR_RVALUE_REPEAT:
            visit_op(&rv->repeat.op, local_flags, orig_local_count, out_stmts, out_idx, thir);
            visit_op(&rv->repeat.count, local_flags, orig_local_count, out_stmts, out_idx, thir);
            break;
        case AX_MIR_RVALUE_CAST: visit_op(&rv->cast.op, local_flags, orig_local_count, out_stmts, out_idx, thir); break;
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
        case AX_MIR_RVALUE_BINARY_OP:
            visit_op(&rv->binary_op.lhs, local_flags, orig_local_count, out_stmts, out_idx, thir);
            visit_op(&rv->binary_op.rhs, local_flags, orig_local_count, out_stmts, out_idx, thir);
            break;
        case AX_MIR_RVALUE_UNARY_OP:
            visit_op(&rv->unary_op.operand, local_flags, orig_local_count, out_stmts, out_idx, thir);
            break;
        case AX_MIR_RVALUE_AGGREGATE:
            for (size_t i = 0; i < rv->aggregate.operand_count; i++) {
                visit_op(&rv->aggregate.operands[i], local_flags, orig_local_count, out_stmts, out_idx, thir);
            }
            break;
        default: break;
    }
}

void ax_mir_drop_elaborate(AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const StrInterner *interner) {
    (void)sink;
    
    size_t orig_local_count = body->local_count;
    uint32_t *local_flags = calloc(orig_local_count, sizeof(uint32_t));
    
    for (size_t i = 1; i < orig_local_count; i++) {
        if (needs_drop(body->locals[i].ty, thir, interner)) {
            AxMirLocalId fid = add_drop_flag(body, thir);
            local_flags[i] = fid.v;
        }
    }
    
    if (body->bb_count > 0) {
        AxMirBb *bb0 = &body->bbs[0];
        size_t init_count = 0;
        for (size_t i = 1; i < orig_local_count; i++) {
            if (local_flags[i]) init_count++;
        }
        
        if (init_count > 0) {
            AxMirStmt *new_stmts = ax_arena_alloc(&body->arena, (bb0->stmt_count + init_count) * sizeof(AxMirStmt), _Alignof(AxMirStmt));
            size_t idx = 0;
            for (size_t i = 1; i < orig_local_count; i++) {
                if (local_flags[i]) {
                    bool is_arg = (body->locals[i].kind == AX_MIR_LOCAL_ARG);
                    new_stmts[idx++] = make_flag_assign((AxMirLocalId){local_flags[i]}, is_arg, thir);
                }
            }
            memcpy(new_stmts + init_count, bb0->stmts, bb0->stmt_count * sizeof(AxMirStmt));
            bb0->stmts = new_stmts;
            bb0->stmt_count += init_count;
            bb0->stmt_cap = bb0->stmt_count;
        }
    }
    
    // We also need to process CALL destinations. A call initializes its destination.
    // Instead of edge splitting, we will just insert flag=true at the top of the call's target BB!
    // We can do a pre-pass to collect all call targets and what they initialize.
    // Assuming each call has a unique target BB (which is true in Axiom builder), we can just prepend.
    struct CallInit { AxMirLocalId dest; };
    struct CallInit *call_inits = calloc(body->bb_count, sizeof(struct CallInit));
    for (size_t i = 0; i < body->bb_count; i++) {
        AxMirTerminator *term = &body->bbs[i].terminator;
        if (term->kind == AX_MIR_TERM_CALL) {
            AxMirPlace dest = term->call.destination;
            if (dest.local.v < orig_local_count && local_flags[dest.local.v]) {
                if (term->call.target.v < body->bb_count) {
                    call_inits[term->call.target.v].dest = dest.local;
                }
            }
        }
    }
    
    for (size_t i = 0; i < body->bb_count; i++) {
        AxMirBb *bb = &body->bbs[i];
        
        // Count maximum extra statements
        size_t max_extra = 0;
        if (call_inits[i].dest.v != 0) max_extra++;
        for (size_t j = 0; j < bb->stmt_count; j++) {
            max_extra += 16; // arbitrary upper bound per stmt
        }
        max_extra += 16; // for terminator moves
        
        AxMirStmt *new_stmts = ax_arena_alloc(&body->arena, (bb->stmt_count + max_extra) * sizeof(AxMirStmt), _Alignof(AxMirStmt));
        size_t idx = 0;
        
        if (call_inits[i].dest.v != 0) {
            new_stmts[idx++] = make_flag_assign((AxMirLocalId){local_flags[call_inits[i].dest.v]}, true, thir);
        }
        
        for (size_t j = 0; j < bb->stmt_count; j++) {
            AxMirStmt *s = &bb->stmts[j];
            
            if (s->kind == AX_MIR_STMT_ASSIGN) {
                visit_rvalue(&s->assign.rvalue, local_flags, orig_local_count, new_stmts, &idx, thir);
            }
            
            new_stmts[idx++] = *s;
            
            if (s->kind == AX_MIR_STMT_ASSIGN) {
                AxMirPlace dst = s->assign.place;
                if (dst.local.v < orig_local_count && local_flags[dst.local.v]) {
                    new_stmts[idx++] = make_flag_assign((AxMirLocalId){local_flags[dst.local.v]}, true, thir);
                }
            }
        }
        
        // Process terminator moves
        AxMirTerminator *term = &bb->terminator;
        if (term->kind == AX_MIR_TERM_SWITCH_INT) {
            visit_op(&term->switch_int.discr, local_flags, orig_local_count, new_stmts, &idx, thir);
        } else if (term->kind == AX_MIR_TERM_CALL) {
            visit_op(&term->call.func, local_flags, orig_local_count, new_stmts, &idx, thir);
            for (size_t a = 0; a < term->call.arg_count; a++) {
                visit_op(&term->call.args[a], local_flags, orig_local_count, new_stmts, &idx, thir);
            }
        } else if (term->kind == AX_MIR_TERM_ASSERT) {
            visit_op(&term->assert.cond, local_flags, orig_local_count, new_stmts, &idx, thir);
        }
        
        bb->stmts = new_stmts;
        bb->stmt_count = idx;
        bb->stmt_cap = idx;
        
        if (bb->terminator.kind == AX_MIR_TERM_DROP) {
            AxMirPlace dp = bb->terminator.drop.place;
            if (dp.local.v < orig_local_count && local_flags[dp.local.v]) {
                bb->terminator.drop_flag = local_flags[dp.local.v];
            }
        }
    }
    
    free(call_inits);
    free(local_flags);
}
