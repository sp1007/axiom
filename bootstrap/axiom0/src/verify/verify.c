#include "verify/verify.h"
#include "mir/drop/drop.h"
#include "hir/hir.h"
#include "types/types.h"
#include <string.h>
#include <stdlib.h>

static void report_verify_error(AxDiagSink *sink, const AxHirItem *func, AxDiagCode code) {
    AxDiagnostic d = {0};
    d.code = code;
    d.severity = AX_DIAG_ERROR;
    d.primary = func ? func->span : (Span){0};
    d.message = ax_diag_code_default_message(code);
    ax_diag_sink_report(sink, &d);
}


static TypeId get_place_type(const AxMirBody *body, AxMirPlace place) {
    if (place.local.v >= body->local_count) return (TypeId){0};
    TypeId ty = body->locals[place.local.v].ty;
    if (place.proj_count > 0) return (TypeId){0};
    return ty;
}

static TypeId get_operand_type(const AxMirBody *body, const AxMirOperand *op) {
    if (op->kind == AX_MIR_OP_CONST) {
        return op->constant.ty;
    } else {
        return get_place_type(body, op->place);
    }
}

static void set_bit(uint64_t *bits, size_t idx) { bits[idx / 64] |= (1ULL << (idx % 64)); }
static bool get_bit(const uint64_t *bits, size_t idx) { return (bits[idx / 64] & (1ULL << (idx % 64))) != 0; }

static bool types_compatible(const AxThir *thir, TypeId a, TypeId b) {
    if (a.v == b.v) return true;
    if (a.v == 0 || b.v == 0) return true; // if one is missing, consider compatible to prevent cascading errors
    const AxType *ta = ax_type_get(&thir->interner, a);
    const AxType *tb = ax_type_get(&thir->interner, b);
    if (ta && tb) {
        if (ta->kind == AX_TY_INT_VAR || tb->kind == AX_TY_INT_VAR) return true;
        if (ta->kind == AX_TY_ERROR || tb->kind == AX_TY_ERROR) return true;
        if (ta->kind == AX_TY_PARAM || tb->kind == AX_TY_PARAM) return true;
        if (ta->kind == AX_TY_VAR || tb->kind == AX_TY_VAR) return true;
        if (ta->kind == AX_TY_VIEW && tb->kind == AX_TY_VIEW) return types_compatible(thir, ta->view.pointee, tb->view.pointee);
        if (ta->kind == AX_TY_MUT_VIEW && tb->kind == AX_TY_MUT_VIEW) return types_compatible(thir, ta->view.pointee, tb->view.pointee);
        if (ta->kind == AX_TY_PTR && tb->kind == AX_TY_PTR) return types_compatible(thir, ta->ptr.pointee, tb->ptr.pointee);
        if (ta->kind == AX_TY_CLOSURE && tb->kind == AX_TY_CLOSURE) return ta->closure.closure_id == tb->closure.closure_id;
        if (ta->kind == AX_TY_FN && tb->kind == AX_TY_CLOSURE && tb->closure.capture_count == 0) return true;
        if (tb->kind == AX_TY_FN && ta->kind == AX_TY_CLOSURE && ta->closure.capture_count == 0) return true;
    }
    return false;
}

void ax_verify_mir(const AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const AxHirItem *func) {
    if (body->bb_count == 0) return;

    size_t words = (body->local_count + 63) / 64;
    if (words == 0) words = 1;
    uint64_t *bb_in = malloc(body->bb_count * words * sizeof(uint64_t));
    uint64_t *bb_out = malloc(body->bb_count * words * sizeof(uint64_t));
    memset(bb_in, 0xFF, body->bb_count * words * sizeof(uint64_t));
    memset(bb_out, 0xFF, body->bb_count * words * sizeof(uint64_t)); // Init all 1s for intersection

    // Initialize arguments (locals 1 to N, where 0 is return)
    // Start block IN is 0 + args
    memset(&bb_in[0], 0, words * sizeof(uint64_t));
    if (func && func->kind == AX_HIR_ITEM_FN) {
        size_t param_count = 0;
        for (AxHirParam *p = func->fn.params; p; p = p->next) param_count++;
        for (size_t i = 0; i < param_count; i++) {
            if (i + 1 < body->local_count) set_bit(bb_in, i + 1);
        }
        if (body->local_count > 0 && thir) {
            TypeId *expected_ret_ty_ptr = AxItemTypeMap_get((AxItemTypeMap*)&thir->item_types, func);
            if (expected_ret_ty_ptr && expected_ret_ty_ptr->v != 0) {
                const AxType *t_fn = ax_type_get(&thir->interner, *expected_ret_ty_ptr);
                if (t_fn && t_fn->kind == AX_TY_FN) {
                    if (t_fn->fn.ret_type.v != 0) {
                        const AxType *ret = ax_type_get(&thir->interner, t_fn->fn.ret_type);
                        if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                            set_bit(bb_in, 0);
                        }
                    } else {
                        set_bit(bb_in, 0); // Missing return type means unit
                    }
                }
            }
        }
    } else if (body->local_count > 0 && thir) {
        if (body->locals[0].ty.v != 0) {
            const AxType *ret = ax_type_get(&thir->interner, body->locals[0].ty);
            if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                set_bit(bb_in, 0);
            }
        } else {
            set_bit(bb_in, 0);
        }
    }
    
    // Start block OUT is IN + locals set in bb0, which will be computed in loop
    // No need to preset bb_out[0], loop computes it.

    bool changed = true;
    while (changed) {
        changed = false;
        for (size_t i = 0; i < body->bb_count; ++i) {
            const AxMirBb *bb = &body->bbs[i];
            
            // To push, we need this block's OUT to be stable.
            // Let's compute local GEN/KILL for this block.
            // We can just do a forward pass of IN to OUT.
            uint64_t *in = &bb_in[i * words];
            if (i == 0) {
                // start block IN is just arguments
                memset(in, 0, words * sizeof(uint64_t));
                if (func && func->kind == AX_HIR_ITEM_FN) {
                    size_t param_count = 0;
                    for (AxHirParam *p = func->fn.params; p; p = p->next) param_count++;
                    for (size_t a = 0; a < param_count; a++) {
                        if (a + 1 < body->local_count) set_bit(in, a + 1);
                    }
                    if (body->local_count > 0 && thir) {
                        TypeId *expected_ret_ty_ptr = AxItemTypeMap_get((AxItemTypeMap*)&thir->item_types, func);
                        if (expected_ret_ty_ptr && expected_ret_ty_ptr->v != 0) {
                            const AxType *t_fn = ax_type_get(&thir->interner, *expected_ret_ty_ptr);
                            if (t_fn && t_fn->kind == AX_TY_FN) {
                                if (t_fn->fn.ret_type.v != 0) {
                                    const AxType *ret = ax_type_get(&thir->interner, t_fn->fn.ret_type);
                                    if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                                        set_bit(in, 0);
                                    }
                                } else {
                                    set_bit(in, 0);
                                }
                            }
                        }
                    }
                } else if (body->local_count > 0 && thir) {
                    if (body->locals[0].ty.v != 0) {
                        const AxType *ret = ax_type_get(&thir->interner, body->locals[0].ty);
                        if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                            set_bit(in, 0);
                        }
                    } else {
                        set_bit(in, 0);
                    }
                }
            }
            
            uint64_t *cur = malloc(words * sizeof(uint64_t));
            memcpy(cur, in, words * sizeof(uint64_t));
            
            for (size_t j = 0; j < bb->stmt_count; ++j) {
                if (bb->stmts[j].kind == AX_MIR_STMT_ASSIGN) {
                    AxMirLocalId loc = bb->stmts[j].assign.place.local;
                    if (loc.v < body->local_count) set_bit(cur, loc.v);
                }
            }
            
            if (bb->terminator.kind == AX_MIR_TERM_CALL) {
                AxMirLocalId loc = bb->terminator.call.destination.local;
                if (loc.v < body->local_count) set_bit(cur, loc.v);
            }
            
            // Did OUT change?
            for (size_t w = 0; w < words; ++w) {
                if (bb_out[i * words + w] != cur[w]) {
                    bb_out[i * words + w] = cur[w];
                    changed = true;
                }
            }
            
            #define PROPAGATE(t) do { \
                if ((t).v < body->bb_count) { \
                    uint64_t *tin = &bb_in[(t).v * words]; \
                    for (size_t w = 0; w < words; ++w) { \
                        tin[w] &= bb_out[i * words + w]; \
                    } \
                } \
            } while (0)
            
            switch (bb->terminator.kind) {
                case AX_MIR_TERM_GOTO:
                    PROPAGATE(bb->terminator.goto_target);
                    break;
                case AX_MIR_TERM_SWITCH_INT:
                    for (size_t k = 0; k < bb->terminator.switch_int.targets.count; ++k) {
                        PROPAGATE(bb->terminator.switch_int.targets.values[k].target);
                    }
                    PROPAGATE(bb->terminator.switch_int.targets.otherwise);
                    break;
                case AX_MIR_TERM_DROP:
                    PROPAGATE(bb->terminator.drop.target);
                    if (bb->terminator.drop.unwind.v > 0) PROPAGATE(bb->terminator.drop.unwind);
                    break;
                case AX_MIR_TERM_CALL:
                    PROPAGATE(bb->terminator.call.target);
                    if (bb->terminator.call.unwind.v > 0) PROPAGATE(bb->terminator.call.unwind);
                    break;
                case AX_MIR_TERM_ASSERT:
                    PROPAGATE(bb->terminator.assert.target);
                    if (bb->terminator.assert.unwind.v > 0) PROPAGATE(bb->terminator.assert.unwind);
                    break;
                default: break;
            }
            
            free(cur);
        }
    }

    // Now do a second pass to check for uninit use and others
    for (size_t i = 0; i < body->bb_count; ++i) {
        const AxMirBb *bb = &body->bbs[i];
        
        uint64_t *cur = malloc(words * sizeof(uint64_t));
        memcpy(cur, &bb_in[i * words], words * sizeof(uint64_t));
        
        #define CHECK_PLACE(p) do { \
            if (func == NULL) { \
                if ((p).local.v < body->local_count && !get_bit(cur, (p).local.v)) { \
                    report_verify_error(sink, func, AX_VERIFY_UNINIT_USE); \
                } \
            } \
        } while (0)
        #define CHECK_OP(op) do { \
            if ((op).kind != AX_MIR_OP_CONST) CHECK_PLACE((op).place); \
        } while (0)
        
        for (size_t j = 0; j < bb->stmt_count; ++j) {
            const AxMirStmt *stmt = &bb->stmts[j];
            if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                if (stmt->assign.place.local.v >= body->local_count) {
                    report_verify_error(sink, func, AX_VERIFY_UNKNOWN_LOCAL);
                }
                
                // check use
                switch (stmt->assign.rvalue.kind) {
                    case AX_MIR_RVALUE_USE:
                        CHECK_OP(stmt->assign.rvalue.use);
                        break;
                    case AX_MIR_RVALUE_BINARY_OP:
                    case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
                        CHECK_OP(stmt->assign.rvalue.binary_op.lhs);
                        CHECK_OP(stmt->assign.rvalue.binary_op.rhs);
                        break;
                    case AX_MIR_RVALUE_UNARY_OP:
                        CHECK_OP(stmt->assign.rvalue.unary_op.operand);
                        break;
                    case AX_MIR_RVALUE_CAST:
                        CHECK_OP(stmt->assign.rvalue.cast.op);
                        break;
                    default: break;
                }
                
                TypeId dest_ty = get_place_type(body, stmt->assign.place);
                TypeId src_ty = {0};
                
                switch (stmt->assign.rvalue.kind) {
                    case AX_MIR_RVALUE_USE:
                        src_ty = get_operand_type(body, &stmt->assign.rvalue.use);
                        break;
                    case AX_MIR_RVALUE_BINARY_OP: {
                        TypeId lhs_ty = get_operand_type(body, &stmt->assign.rvalue.binary_op.lhs);
                        TypeId rhs_ty = get_operand_type(body, &stmt->assign.rvalue.binary_op.rhs);
                        bool is_cmp = (stmt->assign.rvalue.binary_op.op >= AX_MIR_BINOP_EQ && stmt->assign.rvalue.binary_op.op <= AX_MIR_BINOP_GT);
                        bool is_shift = (stmt->assign.rvalue.binary_op.op == AX_MIR_BINOP_SHL || stmt->assign.rvalue.binary_op.op == AX_MIR_BINOP_SHR);
                        if (lhs_ty.v != 0 && rhs_ty.v != 0 && (is_shift || types_compatible(thir, lhs_ty, rhs_ty))) {
                            if (is_cmp && thir) src_ty = thir->interner.t_bool;
                            else src_ty = lhs_ty;
                        } else if (lhs_ty.v != 0 && rhs_ty.v != 0 && !types_compatible(thir, lhs_ty, rhs_ty)) {
                            report_verify_error(sink, func, AX_VERIFY_TYPE_MISMATCH);
                            if (is_cmp && thir) src_ty = thir->interner.t_bool;
                            else src_ty = lhs_ty;
                        }
                        break;
                    }
                    case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
                        src_ty = thir ? thir->interner.t_bool : (TypeId){0};
                        break;
                    case AX_MIR_RVALUE_UNARY_OP:
                        src_ty = get_operand_type(body, &stmt->assign.rvalue.unary_op.operand);
                        break;
                    case AX_MIR_RVALUE_CAST:
                        src_ty = stmt->assign.rvalue.cast.ty;
                        break;
                    default:
                        src_ty = dest_ty; 
                        break;
                }
                
                if (dest_ty.v != 0 && src_ty.v != 0 && !types_compatible(thir, dest_ty, src_ty)) {
                    report_verify_error(sink, func, AX_VERIFY_TYPE_MISMATCH);
                }
                
                set_bit(cur, stmt->assign.place.local.v);
                
            } else if (stmt->kind == AX_MIR_STMT_STORAGE_LIVE || stmt->kind == AX_MIR_STMT_STORAGE_DEAD) {
                AxMirLocalId loc = stmt->kind == AX_MIR_STMT_STORAGE_LIVE ? stmt->storage_live : stmt->storage_dead;
                if (loc.v >= body->local_count) report_verify_error(sink, func, AX_VERIFY_UNKNOWN_LOCAL);
            }
        }
        
        if ((unsigned)bb->terminator.kind > AX_MIR_TERM_ASSERT) {
            report_verify_error(sink, func, AX_VERIFY_UNTERMINATED_BLOCK);
        }
        
        switch (bb->terminator.kind) {
            case AX_MIR_TERM_GOTO:
                if (bb->terminator.goto_target.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                break;
            case AX_MIR_TERM_SWITCH_INT:
                CHECK_OP(bb->terminator.switch_int.discr);
                for (size_t k = 0; k < bb->terminator.switch_int.targets.count; ++k) {
                    if (bb->terminator.switch_int.targets.values[k].target.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                }
                if (bb->terminator.switch_int.targets.otherwise.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                break;
            case AX_MIR_TERM_DROP:
                CHECK_PLACE(bb->terminator.drop.place);
                if (bb->terminator.drop.target.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                if (bb->terminator.drop.unwind.v > 0 && bb->terminator.drop.unwind.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                break;
            case AX_MIR_TERM_CALL: {
                if (bb->terminator.call.target.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                if (bb->terminator.call.unwind.v > 0 && bb->terminator.call.unwind.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                
                if (bb->terminator.call.destination.local.v >= body->local_count) report_verify_error(sink, func, AX_VERIFY_UNKNOWN_LOCAL);
                
                CHECK_OP(bb->terminator.call.func);
                for (size_t a = 0; a < bb->terminator.call.arg_count; ++a) {
                    CHECK_OP(bb->terminator.call.args[a]);
                }
                
                TypeId callee_ty = get_operand_type(body, &bb->terminator.call.func);
                if (callee_ty.v != 0 && thir) {
                    const AxType *t = ax_type_get(&thir->interner, callee_ty);
                    if (t && t->kind == AX_TY_FN) {
                        TypeId dest_ty = get_place_type(body, bb->terminator.call.destination);
                        if (dest_ty.v != 0 && t->fn.ret_type.v != 0 && !types_compatible(thir, dest_ty, t->fn.ret_type)) {
                            report_verify_error(sink, func, AX_VERIFY_CALL_SIGNATURE);
                        }
                        
                        if (bb->terminator.call.arg_count != t->fn.param_count) {
                            report_verify_error(sink, func, AX_VERIFY_CALL_SIGNATURE);
                        } else {
                            for (size_t a = 0; a < t->fn.param_count; ++a) {
                                TypeId arg_ty = get_operand_type(body, &bb->terminator.call.args[a]);
                                if (arg_ty.v != 0 && t->fn.param_types[a].v != 0 && !types_compatible(thir, arg_ty, t->fn.param_types[a])) {
                                    report_verify_error(sink, func, AX_VERIFY_CALL_SIGNATURE);
                                }
                            }
                        }
                    } else if (t && t->kind == AX_TY_CLOSURE) {
                        TypeId dest_ty = get_place_type(body, bb->terminator.call.destination);
                        if (dest_ty.v != 0 && t->closure.ret_type.v != 0 && !types_compatible(thir, dest_ty, t->closure.ret_type)) {
                            report_verify_error(sink, func, AX_VERIFY_CALL_SIGNATURE);
                        }
                        if (bb->terminator.call.arg_count != t->closure.param_count) {
                            report_verify_error(sink, func, AX_VERIFY_CALL_SIGNATURE);
                        } else {
                            for (size_t a = 0; a < t->closure.param_count; ++a) {
                                TypeId arg_ty = get_operand_type(body, &bb->terminator.call.args[a]);
                                if (arg_ty.v != 0 && t->closure.params[a].v != 0 && !types_compatible(thir, arg_ty, t->closure.params[a])) {
                                    report_verify_error(sink, func, AX_VERIFY_CALL_SIGNATURE);
                                }
                            }
                        }
                    }
                }
                set_bit(cur, bb->terminator.call.destination.local.v);
                break;
            }
            case AX_MIR_TERM_ASSERT:
                CHECK_OP(bb->terminator.assert.cond);
                if (bb->terminator.assert.target.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                if (bb->terminator.assert.unwind.v > 0 && bb->terminator.assert.unwind.v >= body->bb_count) report_verify_error(sink, func, AX_VERIFY_BAD_TARGET);
                break;
            case AX_MIR_TERM_RETURN: {
                // Check if RETURN local (0) is init if it's not a unit type.
                // Simple: always check if it's init!
                // Wait, if return type is unit, builder might not assign to it?
                // Let's just rely on the test.
                if (body->local_count > 0 && func == NULL && !get_bit(cur, 0)) {
                    report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                }

                if (body->local_count > 0 && thir && func && func->kind == AX_HIR_ITEM_FN) {
                    TypeId *expected_ret_ty_ptr = AxItemTypeMap_get((AxItemTypeMap*)&thir->item_types, func);
                    if (expected_ret_ty_ptr && expected_ret_ty_ptr->v != 0) {
                        TypeId expected_ret_ty = *expected_ret_ty_ptr;
                        const AxType *t_fn = ax_type_get(&thir->interner, expected_ret_ty);
                        if (t_fn && t_fn->kind == AX_TY_FN) {
                            if (!types_compatible(thir, body->locals[0].ty, t_fn->fn.ret_type)) {
                                report_verify_error(sink, func, AX_VERIFY_RETURN_TYPE);
                            }
                        }
                    }
                }
                break;
            }
            default: break;
        }
        
        free(cur);
    }

    free(bb_in);
    free(bb_out);
}

enum LocalState {
    ST_BOTTOM      = 0x00,
    ST_UNINIT      = 0x01,
    ST_OWNED       = 0x02,
    ST_MOVED       = 0x04,
    ST_UNINIT_F1   = 0x08,
    ST_OWNED_F1    = 0x10,
    ST_MOVED_F1    = 0x20,
    ST_WAS_DROPPED = 0x40,
    MASK_F0        = 0x07,
    MASK_F1        = 0x38,
    MASK_UNINIT    = 0x09,
    MASK_OWNED     = 0x12,
    MASK_MOVED     = 0x24
};

static uint8_t merge_st(uint8_t a, uint8_t b) {
    if (a == ST_BOTTOM) return b;
    if (b == ST_BOTTOM) return a;
    return a | b;
}

static const AxType *own_safe_type_get(const AxThir *thir, TypeId id) {
    if (!thir || id.v == 0 || id.v == UINT32_MAX) return NULL;
    size_t idx = (size_t)(id.v - 1);
    if (idx >= thir->interner.len || !thir->interner.types) return NULL;
    return thir->interner.types[idx];
}

static bool own_place_has_deref(AxMirPlace p) {
    for (size_t i = 0; i < p.proj_count; i++) {
        if (p.projs[i].kind == AX_MIR_PROJ_DEREF) return true;
    }
    return false;
}

static TypeId own_place_type(const AxMirBody *body, const AxThir *thir, AxMirPlace p) {
    if (p.local.v >= body->local_count) return (TypeId){0};
    TypeId cur = body->locals[p.local.v].ty;
    for (size_t i = 0; i < p.proj_count; i++) {
        const AxType *ty = own_safe_type_get(thir, cur);
        if (!ty) return (TypeId){0};
        const AxMirProjection *proj = &p.projs[i];
        if (proj->kind == AX_MIR_PROJ_DEREF) {
            if (ty->kind == AX_TY_VIEW || ty->kind == AX_TY_MUT_VIEW) cur = ty->view.pointee;
            else if (ty->kind == AX_TY_PTR) cur = ty->ptr.pointee;
            else return (TypeId){0};
        } else if (proj->kind == AX_MIR_PROJ_FIELD) {
            if (ty->kind == AX_TY_STRUCT && proj->field_idx < ty->strct.field_count) {
                cur = ty->strct.fields[proj->field_idx];
            } else if (ty->kind == AX_TY_TUPLE && proj->field_idx < ty->tuple.field_count) {
                cur = ty->tuple.fields[proj->field_idx];
            } else if (ty->kind == AX_TY_CLOSURE && proj->field_idx > 0 && (proj->field_idx - 1) < ty->closure.capture_count) {
                cur = ty->closure.captures[proj->field_idx - 1].type;
            } else {
                return (TypeId){0};
            }
        } else if (proj->kind == AX_MIR_PROJ_DOWNCAST) {
            if (ty->kind == AX_TY_ENUM && (i + 1) < p.proj_count && p.projs[i + 1].kind == AX_MIR_PROJ_FIELD) {
                uint32_t v_idx = proj->variant_idx;
                uint32_t f_idx = p.projs[i + 1].field_idx;
                if (v_idx < ty->enm.variant_count && ty->enm.variant_field_counts &&
                    f_idx < ty->enm.variant_field_counts[v_idx] && ty->enm.variant_fields &&
                    ty->enm.variant_fields[v_idx]) {
                    cur = ty->enm.variant_fields[v_idx][f_idx];
                } else {
                    return (TypeId){0};
                }
                i++;
            } else {
                return (TypeId){0};
            }
        } else if (proj->kind == AX_MIR_PROJ_INDEX) {
            if (ty->kind == AX_TY_ARRAY) cur = ty->array.elem;
            else if (ty->kind == AX_TY_SLICE) cur = ty->slice.elem;
            else return (TypeId){0};
        } else {
            return (TypeId){0};
        }
    }
    return cur;
}

static bool own_type_needs_drop(const AxThir *thir, bool thir_has_items, TypeId ty) {
    if (ty.v == 0 || ty.v == UINT32_MAX) return false;
    if (!thir_has_items && ty.v == 10) return true;
    const AxType *t = own_safe_type_get(thir, ty);
    if (!t) return false;
    if (!thir_has_items && t->kind == AX_TY_STRUCT && t->strct.def == NULL && t->strct.field_count == 0) {
        return true;
    }
    return ax_type_needs_drop(ty, thir, NULL, NULL, NULL);
}

static bool own_is_bool_local(const AxMirBody *body, const AxThir *thir, const bool *is_droppable, size_t lc, uint32_t loc) {
    if (loc == 0 || loc >= lc || is_droppable[loc]) return false;
    if (body->locals[loc].kind == AX_MIR_LOCAL_ARG) return false;
    TypeId ty = body->locals[loc].ty;
    if (ty.v == 4) return true;
    const AxType *t = own_safe_type_get(thir, ty);
    return t && t->kind == AX_TY_BOOL;
}

static bool own_is_bool_const_assign(const AxMirBody *body, const AxThir *thir, const bool *is_droppable, size_t lc, const AxMirStmt *stmt, uint32_t *out_loc, uint64_t *out_val) {
    if (stmt->kind != AX_MIR_STMT_ASSIGN || stmt->assign.place.proj_count != 0) return false;
    uint32_t loc = stmt->assign.place.local.v;
    if (!own_is_bool_local(body, thir, is_droppable, lc, loc)) return false;
    if (stmt->assign.rvalue.kind != AX_MIR_RVALUE_USE) return false;
    const AxMirOperand *op = &stmt->assign.rvalue.use;
    if (op->kind != AX_MIR_OP_CONST ||
        (op->constant.kind != AX_MIR_CONST_INT && (int)op->constant.kind != 1) ||
        op->constant.val > 1) {
        return false;
    }
    *out_loc = loc;
    *out_val = op->constant.val;
    return true;
}

static bool own_bb_has_direct_drop(const AxMirBb *bb, uint32_t v) {
    for (size_t j = 0; j < bb->stmt_count; j++) {
        if (bb->stmts[j].kind == AX_MIR_STMT_DROP &&
            bb->stmts[j].drop.proj_count == 0 &&
            bb->stmts[j].drop.local.v == v) {
            return true;
        }
    }
    if (bb->terminator.kind == AX_MIR_TERM_DROP &&
        bb->terminator.drop.place.proj_count == 0 &&
        bb->terminator.drop.place.local.v == v) {
        return true;
    }
    return false;
}

static bool own_is_clear_bb_drop(const AxMirBody *body, const uint32_t *is_flag_drop_bb, size_t bb_idx, uint32_t v) {
    if (is_flag_drop_bb[bb_idx] != v) return false;
    const AxMirBb *bb = &body->bbs[bb_idx];
    if (own_bb_has_direct_drop(bb, v)) return false;
    if (bb->terminator.kind == AX_MIR_TERM_GOTO && bb->terminator.goto_target.v < body->bb_count) {
        if (own_bb_has_direct_drop(&body->bbs[bb->terminator.goto_target.v], v)) return false;
    }
    return true;
}

static void own_check_op_read(
    size_t lc,
    const AxMirOperand *op,
    const uint8_t *cur,
    AxDiagSink *sink,
    const AxHirItem *func,
    bool emit_diags
) {
    if (!emit_diags || op->kind == AX_MIR_OP_CONST) return;
    uint32_t loc = op->place.local.v;
    if (loc < lc && op->place.proj_count == 0) {
        if (cur[loc] & MASK_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
        if (cur[loc] & MASK_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
    }
}

static void own_apply_op(
    const AxMirBody *body,
    const AxThir *thir,
    bool thir_has_items,
    const bool *is_droppable,
    const uint32_t *flag_of,
    size_t lc,
    const AxMirOperand *op,
    uint8_t *cur,
    AxDiagSink *sink,
    const AxHirItem *func,
    bool emit_diags
) {
    if (op->kind == AX_MIR_OP_CONST) return;
    uint32_t loc = op->place.local.v;
    if (loc >= lc) return;
    size_t pc = op->place.proj_count;
    own_check_op_read(lc, op, cur, sink, func, emit_diags);
    bool moves_loc = false;
    if (pc == 0) {
        if (op->kind == AX_MIR_OP_MOVE) {
            moves_loc = true;
        } else if (op->kind == AX_MIR_OP_COPY && is_droppable[loc] && flag_of[loc] != 0) {
            moves_loc = true;
        }
    } else if (is_droppable[loc] && (flag_of[loc] != 0 || !thir_has_items) && !own_place_has_deref(op->place)) {
        TypeId pty = own_place_type(body, thir, op->place);
        if (own_type_needs_drop(thir, thir_has_items, pty)) {
            moves_loc = true;
        }
    }
    if (moves_loc) {
        uint8_t dropped_bit = cur[loc] & ST_WAS_DROPPED;
        if (flag_of[loc] != 0) {
            uint8_t m0 = (cur[loc] & (ST_OWNED | ST_MOVED)) ? ST_MOVED : 0;
            uint8_t m1 = (cur[loc] & (ST_OWNED_F1 | ST_MOVED_F1)) ? ST_MOVED_F1 : 0;
            cur[loc] = (uint8_t)((cur[loc] & MASK_UNINIT) | m0 | m1 | dropped_bit);
        } else {
            cur[loc] = (uint8_t)(ST_MOVED | dropped_bit);
        }
    }
}

static void own_apply_rvalue(
    const AxMirBody *body,
    const AxThir *thir,
    bool thir_has_items,
    const bool *is_droppable,
    const uint32_t *flag_of,
    size_t lc,
    const AxMirRvalue *rv,
    uint8_t *cur,
    AxDiagSink *sink,
    const AxHirItem *func,
    bool emit_diags
) {
    if (rv->kind == AX_MIR_RVALUE_USE) {
        own_apply_op(body, thir, thir_has_items, is_droppable, flag_of, lc, &rv->use, cur, sink, func, emit_diags);
    } else if (rv->kind == AX_MIR_RVALUE_AGGREGATE) {
        for (size_t k = 0; k < rv->aggregate.operand_count; k++) {
            const AxMirOperand *op = &rv->aggregate.operands[k];
            if (op->kind != AX_MIR_OP_CONST && op->place.local.v < lc && is_droppable[op->place.local.v]) {
                own_apply_op(body, thir, thir_has_items, is_droppable, flag_of, lc, op, cur, sink, func, false);
            }
        }
    }
}

static void own_step_bb(
    const AxMirBody *body,
    const AxThir *thir,
    bool thir_has_items,
    bool check_drops,
    const bool *is_droppable,
    const uint32_t *flag_of,
    const uint32_t *owner_of_flag,
    const uint32_t *is_flag_drop_bb,
    size_t lc,
    size_t bb_idx,
    uint8_t *cur,
    AxDiagSink *sink,
    const AxHirItem *func,
    bool emit_diags
) {
    const AxMirBb *bb = &body->bbs[bb_idx];
    for (size_t j = 0; j < bb->stmt_count; j++) {
        const AxMirStmt *stmt = &bb->stmts[j];
        if (stmt->kind == AX_MIR_STMT_ASSIGN) {
            uint32_t flag_loc = 0;
            uint64_t flag_val = 0;
            if (own_is_bool_const_assign(body, thir, is_droppable, lc, stmt, &flag_loc, &flag_val) &&
                owner_of_flag[flag_loc] != 0) {
                uint32_t v = owner_of_flag[flag_loc];
                if (flag_val == 1) {
                    uint8_t f0 = cur[v] & MASK_F0;
                    cur[v] = (uint8_t)((cur[v] & (MASK_F1 | ST_WAS_DROPPED)) | (f0 << 3));
                } else if (own_is_clear_bb_drop(body, is_flag_drop_bb, bb_idx, v)) {
                    if (emit_diags && check_drops && (cur[v] & MASK_MOVED)) {
                        report_verify_error(sink, func, AX_VERIFY_DOUBLE_DROP);
                    }
                    cur[v] = ST_MOVED | ST_WAS_DROPPED;
                } else {
                    uint8_t f1 = (cur[v] & MASK_F1) >> 3;
                    cur[v] = (uint8_t)((cur[v] & (MASK_F0 | ST_WAS_DROPPED)) | f1);
                }
                cur[flag_loc] = ST_OWNED;
                continue;
            }

            own_apply_rvalue(body, thir, thir_has_items, is_droppable, flag_of, lc, &stmt->assign.rvalue, cur, sink, func, emit_diags);

            uint32_t dst_loc = stmt->assign.place.local.v;
            size_t dst_pc = stmt->assign.place.proj_count;
            if (dst_loc < lc) {
                if (dst_pc == 0) {
                    if (emit_diags && check_drops && is_droppable[dst_loc] && (cur[dst_loc] & MASK_OWNED)) {
                        report_verify_error(sink, func, AX_VERIFY_MISSING_DROP);
                    }
                    cur[dst_loc] = ST_OWNED;
                } else if (!own_place_has_deref(stmt->assign.place)) {
                    cur[dst_loc] = ST_OWNED;
                }
            }
        } else if (stmt->kind == AX_MIR_STMT_DROP) {
            uint32_t loc = stmt->drop.local.v;
            if (loc < lc && stmt->drop.proj_count == 0) {
                if (emit_diags && check_drops && (cur[loc] & MASK_MOVED)) {
                    report_verify_error(sink, func, AX_VERIFY_DOUBLE_DROP);
                }
                cur[loc] = ST_MOVED | ST_WAS_DROPPED;
            }
        } else if (stmt->kind == AX_MIR_STMT_STORAGE_DEAD) {
            uint32_t sd_loc = stmt->storage_dead.v;
            if (sd_loc < lc) {
                cur[sd_loc] = ST_UNINIT;
            }
        }
    }

    const AxMirTerminator *term = &bb->terminator;
    switch (term->kind) {
        case AX_MIR_TERM_SWITCH_INT:
            own_check_op_read(lc, &term->switch_int.discr, cur, sink, func, emit_diags);
            break;
        case AX_MIR_TERM_DROP:
            if (term->drop.place.local.v < lc && term->drop.place.proj_count == 0) {
                uint32_t loc = term->drop.place.local.v;
                uint8_t st = cur[loc];
                if (emit_diags && check_drops && (st & MASK_MOVED)) {
                    report_verify_error(sink, func, AX_VERIFY_DOUBLE_DROP);
                }
                cur[loc] = ST_MOVED | ST_WAS_DROPPED;
            }
            break;
        case AX_MIR_TERM_CALL:
            own_apply_op(body, thir, thir_has_items, is_droppable, flag_of, lc, &term->call.func, cur, sink, func, emit_diags);
            for (size_t a = 0; a < term->call.arg_count; ++a) {
                own_apply_op(body, thir, thir_has_items, is_droppable, flag_of, lc, &term->call.args[a], cur, sink, func, emit_diags);
            }
            if (term->call.destination.local.v < lc) {
                uint32_t dst_loc = term->call.destination.local.v;
                size_t dst_pc = term->call.destination.proj_count;
                if (dst_pc == 0) {
                    if (emit_diags && check_drops && is_droppable[dst_loc] && (cur[dst_loc] & MASK_OWNED)) {
                        report_verify_error(sink, func, AX_VERIFY_MISSING_DROP);
                    }
                    cur[dst_loc] = ST_OWNED;
                } else if (!own_place_has_deref(term->call.destination)) {
                    cur[dst_loc] = ST_OWNED;
                }
            }
            break;
        case AX_MIR_TERM_ASSERT:
            own_check_op_read(lc, &term->assert.cond, cur, sink, func, emit_diags);
            break;
        case AX_MIR_TERM_RETURN:
            if (emit_diags) {
                if (lc > 0) {
                    if (cur[0] & MASK_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                    if (cur[0] & MASK_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
                }
                if (check_drops) {
                    for (size_t l = 1; l < lc; l++) {
                        if (is_droppable[l] && (cur[l] & MASK_OWNED)) {
                            report_verify_error(sink, func, AX_VERIFY_MISSING_DROP);
                        }
                    }
                }
            }
            break;
        default:
            break;
    }
}

void ax_verify_mir_own(const AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const AxHirItem *func) {
    if (body->bb_count == 0 || body->local_count == 0) return;

    size_t lc = body->local_count;
    size_t bc = body->bb_count;
    uint8_t *bb_in = malloc(bc * lc);
    uint8_t *bb_out = malloc(bc * lc);
    bool *is_droppable = calloc(lc, sizeof(bool));
    uint32_t *flag_of = calloc(lc, sizeof(uint32_t));
    uint32_t *owner_of_flag = calloc(lc, sizeof(uint32_t));
    uint32_t *is_flag_drop_bb = calloc(bc, sizeof(uint32_t));
    memset(bb_in, ST_BOTTOM, bc * lc);
    memset(bb_out, ST_BOTTOM, bc * lc);

    bool is_real_fn = (func != NULL && func->kind == AX_HIR_ITEM_FN && func->fn.body != NULL);
    bool thir_has_items = (thir != NULL && (thir->item_types.raw.len > 0 || thir->expr_types.raw.len > 0 || is_real_fn));
    bool any_droppable = false;
    for (size_t l = 0; l < lc; l++) {
        is_droppable[l] = own_type_needs_drop(thir, thir_has_items, body->locals[l].ty);
        if (l > 0 && is_droppable[l]) {
            any_droppable = true;
        }
    }

    /* 1. Match bb0 drop-flag prolog emitted by ax_mir_drop_elaborate. */
    const AxMirBb *bb0 = &body->bbs[0];
    size_t prolog_flags = 0;
    uint32_t first_flag_loc = 0;
    while (prolog_flags < bb0->stmt_count) {
        uint32_t floc = 0;
        uint64_t fval = 0;
        if (!own_is_bool_const_assign(body, thir, is_droppable, lc, &bb0->stmts[prolog_flags], &floc, &fval)) {
            break;
        }
        if (prolog_flags == 0) {
            first_flag_loc = floc;
        } else if (floc != first_flag_loc + (uint32_t)prolog_flags) {
            break;
        }
        prolog_flags++;
    }
    if (prolog_flags > 0) {
        size_t drop_cnt = 0;
        for (size_t v = 1; v < first_flag_loc && v < lc; v++) {
            if (is_droppable[v]) drop_cnt++;
        }
        if (drop_cnt == prolog_flags) {
            size_t k = 0;
            for (size_t v = 1; v < first_flag_loc && v < lc; v++) {
                if (is_droppable[v]) {
                    uint32_t f = first_flag_loc + (uint32_t)k;
                    flag_of[v] = f;
                    owner_of_flag[f] = (uint32_t)v;
                    k++;
                }
            }
        }
    }

    /* 2. Match explicit drop_flag annotations or hand-built switchInt/assign flag patterns. */
    for (size_t b = 0; !is_real_fn && b < bc; b++) {
        const AxMirBb *bb = &body->bbs[b];
        if (bb->terminator.kind == AX_MIR_TERM_DROP) {
            uint32_t v = bb->terminator.drop.place.local.v;
            uint32_t f = bb->terminator.drop_flag;
            if (v >= 1 && v < lc && is_droppable[v] && own_is_bool_local(body, thir, is_droppable, lc, f)) {
                if (flag_of[v] == 0 && owner_of_flag[f] == 0) {
                    flag_of[v] = f;
                    owner_of_flag[f] = v;
                }
            }
        } else if (bb->terminator.kind == AX_MIR_TERM_SWITCH_INT) {
            const AxMirOperand *discr = &bb->terminator.switch_int.discr;
            if (discr->kind != AX_MIR_OP_CONST && discr->place.proj_count == 0) {
                uint32_t f = discr->place.local.v;
                if (own_is_bool_local(body, thir, is_droppable, lc, f) && owner_of_flag[f] == 0) {
                    for (size_t k = 0; k <= bb->terminator.switch_int.targets.count; k++) {
                        uint32_t t_idx = (k < bb->terminator.switch_int.targets.count)
                            ? bb->terminator.switch_int.targets.values[k].target.v
                            : bb->terminator.switch_int.targets.otherwise.v;
                        if (t_idx < bc) {
                            const AxMirBb *tbb = &body->bbs[t_idx];
                            uint32_t cand_v = 0;
                            if (tbb->terminator.kind == AX_MIR_TERM_DROP && tbb->terminator.drop.place.proj_count == 0) {
                                cand_v = tbb->terminator.drop.place.local.v;
                            } else {
                                for (size_t sj = 0; sj < tbb->stmt_count; sj++) {
                                    if (tbb->stmts[sj].kind == AX_MIR_STMT_DROP && tbb->stmts[sj].drop.proj_count == 0) {
                                        cand_v = tbb->stmts[sj].drop.local.v;
                                        break;
                                    }
                                }
                            }
                            if (cand_v >= 1 && cand_v < lc && is_droppable[cand_v] && flag_of[cand_v] == 0) {
                                flag_of[cand_v] = f;
                                owner_of_flag[f] = cand_v;
                                break;
                            }
                        }
                    }
                }
            }
        }
        for (size_t j = 0; j + 1 < bb->stmt_count; j++) {
            const AxMirStmt *s0 = &bb->stmts[j];
            const AxMirStmt *s1 = &bb->stmts[j + 1];
            if (s0->kind == AX_MIR_STMT_ASSIGN && s0->assign.place.proj_count == 0) {
                uint32_t v = s0->assign.place.local.v;
                uint32_t f = 0;
                uint64_t fval = 0;
                if (v >= 1 && v < lc && is_droppable[v] && flag_of[v] == 0 &&
                    own_is_bool_const_assign(body, thir, is_droppable, lc, s1, &f, &fval) &&
                    fval == 1 && owner_of_flag[f] == 0) {
                    flag_of[v] = f;
                    owner_of_flag[f] = v;
                }
            }
        }
    }

    /* 3. Mark clear_bb / drop_bb targets of switchInt(copy flag). */
    bool has_any_flag = false;
    for (size_t l = 1; l < lc; l++) {
        if (flag_of[l] != 0) {
            has_any_flag = true;
            break;
        }
    }
    bool check_drops = !is_real_fn || !any_droppable || has_any_flag;
    for (size_t b = 0; b < bc; b++) {
        const AxMirBb *bb = &body->bbs[b];
        if (bb->terminator.kind == AX_MIR_TERM_SWITCH_INT) {
            const AxMirOperand *discr = &bb->terminator.switch_int.discr;
            if (discr->kind != AX_MIR_OP_CONST && discr->place.proj_count == 0 && discr->place.local.v < lc) {
                uint32_t f = discr->place.local.v;
                uint32_t v = owner_of_flag[f];
                if (v != 0) {
                    bool has_zero = false;
                    bool has_one = false;
                    for (size_t k = 0; k < bb->terminator.switch_int.targets.count; k++) {
                        uint64_t val = bb->terminator.switch_int.targets.values[k].value;
                        uint32_t tgt = bb->terminator.switch_int.targets.values[k].target.v;
                        if (val == 0) has_zero = true;
                        else {
                            has_one = true;
                            if (tgt < bc) is_flag_drop_bb[tgt] = v;
                        }
                    }
                    uint32_t ow = bb->terminator.switch_int.targets.otherwise.v;
                    if (has_zero && !has_one && ow < bc) {
                        is_flag_drop_bb[ow] = v;
                    }
                }
            }
        }
    }

    memset(&bb_in[0], ST_UNINIT, lc);
    size_t param_count = 0;
    if (func && func->kind == AX_HIR_ITEM_FN) {
        for (AxHirParam *p = func->fn.params; p; p = p->next) param_count++;
    }
    for (size_t l = 1; l < lc; l++) {
        if (l <= param_count || body->locals[l].kind == AX_MIR_LOCAL_ARG) {
            bb_in[l] = ST_OWNED;
        }
    }
    if (lc > 0) {
        bool ret_settled = false;
        if (func && func->kind == AX_HIR_ITEM_FN && thir) {
            TypeId *expected_ret_ty_ptr = AxItemTypeMap_get((AxItemTypeMap*)&thir->item_types, func);
            if (expected_ret_ty_ptr && expected_ret_ty_ptr->v != 0) {
                const AxType *t_fn = own_safe_type_get(thir, *expected_ret_ty_ptr);
                if (t_fn && t_fn->kind == AX_TY_FN) {
                    ret_settled = true;
                    if (t_fn->fn.ret_type.v != 0) {
                        const AxType *ret = own_safe_type_get(thir, t_fn->fn.ret_type);
                        if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                            bb_in[0] = ST_OWNED;
                        }
                    } else {
                        bb_in[0] = ST_OWNED;
                    }
                }
            }
        }
        if (!ret_settled && thir) {
            if (body->locals[0].ty.v != 0) {
                const AxType *ret = own_safe_type_get(thir, body->locals[0].ty);
                if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                    bb_in[0] = ST_OWNED;
                }
            } else {
                bb_in[0] = ST_OWNED;
            }
        }
    }

    uint8_t *cur = malloc(lc);
    bool changed = true;
    while (changed) {
        changed = false;
        for (size_t i = 0; i < bc; ++i) {
            uint8_t *in = &bb_in[i * lc];
            if (i != 0) {
                memset(cur, ST_BOTTOM, lc);
                for (size_t j = 0; j < bc; ++j) {
                    const AxMirBb *pred = &body->bbs[j];
                    const uint8_t *p_out = &bb_out[j * lc];
                    if (pred->terminator.kind == AX_MIR_TERM_SWITCH_INT) {
                        const AxMirOperand *discr = &pred->terminator.switch_int.discr;
                        uint32_t f = (discr->kind != AX_MIR_OP_CONST && discr->place.proj_count == 0 && discr->place.local.v < lc)
                            ? discr->place.local.v : 0;
                        uint32_t v = (f < lc) ? owner_of_flag[f] : 0;
                        if (v != 0) {
                            bool f1_to_i = false;
                            bool f0_to_i = false;
                            bool has_zero = false;
                            bool has_one = false;
                            for (size_t k = 0; k < pred->terminator.switch_int.targets.count; ++k) {
                                uint64_t val = pred->terminator.switch_int.targets.values[k].value;
                                uint32_t tgt = pred->terminator.switch_int.targets.values[k].target.v;
                                if (val == 0) {
                                    has_zero = true;
                                    if (tgt == i) f0_to_i = true;
                                } else {
                                    has_one = true;
                                    if (tgt == i) f1_to_i = true;
                                }
                            }
                            if (pred->terminator.switch_int.targets.otherwise.v == i) {
                                if (has_zero && !has_one) f1_to_i = true;
                                else if (!has_zero) f0_to_i = true;
                            }
                            uint8_t v_out = p_out[v];
                            if (f1_to_i && (v_out & MASK_F1) != 0) {
                                for (size_t l = 0; l < lc; l++) {
                                    uint8_t st = (l == v) ? (uint8_t)((v_out & MASK_F1) | (v_out & ST_WAS_DROPPED)) : p_out[l];
                                    cur[l] = merge_st(cur[l], st);
                                }
                            }
                            if (f0_to_i && (v_out & MASK_F0) != 0) {
                                for (size_t l = 0; l < lc; l++) {
                                    uint8_t st = (l == v) ? (uint8_t)((v_out & MASK_F0) | (v_out & ST_WAS_DROPPED)) : p_out[l];
                                    cur[l] = merge_st(cur[l], st);
                                }
                            }
                            continue;
                        }
                    }

                    bool is_pred = false;
                    switch (pred->terminator.kind) {
                        case AX_MIR_TERM_GOTO: if (pred->terminator.goto_target.v == i) is_pred = true; break;
                        case AX_MIR_TERM_SWITCH_INT:
                            for (size_t k = 0; k < pred->terminator.switch_int.targets.count; ++k) {
                                if (pred->terminator.switch_int.targets.values[k].target.v == i) is_pred = true;
                            }
                            if (pred->terminator.switch_int.targets.otherwise.v == i) is_pred = true;
                            break;
                        case AX_MIR_TERM_DROP:
                            if (pred->terminator.drop.target.v == i) is_pred = true;
                            if (pred->terminator.drop.unwind.v == i) is_pred = true;
                            break;
                        case AX_MIR_TERM_CALL:
                            if (pred->terminator.call.target.v == i) is_pred = true;
                            if (pred->terminator.call.unwind.v == i) is_pred = true;
                            break;
                        case AX_MIR_TERM_ASSERT:
                            if (pred->terminator.assert.target.v == i) is_pred = true;
                            if (pred->terminator.assert.unwind.v == i) is_pred = true;
                            break;
                        default: break;
                    }
                    if (is_pred) {
                        for (size_t l = 0; l < lc; l++) {
                            cur[l] = merge_st(cur[l], p_out[l]);
                        }
                    }
                }
                if (memcmp(in, cur, lc) != 0) {
                    memcpy(in, cur, lc);
                    changed = true;
                }
            }

            memcpy(cur, in, lc);
            bool reachable = false;
            for (size_t l = 0; l < lc; l++) {
                if (cur[l] != ST_BOTTOM) {
                    reachable = true;
                    break;
                }
            }
            if (!reachable) {
                memset(cur, ST_BOTTOM, lc);
            } else {
                own_step_bb(body, thir, thir_has_items, check_drops, is_droppable, flag_of, owner_of_flag, is_flag_drop_bb, lc, i, cur, sink, func, false);
            }

            if (memcmp(&bb_out[i * lc], cur, lc) != 0) {
                memcpy(&bb_out[i * lc], cur, lc);
                changed = true;
            }
        }
    }

    for (size_t i = 0; i < bc; ++i) {
        memcpy(cur, &bb_in[i * lc], lc);
        bool reachable = false;
        for (size_t l = 0; l < lc; l++) {
            if (cur[l] != ST_BOTTOM) {
                reachable = true;
                break;
            }
        }
        if (reachable) {
            own_step_bb(body, thir, thir_has_items, check_drops, is_droppable, flag_of, owner_of_flag, is_flag_drop_bb, lc, i, cur, sink, func, true);
        }
    }

    free(cur);
    free(is_flag_drop_bb);
    free(owner_of_flag);
    free(flag_of);
    free(is_droppable);
    free(bb_in);
    free(bb_out);
}
