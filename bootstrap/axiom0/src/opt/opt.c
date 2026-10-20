#include "opt.h"
#include "verify/verify.h"
#include "types/types.h"
#include <string.h>
#include <stdlib.h>

static bool do_const_fold_binop(AxMirBinOp op, const AxMirConst *lhs, const AxMirConst *rhs, AxMirConst *out, TypeInterner *in) {
    if (lhs->kind != AX_MIR_CONST_INT || rhs->kind != AX_MIR_CONST_INT) return false;
    if (lhs->ty.v != rhs->ty.v) return false;
    
    bool is_signed = ax_type_is_signed(lhs->ty, in);
    uint32_t bits = ax_type_size(lhs->ty, in) * 8;
    if (bits == 0 || bits > 64) return false; // Should not happen for standard ints
    
    uint64_t l = lhs->val;
    uint64_t r = rhs->val;
    uint64_t res = 0;
    
    // Sign extend for signed operations
    int64_t sl = (int64_t)l;
    int64_t sr = (int64_t)r;
    if (is_signed && bits < 64) {
        uint64_t shift = 64 - bits;
        sl = (int64_t)(l << shift) >> shift;
        sr = (int64_t)(r << shift) >> shift;
    }
    
    switch (op) {
        case AX_MIR_BINOP_ADD: {
            if (is_signed) {
                int64_t sres;
                if (__builtin_add_overflow(sl, sr, &sres)) return false;
                // Check if result fits in 'bits'
                int64_t min_val = bits == 64 ? INT64_MIN : -(1LL << (bits - 1));
                int64_t max_val = bits == 64 ? INT64_MAX : (1LL << (bits - 1)) - 1;
                if (sres < min_val || sres > max_val) return false;
                res = (uint64_t)sres;
            } else {
                if (__builtin_add_overflow(l, r, &res)) return false;
                if (bits < 64 && res >= (1ULL << bits)) return false;
            }
            break;
        }
        case AX_MIR_BINOP_SUB: {
            if (is_signed) {
                int64_t sres;
                if (__builtin_sub_overflow(sl, sr, &sres)) return false;
                int64_t min_val = bits == 64 ? INT64_MIN : -(1LL << (bits - 1));
                int64_t max_val = bits == 64 ? INT64_MAX : (1LL << (bits - 1)) - 1;
                if (sres < min_val || sres > max_val) return false;
                res = (uint64_t)sres;
            } else {
                if (__builtin_sub_overflow(l, r, &res)) return false;
                // Since unsigned can't be negative, the above builtin checks if l < r
            }
            break;
        }
        case AX_MIR_BINOP_MUL: {
            if (is_signed) {
                int64_t sres;
                if (__builtin_mul_overflow(sl, sr, &sres)) return false;
                int64_t min_val = bits == 64 ? INT64_MIN : -(1LL << (bits - 1));
                int64_t max_val = bits == 64 ? INT64_MAX : (1LL << (bits - 1)) - 1;
                if (sres < min_val || sres > max_val) return false;
                res = (uint64_t)sres;
            } else {
                if (__builtin_mul_overflow(l, r, &res)) return false;
                if (bits < 64 && res >= (1ULL << bits)) return false;
            }
            break;
        }
        case AX_MIR_BINOP_DIV: {
            if (r == 0) return false;
            if (is_signed) {
                if (sl == (bits == 64 ? INT64_MIN : -(1LL << (bits - 1))) && sr == -1) return false;
                res = (uint64_t)(sl / sr);
            } else {
                res = l / r;
            }
            break;
        }
        case AX_MIR_BINOP_REM: {
            if (r == 0) return false;
            if (is_signed) {
                if (sl == (bits == 64 ? INT64_MIN : -(1LL << (bits - 1))) && sr == -1) return false;
                res = (uint64_t)(sl % sr);
            } else {
                res = l % r;
            }
            break;
        }
        /* T134: same semantics as the interpreter and the native backend: modulo 2^bits, never fails. */
        case AX_MIR_BINOP_WRAPPING_ADD: res = l + r; out->ty = lhs->ty; break;
        case AX_MIR_BINOP_WRAPPING_SUB: res = l - r; out->ty = lhs->ty; break;
        case AX_MIR_BINOP_WRAPPING_MUL: res = l * r; out->ty = lhs->ty; break;
        case AX_MIR_BINOP_BIT_XOR: res = l ^ r; break;
        case AX_MIR_BINOP_BIT_AND: res = l & r; break;
        case AX_MIR_BINOP_BIT_OR:  res = l | r; break;
        case AX_MIR_BINOP_SHL: {
            if (r >= bits) return false; // Shift amount out of range panic
            res = l << r;
            break;
        }
        case AX_MIR_BINOP_SHR: {
            if (r >= bits) return false; // Shift amount out of range panic
            if (is_signed) {
                res = (uint64_t)(sl >> r);
            } else {
                res = l >> r;
            }
            break;
        }
        case AX_MIR_BINOP_EQ: res = (l == r); out->ty = in->t_bool; break;
        case AX_MIR_BINOP_NE: res = (l != r); out->ty = in->t_bool; break;
        case AX_MIR_BINOP_LT: res = is_signed ? (sl < sr) : (l < r); out->ty = in->t_bool; break;
        case AX_MIR_BINOP_LE: res = is_signed ? (sl <= sr) : (l <= r); out->ty = in->t_bool; break;
        case AX_MIR_BINOP_GT: res = is_signed ? (sl > sr) : (l > r); out->ty = in->t_bool; break;
        case AX_MIR_BINOP_GE: res = is_signed ? (sl >= sr) : (l >= r); out->ty = in->t_bool; break;
        default: return false;
    }
    
    // Mask res to the type size
    if (bits < 64) {
        res &= (1ULL << bits) - 1;
    }
    
    if (op < AX_MIR_BINOP_EQ) {
        out->ty = lhs->ty;
    }
    out->kind = AX_MIR_CONST_INT;
    out->val = res;
    return true;
}

static bool do_const_fold_unop(AxMirUnOp op, const AxMirConst *operand, AxMirConst *out, TypeInterner *in) {
    if (operand->kind != AX_MIR_CONST_INT) return false;
    uint32_t bits = ax_type_size(operand->ty, in) * 8;
    if (bits == 0 || bits > 64) return false;
    
    uint64_t val = operand->val;
    uint64_t res = 0;
    
    switch (op) {
        case AX_MIR_UNOP_NOT:
            if (operand->ty.v != in->t_bool.v) return false;
            res = (val == 0) ? 1 : 0;
            break;
        case AX_MIR_UNOP_BITNOT:
            res = ~val;
            break;
        case AX_MIR_UNOP_NEG: {
            bool is_signed = ax_type_is_signed(operand->ty, in);
            if (!is_signed) return false;
            // Sign extend
            int64_t sval = (int64_t)val;
            if (bits < 64) {
                uint64_t shift = 64 - bits;
                sval = (int64_t)(val << shift) >> shift;
            }
            if (sval == (bits == 64 ? INT64_MIN : -(1LL << (bits - 1)))) return false; // overflow
            res = (uint64_t)(-sval);
            break;
        }
        default: return false;
    }
    
    if (bits < 64) {
        res &= (1ULL << bits) - 1;
    }
    
    out->ty = operand->ty;
    out->kind = AX_MIR_CONST_INT;
    out->val = res;
    return true;
}

static void ax_opt_const_fold(AxMirBody *body, AxThir *thir) {
    bool changed = true;
    while (changed) {
        changed = false;
        for (size_t i = 0; i < body->bb_count; ++i) {
            AxMirBb *bb = &body->bbs[i];
            for (size_t j = 0; j < bb->stmt_count; ++j) {
                AxMirStmt *stmt = &bb->stmts[j];
                if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                    AxMirRvalue *rv = &stmt->assign.rvalue;
                    if (rv->kind == AX_MIR_RVALUE_BINARY_OP || rv->kind == AX_MIR_RVALUE_OVERFLOWS_BINARY_OP) {
                        if (rv->binary_op.lhs.kind == AX_MIR_OP_CONST && rv->binary_op.rhs.kind == AX_MIR_OP_CONST) {
                            AxMirConst out;
                            if (do_const_fold_binop(rv->binary_op.op, &rv->binary_op.lhs.constant, &rv->binary_op.rhs.constant, &out, &thir->interner)) {
                                if (rv->kind == AX_MIR_RVALUE_OVERFLOWS_BINARY_OP) {
                                    rv->kind = AX_MIR_RVALUE_USE;
                                    rv->use.kind = AX_MIR_OP_CONST;
                                    rv->use.constant.kind = AX_MIR_CONST_INT;
                                    rv->use.constant.val = 0; // it didn't overflow
                                    rv->use.constant.ty = body->locals[stmt->assign.place.local.v].ty;
                                    changed = true;
                                } else {
                                    rv->kind = AX_MIR_RVALUE_USE;
                                    rv->use.kind = AX_MIR_OP_CONST;
                                    rv->use.constant = out;
                                    changed = true;
                                }
                            }
                        }
                    } else if (rv->kind == AX_MIR_RVALUE_UNARY_OP) {
                        if (rv->unary_op.operand.kind == AX_MIR_OP_CONST) {
                            AxMirConst out;
                            if (do_const_fold_unop(rv->unary_op.op, &rv->unary_op.operand.constant, &out, &thir->interner)) {
                                rv->kind = AX_MIR_RVALUE_USE;
                                rv->use.kind = AX_MIR_OP_CONST;
                                rv->use.constant = out;
                                changed = true;
                            }
                        }
                    }
                }
            }
        }
    }
}

static void ax_opt_cfg_simplify(AxMirBody *body) {
    bool changed = true;
    while (changed) {
        changed = false;
        for (size_t i = 0; i < body->bb_count; ++i) {
            AxMirBb *bb = &body->bbs[i];
            if (bb->terminator.kind == AX_MIR_TERM_SWITCH_INT) {
                if (bb->terminator.switch_int.discr.kind == AX_MIR_OP_CONST && 
                    bb->terminator.switch_int.discr.constant.kind == AX_MIR_CONST_INT) {
                    
                    uint64_t val = bb->terminator.switch_int.discr.constant.val;
                    AxMirBbId target = bb->terminator.switch_int.targets.otherwise;
                    
                    for (size_t j = 0; j < bb->terminator.switch_int.targets.count; ++j) {
                        if (bb->terminator.switch_int.targets.values[j].value == val) {
                            target = bb->terminator.switch_int.targets.values[j].target;
                            break;
                        }
                    }
                    
                    bb->terminator.kind = AX_MIR_TERM_GOTO;
                    bb->terminator.goto_target = target;
                    changed = true;
                }
            }
        }
        
        // Remove unreachable blocks
        bool *reachable = calloc(body->bb_count, sizeof(bool));
        if (body->bb_count > 0) {
            reachable[0] = true;
            bool reach_changed = true;
            while (reach_changed) {
                reach_changed = false;
                for (size_t i = 0; i < body->bb_count; ++i) {
                    if (!reachable[i]) continue;
                    AxMirBb *bb = &body->bbs[i];
                    if (bb->terminator.kind == AX_MIR_TERM_GOTO) {
                        if (!reachable[bb->terminator.goto_target.v]) {
                            reachable[bb->terminator.goto_target.v] = true;
                            reach_changed = true;
                        }
                    } else if (bb->terminator.kind == AX_MIR_TERM_SWITCH_INT) {
                        for (size_t j = 0; j < bb->terminator.switch_int.targets.count; ++j) {
                            if (!reachable[bb->terminator.switch_int.targets.values[j].target.v]) {
                                reachable[bb->terminator.switch_int.targets.values[j].target.v] = true;
                                reach_changed = true;
                            }
                        }
                        if (!reachable[bb->terminator.switch_int.targets.otherwise.v]) {
                            reachable[bb->terminator.switch_int.targets.otherwise.v] = true;
                            reach_changed = true;
                        }
                    } else if (bb->terminator.kind == AX_MIR_TERM_DROP) {
                        if (!reachable[bb->terminator.drop.target.v]) {
                            reachable[bb->terminator.drop.target.v] = true;
                            reach_changed = true;
                        }
                        if (bb->terminator.drop.unwind.v != 0 && !reachable[bb->terminator.drop.unwind.v]) {
                            reachable[bb->terminator.drop.unwind.v] = true;
                            reach_changed = true;
                        }
                    } else if (bb->terminator.kind == AX_MIR_TERM_CALL) {
                        if (!reachable[bb->terminator.call.target.v]) {
                            reachable[bb->terminator.call.target.v] = true;
                            reach_changed = true;
                        }
                        if (bb->terminator.call.unwind.v != 0 && !reachable[bb->terminator.call.unwind.v]) {
                            reachable[bb->terminator.call.unwind.v] = true;
                            reach_changed = true;
                        }
                    } else if (bb->terminator.kind == AX_MIR_TERM_ASSERT) {
                        if (!reachable[bb->terminator.assert.target.v]) {
                            reachable[bb->terminator.assert.target.v] = true;
                            reach_changed = true;
                        }
                        if (bb->terminator.assert.unwind.v != 0 && !reachable[bb->terminator.assert.unwind.v]) {
                            reachable[bb->terminator.assert.unwind.v] = true;
                            reach_changed = true;
                        }
                    }
                }
            }
        }
        
        for (size_t i = 0; i < body->bb_count; ++i) {
            if (!reachable[i]) {
                AxMirBb *bb = &body->bbs[i];
                if (bb->terminator.kind != AX_MIR_TERM_UNREACHABLE) {
                    bb->stmt_count = 0;
                    bb->terminator.kind = AX_MIR_TERM_UNREACHABLE;
                    changed = true;
                }
            }
        }
        free(reachable);
    }
}

static void count_place_uses(AxMirPlace *p, size_t *use_counts) {
    for (size_t i = 0; i < p->proj_count; i++) {
        if (p->projs[i].kind == AX_MIR_PROJ_INDEX) {
            use_counts[p->projs[i].index_local.v]++;
        } else if (p->projs[i].kind == AX_MIR_PROJ_SUB_SLICE) {
            if (p->projs[i].sub_slice.has_from) use_counts[p->projs[i].sub_slice.from_local.v]++;
            if (p->projs[i].sub_slice.has_to) use_counts[p->projs[i].sub_slice.to_local.v]++;
        }
    }
}

static void count_place_full_use(AxMirPlace *p, size_t *use_counts) {
    use_counts[p->local.v]++;
    count_place_uses(p, use_counts);
}

static void count_operand_uses(AxMirOperand *op, size_t *use_counts) {
    if (op->kind == AX_MIR_OP_COPY || op->kind == AX_MIR_OP_MOVE) {
        count_place_full_use(&op->place, use_counts);
    }
}

static bool rvalue_is_pure(AxMirRvalue *rv) {
    if (rv->kind == AX_MIR_RVALUE_USE) return true;
    if (rv->kind == AX_MIR_RVALUE_REF) return true;
    if (rv->kind == AX_MIR_RVALUE_CAST) return true;
    if (rv->kind == AX_MIR_RVALUE_AGGREGATE) return true;
    if (rv->kind == AX_MIR_RVALUE_DISCRIMINANT) return true;
    if (rv->kind == AX_MIR_RVALUE_LEN) return true;
    return false;
}

static void ax_opt_dce(AxMirBody *body) {
    bool changed = true;
    while (changed) {
        changed = false;
        size_t *use_counts = calloc(body->local_count, sizeof(size_t));
        
        // Local 0 is return value
        if (body->local_count > 0) {
            use_counts[0] = 1;
        }
        
        for (size_t i = 0; i < body->bb_count; ++i) {
            AxMirBb *bb = &body->bbs[i];
            if (bb->terminator.kind == AX_MIR_TERM_UNREACHABLE) continue;
            
            for (size_t j = 0; j < bb->stmt_count; ++j) {
                AxMirStmt *stmt = &bb->stmts[j];
                if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                    if (stmt->assign.place.proj_count > 0) {
                        use_counts[stmt->assign.place.local.v]++;
                    }
                    count_place_uses(&stmt->assign.place, use_counts);
                    
                    AxMirRvalue *rv = &stmt->assign.rvalue;
                    if (rv->kind == AX_MIR_RVALUE_USE) {
                        count_operand_uses(&rv->use, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_REPEAT) {
                        count_operand_uses(&rv->repeat.op, use_counts);
                        count_operand_uses(&rv->repeat.count, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_REF) {
                        count_place_full_use(&rv->ref.place, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_LEN) {
                        count_place_full_use(&rv->len, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_CAST) {
                        count_operand_uses(&rv->cast.op, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_BINARY_OP || rv->kind == AX_MIR_RVALUE_OVERFLOWS_BINARY_OP) {
                        count_operand_uses(&rv->binary_op.lhs, use_counts);
                        count_operand_uses(&rv->binary_op.rhs, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_UNARY_OP) {
                        count_operand_uses(&rv->unary_op.operand, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_DISCRIMINANT) {
                        count_place_full_use(&rv->discriminant, use_counts);
                    } else if (rv->kind == AX_MIR_RVALUE_AGGREGATE) {
                        for (size_t k = 0; k < rv->aggregate.operand_count; ++k) {
                            count_operand_uses(&rv->aggregate.operands[k], use_counts);
                        }
                    }
                }
            }
            
            AxMirTerminator *term = &bb->terminator;
            if (term->kind == AX_MIR_TERM_SWITCH_INT) {
                count_operand_uses(&term->switch_int.discr, use_counts);
            } else if (term->kind == AX_MIR_TERM_DROP) {
                count_place_full_use(&term->drop.place, use_counts);
            } else if (term->kind == AX_MIR_TERM_CALL) {
                count_operand_uses(&term->call.func, use_counts);
                for (size_t k = 0; k < term->call.arg_count; ++k) {
                    count_operand_uses(&term->call.args[k], use_counts);
                }
                if (term->call.destination.proj_count > 0) {
                    use_counts[term->call.destination.local.v]++;
                }
                count_place_uses(&term->call.destination, use_counts);
            } else if (term->kind == AX_MIR_TERM_ASSERT) {
                count_operand_uses(&term->assert.cond, use_counts);
            }
        }
        
        for (size_t i = 0; i < body->bb_count; ++i) {
            AxMirBb *bb = &body->bbs[i];
            if (bb->terminator.kind == AX_MIR_TERM_UNREACHABLE) continue;
            
            size_t write_idx = 0;
            for (size_t j = 0; j < bb->stmt_count; ++j) {
                AxMirStmt *stmt = &bb->stmts[j];
                bool keep = true;
                
                if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                    if (stmt->assign.place.proj_count == 0 && use_counts[stmt->assign.place.local.v] == 0) {
                        if (rvalue_is_pure(&stmt->assign.rvalue)) {
                            keep = false;
                        }
                    }
                } else if (stmt->kind == AX_MIR_STMT_STORAGE_LIVE || stmt->kind == AX_MIR_STMT_STORAGE_DEAD) {
                    AxMirLocalId l = (stmt->kind == AX_MIR_STMT_STORAGE_LIVE) ? stmt->storage_live : stmt->storage_dead;
                    if (use_counts[l.v] == 0) {
                        keep = false; // Dead local, we can remove its storage annotations
                    }
                }
                
                if (keep) {
                    if (write_idx != j) {
                        bb->stmts[write_idx] = *stmt;
                    }
                    write_idx++;
                } else {
                    changed = true;
                }
            }
            bb->stmt_count = write_idx;
        }
        free(use_counts);
    }
}

void ax_opt_run(AxMirBody *body, AxThir *thir, AxDiagSink *sink, const AxHirItem *item, bool verify_each) {
    ax_opt_const_fold(body, thir);
    if (verify_each) ax_verify_mir(body, thir, sink, item);

    ax_opt_dce(body);
    if (verify_each) ax_verify_mir(body, thir, sink, item);

    ax_opt_cfg_simplify(body);
    if (verify_each) ax_verify_mir(body, thir, sink, item);
}

