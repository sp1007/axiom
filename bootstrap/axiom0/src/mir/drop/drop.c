#include "mir/drop/drop.h"
#include "types/types.h"
#include "source/source.h"
#include <string.h>
#include <stdlib.h>

static bool needs_drop(TypeId ty, const AxThir *thir, const StrInterner *interner, const AxHir *hir, const struct SourceDatabase *db) {
    const AxType *t = ax_type_get(&thir->interner, ty);
    if (!t) return false;
    
    if (t->kind == AX_TY_STRUCT) {
        if (t->strct.def->struct_decl.struct_fields == NULL) return true;
        
        if (hir && db) {
            StrView target_sname = ax_interner_get((StrInterner*)interner, t->strct.def->struct_decl.name);
            for (AxHirItem *it = (AxHirItem*)hir->items; it; it = it->next) {
                if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path && it->impl.self_type && it->impl.self_type->kind == AX_HIR_TYPE_PATH) {
                    StrView trait_sname = ax_source_db_span_text(db, it->impl.trait_path->span);
                    if (trait_sname.len == 4 && memcmp(trait_sname.ptr, "Drop", 4) == 0) {
                        StrView impl_sname = ax_source_db_span_text(db, it->impl.self_type->path.path.span);
                        if (ax_sv_eq(target_sname, impl_sname)) {
                            for (AxHirItem *m = it->impl.members; m; m = m->next) {
                                if (m->kind == AX_HIR_ITEM_FN) {
                                    return true;
                                }
                            }
                        }
                    }
                }
            }
        }
        
        for (size_t i = 0; i < t->strct.field_count; i++) {
            if (needs_drop(t->strct.fields[i], thir, interner, hir, db)) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_TUPLE) {
        for (size_t i = 0; i < t->tuple.field_count; i++) {
            if (needs_drop(t->tuple.fields[i], thir, interner, hir, db)) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_ENUM) {
        for (size_t v = 0; v < t->enm.variant_count; v++) {
            for (size_t i = 0; i < t->enm.variant_field_counts[v]; i++) {
                if (needs_drop(t->enm.variant_fields[v][i], thir, interner, hir, db)) return true;
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

static TypeId place_type(AxMirPlace p, AxMirBody *body, const AxThir *thir) {
    TypeId current_ty = body->locals[p.local.v].ty;
    for (size_t i = 0; i < p.proj_count; i++) {
        const AxMirProjection *proj = &p.projs[i];
        const AxType *ty = ax_type_get(&thir->interner, current_ty);
        if (proj->kind == AX_MIR_PROJ_DEREF) {
            if (ty->kind == AX_TY_VIEW || ty->kind == AX_TY_MUT_VIEW) current_ty = ty->view.pointee;
            else current_ty = ty->ptr.pointee;
        } else if (proj->kind == AX_MIR_PROJ_FIELD) {
            if (ty->kind == AX_TY_STRUCT) current_ty = ty->strct.fields[proj->field_idx];
            else if (ty->kind == AX_TY_TUPLE) current_ty = ty->tuple.fields[proj->field_idx];
        } else if (proj->kind == AX_MIR_PROJ_INDEX) {
            if (ty->kind == AX_TY_ARRAY) current_ty = ty->array.elem;
            else if (ty->kind == AX_TY_SLICE) current_ty = ty->slice.elem;
        }
    }
    return current_ty;
}

static bool expand_drop(AxMirBody *body, AxMirBbId bb_idx, const AxThir *thir, const AxHir *hir, const struct SourceDatabase *db, const StrInterner *interner) {
    AxMirBb *bb = &body->bbs[bb_idx.v];
    if (bb->terminator.kind != AX_MIR_TERM_DROP) return false;
    
    AxMirPlace place = bb->terminator.drop.place;
    AxMirBbId target = bb->terminator.drop.target;
    uint32_t flag = bb->terminator.drop_flag;
    
    TypeId ty_id = place_type(place, body, thir);
    const AxType *ty = ax_type_get(&thir->interner, ty_id);
    
    AxHirItem *drop_fn = NULL;
    if (ty && ty->kind == AX_TY_STRUCT) {
        StrView target_sname = ax_interner_get((StrInterner*)interner, ty->strct.def->struct_decl.name);
        for (AxHirItem *it = (AxHirItem*)hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path && it->impl.self_type && it->impl.self_type->kind == AX_HIR_TYPE_PATH) {
                StrView trait_sname = ax_source_db_span_text(db, it->impl.trait_path->span);
                if (trait_sname.len == 4 && memcmp(trait_sname.ptr, "Drop", 4) == 0) {
                    StrView impl_sname = ax_source_db_span_text(db, it->impl.self_type->path.path.span);
                    if (ax_sv_eq(target_sname, impl_sname)) {
                        for (AxHirItem *m = it->impl.members; m; m = m->next) {
                            if (m->kind == AX_HIR_ITEM_FN) {
                                drop_fn = m;
                                break;
                            }
                        }
                        if (drop_fn) break;
                    }
                }
            }
        }
    }
    
    AxMirBbId inner_target = target;
    
    // Generate field drops
    if (ty && (ty->kind == AX_TY_STRUCT || ty->kind == AX_TY_TUPLE)) {
        size_t field_count = (ty->kind == AX_TY_STRUCT) ? ty->strct.field_count : ty->tuple.field_count;
        for (size_t i = field_count; i > 0; i--) {
            size_t idx = i - 1;
            TypeId field_ty = (ty->kind == AX_TY_STRUCT) ? ty->strct.fields[idx] : ty->tuple.fields[idx];
            if (needs_drop(field_ty, thir, interner, hir, db)) {
                AxMirBb *bbs = ax_arena_alloc(&body->arena, (body->bb_count + 1) * sizeof(AxMirBb), _Alignof(AxMirBb));
                memcpy(bbs, body->bbs, body->bb_count * sizeof(AxMirBb));
                body->bbs = bbs;
                AxMirBbId field_bb = { (uint32_t)body->bb_count++ };
                
                AxMirProjection *projs = ax_arena_alloc(&body->arena, (place.proj_count + 1) * sizeof(AxMirProjection), _Alignof(AxMirProjection));
                if (place.proj_count > 0) memcpy(projs, place.projs, place.proj_count * sizeof(AxMirProjection));
                projs[place.proj_count].kind = AX_MIR_PROJ_FIELD;
                projs[place.proj_count].field_idx = (uint32_t)idx;
                
                AxMirPlace field_place = place;
                field_place.projs = projs;
                field_place.proj_count++;
                
                body->bbs[field_bb.v].stmts = NULL;
                body->bbs[field_bb.v].stmt_count = 0;
                body->bbs[field_bb.v].terminator.kind = AX_MIR_TERM_DROP;
                body->bbs[field_bb.v].terminator.drop.place = field_place;
                body->bbs[field_bb.v].terminator.drop.target = inner_target;
                body->bbs[field_bb.v].terminator.drop_flag = 0; // fields inherit the check from the outer struct for now
                
                inner_target = field_bb;
            }
        }
    }
    

    
    if (drop_fn) {

        AxMirLocalDecl *decl = ax_arena_alloc(&body->arena, (body->local_count + 1) * sizeof(AxMirLocalDecl), _Alignof(AxMirLocalDecl));
        memcpy(decl, body->locals, body->local_count * sizeof(AxMirLocalDecl));
        body->locals = decl;
        AxMirLocalId tmp = { (uint32_t)body->local_count++ };
        body->locals[tmp.v].ty = thir->interner.t_unit;
        body->locals[tmp.v].kind = AX_MIR_LOCAL_TEMP;
        
        AxMirLocalDecl *decl2 = ax_arena_alloc(&body->arena, (body->local_count + 1) * sizeof(AxMirLocalDecl), _Alignof(AxMirLocalDecl));
        memcpy(decl2, body->locals, body->local_count * sizeof(AxMirLocalDecl));
        body->locals = decl2;
        AxMirLocalId arg_tmp = { (uint32_t)body->local_count++ };
        AxType mut_view_t = { .kind = AX_TY_MUT_VIEW, .view = { .pointee = ty_id } };
        body->locals[arg_tmp.v].ty = ax_intern_type((TypeInterner*)&thir->interner, &mut_view_t);
        body->locals[arg_tmp.v].kind = AX_MIR_LOCAL_TEMP;
        
        AxMirBb *bbs = ax_arena_alloc(&body->arena, (body->bb_count + 1) * sizeof(AxMirBb), _Alignof(AxMirBb));
        memcpy(bbs, body->bbs, body->bb_count * sizeof(AxMirBb));
        body->bbs = bbs;
        AxMirBbId call_bb = { (uint32_t)body->bb_count++ };
        
        AxMirStmt *stmts = ax_arena_alloc(&body->arena, sizeof(AxMirStmt), _Alignof(AxMirStmt));
        stmts[0].kind = AX_MIR_STMT_ASSIGN;
        stmts[0].assign.place = (AxMirPlace){.local = arg_tmp};
        stmts[0].assign.rvalue.kind = AX_MIR_RVALUE_REF;
        stmts[0].assign.rvalue.ref.place = place;
        
        body->bbs[call_bb.v].stmts = stmts;
        body->bbs[call_bb.v].stmt_count = 1;
        body->bbs[call_bb.v].stmt_cap = 1;
        
        AxMirTerminator call = {0};
        call.kind = AX_MIR_TERM_CALL;
        call.call.func.kind = AX_MIR_OP_CONST;
        call.call.func.constant.val = drop_fn->fn.symbol.v;
        AxType fn_t = { .kind = AX_TY_FN };
        call.call.func.constant.ty = ax_intern_type((TypeInterner*)&thir->interner, &fn_t);
        
        AxMirOperand *args = ax_arena_alloc(&body->arena, sizeof(AxMirOperand), _Alignof(AxMirOperand));
        args[0].kind = AX_MIR_OP_MOVE;
        args[0].place = (AxMirPlace){.local = arg_tmp};
        
        call.call.args = args;
        call.call.arg_count = 1;
        call.call.destination = (AxMirPlace){.local = tmp};
        call.call.target = inner_target;
        
        body->bbs[call_bb.v].terminator = call;
        inner_target = call_bb;
    }
    
    bb = &body->bbs[bb_idx.v];
    
    if (flag) {
        AxMirBb *bbs = ax_arena_alloc(&body->arena, (body->bb_count + 1) * sizeof(AxMirBb), _Alignof(AxMirBb));
        memcpy(bbs, body->bbs, body->bb_count * sizeof(AxMirBb));
        body->bbs = bbs;
        AxMirBbId clear_bb = { (uint32_t)body->bb_count++ };
        
        AxMirStmt *clear_stmts = ax_arena_alloc(&body->arena, sizeof(AxMirStmt), _Alignof(AxMirStmt));
        clear_stmts[0] = make_flag_assign((AxMirLocalId){flag}, false, thir);
        body->bbs[clear_bb.v].stmts = clear_stmts;
        body->bbs[clear_bb.v].stmt_count = 1;
        body->bbs[clear_bb.v].terminator.kind = AX_MIR_TERM_GOTO;
        body->bbs[clear_bb.v].terminator.goto_target = inner_target;
        
        bb = &body->bbs[bb_idx.v];
        bb->terminator.kind = AX_MIR_TERM_SWITCH_INT;
        bb->terminator.switch_int.discr.kind = AX_MIR_OP_COPY;
        bb->terminator.switch_int.discr.place = (AxMirPlace){.local = (AxMirLocalId){flag}};
        bb->terminator.switch_int.targets.values = ax_arena_alloc(&body->arena, 1 * sizeof(AxMirSwitchTarget), _Alignof(AxMirSwitchTarget));
        bb->terminator.switch_int.targets.count = 1;
        bb->terminator.switch_int.targets.otherwise = target;
        
        bb->terminator.switch_int.targets.values[0].value = 1;
        bb->terminator.switch_int.targets.values[0].target = clear_bb;
    } else {
        bb->terminator.kind = AX_MIR_TERM_GOTO;
        bb->terminator.goto_target = inner_target;
    }
    
    return true;
}

void ax_mir_drop_elaborate(AxMirBody *body, const AxThir *thir, const AxHir *hir, const struct SourceDatabase *db, AxDiagSink *sink, const StrInterner *interner) {
    (void)sink;
    
    size_t orig_local_count = body->local_count;
    uint32_t *local_flags = calloc(orig_local_count, sizeof(uint32_t));
    
    for (size_t i = 1; i < orig_local_count; i++) {
        if (needs_drop(body->locals[i].ty, thir, interner, hir, db)) {
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
        
        size_t max_extra = 0;
        if (call_inits[i].dest.v != 0) max_extra++;
        for (size_t j = 0; j < bb->stmt_count; j++) {
            max_extra += 16;
        }
        max_extra += 16;
        
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
    
    // Recursively elaborate all drops
    bool changed = true;
    while (changed) {
        changed = false;
        size_t current_count = body->bb_count; 
        for (size_t i = 0; i < current_count; i++) {
            if (expand_drop(body, (AxMirBbId){(uint32_t)i}, thir, hir, db, interner)) {
                changed = true;
            }
        }
    }
    
    free(call_inits);
    free(local_flags);
}
