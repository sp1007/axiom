#include "types/types.h"
#include "source/source.h"
#include <string.h>
#include <stdio.h>
#include <inttypes.h>

/* Type checker for the axiom0 subset (SPEC-03 §2-§4, §8).
 *
 * Diagnostic discipline (T115): a mismatch is reported exactly once, at the place where it is
 * detected. check_expr() is the single coercion seam: it unifies the expression's type with the
 * expected type and, on failure, reports AX_TYPE_MISMATCH and returns the error type. The error
 * type unifies with everything, so enclosing expressions never report the same problem again. */

typedef struct IntTypeVar {
    TypeId resolved_to; // none if unresolved
    bool is_generic;
    Span span;
} IntTypeVar;

/* AXS-SEM-021: integer literals are range-checked after typing (the final type is known only
 * once the function body has been inferred and unconstrained variables defaulted). */
typedef struct LitCheck {
    Span span;          // the literal
    Span neg_span;      // the enclosing unary minus when negated
    uint64_t value;
    TypeId ty;
    bool negated;
} LitCheck;

/* A unary minus on a non-literal operand whose type is still an integer variable: whether it is
 * applied to an unsigned type is known only after inference. */
typedef struct NegCheck {
    Span span;
    TypeId ty;
} NegCheck;


typedef struct LoopEnv {
    StrId label;
    TypeId break_ty;
    bool has_break;
} LoopEnv;
typedef struct VarState {
    AxSymbolId sym;
    bool is_mut;
    bool is_init;
} VarState;

typedef struct TypeckCtx {
    const AxHir *hir;
    AxThir *thir;
    AxDiagSink *sink;
    StrInterner *str_in;
    const SourceDatabase *db;

    // Integer type variables. Numbering is global to one typeck run so that a variable TypeId
    // never aliases a variable of another function; defaulting is per function (fn_var_start).
    IntTypeVar *int_vars;
    size_t int_vars_len;
    size_t int_vars_cap;
    size_t fn_var_start;

    LitCheck *lits;
    size_t lits_len;
    size_t lits_cap;

    NegCheck *negs;
    size_t negs_len;
    size_t negs_cap;
    
    VarState *vars;
    size_t vars_len;
    size_t vars_cap;

    TypeId return_type;
    bool in_loop;

    LoopEnv *loops;
    size_t loops_len;
    size_t loops_cap;

    const AxHirItem *current_fn;
    const AxHirItem *current_impl;
    TypeId self_ty;
    uint32_t next_closure_id;
} TypeckCtx;

static bool dotted_name_eq(const AxAstDottedName *a, const AxAstDottedName *b) {
    if (!a || !b) return true;
    if (a->count != b->count) return false;
    for (size_t i = 0; i < a->count; i++) {
        if (a->segments[i].v != b->segments[i].v) return false;
    }
    return true;
}

static TypeId type_error(TypeckCtx *cx, Span span, AxDiagCode code) {
    AxDiagnostic d = {0};
    d.code = code;
    d.severity = AX_DIAG_ERROR;
    d.message = ax_diag_code_default_message(code);
    d.primary = span;
    ax_diag_sink_report(cx->sink, &d);
    return cx->thir->interner.t_error;
}

static TypeId new_int_var(TypeckCtx *cx) {
    if (cx->int_vars_len == cx->int_vars_cap) {
        cx->int_vars = ax_grow_array(cx->int_vars, &cx->int_vars_cap, sizeof(IntTypeVar), cx->int_vars_len + 1);
    }
    uint32_t var_id = (uint32_t)cx->int_vars_len;
    cx->int_vars[cx->int_vars_len].resolved_to = TypeId_none();
    cx->int_vars[cx->int_vars_len].is_generic = false;
    cx->int_vars[cx->int_vars_len].span = (Span){0};
    cx->int_vars_len++;

    AxType t;
    memset(&t, 0, sizeof(t));
    t.kind = AX_TY_INT_VAR;
    t.int_var.var_id = var_id;
    return ax_intern_type(&cx->thir->interner, &t);
}


static TypeId new_ty_var(TypeckCtx *cx, Span span) {
    if (cx->int_vars_len == cx->int_vars_cap) {
        cx->int_vars = ax_grow_array(cx->int_vars, &cx->int_vars_cap, sizeof(IntTypeVar), cx->int_vars_len + 1);
    }
    uint32_t var_id = (uint32_t)cx->int_vars_len;
    cx->int_vars[cx->int_vars_len].resolved_to = TypeId_none();
    cx->int_vars[cx->int_vars_len].is_generic = true;
    cx->int_vars[cx->int_vars_len].span = span;
    cx->int_vars_len++;

    AxType t;
    memset(&t, 0, sizeof(t));
    t.kind = AX_TY_VAR;
    t.int_var.var_id = var_id;
    return ax_intern_type(&cx->thir->interner, &t);
}

static TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path, AxGenericArgs *out_args);
static TypeId resolve_ty(TypeckCtx *cx, TypeId id) {
    if (TypeId_is_none(id) || id.v == 0) return id;
    const AxType *t = ax_type_get(&cx->thir->interner, id);
    if (!t) return id;
    if (t->kind == AX_TY_INT_VAR || t->kind == AX_TY_VAR) {
        TypeId resolved = cx->int_vars[t->int_var.var_id].resolved_to;
        if (TypeId_is_some(resolved) && resolved.v != 0) {
            // Path compression
            TypeId fully_resolved = resolve_ty(cx, resolved);
            cx->int_vars[t->int_var.var_id].resolved_to = fully_resolved;
            return fully_resolved;
        }
    }
    return id;
}

static AxTypeKind kind_of(TypeckCtx *cx, TypeId id) {
    if (TypeId_is_none(id) || id.v == 0) return AX_TY_ERROR;
    TypeId r = resolve_ty(cx, id);
    if (TypeId_is_none(r) || r.v == 0) return AX_TY_ERROR;
    const AxType *t = ax_type_get(&cx->thir->interner, r);
    return t ? t->kind : AX_TY_ERROR;
}

static bool is_error(TypeckCtx *cx, TypeId id) {
    return kind_of(cx, id) == AX_TY_ERROR;
}

static bool is_never(TypeckCtx *cx, TypeId id) {
    return kind_of(cx, id) == AX_TY_NEVER;
}

/* Integer type or integer type variable. */
static bool is_intlike(TypeckCtx *cx, TypeId id) {
    TypeId r = resolve_ty(cx, id);
    return kind_of(cx, r) == AX_TY_INT_VAR || ax_type_is_int(r, &cx->thir->interner);
}

static bool unify_ty(TypeckCtx *cx, TypeId a, TypeId b) {
    a = resolve_ty(cx, a);
    b = resolve_ty(cx, b);
    if (TypeId_eq(a, b)) return true;

    const AxType *ta = ax_type_get(&cx->thir->interner, a);
    const AxType *tb = ax_type_get(&cx->thir->interner, b);

    if (ta->kind == AX_TY_ERROR || tb->kind == AX_TY_ERROR) return true;
    if (ta->kind == AX_TY_NEVER || tb->kind == AX_TY_NEVER) return true; // never coerces


    // AXS-SEM-020: an integer type variable can only become an integer type.
    if (ta->kind == AX_TY_VAR) {
        if (tb->kind != AX_TY_VAR || ta->int_var.var_id != tb->int_var.var_id)
            cx->int_vars[ta->int_var.var_id].resolved_to = b;
        return true;
    }
    if (tb->kind == AX_TY_VAR) {
        cx->int_vars[tb->int_var.var_id].resolved_to = a;
        return true;
    }

    if (ta->kind == AX_TY_INT_VAR) {
        if (tb->kind == AX_TY_INT_VAR || ax_type_is_int(b, &cx->thir->interner)) {
            cx->int_vars[ta->int_var.var_id].resolved_to = b;
            return true;
        }
        return false;
    }
    if (tb->kind == AX_TY_INT_VAR) {
        if (ax_type_is_int(a, &cx->thir->interner)) {
            cx->int_vars[tb->int_var.var_id].resolved_to = a;
            return true;
        }
        return false;
    }

    if (ta->kind == AX_TY_TUPLE && tb->kind == AX_TY_TUPLE) {
        if (ta->tuple.field_count != tb->tuple.field_count) return false;
        bool ok = true;
        for (size_t i = 0; i < ta->tuple.field_count; i++) {
            if (!unify_ty(cx, ta->tuple.fields[i], tb->tuple.fields[i])) ok = false;
        }
        return ok;
    }

    if (ta->kind == AX_TY_ARRAY && tb->kind == AX_TY_ARRAY) {
        return ta->array.len == tb->array.len && unify_ty(cx, ta->array.elem, tb->array.elem);
    }

    if (ta->kind == AX_TY_VIEW && tb->kind == AX_TY_VIEW) {
        return unify_ty(cx, ta->view.pointee, tb->view.pointee);
    }
    if (ta->kind == AX_TY_MUT_VIEW && tb->kind == AX_TY_MUT_VIEW) {
        return unify_ty(cx, ta->view.pointee, tb->view.pointee);
    }
    if (ta->kind == AX_TY_STR && tb->kind == AX_TY_VIEW) {
        const AxType *p_tb = ax_type_get(&cx->thir->interner, tb->view.pointee);
        return p_tb->kind == AX_TY_SLICE && unify_ty(cx, cx->thir->interner.t_u8, p_tb->slice.elem);
    }
    if (tb->kind == AX_TY_STR && ta->kind == AX_TY_VIEW) {
        const AxType *p_ta = ax_type_get(&cx->thir->interner, ta->view.pointee);
        return p_ta->kind == AX_TY_SLICE && unify_ty(cx, cx->thir->interner.t_u8, p_ta->slice.elem);
    }

    if (ta->kind == AX_TY_ENUM && tb->kind == AX_TY_ENUM) {
        if (ta->enm.def != tb->enm.def) return false;
        if (ta->enm.arg_count != tb->enm.arg_count) return false;
        bool ok = true;
        for (size_t i = 0; i < ta->enm.arg_count; i++) {
            if (!unify_ty(cx, ta->enm.args[i], tb->enm.args[i])) ok = false;
        }
        return ok;
    }

    if (ta->kind == AX_TY_STRUCT && tb->kind == AX_TY_STRUCT) {
        if (ta->strct.def != tb->strct.def) return false;
        if (ta->strct.arg_count != tb->strct.arg_count) return false;
        bool ok = true;
        for (size_t i = 0; i < ta->strct.arg_count; i++) {
            if (!unify_ty(cx, ta->strct.args[i], tb->strct.args[i])) ok = false;
        }
        return ok;
    }

    if (ta->kind == AX_TY_FN && tb->kind == AX_TY_FN) {
        if (ta->fn.param_count != tb->fn.param_count) return false;
        if (!unify_ty(cx, ta->fn.ret_type, tb->fn.ret_type)) return false;
        for (size_t i = 0; i < ta->fn.param_count; i++) {
            if (!unify_ty(cx, ta->fn.param_types[i], tb->fn.param_types[i])) return false;
        }
        return true;
    }

    if (ta->kind == AX_TY_CLOSURE && tb->kind == AX_TY_CLOSURE) {
        return ta->closure.closure_id == tb->closure.closure_id;
    }

    return false;
}

static TypeId coerce(TypeckCtx *cx, TypeId ty, TypeId expected, Span span) {
    if (TypeId_is_none(expected)) return ty;
    
    if (ty.v && expected.v && !is_error(cx, ty) && !is_error(cx, expected)) {
        const AxType *t_ty = ax_type_get(&cx->thir->interner, resolve_ty(cx, ty));
        const AxType *t_exp = ax_type_get(&cx->thir->interner, resolve_ty(cx, expected));
        if ((t_ty->kind == AX_TY_VIEW && t_exp->kind == AX_TY_VIEW) || 
            (t_ty->kind == AX_TY_MUT_VIEW && t_exp->kind == AX_TY_MUT_VIEW)) {
            const AxType *p_ty = ax_type_get(&cx->thir->interner, t_ty->view.pointee);
            const AxType *p_exp = ax_type_get(&cx->thir->interner, t_exp->view.pointee);
            if (p_ty->kind == AX_TY_ARRAY && p_exp->kind == AX_TY_SLICE) {
                if (unify_ty(cx, p_ty->array.elem, p_exp->slice.elem)) {
                    return expected;
                }
            }
        }
        if (t_ty->kind == AX_TY_CLOSURE && t_exp->kind == AX_TY_FN) {
            if (t_ty->closure.capture_count == 0 && t_ty->closure.param_count == t_exp->fn.param_count) {
                bool ok = unify_ty(cx, t_ty->closure.ret_type, t_exp->fn.ret_type);
                for (size_t i = 0; i < t_ty->closure.param_count && ok; i++) {
                    ok = unify_ty(cx, t_ty->closure.params[i], t_exp->fn.param_types[i]);
                }
                if (ok) return expected;
            }
            return type_error(cx, span, AX_TYPE_MISMATCH);
        }
        if (t_ty->kind == AX_TY_FN && t_exp->kind == AX_TY_CLOSURE) {
            return type_error(cx, span, AX_TYPE_MISMATCH);
        }
    }
    
    if (!unify_ty(cx, ty, expected)) {
        return type_error(cx, span, AX_TYPE_MISMATCH);
    }
    return ty;
}

static void default_int_vars(TypeckCtx *cx) {
    // AXS-SEM-020: still unconstrained at the end of the function body -> i32.
    for (size_t i = cx->fn_var_start; i < cx->int_vars_len; i++) {
        if (TypeId_is_none(cx->int_vars[i].resolved_to)) {
            if (cx->int_vars[i].is_generic) {
                type_error(cx, cx->int_vars[i].span, AX_TYPE_UNKNOWN);
                cx->int_vars[i].resolved_to = cx->thir->interner.t_error;
            } else {
                cx->int_vars[i].resolved_to = cx->thir->interner.t_i32;
            }
        }
    }
}

static TypeId hir_type_to_typeid(TypeckCtx *cx, const AxHirType *ht) {
    if (!ht) return (TypeId){0};
    if (ht->kind == AX_HIR_TYPE_ERROR) return cx->thir->interner.t_error;
    if (ht->kind == AX_HIR_TYPE_PATH) {
        StrView name = ax_source_db_span_text(cx->db, ht->path.path.span);
        if (ax_sv_eq_cstr(name, "i32")) return cx->thir->interner.t_i32;
        if (ax_sv_eq_cstr(name, "u32")) return cx->thir->interner.t_u32;
        if (ax_sv_eq_cstr(name, "i64")) return cx->thir->interner.t_i64;
        if (ax_sv_eq_cstr(name, "u64")) return cx->thir->interner.t_u64;
        if (ax_sv_eq_cstr(name, "i16")) return cx->thir->interner.t_i16;
        if (ax_sv_eq_cstr(name, "u16")) return cx->thir->interner.t_u16;
        if (ax_sv_eq_cstr(name, "i8")) return cx->thir->interner.t_i8;
        if (ax_sv_eq_cstr(name, "u8")) return cx->thir->interner.t_u8;
        if (ax_sv_eq_cstr(name, "isize")) return cx->thir->interner.t_isize;
        if (ax_sv_eq_cstr(name, "usize")) return cx->thir->interner.t_usize;
        if (ax_sv_eq_cstr(name, "bool")) return cx->thir->interner.t_bool;
        if (ax_sv_eq_cstr(name, "char")) return cx->thir->interner.t_char;
        if (ax_sv_eq_cstr(name, "Str")) return cx->thir->interner.t_str;
        if (ax_sv_eq_cstr(name, "never")) return cx->thir->interner.t_never;
        if (ax_sv_eq_cstr(name, "f32") || ax_sv_eq_cstr(name, "f64")) return type_error(cx, ht->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);

        TypeId t = lookup_path_type(cx, &ht->path.path, NULL);
        return t;
    }
    if (ht->kind == AX_HIR_TYPE_FN) {
        AxType t;
        memset(&t, 0, sizeof(t));
        t.kind = AX_TY_FN;
        t.fn.is_unsafe = ht->fn.is_unsafe;
        t.fn.abi = ht->fn.abi;
        t.fn.ret_type = hir_type_to_typeid(cx, ht->fn.ret_type);

        size_t count = 0;
        for (const AxHirType *p = ht->fn.param_types; p; p = p->next) count++;
        t.fn.param_count = count;
        if (count > 0) {
            t.fn.param_types = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * count, _Alignof(TypeId));
            size_t i = 0;
            for (const AxHirType *p = ht->fn.param_types; p; p = p->next) {
                t.fn.param_types[i++] = hir_type_to_typeid(cx, p);
            }
        } else {
            t.fn.param_types = NULL;
        }
        return ax_intern_type(&cx->thir->interner, &t);
    }
    if (ht->kind == AX_HIR_TYPE_ARRAY) {
        TypeId elem = hir_type_to_typeid(cx, ht->array.elem);
        uint64_t len = 0;
        if (ht->array.count->kind == AX_HIR_EXPR_LITERAL && ht->array.count->literal.kind == AX_TOK_INT) {
            len = ht->array.count->literal.val.int_val.value;
        } else {
            type_error(cx, ht->array.count->span, AX_TYPE_ARRAY_SIZE);
            return cx->thir->interner.t_error;
        }
        AxType t;
        memset(&t, 0, sizeof(t));
        t.kind = AX_TY_ARRAY;
        t.array.elem = elem;
        t.array.len = len;
        return ax_intern_type(&cx->thir->interner, &t);
    }
    if (ht->kind == AX_HIR_TYPE_TUPLE) {
        size_t count = 0;
        for (const AxHirType *e = ht->tuple.elem_types; e; e = e->next) count++;
        TypeId *fields = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * count, _Alignof(TypeId));
        size_t i = 0;
        for (const AxHirType *e = ht->tuple.elem_types; e; e = e->next) {
            fields[i++] = hir_type_to_typeid(cx, e);
        }
        AxType t = { .kind = AX_TY_TUPLE, .tuple = { .field_count = count, .fields = fields } };
        return ax_intern_type(&cx->thir->interner, &t);
    }
    if (ht->kind == AX_HIR_TYPE_SLICE) {
        TypeId elem = hir_type_to_typeid(cx, ht->slice.elem);
        AxType t;
        memset(&t, 0, sizeof(t));
        t.kind = AX_TY_SLICE;
        t.slice.elem = elem;
        return ax_intern_type(&cx->thir->interner, &t);
    }
    if (ht->kind == AX_HIR_TYPE_VIEW) {
        AxType t;
        memset(&t, 0, sizeof(t));
        t.kind = ht->view.is_mut ? AX_TY_MUT_VIEW : AX_TY_VIEW;
        t.view.pointee = hir_type_to_typeid(cx, ht->view.elem);
        return ax_intern_type(&cx->thir->interner, &t);
    }
    return type_error(cx, ht->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
}

/* ---- AXS-SEM-021 literal range checks ---------------------------------------------------- */

static size_t record_lit(TypeckCtx *cx, Span span, uint64_t value, TypeId ty) {
    if (cx->lits_len == cx->lits_cap) {
        cx->lits = ax_grow_array(cx->lits, &cx->lits_cap, sizeof(LitCheck), cx->lits_len + 1);
    }
    LitCheck *l = &cx->lits[cx->lits_len];
    memset(l, 0, sizeof(*l));
    l->span = span;
    l->value = value;
    l->ty = ty;
    l->negated = false;
    return cx->lits_len++;
}

static void record_neg(TypeckCtx *cx, Span span, TypeId ty) {
    if (cx->negs_len == cx->negs_cap) {
        cx->negs = ax_grow_array(cx->negs, &cx->negs_cap, sizeof(NegCheck), cx->negs_len + 1);
    }
    cx->negs[cx->negs_len].span = span;
    cx->negs[cx->negs_len].ty = ty;
    cx->negs_len++;
}

/* Largest magnitude allowed for a literal of `kind`: the positive maximum, or (negated) the
 * magnitude of the minimum. isize/usize are 64-bit on every v0.1 target (AXS-SEM-011). */
static uint64_t int_limit(AxTypeKind kind, bool negated) {
    switch (kind) {
        case AX_TY_I8: return negated ? UINT64_C(128) : UINT64_C(127);
        case AX_TY_I16: return negated ? UINT64_C(32768) : UINT64_C(32767);
        case AX_TY_I32: return negated ? UINT64_C(2147483648) : UINT64_C(2147483647);
        case AX_TY_I64:
        case AX_TY_ISIZE: return negated ? (UINT64_C(1) << 63) : ((UINT64_C(1) << 63) - 1);
        case AX_TY_U8: return UINT64_C(0xFF);
        case AX_TY_U16: return UINT64_C(0xFFFF);
        case AX_TY_U32: return UINT64_C(0xFFFFFFFF);
        case AX_TY_U64:
        case AX_TY_USIZE: return UINT64_MAX;
        default: return UINT64_MAX;
    }
}

static void check_literal_ranges(TypeckCtx *cx) {
    for (size_t i = 0; i < cx->lits_len; i++) {
        const LitCheck *l = &cx->lits[i];
        TypeId t = resolve_ty(cx, l->ty);
        if (!ax_type_is_int(t, &cx->thir->interner)) continue; // already reported elsewhere
        AxTypeKind k = ax_type_get(&cx->thir->interner, t)->kind;
        if (l->negated && ax_type_is_unsigned(t, &cx->thir->interner)) {
            // `-0` is the one negated unsigned literal SPEC-03 accepts.
            if (l->value != 0) type_error(cx, l->neg_span, AX_TYPE_NEG_UNSIGNED);
            continue;
        }
        if (l->value > int_limit(k, l->negated)) {
            type_error(cx, l->negated ? l->neg_span : l->span, AX_TYPE_LITERAL_OUT_OF_RANGE);
        }
    }
    cx->lits_len = 0;

    for (size_t i = 0; i < cx->negs_len; i++) {
        TypeId t = resolve_ty(cx, cx->negs[i].ty);
        if (ax_type_is_unsigned(t, &cx->thir->interner)) {
            type_error(cx, cx->negs[i].span, AX_TYPE_NEG_UNSIGNED);
        }
    }
    cx->negs_len = 0;
}

static TypeId suffix_type(TypeckCtx *cx, AxSuffix s) {
    const TypeInterner *in = &cx->thir->interner;
    switch (s) {
        case AX_SUFFIX_I8: return in->t_i8;
        case AX_SUFFIX_I16: return in->t_i16;
        case AX_SUFFIX_I32: return in->t_i32;
        case AX_SUFFIX_I64: return in->t_i64;
        case AX_SUFFIX_ISIZE: return in->t_isize;
        case AX_SUFFIX_U8: return in->t_u8;
        case AX_SUFFIX_U16: return in->t_u16;
        case AX_SUFFIX_U32: return in->t_u32;
        case AX_SUFFIX_U64: return in->t_u64;
        case AX_SUFFIX_USIZE: return in->t_usize;
        default: return TypeId_none();
    }
}

/* Type of an integer literal token: its suffix type (AXS-SEM-020) or a fresh variable. Records
 * the literal for the range check; *lit_index receives the record index. */
static TypeId int_literal_type(TypeckCtx *cx, const AxToken *tok, Span span, size_t *lit_index) {
    AxSuffix s = tok->val.int_val.suffix;
    if (s == AX_SUFFIX_F32 || s == AX_SUFFIX_F64) {
        // AXS-SEM-010: `1f64` is a float literal; floats are not in axiom0.
        return type_error(cx, span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
    }
    TypeId ty = s == AX_SUFFIX_NONE ? new_int_var(cx) : suffix_type(cx, s);
    size_t idx = record_lit(cx, span, tok->val.int_val.value, ty);
    if (lit_index) *lit_index = idx;
    return ty;
}

/* ---- AXS-SEM-080 main signature ---------------------------------------------------------- */

static void check_main_signature(TypeckCtx *cx) {
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind != AX_HIR_ITEM_FN) continue;
        StrView name = ax_interner_get(cx->str_in, it->fn.name);
        if (!ax_sv_eq_cstr(name, "main")) continue;

        bool ok = it->fn.params == NULL && !it->fn.is_unsafe && it->fn.abi.v == 0 &&
                  !it->fn.is_async && !it->fn.is_comptime &&
                  (it->fn.generic_params == NULL || it->fn.generic_params->params == NULL);
        TypeId *fn_ty = AxItemTypeMap_get(&cx->thir->item_types, it);
        if (ok && fn_ty) {
            TypeId ret = ax_type_get(&cx->thir->interner, *fn_ty)->fn.ret_type;
            const TypeInterner *in = &cx->thir->interner;
            if (TypeId_is_some(ret) && !TypeId_eq(ret, in->t_unit) && !TypeId_eq(ret, in->t_never) &&
                !TypeId_eq(ret, in->t_i32) && !TypeId_eq(ret, in->t_u32) && !TypeId_eq(ret, in->t_error)) {
                ok = false; // an error return type was already reported
            }
        }
        if (!ok) {
            type_error(cx, it->span, AX_TYPE_MAIN_SIGNATURE);
        }
    }
}

/* ---- THIR finalisation ------------------------------------------------------------------- */

static TypeId resolve_deep_ty(TypeckCtx *cx, TypeId id) {
    if (TypeId_is_none(id) || id.v == 0) return id;
    id = resolve_ty(cx, id);
    if (TypeId_is_none(id) || id.v == 0) return id;
    const AxType *t = ax_type_get(&cx->thir->interner, id);
    if (!t) return id;
    if (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) {
        TypeId p = resolve_deep_ty(cx, t->view.pointee);
        if (!TypeId_eq(p, t->view.pointee)) {
            AxType nt = *t;
            nt.view.pointee = p;
            return ax_intern_type(&cx->thir->interner, &nt);
        }
    }
    return id;
}

/* Replace every integer type variable in the THIR by its final type, so later phases (MIR
 * builder, verifier, interpreter, dumps) only see concrete types. */
static void finalize_types(TypeckCtx *cx) {
    uint32_t cur = 0;
    AxExprTypeMapEntry *ee;
    while (AxExprTypeMap_next(&cx->thir->expr_types, &cur, &ee)) ee->value = resolve_deep_ty(cx, ee->value);
    cur = 0;
    AxPatTypeMapEntry *pe;
    while (AxPatTypeMap_next(&cx->thir->pat_types, &cur, &pe)) pe->value = resolve_deep_ty(cx, pe->value);
    cur = 0;
    AxSymbolTypeMapEntry *se;
    while (AxSymbolTypeMap_next(&cx->thir->symbol_types, &cur, &se)) se->value = resolve_deep_ty(cx, se->value);
    cur = 0;
    AxParamTypeMapEntry *pme;
    while (AxParamTypeMap_next(&cx->thir->param_types, &cur, &pme)) pme->value = resolve_deep_ty(cx, pme->value);
}

typedef enum AxTraitResult {
    AX_TRAIT_PROVEN,
    AX_TRAIT_DISPROVEN,
    AX_TRAIT_AMBIGUOUS,
    AX_TRAIT_OVERFLOW
} AxTraitResult;

static const AxHirItem *find_trait_default_method(TypeckCtx *cx, const AxHirItem *tr, StrView method_name) {
    if (!tr || tr->kind != AX_HIR_ITEM_TRAIT) return NULL;
    for (const AxHirItem *m = tr->trait.members; m; m = m->next) {
        if (m->kind == AX_HIR_ITEM_FN && m->fn.body != NULL) {
            StrView mname = ax_interner_get(cx->str_in, m->fn.name);
            if (ax_sv_eq(mname, method_name)) return m;
        }
    }
    for (const AxHirType *st = tr->trait.supertraits; st; st = st->next) {
        StrView st_name = (st->span.file.v != 0) ? ax_source_db_span_text(cx->db, st->span) : (StrView){0};
        if (st_name.len == 0 && st->path.path.name.v != 0) st_name = ax_interner_get(cx->str_in, st->path.path.name);
        for (const AxHirItem *item = cx->hir->items; item; item = item->next) {
            if (item->kind == AX_HIR_ITEM_TRAIT) {
                StrView tname = ax_interner_get(cx->str_in, item->trait.name);
                if (ax_sv_eq(tname, st_name)) {
                    const AxHirItem *dm = find_trait_default_method(cx, item, method_name);
                    if (dm) return dm;
                }
            }
        }
    }
    return NULL;
}

static const AxHirItem *find_method(TypeckCtx *cx, TypeId base_ty, StrView method_name, AxTraitResult *out_res) {
    if (is_error(cx, base_ty)) return NULL;
    const AxHirItem *found = NULL;
    int matches = 0;
    *out_res = AX_TRAIT_DISPROVEN;
    
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL) {
            const AxHirItem *old_impl = cx->current_impl;
            cx->current_impl = it;
            TypeId self_ty = hir_type_to_typeid(cx, it->impl.self_type);
            cx->current_impl = old_impl;
            if (is_error(cx, self_ty)) continue;
            
            bool match = false;
            if (self_ty.v == base_ty.v) {
                match = true;
            } else {
                const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
                const AxType *s = ax_type_get(&cx->thir->interner, self_ty);
                if (b->kind == AX_TY_VIEW && s->kind == AX_TY_VIEW) {
                     match = (b->view.pointee.v == s->view.pointee.v);
                } else if (b->kind == AX_TY_VIEW) {
                     if (b->view.pointee.v == self_ty.v) match = true;
                }
            }

            if (match) {
                bool found_in_impl = false;
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        StrView mname = ax_interner_get(cx->str_in, m->fn.name);
                        if (ax_sv_eq(mname, method_name)) {
                            found = m;
                            matches++;
                            found_in_impl = true;
                        }
                    }
                }
                if (!found_in_impl && it->impl.trait_path) {
                    StrView tr_name = (it->impl.trait_path->span.file.v != 0) ? ax_source_db_span_text(cx->db, it->impl.trait_path->span) : (StrView){0};
                    if (tr_name.len == 0 && it->impl.trait_path->path.path.name.v != 0) {
                        tr_name = ax_interner_get(cx->str_in, it->impl.trait_path->path.path.name);
                    }
                    for (const AxHirItem *item = cx->hir->items; item; item = item->next) {
                        if (item->kind == AX_HIR_ITEM_TRAIT) {
                            bool tr_match = (it->impl.trait_path->path.path.symbol.v != 0 && item->trait.symbol.v == it->impl.trait_path->path.path.symbol.v);
                            if (!tr_match && tr_name.len > 0) {
                                StrView tname = ax_interner_get(cx->str_in, item->trait.name);
                                if (ax_sv_eq(tname, tr_name)) tr_match = true;
                            }
                            if (tr_match) {
                                const AxHirItem *dm = find_trait_default_method(cx, item, method_name);
                                if (dm) {
                                    found = dm;
                                    matches++;
                                }
                                break;
                            }
                        }
                    }
                }
            }
        } else if (it->kind == AX_HIR_ITEM_TRAIT) {
            // Also check trait methods if we are calling on a generic parameter
            const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
            bool is_param = false;
            if (b->kind == AX_TY_PARAM) is_param = true;
            if (b->kind == AX_TY_VIEW) {
                const AxType *pb = ax_type_get(&cx->thir->interner, b->view.pointee);
                if (pb->kind == AX_TY_PARAM) is_param = true;
            }
            if (is_param) {
                for (const AxHirItem *m = it->trait.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        StrView mname = ax_interner_get(cx->str_in, m->fn.name);
                        if (ax_sv_eq(mname, method_name)) {
                            found = m;
                            matches++;
                        }
                    }
                }
            }
        }
    }
    
    if (matches > 1) {
        *out_res = AX_TRAIT_AMBIGUOUS;
        return NULL;
    } else if (matches == 1) {
        *out_res = AX_TRAIT_PROVEN;
        return found;
    } else {
        *out_res = AX_TRAIT_DISPROVEN;
        return NULL;
    }
}


TypeId ax_subst_ty(TypeckCtx *cx, TypeId ty, const AxGenericArgs *args) {
    if (TypeId_is_none(ty)) return ty;
    if (args == NULL || args->count == 0) return ty;
    ty = resolve_ty(cx, ty);
    const AxType *t = ax_type_get(&cx->thir->interner, ty);
    if (t->kind == AX_TY_PARAM) {
        if (t->param.index < args->count) {
            return args->args[t->param.index];
        }
        return ty;
    }
    if (t->kind == AX_TY_ARRAY) {
        TypeId elem = ax_subst_ty(cx, t->array.elem, args);
        if (elem.v == t->array.elem.v) return ty;
        AxType new_t = *t;
        new_t.array.elem = elem;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_SLICE) {
        TypeId elem = ax_subst_ty(cx, t->slice.elem, args);
        if (elem.v == t->slice.elem.v) return ty;
        AxType new_t = *t;
        new_t.slice.elem = elem;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) {
        TypeId pointee = ax_subst_ty(cx, t->view.pointee, args);
        if (pointee.v == t->view.pointee.v) return ty;
        AxType new_t = *t;
        new_t.view.pointee = pointee;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_PTR) {
        TypeId pointee = ax_subst_ty(cx, t->ptr.pointee, args);
        if (pointee.v == t->ptr.pointee.v) return ty;
        AxType new_t = *t;
        new_t.ptr.pointee = pointee;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_TUPLE) {
        bool changed = false;
        TypeId *fields = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->tuple.field_count, _Alignof(TypeId));
        for (size_t i = 0; i < t->tuple.field_count; i++) {
            fields[i] = ax_subst_ty(cx, t->tuple.fields[i], args);
            if (fields[i].v != t->tuple.fields[i].v) changed = true;
        }
        if (!changed) return ty;
        AxType new_t = *t;
        new_t.tuple.fields = fields;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_FN) {
        bool changed = false;
        TypeId ret = ax_subst_ty(cx, t->fn.ret_type, args);
        if (ret.v != t->fn.ret_type.v) changed = true;
        TypeId *param_types = NULL;
        if (t->fn.param_count > 0) {
            param_types = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->fn.param_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->fn.param_count; i++) {
                param_types[i] = ax_subst_ty(cx, t->fn.param_types[i], args);
                if (param_types[i].v != t->fn.param_types[i].v) changed = true;
            }
        }
        if (!changed) return ty;
        AxType new_t = *t;
        new_t.fn.ret_type = ret;
        new_t.fn.param_types = param_types;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_STRUCT) {
        bool changed = false;
        TypeId *sargs = NULL;
        TypeId *fields = NULL;
        if (t->strct.arg_count > 0) {
            sargs = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->strct.arg_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->strct.arg_count; i++) {
                sargs[i] = ax_subst_ty(cx, t->strct.args[i], args);
                if (sargs[i].v != t->strct.args[i].v) changed = true;
            }
        }
        if (t->strct.field_count > 0) {
            fields = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->strct.field_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->strct.field_count; i++) {
                fields[i] = ax_subst_ty(cx, t->strct.fields[i], args);
                if (fields[i].v != t->strct.fields[i].v) changed = true;
            }
        }
        if (!changed) return ty;
        AxType new_t = *t;
        if (sargs) new_t.strct.args = sargs;
        if (fields) new_t.strct.fields = fields;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_ENUM) {
        bool changed = false;
        TypeId *eargs = NULL;
        TypeId **vfields = NULL;
        if (t->enm.arg_count > 0) {
            eargs = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->enm.arg_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->enm.arg_count; i++) {
                eargs[i] = ax_subst_ty(cx, t->enm.args[i], args);
                if (eargs[i].v != t->enm.args[i].v) changed = true;
            }
        }
        if (t->enm.variant_count > 0) {
            vfields = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId*) * t->enm.variant_count, _Alignof(TypeId*));
            for (size_t v = 0; v < t->enm.variant_count; v++) {
                if (t->enm.variant_field_counts[v] > 0) {
                    vfields[v] = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->enm.variant_field_counts[v], _Alignof(TypeId));
                    for (size_t i = 0; i < t->enm.variant_field_counts[v]; i++) {
                        vfields[v][i] = ax_subst_ty(cx, t->enm.variant_fields[v][i], args);
                        if (vfields[v][i].v != t->enm.variant_fields[v][i].v) changed = true;
                    }
                } else {
                    vfields[v] = NULL;
                }
            }
        }
        if (!changed) return ty;
        AxType new_t = *t;
        if (eargs) new_t.enm.args = eargs;
        if (vfields) new_t.enm.variant_fields = vfields;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    return ty;
}

static TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected);

static void desugar_let_else(TypeckCtx *cx, AxHirStmt *stmt) {
    if (!stmt->let.else_block) return;
    
    AxHirMatchArm *arm_else = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirMatchArm), _Alignof(AxHirMatchArm));
    arm_else->span = stmt->span;
    AxHirPat *wild = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirPat), _Alignof(AxHirPat));
    wild->kind = AX_HIR_PAT_WILDCARD;
    wild->span = stmt->span;
    wild->next = NULL;
    arm_else->pat = wild;
    
    AxHirExpr *else_blk = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    else_blk->kind = AX_HIR_EXPR_BLOCK;
    else_blk->span = stmt->let.else_block->span;
    else_blk->next = NULL;
    else_blk->block.block = *stmt->let.else_block;
    arm_else->body = else_blk;
    arm_else->guard = NULL;
    arm_else->next = NULL;
    
    AxHirMatchArm *arm_then = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirMatchArm), _Alignof(AxHirMatchArm));
    arm_then->span = stmt->span;
    arm_then->pat = stmt->let.pat;
    AxHirExpr *then_blk = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    then_blk->kind = AX_HIR_EXPR_BLOCK;
    then_blk->span = stmt->span;
    then_blk->next = NULL;
    then_blk->block.block.span = stmt->span;
    then_blk->block.block.stmts = NULL; // unit block
    arm_then->body = then_blk;
    arm_then->guard = NULL;
    arm_then->next = arm_else;
    
    AxHirExpr *match_expr = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    match_expr->kind = AX_HIR_EXPR_MATCH;
    match_expr->span = stmt->span;
    match_expr->next = NULL;
    match_expr->match.expr = stmt->let.expr;
    match_expr->match.arms = arm_then;
    
    stmt->kind = AX_HIR_STMT_EXPR;
    stmt->expr_stmt.expr = match_expr;
    stmt->expr_stmt.has_semi = true;
}


static bool is_pat_irrefutable(TypeckCtx *cx, const AxHirPat *pat, TypeId ty) {
    if (!pat) return true;
    switch (pat->kind) {
        case AX_HIR_PAT_WILDCARD:
        case AX_HIR_PAT_BINDING:
            return true;
        case AX_HIR_PAT_TUPLE:
            if (pat->tuple.elems) {
                const AxType *t = TypeId_is_none(ty) ? NULL : ax_type_get(&cx->thir->interner, ty);
                size_t i = 0;
                for (const AxHirPat *p = pat->tuple.elems; p; p = p->next) {
                    TypeId inner_ty = (t && t->kind == AX_TY_TUPLE && i < t->tuple.field_count) ? t->tuple.fields[i] : TypeId_none();
                    if (!is_pat_irrefutable(cx, p, inner_ty)) return false;
                    i++;
                }
            }
            return true;
        case AX_HIR_PAT_STRUCT:
        case AX_HIR_PAT_PATH: {
            if (TypeId_is_none(ty)) return true; // prevent crash if type is unknown
            const AxType *t = ax_type_get(&cx->thir->interner, ty);
            if (t->kind == AX_TY_STRUCT) {
                if (pat->kind == AX_HIR_PAT_STRUCT) {
                    for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                        // find field index
                        size_t idx = 0;
                        for (const AxHirFieldDecl *fd = t->strct.def->struct_decl.struct_fields; fd; fd = fd->next, idx++) {
                            if (fd->name.v == pf->name.v) break;
                        }
                        if (idx < t->strct.field_count) {
                            if (!is_pat_irrefutable(cx, pf->pat, t->strct.fields[idx])) return false;
                        }
                    }
                }
                return true;
            } else if (t->kind == AX_TY_ENUM && t->enm.variant_count == 1) {
                // Single variant enums are irrefutable!
                if (pat->kind == AX_HIR_PAT_STRUCT) {
                    for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                        size_t idx = 0;
                        const AxHirVariantDecl *vd = t->enm.def->enum_decl.variants;
                        if (vd) {
                            for (const AxHirFieldDecl *fd = vd->struct_fields; fd; fd = fd->next, idx++) {
                                if (fd->name.v == pf->name.v) break;
                            }
                            if (idx < t->enm.variant_field_counts[0]) {
                                if (!is_pat_irrefutable(cx, pf->pat, t->enm.variant_fields[0][idx])) return false;
                            }
                        }
                    }
                }
                return true;
            }
            return false;
        }
        case AX_HIR_PAT_LITERAL:
        case AX_HIR_PAT_RANGE:
        case AX_HIR_PAT_OR:
        default:
            return false; // Actually OR pattern is irrefutable if one of its branches is irrefutable? No, `A | B` is refutable unless they together cover everything, but `let` requires structurally irrefutable.
    }
}

static TypeId check_block(TypeckCtx *cx, const AxHirBlock *block, TypeId expected);
static TypeId check_expr_kind(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected);


static bool type_contains_view(const TypeckCtx *cx, TypeId id, TypeId target) {
    if (id.v == 0) return false;
    const AxType *ty = ax_type_get(&cx->thir->interner, id);
    if (!ty) return false;
    
    if (ty->kind == AX_TY_VIEW || ty->kind == AX_TY_MUT_VIEW) {
        if (target.v == 0) return true;
        if (ty->view.pointee.v == target.v) return true;
        return type_contains_view(cx, ty->view.pointee, target);
    }
    
    if (ty->kind == AX_TY_ARRAY) return type_contains_view(cx, ty->array.elem, target);
    if (ty->kind == AX_TY_TUPLE) {
        for (size_t i = 0; i < ty->tuple.field_count; i++) {
            if (type_contains_view(cx, ty->tuple.fields[i], target)) return true;
        }
    }
    if (ty->kind == AX_TY_STRUCT) {
        if (target.v != 0 && id.v == target.v) return false; // avoid infinite recursion on the target struct itself
        for (size_t i = 0; i < ty->strct.field_count; i++) {
            if (type_contains_view(cx, ty->strct.fields[i], target)) return true;
        }
    }
    if (ty->kind == AX_TY_ENUM) {
        if (target.v != 0 && id.v == target.v) return false;
        for (size_t i = 0; i < ty->enm.variant_count; i++) {
            for (size_t j = 0; j < ty->enm.variant_field_counts[i]; j++) {
                if (type_contains_view(cx, ty->enm.variant_fields[i][j], target)) return true;
            }
        }
    }
    return false;
}

static bool satisfies_bound(TypeckCtx *cx, TypeId arg_ty, AxHirType *bound) {
    if (bound->kind != AX_HIR_TYPE_PATH) return true;
    AxSymbolId trait_sym = bound->path.path.symbol;
    StrView bound_name = (bound->span.file.v != 0) ? ax_source_db_span_text(cx->db, bound->span) : (StrView){0};
    if (bound_name.len == 0 && bound->path.path.name.v != 0) bound_name = ax_interner_get(cx->str_in, bound->path.path.name);

    StrView tr_name = (bound->path.path.name.v != 0) ? ax_interner_get(cx->str_in, bound->path.path.name) : bound_name;
    bool is_fn = ax_sv_eq_cstr(tr_name, "Fn");
    bool is_fn_mut = ax_sv_eq_cstr(tr_name, "FnMut");
    bool is_fn_once = ax_sv_eq_cstr(tr_name, "FnOnce");
    bool is_callable = ax_sv_eq_cstr(tr_name, "Callable");

    if (is_fn || is_fn_mut || is_fn_once || is_callable) {
        const AxType *t = ax_type_get(&cx->thir->interner, arg_ty);
        if (t->kind == AX_TY_PARAM || t->kind == AX_TY_VAR || t->kind == AX_TY_INT_VAR) return true;
        if (t->kind == AX_TY_FN) return true;
        if (t->kind == AX_TY_CLOSURE) {
            if (is_fn) {
                for (size_t i = 0; i < t->closure.capture_count; i++) {
                    if (t->closure.captures[i].mode == AX_CAP_MUT_VIEW ||
                        t->closure.captures[i].mode == AX_CAP_MOVE) {
                        return false;
                    }
                }
                return true;
            }
            if (is_fn_mut) {
                for (size_t i = 0; i < t->closure.capture_count; i++) {
                    if (t->closure.captures[i].mode == AX_CAP_MOVE) {
                        return false;
                    }
                }
                return true;
            }
            if (is_fn_once || is_callable) {
                return true;
            }
        }
        return false;
    }

    const AxType *t = ax_type_get(&cx->thir->interner, arg_ty);
    if (t->kind == AX_TY_PARAM || t->kind == AX_TY_VAR || t->kind == AX_TY_INT_VAR) return true;

    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path && it->impl.trait_path->kind == AX_HIR_TYPE_PATH) {
            bool trait_match = (trait_sym.v != 0 && it->impl.trait_path->path.path.symbol.v == trait_sym.v);
            if (!trait_match && bound_name.len > 0) {
                StrView it_tr_name = (it->impl.trait_path->span.file.v != 0) ? ax_source_db_span_text(cx->db, it->impl.trait_path->span) : (StrView){0};
                if (it_tr_name.len == 0 && it->impl.trait_path->path.path.name.v != 0) it_tr_name = ax_interner_get(cx->str_in, it->impl.trait_path->path.path.name);
                if (ax_sv_eq(bound_name, it_tr_name)) trait_match = true;
            }
            if (trait_match && it->impl.self_type) {
                const AxHirItem *old_impl = cx->current_impl;
                cx->current_impl = it;
                TypeId impl_self_ty = hir_type_to_typeid(cx, it->impl.self_type);
                cx->current_impl = old_impl;
                if (unify_ty(cx, impl_self_ty, arg_ty)) return true;
            }
        }
    }
    return false;
}

static void check_all_bounds(TypeckCtx *cx) {
    uint32_t cur = 0;
    AxExprSubstMapEntry *e;
    while (AxExprSubstMap_next(&cx->thir->expr_substs, &cur, &e)) {
        const AxHirExpr *expr = e->key;
        AxGenericArgs *gargs = &e->value;
        const AxHirPath *path = NULL;
        if (expr->kind == AX_HIR_EXPR_PATH) {
            path = &expr->path.path;
        } else if (expr->kind == AX_HIR_EXPR_STRUCT) {
            path = &expr->struct_lit.path;
        }
        if (!path || path->symbol.v == 0) continue;

        const AxHirItem *target = NULL;
        for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == path->symbol.v) target = it;
            else if (it->kind == AX_HIR_ITEM_STRUCT && it->struct_decl.symbol.v == path->symbol.v) target = it;
            else if (it->kind == AX_HIR_ITEM_ENUM && it->enum_decl.symbol.v == path->symbol.v) target = it;
            if (target) break;
        }
        if (!target) continue;

        AxHirGenericParams *gps = NULL;
        AxHirWhereClause *wc = NULL;
        if (target->kind == AX_HIR_ITEM_FN) { gps = target->fn.generic_params; wc = target->fn.where_clause; }
        else if (target->kind == AX_HIR_ITEM_STRUCT) { gps = target->struct_decl.generic_params; wc = target->struct_decl.where_clause; }
        else if (target->kind == AX_HIR_ITEM_ENUM) { gps = target->enum_decl.generic_params; wc = target->enum_decl.where_clause; }

        if (gps) {
            size_t param_idx = 0;
            for (AxHirGenericParam *p = gps->params; p && param_idx < gargs->count; p = p->next, param_idx++) {
                TypeId arg_ty = resolve_ty(cx, gargs->args[param_idx]);
                for (AxHirType *b = p->bounds; b; b = b->next) {
                    if (!satisfies_bound(cx, arg_ty, b)) {
                        AxDiagnostic d = {0};
                        d.code = AX_TRAIT_UNSATISFIED_BOUND;
                        d.severity = AX_DIAG_ERROR;
                        d.message = "the trait bound is not satisfied";
                        d.primary = path->generic_args ? path->generic_args->span : expr->span;
                        ax_diag_sink_report(cx->sink, &d);
                    }
                }
            }
        }
        if (wc) {
            for (AxHirWherePred *pred = wc->preds; pred; pred = pred->next) {
                TypeId pred_ty_id = hir_type_to_typeid(cx, pred->type);
                pred_ty_id = ax_subst_ty(cx, pred_ty_id, gargs);
                pred_ty_id = resolve_ty(cx, pred_ty_id);
                for (AxHirType *b = pred->bounds; b; b = b->next) {
                    if (!satisfies_bound(cx, pred_ty_id, b)) {
                        AxDiagnostic d = {0};
                        d.code = AX_TRAIT_UNSATISFIED_BOUND;
                        d.severity = AX_DIAG_ERROR;
                        d.message = "the trait bound is not satisfied";
                        d.primary = path->generic_args ? path->generic_args->span : expr->span;
                        ax_diag_sink_report(cx->sink, &d);
                    }
                }
            }
        }
    }

    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path) {
            StrView tr_name = (it->impl.trait_path->span.file.v != 0) ? ax_source_db_span_text(cx->db, it->impl.trait_path->span) : (StrView){0};
            if (tr_name.len == 0 && it->impl.trait_path->path.path.name.v != 0) tr_name = ax_interner_get(cx->str_in, it->impl.trait_path->path.path.name);
            const AxHirItem *tr = NULL;
            for (const AxHirItem *item = cx->hir->items; item; item = item->next) {
                if (item->kind == AX_HIR_ITEM_TRAIT) {
                    bool tr_match = (it->impl.trait_path->path.path.symbol.v != 0 && item->trait.symbol.v == it->impl.trait_path->path.path.symbol.v);
                    if (!tr_match && tr_name.len > 0) {
                        StrView tname = ax_interner_get(cx->str_in, item->trait.name);
                        if (ax_sv_eq(tname, tr_name)) tr_match = true;
                    }
                    if (tr_match) { tr = item; break; }
                }
            }
            if (tr) {
                const AxHirItem *old_impl = cx->current_impl;
                cx->current_impl = it;
                TypeId self_ty = hir_type_to_typeid(cx, it->impl.self_type);
                cx->current_impl = old_impl;
                for (AxHirType *st = tr->trait.supertraits; st; st = st->next) {
                    if (!satisfies_bound(cx, self_ty, st)) {
                        AxDiagnostic d = {0};
                        d.code = AX_TRAIT_UNSATISFIED_BOUND;
                        d.severity = AX_DIAG_ERROR;
                        d.message = "the trait bound is not satisfied";
                        d.primary = it->span;
                        ax_diag_sink_report(cx->sink, &d);
                    }
                }
            }
        }
    }
}

AxThir ax_typeck(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in, const SourceDatabase *db) {
    AxThir thir;
    ax_thir_init(&thir);

    TypeckCtx cx;
    memset(&cx, 0, sizeof(cx));
    cx.hir = hir;
    cx.thir = &thir;
    cx.sink = sink;
    cx.str_in = str_in;
    cx.db = db;
    cx.return_type = thir.interner.t_unit;
    cx.in_loop = false;
    cx.next_closure_id = 1;

    // Pass 1a: Structs and Enums (so function signatures can reference any struct/enum)
    for (const AxHirItem *it = hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_STRUCT) {
            AxType st;
            memset(&st, 0, sizeof(st));
            st.kind = AX_TY_STRUCT;
            st.strct.def = it;
            

            size_t param_count = 0;
            AxHirGenericParam *gp = it->struct_decl.generic_params ? it->struct_decl.generic_params->params : NULL;
            for (AxHirGenericParam *p = gp; p; p = p->next) param_count++;
            
            st.strct.arg_count = param_count;
            if (param_count > 0) {
                st.strct.args = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId) * param_count, _Alignof(TypeId));
                size_t i = 0;
                for (AxHirGenericParam *p = gp; p; p = p->next) {
                    AxType pt;
                    memset(&pt, 0, sizeof(pt));
                    pt.kind = AX_TY_PARAM;
                    pt.param.name = p->name;
                    pt.param.index = i;
                    TypeId pt_id = ax_intern_type(&thir.interner, &pt);
                    st.strct.args[i] = pt_id;
                    if (p->symbol.v != 0) {
                        AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pt_id);
                    }
                    i++;
                }
            } else {
                st.strct.args = NULL;
            }

            size_t count = 0;
            for (const AxHirFieldDecl *f = it->struct_decl.struct_fields; f; f = f->next) count++;
            st.strct.field_count = count;
            
            if (count > 0) {
                st.strct.fields = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId) * count, _Alignof(TypeId));
                size_t i = 0;
                for (const AxHirFieldDecl *f = it->struct_decl.struct_fields; f; f = f->next) {
                    st.strct.fields[i++] = hir_type_to_typeid(&cx, f->type);
                }
            } else {
                st.strct.fields = NULL;
            }
            
            for (const AxHirAttr *a = it->attrs; a; a = a->next) {
                StrView aname = ax_interner_get(str_in, a->name);
                if (ax_sv_eq_cstr(aname, "repr")) {
                    st.strct.is_repr_c = true;
                }
            }
            
            TypeId st_ty = ax_intern_type(&thir.interner, &st);
            AxItemTypeMap_insert(&thir.item_types, it, st_ty);
            for (const AxHirFieldDecl *f = it->struct_decl.struct_fields; f; f = f->next) {
                if (f->type->kind == AX_HIR_TYPE_VIEW) {
                    if (f->type->view.elem->kind == AX_HIR_TYPE_PATH) {
                        StrView name = ax_source_db_span_text(cx.db, f->type->view.elem->path.path.span);
                        StrView it_name = ax_interner_get(cx.str_in, it->struct_decl.name);
                        if (ax_sv_eq(name, it_name)) {
                            AxDiagnostic d = {0};
                            d.code = AX_TYPE_STORED_VIEW_SELF_REF;
                            d.severity = AX_DIAG_ERROR;
                            d.message = "self-referencing stored views within the same struct are forbidden";
                            d.primary = f->span;
                            ax_diag_sink_report(sink, &d);
                            break;
                        }
                    }
                }
            }
        } else if (it->kind == AX_HIR_ITEM_ENUM) {
            AxType en;
            memset(&en, 0, sizeof(en));
            en.kind = AX_TY_ENUM;
            en.enm.def = it;
            

            size_t param_count = 0;
            AxHirGenericParam *gp = it->enum_decl.generic_params ? it->enum_decl.generic_params->params : NULL;
            for (AxHirGenericParam *p = gp; p; p = p->next) param_count++;
            
            en.enm.arg_count = param_count;
            if (param_count > 0) {
                en.enm.args = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId) * param_count, _Alignof(TypeId));
                size_t i = 0;
                for (AxHirGenericParam *p = gp; p; p = p->next) {
                    AxType pt;
                    memset(&pt, 0, sizeof(pt));
                    pt.kind = AX_TY_PARAM;
                    pt.param.name = p->name;
                    pt.param.index = i;
                    TypeId pt_id = ax_intern_type(&thir.interner, &pt);
                    en.enm.args[i] = pt_id;
                    if (p->symbol.v != 0) {
                        AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pt_id);
                    }
                    i++;
                }
            } else {
                en.enm.args = NULL;
            }

            size_t vcount = 0;
            for (const AxHirVariantDecl *v = it->enum_decl.variants; v; v = v->next) vcount++;
            en.enm.variant_count = vcount;
            
            if (vcount > 0) {
                en.enm.variant_fields = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId*) * vcount, _Alignof(TypeId*));
                en.enm.variant_field_counts = ax_arena_alloc(&thir.interner.arena, sizeof(size_t) * vcount, _Alignof(size_t));
                size_t i = 0;
                for (const AxHirVariantDecl *v = it->enum_decl.variants; v; v = v->next) {
                    size_t fcount = 0;
                    if (v->is_struct) {
                        for (const AxHirFieldDecl *f = v->struct_fields; f; f = f->next) fcount++;
                        en.enm.variant_field_counts[i] = fcount;
                        if (fcount > 0) {
                            en.enm.variant_fields[i] = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId) * fcount, _Alignof(TypeId));
                            size_t j = 0;
                            for (const AxHirFieldDecl *f = v->struct_fields; f; f = f->next) {
                                en.enm.variant_fields[i][j++] = hir_type_to_typeid(&cx, f->type);
                            }
                        } else {
                            en.enm.variant_fields[i] = NULL;
                        }
                    } else {
                        for (const AxHirType *t = v->tuple_types; t; t = t->next) fcount++;
                        en.enm.variant_field_counts[i] = fcount;
                        if (fcount > 0) {
                            en.enm.variant_fields[i] = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId) * fcount, _Alignof(TypeId));
                            size_t j = 0;
                            for (const AxHirType *t = v->tuple_types; t; t = t->next) {
                                en.enm.variant_fields[i][j++] = hir_type_to_typeid(&cx, t);
                            }
                        } else {
                            en.enm.variant_fields[i] = NULL;
                        }
                    }
                    i++;
                }
            } else {
                en.enm.variant_fields = NULL;
                en.enm.variant_field_counts = NULL;
            }
            TypeId en_ty = ax_intern_type(&thir.interner, &en);
            AxItemTypeMap_insert(&thir.item_types, it, en_ty);
        } else if (it->kind == AX_HIR_ITEM_IMPL && it->impl.generic_params) {
            size_t i = 0;
            for (AxHirGenericParam *p = it->impl.generic_params->params; p; p = p->next) {
                AxType pt;
                memset(&pt, 0, sizeof(pt));
                pt.kind = AX_TY_PARAM;
                pt.param.name = p->name;
                pt.param.index = i;
                TypeId pt_id = ax_intern_type(&thir.interner, &pt);
                if (p->symbol.v != 0) {
                    AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pt_id);
                }
                i++;
            }
        } else if (it->kind == AX_HIR_ITEM_TRAIT && it->trait.generic_params) {
            size_t i = 0;
            for (AxHirGenericParam *p = it->trait.generic_params->params; p; p = p->next) {
                AxType pt;
                memset(&pt, 0, sizeof(pt));
                pt.kind = AX_TY_PARAM;
                pt.param.name = p->name;
                pt.param.index = i;
                TypeId pt_id = ax_intern_type(&thir.interner, &pt);
                if (p->symbol.v != 0) {
                    AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pt_id);
                }
                i++;
            }
        } else if (it->kind == AX_HIR_ITEM_TYPE_ALIAS && it->type_alias.generic_params) {
            size_t i = 0;
            for (AxHirGenericParam *p = it->type_alias.generic_params->params; p; p = p->next) {
                AxType pt;
                memset(&pt, 0, sizeof(pt));
                pt.kind = AX_TY_PARAM;
                pt.param.name = p->name;
                pt.param.index = i;
                TypeId pt_id = ax_intern_type(&thir.interner, &pt);
                if (p->symbol.v != 0) {
                    AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pt_id);
                }
                i++;
            }
        }
    }

    // Pass 1b: Function signatures
    for (const AxHirItem *top_it = hir->items; top_it; top_it = top_it->next) {
        if (top_it->kind == AX_HIR_ITEM_IMPL) {
            cx.current_impl = top_it;
            if (top_it->impl.self_type) {
                cx.self_ty = hir_type_to_typeid(&cx, top_it->impl.self_type);
            } else {
                cx.self_ty = TypeId_none();
            }
        } else if (top_it->kind == AX_HIR_ITEM_FN && top_it->fn.symbol.v != 0) {
            cx.current_impl = NULL;
            const AxHirItem *orig_m = NULL;
            for (const AxHirItem *impl_it = hir->items; impl_it; impl_it = impl_it->next) {
                if (impl_it->kind == AX_HIR_ITEM_IMPL) {
                    for (const AxHirItem *m = impl_it->impl.members; m; m = m->next) {
                        if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == top_it->fn.symbol.v && m != top_it) {
                            orig_m = m;
                            break;
                        }
                    }
                    if (orig_m) break;
                }
            }
            if (orig_m) {
                TypeId *m_ty = AxItemTypeMap_get(&thir.item_types, orig_m);
                if (m_ty) AxItemTypeMap_insert(&thir.item_types, top_it, *m_ty);
                continue;
            }
            cx.self_ty = TypeId_none();
        } else {
            cx.current_impl = NULL;
            cx.self_ty = TypeId_none();
        }
        for (int impl_pass = 0; impl_pass < 2; impl_pass++) {
            const AxHirItem *it = (impl_pass == 0) ? top_it : 
                                  (top_it->kind == AX_HIR_ITEM_IMPL ? top_it->impl.members : 
                                  (top_it->kind == AX_HIR_ITEM_TRAIT ? top_it->trait.members : NULL));
            for (; it; it = (impl_pass == 0) ? NULL : it->next) {
            if (it->kind == AX_HIR_ITEM_FN) {
                AxHirGenericParam *gp = it->fn.generic_params ? it->fn.generic_params->params : NULL;
                size_t i = 0;
                for (AxHirGenericParam *p = gp; p; p = p->next) {
                    AxType pt;
                    memset(&pt, 0, sizeof(pt));
                    pt.kind = AX_TY_PARAM;
                    pt.param.name = p->name;
                    pt.param.index = i;
                    TypeId pt_id = ax_intern_type(&thir.interner, &pt);
                    if (p->symbol.v != 0) {
                        AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pt_id);
                    }
                    i++;
                }
                
                TypeId ret_ty = hir_type_to_typeid(&cx, it->fn.ret_type);
                if (type_contains_view(&cx, ret_ty, (TypeId){0})) {

                AxDiagnostic d2 = {0}; d2.code = AX_TYPE_STORED_VIEW_ESCAPE; d2.severity = AX_DIAG_ERROR; d2.message = "stored view might outlive the owner of the referenced data"; d2.primary = it->fn.ret_type ? it->fn.ret_type->span : it->span; ax_diag_sink_report(sink, &d2);
            }
            if (TypeId_is_none(ret_ty)) {
                ret_ty = thir.interner.t_unit;
            }

            AxType ft;
            memset(&ft, 0, sizeof(ft));
            ft.kind = AX_TY_FN;
            ft.fn.is_unsafe = it->fn.is_unsafe;
            ft.fn.abi = it->fn.abi;
            ft.fn.ret_type = ret_ty;

            size_t count = 0;
            for (const AxHirParam *p = it->fn.params; p; p = p->next) count++;
            ft.fn.param_count = count;
            if (count > 0) {
                ft.fn.param_types = ax_arena_alloc(&thir.interner.arena, sizeof(TypeId) * count, _Alignof(TypeId));
                size_t i = 0;
                for (const AxHirParam *p = it->fn.params; p; p = p->next) {
                    TypeId pty = hir_type_to_typeid(&cx, p->type);
                    ft.fn.param_types[i++] = pty;
                }
            } else {
                ft.fn.param_types = NULL;
            }

            TypeId fn_ty = ax_intern_type(&thir.interner, &ft);
            AxItemTypeMap_insert(&thir.item_types, it, fn_ty);
                } else if (it->kind == AX_HIR_ITEM_TYPE_ALIAS) {
                    TypeId ty = TypeId_none();
                    if (it->type_alias.type) {
                        ty = hir_type_to_typeid(&cx, it->type_alias.type);
                    } else {
                        AxType pt;
                        memset(&pt, 0, sizeof(pt));
                        pt.kind = AX_TY_PARAM;
                        pt.param.name = it->type_alias.name;
                        pt.param.index = 0;
                        ty = ax_intern_type(&thir.interner, &pt);
                    }
                    AxItemTypeMap_insert(&thir.item_types, it, ty);
                    if (it->type_alias.symbol.v != 0) {
                        AxSymbolTypeMap_insert(&thir.symbol_types, it->type_alias.symbol, ty);
                    }
                } else if (it->kind == AX_HIR_ITEM_CONST) {
                    TypeId ty = hir_type_to_typeid(&cx, it->const_decl.type);
                    AxItemTypeMap_insert(&thir.item_types, it, ty);
                    if (it->const_decl.symbol.v != 0) {
                        AxSymbolTypeMap_insert(&thir.symbol_types, it->const_decl.symbol, ty);
                    }
                }
            }
        }
    }

    // AXS-SEM-080 is a type rule: `check` reports it (only MAIN_MISSING is build/run-only).
    check_main_signature(&cx);

    // Pass 2: Typecheck bodies
    for (const AxHirItem *top_it = hir->items; top_it; top_it = top_it->next) {
        if (top_it->kind == AX_HIR_ITEM_IMPL) {
            cx.current_impl = top_it;
            if (top_it->impl.self_type) {
                cx.self_ty = hir_type_to_typeid(&cx, top_it->impl.self_type);
            } else {
                cx.self_ty = TypeId_none();
            }
        } else if (top_it->kind == AX_HIR_ITEM_FN && top_it->fn.symbol.v != 0) {
            cx.current_impl = NULL;
            bool is_copied = false;
            for (const AxHirItem *impl_it = hir->items; impl_it; impl_it = impl_it->next) {
                if (impl_it->kind == AX_HIR_ITEM_IMPL) {
                    for (const AxHirItem *m = impl_it->impl.members; m; m = m->next) {
                        if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == top_it->fn.symbol.v && m != top_it) {
                            is_copied = true;
                            break;
                        }
                    }
                    if (is_copied) break;
                }
            }
            if (is_copied) continue;
            cx.self_ty = TypeId_none();
        } else {
            cx.current_impl = NULL;
            cx.self_ty = TypeId_none();
        }
        for (int impl_pass = 0; impl_pass < 2; impl_pass++) {
            const AxHirItem *it = (impl_pass == 0) ? top_it : 
                                  (top_it->kind == AX_HIR_ITEM_IMPL ? top_it->impl.members : 
                                  (top_it->kind == AX_HIR_ITEM_TRAIT ? top_it->trait.members : NULL));
            for (; it; it = (impl_pass == 0) ? NULL : it->next) {
                bool is_closure = (it->fn.symbol.v >= 0x40000000 && it->fn.symbol.v < 0x50000000);
                if (it->kind == AX_HIR_ITEM_FN && it->fn.body && !is_closure) {
                    cx.current_fn = it;
            TypeId *fn_ty_ptr = AxItemTypeMap_get(&thir.item_types, it);
            if (!fn_ty_ptr) AX_ICE("typeck: fn item without a signature type");
            const AxType *fn_ty = ax_type_get(&thir.interner, *fn_ty_ptr);

            cx.fn_var_start = cx.int_vars_len;
            cx.lits_len = 0;
            cx.negs_len = 0;
            cx.return_type = fn_ty->fn.ret_type;

            size_t i = 0;
            for (const AxHirParam *p = it->fn.params; p; p = p->next, i++) {
                if (p->symbol.v != 0) {
                    AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, fn_ty->fn.param_types[i]);
                }
                AxParamTypeMap_insert(&thir.param_types, p, fn_ty->fn.param_types[i]);
            }

            check_block(&cx, it->fn.body, cx.return_type);
            default_int_vars(&cx);
            check_literal_ranges(&cx);
                } else if (it->kind == AX_HIR_ITEM_CONST && it->const_decl.expr) {
                    TypeId *cty = AxItemTypeMap_get(&thir.item_types, it);
                    TypeId expected = cty ? *cty : TypeId_none();
                    check_expr(&cx, it->const_decl.expr, expected);
                    if (it->const_decl.expr->kind == AX_HIR_EXPR_LITERAL) {
                        if (it->const_decl.expr->literal.kind == AX_TOK_INT || it->const_decl.expr->literal.kind == AX_TOK_CHAR) {
                            uint64_t val = it->const_decl.expr->literal.val.int_val.value;
                            if (it->const_decl.symbol.v != 0) {
                                AxSymbolConstMap_insert(&thir.symbol_consts, it->const_decl.symbol, val);
                            }
                        }
                    }
                }
            }
        }
    }

    finalize_types(&cx);
    check_all_bounds(&cx);

    ax_xfree(cx.int_vars);
    ax_xfree(cx.lits);
    ax_xfree(cx.negs);
    ax_xfree(cx.vars);
    ax_xfree(cx.loops);
    return thir;
}

static TypeId check_pat(TypeckCtx *cx, const AxHirPat *pat, TypeId expected, bool is_init) {
    if (!pat) return cx->thir->interner.t_unit;
    TypeId ty = expected;
    switch (pat->kind) {
        case AX_HIR_PAT_BINDING:
            if (pat->binding.symbol.v != 0) {
                AxSymbolTypeMap_insert(&cx->thir->symbol_types, pat->binding.symbol, ty);
                if (cx->vars_len == cx->vars_cap) {
                    cx->vars = ax_grow_array(cx->vars, &cx->vars_cap, sizeof(VarState), cx->vars_len + 1);
                }
                cx->vars[cx->vars_len].sym = pat->binding.symbol;
                cx->vars[cx->vars_len].is_mut = pat->binding.is_mut;
                cx->vars[cx->vars_len].is_init = is_init;
                cx->vars_len++;
            }
            break;
        case AX_HIR_PAT_LITERAL: {
            TypeId lit_ty = cx->thir->interner.t_error;
            if (pat->literal.tok.kind == AX_TOK_KW_TRUE || pat->literal.tok.kind == AX_TOK_KW_FALSE) {
                lit_ty = cx->thir->interner.t_bool;
            } else if (pat->literal.tok.kind == AX_TOK_CHAR) {
                lit_ty = cx->thir->interner.t_char;
            } else if (pat->literal.tok.kind == AX_TOK_INT) {
                lit_ty = int_literal_type(cx, &pat->literal.tok, pat->span, NULL);
            } else {
                return type_error(cx, pat->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
            }
            if (!unify_ty(cx, ty, lit_ty)) {
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }
            break;
        }
        case AX_HIR_PAT_WILDCARD:
            break;

        case AX_HIR_PAT_STRUCT: {
            AxGenericArgs gargs = {0};
            TypeId path_ty = lookup_path_type(cx, &pat->struct_pat.path, &gargs);
            if (gargs.count > 0) {
                AxPatSubstMap_insert(&cx->thir->pat_substs, pat, gargs);
            }
            if (!unify_ty(cx, ty, path_ty)) {
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }
            if (!is_error(cx, path_ty)) {
                const AxType *t = ax_type_get(&cx->thir->interner, path_ty);
                if (t->kind == AX_TY_ENUM) {
                    StrView name = ax_source_db_span_text(cx->db, pat->struct_pat.path.span);
                    StrView vname = name;
                    const char *dot = memchr(name.ptr, '.', name.len);
                    if (dot) {
                        vname.ptr = dot + 1;
                        vname.len = name.len - (dot - name.ptr) - 1;
                    }
                    bool found_variant = false;
                    size_t vidx = 0;
                    for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                        StrView var_name = ax_interner_get(cx->str_in, v->name);
                        if (ax_sv_eq(var_name, vname)) {
                            found_variant = true;
                    AxPatVariantMap_insert(&cx->thir->pat_variants, pat, vidx);
                            if (!v->is_struct) return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                            for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                                StrView iname = ax_interner_get(cx->str_in, pf->name);
                                bool found = false;
                                size_t idx = 0;
                                for (const AxHirFieldDecl *f = v->struct_fields; f; f = f->next) {
                                    StrView fname = ax_interner_get(cx->str_in, f->name);
                                    if (ax_sv_eq(fname, iname)) {
                                        found = true;
                                        check_pat(cx, pf->pat, t->enm.variant_fields[vidx][idx], is_init);
                                        break;
                                    }
                                    idx++;
                                }
                                if (!found) type_error(cx, pf->span, AX_TYPE_UNKNOWN_FIELD);
                            }
                            if (!pat->struct_pat.has_rest) {
                                for (const AxHirFieldDecl *f = v->struct_fields; f; f = f->next) {
                                    StrView fname = ax_interner_get(cx->str_in, f->name);
                                    bool found = false;
                                    for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                                        StrView iname = ax_interner_get(cx->str_in, pf->name);
                                        if (ax_sv_eq(fname, iname)) { found = true; break; }
                                    }
                                    if (!found) type_error(cx, pat->span, AX_TYPE_MISSING_FIELD);
                                }
                            }
                            break;
                        }
                        vidx++;
                    }
                    if (!found_variant) return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                    ty = path_ty;
                    break;
                } else if (t->kind == AX_TY_STRUCT) {
                    for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                        StrView iname = ax_interner_get(cx->str_in, pf->name);
                        bool found = false;
                        size_t idx = 0;
                        for (const AxHirFieldDecl *f = t->strct.def->struct_decl.struct_fields; f; f = f->next) {
                            StrView fname = ax_interner_get(cx->str_in, f->name);
                            if (ax_sv_eq(fname, iname)) {
                                found = true;
                                check_pat(cx, pf->pat, t->strct.fields[idx], is_init);
                                break;
                            }
                            idx++;
                        }
                        if (!found) type_error(cx, pf->span, AX_TYPE_UNKNOWN_FIELD);
                    }
                    if (!pat->struct_pat.has_rest) {
                        for (const AxHirFieldDecl *f = t->strct.def->struct_decl.struct_fields; f; f = f->next) {
                            StrView fname = ax_interner_get(cx->str_in, f->name);
                            bool found = false;
                            for (const AxHirPatField *pf = pat->struct_pat.fields; pf; pf = pf->next) {
                                StrView iname = ax_interner_get(cx->str_in, pf->name);
                                if (ax_sv_eq(fname, iname)) { found = true; break; }
                            }
                            if (!found) type_error(cx, pat->span, AX_TYPE_MISSING_FIELD);
                        }
                    }
                    ty = path_ty;
                    break;
                } else if (t->kind != AX_TY_ERROR) {
                    return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                } else {
                    ty = path_ty;
                    break;
                }
            } else {
                return cx->thir->interner.t_error;
            }
        }
        case AX_HIR_PAT_PATH: {
            AxGenericArgs gargs = {0};
            TypeId path_ty = lookup_path_type(cx, &pat->path.path, &gargs);
            if (gargs.count > 0) {
                AxPatSubstMap_insert(&cx->thir->pat_substs, pat, gargs);
            }
            if (is_error(cx, path_ty)) return cx->thir->interner.t_error;
            if (!unify_ty(cx, ty, path_ty)) {
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }
            const AxType *t = ax_type_get(&cx->thir->interner, path_ty);
            if (t->kind != AX_TY_ENUM) {
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }
            StrView name = (pat->path.path.span.file.v != 0) ? ax_source_db_span_text(cx->db, pat->path.path.span) : (StrView){0};
            StrView vname = name;
            const char *dot = NULL;
            for (size_t i = 0; i < name.len; i++) {
                if (name.ptr[i] == '.') dot = name.ptr + i;
            }
            if (dot) {
                vname.ptr = dot + 1;
                vname.len = name.len - (dot - name.ptr) - 1;
            }
            if (vname.len == 0 && pat->path.path.name.v != 0) {
                vname = ax_interner_get(cx->str_in, pat->path.path.name);
            }

            bool found_variant = false;
            size_t vidx = 0;
            for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                StrView var_name = ax_interner_get(cx->str_in, v->name);
                if (ax_sv_eq(var_name, vname)) {
                    found_variant = true;
                    AxPatVariantMap_insert(&cx->thir->pat_variants, pat, vidx);
                    if (v->is_struct) {
                        return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                    }
                    if (pat->path.payload) {
                        if (pat->path.payload->kind != AX_HIR_PAT_TUPLE) {
                            return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                        }
                        size_t count = 0;
                        for (const AxHirPat *p = pat->path.payload->tuple.elems; p; p = p->next) count++;
                        if (count != t->enm.variant_field_counts[vidx]) {
                            return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                        }
                        size_t i = 0;
                        for (const AxHirPat *p = pat->path.payload->tuple.elems; p; p = p->next) {
                            check_pat(cx, p, t->enm.variant_fields[vidx][i++], is_init);
                        }
                    } else {
                        if (t->enm.variant_field_counts[vidx] > 0) {
                            return type_error(cx, pat->span, AX_TYPE_MISMATCH);
                        }
                    }
                    break;
                }
                vidx++;
            }
            if (!found_variant) return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            
            ty = path_ty;
            break;
        }
        case AX_HIR_PAT_TUPLE: {
            if (is_error(cx, ty)) return cx->thir->interner.t_error;
            if (TypeId_is_none(ty)) return type_error(cx, pat->span, AX_TYPE_UNKNOWN);
            const AxType *t = ax_type_get(&cx->thir->interner, ty);
            if (!t || t->kind != AX_TY_TUPLE) return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            size_t count = 0;
            for (const AxHirPat *p = pat->tuple.elems; p; p = p->next) count++;
            if (count != t->tuple.field_count) return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            size_t i = 0;
            for (const AxHirPat *p = pat->tuple.elems; p; p = p->next) {
                check_pat(cx, p, t->tuple.fields[i++], is_init);
            }
            break;
        }
        case AX_HIR_PAT_RANGE: {
            if (is_error(cx, ty)) return cx->thir->interner.t_error;
            if (TypeId_is_none(ty)) return type_error(cx, pat->span, AX_TYPE_UNKNOWN);
            const AxType *t = ax_type_get(&cx->thir->interner, ty);
            if (!t || (t->kind != AX_TY_I8 && t->kind != AX_TY_I16 && t->kind != AX_TY_I32 && t->kind != AX_TY_I64 &&
                       t->kind != AX_TY_U8 && t->kind != AX_TY_U16 && t->kind != AX_TY_U32 && t->kind != AX_TY_U64 &&
                       t->kind != AX_TY_CHAR && t->kind != AX_TY_INT_VAR)) {
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }
            check_pat(cx, pat->range.start, ty, is_init);
            check_pat(cx, pat->range.end, ty, is_init);
            break;
        }
        case AX_HIR_PAT_OR: {
            if (is_error(cx, ty)) return cx->thir->interner.t_error;
            for (const AxHirPat *p = pat->or_pat.pats; p; p = p->next) {
                check_pat(cx, p, ty, is_init);
            }
            break;
        }

        default:
            return type_error(cx, pat->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
    }
    AxPatTypeMap_insert(&cx->thir->pat_types, pat, ty);
    return ty;
}



static TypeId instantiate_path(TypeckCtx *cx, TypeId ty, const AxHirItem *it, const AxHirPath *path, AxGenericArgs *out_args) {
    if (TypeId_is_none(ty)) return ty;
    
    AxHirGenericParams *gps = NULL;
    if (it->kind == AX_HIR_ITEM_FN) gps = it->fn.generic_params;
    else if (it->kind == AX_HIR_ITEM_STRUCT) gps = it->struct_decl.generic_params;
    else if (it->kind == AX_HIR_ITEM_ENUM) gps = it->enum_decl.generic_params;
    
    size_t param_count = 0;
    if (gps) {
        for (AxHirGenericParam *p = gps->params; p; p = p->next) param_count++;
    }
    
    if (param_count == 0) return ty;
    
    AxGenericArgs gargs;
    gargs.count = param_count;
    gargs.args = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * param_count, _Alignof(TypeId));
    
    if (path->generic_args) {
        size_t arg_count = 0;
        for (AxHirGenericArg *a = path->generic_args->args; a; a = a->next) arg_count++;
        if (arg_count != param_count) {
            type_error(cx, path->span, AX_TYPE_ARG_COUNT);
            return cx->thir->interner.t_error;
        }
        size_t i = 0;
        for (AxHirGenericArg *a = path->generic_args->args; a; a = a->next) {
            gargs.args[i++] = hir_type_to_typeid(cx, a->type);
        }
    } else {
        for (size_t i = 0; i < param_count; i++) {
            gargs.args[i] = new_ty_var(cx, path->span);
        }
    }
    
    if (out_args) *out_args = gargs;
    return ax_subst_ty(cx, ty, &gargs);
}

static TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path, AxGenericArgs *out_args) {
    if (path->symbol.v != 0) {
        TypeId *t = AxSymbolTypeMap_get(&cx->thir->symbol_types, path->symbol);
        if (t) return *t;

        for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
            bool match = false;
            if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == path->symbol.v) match = true;
            else if (it->kind == AX_HIR_ITEM_STRUCT && it->struct_decl.symbol.v == path->symbol.v) match = true;
            else if (it->kind == AX_HIR_ITEM_ENUM) {
                if (it->enum_decl.symbol.v == path->symbol.v) match = true;
                else {
                    for (const AxHirVariantDecl *v = it->enum_decl.variants; v; v = v->next) {
                        if (v->symbol.v == path->symbol.v) {
                            match = true;
                            break;
                        }
                    }
                }
            }
            else if (it->kind == AX_HIR_ITEM_TYPE_ALIAS && it->type_alias.symbol.v == path->symbol.v) match = true;
            else if (it->kind == AX_HIR_ITEM_CONST && it->const_decl.symbol.v == path->symbol.v) match = true;

            if (match) {
                TypeId *it_t = AxItemTypeMap_get(&cx->thir->item_types, it);
                if (it_t) return instantiate_path(cx, *it_t, it, path, out_args);
            }
        }
        
        StrView name = ax_source_db_span_text(cx->db, path->span);
    if (name.len == 0 && path->name.v != 0) {
        name = ax_interner_get(cx->str_in, path->name);
    }
        if (ax_sv_eq_cstr(name, "Self")) {
            if (TypeId_is_some(cx->self_ty)) return cx->self_ty;
            AxType pt;
            memset(&pt, 0, sizeof(pt));
            pt.kind = AX_TY_PARAM;
            pt.param.name = ax_intern_cstr(cx->str_in, "Self");
            pt.param.index = 0;
            return ax_intern_type(&cx->thir->interner, &pt);
        }
        if (ax_sv_eq_cstr(name, "len")) {
            AxType st;
            memset(&st, 0, sizeof(st));
            st.kind = AX_TY_BUILTIN_LEN;
            return ax_intern_type(&cx->thir->interner, &st);
        }
        if (ax_sv_eq_cstr(name, "print")) {
            AxType st;
            memset(&st, 0, sizeof(st));
            st.kind = AX_TY_BUILTIN_PRINT;
            return ax_intern_type(&cx->thir->interner, &st);
        }
        if (ax_sv_eq_cstr(name, "print_int")) {
            AxType st;
            memset(&st, 0, sizeof(st));
            st.kind = AX_TY_BUILTIN_PRINT_INT;
            return ax_intern_type(&cx->thir->interner, &st);
        }
        if (ax_sv_eq_cstr(name, "drop")) {
            AxType st;
            memset(&st, 0, sizeof(st));
            st.kind = AX_TY_BUILTIN_DROP;
            return ax_intern_type(&cx->thir->interner, &st);
        }
    }
    StrView name = ax_source_db_span_text(cx->db, path->span);
    if (name.len == 0 && path->name.v != 0) {
        name = ax_interner_get(cx->str_in, path->name);
    }
    
    // Check built-in types for UFCS
    if (ax_sv_eq_cstr(name, "bool")) return cx->thir->interner.t_bool;
    if (ax_sv_eq_cstr(name, "char")) return cx->thir->interner.t_char;
    if (ax_sv_eq_cstr(name, "i8")) return cx->thir->interner.t_i8;
    if (ax_sv_eq_cstr(name, "i16")) return cx->thir->interner.t_i16;
    if (ax_sv_eq_cstr(name, "i32")) return cx->thir->interner.t_i32;
    if (ax_sv_eq_cstr(name, "i64")) return cx->thir->interner.t_i64;
    if (ax_sv_eq_cstr(name, "isize")) return cx->thir->interner.t_isize;
    if (ax_sv_eq_cstr(name, "u8")) return cx->thir->interner.t_u8;
    if (ax_sv_eq_cstr(name, "u16")) return cx->thir->interner.t_u16;
    if (ax_sv_eq_cstr(name, "u32")) return cx->thir->interner.t_u32;
    if (ax_sv_eq_cstr(name, "u64")) return cx->thir->interner.t_u64;
    if (ax_sv_eq_cstr(name, "usize")) return cx->thir->interner.t_usize;
    if (ax_sv_eq_cstr(name, "str")) return cx->thir->interner.t_str;

    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {

        if (it->kind == AX_HIR_ITEM_FN) {
            StrView it_name = ax_interner_get(cx->str_in, it->fn.name);
            if (ax_sv_eq(it_name, name)) {
                TypeId *t = AxItemTypeMap_get(&cx->thir->item_types, it);
                if (t) return instantiate_path(cx, *t, it, path, out_args);
            }
        } else if (it->kind == AX_HIR_ITEM_STRUCT) {
            StrView it_name = ax_interner_get(cx->str_in, it->struct_decl.name);
            StrView struct_name = name;
            const char *lt = memchr(name.ptr, '<', name.len);
            if (lt) struct_name.len = lt - name.ptr;
            if (ax_sv_eq(it_name, struct_name)) {
                TypeId *t = AxItemTypeMap_get(&cx->thir->item_types, it);
                if (t) return instantiate_path(cx, *t, it, path, out_args);
                return cx->thir->interner.t_error; // Being computed
            }
        } else if (it->kind == AX_HIR_ITEM_ENUM) {
            StrView enum_name = name;
            const char *dot = memchr(name.ptr, '.', name.len);
            const char *lt = memchr(name.ptr, '<', name.len);
            const char *end = name.ptr + name.len;
            if (dot && dot < end) end = dot;
            if (lt && lt < end) end = lt;
            enum_name.len = end - name.ptr;
            StrView it_name = ax_interner_get(cx->str_in, it->enum_decl.name);
            if (ax_sv_eq(it_name, enum_name)) {
                TypeId *t = AxItemTypeMap_get(&cx->thir->item_types, it);
                if (t) return instantiate_path(cx, *t, it, path, out_args);
            }
        }
    }
    
    if (cx->current_impl && cx->current_impl->kind == AX_HIR_ITEM_IMPL && cx->current_impl->impl.generic_params) {
        size_t idx = 0;
        for (AxHirGenericParam *gp = cx->current_impl->impl.generic_params->params; gp; gp = gp->next, idx++) {
            StrView gp_name = ax_interner_get(cx->str_in, gp->name);
            if (ax_sv_eq(gp_name, name)) {
                AxType pt;
                memset(&pt, 0, sizeof(pt));
                pt.kind = AX_TY_PARAM;
                pt.param.name = gp->name;
                pt.param.index = idx;
                return ax_intern_type(&cx->thir->interner, &pt);
            }
        }
    }
    if (cx->current_fn && cx->current_fn->kind == AX_HIR_ITEM_FN && cx->current_fn->fn.generic_params) {
        size_t idx = 0;
        for (AxHirGenericParam *gp = cx->current_fn->fn.generic_params->params; gp; gp = gp->next, idx++) {
            StrView gp_name = ax_interner_get(cx->str_in, gp->name);
            if (ax_sv_eq(gp_name, name)) {
                AxType pt;
                memset(&pt, 0, sizeof(pt));
                pt.kind = AX_TY_PARAM;
                pt.param.name = gp->name;
                pt.param.index = idx;
                return ax_intern_type(&cx->thir->interner, &pt);
            }
        }
    }

    AxDiagnostic d = {0};
    d.code = AX_NAME_UNRESOLVED;
    d.severity = AX_DIAG_ERROR;
    d.message = "unresolved name";
    d.primary = path->span;
    ax_diag_sink_report(cx->sink, &d);
    return cx->thir->interner.t_error;
}

static TypeId check_literal(TypeckCtx *cx, const AxHirExpr *expr) {
    switch (expr->literal.kind) {
        case AX_TOK_KW_TRUE:
        case AX_TOK_KW_FALSE:
            return cx->thir->interner.t_bool;
        case AX_TOK_CHAR:
            return cx->thir->interner.t_char;
        case AX_TOK_INT:
            return int_literal_type(cx, &expr->literal, expr->span, NULL);
        case AX_TOK_FLOAT:
            // AXS-SEM-010: float literals are rejected by axiom0 type checking.
            return type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
        case AX_TOK_STR:
        case AX_TOK_BYTE_STR:
            return cx->thir->interner.t_str;
        default:
            AX_ICE("typeck: literal with token kind %d", (int)expr->literal.kind);
    }
    return cx->thir->interner.t_error;
}

static TypeId check_binary(TypeckCtx *cx, const AxHirExpr *expr) {
    const TypeInterner *in = &cx->thir->interner;
    AxAstBinOp op = expr->binary.op;
    switch (op) {
        case AX_BINOP_LOGAND:
        case AX_BINOP_LOGOR:
            // AXS-SEM-036: both operands are bool.
            check_expr(cx, expr->binary.left, in->t_bool);
            check_expr(cx, expr->binary.right, in->t_bool);
            return in->t_bool;

        case AX_BINOP_SHL:
        case AX_BINOP_SHR: {
            // AXS-SEM-034: the amount has any integer type, independent of the value type.
            TypeId left_ty = check_expr(cx, expr->binary.left, TypeId_none());
            TypeId right_ty = check_expr(cx, expr->binary.right, TypeId_none());
            if (!is_error(cx, left_ty) && !is_intlike(cx, left_ty)) {
                return type_error(cx, expr->binary.left->span, AX_TYPE_OPERATOR);
            }
            if (!is_error(cx, right_ty) && !is_intlike(cx, right_ty)) {
                return type_error(cx, expr->binary.right->span, AX_TYPE_OPERATOR);
            }
            return left_ty;
        }

        case AX_BINOP_EQ: case AX_BINOP_NE:
        case AX_BINOP_LT: case AX_BINOP_LE: case AX_BINOP_GT: case AX_BINOP_GE:
        case AX_BINOP_ADD: case AX_BINOP_SUB: case AX_BINOP_MUL: case AX_BINOP_DIV: case AX_BINOP_REM:
        case AX_BINOP_BITAND: case AX_BINOP_BITOR: case AX_BINOP_BITXOR: {
            // AXS-SEM-022: both operands have the same type; a mismatch is reported once, at the
            // right operand (the coercion site).
            TypeId left_ty = check_expr(cx, expr->binary.left, TypeId_none());
            TypeId right_ty = check_expr(cx, expr->binary.right, left_ty);
            TypeId opnd = is_never(cx, left_ty) ? right_ty : left_ty;
            if (is_error(cx, opnd) || is_never(cx, opnd)) {
                bool cmp = op >= AX_BINOP_EQ && op <= AX_BINOP_GE;
                return cmp ? in->t_bool : opnd;
            }
            AxTypeKind k = kind_of(cx, opnd);
            bool ok;
            if (op >= AX_BINOP_EQ && op <= AX_BINOP_GE) {
                // AXS-SEM-035: integers, bool, char.
                ok = is_intlike(cx, opnd) || k == AX_TY_BOOL || k == AX_TY_CHAR;
            } else if (op == AX_BINOP_BITAND || op == AX_BINOP_BITOR || op == AX_BINOP_BITXOR) {
                // AXS-SEM-033: integers, or bool (non-short-circuit logic).
                ok = is_intlike(cx, opnd) || k == AX_TY_BOOL;
            } else {
                ok = is_intlike(cx, opnd);
            }
            
              if (!ok) {
                  const char *method_name = NULL;
                  bool is_cmp = false;
                  switch (op) {
                      case AX_BINOP_ADD: method_name = "add"; break;
                      case AX_BINOP_SUB: method_name = "sub"; break;
                      case AX_BINOP_MUL: method_name = "mul"; break;
                      case AX_BINOP_DIV: method_name = "div"; break;
                      case AX_BINOP_REM: method_name = "rem"; break;
                      case AX_BINOP_BITAND: method_name = "bitand"; break;
                      case AX_BINOP_BITOR: method_name = "bitor"; break;
                      case AX_BINOP_BITXOR: method_name = "bitxor"; break;
                      case AX_BINOP_SHL: method_name = "shl"; break;
                      case AX_BINOP_SHR: method_name = "shr"; break;
                      case AX_BINOP_EQ: method_name = "eq"; is_cmp = true; break;
                      case AX_BINOP_NE: method_name = "eq"; is_cmp = true; break;
                      case AX_BINOP_LT: method_name = "cmp"; is_cmp = true; break;
                      case AX_BINOP_LE: method_name = "cmp"; is_cmp = true; break;
                      case AX_BINOP_GT: method_name = "cmp"; is_cmp = true; break;
                      case AX_BINOP_GE: method_name = "cmp"; is_cmp = true; break;
                      default: break;
                  }
                  if (method_name) {
                      AxTraitResult trait_res = AX_TRAIT_DISPROVEN;
                      const AxHirItem *method_item = find_method(cx, left_ty, ax_sv_cstr(method_name), &trait_res);
                      if (method_item) {
                          AxExprMethodMap_insert(&cx->thir->expr_methods, expr, method_item);
                          TypeId *fn_ty_ptr = AxItemTypeMap_get(&cx->thir->item_types, method_item);
                          if (fn_ty_ptr) {
                              const AxType *fn_ty = ax_type_get(&cx->thir->interner, *fn_ty_ptr);
                              return is_cmp ? in->t_bool : fn_ty->fn.ret_type;
                          }
                      }
                  }
                  return type_error(cx, expr->span, AX_TYPE_OPERATOR);
              }

            if (op >= AX_BINOP_EQ && op <= AX_BINOP_GE) return in->t_bool;
            return opnd;
        }
        default:
            AX_ICE("typeck: unknown binary operator %d", (int)op);
    }
    return in->t_error;
}

static TypeId check_unary(TypeckCtx *cx, const AxHirExpr *expr) {
    const TypeInterner *in = &cx->thir->interner;
    const AxHirExpr *operand = expr->unary.expr;
    switch (expr->unary.op) {
        case AX_UNOP_NOT:
            // AXS-SEM-033: `!` applies to bool only.
            check_expr(cx, operand, in->t_bool);
            return in->t_bool;

        case AX_UNOP_NEG: {
            if (operand && operand->kind == AX_HIR_EXPR_LITERAL && operand->literal.kind == AX_TOK_INT) {
                // AXS-SEM-021: `-<literal>` is folded before the range check.
                size_t before = cx->lits_len;
                TypeId ty = check_expr(cx, operand, TypeId_none());
                if (cx->lits_len == before + 1) {
                    cx->lits[before].negated = true;
                    cx->lits[before].neg_span = expr->span;
                }
                return ty;
            }
            TypeId ty = check_expr(cx, operand, TypeId_none());
            TypeId r = resolve_ty(cx, ty);
            AxTypeKind k = kind_of(cx, r);
            if (k == AX_TY_ERROR || k == AX_TY_NEVER) return r;
            if (k == AX_TY_INT_VAR) {
                record_neg(cx, expr->span, r);
                return r;
            }
            if (ax_type_is_signed(r, in)) return r;
            if (ax_type_is_unsigned(r, in)) return type_error(cx, expr->span, AX_TYPE_NEG_UNSIGNED);
            return type_error(cx, expr->span, AX_TYPE_OPERATOR);
        }

        case AX_UNOP_BITNOT: {
            // AXS-SEM-033: `~x` inverts the bits of an integer.
            TypeId ty = check_expr(cx, operand, TypeId_none());
            if (is_error(cx, ty) || is_never(cx, ty) || is_intlike(cx, ty)) return resolve_ty(cx, ty);
            return type_error(cx, expr->span, AX_TYPE_OPERATOR);
        }

        case AX_UNOP_DEREF: {
            TypeId op = check_expr(cx, operand, TypeId_none());
            if (!is_error(cx, op)) {
                const AxType *t = ax_type_get(&cx->thir->interner, op);
                if (t->kind == AX_TY_PTR) return t->ptr.pointee;
                if (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) return t->view.pointee;
            }
            return type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
        }

        default:
            AX_ICE("typeck: unknown unary operator %d", (int)expr->unary.op);
    }
    return in->t_error;
}

static TypeId check_call(TypeckCtx *cx, const AxHirExpr *expr) {
    TypeId callee_ty;
    if (expr->call.callee->kind == AX_HIR_EXPR_PATH) {
        AxGenericArgs gargs = {0};
        callee_ty = resolve_ty(cx, lookup_path_type(cx, &expr->call.callee->path.path, &gargs));
        AxExprTypeMap_insert(&cx->thir->expr_types, expr->call.callee, callee_ty);
        if (gargs.count > 0) {
            AxExprSubstMap_insert(&cx->thir->expr_substs, expr->call.callee, gargs);
        }
        if (expr->call.callee->path.path.symbol.v != 0) {
            for (size_t i = 0; i < cx->vars_len; i++) {
                if (cx->vars[i].sym.v == expr->call.callee->path.path.symbol.v) {
                    break;
                }
            }
        }
    } else {
        callee_ty = resolve_ty(cx, check_expr(cx, expr->call.callee, TypeId_none()));
    }

    const AxType *ct = ax_type_get(&cx->thir->interner, callee_ty);
    
    if (ct->kind == AX_TY_BUILTIN_LEN) {
        // BOOTSTRAP-SHORTCUT T036 built-in len(a)
        size_t argc = 0;
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
        if (argc != 1) {
            return type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
        }
        TypeId arg_ty = resolve_ty(cx, check_expr(cx, expr->call.args, TypeId_none()));
        if (!is_error(cx, arg_ty)) {
            const AxType *t = ax_type_get(&cx->thir->interner, arg_ty);
            bool is_slice_view = (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) && ax_type_get(&cx->thir->interner, t->view.pointee)->kind == AX_TY_SLICE;
            if (t->kind != AX_TY_ARRAY && t->kind != AX_TY_STR && !is_slice_view) {
                type_error(cx, expr->call.args->span, AX_TYPE_MISMATCH); // Or maybe custom error
                return cx->thir->interner.t_error;
            }
        }
        return cx->thir->interner.t_usize;
    }
    if (ct->kind == AX_TY_BUILTIN_PRINT) {
        size_t argc = 0;
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
        if (argc != 1) return type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
        TypeId arg_ty = resolve_ty(cx, check_expr(cx, expr->call.args, TypeId_none()));
        if (!is_error(cx, arg_ty)) {
            if (!TypeId_eq(arg_ty, cx->thir->interner.t_str)) {
                type_error(cx, expr->call.args->span, AX_TYPE_MISMATCH);
                return cx->thir->interner.t_error;
            }
        }
        return cx->thir->interner.t_unit;
    }
    if (ct->kind == AX_TY_BUILTIN_PRINT_INT) {
        size_t argc = 0;
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
        if (argc != 1) return type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
        TypeId arg_ty = resolve_ty(cx, check_expr(cx, expr->call.args, TypeId_none()));
        if (!is_error(cx, arg_ty)) {
            if (!ax_type_is_int(arg_ty, &cx->thir->interner)) {
                type_error(cx, expr->call.args->span, AX_TYPE_MISMATCH);
                return cx->thir->interner.t_error;
            }
        }
        return cx->thir->interner.t_unit;
    }
    if (ct->kind == AX_TY_BUILTIN_DROP) {
        size_t argc = 0;
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
        if (argc != 1) return type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
        resolve_ty(cx, check_expr(cx, expr->call.args, TypeId_none()));
        return cx->thir->interner.t_unit;
    }
    
    if (ct->kind == AX_TY_CLOSURE) {
        size_t argc = 0;
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
        if (argc != ct->closure.param_count) {
            for (const AxHirExpr *a = expr->call.args; a; a = a->next) check_expr(cx, a, TypeId_none());
            return type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
        }
        TypeId ret = ct->closure.ret_type;
        const TypeId *params = ct->closure.params;
        size_t i = 0;
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) {
            check_expr(cx, a, params[i++]);
        }
        return TypeId_is_none(ret) ? cx->thir->interner.t_unit : ret;
    }
    
    if (ct->kind == AX_TY_PARAM) {
        bool is_callable_param = false;
        if (cx->current_fn && cx->current_fn->fn.generic_params) {
            size_t idx = 0;
            for (AxHirGenericParam *gp = cx->current_fn->fn.generic_params->params; gp; gp = gp->next, idx++) {
                if (idx == ct->param.index || (gp->name.v != 0 && gp->name.v == ct->param.name.v)) {
                    for (AxHirType *b = gp->bounds; b; b = b->next) {
                        StrView bname = (b->path.path.name.v != 0) ? ax_interner_get(cx->str_in, b->path.path.name) : (StrView){0};
                        if (ax_sv_eq_cstr(bname, "Fn") || ax_sv_eq_cstr(bname, "FnMut") ||
                            ax_sv_eq_cstr(bname, "FnOnce") || ax_sv_eq_cstr(bname, "Callable")) {
                            is_callable_param = true;
                            break;
                        }
                    }
                    break;
                }
            }
        }
        if (is_callable_param) {
            for (const AxHirExpr *a = expr->call.args; a; a = a->next) check_expr(cx, a, TypeId_none());
            return cx->return_type.v != 0 ? cx->return_type : cx->thir->interner.t_i32;
        }
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) check_expr(cx, a, TypeId_none());
        return type_error(cx, expr->call.callee->span, AX_TYPE_NOT_CALLABLE);
    }

    if (ct->kind != AX_TY_FN) {
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) check_expr(cx, a, TypeId_none());
        if (ct->kind == AX_TY_ERROR) return cx->thir->interner.t_error;
        return type_error(cx, expr->call.callee->span, AX_TYPE_NOT_CALLABLE);
    }
    size_t argc = 0;
    for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
    if (argc != ct->fn.param_count) {
        for (const AxHirExpr *a = expr->call.args; a; a = a->next) check_expr(cx, a, TypeId_none());
        return type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
    }
    // The interner may grow while arguments are checked: copy what is needed first.
    TypeId ret = ct->fn.ret_type;
    const TypeId *params = ct->fn.param_types;
    size_t i = 0;
    for (const AxHirExpr *a = expr->call.args; a; a = a->next) {
        check_expr(cx, a, params[i++]); // the argument is the coercion site (AXS-SEM-022)
    }
    return TypeId_is_none(ret) ? cx->thir->interner.t_unit : ret;
}


static void desugar_if_let(TypeckCtx *cx, AxHirExpr *expr) {
    if (!expr->if_expr.let_pat) return;
    
    AxHirMatchArm *arm_else = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirMatchArm), _Alignof(AxHirMatchArm));
    arm_else->span = expr->span;
    AxHirPat *wild = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirPat), _Alignof(AxHirPat));
    wild->kind = AX_HIR_PAT_WILDCARD;
    wild->span = expr->span;
    wild->next = NULL;
    arm_else->pat = wild;
    
    AxHirExpr *else_blk;
    if (expr->if_expr.else_branch) {
        else_blk = expr->if_expr.else_branch;
    } else {
        else_blk = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
        else_blk->kind = AX_HIR_EXPR_BLOCK;
        else_blk->span = expr->span;
        else_blk->next = NULL;
        else_blk->block.block.span = expr->span;
        else_blk->block.block.stmts = NULL;
    }
    arm_else->body = else_blk;
    arm_else->guard = NULL;
    arm_else->next = NULL;
    
    AxHirMatchArm *arm_then = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirMatchArm), _Alignof(AxHirMatchArm));
    arm_then->span = expr->if_expr.block.span;
    arm_then->pat = expr->if_expr.let_pat;
    AxHirExpr *then_blk = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    then_blk->kind = AX_HIR_EXPR_BLOCK;
    then_blk->span = expr->if_expr.block.span;
    then_blk->next = NULL;
    then_blk->block.block = expr->if_expr.block;
    arm_then->body = then_blk;
    arm_then->guard = NULL;
    arm_then->next = arm_else;
    
    AxHirExpr *cond = expr->if_expr.cond;
    expr->kind = AX_HIR_EXPR_MATCH;
    expr->match.expr = cond;
    expr->match.arms = arm_then;
}

static void desugar_while_let(TypeckCtx *cx, AxHirExpr *expr) {
    if (!expr->while_expr.let_pat) return;
    
    AxHirExpr *brk_expr = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    brk_expr->kind = AX_HIR_EXPR_JUMP;
    brk_expr->span = expr->span;
    brk_expr->next = NULL;
    brk_expr->jump.jump_kind = AX_JUMP_BREAK;
    brk_expr->jump.label = (StrId){0}; 
    brk_expr->jump.expr = NULL;

    AxHirMatchArm *arm_else = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirMatchArm), _Alignof(AxHirMatchArm));
    arm_else->span = expr->span;
    AxHirPat *wild = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirPat), _Alignof(AxHirPat));
    wild->kind = AX_HIR_PAT_WILDCARD;
    wild->span = expr->span;
    wild->next = NULL;
    arm_else->pat = wild;
    arm_else->body = brk_expr;
    arm_else->guard = NULL;
    arm_else->next = NULL;
    
    AxHirMatchArm *arm_then = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirMatchArm), _Alignof(AxHirMatchArm));
    arm_then->span = expr->while_expr.block.span;
    arm_then->pat = expr->while_expr.let_pat;
    AxHirExpr *then_blk = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    then_blk->kind = AX_HIR_EXPR_BLOCK;
    then_blk->span = expr->while_expr.block.span;
    then_blk->next = NULL;
    then_blk->block.block = expr->while_expr.block;
    arm_then->body = then_blk;
    arm_then->guard = NULL;
    arm_then->next = arm_else;
    
    AxHirExpr *match_expr = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    match_expr->kind = AX_HIR_EXPR_MATCH;
    match_expr->span = expr->span;
    match_expr->next = NULL;
    match_expr->match.expr = expr->while_expr.cond;
    match_expr->match.arms = arm_then;
    
    AxHirStmt *match_stmt = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirStmt), _Alignof(AxHirStmt));
    match_stmt->kind = AX_HIR_STMT_EXPR;
    match_stmt->span = expr->span;
    match_stmt->next = NULL;
    match_stmt->expr_stmt.expr = match_expr;
    match_stmt->expr_stmt.has_semi = false;
    
    StrId lbl = expr->while_expr.label;
    expr->kind = AX_HIR_EXPR_LOOP;
    expr->loop.label = lbl;
    expr->loop.block.span = expr->span;
    expr->loop.block.stmts = match_stmt;
}

static TypeId check_if(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected) {
    if (expr->if_expr.let_pat) {
        desugar_if_let(cx, (AxHirExpr*)expr);
        return check_expr_kind(cx, expr, expected);
    }
    const TypeInterner *in = &cx->thir->interner;
    if (expr->if_expr.let_pat) {
        TypeId cond_ty = check_expr(cx, expr->if_expr.cond, TypeId_none());
        check_pat(cx, expr->if_expr.let_pat, cond_ty, true);
    } else {
        check_expr(cx, expr->if_expr.cond, in->t_bool); // AXS-SEM-012: the condition is bool
    }
    if (!expr->if_expr.else_branch) {
        // Without else the value is (); the enclosing coercion reports a non-unit expectation.
        check_block(cx, &expr->if_expr.block, in->t_unit);
        return in->t_unit;
    }
    TypeId then_ty = check_block(cx, &expr->if_expr.block, expected);
    TypeId else_ty = check_expr(cx, expr->if_expr.else_branch, TypeId_is_some(expected) ? expected : then_ty);
    if (is_never(cx, then_ty)) return else_ty;
    if (is_error(cx, else_ty)) return else_ty;
    return resolve_ty(cx, then_ty);
}

typedef struct {
    AxSymbolId sym;
    bool is_mutated;
    bool is_moved;
    bool is_read;
} RawCapture;

static void record_cap(RawCapture *caps, size_t *cap_count, AxSymbolId sym, bool is_mut, bool is_move) {
    for (size_t i = 0; i < *cap_count; i++) {
        if (caps[i].sym.v == sym.v) {
            if (is_move) caps[i].is_moved = true;
            else if (is_mut) caps[i].is_mutated = true;
            else caps[i].is_read = true;
            return;
        }
    }
    if (*cap_count < 64) {
        caps[*cap_count].sym = sym;
        caps[*cap_count].is_mutated = is_mut;
        caps[*cap_count].is_moved = is_move;
        caps[*cap_count].is_read = !is_mut && !is_move;
        (*cap_count)++;
    }
}

static bool is_inner_sym(AxSymbolId sym, const AxSymbolId *inner, size_t inner_count) {
    for (size_t i = 0; i < inner_count; i++) {
        if (inner[i].v == sym.v) return true;
    }
    return false;
}

static bool is_outer_var(TypeckCtx *cx, AxSymbolId sym) {
    for (size_t i = 0; i < cx->vars_len; i++) {
        if (cx->vars[i].sym.v == sym.v) return true;
    }
    return false;
}

static void add_pat_syms(const AxHirPat *pat, AxSymbolId *inner, size_t *inner_count) {
    if (!pat) return;
    if (pat->kind == AX_HIR_PAT_BINDING) {
        if (*inner_count < 128) inner[(*inner_count)++] = pat->binding.symbol;
    } else if (pat->kind == AX_HIR_PAT_TUPLE) {
        for (const AxHirPat *p = pat->tuple.elems; p; p = p->next) add_pat_syms(p, inner, inner_count);
    } else if (pat->kind == AX_HIR_PAT_STRUCT) {
        for (const AxHirPatField *f = pat->struct_pat.fields; f; f = f->next) add_pat_syms(f->pat, inner, inner_count);
    }
}

static void scan_expr_captures(TypeckCtx *cx, const AxHirExpr *expr, AxSymbolId *inner, size_t *inner_count,
                               RawCapture *caps, size_t *cap_count, bool in_mut, bool in_move);

static void scan_block_captures(TypeckCtx *cx, const AxHirBlock *block, AxSymbolId *inner, size_t *inner_count,
                                RawCapture *caps, size_t *cap_count) {
    if (!block) return;
    size_t save_inner = *inner_count;
    for (const AxHirStmt *s = block->stmts; s; s = s->next) {
        if (s->kind == AX_HIR_STMT_LET) {
            if (s->let.expr) scan_expr_captures(cx, s->let.expr, inner, inner_count, caps, cap_count, false, false);
            if (s->let.else_block) scan_block_captures(cx, s->let.else_block, inner, inner_count, caps, cap_count);
            add_pat_syms(s->let.pat, inner, inner_count);
        } else if (s->kind == AX_HIR_STMT_ASSIGN) {
            scan_expr_captures(cx, s->assign.left, inner, inner_count, caps, cap_count, true, false);
            scan_expr_captures(cx, s->assign.right, inner, inner_count, caps, cap_count, false, false);
        } else if (s->kind == AX_HIR_STMT_EXPR) {
            scan_expr_captures(cx, s->expr_stmt.expr, inner, inner_count, caps, cap_count, false, false);
        }
    }
    *inner_count = save_inner;
}

static void scan_expr_captures(TypeckCtx *cx, const AxHirExpr *expr, AxSymbolId *inner, size_t *inner_count,
                               RawCapture *caps, size_t *cap_count, bool in_mut, bool in_move) {
    if (!expr) return;
    switch (expr->kind) {
        case AX_HIR_EXPR_PATH:
            if (expr->path.path.symbol.v != 0) {
                AxSymbolId sym = expr->path.path.symbol;
                if (!is_inner_sym(sym, inner, *inner_count) && is_outer_var(cx, sym)) {
                    record_cap(caps, cap_count, sym, in_mut, in_move);
                }
            }
            break;
        case AX_HIR_EXPR_BINARY:
            scan_expr_captures(cx, expr->binary.left, inner, inner_count, caps, cap_count, false, false);
            scan_expr_captures(cx, expr->binary.right, inner, inner_count, caps, cap_count, false, false);
            break;
        case AX_HIR_EXPR_UNARY:
            scan_expr_captures(cx, expr->unary.expr, inner, inner_count, caps, cap_count, false, false);
            break;
        case AX_HIR_EXPR_CAST:
            scan_expr_captures(cx, expr->cast.expr, inner, inner_count, caps, cap_count, false, false);
            break;
        case AX_HIR_EXPR_VIEW:
            scan_expr_captures(cx, expr->view.expr, inner, inner_count, caps, cap_count, expr->view.is_mut, false);
            break;
        case AX_HIR_EXPR_BLOCK:
            scan_block_captures(cx, &expr->block.block, inner, inner_count, caps, cap_count);
            break;
        case AX_HIR_EXPR_IF:
            scan_expr_captures(cx, expr->if_expr.cond, inner, inner_count, caps, cap_count, false, false);
            scan_block_captures(cx, &expr->if_expr.block, inner, inner_count, caps, cap_count);
            if (expr->if_expr.else_branch) scan_expr_captures(cx, expr->if_expr.else_branch, inner, inner_count, caps, cap_count, false, false);
            break;
        case AX_HIR_EXPR_WHILE:
            scan_expr_captures(cx, expr->while_expr.cond, inner, inner_count, caps, cap_count, false, false);
            scan_block_captures(cx, &expr->while_expr.block, inner, inner_count, caps, cap_count);
            break;
        case AX_HIR_EXPR_MATCH: {
            scan_expr_captures(cx, expr->match.expr, inner, inner_count, caps, cap_count, false, false);
            for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
                size_t save = *inner_count;
                add_pat_syms(arm->pat, inner, inner_count);
                if (arm->guard) scan_expr_captures(cx, arm->guard, inner, inner_count, caps, cap_count, false, false);
                scan_expr_captures(cx, arm->body, inner, inner_count, caps, cap_count, false, false);
                *inner_count = save;
            }
            break;
        }
        case AX_HIR_EXPR_CALL: {
            bool is_drop = false;
            if (expr->call.callee->kind == AX_HIR_EXPR_PATH) {
                TypeId cty = lookup_path_type(cx, &expr->call.callee->path.path, NULL);
                if (!TypeId_is_none(cty)) {
                    const AxType *ct = ax_type_get(&cx->thir->interner, cty);
                    if (ct && ct->kind == AX_TY_BUILTIN_DROP) is_drop = true;
                }
            }
            scan_expr_captures(cx, expr->call.callee, inner, inner_count, caps, cap_count, false, false);
            for (const AxHirExpr *a = expr->call.args; a; a = a->next) {
                bool arg_move = is_drop;
                if (!arg_move && a->kind == AX_HIR_EXPR_PATH && a->path.path.symbol.v != 0) {
                    const TypeId *vty = AxSymbolTypeMap_get(&cx->thir->symbol_types, a->path.path.symbol);
                    if (vty && !ax_type_is_copy(*vty, cx->thir, cx->str_in)) {
                        arg_move = true;
                    }
                }
                scan_expr_captures(cx, a, inner, inner_count, caps, cap_count, false, arg_move);
            }
            break;
        }
        case AX_HIR_EXPR_METHOD_CALL:
            scan_expr_captures(cx, expr->method_call.receiver, inner, inner_count, caps, cap_count, false, false);
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                scan_expr_captures(cx, a, inner, inner_count, caps, cap_count, false, false);
            }
            break;
        case AX_HIR_EXPR_FIELD:
            scan_expr_captures(cx, expr->field.base, inner, inner_count, caps, cap_count, in_mut, in_move);
            break;
        case AX_HIR_EXPR_TUPLE_INDEX:
            scan_expr_captures(cx, expr->tuple_index.base, inner, inner_count, caps, cap_count, in_mut, in_move);
            break;
        case AX_HIR_EXPR_INDEX:
            scan_expr_captures(cx, expr->index.base, inner, inner_count, caps, cap_count, in_mut, false);
            scan_expr_captures(cx, expr->index.arg, inner, inner_count, caps, cap_count, false, false);
            break;
        case AX_HIR_EXPR_TUPLE:
            for (const AxHirExpr *e = expr->tuple.elems; e; e = e->next) {
                scan_expr_captures(cx, e, inner, inner_count, caps, cap_count, false, false);
            }
            break;
        case AX_HIR_EXPR_ARRAY:
            for (const AxHirExpr *e = expr->array.elems; e; e = e->next) {
                scan_expr_captures(cx, e, inner, inner_count, caps, cap_count, false, false);
            }
            if (expr->array.count) scan_expr_captures(cx, expr->array.count, inner, inner_count, caps, cap_count, false, false);
            break;
        case AX_HIR_EXPR_STRUCT:
            for (const AxHirFieldInit *f = expr->struct_lit.fields; f; f = f->next) {
                scan_expr_captures(cx, f->expr, inner, inner_count, caps, cap_count, false, false);
            }
            break;
        case AX_HIR_EXPR_JUMP:
            if (expr->jump.expr) scan_expr_captures(cx, expr->jump.expr, inner, inner_count, caps, cap_count, false, false);
            break;
        default: break;
    }
}

/* Computes the type of `expr`; `expected` is only a hint for sub-expressions that carry it on
 * (blocks, if branches). Every case reports its own errors and returns t_error after one. */
static TypeId check_expr_kind(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected) {
    const TypeInterner *in = &cx->thir->interner;
    switch (expr->kind) {
        case AX_HIR_EXPR_ERROR:
            return in->t_error;
        case AX_HIR_EXPR_LITERAL:
            return check_literal(cx, expr);
        case AX_HIR_EXPR_TUPLE: {
            size_t count = 0;
            for (AxHirExpr *e = expr->tuple.elems; e; e = e->next) count++;
            TypeId *fields = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * count, _Alignof(TypeId));
            size_t i = 0;
            
            const AxType *exp_t = NULL;
            if (TypeId_is_some(expected)) {
                exp_t = ax_type_get(&cx->thir->interner, resolve_ty(cx, expected));
                if (exp_t->kind != AX_TY_TUPLE || exp_t->tuple.field_count != count) {
                    exp_t = NULL;
                }
            }

            for (AxHirExpr *e = expr->tuple.elems; e; e = e->next) {
                TypeId exp_elem = exp_t ? exp_t->tuple.fields[i] : TypeId_none();
                fields[i++] = check_expr(cx, e, exp_elem);
            }
            AxType t = { .kind = AX_TY_TUPLE, .tuple = { .field_count = count, .fields = fields } };
            return ax_intern_type(&cx->thir->interner, &t);
        }

        case AX_HIR_EXPR_STRUCT: {
            AxGenericArgs gargs = {0};
            TypeId path_ty = lookup_path_type(cx, &expr->struct_lit.path, &gargs);
            if (gargs.count > 0) {
                AxExprSubstMap_insert(&cx->thir->expr_substs, expr, gargs);
            }
            if (!is_error(cx, path_ty)) {
                const AxType *t = ax_type_get(&cx->thir->interner, path_ty);
                if (t->kind == AX_TY_ENUM) {
                    StrView name = ax_source_db_span_text(cx->db, expr->struct_lit.path.span);
                    StrView vname = name;
                    const char *dot = memchr(name.ptr, '.', name.len);
                    if (dot) {
                        vname.ptr = dot + 1;
                        vname.len = name.len - (dot - name.ptr) - 1;
                    }
                    bool found_variant = false;
                    size_t vidx = 0;
                    for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                        StrView var_name = ax_interner_get(cx->str_in, v->name);
                        if (ax_sv_eq(var_name, vname)) {
                            found_variant = true;
                            AxExprVariantMap_insert(&cx->thir->expr_variants, expr, vidx);
                            if (!v->is_struct) return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                            
                            // check duplicate fields
                            for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                                StrView iname = ax_interner_get(cx->str_in, init->name);
                                for (const AxHirFieldInit *other = init->next; other; other = other->next) {
                                    StrView oname = ax_interner_get(cx->str_in, other->name);
                                    if (ax_sv_eq(iname, oname)) {
                                        type_error(cx, other->span, AX_TYPE_DUPLICATE_FIELD);
                                    }
                                }
                            }

                            // check fields
                            for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                                StrView iname = ax_interner_get(cx->str_in, init->name);
                                bool found = false;
                                size_t idx = 0;
                                for (const AxHirFieldDecl *f = v->struct_fields; f; f = f->next) {
                                    StrView fname = ax_interner_get(cx->str_in, f->name);
                                    if (ax_sv_eq(fname, iname)) {
                                        found = true;
                                        check_expr(cx, init->expr, t->enm.variant_fields[vidx][idx]);
                                        break;
                                    }
                                    idx++;
                                }
                                if (!found) {
                                    type_error(cx, init->span, AX_TYPE_UNKNOWN_FIELD);
                                }
                            }
                            // check missing
                            for (const AxHirFieldDecl *f = v->struct_fields; f; f = f->next) {
                                StrView fname = ax_interner_get(cx->str_in, f->name);
                                bool found = false;
                                for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                                    StrView iname = ax_interner_get(cx->str_in, init->name);
                                    if (ax_sv_eq(fname, iname)) found = true;
                                }
                                if (!found) {
                                    type_error(cx, expr->span, AX_TYPE_MISSING_FIELD);
                                }
                            }
                            break;
                        }
                        vidx++;
                    }
                    if (!found_variant) return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                } else if (t->kind != AX_TY_STRUCT) {
                    return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                } else {
                
                // check duplicate fields
                for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                    StrView iname = ax_interner_get(cx->str_in, init->name);
                    for (const AxHirFieldInit *other = init->next; other; other = other->next) {
                        StrView oname = ax_interner_get(cx->str_in, other->name);
                        if (ax_sv_eq(iname, oname)) {
                            type_error(cx, other->span, AX_TYPE_DUPLICATE_FIELD);
                        }
                    }
                }

                // check fields
                for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                    StrView iname = ax_interner_get(cx->str_in, init->name);
                    bool found = false;
                    size_t idx = 0;
                    for (const AxHirFieldDecl *f = t->strct.def->struct_decl.struct_fields; f; f = f->next) {
                        StrView fname = ax_interner_get(cx->str_in, f->name);
                        if (ax_sv_eq(fname, iname)) {
                            found = true;
                            if (f->vis.kind == AX_HIR_VIS_PRIVATE || f->vis.kind == AX_HIR_VIS_PUB_MODULE) {
                                if (cx->current_fn && t->strct.def) {
                                    if (!dotted_name_eq(&cx->current_fn->module_path, &t->strct.def->module_path)) {
                                        type_error(cx, init->span, AX_NAME_PRIVATE);
                                    }
                                }
                            } else if (f->vis.kind == AX_HIR_VIS_PUB_PACKAGE) {
                                if (cx->current_fn && t->strct.def) {
                                    bool diff = false;
                                    if (cx->current_fn->module_path.count == 0 || t->strct.def->module_path.count == 0) {
                                        diff = (cx->current_fn->module_path.count != t->strct.def->module_path.count);
                                    } else if (cx->current_fn->module_path.segments[0].v != t->strct.def->module_path.segments[0].v) {
                                        diff = true;
                                    }
                                    if (diff) {
                                        type_error(cx, init->span, AX_NAME_PRIVATE);
                                    }
                                }
                            }
                            check_expr(cx, init->expr, t->strct.fields[idx]);
                            break;
                        }
                        idx++;
                    }
                    if (!found) {
                        type_error(cx, init->span, AX_TYPE_UNKNOWN_FIELD);
                    }
                }
                // check missing
                for (const AxHirFieldDecl *f = t->strct.def->struct_decl.struct_fields; f; f = f->next) {
                    StrView fname = ax_interner_get(cx->str_in, f->name);
                    bool found = false;
                    for (const AxHirFieldInit *init = expr->struct_lit.fields; init; init = init->next) {
                        StrView iname = ax_interner_get(cx->str_in, init->name);
                        if (ax_sv_eq(fname, iname)) found = true;
                    }
                    if (!found) {
                        type_error(cx, expr->span, AX_TYPE_MISSING_FIELD);
                    }
                }
                } // close else { t->kind == AX_TY_STRUCT }
            }
            return path_ty;
        }
        case AX_HIR_EXPR_FIELD: {
            TypeId obj_ty = check_expr(cx, expr->field.base, TypeId_none());
            if (!is_error(cx, obj_ty)) {
                TypeId base_ty = obj_ty;
                const AxType *t = ax_type_get(&cx->thir->interner, base_ty);
                while (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW || t->kind == AX_TY_PTR) {
                    base_ty = (t->kind == AX_TY_PTR) ? t->ptr.pointee : t->view.pointee;
                    t = ax_type_get(&cx->thir->interner, base_ty);
                }
                if (t->kind == AX_TY_STRUCT) {
                    bool found = false;
                    size_t idx = 0;
                    for (const AxHirFieldDecl *f = t->strct.def->struct_decl.struct_fields; f; f = f->next) {
                        StrView fname = ax_interner_get(cx->str_in, f->name);
                        StrView search = ax_interner_get(cx->str_in, expr->field.name);
                        if (ax_sv_eq(fname, search)) {
                            found = true;
                            if (f->vis.kind == AX_HIR_VIS_PRIVATE || f->vis.kind == AX_HIR_VIS_PUB_MODULE) {
                                if (cx->current_fn && t->strct.def) {
                                    if (!dotted_name_eq(&cx->current_fn->module_path, &t->strct.def->module_path)) {
                                        return type_error(cx, expr->span, AX_NAME_PRIVATE);
                                    }
                                }
                            } else if (f->vis.kind == AX_HIR_VIS_PUB_PACKAGE) {
                                if (cx->current_fn && t->strct.def) {
                                    bool diff = false;
                                    if (cx->current_fn->module_path.count == 0 || t->strct.def->module_path.count == 0) {
                                        diff = (cx->current_fn->module_path.count != t->strct.def->module_path.count);
                                    } else if (cx->current_fn->module_path.segments[0].v != t->strct.def->module_path.segments[0].v) {
                                        diff = true;
                                    }
                                    if (diff) {
                                        return type_error(cx, expr->span, AX_NAME_PRIVATE);
                                    }
                                }
                            }
                            return t->strct.fields[idx];
                        }
                        idx++;
                    }
                    if (!found) {
                        StrView search = ax_interner_get(cx->str_in, expr->field.name);
                        for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
                            if (it->kind == AX_HIR_ITEM_IMPL && it->impl.self_type) {
                                const AxHirItem *old_impl = cx->current_impl;
                                cx->current_impl = it;
                                TypeId impl_self_ty = hir_type_to_typeid(cx, it->impl.self_type);
                                cx->current_impl = old_impl;
                                if (unify_ty(cx, impl_self_ty, base_ty)) {
                                    for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                                        if (m->kind == AX_HIR_ITEM_CONST) {
                                            StrView cname = ax_interner_get(cx->str_in, m->const_decl.name);
                                            if (ax_sv_eq(cname, search)) {
                                                AxExprMethodMap_insert(&cx->thir->expr_methods, expr, m);
                                                TypeId *cty = AxItemTypeMap_get(&cx->thir->item_types, m);
                                                return cty ? *cty : in->t_i32;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                    }
                } else if (t->kind == AX_TY_PARAM) {
                    StrView search = ax_interner_get(cx->str_in, expr->field.name);
                    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
                        if (it->kind == AX_HIR_ITEM_TRAIT) {
                            for (const AxHirItem *m = it->trait.members; m; m = m->next) {
                                if (m->kind == AX_HIR_ITEM_CONST) {
                                    StrView cname = ax_interner_get(cx->str_in, m->const_decl.name);
                                    if (ax_sv_eq(cname, search)) {
                                        AxExprMethodMap_insert(&cx->thir->expr_methods, expr, m);
                                        TypeId *cty = AxItemTypeMap_get(&cx->thir->item_types, m);
                                        return cty ? *cty : in->t_i32;
                                    }
                                }
                            }
                        }
                    }
                    return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                } else if (t->kind == AX_TY_ENUM) {
                    bool found = false;
                    size_t vidx = 0;
                    for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                        StrView vname = ax_interner_get(cx->str_in, v->name); 
                        StrView search = ax_interner_get(cx->str_in, expr->field.name); 
                        if (ax_sv_eq(vname, search)) {
                            AxExprVariantMap_insert(&cx->thir->expr_variants, expr, vidx);
                            found = true;
                            if (v->is_struct || t->enm.variant_field_counts[vidx] > 0) {
                                return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                            }
                            return obj_ty;
                        }
                        vidx++;
                    }
                    if (!found) {
                        return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                    }
                    return obj_ty;
                } else {
                    return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                }
            }
            return cx->thir->interner.t_error;
        }
        case AX_HIR_EXPR_TUPLE_INDEX: {
            TypeId obj_ty = check_expr(cx, expr->tuple_index.base, TypeId_none());
            if (!is_error(cx, obj_ty)) {
                const AxType *t = ax_type_get(&cx->thir->interner, obj_ty);
                if (t->kind == AX_TY_STRUCT && t->strct.def->struct_decl.is_tuple) {
                    if (expr->tuple_index.tuple_index < t->strct.field_count) {
                        return t->strct.fields[expr->tuple_index.tuple_index];
                    }
                    return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                } else if (t->kind == AX_TY_TUPLE) {
                    if (expr->tuple_index.tuple_index < t->tuple.field_count) {
                        return t->tuple.fields[expr->tuple_index.tuple_index];
                    }
                    return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                } else {
                    return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
                }
            }
            return cx->thir->interner.t_error;
        }

        case AX_HIR_EXPR_PATH: {
            
            AxGenericArgs gargs = {0};
            TypeId t = lookup_path_type(cx, &expr->path.path, &gargs);
            if (gargs.count > 0) {
                AxExprSubstMap_insert(&cx->thir->expr_substs, expr, gargs);
            }

            if (expr->path.path.symbol.v != 0) {
                for (size_t i = 0; i < cx->vars_len; i++) {
                    if (cx->vars[i].sym.v == expr->path.path.symbol.v) {
                        break;
                    }
                }
            }
            if (!is_error(cx, t)) {
                AxTypeKind k = ax_type_get(&cx->thir->interner, resolve_ty(cx, t))->kind;
                if (k == AX_TY_BUILTIN_DROP || k == AX_TY_BUILTIN_LEN || k == AX_TY_BUILTIN_PRINT || k == AX_TY_BUILTIN_PRINT_INT) {
                    return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
            }
            return t;
        }
        case AX_HIR_EXPR_BLOCK:
            return check_block(cx, &expr->block.block, expected);
        case AX_HIR_EXPR_IF:
            return check_if(cx, expr, expected);
                case AX_HIR_EXPR_LOOP: {
            bool old_loop = cx->in_loop;
            cx->in_loop = true;
            if (cx->loops_len == cx->loops_cap) {
                cx->loops = ax_grow_array(cx->loops, &cx->loops_cap, sizeof(LoopEnv), cx->loops_len + 1);
            }
            cx->loops[cx->loops_len].label = expr->loop.label;
            cx->loops[cx->loops_len].break_ty = TypeId_none();
            cx->loops[cx->loops_len].has_break = false;
            cx->loops_len++;
            
            check_block(cx, &expr->loop.block, in->t_unit);
            
            cx->loops_len--;
            cx->in_loop = old_loop;
            
            if (cx->loops[cx->loops_len].has_break) {
                return cx->loops[cx->loops_len].break_ty;
            }
            return in->t_never;
        }
                case AX_HIR_EXPR_WHILE: {
            bool old_loop = cx->in_loop;
            cx->in_loop = true;
            if (cx->loops_len == cx->loops_cap) {
                cx->loops = ax_grow_array(cx->loops, &cx->loops_cap, sizeof(LoopEnv), cx->loops_len + 1);
            }
            cx->loops[cx->loops_len].label = expr->while_expr.label;
            cx->loops[cx->loops_len].break_ty = in->t_unit; // Cannot break with value from while
            cx->loops[cx->loops_len].has_break = false;
            cx->loops_len++;
            if (expr->while_expr.let_pat) {
                desugar_while_let(cx, (AxHirExpr*)expr);
                cx->loops_len--;
                cx->in_loop = old_loop;
                return check_expr_kind(cx, expr, expected);
            } else {
                check_expr(cx, expr->while_expr.cond, in->t_bool);
            }

            check_block(cx, &expr->while_expr.block, in->t_unit);
            
            cx->loops_len--;
            cx->in_loop = old_loop;
            return in->t_unit;
        }
                case AX_HIR_EXPR_JUMP:
            if (expr->jump.jump_kind == AX_JUMP_RETURN) {
                TypeId ret = TypeId_is_none(cx->return_type) ? in->t_unit : cx->return_type;
                if (expr->jump.expr) {
                    check_expr(cx, expr->jump.expr, ret);
                } else if (!unify_ty(cx, in->t_unit, ret)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
            } else if (expr->jump.jump_kind == AX_JUMP_BREAK) {
                LoopEnv *target = NULL;
                if (expr->jump.label.v != 0) {
                    for (size_t i = cx->loops_len; i > 0; i--) {
                        if (cx->loops[i-1].label.v == expr->jump.label.v) {
                            target = &cx->loops[i-1];
                            break;
                        }
                    }
                } else if (cx->loops_len > 0) {
                    target = &cx->loops[cx->loops_len - 1];
                }
                
                if (target) {
                    TypeId val_ty = in->t_unit;
                    if (expr->jump.expr) {
                        val_ty = check_expr(cx, expr->jump.expr, target->break_ty);
                    }
                    if (!target->has_break) {
                        target->break_ty = val_ty;
                        target->has_break = true;
                    } else if (!is_error(cx, target->break_ty) && !is_error(cx, val_ty)) {
                        target->break_ty = coerce(cx, val_ty, target->break_ty, expr->jump.expr ? expr->jump.expr->span : expr->span);
                    }
                } else {
                    if (expr->jump.expr) check_expr(cx, expr->jump.expr, TypeId_none());
                }
            } else if (expr->jump.jump_kind == AX_JUMP_CONTINUE) {
                // Continue can't have value, no need to track types
            }
            return in->t_never;
        case AX_HIR_EXPR_CALL:
            return check_call(cx, expr);
        case AX_HIR_EXPR_BINARY:
            return check_binary(cx, expr);
        case AX_HIR_EXPR_UNARY:
            return check_unary(cx, expr);
        case AX_HIR_EXPR_CAST: {
            TypeId src_ty = resolve_ty(cx, check_expr(cx, expr->cast.expr, TypeId_none()));
            TypeId dest_ty = resolve_ty(cx, hir_type_to_typeid(cx, expr->cast.type));
            if (TypeId_is_none(dest_ty) || is_error(cx, src_ty) || is_error(cx, dest_ty)) return in->t_error;
            if (TypeId_eq(src_ty, dest_ty)) return dest_ty;

            bool is_valid = false;
            if (is_intlike(cx, src_ty) && ax_type_is_int(dest_ty, in)) {
                is_valid = true;
                        } else if (ax_type_get(in, src_ty)->kind == AX_TY_ENUM && ax_type_is_int(dest_ty, in)) {
                const AxType *t = ax_type_get(in, src_ty);
                bool has_payload = false;
                for (size_t i = 0; i < t->enm.variant_count; i++) {
                    if (t->enm.variant_field_counts[i] > 0) {
                        has_payload = true;
                        break;
                    }
                }
                if (!has_payload) is_valid = true;
            } else if (TypeId_eq(src_ty, in->t_bool) && ax_type_is_int(dest_ty, in)) {
                is_valid = true;
            } else if (TypeId_eq(src_ty, in->t_u8) && TypeId_eq(dest_ty, in->t_char)) {
                is_valid = true;
            } else if (TypeId_eq(src_ty, in->t_u32) && TypeId_eq(dest_ty, in->t_char)) {
                is_valid = true;
            } else if (TypeId_eq(src_ty, in->t_char) && ax_type_is_int(dest_ty, in)) {
                AxTypeKind k = kind_of(cx, dest_ty);
                if (k == AX_TY_U32 || k == AX_TY_I32 || k == AX_TY_U64 || k == AX_TY_I64 || k == AX_TY_USIZE || k == AX_TY_ISIZE) {
                    is_valid = true;
                }
            } else if (is_never(cx, src_ty)) {
                is_valid = true;
            }
            // Enums and pointers are for later tasks.

            if (is_valid) return dest_ty;
            return type_error(cx, expr->span, AX_TYPE_INVALID_CAST);
        }


        // Valid Axiom outside the axiom0 subset (AXD-013): a diagnostic, never a silent type.
        case AX_HIR_EXPR_ARRAY: {
            if (expr->array.count) {
                // Repeat array [expr; count]
                uint64_t len = 0;
                if (expr->array.count->kind == AX_HIR_EXPR_LITERAL && expr->array.count->literal.kind == AX_TOK_INT) {
                    len = expr->array.count->literal.val.int_val.value;
                } else {
                    type_error(cx, expr->array.count->span, AX_TYPE_ARRAY_SIZE);
                    return in->t_error;
                }
                
                TypeId expected_elem = TypeId_none();
                if (TypeId_is_some(expected) && kind_of(cx, expected) == AX_TY_ARRAY) {
                    expected_elem = ax_type_get(in, resolve_ty(cx, expected))->array.elem;
                }
                
                TypeId elem_ty = check_expr(cx, expr->array.elems, expected_elem);
                if (is_error(cx, elem_ty)) return in->t_error;
                
                AxType t;
                memset(&t, 0, sizeof(t));
                t.kind = AX_TY_ARRAY;
                t.array.elem = elem_ty;
                t.array.len = len;
                return ax_intern_type(&cx->thir->interner, &t);
            } else {
                // List array [e1, e2, ...]
                TypeId expected_elem = TypeId_none();
                if (TypeId_is_some(expected) && kind_of(cx, expected) == AX_TY_ARRAY) {
                    expected_elem = ax_type_get(in, resolve_ty(cx, expected))->array.elem;
                }
                
                uint64_t count = 0;
                TypeId elem_ty = expected_elem;
                
                for (const AxHirExpr *e = expr->array.elems; e; e = e->next) {
                    count++;
                    TypeId t = check_expr(cx, e, elem_ty);
                    if (TypeId_is_none(elem_ty)) {
                        elem_ty = t;
                    }
                }
                
                if (TypeId_is_none(elem_ty)) {
                    elem_ty = in->t_never; // empty array with no expected type
                }
                
                if (is_error(cx, elem_ty)) return in->t_error;
                
                AxType t;
                memset(&t, 0, sizeof(t));
                t.kind = AX_TY_ARRAY;
                t.array.elem = elem_ty;
                t.array.len = count;
                return ax_intern_type(&cx->thir->interner, &t);
            }
        }
        case AX_HIR_EXPR_INDEX: {
            TypeId base_ty = resolve_ty(cx, check_expr(cx, expr->index.base, TypeId_none()));
            if (is_error(cx, base_ty)) return in->t_error;
            
            const AxType *t = ax_type_get(in, base_ty);
            bool is_slice = (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) && ax_type_get(in, t->view.pointee)->kind == AX_TY_SLICE;
            bool is_array = t->kind == AX_TY_ARRAY;
            bool is_str = t->kind == AX_TY_STR;
            
            if (expr->index.arg->kind == AX_HIR_EXPR_RANGE) {
                if (!is_slice && !is_array && !is_str) return type_error(cx, expr->index.base->span, AX_TYPE_CANNOT_INDEX);
                const AxHirExpr *start = expr->index.arg->range.start;
                const AxHirExpr *end = expr->index.arg->range.end;
                if (start) check_expr(cx, start, in->t_usize);
                if (end) check_expr(cx, end, in->t_usize);
                
                AxType v; memset(&v, 0, sizeof(v));
                if (is_slice || is_str) {
                    v.kind = t->kind;
                    v.view.pointee = t->view.pointee; // For STR it doesn't matter, we can return STR
                    if (is_str) return in->t_str;
                } else {
                    v.kind = AX_TY_VIEW;
                    AxType sl; memset(&sl, 0, sizeof(sl));
                    sl.kind = AX_TY_SLICE;
                    sl.slice.elem = t->array.elem;
                    v.view.pointee = ax_intern_type(&cx->thir->interner, &sl);
                }
                return ax_intern_type(&cx->thir->interner, &v);
            }
            
            if (is_array || is_slice || is_str) {
                TypeId idx_ty = check_expr(cx, expr->index.arg, in->t_usize);
                if (is_error(cx, idx_ty)) return in->t_error;
                if (is_array) return t->array.elem;
                if (is_slice) return ax_type_get(in, t->view.pointee)->slice.elem;
                if (is_str) return in->t_u8;
            }
            
            AxTraitResult trait_res = AX_TRAIT_DISPROVEN;
            const AxHirItem *method_item = find_method(cx, base_ty, ax_sv_cstr("index"), &trait_res);
            if (method_item) {
                AxExprMethodMap_insert(&cx->thir->expr_methods, expr, method_item);
                TypeId *fn_ty_ptr = AxItemTypeMap_get(&cx->thir->item_types, method_item);
                if (fn_ty_ptr) {
                    const AxType *fn_ty = ax_type_get(&cx->thir->interner, *fn_ty_ptr);
                    TypeId expected_idx_ty = (fn_ty->fn.param_count >= 2) ? fn_ty->fn.param_types[1] : in->t_usize;
                    check_expr(cx, expr->index.arg, expected_idx_ty);
                    return fn_ty->fn.ret_type;
                }
            }
            return type_error(cx, expr->index.base->span, AX_TYPE_CANNOT_INDEX);
        }
        /* case AX_HIR_EXPR_STRUCT: */
        case AX_HIR_EXPR_MATCH: {
            TypeId val_ty = resolve_ty(cx, check_expr(cx, expr->match.expr, TypeId_none()));
            if (is_error(cx, val_ty)) return in->t_error;

            TypeId match_ty = expected;
            bool first = true;
            bool has_error = false;
            for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
                TypeId p_ty = check_pat(cx, arm->pat, val_ty, true);
                if (is_error(cx, p_ty)) has_error = true;
                if (arm->guard) {
                    check_expr(cx, arm->guard, in->t_bool);
                }
                TypeId arm_ty = check_expr(cx, arm->body, match_ty);
                if (first && !is_error(cx, arm_ty)) {
                    match_ty = arm_ty;
                    first = false;
                }
            }
            
            if (TypeId_is_none(match_ty)) {
                match_ty = expr->match.arms ? in->t_error : in->t_never;
            }
            
            if (!has_error && !is_error(cx, val_ty)) {
                extern void ax_match_check_exhaustiveness(AxThir *thir, StrInterner *str_in, const SourceDatabase *db, AxDiagSink *sink, const AxHirExpr *expr, TypeId val_ty);
                ax_match_check_exhaustiveness(cx->thir, cx->str_in, cx->db, cx->sink, expr, val_ty);
            }
            
            return match_ty;
        }
        case AX_HIR_EXPR_VIEW: {
            TypeId expected_inner = TypeId_none();
            if (expected.v && !is_error(cx, expected)) {
                const AxType *exp_t = ax_type_get(in, expected);
                if (exp_t->kind == (expr->view.is_mut ? AX_TY_MUT_VIEW : AX_TY_VIEW)) {
                    expected_inner = exp_t->view.pointee;
                }
            }
            TypeId inner_ty_expected = expected_inner;
            if (expected_inner.v && !is_error(cx, expected_inner) && ax_type_get(in, expected_inner)->kind == AX_TY_SLICE) {
                inner_ty_expected = TypeId_none();
            }
            TypeId inner_ty = check_expr(cx, expr->view.expr, inner_ty_expected);
            if (is_error(cx, inner_ty)) return in->t_error;
            
            if (expected_inner.v && !is_error(cx, expected_inner)) {
                const AxType *it = ax_type_get(in, inner_ty);
                if (it->kind == AX_TY_ARRAY && ax_type_get(in, expected_inner)->kind == AX_TY_SLICE) {
                    AxType slice; memset(&slice, 0, sizeof(slice));
                    slice.kind = AX_TY_SLICE;
                    slice.slice.elem = it->array.elem;
                    inner_ty = ax_intern_type(&cx->thir->interner, &slice);
                }
            }
            
            AxType t;
            memset(&t, 0, sizeof(t));
            t.kind = expr->view.is_mut ? AX_TY_MUT_VIEW : AX_TY_VIEW;
            t.view.pointee = inner_ty;
            return ax_intern_type(&cx->thir->interner, &t);
        }
        case AX_HIR_EXPR_FOR:
        case AX_HIR_EXPR_UNSAFE:
        case AX_HIR_EXPR_COMPTIME:
            return in->t_error;
        case AX_HIR_EXPR_CLOSURE: {
            AxSymbolId inner_syms[128];
            size_t inner_count = 0;
            for (const AxHirParam *p = expr->closure.params; p; p = p->next) {
                if (inner_count < 128) inner_syms[inner_count++] = p->symbol;
            }
            
            RawCapture raw_caps[64];
            size_t raw_cap_count = 0;
            scan_expr_captures(cx, expr->closure.body, inner_syms, &inner_count, raw_caps, &raw_cap_count, false, false);
            
            AxClosureCapture *caps = NULL;
            if (raw_cap_count > 0) {
                caps = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxClosureCapture) * raw_cap_count, _Alignof(AxClosureCapture));
                for (size_t i = 0; i < raw_cap_count; i++) {
                    caps[i].sym = raw_caps[i].sym;
                    const TypeId *vty_ptr = AxSymbolTypeMap_get(&cx->thir->symbol_types, raw_caps[i].sym);
                    TypeId base_ty = vty_ptr ? *vty_ptr : cx->thir->interner.t_i32;
                    
                    if (raw_caps[i].is_moved) {
                        caps[i].mode = AX_CAP_MOVE;
                        caps[i].type = base_ty;
                    } else if (raw_caps[i].is_mutated) {
                        caps[i].mode = AX_CAP_MUT_VIEW;
                        AxType vt; memset(&vt, 0, sizeof(vt));
                        vt.kind = AX_TY_MUT_VIEW;
                        vt.view.pointee = base_ty;
                        caps[i].type = ax_intern_type(&cx->thir->interner, &vt);
                    } else {
                        if (ax_type_is_copy(base_ty, cx->thir, cx->str_in)) {
                            caps[i].mode = AX_CAP_COPY;
                            caps[i].type = base_ty;
                        } else {
                            caps[i].mode = AX_CAP_VIEW;
                            AxType vt; memset(&vt, 0, sizeof(vt));
                            vt.kind = AX_TY_VIEW;
                            vt.view.pointee = base_ty;
                            caps[i].type = ax_intern_type(&cx->thir->interner, &vt);
                        }
                    }
                }
            }
            
            size_t param_count = 0;
            for (const AxHirParam *p = expr->closure.params; p; p = p->next) param_count++;
            
            const AxType *exp_t = (!TypeId_is_none(expected) && !is_error(cx, expected)) ? ax_type_get(in, resolve_ty(cx, expected)) : NULL;
            TypeId *closure_param_types = NULL;
            if (param_count > 0) {
                closure_param_types = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * param_count, _Alignof(TypeId));
                size_t idx = 0;
                for (const AxHirParam *p = expr->closure.params; p; p = p->next, idx++) {
                    TypeId pty;
                    if (p->type) {
                        pty = resolve_ty(cx, hir_type_to_typeid(cx, p->type));
                    } else if (exp_t && exp_t->kind == AX_TY_FN && idx < exp_t->fn.param_count) {
                        pty = exp_t->fn.param_types[idx];
                    } else if (exp_t && exp_t->kind == AX_TY_CLOSURE && idx < exp_t->closure.param_count) {
                        pty = exp_t->closure.params[idx];
                    } else {
                        pty = new_int_var(cx);
                    }
                    closure_param_types[idx] = pty;
                    AxParamTypeMap_insert(&cx->thir->param_types, p, pty);
                    AxSymbolTypeMap_insert(&cx->thir->symbol_types, p->symbol, pty);
                }
            }
            
            TypeId exp_ret = TypeId_none();
            if (expr->closure.ret_type) {
                exp_ret = resolve_ty(cx, hir_type_to_typeid(cx, expr->closure.ret_type));
            } else if (exp_t && exp_t->kind == AX_TY_FN) {
                exp_ret = exp_t->fn.ret_type;
            } else if (exp_t && exp_t->kind == AX_TY_CLOSURE) {
                exp_ret = exp_t->closure.ret_type;
            }
            
            TypeId old_ret = cx->return_type;
            size_t old_vars_len = cx->vars_len;
            cx->return_type = exp_ret;
            
            for (const AxHirParam *p = expr->closure.params; p; p = p->next) {
                if (cx->vars_len == cx->vars_cap) {
                    cx->vars = ax_grow_array(cx->vars, &cx->vars_cap, sizeof(VarState), cx->vars_len + 1);
                }
                cx->vars[cx->vars_len].sym = p->symbol;
                cx->vars[cx->vars_len].is_mut = p->is_mut;
                cx->vars[cx->vars_len].is_init = true;
                cx->vars_len++;
            }
            
            TypeId body_ty = check_expr(cx, expr->closure.body, exp_ret);
            if (TypeId_is_none(body_ty) || body_ty.v == 0) body_ty = in->t_unit;
            
            cx->return_type = old_ret;
            cx->vars_len = old_vars_len;
            
            uint32_t closure_id = cx->next_closure_id++;
            uint32_t closure_sym = 0x40000000 + closure_id;
            
            AxHirItem *fn_item = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirItem), _Alignof(AxHirItem));
            memset(fn_item, 0, sizeof(AxHirItem));
            fn_item->kind = AX_HIR_ITEM_FN;
            fn_item->span = expr->span;
            fn_item->fn.symbol = (AxSymbolId){ closure_sym };
            
            AxHirParam *first_p = NULL;
            AxHirParam **curr_p = &first_p;
            for (size_t i = 0; i < raw_cap_count; i++) {
                AxHirParam *hp = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirParam), _Alignof(AxHirParam));
                memset(hp, 0, sizeof(AxHirParam));
                hp->span = expr->span;
                hp->is_mut = (caps[i].mode == AX_CAP_MUT_VIEW);
                hp->symbol = caps[i].sym;
                *curr_p = hp;
                curr_p = &hp->next;
                AxParamTypeMap_insert(&cx->thir->param_types, hp, caps[i].type);
            }
            for (const AxHirParam *p = expr->closure.params; p; p = p->next) {
                AxHirParam *hp = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirParam), _Alignof(AxHirParam));
                memset(hp, 0, sizeof(AxHirParam));
                hp->span = p->span;
                hp->name = p->name;
                hp->symbol = p->symbol;
                hp->is_mut = p->is_mut;
                *curr_p = hp;
                curr_p = &hp->next;
                TypeId pty = *AxParamTypeMap_get(&cx->thir->param_types, p);
                AxParamTypeMap_insert(&cx->thir->param_types, hp, pty);
            }
            *curr_p = NULL;
            fn_item->fn.params = first_p;
            
            if (expr->closure.body->kind == AX_HIR_EXPR_BLOCK) {
                fn_item->fn.body = &expr->closure.body->block.block;
            } else {
                AxHirBlock *blk = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirBlock), _Alignof(AxHirBlock));
                memset(blk, 0, sizeof(AxHirBlock));
                blk->span = expr->closure.body->span;
                AxHirStmt *st = ax_arena_alloc(&cx->thir->interner.arena, sizeof(AxHirStmt), _Alignof(AxHirStmt));
                memset(st, 0, sizeof(AxHirStmt));
                st->kind = AX_HIR_STMT_EXPR;
                st->span = expr->closure.body->span;
                st->expr_stmt.expr = expr->closure.body;
                st->expr_stmt.has_semi = false;
                blk->stmts = st;
                fn_item->fn.body = blk;
            }
            
            size_t total_fn_params = raw_cap_count + param_count;
            TypeId *fn_param_types = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * (total_fn_params ? total_fn_params : 1), _Alignof(TypeId));
            for (size_t i = 0; i < raw_cap_count; i++) fn_param_types[i] = caps[i].type;
            for (size_t i = 0; i < param_count; i++) fn_param_types[raw_cap_count + i] = closure_param_types[i];
            
            AxType fnt; memset(&fnt, 0, sizeof(fnt));
            fnt.kind = AX_TY_FN;
            fnt.fn.param_count = total_fn_params;
            fnt.fn.param_types = fn_param_types;
            fnt.fn.ret_type = body_ty;
            TypeId fn_type_id = ax_intern_type(&cx->thir->interner, &fnt);
            
            AxItemTypeMap_insert(&cx->thir->item_types, fn_item, fn_type_id);
            
            AxHirItem **tail = &((AxHir*)cx->hir)->items;
            while (*tail) tail = &(*tail)->next;
            *tail = fn_item;
            
            AxType cty; memset(&cty, 0, sizeof(cty));
            cty.kind = AX_TY_CLOSURE;
            cty.closure.closure_id = closure_id;
            cty.closure.fn_sym = closure_sym;
            cty.closure.fn_type = fn_type_id;
            cty.closure.ret_type = body_ty;
            cty.closure.param_count = param_count;
            cty.closure.params = closure_param_types;
            cty.closure.capture_count = raw_cap_count;
            cty.closure.captures = caps;
            
            return ax_intern_type(&cx->thir->interner, &cty);
        }
        /* case AX_HIR_EXPR_FIELD: */
        /* case AX_HIR_EXPR_TUPLE_INDEX: */
        case AX_HIR_EXPR_METHOD_CALL: {
            bool is_type_name = false;
            if (expr->method_call.receiver->kind == AX_HIR_EXPR_PATH) {
                is_type_name = true;
                if (expr->method_call.receiver->path.path.symbol.v != 0) {
                    for (size_t k = 0; k < cx->vars_len; k++) {
                        if (cx->vars[k].sym.v == expr->method_call.receiver->path.path.symbol.v) {
                            is_type_name = false;
                            break;
                        }
                    }
                    if (is_type_name && cx->current_fn) {
                        for (const AxHirParam *p = cx->current_fn->fn.params; p; p = p->next) {
                            if (p->symbol.v == expr->method_call.receiver->path.path.symbol.v) {
                                is_type_name = false;
                                break;
                            }
                        }
                    }
                }
            }
            TypeId receiver_ty = check_expr(cx, expr->method_call.receiver, TypeId_none());
            if (is_error(cx, receiver_ty)) return cx->thir->interner.t_error;
            
            // Strip view/mut_view to find the base type for method lookup
            TypeId base_ty = receiver_ty;
            const AxType *t = ax_type_get(&cx->thir->interner, base_ty);
            while (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW || t->kind == AX_TY_PTR) {
                base_ty = (t->kind == AX_TY_PTR) ? t->ptr.pointee : t->view.pointee;
                t = ax_type_get(&cx->thir->interner, base_ty);
            }
            
            StrView mname = ax_interner_get(cx->str_in, expr->method_call.method_name);
            AxTraitResult trait_res = AX_TRAIT_DISPROVEN;
            const AxHirItem *method_item = find_method(cx, base_ty, mname, &trait_res);
            
            if (trait_res == AX_TRAIT_AMBIGUOUS) {
                return type_error(cx, expr->span, AX_TRAIT_AMBIGUOUS_METHOD);
            }
            if (!method_item) {
                if (t->kind == AX_TY_ENUM) {
                    size_t vidx = 0;
                    for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                        StrView vname = ax_interner_get(cx->str_in, v->name);
                        if (ax_sv_eq(vname, mname)) {
                            AxExprVariantMap_insert(&cx->thir->expr_variants, expr, vidx);
                            if (v->is_struct) {
                                return type_error(cx, expr->span, AX_TYPE_MISMATCH);
                            }
                            size_t expected_args = t->enm.variant_field_counts[vidx];
                            size_t argc = 0;
                            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) argc++;
                            if (argc != expected_args) {
                                return type_error(cx, expr->span, AX_TYPE_ARG_COUNT);
                            }
                            const TypeId *payloads = t->enm.variant_fields[vidx];
                            size_t arg_idx = 0;
                            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                                check_expr(cx, a, payloads[arg_idx++]);
                            }
                            return receiver_ty;
                        }
                        vidx++;
                    }
                }
                return type_error(cx, expr->span, AX_TYPE_UNKNOWN_FIELD);
            }
            
            AxExprMethodMap_insert(&cx->thir->expr_methods, expr, method_item);
            
            TypeId *fn_ty_ptr = AxItemTypeMap_get(&cx->thir->item_types, method_item);
            if (!fn_ty_ptr) AX_ICE("Method missing fn type");
            TypeId fn_ty_id = *fn_ty_ptr;
            if (method_item->kind == AX_HIR_ITEM_FN && method_item->fn.generic_params) {
                size_t param_count = 0;
                for (AxHirGenericParam *p = method_item->fn.generic_params->params; p; p = p->next) param_count++;
                if (param_count > 0) {
                    AxGenericArgs gargs;
                    gargs.count = param_count;
                    gargs.args = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * param_count, _Alignof(TypeId));
                    if (expr->method_call.generic_args) {
                        AxHirGenericArg *ga = expr->method_call.generic_args->args;
                        for (size_t k = 0; k < param_count; k++) {
                            gargs.args[k] = ga ? hir_type_to_typeid(cx, ga->type) : new_ty_var(cx, expr->span);
                            if (ga) ga = ga->next;
                        }
                    } else {
                        for (size_t k = 0; k < param_count; k++) {
                            gargs.args[k] = new_ty_var(cx, expr->span);
                        }
                    }
                    fn_ty_id = ax_subst_ty(cx, fn_ty_id, &gargs);
                }
            }
            const AxType *fn_ty = ax_type_get(&cx->thir->interner, fn_ty_id);
            
            size_t expected_args = fn_ty->fn.param_count;
            bool has_self = (method_item->fn.params && ax_sv_eq_cstr(ax_interner_get(cx->str_in, method_item->fn.params->name), "self"));
            
            bool pass_receiver = has_self && !is_type_name;
            size_t argc = pass_receiver ? 1 : 0;
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) argc++;
            
            if (argc != expected_args) {
                for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                    check_expr(cx, a, TypeId_none());
                }
                return type_error(cx, expr->span, AX_TYPE_ARG_COUNT);
            }
            
            size_t i = pass_receiver ? 1 : 0;
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) {
                TypeId arg_expected = fn_ty->fn.param_types[i];
                TypeId arg_ty = check_expr(cx, a, arg_expected);
                if (!is_error(cx, arg_ty) && !unify_ty(cx, arg_ty, arg_expected)) {
                    type_error(cx, a->span, AX_TYPE_MISMATCH);
                }
                i++;
            }
            
            return fn_ty->fn.ret_type;
        }
                case AX_HIR_EXPR_TRY: {
            TypeId expr_ty = check_expr(cx, expr->try_expr.expr, TypeId_none());
            if (is_error(cx, expr_ty)) return in->t_error;
            const AxType *t = ax_type_get(in, expr_ty);
            if (t->kind != AX_TY_ENUM) {
                return type_error(cx, expr->span, AX_TYPE_TRY_OPERAND);
            }
            StrView enum_name = ax_interner_get(cx->str_in, t->enm.def->enum_decl.name);
            bool is_opt = ax_sv_eq_cstr(enum_name, "Option");
            bool is_res = ax_sv_eq_cstr(enum_name, "Result");
            if (!is_opt && !is_res) {
                return type_error(cx, expr->span, AX_TYPE_TRY_OPERAND);
            }
            
            if (is_error(cx, cx->return_type)) return in->t_error;
            const AxType *ret_t = ax_type_get(in, cx->return_type);
            if (ret_t->kind != AX_TY_ENUM) return type_error(cx, expr->span, AX_TYPE_TRY_RETURN_MISMATCH);
            StrView ret_enum_name = ax_interner_get(cx->str_in, ret_t->enm.def->enum_decl.name);
            if (is_opt && !ax_sv_eq_cstr(ret_enum_name, "Option")) {
                return type_error(cx, expr->span, AX_TYPE_TRY_RETURN_MISMATCH);
            }
            if (is_res && !ax_sv_eq_cstr(ret_enum_name, "Result")) {
                return type_error(cx, expr->span, AX_TYPE_TRY_RETURN_MISMATCH);
            }
            
            const char *payload_var_name = is_opt ? "Some" : "Ok";
            const AxHirVariantDecl *payload_var = NULL;
            uint32_t payload_idx = 0;
            uint32_t err_idx = 0;
            uint32_t curr_idx = 0;
            for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next, curr_idx++) {
                if (ax_sv_eq_cstr(ax_interner_get(cx->str_in, v->name), payload_var_name)) {
                    payload_var = v;
                    payload_idx = curr_idx;
                } else {
                    err_idx = curr_idx;
                }
            }
            if (!payload_var || payload_var->is_struct || !payload_var->tuple_types) return in->t_error;
            
            // NOTE: cast away const to mutate the HIR
            AxHirExpr *mut_expr = (AxHirExpr *)expr;
            mut_expr->try_expr.is_opt = is_opt;
            mut_expr->try_expr.payload_idx = payload_idx;
            mut_expr->try_expr.err_idx = err_idx;
            
            if (t->enm.variant_field_counts[payload_idx] > 0) {
                return t->enm.variant_fields[payload_idx][0];
            } else {
                return hir_type_to_typeid(cx, payload_var->tuple_types);
            }
        }
        case AX_HIR_EXPR_AWAIT:
            return type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);

        default:
            AX_ICE("typeck: unknown HIR expression kind %d", (int)expr->kind);
    }
    return in->t_error;
}

static TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected) {
    if (!expr) return cx->thir->interner.t_unit;
    TypeId ty = check_expr_kind(cx, expr, expected);
    AxExprTypeMap_insert(&cx->thir->expr_types, expr, ty);
    return coerce(cx, ty, expected, expr->span);
}

static TypeId check_block(TypeckCtx *cx, const AxHirBlock *block, TypeId expected) {
    const TypeInterner *in = &cx->thir->interner;
    TypeId ty = in->t_unit;
    const AxHirExpr *tail = NULL;
    bool diverges = false;
    bool reported_unreachable = false;
    for (const AxHirStmt *s = block->stmts; s; s = s->next) {
        if (diverges && !reported_unreachable) {
            AxDiagnostic d = {0};
            d.code = AX_TYPE_UNREACHABLE;
            d.severity = AX_DIAG_WARNING;
            d.message = "unreachable statement";
            d.primary = s->span;
            ax_diag_sink_report(cx->sink, &d);
            reported_unreachable = true;
        }
        tail = NULL;
        if (s->kind == AX_HIR_STMT_LET) {
            if (s->let.else_block) {
                desugar_let_else(cx, (AxHirStmt*)s);
                // Fall through to AX_HIR_STMT_EXPR! Wait, I can't fall through directly without goto.
                // Let's just process it as EXPR right away:
                TypeId ety = check_expr(cx, s->expr_stmt.expr, TypeId_none());
                if (is_never(cx, ety)) diverges = true;
                if (s->expr_stmt.has_semi) {
                    ty = in->t_unit;
                } else {
                    ty = ety;
                    tail = s->expr_stmt.expr;
                }
                continue;
            }
            // Irrefutability check for normal let
            TypeId declared = hir_type_to_typeid(cx, s->let.type);

            bool is_init = false;
            if (s->let.expr) {
                // The initializer is the coercion site for the annotation.
                TypeId init = check_expr(cx, s->let.expr, declared);
                if (is_never(cx, init)) diverges = true;
                if (TypeId_is_none(declared)) declared = init;
                is_init = true;
            } else if (TypeId_is_none(declared)) {
                type_error(cx, s->let.pat->span, AX_TYPE_UNKNOWN);
                declared = in->t_error;
            }
            
            // Do irrefutability check:
            if (!is_pat_irrefutable(cx, s->let.pat, declared)) {
                AxDiagnostic d = {0};
                d.code = AX_PAT_REFUTABLE;
                d.severity = AX_DIAG_ERROR;
                d.message = ax_diag_code_default_message(AX_PAT_REFUTABLE);
                d.primary = s->let.pat->span;
                ax_diag_sink_report(cx->sink, &d);
            }

            check_pat(cx, s->let.pat, declared, is_init);
            ty = in->t_unit;
        } else if (s->kind == AX_HIR_STMT_ASSIGN) {
            // Note: right hand side is evaluated first in assignment
            TypeId right = check_expr(cx, s->assign.right, TypeId_none());
            
            // To avoid UNINIT_USE when re-assigning, we check if it's a path and update it first
            // Wait, actually `check_expr` on left will trigger UNINIT_USE if we just call it normally!
            // But an assignment to a variable is NOT a use of its previous value.
            // So we shouldn't do a full `check_expr(left)` which evaluates it as an r-value, 
            // unless we handle `AX_HIR_EXPR_PATH` specially here.
            TypeId left = TypeId_none();
            if (s->assign.left->kind == AX_HIR_EXPR_PATH) {
                left = lookup_path_type(cx, &s->assign.left->path.path, NULL);
                AxExprTypeMap_insert(&cx->thir->expr_types, s->assign.left, left);
                if (s->assign.left->path.path.symbol.v != 0) {
                    AxSymbolId sym = s->assign.left->path.path.symbol;
                    for (size_t i = 0; i < cx->vars_len; i++) {
                        if (cx->vars[i].sym.v == sym.v) {
                            if (cx->vars[i].is_init && !cx->vars[i].is_mut) {
                                type_error(cx, s->assign.left->span, AX_TYPE_ASSIGN_IMMUTABLE);
                            }
                            cx->vars[i].is_init = true;
                            break;
                        }
                    }
                }
            } else {
                left = check_expr(cx, s->assign.left, TypeId_none());
                const AxHirExpr* base = s->assign.left;
                while (base->kind == AX_HIR_EXPR_FIELD || base->kind == AX_HIR_EXPR_TUPLE_INDEX) {
                    if (base->kind == AX_HIR_EXPR_FIELD) {
                        base = base->field.base;
                    } else {
                        base = base->tuple_index.base;
                    }
                }
                if (base->kind == AX_HIR_EXPR_PATH) {
                    if (base->path.path.symbol.v != 0) {
                        AxSymbolId sym = base->path.path.symbol;
                        for (size_t i = 0; i < cx->vars_len; i++) {
                            if (cx->vars[i].sym.v == sym.v) {
                                if (cx->vars[i].is_init && !cx->vars[i].is_mut) {
                                    type_error(cx, s->assign.left->span, AX_TYPE_ASSIGN_IMMUTABLE);
                                }
                                break;
                            }
                        }
                    }
                }
            }
            coerce(cx, right, left, s->assign.right->span);
            if (is_never(cx, right)) diverges = true;
            ty = in->t_unit;
        } else if (s->kind == AX_HIR_STMT_EXPR) {
            TypeId ety = check_expr(cx, s->expr_stmt.expr, TypeId_none());
            if (is_never(cx, ety)) diverges = true;
            if (s->expr_stmt.has_semi) {
                ty = in->t_unit;
            } else {
                ty = ety;
                tail = s->expr_stmt.expr;
            }
        } else {
            ty = in->t_unit; // AX_HIR_STMT_ERROR: already diagnosed by lowering
        }
    }

    if (diverges) {
        ty = in->t_never;
    }

    if (TypeId_is_some(expected) && !unify_ty(cx, ty, expected)) {
        if (TypeId_eq(resolve_ty(cx, ty), in->t_unit)) {
            // AXS-SEM-014/015: the body can reach its end without producing the value.
            return type_error(cx, block->span, AX_TYPE_RETURN);
        }
        return type_error(cx, tail ? tail->span : block->span, AX_TYPE_MISMATCH);
    }

    return ty;
}

