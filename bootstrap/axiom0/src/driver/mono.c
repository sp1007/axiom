#include "driver/mono.h"
#include "driver/driver.h"
#include "resolve/resolve.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void deduce_args(TypeId gen_ty, TypeId spec_ty, TypeInterner *in, TypeId *args) {
    if (gen_ty.v == spec_ty.v || gen_ty.v == 0 || spec_ty.v == 0) return;
    const AxType *gen = ax_type_get(in, gen_ty);
    const AxType *spec = ax_type_get(in, spec_ty);
    if (!gen || !spec) return;

    if (gen->kind == AX_TY_PARAM) {
        args[gen->param.index] = spec_ty;
        return;
    }
    if (gen->kind != spec->kind) return;

    switch ((int)gen->kind) {
        case AX_TY_FN:
            deduce_args(gen->fn.ret_type, spec->fn.ret_type, in, args);
            for (size_t i = 0; i < gen->fn.param_count && i < spec->fn.param_count; i++) {
                deduce_args(gen->fn.param_types[i], spec->fn.param_types[i], in, args);
            }
            break;
        case AX_TY_PTR:
            deduce_args(gen->ptr.pointee, spec->ptr.pointee, in, args);
            break;
        case AX_TY_VIEW:
        case AX_TY_MUT_VIEW:
            deduce_args(gen->view.pointee, spec->view.pointee, in, args);
            break;
        case AX_TY_ARRAY:
            deduce_args(gen->array.elem, spec->array.elem, in, args);
            break;
        case AX_TY_SLICE:
            deduce_args(gen->slice.elem, spec->slice.elem, in, args);
            break;
        case AX_TY_TUPLE:
            for (size_t i = 0; i < gen->tuple.field_count && i < spec->tuple.field_count; i++) {
                deduce_args(gen->tuple.fields[i], spec->tuple.fields[i], in, args);
            }
            break;
        case AX_TY_STRUCT:
            for (size_t i = 0; i < gen->strct.arg_count && i < spec->strct.arg_count; i++) {
                deduce_args(gen->strct.args[i], spec->strct.args[i], in, args);
            }
            break;
        case AX_TY_ENUM:
            for (size_t i = 0; i < gen->enm.arg_count && i < spec->enm.arg_count; i++) {
                deduce_args(gen->enm.args[i], spec->enm.args[i], in, args);
            }
            break;
        default: break;
    }
}

static TypeId subst_ty_local(TypeId ty, const AxGenericArgs *args, TypeInterner *in) {
    if (!args || args->count == 0) return ty;
    const AxType *t = ax_type_get(in, ty);
    if (!t) return ty;
    if (t->kind == AX_TY_PARAM) {
        if (t->param.index < args->count) return args->args[t->param.index];
        return ty;
    }
    AxType new_t = *t;
    bool changed = false;
    switch ((int)t->kind) {
        case AX_TY_FN: {
            new_t.fn.ret_type = subst_ty_local(t->fn.ret_type, args, in);
            if (new_t.fn.ret_type.v != t->fn.ret_type.v) changed = true;
            TypeId *params = malloc(t->fn.param_count * sizeof(TypeId));
            for (size_t i = 0; i < t->fn.param_count; i++) {
                params[i] = subst_ty_local(t->fn.param_types[i], args, in);
                if (params[i].v != t->fn.param_types[i].v) changed = true;
            }
            new_t.fn.param_types = params;
            break;
        }
        case AX_TY_PTR:
            new_t.ptr.pointee = subst_ty_local(t->ptr.pointee, args, in);
            if (new_t.ptr.pointee.v != t->ptr.pointee.v) changed = true;
            break;
        case AX_TY_VIEW:
        case AX_TY_MUT_VIEW:
            new_t.view.pointee = subst_ty_local(t->view.pointee, args, in);
            if (new_t.view.pointee.v != t->view.pointee.v) changed = true;
            break;
        case AX_TY_ARRAY:
            new_t.array.elem = subst_ty_local(t->array.elem, args, in);
            if (new_t.array.elem.v != t->array.elem.v) changed = true;
            break;
        case AX_TY_SLICE:
            new_t.slice.elem = subst_ty_local(t->slice.elem, args, in);
            if (new_t.slice.elem.v != t->slice.elem.v) changed = true;
            break;
        case AX_TY_TUPLE: {
            TypeId *fields = malloc(t->tuple.field_count * sizeof(TypeId));
            for (size_t i = 0; i < t->tuple.field_count; i++) {
                fields[i] = subst_ty_local(t->tuple.fields[i], args, in);
                if (fields[i].v != t->tuple.fields[i].v) changed = true;
            }
            new_t.tuple.fields = fields;
            break;
        }
        case AX_TY_STRUCT: {
            TypeId *s_args = malloc(t->strct.arg_count * sizeof(TypeId));
            for (size_t i = 0; i < t->strct.arg_count; i++) {
                s_args[i] = subst_ty_local(t->strct.args[i], args, in);
                if (s_args[i].v != t->strct.args[i].v) changed = true;
            }
            new_t.strct.args = s_args;
            break;
        }
        case AX_TY_ENUM: {
            TypeId *e_args = malloc(t->enm.arg_count * sizeof(TypeId));
            for (size_t i = 0; i < t->enm.arg_count; i++) {
                e_args[i] = subst_ty_local(t->enm.args[i], args, in);
                if (e_args[i].v != t->enm.args[i].v) changed = true;
            }
            new_t.enm.args = e_args;
            if (t->enm.variant_fields) {
                TypeId **new_vfields = malloc(t->enm.variant_count * sizeof(TypeId *));
                for (size_t v = 0; v < t->enm.variant_count; v++) {
                    if (t->enm.variant_field_counts[v] > 0) {
                        new_vfields[v] = malloc(t->enm.variant_field_counts[v] * sizeof(TypeId));
                        for (size_t i = 0; i < t->enm.variant_field_counts[v]; i++) {
                            new_vfields[v][i] = subst_ty_local(t->enm.variant_fields[v][i], args, in);
                            if (new_vfields[v][i].v != t->enm.variant_fields[v][i].v) changed = true;
                        }
                    } else {
                        new_vfields[v] = NULL;
                    }
                }
                new_t.enm.variant_fields = (TypeId **)new_vfields;
            }
            break;
        }
        default: break;
    }
    if (changed) return ax_intern_type(in, &new_t);
    return ty;
}

typedef struct WorkItem {
    AxHirItem *orig_item;
    AxGenericArgs args;
    AxSymbolId mangled_sym;
    StrId mangled_name;
    AxMirBody *body;
    AxHirItem *new_item;
    struct WorkItem *next;
} WorkItem;

static WorkItem *g_worklist = NULL;
static WorkItem *g_instances = NULL;

static bool args_eq(const AxGenericArgs *a, const AxGenericArgs *b) {
    if (a->count != b->count) return false;
    for (size_t i = 0; i < a->count; i++) {
        if (a->args[i].v != b->args[i].v) return false;
    }
    return true;
}

static WorkItem *find_or_create_inst(AxDriverState *st, AxHirItem *orig_item, AxGenericArgs args) {
    for (WorkItem *w = g_instances; w; w = w->next) {
        if (w->orig_item == orig_item && args_eq(&w->args, &args)) return w;
    }
    WorkItem *w = malloc(sizeof(WorkItem));
    w->orig_item = orig_item;
    w->args = args;
    w->body = NULL;
    
    if (args.count == 0) {
        w->mangled_sym = orig_item->fn.symbol;
        w->mangled_name = orig_item->fn.name;
        w->new_item = orig_item;
    } else {
        w->mangled_sym.v = ++st->resolve_map.next_symbol_v;
        StrView orig_name = ax_interner_get(&st->interner, orig_item->fn.name);
        char buf[256];
        static int counter = 1;
        snprintf(buf, sizeof(buf), "%.*s_I%dE", (int)orig_name.len, orig_name.ptr, counter++);
        w->mangled_name = ax_intern_cstr(&st->interner, buf);
        
        w->new_item = ax_arena_alloc(&st->hir_arena, sizeof(AxHirItem), _Alignof(AxHirItem));
        *w->new_item = *orig_item;
        w->new_item->fn.name = w->mangled_name;
        w->new_item->fn.symbol = w->mangled_sym;
        w->new_item->next = st->hir.items;
        st->hir.items = w->new_item;
    }
    
    w->next = g_instances;
    g_instances = w;
    
    WorkItem *todo = malloc(sizeof(WorkItem));
    *todo = *w;
    todo->next = g_worklist;
    g_worklist = todo;
    return w;
}

static AxMirBody *subst_mir_body(AxDriverState *st, AxMirBody *orig, const AxGenericArgs *args) {
    if (args->count == 0) return orig;
    AxMirBody *b = ax_arena_alloc(&st->hir_arena, sizeof(AxMirBody), _Alignof(AxMirBody));
    *b = *orig;
    b->locals = ax_arena_alloc(&st->hir_arena, orig->local_count * sizeof(AxMirLocalDecl), _Alignof(AxMirLocalDecl));
    memcpy(b->locals, orig->locals, orig->local_count * sizeof(AxMirLocalDecl));
    for (size_t i = 0; i < b->local_count; i++) {
        b->locals[i].ty = subst_ty_local(orig->locals[i].ty, args, &st->thir.interner);
    }
    
    b->bbs = ax_arena_alloc(&st->hir_arena, orig->bb_count * sizeof(AxMirBb), _Alignof(AxMirBb));
    for (size_t i = 0; i < orig->bb_count; i++) {
        b->bbs[i] = orig->bbs[i];
        if (orig->bbs[i].stmt_count > 0) {
            b->bbs[i].stmts = ax_arena_alloc(&st->hir_arena, orig->bbs[i].stmt_count * sizeof(AxMirStmt), _Alignof(AxMirStmt));
            memcpy(b->bbs[i].stmts, orig->bbs[i].stmts, orig->bbs[i].stmt_count * sizeof(AxMirStmt));
            for (size_t j = 0; j < b->bbs[i].stmt_count; j++) {
                AxMirStmt *stmt = &b->bbs[i].stmts[j];
                if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                    if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_CAST) {
                        stmt->assign.rvalue.cast.ty = subst_ty_local(stmt->assign.rvalue.cast.ty, args, &st->thir.interner);
                    }
                    if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_USE && stmt->assign.rvalue.use.kind == AX_MIR_OP_CONST) {
                        stmt->assign.rvalue.use.constant.ty = subst_ty_local(stmt->assign.rvalue.use.constant.ty, args, &st->thir.interner);
                    }
                }
            }
        }
        
        AxMirTerminator *term = &b->bbs[i].terminator;
        if (term->kind == AX_MIR_TERM_CALL) {
            if (term->call.func.kind == AX_MIR_OP_CONST) {
                term->call.func.constant.ty = subst_ty_local(term->call.func.constant.ty, args, &st->thir.interner);
            }
            if (term->call.arg_count > 0) {
                term->call.args = ax_arena_alloc(&st->hir_arena, orig->bbs[i].terminator.call.arg_count * sizeof(AxMirOperand), _Alignof(AxMirOperand));
                memcpy(term->call.args, orig->bbs[i].terminator.call.args, term->call.arg_count * sizeof(AxMirOperand));
                for (size_t j = 0; j < term->call.arg_count; j++) {
                    if (term->call.args[j].kind == AX_MIR_OP_CONST) {
                        term->call.args[j].constant.ty = subst_ty_local(term->call.args[j].constant.ty, args, &st->thir.interner);
                    }
                }
            }
        }
    }
    return b;
}

void ax_stage_mono(struct AxDriverState *st) {
    st->mono_instances = NULL;
    g_worklist = NULL;
    g_instances = NULL;

    for (AxHirItem *it = st->hir.items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) {
            size_t count = 0;
            if (it->fn.generic_params) {
                for (AxHirGenericParam *p = it->fn.generic_params->params; p; p = p->next) count++;
            }
            if (count == 0) {
                find_or_create_inst(st, it, (AxGenericArgs){NULL, 0});
            }
        }
    }

    while (g_worklist != NULL) {
        WorkItem *w = g_worklist;
        g_worklist = w->next;

        AxMirBody *orig_mir = ax_pipeline_get_mir(w->orig_item);
        if (orig_mir) {
            w->body = subst_mir_body(st, orig_mir, &w->args);
            for (size_t i = 0; i < w->body->bb_count; i++) {
                AxMirTerminator *term = &w->body->bbs[i].terminator;
                if (term->kind == AX_MIR_TERM_CALL && term->call.func.kind == AX_MIR_OP_CONST) {
                    AxSymbolId sym_v = { (uint32_t)term->call.func.constant.val };
                    AxHirItem *callee = NULL;
                    for (AxHirItem *it = st->hir.items; it; it = it->next) {
                        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == sym_v.v) {
                            callee = it;
                            break;
                        }
                    }
                    if (!callee) {
                        AxHirItem *trait_method = NULL;
                        for (AxHirItem *it = st->hir.items; it; it = it->next) {
                            if (it->kind == AX_HIR_ITEM_TRAIT) {
                                for (AxHirItem *m = it->trait.members; m; m = m->next) {
                                    if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v.v) {
                                        trait_method = m;
                                        break;
                                    }
                                }
                            }
                        }
                        if (trait_method) {
                            // Find the impl for S
                            for (AxHirItem *it = st->hir.items; it; it = it->next) {
                                if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path) {
                                    for (AxHirItem *m = it->impl.members; m; m = m->next) {
                                        if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == trait_method->fn.name.v) {
                                            callee = m;
                                            term->call.func.constant.val = m->fn.symbol.v;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                    size_t count = 0;
                    if (callee && callee->fn.generic_params) {
                        for (AxHirGenericParam *p = callee->fn.generic_params->params; p; p = p->next) count++;
                    }
                    if (count > 0) {
                        const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, callee);
                        if (pty) {
                            TypeId gen_ty = *pty;
                            TypeId spec_ty = term->call.func.constant.ty;
                            TypeId *args = calloc(count, sizeof(TypeId));
                            deduce_args(gen_ty, spec_ty, &st->thir.interner, args);
                            AxGenericArgs gargs = { args, count };
                            WorkItem *callee_inst = find_or_create_inst(st, callee, gargs);
                            term->call.func.constant.val = callee_inst->mangled_sym.v;
                        }
                    }
                }
            }
        }

        WorkItem *saved = g_instances;
        while (saved) {
            if (saved->orig_item == w->orig_item && args_eq(&saved->args, &w->args)) {
                saved->body = w->body;
                break;
            }
            saved = saved->next;
        }
        free(w);
    }

    AxMonoInstance **tail = &st->mono_instances;
    WorkItem *curr = g_instances;
    while (curr) {
        if (curr->body) {
            AxMonoInstance *inst = ax_arena_alloc(&st->hir_arena, sizeof(AxMonoInstance), _Alignof(AxMonoInstance));
            inst->item = curr->new_item;
            inst->body = curr->body;
            inst->mangled_name = curr->mangled_name;
            inst->next = NULL;
            *tail = inst;
            tail = &inst->next;
        }
        WorkItem *next = curr->next;
        free(curr);
        curr = next;
    }
}
