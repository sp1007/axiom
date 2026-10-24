#include "own/cap/cap.h"
#include "mir/cap/cap.h"
#include "mir/regions/region.h"
#include "diag/diag.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* Capability (view / mut_view) checker on pre-elaboration MIR (SPEC-11).
 *
 * A forward dataflow records, per local, the capability it holds (the viewed place and the view
 * kind). Conflicts (AXS-CAP-003) are checked against every capability that is still in scope
 * (until the holder's StorageDead / reassignment). The owner-outlives check (AXS-CAP-004) on a
 * drop or move of the owner only reports a holder that is still used afterwards: a view local is
 * active until its last use (AXS-CAP-009), so the scope-end drops of owners declared before it,
 * which run after its last use, are not violations (T157). A capability consumed by a cast (the
 * `address_of` / `address_of_mut` lowering `_t = &place; _p = copy _t as *T`) ends at that cast
 * when the temporary is not used again: the raw pointer holds no capability (AXS-CAP-008). Both
 * rules need the same "is this local used later" query, answered by a forward search over the
 * normal (non-unwind) CFG edges from the current position; the port compiler/own/cap.ax is the
 * same algorithm (ADR-0034 section 2). */

static void emit_cap_diag(AxDiagSink *sink, AxDiagCode code, AxLocation loc, const char *msg) {
    AxDiagnostic d = {0};
    d.code = code;
    d.severity = ax_diag_code_severity(code);
    d.message = msg;
    d.primary = loc;
    ax_diag_sink_report(sink, &d);
}

typedef struct {
    AxMirCap *caps;
} CapState;

/* Position of the statement being visited: `stmt == bb.stmt_count` is the terminator. */
typedef struct {
    const AxMirBody *body;
    size_t bb;
    size_t stmt;
} CapPos;

/* ---- "is local `l` used at or after a position" (T157) ---- */

enum { CAP_EFF_NONE, CAP_EFF_USE, CAP_EFF_KILL };

static bool cap_place_uses(const AxMirPlace *p, uint32_t l) {
    if (p->local.v == l) return true;
    for (size_t i = 0; i < p->proj_count; i++) {
        const AxMirProjection *pr = &p->projs[i];
        if (pr->kind == AX_MIR_PROJ_INDEX && pr->index_local.v == l) return true;
        if (pr->kind == AX_MIR_PROJ_SUB_SLICE) {
            if (pr->sub_slice.has_from && pr->sub_slice.from_local.v == l) return true;
            if (pr->sub_slice.has_to && pr->sub_slice.to_local.v == l) return true;
        }
    }
    return false;
}

static bool cap_operand_uses(const AxMirOperand *op, uint32_t l) {
    if (op->kind != AX_MIR_OP_COPY && op->kind != AX_MIR_OP_MOVE) return false;
    return cap_place_uses(&op->place, l);
}

static bool cap_rvalue_uses(const AxMirRvalue *rv, uint32_t l) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            return cap_operand_uses(&rv->use, l);
        case AX_MIR_RVALUE_REPEAT:
            /* only the element: the count is a usize, never a capability holder */
            return cap_operand_uses(&rv->repeat.op, l);
        case AX_MIR_RVALUE_REF:
            return cap_place_uses(&rv->ref.place, l);
        case AX_MIR_RVALUE_LEN:
            return cap_place_uses(&rv->len, l);
        case AX_MIR_RVALUE_CAST:
            return cap_operand_uses(&rv->cast.op, l);
        case AX_MIR_RVALUE_BINARY_OP:
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
            return cap_operand_uses(&rv->binary_op.lhs, l) || cap_operand_uses(&rv->binary_op.rhs, l);
        case AX_MIR_RVALUE_UNARY_OP:
            return cap_operand_uses(&rv->unary_op.operand, l);
        case AX_MIR_RVALUE_DISCRIMINANT:
            return cap_place_uses(&rv->discriminant, l);
        case AX_MIR_RVALUE_AGGREGATE:
            for (size_t i = 0; i < rv->aggregate.operand_count; i++) {
                if (cap_operand_uses(&rv->aggregate.operands[i], l)) return true;
            }
            return false;
    }
    return false;
}

static int cap_stmt_effect(const AxMirStmt *stmt, uint32_t l) {
    switch (stmt->kind) {
        case AX_MIR_STMT_ASSIGN:
            if (cap_rvalue_uses(&stmt->assign.rvalue, l)) return CAP_EFF_USE;
            if (stmt->assign.place.proj_count > 0) {
                return cap_place_uses(&stmt->assign.place, l) ? CAP_EFF_USE : CAP_EFF_NONE;
            }
            return stmt->assign.place.local.v == l ? CAP_EFF_KILL : CAP_EFF_NONE;
        case AX_MIR_STMT_STORAGE_LIVE:
            return stmt->storage_live.v == l ? CAP_EFF_KILL : CAP_EFF_NONE;
        case AX_MIR_STMT_STORAGE_DEAD:
            return stmt->storage_dead.v == l ? CAP_EFF_KILL : CAP_EFF_NONE;
        case AX_MIR_STMT_DROP:
            return cap_place_uses(&stmt->drop, l) ? CAP_EFF_USE : CAP_EFF_NONE;
    }
    return CAP_EFF_NONE;
}

static bool cap_term_uses(const AxMirTerminator *t, uint32_t l) {
    switch (t->kind) {
        case AX_MIR_TERM_SWITCH_INT:
            return cap_operand_uses(&t->switch_int.discr, l);
        case AX_MIR_TERM_RETURN:
            return l == 0;
        case AX_MIR_TERM_DROP:
            return cap_place_uses(&t->drop.place, l);
        case AX_MIR_TERM_CALL:
            if (cap_operand_uses(&t->call.func, l)) return true;
            for (size_t i = 0; i < t->call.arg_count; i++) {
                if (cap_operand_uses(&t->call.args[i], l)) return true;
            }
            return t->call.destination.proj_count > 0 && cap_place_uses(&t->call.destination, l);
        case AX_MIR_TERM_ASSERT:
            return cap_operand_uses(&t->assert.cond, l);
        default:
            return false;
    }
}

/* Normal successors only (unwind edges carry no uses of a view local). */
static size_t cap_term_successors(const AxMirTerminator *t, uint32_t out[16]) {
    size_t n = 0;
    switch (t->kind) {
        case AX_MIR_TERM_GOTO:
            out[n++] = t->goto_target.v;
            break;
        case AX_MIR_TERM_SWITCH_INT:
            for (size_t j = 0; j < t->switch_int.targets.count && n < 15; j++) {
                out[n++] = t->switch_int.targets.values[j].target.v;
            }
            out[n++] = t->switch_int.targets.otherwise.v;
            break;
        case AX_MIR_TERM_DROP:
            out[n++] = t->drop.target.v;
            break;
        case AX_MIR_TERM_CALL:
            out[n++] = t->call.target.v;
            break;
        case AX_MIR_TERM_ASSERT:
            out[n++] = t->assert.target.v;
            break;
        default:
            break;
    }
    return n;
}

/* True when some normal CFG path from statement `pos.stmt` of block `pos.bb` (inclusive) reaches a
 * use of local `l` before `l` is reassigned or its storage ends. */
static bool cap_local_used_from(CapPos pos, uint32_t l) {
    const AxMirBody *body = pos.body;
    size_t n = body->bb_count;
    bool *queued = calloc(n, sizeof(bool));
    size_t *work = malloc((n + 1) * sizeof(size_t));
    size_t work_len = 0;
    bool used = false;
    size_t cur_bb = pos.bb;
    size_t cur_stmt = pos.stmt;
    for (;;) {
        const AxMirBb *bb = &body->bbs[cur_bb];
        bool killed = false;
        for (size_t i = cur_stmt; i < bb->stmt_count; i++) {
            int eff = cap_stmt_effect(&bb->stmts[i], l);
            if (eff == CAP_EFF_USE) { used = true; break; }
            if (eff == CAP_EFF_KILL) { killed = true; break; }
        }
        if (used) break;
        if (!killed) {
            const AxMirTerminator *t = &bb->terminator;
            if (cap_term_uses(t, l)) { used = true; break; }
            bool dest_kill = t->kind == AX_MIR_TERM_CALL && t->call.destination.proj_count == 0 &&
                             t->call.destination.local.v == l;
            if (!dest_kill) {
                uint32_t succ[16];
                size_t sc = cap_term_successors(t, succ);
                for (size_t j = 0; j < sc; j++) {
                    if (succ[j] < n && !queued[succ[j]]) {
                        queued[succ[j]] = true;
                        work[work_len++] = succ[j];
                    }
                }
            }
        }
        if (work_len == 0) break;
        cur_bb = work[--work_len];
        cur_stmt = 0;
    }
    free(queued);
    free(work);
    return used;
}

/* True when the body drops the whole local `l` somewhere. Such a local has a type that needs drop,
 * which is never Copy, so a `copy _l` of it is a move (the MIR builder writes `copy` for every use of
 * a named local; own.c decides moves by type, this checker has no types). */
static bool cap_local_is_dropped(const AxMirBody *body, uint32_t l) {
    for (size_t b = 0; b < body->bb_count; b++) {
        const AxMirBb *bb = &body->bbs[b];
        for (size_t i = 0; i < bb->stmt_count; i++) {
            const AxMirStmt *st = &bb->stmts[i];
            if (st->kind == AX_MIR_STMT_DROP && st->drop.proj_count == 0 && st->drop.local.v == l) return true;
        }
        if (bb->terminator.kind == AX_MIR_TERM_DROP && bb->terminator.drop.place.proj_count == 0 &&
            bb->terminator.drop.place.local.v == l) {
            return true;
        }
    }
    return false;
}

static bool merge_states(CapState *dest, const CapState *src, size_t local_count) {
    bool changed = false;
    for (size_t i = 0; i < local_count; i++) {
        if (src->caps[i].view != AX_MIR_VIEW_UNKNOWN && dest->caps[i].view == AX_MIR_VIEW_UNKNOWN) {
            // merge
            dest->caps[i] = src->caps[i];
            changed = true;
        }
    }
    return changed;
}

static void check_conflict(const CapState *state, size_t local_count, const AxMirPlace *place, AxMirView view, AxLocation loc, AxDiagSink *sink, bool report) {
    if (!report) return;
    for (size_t i = 0; i < local_count; i++) {
        if (state->caps[i].view == AX_MIR_VIEW_UNKNOWN) continue;
        AxMirRegion rel = ax_mir_region_relate(&state->caps[i].place, place);
        if (rel != AX_MIR_REGION_DISJOINT) {
            if (view == AX_MIR_VIEW_MUT || state->caps[i].view == AX_MIR_VIEW_MUT) {
                if (view == AX_MIR_VIEW_MUT) {
                    emit_cap_diag(sink, AX_CAP_CONFLICT_MUT, loc, "cannot create a mutable view because it conflicts with an existing view");
                } else {
                    emit_cap_diag(sink, AX_CAP_CONFLICT_READ, loc, "cannot create a read view because the place is mutably viewed");
                }
                return;
            }
        }
    }
}

/* The owner `place` is moved or dropped at `pos`. A holder declared before its owner (lower local
 * index) was already reported when the capability was bound (see visit_stmt), so it is not reported
 * a second time; any other holder is a violation only while it is still used (AXS-CAP-009).
 * `by_copy`: the place is read by a whole-local `copy`, which is a move only when the local needs
 * drop (cap_local_is_dropped). */
static void check_invalidate(const CapState *state, size_t local_count, const AxMirPlace *place, bool by_copy, AxLocation loc, CapPos pos, AxDiagSink *sink, bool report) {
    if (!report) return;
    for (size_t i = 0; i < local_count; i++) {
        if (state->caps[i].view == AX_MIR_VIEW_UNKNOWN) continue;
        AxMirRegion rel = ax_mir_region_relate(&state->caps[i].place, place);
        if (rel != AX_MIR_REGION_DISJOINT) {
            if (by_copy && !cap_local_is_dropped(pos.body, place->local.v)) return;
            if ((uint32_t)i < state->caps[i].place.local.v) continue;
            if (!cap_local_used_from(pos, (uint32_t)i)) continue;
            // The owner is being moved/dropped, but a view that is still used exists.
            emit_cap_diag(sink, AX_CAP_OUTLIVES_OWNER, loc, "active view outlives its originating owner place");
            return;
        }
    }
}

static void visit_operand(CapState *state, size_t local_count, const AxMirOperand *op, AxLocation loc, CapPos pos, AxDiagSink *sink, bool report) {
    if (op->kind == AX_MIR_OP_MOVE) {
        check_invalidate(state, local_count, &op->place, false, loc, pos, sink, report);
    } else if (op->kind == AX_MIR_OP_COPY && op->place.proj_count == 0) {
        check_invalidate(state, local_count, &op->place, true, loc, pos, sink, report);
    }
}

static void visit_rvalue(CapState *state, size_t local_count, const AxMirRvalue *rv, AxLocation loc, CapPos pos, AxDiagSink *sink, bool report) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            visit_operand(state, local_count, &rv->use, loc, pos, sink, report);
            break;
        case AX_MIR_RVALUE_REPEAT:
            visit_operand(state, local_count, &rv->repeat.op, loc, pos, sink, report);
            visit_operand(state, local_count, &rv->repeat.count, loc, pos, sink, report);
            break;
        case AX_MIR_RVALUE_REF: {
            AxMirView v = rv->ref.bk == AX_MIR_BORROW_MUT ? AX_MIR_VIEW_MUT : AX_MIR_VIEW_READ;
            check_conflict(state, local_count, &rv->ref.place, v, loc, sink, report);
            break;
        }
        case AX_MIR_RVALUE_LEN:
            break;
        case AX_MIR_RVALUE_CAST:
            visit_operand(state, local_count, &rv->cast.op, loc, pos, sink, report);
            break;
        case AX_MIR_RVALUE_BINARY_OP:
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
            visit_operand(state, local_count, &rv->binary_op.lhs, loc, pos, sink, report);
            visit_operand(state, local_count, &rv->binary_op.rhs, loc, pos, sink, report);
            break;
        case AX_MIR_RVALUE_UNARY_OP:
            visit_operand(state, local_count, &rv->unary_op.operand, loc, pos, sink, report);
            break;
        case AX_MIR_RVALUE_DISCRIMINANT:
            break;
        case AX_MIR_RVALUE_AGGREGATE:
            for (size_t i = 0; i < rv->aggregate.operand_count; i++) {
                visit_operand(state, local_count, &rv->aggregate.operands[i], loc, pos, sink, report);
            }
            break;
    }
}

static void visit_stmt(CapState *state, size_t local_count, const AxMirStmt *stmt, CapPos pos, AxDiagSink *sink, bool report) {
    switch (stmt->kind) {
        case AX_MIR_STMT_ASSIGN:
            visit_rvalue(state, local_count, &stmt->assign.rvalue, stmt->location, pos, sink, report);
            if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_REF) {
                if (stmt->assign.place.proj_count == 0) {
                    AxMirView v = stmt->assign.rvalue.ref.bk == AX_MIR_BORROW_MUT ? AX_MIR_VIEW_MUT : AX_MIR_VIEW_READ;
                    state->caps[stmt->assign.place.local.v].place = stmt->assign.rvalue.ref.place;
                    state->caps[stmt->assign.place.local.v].view = v;
                    if (report) {
                        uint32_t dest = stmt->assign.place.local.v;
                        uint32_t src = stmt->assign.rvalue.ref.place.local.v;
                        if (dest < src) {
                            emit_cap_diag(sink, AX_CAP_OUTLIVES_OWNER, stmt->location, "active view outlives its originating owner place");
                        }
                    }
                }
            } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_USE && (stmt->assign.rvalue.use.kind == AX_MIR_OP_COPY || stmt->assign.rvalue.use.kind == AX_MIR_OP_MOVE)) {
                if (stmt->assign.place.proj_count == 0 && stmt->assign.rvalue.use.place.proj_count == 0) {
                    state->caps[stmt->assign.place.local.v] = state->caps[stmt->assign.rvalue.use.place.local.v];
                    if (report && state->caps[stmt->assign.place.local.v].view != AX_MIR_VIEW_UNKNOWN) {
                        uint32_t dest = stmt->assign.place.local.v;
                        uint32_t src = state->caps[dest].place.local.v;
                        if (dest < src) {
                            emit_cap_diag(sink, AX_CAP_OUTLIVES_OWNER, stmt->location, "active view outlives its originating owner place");
                        }
                    }
                }
            } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_AGGREGATE) {
                if (stmt->assign.place.proj_count == 0) {
                    for (size_t i = 0; i < stmt->assign.rvalue.aggregate.operand_count; i++) {
                        const AxMirOperand *op = &stmt->assign.rvalue.aggregate.operands[i];
                        if (op->kind == AX_MIR_OP_COPY || op->kind == AX_MIR_OP_MOVE) {
                            if (op->place.proj_count == 0 && state->caps[op->place.local.v].view != AX_MIR_VIEW_UNKNOWN) {
                                state->caps[stmt->assign.place.local.v] = state->caps[op->place.local.v];
                                if (report) {
                                    uint32_t dest = stmt->assign.place.local.v;
                                    uint32_t src = state->caps[dest].place.local.v;
                                    if (dest < src) {
                                        emit_cap_diag(sink, AX_CAP_OUTLIVES_OWNER, stmt->location, "active view outlives its originating owner place");
                                    }
                                }
                            }
                        }
                    }
                }
            } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_CAST) {
                /* AXS-CAP-008: `_p = copy _t as *T` turns the ephemeral capability of the
                 * `address_of` temporary `_t` into a raw pointer that holds none; the capability ends
                 * here unless `_t` itself is used again. */
                const AxMirOperand *op = &stmt->assign.rvalue.cast.op;
                if ((op->kind == AX_MIR_OP_COPY || op->kind == AX_MIR_OP_MOVE) && op->place.proj_count == 0 &&
                    op->place.local.v < local_count && state->caps[op->place.local.v].view != AX_MIR_VIEW_UNKNOWN) {
                    CapPos next = pos;
                    next.stmt = pos.stmt + 1;
                    if (!cap_local_used_from(next, op->place.local.v)) {
                        state->caps[op->place.local.v].view = AX_MIR_VIEW_UNKNOWN;
                    }
                }
            }

            if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_USE && stmt->assign.rvalue.use.kind == AX_MIR_OP_MOVE) {
                if (stmt->assign.rvalue.use.place.proj_count == 0 && stmt->assign.rvalue.use.place.local.v < local_count) {
                    state->caps[stmt->assign.rvalue.use.place.local.v].view = AX_MIR_VIEW_UNKNOWN;
                }
            } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_AGGREGATE) {
                for (size_t i = 0; i < stmt->assign.rvalue.aggregate.operand_count; i++) {
                    const AxMirOperand *op = &stmt->assign.rvalue.aggregate.operands[i];
                    if (op->kind == AX_MIR_OP_MOVE && op->place.proj_count == 0 && op->place.local.v < local_count) {
                        state->caps[op->place.local.v].view = AX_MIR_VIEW_UNKNOWN;
                    }
                }
            }
            break;
        case AX_MIR_STMT_STORAGE_LIVE:
            state->caps[stmt->storage_live.v].view = AX_MIR_VIEW_UNKNOWN;
            break;
        case AX_MIR_STMT_STORAGE_DEAD:
            state->caps[stmt->storage_dead.v].view = AX_MIR_VIEW_UNKNOWN;
            break;
        case AX_MIR_STMT_DROP:
            check_invalidate(state, local_count, &stmt->drop, false, stmt->location, pos, sink, report);
            break;
    }
}

static void visit_bb(CapState *state, size_t local_count, const AxMirBody *body, size_t bb_idx, AxDiagSink *sink, bool report) {
    const AxMirBb *bb = &body->bbs[bb_idx];
    CapPos pos = { body, bb_idx, 0 };
    for (size_t i = 0; i < bb->stmt_count; i++) {
        pos.stmt = i;
        visit_stmt(state, local_count, &bb->stmts[i], pos, sink, report);
    }
    pos.stmt = bb->stmt_count;
    const AxMirTerminator *term = &bb->terminator;
    AxLocation loc = term->location;
    if (term->kind == AX_MIR_TERM_DROP) {
        check_invalidate(state, local_count, &term->drop.place, false, loc, pos, sink, report);
    } else if (term->kind == AX_MIR_TERM_CALL) {
        for (size_t i = 0; i < term->call.arg_count; i++) {
            visit_operand(state, local_count, &term->call.args[i], loc, pos, sink, report);
            const AxMirOperand *op = &term->call.args[i];
            if (op->kind == AX_MIR_OP_MOVE && op->place.proj_count == 0 && op->place.local.v < local_count) {
                state->caps[op->place.local.v].view = AX_MIR_VIEW_UNKNOWN;
            }
        }
    }
}

void ax_own_cap_check(const AxMirBody *body, AxDiagSink *sink) {
    if (body->bb_count == 0) return;
    size_t local_count = body->local_count;

    CapState *bb_in = malloc(body->bb_count * sizeof(CapState));
    for (size_t i = 0; i < body->bb_count; i++) {
        bb_in[i].caps = calloc(local_count, sizeof(AxMirCap));
    }

    bool *visited = calloc(body->bb_count, sizeof(bool));
    visited[0] = true;
    bool changed = true;

    CapState temp;
    temp.caps = malloc(local_count * sizeof(AxMirCap));

    while (changed) {
        changed = false;
        for (size_t i = 0; i < body->bb_count; i++) {
            if (!visited[i]) continue;
            memcpy(temp.caps, bb_in[i].caps, local_count * sizeof(AxMirCap));
            visit_bb(&temp, local_count, body, i, sink, false);

            const AxMirTerminator *term = &body->bbs[i].terminator;
            AxMirBbId targets[16];
            size_t target_count = 0;

            if (term->kind == AX_MIR_TERM_GOTO) {
                targets[target_count++] = term->goto_target;
            } else if (term->kind == AX_MIR_TERM_SWITCH_INT) {
                for (size_t j = 0; j < term->switch_int.targets.count && target_count < 15; j++) {
                    targets[target_count++] = term->switch_int.targets.values[j].target;
                }
                if (target_count < 16) targets[target_count++] = term->switch_int.targets.otherwise;
            } else if (term->kind == AX_MIR_TERM_DROP) {
                targets[target_count++] = term->drop.target;
                if (term->drop.unwind.v != 0) targets[target_count++] = term->drop.unwind;
            } else if (term->kind == AX_MIR_TERM_CALL) {
                targets[target_count++] = term->call.target;
                if (term->call.unwind.v != 0) targets[target_count++] = term->call.unwind;
            } else if (term->kind == AX_MIR_TERM_ASSERT) {
                targets[target_count++] = term->assert.target;
                if (term->assert.unwind.v != 0) targets[target_count++] = term->assert.unwind;
            }

            for (size_t j = 0; j < target_count; j++) {
                AxMirBbId tgt = targets[j];
                if (tgt.v < body->bb_count) {
                    if (!visited[tgt.v]) {
                        memcpy(bb_in[tgt.v].caps, temp.caps, local_count * sizeof(AxMirCap));
                        visited[tgt.v] = true;
                        changed = true;
                    } else {
                        if (merge_states(&bb_in[tgt.v], &temp, local_count)) {
                            changed = true;
                        }
                    }
                }
            }
        }
    }

    for (size_t i = 0; i < body->bb_count; i++) {
        if (!visited[i]) continue;
        memcpy(temp.caps, bb_in[i].caps, local_count * sizeof(AxMirCap));
        visit_bb(&temp, local_count, body, i, sink, true);
    }

    for (size_t i = 0; i < body->bb_count; i++) {
        free(bb_in[i].caps);
    }
    free(bb_in);
    free(temp.caps);
    free(visited);
}
