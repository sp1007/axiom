#include "driver/mono.h"
#include "driver/driver.h"
#include "resolve/resolve.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* T161: must equal TC_SELF_PARAM_INDEX (types/typeck.c), the parameter index of the trait `Self`. */
#define AX_MONO_SELF_PARAM_INDEX 0xFFFFFF00u

static void deduce_args_n(TypeId gen_ty, TypeId spec_ty, TypeInterner *in, TypeId *args, size_t count) {
    if (gen_ty.v == spec_ty.v || gen_ty.v == 0 || spec_ty.v == 0) return;
    const AxType *gen = ax_type_get(in, gen_ty);
    const AxType *spec = ax_type_get(in, spec_ty);
    if (!gen || !spec) return;

    if (gen->kind == AX_TY_PARAM) {
        /* T161: the trait `Self` parameter is not one of the callee's generic arguments. */
        if (gen->param.index == AX_MONO_SELF_PARAM_INDEX || gen->param.index >= count) return;
        args[gen->param.index] = spec_ty;
        return;
    }
    if (gen->kind != spec->kind) return;

    switch ((int)gen->kind) {
        case AX_TY_FN:
            deduce_args_n(gen->fn.ret_type, spec->fn.ret_type, in, args, count);
            for (size_t i = 0; i < gen->fn.param_count && i < spec->fn.param_count; i++) {
                deduce_args_n(gen->fn.param_types[i], spec->fn.param_types[i], in, args, count);
            }
            break;
        case AX_TY_PTR:
            deduce_args_n(gen->ptr.pointee, spec->ptr.pointee, in, args, count);
            break;
        case AX_TY_VIEW:
        case AX_TY_MUT_VIEW:
            deduce_args_n(gen->view.pointee, spec->view.pointee, in, args, count);
            break;
        case AX_TY_ARRAY:
            deduce_args_n(gen->array.elem, spec->array.elem, in, args, count);
            break;
        case AX_TY_SLICE:
            deduce_args_n(gen->slice.elem, spec->slice.elem, in, args, count);
            break;
        case AX_TY_TUPLE:
            for (size_t i = 0; i < gen->tuple.field_count && i < spec->tuple.field_count; i++) {
                deduce_args_n(gen->tuple.fields[i], spec->tuple.fields[i], in, args, count);
            }
            break;
        case AX_TY_STRUCT:
            for (size_t i = 0; i < gen->strct.arg_count && i < spec->strct.arg_count; i++) {
                deduce_args_n(gen->strct.args[i], spec->strct.args[i], in, args, count);
            }
            break;
        case AX_TY_ENUM:
            for (size_t i = 0; i < gen->enm.arg_count && i < spec->enm.arg_count; i++) {
                deduce_args_n(gen->enm.args[i], spec->enm.args[i], in, args, count);
            }
            break;
        default: break;
    }
}

/* Substitutes the generic arguments `args` and, when self_ty is set, the trait `Self` parameter
 * (T161: the MIR instance of a default method for one implementing type). */
static TypeId subst_ty_self(TypeId ty, const AxGenericArgs *args, TypeId self_ty, TypeInterner *in) {
    if ((!args || args->count == 0) && self_ty.v == 0) return ty;
    const AxType *t = ax_type_get(in, ty);
    if (!t) return ty;
    if (t->kind == AX_TY_PARAM) {
        if (self_ty.v != 0 && t->param.index == AX_MONO_SELF_PARAM_INDEX) return self_ty;
        if (args && t->param.index < args->count && args->args[t->param.index].v != 0) return args->args[t->param.index];
        return ty;
    }
    AxType new_t = *t;
    bool changed = false;
    switch ((int)t->kind) {
        case AX_TY_FN: {
            new_t.fn.ret_type = subst_ty_self(t->fn.ret_type, args, self_ty, in);
            if (new_t.fn.ret_type.v != t->fn.ret_type.v) changed = true;
            TypeId *params = malloc(t->fn.param_count * sizeof(TypeId));
            for (size_t i = 0; i < t->fn.param_count; i++) {
                params[i] = subst_ty_self(t->fn.param_types[i], args, self_ty, in);
                if (params[i].v != t->fn.param_types[i].v) changed = true;
            }
            new_t.fn.param_types = params;
            break;
        }
        case AX_TY_PTR:
            new_t.ptr.pointee = subst_ty_self(t->ptr.pointee, args, self_ty, in);
            if (new_t.ptr.pointee.v != t->ptr.pointee.v) changed = true;
            break;
        case AX_TY_VIEW:
        case AX_TY_MUT_VIEW:
            new_t.view.pointee = subst_ty_self(t->view.pointee, args, self_ty, in);
            if (new_t.view.pointee.v != t->view.pointee.v) changed = true;
            break;
        case AX_TY_ARRAY:
            new_t.array.elem = subst_ty_self(t->array.elem, args, self_ty, in);
            if (new_t.array.elem.v != t->array.elem.v) changed = true;
            break;
        case AX_TY_SLICE:
            new_t.slice.elem = subst_ty_self(t->slice.elem, args, self_ty, in);
            if (new_t.slice.elem.v != t->slice.elem.v) changed = true;
            break;
        case AX_TY_TUPLE: {
            TypeId *fields = malloc(t->tuple.field_count * sizeof(TypeId));
            for (size_t i = 0; i < t->tuple.field_count; i++) {
                fields[i] = subst_ty_self(t->tuple.fields[i], args, self_ty, in);
                if (fields[i].v != t->tuple.fields[i].v) changed = true;
            }
            new_t.tuple.fields = fields;
            break;
        }
        case AX_TY_STRUCT: {
            TypeId *s_args = malloc(t->strct.arg_count * sizeof(TypeId));
            for (size_t i = 0; i < t->strct.arg_count; i++) {
                s_args[i] = subst_ty_self(t->strct.args[i], args, self_ty, in);
                if (s_args[i].v != t->strct.args[i].v) changed = true;
            }
            new_t.strct.args = s_args;
            if (t->strct.field_count > 0 && t->strct.fields) {
                TypeId *s_fields = malloc(t->strct.field_count * sizeof(TypeId));
                for (size_t i = 0; i < t->strct.field_count; i++) {
                    s_fields[i] = subst_ty_self(t->strct.fields[i], args, self_ty, in);
                    if (s_fields[i].v != t->strct.fields[i].v) changed = true;
                }
                new_t.strct.fields = s_fields;
            }
            break;
        }
        case AX_TY_ENUM: {
            TypeId *e_args = malloc(t->enm.arg_count * sizeof(TypeId));
            for (size_t i = 0; i < t->enm.arg_count; i++) {
                e_args[i] = subst_ty_self(t->enm.args[i], args, self_ty, in);
                if (e_args[i].v != t->enm.args[i].v) changed = true;
            }
            new_t.enm.args = e_args;
            if (t->enm.variant_fields) {
                TypeId **new_vfields = malloc(t->enm.variant_count * sizeof(TypeId *));
                for (size_t v = 0; v < t->enm.variant_count; v++) {
                    if (t->enm.variant_field_counts[v] > 0) {
                        new_vfields[v] = malloc(t->enm.variant_field_counts[v] * sizeof(TypeId));
                        for (size_t i = 0; i < t->enm.variant_field_counts[v]; i++) {
                            new_vfields[v][i] = subst_ty_self(t->enm.variant_fields[v][i], args, self_ty, in);
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
        case AX_TY_CLOSURE: {
            new_t.closure.ret_type = subst_ty_self(t->closure.ret_type, args, self_ty, in);
            if (new_t.closure.ret_type.v != t->closure.ret_type.v) changed = true;
            if (t->closure.param_count > 0) {
                TypeId *params = malloc(t->closure.param_count * sizeof(TypeId));
                for (size_t i = 0; i < t->closure.param_count; i++) {
                    params[i] = subst_ty_self(t->closure.params[i], args, self_ty, in);
                    if (params[i].v != t->closure.params[i].v) changed = true;
                }
                new_t.closure.params = params;
            }
            if (t->closure.capture_count > 0) {
                AxClosureCapture *caps = malloc(t->closure.capture_count * sizeof(AxClosureCapture));
                for (size_t i = 0; i < t->closure.capture_count; i++) {
                    caps[i] = t->closure.captures[i];
                    caps[i].type = subst_ty_self(t->closure.captures[i].type, args, self_ty, in);
                    if (caps[i].type.v != t->closure.captures[i].type.v) changed = true;
                }
                new_t.closure.captures = caps;
            }
            break;
        }
        default: break;
    }
    if (changed) return ax_intern_type(in, &new_t);
    return ty;
}

static TypeId subst_ty_local(TypeId ty, const AxGenericArgs *args, TypeInterner *in) {
    return subst_ty_self(ty, args, (TypeId){0}, in);
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
        if ((w->orig_item == orig_item || (orig_item->fn.symbol.v != 0 && w->orig_item->fn.symbol.v == orig_item->fn.symbol.v)) && args_eq(&w->args, &args)) return w;
    }
    WorkItem *w = malloc(sizeof(WorkItem));
    w->orig_item = orig_item;
    w->args = args;
    w->body = NULL;
    
    if (orig_item->fn.name.v == 0) {
        char buf[64];
        snprintf(buf, sizeof(buf), "__ax_fn_%u", orig_item->fn.symbol.v);
        w->mangled_name = ax_intern_cstr(&st->interner, buf);
        w->mangled_sym = orig_item->fn.symbol;
        w->new_item = orig_item;
    } else if (args.count == 0) {
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

        const TypeId *orig_pty = AxItemTypeMap_get(&st->thir.item_types, orig_item);
        if (orig_pty) {
            TypeId new_ty = subst_ty_local(*orig_pty, &args, &st->thir.interner);
            AxItemTypeMap_insert(&st->thir.item_types, w->new_item, new_ty);
        }
    }
    
    w->next = g_instances;
    g_instances = w;
    
    WorkItem *todo = malloc(sizeof(WorkItem));
    *todo = *w;
    todo->next = g_worklist;
    g_worklist = todo;
    return w;
}

static void subst_operand(AxMirOperand *op, const AxGenericArgs *args, TypeId self_ty, TypeInterner *in) {
    if (op->kind == AX_MIR_OP_CONST) {
        op->constant.ty = subst_ty_self(op->constant.ty, args, self_ty, in);
    }
}

static AxMirBody *subst_mir_body_self(AxDriverState *st, AxMirBody *orig, const AxGenericArgs *args, TypeId self_ty) {
    if (args->count == 0 && self_ty.v == 0) return orig;
    AxMirBody *b = ax_arena_alloc(&st->hir_arena, sizeof(AxMirBody), _Alignof(AxMirBody));
    *b = *orig;
    b->locals = ax_arena_alloc(&st->hir_arena, orig->local_count * sizeof(AxMirLocalDecl), _Alignof(AxMirLocalDecl));
    memcpy(b->locals, orig->locals, orig->local_count * sizeof(AxMirLocalDecl));
    for (size_t i = 0; i < b->local_count; i++) {
        b->locals[i].ty = subst_ty_self(orig->locals[i].ty, args, self_ty, &st->thir.interner);
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
                    switch (stmt->assign.rvalue.kind) {
                        case AX_MIR_RVALUE_USE:
                            subst_operand(&stmt->assign.rvalue.use, args, self_ty, &st->thir.interner);
                            break;
                        case AX_MIR_RVALUE_REPEAT:
                            subst_operand(&stmt->assign.rvalue.repeat.op, args, self_ty, &st->thir.interner);
                            subst_operand(&stmt->assign.rvalue.repeat.count, args, self_ty, &st->thir.interner);
                            break;
                        case AX_MIR_RVALUE_CAST:
                            stmt->assign.rvalue.cast.ty = subst_ty_self(stmt->assign.rvalue.cast.ty, args, self_ty, &st->thir.interner);
                            subst_operand(&stmt->assign.rvalue.cast.op, args, self_ty, &st->thir.interner);
                            break;
                        case AX_MIR_RVALUE_BINARY_OP:
                            subst_operand(&stmt->assign.rvalue.binary_op.lhs, args, self_ty, &st->thir.interner);
                            subst_operand(&stmt->assign.rvalue.binary_op.rhs, args, self_ty, &st->thir.interner);
                            break;
                        case AX_MIR_RVALUE_UNARY_OP:
                            subst_operand(&stmt->assign.rvalue.unary_op.operand, args, self_ty, &st->thir.interner);
                            break;
                        case AX_MIR_RVALUE_AGGREGATE:
                            if (stmt->assign.rvalue.aggregate.operand_count > 0) {
                                size_t op_cnt = stmt->assign.rvalue.aggregate.operand_count;
                                AxMirOperand *ops = ax_arena_alloc(&st->hir_arena, op_cnt * sizeof(AxMirOperand), _Alignof(AxMirOperand));
                                memcpy(ops, stmt->assign.rvalue.aggregate.operands, op_cnt * sizeof(AxMirOperand));
                                for (size_t k = 0; k < op_cnt; k++) {
                                    subst_operand(&ops[k], args, self_ty, &st->thir.interner);
                                }
                                stmt->assign.rvalue.aggregate.operands = ops;
                            }
                            break;
                        default: break;
                    }
                }
            }
        }
        
        AxMirTerminator *term = &b->bbs[i].terminator;
        switch (term->kind) {
            case AX_MIR_TERM_CALL:
                subst_operand(&term->call.func, args, self_ty, &st->thir.interner);
                if (term->call.arg_count > 0) {
                    term->call.args = ax_arena_alloc(&st->hir_arena, orig->bbs[i].terminator.call.arg_count * sizeof(AxMirOperand), _Alignof(AxMirOperand));
                    memcpy(term->call.args, orig->bbs[i].terminator.call.args, term->call.arg_count * sizeof(AxMirOperand));
                    for (size_t j = 0; j < term->call.arg_count; j++) {
                        subst_operand(&term->call.args[j], args, self_ty, &st->thir.interner);
                    }
                }
                break;
            case AX_MIR_TERM_SWITCH_INT:
                subst_operand(&term->switch_int.discr, args, self_ty, &st->thir.interner);
                break;
            case AX_MIR_TERM_ASSERT:
                subst_operand(&term->assert.cond, args, self_ty, &st->thir.interner);
                break;
            default: break;
        }
    }
    return b;
}

static AxMirBody *subst_mir_body(AxDriverState *st, AxMirBody *orig, const AxGenericArgs *args) {
    return subst_mir_body_self(st, orig, args, (TypeId){0});
}

static bool impl_matches_receiver(AxDriverState *st, const AxHirItem *impl_it, TypeId receiver_ty) {
    if (receiver_ty.v == 0 || !impl_it->impl.self_type) return false;
    const AxType *rt = ax_type_get(&st->thir.interner, receiver_ty);
    while (rt && (rt->kind == AX_TY_VIEW || rt->kind == AX_TY_MUT_VIEW || rt->kind == AX_TY_PTR)) {
        receiver_ty = (rt->kind == AX_TY_PTR) ? rt->ptr.pointee : rt->view.pointee;
        if (receiver_ty.v == 0) return false;
        rt = ax_type_get(&st->thir.interner, receiver_ty);
    }
    if (!rt) return false;

    const AxHirType *st_hir = impl_it->impl.self_type;
    if (st_hir->kind == AX_HIR_TYPE_PATH) {
        if (st_hir->path.path.symbol.v != 0) {
            if (rt->kind == AX_TY_STRUCT && rt->strct.def && rt->strct.def->struct_decl.symbol.v == st_hir->path.path.symbol.v) return true;
            if (rt->kind == AX_TY_ENUM && rt->enm.def && rt->enm.def->enum_decl.symbol.v == st_hir->path.path.symbol.v) return true;
        }
        StrId s_name = st_hir->path.path.name;
        if (s_name.v != 0) {
            if (rt->kind == AX_TY_STRUCT && rt->strct.def && rt->strct.def->struct_decl.name.v == s_name.v) return true;
            if (rt->kind == AX_TY_ENUM && rt->enm.def && rt->enm.def->enum_decl.name.v == s_name.v) return true;
            StrView sv = ax_interner_get(&st->interner, s_name);
            if (rt->kind == AX_TY_I32 && ax_sv_eq(sv, ax_sv_cstr("i32"))) return true;
            if (rt->kind == AX_TY_U32 && ax_sv_eq(sv, ax_sv_cstr("u32"))) return true;
            if (rt->kind == AX_TY_I64 && ax_sv_eq(sv, ax_sv_cstr("i64"))) return true;
            if (rt->kind == AX_TY_U64 && ax_sv_eq(sv, ax_sv_cstr("u64"))) return true;
            if (rt->kind == AX_TY_ISIZE && ax_sv_eq(sv, ax_sv_cstr("isize"))) return true;
            if (rt->kind == AX_TY_USIZE && ax_sv_eq(sv, ax_sv_cstr("usize"))) return true;
            if (rt->kind == AX_TY_BOOL && ax_sv_eq(sv, ax_sv_cstr("bool"))) return true;
            if (rt->kind == AX_TY_CHAR && ax_sv_eq(sv, ax_sv_cstr("char"))) return true;
            if (rt->kind == AX_TY_STR && ax_sv_eq(sv, ax_sv_cstr("str"))) return true;
        }
    }
    return false;
}

/* ---- T161: per-implementing-type instances of trait default methods -------------------------------------------
 * typeck gives every impl that does not override a default method a member item sharing the trait member's body
 * (types/typeck.c tc_instantiate_default_methods) and records the implementing type under the item address tagged
 * with 2. Here the MIR built from that shared body becomes the body "as if written in the impl" (0133 §8, §9, §14):
 * `Self` is replaced by the implementing type, and every call of a trait member whose receiver now has a concrete
 * type is bound to that type's impl member (an override or the type's own default instance). Calls on other
 * type parameters (a default method's own `U`) stay as they are and are bound per instance below (native) as for
 * any generic function. */
static const AxHirItem *trait_of_member(AxDriverState *st, uint32_t sym_v, const AxHirItem **out_member) {
    for (const AxHirItem *it = st->hir.items; it; it = it->next) {
        if (it->kind != AX_HIR_ITEM_TRAIT) continue;
        for (const AxHirItem *m = it->trait.members; m; m = m->next) {
            if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v) {
                *out_member = m;
                return it;
            }
        }
    }
    return NULL;
}

static bool impl_is_of_trait(AxDriverState *st, const AxHirItem *impl_it, const AxHirItem *tr) {
    const AxHirType *tp = impl_it->impl.trait_path;
    if (!tp || !tr) return false;
    if (tp->path.path.symbol.v != 0 && tp->path.path.symbol.v == tr->trait.symbol.v) return true;
    StrView tr_name = (tp->span.file.v != 0) ? ax_source_db_span_text(&st->db, tp->span) : (StrView){0};
    if (tr_name.len == 0 && tp->path.path.name.v != 0) tr_name = ax_interner_get(&st->interner, tp->path.path.name);
    return tr_name.len > 0 && ax_sv_eq(ax_interner_get(&st->interner, tr->trait.name), tr_name);
}

static const AxHirItem *impl_member_for(AxDriverState *st, const AxHirItem *tr, StrId name, TypeId receiver_ty) {
    for (int pass = 0; pass < 2; pass++) {
        for (const AxHirItem *it = st->hir.items; it; it = it->next) {
            if (it->kind != AX_HIR_ITEM_IMPL || !it->impl.trait_path) continue;
            if (pass == 0 && !impl_is_of_trait(st, it, tr)) continue;
            if (!impl_matches_receiver(st, it, receiver_ty)) continue;
            for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == name.v) return m;
            }
        }
    }
    return NULL;
}

static bool tm_has_self_param(AxDriverState *st, const AxHirItem *tm) {
    if (!tm || !tm->fn.params) return false;
    StrView sv = {0};
    if (tm->fn.params->name.v != 0) {
        sv = ax_interner_get(&st->interner, tm->fn.params->name);
    } else if (tm->fn.params->span.file.v != 0) {
        sv = ax_source_db_span_text(&st->db, tm->fn.params->span);
    }
    return ax_sv_eq(sv, ax_sv_cstr("self"));
}

AxMirBody *ax_mono_instantiate_default(AxDriverState *st, const AxHirItem *inst, AxMirBody *body) {
    if (!inst || !body) return body;
    const TypeId *self_ty = AxItemTypeMap_get(&st->thir.item_types, (const AxHirItem *)((uintptr_t)inst | (uintptr_t)2));
    if (!self_ty || self_ty->v == 0) return body;
    static const AxGenericArgs no_args = {NULL, 0};
    AxMirBody *b = subst_mir_body_self(st, body, &no_args, *self_ty);
    TypeInterner *in = &st->thir.interner;
    for (size_t i = 0; i < b->bb_count; i++) {
        AxMirTerminator *term = &b->bbs[i].terminator;
        if (term->kind != AX_MIR_TERM_CALL || term->call.func.kind != AX_MIR_OP_CONST) continue;
        TypeId fty = term->call.func.constant.ty;
        const AxType *ft = (fty.v != 0) ? ax_type_get(in, fty) : NULL;
        if (!ft || ft->kind != AX_TY_FN) continue;
        const AxHirItem *tm = NULL;
        const AxHirItem *tr = trait_of_member(st, (uint32_t)term->call.func.constant.val, &tm);
        if (!tr) continue;
        bool has_self = tm_has_self_param(st, tm);
        TypeId recv = {0};
        if (has_self) {
            if (term->call.arg_count == 0) continue;
            recv = (term->call.args[0].kind == AX_MIR_OP_CONST) ? term->call.args[0].constant.ty
                 : (term->call.args[0].place.local.v < b->local_count ? b->locals[term->call.args[0].place.local.v].ty : (TypeId){0});
        } else {
            recv = *self_ty;
        }
        if (recv.v == 0) continue;
        const AxHirItem *m = impl_member_for(st, tr, tm->fn.name, recv);
        if (!m) continue;
        term->call.func.constant.val = m->fn.symbol.v;
        const TypeId *mty = AxItemTypeMap_get(&st->thir.item_types, m);
        if (mty && mty->v != 0) term->call.func.constant.ty = *mty;
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
                        if (it->kind == AX_HIR_ITEM_IMPL) {
                            for (AxHirItem *m = it->impl.members; m; m = m->next) {
                                if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v.v) {
                                    callee = m;
                                    break;
                                }
                            }
                            if (callee) break;
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
                                if (trait_method) break;
                            }
                        }
                        if (trait_method) {
                            TypeId receiver_ty = (TypeId){0};
                            if (term->call.arg_count > 0) {
                                if (term->call.args[0].kind == AX_MIR_OP_CONST) {
                                    receiver_ty = term->call.args[0].constant.ty;
                                } else {
                                    receiver_ty = w->body->locals[term->call.args[0].place.local.v].ty;
                                }
                            }
                            // Find the matching impl for receiver_ty
                            for (AxHirItem *it = st->hir.items; it; it = it->next) {
                                if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path) {
                                    if (receiver_ty.v == 0 || impl_matches_receiver(st, it, receiver_ty)) {
                                        for (AxHirItem *m = it->impl.members; m; m = m->next) {
                                            if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == trait_method->fn.name.v) {
                                                callee = m;
                                                term->call.func.constant.val = m->fn.symbol.v;
                                                break;
                                            }
                                        }
                                        if (callee) break;
                                    }
                                }
                            }
                            if (!callee) {
                                callee = trait_method;
                                term->call.func.constant.val = trait_method->fn.symbol.v;
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
                            deduce_args_n(gen_ty, spec_ty, &st->thir.interner, args, count);

                            const AxType *gt = ax_type_get(&st->thir.interner, gen_ty);
                            if (gt && gt->kind == AX_TY_FN) {
                                for (size_t a = 0; a < term->call.arg_count && a < gt->fn.param_count; a++) {
                                    TypeId arg_ty = (TypeId){0};
                                    if (term->call.args[a].kind == AX_MIR_OP_CONST) {
                                        arg_ty = term->call.args[a].constant.ty;
                                    } else if (term->call.args[a].place.local.v < w->body->local_count) {
                                        arg_ty = w->body->locals[term->call.args[a].place.local.v].ty;
                                    }
                                    if (arg_ty.v != 0) {
                                        deduce_args_n(gt->fn.param_types[a], arg_ty, &st->thir.interner, args, count);
                                    }
                                }
                                if (term->call.destination.local.v < w->body->local_count) {
                                    TypeId ret_ty = w->body->locals[term->call.destination.local.v].ty;
                                    if (ret_ty.v != 0) {
                                        deduce_args_n(gt->fn.ret_type, ret_ty, &st->thir.interner, args, count);
                                    }
                                }
                            }

                            AxGenericArgs gargs = { args, count };
                            WorkItem *callee_inst = find_or_create_inst(st, callee, gargs);
                            term->call.func.constant.val = callee_inst->mangled_sym.v;
                            const TypeId *inst_ty = AxItemTypeMap_get(&st->thir.item_types, callee_inst->new_item);
                            if (inst_ty && inst_ty->v != 0) {
                                term->call.func.constant.ty = *inst_ty;
                            }
                        }
                    } else if (callee) {
                        WorkItem *callee_inst = find_or_create_inst(st, callee, (AxGenericArgs){NULL, 0});
                        term->call.func.constant.val = callee_inst->mangled_sym.v;
                        const TypeId *inst_ty = AxItemTypeMap_get(&st->thir.item_types, callee_inst->new_item);
                        if (inst_ty && inst_ty->v != 0) {
                            term->call.func.constant.ty = *inst_ty;
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

    // Deduplicate any colliding symbol names in g_instances
    for (WorkItem *w = g_instances; w; w = w->next) {
        if (!w->body || !w->orig_item || w->orig_item->fn.name.v == 0) continue;
        StrView w_name = ax_interner_get(&st->interner, w->orig_item->fn.name);
        if (ax_sv_eq(w_name, ax_sv_cstr("main"))) continue;

        bool has_duplicate = false;
        for (WorkItem *other = g_instances; other; other = other->next) {
            if (other != w && other->body && other->orig_item && other->orig_item->fn.name.v != 0 &&
                other->orig_item->fn.name.v == w->orig_item->fn.name.v) {
                has_duplicate = true;
                break;
            }
        }

        if (has_duplicate) {
            char buf[256];
            snprintf(buf, sizeof(buf), "%.*s_%u", (int)w_name.len, w_name.ptr, w->mangled_sym.v);
            StrId new_name = ax_intern_cstr(&st->interner, buf);
            w->mangled_name = new_name;
            if (w->new_item) w->new_item->fn.name = new_name;
            if (w->orig_item) w->orig_item->fn.name = new_name;
            for (AxHirItem *it = st->hir.items; it; it = it->next) {
                if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == w->mangled_sym.v) {
                    it->fn.name = new_name;
                }
                if (it->kind == AX_HIR_ITEM_IMPL) {
                    for (AxHirItem *m = it->impl.members; m; m = m->next) {
                        if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == w->mangled_sym.v) {
                            m->fn.name = new_name;
                        }
                    }
                }
            }
        }
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
