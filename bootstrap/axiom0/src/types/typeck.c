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
} TypeckCtx;

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
    cx->int_vars_len++;

    AxType t;
    memset(&t, 0, sizeof(t));
    t.kind = AX_TY_INT_VAR;
    t.int_var.var_id = var_id;
    return ax_intern_type(&cx->thir->interner, &t);
}

static TypeId resolve_ty(TypeckCtx *cx, TypeId id) {
    if (TypeId_is_none(id)) return id;
    const AxType *t = ax_type_get(&cx->thir->interner, id);
    if (t->kind == AX_TY_INT_VAR) {
        TypeId resolved = cx->int_vars[t->int_var.var_id].resolved_to;
        if (TypeId_is_some(resolved)) {
            // Path compression
            TypeId fully_resolved = resolve_ty(cx, resolved);
            cx->int_vars[t->int_var.var_id].resolved_to = fully_resolved;
            return fully_resolved;
        }
    }
    return id;
}

static AxTypeKind kind_of(TypeckCtx *cx, TypeId id) {
    return ax_type_get(&cx->thir->interner, resolve_ty(cx, id))->kind;
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

    return false;
}

/* The coercion seam: report a mismatch once and poison the result. */
static TypeId coerce(TypeckCtx *cx, TypeId ty, TypeId expected, Span span) {
    if (TypeId_is_none(expected)) return ty;
    if (!unify_ty(cx, ty, expected)) {
        return type_error(cx, span, AX_TYPE_MISMATCH);
    }
    return ty;
}

static void default_int_vars(TypeckCtx *cx) {
    // AXS-SEM-020: still unconstrained at the end of the function body -> i32.
    for (size_t i = cx->fn_var_start; i < cx->int_vars_len; i++) {
        if (TypeId_is_none(cx->int_vars[i].resolved_to)) {
            cx->int_vars[i].resolved_to = cx->thir->interner.t_i32;
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
        if (ax_sv_eq_cstr(name, "never")) return cx->thir->interner.t_never;
        // AXS-SEM-010: f32/f64 (and everything else) are outside the axiom0 subset.
        return type_error(cx, ht->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
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

/* Replace every integer type variable in the THIR by its final type, so later phases (MIR
 * builder, verifier, interpreter, dumps) only see concrete types. */
static void finalize_types(TypeckCtx *cx) {
    uint32_t cur = 0;
    AxExprTypeMapEntry *ee;
    while (AxExprTypeMap_next(&cx->thir->expr_types, &cur, &ee)) ee->value = resolve_ty(cx, ee->value);
    cur = 0;
    AxPatTypeMapEntry *pe;
    while (AxPatTypeMap_next(&cx->thir->pat_types, &cur, &pe)) pe->value = resolve_ty(cx, pe->value);
    cur = 0;
    AxSymbolTypeMapEntry *se;
    while (AxSymbolTypeMap_next(&cx->thir->symbol_types, &cur, &se)) se->value = resolve_ty(cx, se->value);
}

static TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected);
static TypeId check_block(TypeckCtx *cx, const AxHirBlock *block, TypeId expected);

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

    // Pass 1: Global types (each signature type is converted, and so diagnosed, once)
    for (const AxHirItem *it = hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) {
            TypeId ret_ty = hir_type_to_typeid(&cx, it->fn.ret_type);
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
        }
    }

    // AXS-SEM-080 is a type rule: `check` reports it (only MAIN_MISSING is build/run-only).
    check_main_signature(&cx);

    // Pass 2: Typecheck bodies
    for (const AxHirItem *it = hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.body) {
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
            }

            check_block(&cx, it->fn.body, cx.return_type);
            default_int_vars(&cx);
            check_literal_ranges(&cx);
        }
    }

    finalize_types(&cx);

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
        default:
            return type_error(cx, pat->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
    }
    AxPatTypeMap_insert(&cx->thir->pat_types, pat, ty);
    return ty;
}

static TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path) {
    if (path->symbol.v != 0) {
        TypeId *t = AxSymbolTypeMap_get(&cx->thir->symbol_types, path->symbol);
        if (t) return *t;
    }
    StrView name = ax_source_db_span_text(cx->db, path->span);
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) {
            StrView it_name = ax_interner_get(cx->str_in, it->fn.name);
            if (ax_sv_eq(it_name, name)) {
                TypeId *t = AxItemTypeMap_get(&cx->thir->item_types, it);
                if (t) return *t;
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
            // Str arrives with T041; until then a string literal is outside the subset.
            return type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
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
            if (!ok) return type_error(cx, expr->span, AX_TYPE_OPERATOR);
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

        case AX_UNOP_DEREF:
            check_expr(cx, operand, TypeId_none());
            return type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);

        default:
            AX_ICE("typeck: unknown unary operator %d", (int)expr->unary.op);
    }
    return in->t_error;
}

static TypeId check_call(TypeckCtx *cx, const AxHirExpr *expr) {
    TypeId callee_ty = resolve_ty(cx, check_expr(cx, expr->call.callee, TypeId_none()));
    const AxType *ct = ax_type_get(&cx->thir->interner, callee_ty);
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

static TypeId check_if(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected) {
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

/* Computes the type of `expr`; `expected` is only a hint for sub-expressions that carry it on
 * (blocks, if branches). Every case reports its own errors and returns t_error after one. */
static TypeId check_expr_kind(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected) {
    const TypeInterner *in = &cx->thir->interner;
    switch (expr->kind) {
        case AX_HIR_EXPR_ERROR:
            return in->t_error;
        case AX_HIR_EXPR_LITERAL:
            return check_literal(cx, expr);
        case AX_HIR_EXPR_PATH: {
            TypeId t = lookup_path_type(cx, &expr->path.path);
            if (expr->path.path.symbol.v != 0) {
                for (size_t i = 0; i < cx->vars_len; i++) {
                    if (cx->vars[i].sym.v == expr->path.path.symbol.v) {
                        if (!cx->vars[i].is_init) {
                            type_error(cx, expr->span, AX_TYPE_UNINIT_USE);
                        }
                        break;
                    }
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
                TypeId cond_ty = check_expr(cx, expr->while_expr.cond, TypeId_none());
                check_pat(cx, expr->while_expr.let_pat, cond_ty, true);
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
            // Casts are MS-P5; the minimal v1 rule is kept as delivered by T017.
            TypeId src_ty = resolve_ty(cx, check_expr(cx, expr->cast.expr, TypeId_none()));
            TypeId dest_ty = resolve_ty(cx, hir_type_to_typeid(cx, expr->cast.type));
            if (TypeId_is_none(dest_ty) || is_error(cx, src_ty) || is_error(cx, dest_ty)) return in->t_error;
            if (TypeId_eq(src_ty, dest_ty)) return dest_ty;
            bool src_ok = is_intlike(cx, src_ty) || TypeId_eq(src_ty, in->t_bool) || TypeId_eq(src_ty, in->t_char);
            if (src_ok && ax_type_is_int(dest_ty, in)) return dest_ty;
            return type_error(cx, expr->span, AX_TYPE_MISMATCH); // AX_TYPE_INVALID_CAST: MS-P5
        }

        // Valid Axiom outside the axiom0 subset (AXD-013): a diagnostic, never a silent type.
        case AX_HIR_EXPR_ARRAY:
        case AX_HIR_EXPR_STRUCT:
        case AX_HIR_EXPR_MATCH:
        case AX_HIR_EXPR_FOR:
        case AX_HIR_EXPR_UNSAFE:
        case AX_HIR_EXPR_VIEW:
        case AX_HIR_EXPR_COMPTIME:
        case AX_HIR_EXPR_CLOSURE:
        case AX_HIR_EXPR_RANGE:
        case AX_HIR_EXPR_FIELD:
        case AX_HIR_EXPR_TUPLE_INDEX:
        case AX_HIR_EXPR_METHOD_CALL:
        case AX_HIR_EXPR_INDEX:
        case AX_HIR_EXPR_TRY:
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
                left = lookup_path_type(cx, &s->assign.left->path.path);
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
