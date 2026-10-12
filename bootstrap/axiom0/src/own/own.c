#include "own/own.h"
#include "kernel/arena.h"
#include "kernel/hashmap.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "mir/cap/cap.h"

typedef struct {
    AxOwnState state;
    AxLocation move_loc;
} AxOwnStateInfo;

bool ax_type_is_copy(TypeId id, const AxThir *thir, const StrInterner *str_in) {
    if (id.v == 0) return false;
    const AxType *ty = ax_type_get(&thir->interner, id);
    if (!ty) return false;
    
    switch ((int)ty->kind) {
        case AX_TY_ERROR: return false;
        case AX_TY_UNIT:
        case AX_TY_NEVER:
        case AX_TY_BOOL:
        case AX_TY_CHAR:
        case AX_TY_I8: case AX_TY_I16: case AX_TY_I32: case AX_TY_I64: case AX_TY_ISIZE:
        case AX_TY_U8: case AX_TY_U16: case AX_TY_U32: case AX_TY_U64: case AX_TY_USIZE:
        case AX_TY_PTR:
        case AX_TY_FN:
        case AX_TY_INT_VAR:
        case AX_TY_VIEW:
            return true;
        case AX_TY_STR:
            return false;
        case AX_TY_ARRAY:
            return ax_type_is_copy(ty->array.elem, thir, str_in);
        case AX_TY_TUPLE:
            for (size_t i = 0; i < ty->tuple.field_count; i++) {
                if (!ax_type_is_copy(ty->tuple.fields[i], thir, str_in)) return false;
            }
            return true;
        case AX_TY_STRUCT:
        case AX_TY_ENUM: {
            const AxHirItem *def = (ty->kind == AX_TY_STRUCT) ? ty->strct.def : ty->enm.def;
            if (!def) return false;
            for (const AxHirAttr *attr = def->attrs; attr; attr = attr->next) {
                StrView attr_name = ax_interner_get(str_in, attr->name);
                if (attr_name.len == 6 && memcmp(attr_name.ptr, "derive", 6) == 0) {
                    for (const AxHirAttrArg *arg = attr->args; arg; arg = arg->next) {
                        StrView arg_name = ax_interner_get(str_in, arg->name);
                        if (arg_name.len == 4 && memcmp(arg_name.ptr, "Copy", 4) == 0) {
                            return true;
                        }
                    }
                }
            }
            return false;
        }
        default: return false;
    }
}

typedef struct PathNode {
    uint32_t parent;
    uint32_t first_child;
    uint32_t num_children;
    bool is_copy;
} PathNode;

typedef struct {
    PathNode *nodes;
    size_t count;
    size_t cap;
    uint32_t *local_roots;
    size_t local_count;
} PathCtx;

static void populate_path_tree(PathCtx *ctx, uint32_t node_idx, TypeId ty_id, const AxThir *thir, const StrInterner *str_in) {
    const AxType *ty = ax_type_get(&thir->interner, ty_id);
    if (!ty) return;

    size_t field_count = 0;
    TypeId *fields = NULL;

    if (ty->kind == AX_TY_TUPLE) {
        field_count = ty->tuple.field_count;
        fields = ty->tuple.fields;
    } else if (ty->kind == AX_TY_STRUCT) {
        field_count = ty->strct.field_count;
        fields = ty->strct.fields;
    }

    if (field_count > 0) {
        uint32_t first_child = ctx->count;
        ctx->count += field_count;
        if (ctx->count > ctx->cap) {
            while (ctx->count > ctx->cap) ctx->cap = ctx->cap ? ctx->cap * 2 : 64;
            ctx->nodes = realloc(ctx->nodes, ctx->cap * sizeof(PathNode));
        }
        ctx->nodes[node_idx].first_child = first_child;
        ctx->nodes[node_idx].num_children = field_count;

        for (uint32_t i = 0; i < field_count; i++) {
            PathNode *c = &ctx->nodes[first_child + i];
            c->parent = node_idx;
            c->first_child = 0;
            c->num_children = 0;
            c->is_copy = ax_type_is_copy(fields[i], thir, str_in);
        }
        for (uint32_t i = 0; i < field_count; i++) {
            populate_path_tree(ctx, first_child + i, fields[i], thir, str_in);
        }
    }
}

static uint32_t resolve_place(const PathCtx *ctx, const AxMirPlace *place) {
    uint32_t node = ctx->local_roots[place->local.v];
    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_FIELD) {
            uint32_t f = place->projs[i].field_idx;
            if (f < ctx->nodes[node].num_children) {
                node = ctx->nodes[node].first_child + f;
            }
        }
    }
    return node;
}

static void update_parent(AxOwnStateInfo *state, const PathCtx *ctx, uint32_t node) {
    uint32_t p = ctx->nodes[node].parent;
    if (p == UINT32_MAX) return;
    
    bool all_init = true;
    bool all_moved = true;
    bool any_moved = false;
    bool any_init = false;
    AxLocation move_loc = {0};
    for (uint32_t i = 0; i < ctx->nodes[p].num_children; i++) {
        AxOwnState cst = state[ctx->nodes[p].first_child + i].state;
        if (cst != AX_OWN_OWNED) all_init = false;
        if (cst == AX_OWN_OWNED) any_init = true;
        
        if (cst != AX_OWN_MOVED && cst != AX_OWN_UNINIT) all_moved = false;
        if (cst == AX_OWN_MOVED || cst == AX_OWN_PARTIAL) {
            any_moved = true;
            if (move_loc.file.v == 0) move_loc = state[ctx->nodes[p].first_child + i].move_loc;
        }
    }
    
    AxOwnState new_p;
    if (all_init) new_p = AX_OWN_OWNED;
    else if (all_moved) new_p = AX_OWN_MOVED;
    else if (any_moved) new_p = AX_OWN_PARTIAL;
    else if (any_init) new_p = AX_OWN_PARTIAL; 
    else new_p = AX_OWN_UNINIT;
    
    state[p].state = new_p;
    if (new_p == AX_OWN_MOVED || new_p == AX_OWN_PARTIAL) {
        state[p].move_loc = move_loc;
    }
    update_parent(state, ctx, p);
}

static void mark_state(AxOwnStateInfo *state, const PathCtx *ctx, uint32_t node, AxOwnState new_state, AxLocation move_loc) {
    state[node].state = new_state;
    if (new_state == AX_OWN_MOVED || new_state == AX_OWN_PARTIAL) {
        state[node].move_loc = move_loc;
    }
    for (uint32_t i = 0; i < ctx->nodes[node].num_children; i++) {
        mark_state(state, ctx, ctx->nodes[node].first_child + i, new_state, move_loc);
    }
}

static AxOwnState merge_state_val(AxOwnState a, AxOwnState b) {
    if (a == b) return a;
    if (a == AX_OWN_PARTIAL || b == AX_OWN_PARTIAL) return AX_OWN_PARTIAL;
    if (a == AX_OWN_OWNED || b == AX_OWN_OWNED) return AX_OWN_PARTIAL;
    return a == AX_OWN_MOVED ? AX_OWN_MOVED : b;
}

static bool merge_states(AxOwnStateInfo *dest, const AxOwnStateInfo *src, size_t count) {
    bool changed = false;
    for (size_t i = 0; i < count; i++) {
        AxOwnState m = merge_state_val(dest[i].state, src[i].state);
        AxLocation new_loc = dest[i].move_loc;
        if (new_loc.file.v == 0) new_loc = src[i].move_loc;

        if (m != dest[i].state || 
            ((m == AX_OWN_MOVED || m == AX_OWN_PARTIAL) && dest[i].move_loc.file.v == 0 && new_loc.file.v != 0)) {
            dest[i].state = m;
            if (m == AX_OWN_MOVED || m == AX_OWN_PARTIAL) {
                dest[i].move_loc = new_loc;
            }
            changed = true;
        }
    }
    return changed;
}

typedef struct {
    AxOwnStateInfo *state;
    const PathCtx *ctx;
    AxDiagSink *sink;
    bool report;
    const AxMirBody *body;
    const AxThir *thir;
    AxMirCapTracker *cap_tracker;
} Visitor;

static void check_use(Visitor *v, const AxMirPlace *place, AxLocation loc) {
    AxMirPlace base = *place;
    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            base.proj_count = i;
            place = &base; break;
        }
    }
    uint32_t node = resolve_place(v->ctx, place);
    AxOwnState st = v->state[node].state;
    if (st != AX_OWN_OWNED && v->report) {
        AxDiagnostic *d = ax_arena_alloc(&v->sink->arena, sizeof(AxDiagnostic), _Alignof(AxDiagnostic));
        memset(d, 0, sizeof(*d));
        bool is_uninit = (st == AX_OWN_UNINIT) || (st == AX_OWN_PARTIAL && v->state[node].move_loc.file.v == 0);
        if (v->sink->errors > 0) return;
        d->code = is_uninit ? AX_INIT_USE_UNINIT : AX_MOVE_USE_AFTER_MOVE;
        d->severity = AX_DIAG_ERROR;
        d->message = ax_diag_code_default_message(d->code);
        d->primary = loc;
        
        if (st == AX_OWN_MOVED || (st == AX_OWN_PARTIAL && v->state[node].move_loc.file.v != 0)) {
            AxDiagLabel *l = ax_arena_alloc(&v->sink->arena, sizeof(AxDiagLabel), _Alignof(AxDiagLabel));
            l->span = v->state[node].move_loc;
            l->message = "moved here";
            d->labels = l;
            d->label_count = 1;
        }
        
        ax_diag_sink_report(v->sink, d);
    }
}

static void do_move(Visitor *v, const AxMirPlace *place, AxLocation loc) {
    AxMirPlace base = *place;
    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            base.proj_count = i;
            check_use(v, &base, loc); return;
        }
    }
    uint32_t node = resolve_place(v->ctx, place);
    if (!v->ctx->nodes[node].is_copy) {
        mark_state(v->state, v->ctx, node, AX_OWN_MOVED, loc);
        update_parent(v->state, v->ctx, node);
    }
}

static void do_assign(Visitor *v, const AxMirPlace *place, AxLocation loc) {
    AxMirPlace base = *place;
    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            base.proj_count = i;
            check_use(v, &base, loc); return;
        }
    }
    uint32_t node = resolve_place(v->ctx, place);
    mark_state(v->state, v->ctx, node, AX_OWN_OWNED, loc);
    update_parent(v->state, v->ctx, node);
}

static void visit_operand(Visitor *v, const AxMirOperand *op, AxLocation loc) {
    AxLocation op_loc = op->location.file.v != 0 ? op->location : loc;
    if (op->kind == AX_MIR_OP_COPY || op->kind == AX_MIR_OP_MOVE) {
        check_use(v, &op->place, op_loc);
        do_move(v, &op->place, op_loc);
    }
}

static void visit_rvalue(Visitor *v, const AxMirRvalue *rv, AxLocation loc) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            visit_operand(v, &rv->use, loc);
            break;
        case AX_MIR_RVALUE_REPEAT:
            visit_operand(v, &rv->repeat.op, loc);
            visit_operand(v, &rv->repeat.count, loc);
            break;
        case AX_MIR_RVALUE_REF:
            check_use(v, &rv->ref.place, loc);
            ax_mir_cap_tracker_add(v->cap_tracker, &rv->ref.place, rv->ref.bk == AX_MIR_BORROW_MUT ? AX_MIR_VIEW_MUT : AX_MIR_VIEW_READ);
            break;
        case AX_MIR_RVALUE_LEN:
            check_use(v, &rv->len, loc);
            break;
        case AX_MIR_RVALUE_CAST:
            visit_operand(v, &rv->cast.op, loc);
            break;
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
        case AX_MIR_RVALUE_BINARY_OP:
            visit_operand(v, &rv->binary_op.lhs, loc);
            visit_operand(v, &rv->binary_op.rhs, loc);
            break;
        case AX_MIR_RVALUE_UNARY_OP:
            visit_operand(v, &rv->unary_op.operand, loc);
            break;
        case AX_MIR_RVALUE_DISCRIMINANT:
            check_use(v, &rv->discriminant, loc);
            break;
        case AX_MIR_RVALUE_AGGREGATE:
            for (size_t i = 0; i < rv->aggregate.operand_count; i++) {
                visit_operand(v, &rv->aggregate.operands[i], loc);
            }
            break;
    }
}

static void visit_stmt(Visitor *v, const AxMirStmt *stmt) {
    switch (stmt->kind) {
        case AX_MIR_STMT_ASSIGN:
            visit_rvalue(v, &stmt->assign.rvalue, stmt->location);
            do_assign(v, &stmt->assign.place, stmt->location);
            break;
        case AX_MIR_STMT_STORAGE_LIVE:
        case AX_MIR_STMT_STORAGE_DEAD:
            break;
        case AX_MIR_STMT_DROP:
            check_use(v, &stmt->drop, stmt->location);
            do_move(v, &stmt->drop, stmt->location);
            break;
    }
}

static void visit_bb(Visitor *v, const AxMirBb *bb) {
    for (size_t i = 0; i < bb->stmt_count; i++) {
        visit_stmt(v, &bb->stmts[i]);
    }
    const AxMirTerminator *term = &bb->terminator;
    AxLocation loc = term->location;
    switch (term->kind) {
        case AX_MIR_TERM_SWITCH_INT:
            visit_operand(v, &term->switch_int.discr, loc);
            break;
        case AX_MIR_TERM_DROP:
            if (term->drop.is_explicit) {
                check_use(v, &term->drop.place, loc);
            }
            do_move(v, &term->drop.place, loc);
            break;
        case AX_MIR_TERM_CALL:
            visit_operand(v, &term->call.func, loc);
            for (size_t i = 0; i < term->call.arg_count; i++) {
                visit_operand(v, &term->call.args[i], loc);
            }
            do_assign(v, &term->call.destination, loc);
            break;
        case AX_MIR_TERM_ASSERT:
            visit_operand(v, &term->assert.cond, loc);
            break;
        case AX_MIR_TERM_RETURN:
            {
                AxMirPlace ret_place = {0};
                ret_place.local.v = 0;
                bool needs_check = true;
                if (v->body->local_count > 0 && v->thir) {
                    const AxType *ty = ax_type_get(&v->thir->interner, v->body->locals[0].ty);
                    if (ty && (ty->kind == AX_TY_UNIT || ty->kind == AX_TY_NEVER)) {
                        needs_check = false;
                    }
                }
                if (needs_check) {
                    check_use(v, &ret_place, loc);
                }
            }
            break;
        default:
            break;
    }
}

#include "own/cap/cap.h"

void ax_own_check(const AxHirItem *it, AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const StrInterner *str_in) {
    ax_own_cap_check(body, sink);
    PathCtx ctx = {0};
    ctx.cap = body->local_count * 2;
    ctx.nodes = malloc(ctx.cap * sizeof(PathNode));
    ctx.local_roots = calloc(body->local_count, sizeof(uint32_t));
    ctx.local_count = body->local_count;

    for (size_t i = 0; i < body->local_count; i++) {
        uint32_t node_idx = ctx.count++;
        if (ctx.count > ctx.cap) {
            ctx.cap = ctx.cap * 2;
            ctx.nodes = realloc(ctx.nodes, ctx.cap * sizeof(PathNode));
        }
        ctx.local_roots[i] = node_idx;
        ctx.nodes[node_idx].parent = UINT32_MAX;
        ctx.nodes[node_idx].first_child = 0;
        ctx.nodes[node_idx].num_children = 0;
        ctx.nodes[node_idx].is_copy = ax_type_is_copy(body->locals[i].ty, thir, str_in);
    }
    for (size_t i = 0; i < body->local_count; i++) {
        populate_path_tree(&ctx, ctx.local_roots[i], body->locals[i].ty, thir, str_in);
    }

    AxOwnStateInfo **bb_in = malloc(body->bb_count * sizeof(AxOwnStateInfo*));
    for (size_t i = 0; i < body->bb_count; i++) {
        bb_in[i] = malloc(ctx.count * sizeof(AxOwnStateInfo));
        for (size_t j = 0; j < ctx.count; j++) {
            bb_in[i][j].state = AX_OWN_UNINIT; bb_in[i][j].move_loc = (AxLocation){0};
        }
    }

    size_t arg_count = 0;
    if (it && it->kind == AX_HIR_ITEM_FN) {
        for (AxHirParam *p = it->fn.params; p; p = p->next) {
            arg_count++;
        }
    }

    if (body->bb_count > 0) {
        for (size_t i = 0; i < arg_count; i++) {
            if (i + 1 < body->local_count) {
                AxLocation l = {0}; mark_state(bb_in[0], &ctx, ctx.local_roots[i + 1], AX_OWN_OWNED, l);
            }
        }
    }

    bool *visited = calloc(body->bb_count, sizeof(bool));
    if (body->bb_count > 0) visited[0] = true;

    bool changed = true;
    AxArena cap_arena;
    ax_arena_init(&cap_arena, 0);
    AxMirCapTracker *cap_tracker = ax_mir_cap_tracker_new(&cap_arena);
    AxOwnStateInfo *temp = malloc(ctx.count * sizeof(AxOwnStateInfo));
    Visitor v = { .state = temp, .ctx = &ctx, .sink = sink, .report = false, .body = body, .thir = thir, .cap_tracker = cap_tracker };

    while (changed) {
        changed = false;
        for (size_t i = 0; i < body->bb_count; i++) {
            if (!visited[i]) continue;
            memcpy(temp, bb_in[i], ctx.count * sizeof(AxOwnStateInfo));
            visit_bb(&v, &body->bbs[i]);

            const AxMirTerminator *term = &body->bbs[i].terminator;
            AxMirBbId targets[16];
            size_t target_count = 0;

            if (term->kind == AX_MIR_TERM_GOTO) {
                targets[target_count++] = term->goto_target;
            } else if (term->kind == AX_MIR_TERM_SWITCH_INT) {
                for (size_t j = 0; j < term->switch_int.targets.count && target_count < 15; j++) {
                    targets[target_count++] = term->switch_int.targets.values[j].target;
                }
                if (target_count < 16) {
                    targets[target_count++] = term->switch_int.targets.otherwise;
                }
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
                        memcpy(bb_in[tgt.v], temp, ctx.count * sizeof(AxOwnStateInfo));
                        visited[tgt.v] = true;
                        changed = true;
                    } else {
                        if (merge_states(bb_in[tgt.v], temp, ctx.count)) {
                            changed = true;
                        }
                    }
                }
            }
        }
    }

    v.report = true;
    for (size_t i = 0; i < body->bb_count; i++) {
        if (!visited[i]) continue;
        memcpy(temp, bb_in[i], ctx.count * sizeof(AxOwnStateInfo));
        visit_bb(&v, &body->bbs[i]);
    }

    free(visited);
    free(temp);
    for (size_t i = 0; i < body->bb_count; i++) free(bb_in[i]);
    free(bb_in);
    free(ctx.nodes);
    free(ctx.local_roots);
    ax_arena_destroy(&cap_arena);
}
