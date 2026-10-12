import os

path = "bootstrap/axiom0/src/verify/verify.c"
with open(path, "r") as f:
    orig = f.read()

own_code = """
enum LocalState {
    ST_UNINIT = 0,
    ST_OWNED = 1,
    ST_MOVED = 2,
    ST_UNKNOWN = 3,
    ST_BOTTOM = 4
};

static uint8_t merge_st(uint8_t a, uint8_t b) {
    if (a == ST_BOTTOM) return b;
    if (b == ST_BOTTOM) return a;
    if (a == b) return a;
    return ST_UNKNOWN;
}

static void ax_verify_mir_own(const AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const AxHirItem *func) {
    size_t lc = body->local_count;
    uint8_t *bb_in = malloc(body->bb_count * lc);
    uint8_t *bb_out = malloc(body->bb_count * lc);
    memset(bb_in, ST_BOTTOM, body->bb_count * lc);
    memset(bb_out, ST_BOTTOM, body->bb_count * lc);

    bool *is_drop = calloc(lc, sizeof(bool));
    for (size_t i = 0; i < body->bb_count; ++i) {
        for (size_t j = 0; j < body->bbs[i].stmt_count; j++) {
            if (body->bbs[i].stmts[j].kind == AX_MIR_STMT_DROP) {
                if (body->bbs[i].stmts[j].drop.local.v < lc)
                    is_drop[body->bbs[i].stmts[j].drop.local.v] = true;
            }
        }
        if (body->bbs[i].terminator.kind == AX_MIR_TERM_DROP) {
            if (body->bbs[i].terminator.drop.place.local.v < lc)
                is_drop[body->bbs[i].terminator.drop.place.local.v] = true;
        }
    }

    memset(&bb_in[0], ST_UNINIT, lc);
    if (func && func->kind == AX_HIR_ITEM_FN) {
        size_t param_count = 0;
        for (AxHirParam *p = func->fn.params; p; p = p->next) param_count++;
        for (size_t i = 0; i < param_count; i++) {
            if (i + 1 < lc) bb_in[i + 1] = ST_OWNED;
        }
        if (lc > 0 && thir) {
            TypeId *expected_ret_ty_ptr = AxItemTypeMap_get((AxItemTypeMap*)&thir->item_types, func);
            if (expected_ret_ty_ptr && expected_ret_ty_ptr->v != 0) {
                const AxType *t_fn = ax_type_get(&thir->interner, *expected_ret_ty_ptr);
                if (t_fn && t_fn->kind == AX_TY_FN && t_fn->fn.ret_type.v != 0) {
                    const AxType *ret = ax_type_get(&thir->interner, t_fn->fn.ret_type);
                    if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                        bb_in[0] = ST_OWNED;
                    }
                } else if (t_fn && t_fn->kind == AX_TY_FN) {
                    bb_in[0] = ST_OWNED;
                }
            }
        }
    } else if (lc > 0 && thir) {
        if (body->locals[0].ty.v != 0) {
            const AxType *ret = ax_type_get(&thir->interner, body->locals[0].ty);
            if (!ret || ret->kind == AX_TY_UNIT || ret->kind == AX_TY_ERROR) {
                bb_in[0] = ST_OWNED;
            }
        } else {
            bb_in[0] = ST_OWNED;
        }
    }

    bool changed = true;
    while (changed) {
        changed = false;
        for (size_t i = 0; i < body->bb_count; ++i) {
            uint8_t *in = &bb_in[i * lc];
            if (i != 0) {
                for (size_t l = 0; l < lc; l++) in[l] = ST_BOTTOM;
                for (size_t j = 0; j < body->bb_count; ++j) {
                    const AxMirBb *pred = &body->bbs[j];
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
                            in[l] = merge_st(in[l], bb_out[j * lc + l]);
                        }
                    }
                }
            }

            uint8_t *cur = malloc(lc);
            memcpy(cur, in, lc);

            for (size_t j = 0; j < body->bbs[i].stmt_count; j++) {
                const AxMirStmt *stmt = &body->bbs[i].stmts[j];
                if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                    if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_USE) {
                        if (stmt->assign.rvalue.use.kind == AX_MIR_OP_MOVE) {
                            cur[stmt->assign.rvalue.use.place.local.v] = ST_MOVED;
                        }
                    }
                    cur[stmt->assign.place.local.v] = ST_OWNED;
                } else if (stmt->kind == AX_MIR_STMT_DROP) {
                    cur[stmt->drop.local.v] = ST_MOVED;
                }
            }
            
            const AxMirTerminator *term = &body->bbs[i].terminator;
            if (term->kind == AX_MIR_TERM_DROP) {
                cur[term->drop.place.local.v] = ST_MOVED;
            } else if (term->kind == AX_MIR_TERM_CALL) {
                for (size_t a = 0; a < term->call.arg_count; a++) {
                    if (term->call.args[a].kind == AX_MIR_OP_MOVE) {
                        cur[term->call.args[a].place.local.v] = ST_MOVED;
                    }
                }
                cur[term->call.destination.local.v] = ST_OWNED;
            }
            
            for (size_t l = 0; l < lc; l++) {
                if (bb_out[i * lc + l] != cur[l]) {
                    bb_out[i * lc + l] = cur[l];
                    changed = true;
                }
            }
            free(cur);
        }
    }

    for (size_t i = 0; i < body->bb_count; ++i) {
        uint8_t *cur = malloc(lc);
        memcpy(cur, &bb_in[i * lc], lc);
        
        const AxMirBb *bb = &body->bbs[i];
        
        for (size_t j = 0; j < bb->stmt_count; j++) {
            const AxMirStmt *stmt = &bb->stmts[j];
            if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_USE) {
                    if (stmt->assign.rvalue.use.kind != AX_MIR_OP_CONST) {
                        uint32_t loc = stmt->assign.rvalue.use.place.local.v;
                        if (loc < lc) {
                            if (cur[loc] == ST_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                            if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
                        }
                        if (stmt->assign.rvalue.use.kind == AX_MIR_OP_MOVE) {
                            cur[loc] = ST_MOVED;
                        }
                    }
                }
                if (stmt->assign.place.local.v < lc) {
                    cur[stmt->assign.place.local.v] = ST_OWNED;
                }
            } else if (stmt->kind == AX_MIR_STMT_DROP) {
                uint32_t loc = stmt->drop.local.v;
                if (loc < lc) {
                    if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_DOUBLE_DROP);
                    cur[loc] = ST_MOVED;
                }
            }
        }
        
        const AxMirTerminator *term = &bb->terminator;
        switch (term->kind) {
            case AX_MIR_TERM_SWITCH_INT:
                if (term->switch_int.discr.kind != AX_MIR_OP_CONST) {
                    uint32_t loc = term->switch_int.discr.place.local.v;
                    if (loc < lc) {
                        if (cur[loc] == ST_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                        if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
                    }
                }
                break;
            case AX_MIR_TERM_DROP:
                if (term->drop.place.local.v < lc) {
                    uint32_t loc = term->drop.place.local.v;
                    if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_DOUBLE_DROP);
                    cur[loc] = ST_MOVED;
                }
                break;
            case AX_MIR_TERM_CALL:
                if (term->call.func.kind != AX_MIR_OP_CONST) {
                    uint32_t loc = term->call.func.place.local.v;
                    if (loc < lc) {
                        if (cur[loc] == ST_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                        if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
                    }
                }
                for (size_t a = 0; a < term->call.arg_count; ++a) {
                    if (term->call.args[a].kind != AX_MIR_OP_CONST) {
                        uint32_t loc = term->call.args[a].place.local.v;
                        if (loc < lc) {
                            if (cur[loc] == ST_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                            if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
                            if (term->call.args[a].kind == AX_MIR_OP_MOVE) {
                                cur[loc] = ST_MOVED;
                            }
                        }
                    }
                }
                if (term->call.destination.local.v < lc) {
                    cur[term->call.destination.local.v] = ST_OWNED;
                }
                break;
            case AX_MIR_TERM_ASSERT:
                if (term->assert.cond.kind != AX_MIR_OP_CONST) {
                    uint32_t loc = term->assert.cond.place.local.v;
                    if (loc < lc) {
                        if (cur[loc] == ST_UNINIT) report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                        if (cur[loc] == ST_MOVED) report_verify_error(sink, func, AX_VERIFY_USE_AFTER_MOVE);
                    }
                }
                break;
            case AX_MIR_TERM_RETURN:
                if (lc > 0 && func == NULL && cur[0] == ST_UNINIT) {
                    report_verify_error(sink, func, AX_VERIFY_UNINIT_USE);
                }
                for (size_t l = 1; l < lc; l++) {
                    if (is_drop[l] && cur[l] == ST_OWNED) {
                        report_verify_error(sink, func, AX_VERIFY_MISSING_DROP);
                    }
                }
                break;
            default: break;
        }
        
        free(cur);
    }

    free(bb_in);
    free(bb_out);
    free(is_drop);
}
"""

with open(path, "w") as f:
    f.write(orig + own_code)
