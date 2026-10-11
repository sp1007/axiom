#include "own/cap/cap.h"
#include "mir/cap/cap.h"
#include "mir/regions/region.h"
#include "diag/diag.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

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

static void check_invalidate(const CapState *state, size_t local_count, const AxMirPlace *place, AxLocation loc, AxDiagSink *sink, bool report) {
    if (!report) return;
    for (size_t i = 0; i < local_count; i++) {
        if (state->caps[i].view == AX_MIR_VIEW_UNKNOWN) continue;
        AxMirRegion rel = ax_mir_region_relate(&state->caps[i].place, place);
        if (rel != AX_MIR_REGION_DISJOINT) {
            // The owner is being moved/dropped, but a view still exists.
            emit_cap_diag(sink, AX_CAP_OUTLIVES_OWNER, loc, "active view outlives its originating owner place");
            return;
        }
    }
}

static void visit_operand(CapState *state, size_t local_count, const AxMirOperand *op, AxLocation loc, AxDiagSink *sink, bool report) {
    if (op->kind == AX_MIR_OP_MOVE) {
        check_invalidate(state, local_count, &op->place, loc, sink, report);
    }
}

static void visit_rvalue(CapState *state, size_t local_count, const AxMirRvalue *rv, AxLocation loc, AxDiagSink *sink, bool report) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            visit_operand(state, local_count, &rv->use, loc, sink, report);
            break;
        case AX_MIR_RVALUE_REPEAT:
            visit_operand(state, local_count, &rv->repeat.op, loc, sink, report);
            visit_operand(state, local_count, &rv->repeat.count, loc, sink, report);
            break;
        case AX_MIR_RVALUE_REF: {
            AxMirView v = rv->ref.bk == AX_MIR_BORROW_MUT ? AX_MIR_VIEW_MUT : AX_MIR_VIEW_READ;
            check_conflict(state, local_count, &rv->ref.place, v, loc, sink, report);
            break;
        }
        case AX_MIR_RVALUE_LEN:
            break;
        case AX_MIR_RVALUE_CAST:
            visit_operand(state, local_count, &rv->cast.op, loc, sink, report);
            break;
        case AX_MIR_RVALUE_BINARY_OP:
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
            visit_operand(state, local_count, &rv->binary_op.lhs, loc, sink, report);
            visit_operand(state, local_count, &rv->binary_op.rhs, loc, sink, report);
            break;
        case AX_MIR_RVALUE_UNARY_OP:
            visit_operand(state, local_count, &rv->unary_op.operand, loc, sink, report);
            break;
        case AX_MIR_RVALUE_DISCRIMINANT:
            break;
        case AX_MIR_RVALUE_AGGREGATE:
            for (size_t i = 0; i < rv->aggregate.operand_count; i++) {
                visit_operand(state, local_count, &rv->aggregate.operands[i], loc, sink, report);
            }
            break;
    }
}

static void visit_stmt(CapState *state, size_t local_count, const AxMirStmt *stmt, AxDiagSink *sink, bool report) {
    switch (stmt->kind) {
        case AX_MIR_STMT_ASSIGN:
            visit_rvalue(state, local_count, &stmt->assign.rvalue, stmt->location, sink, report);
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
            } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_USE && stmt->assign.rvalue.use.kind == AX_MIR_OP_COPY) {
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
            }
            break;
        case AX_MIR_STMT_STORAGE_LIVE:
            state->caps[stmt->storage_live.v].view = AX_MIR_VIEW_UNKNOWN;
            break;
        case AX_MIR_STMT_STORAGE_DEAD:
            state->caps[stmt->storage_dead.v].view = AX_MIR_VIEW_UNKNOWN;
            break;
        case AX_MIR_STMT_DROP:
            check_invalidate(state, local_count, &stmt->drop, stmt->location, sink, report);
            break;
    }
}

static void visit_bb(CapState *state, size_t local_count, const AxMirBb *bb, AxDiagSink *sink, bool report) {
    for (size_t i = 0; i < bb->stmt_count; i++) {
        visit_stmt(state, local_count, &bb->stmts[i], sink, report);
    }
    const AxMirTerminator *term = &bb->terminator;
    AxLocation loc = term->location;
    if (term->kind == AX_MIR_TERM_DROP) {
        check_invalidate(state, local_count, &term->drop.place, loc, sink, report);
    } else if (term->kind == AX_MIR_TERM_CALL) {
        for (size_t i = 0; i < term->call.arg_count; i++) {
            visit_operand(state, local_count, &term->call.args[i], loc, sink, report);
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
            visit_bb(&temp, local_count, &body->bbs[i], sink, false);

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
        visit_bb(&temp, local_count, &body->bbs[i], sink, true);
    }

    for (size_t i = 0; i < body->bb_count; i++) {
        free(bb_in[i].caps);
    }
    free(bb_in);
    free(temp.caps);
    free(visited);
}
