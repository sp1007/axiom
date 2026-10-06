#include "verify/verify.h"
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
            if ((p).local.v < body->local_count && !get_bit(cur, (p).local.v)) { \
                report_verify_error(sink, func, AX_VERIFY_UNINIT_USE); \
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
                        if (lhs_ty.v != 0 && rhs_ty.v != 0 && lhs_ty.v == rhs_ty.v) {
                            if (is_cmp && thir) src_ty = thir->interner.t_bool;
                            else src_ty = lhs_ty;
                        } else if (lhs_ty.v != 0 && rhs_ty.v != 0 && lhs_ty.v != rhs_ty.v) {
                            report_verify_error(sink, func, AX_VERIFY_TYPE_MISMATCH);
                            if (is_cmp && thir) src_ty = thir->interner.t_bool;
                            else src_ty = lhs_ty;
                        }
                        break;
                    }
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
                
                if (dest_ty.v != 0 && src_ty.v != 0 && dest_ty.v != src_ty.v) {
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
                if (body->local_count > 0 && func != NULL && !get_bit(cur, 0)) {
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
