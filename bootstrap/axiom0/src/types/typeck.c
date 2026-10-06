#include "types/types.h"
#include "source/source.h"
#include <string.h>
#include <stdio.h>
#include <inttypes.h>

typedef struct IntTypeVar {
    TypeId resolved_to; // none if unresolved
} IntTypeVar;

typedef struct TypeckCtx {
    const AxHir *hir;
    AxThir *thir;
    AxDiagSink *sink;
    StrInterner *str_in;
    const SourceDatabase *db;
    
    // Per-function inference context
    IntTypeVar *int_vars;
    size_t int_vars_len;
    size_t int_vars_cap;
    
    TypeId return_type;
    bool in_loop;
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

static bool unify_ty(TypeckCtx *cx, TypeId a, TypeId b) {
    a = resolve_ty(cx, a);
    b = resolve_ty(cx, b);
    if (TypeId_eq(a, b)) return true;
    
    const AxType *ta = ax_type_get(&cx->thir->interner, a);
    const AxType *tb = ax_type_get(&cx->thir->interner, b);
    
    if (ta->kind == AX_TY_ERROR || tb->kind == AX_TY_ERROR) return true;
    if (ta->kind == AX_TY_NEVER || tb->kind == AX_TY_NEVER) return true; // never coerces
    
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

static void default_int_vars(TypeckCtx *cx) {
    for (size_t i = 0; i < cx->int_vars_len; i++) {
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
        return type_error(cx, ht->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
    }
    if (ht->kind == AX_HIR_TYPE_FN) {
        AxType t;
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

static TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected);
static TypeId check_block(TypeckCtx *cx, const AxHirBlock *block, TypeId expected);

AxThir ax_typeck(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in, const SourceDatabase *db) {
    AxThir thir;
    ax_thir_init(&thir);
    
    TypeckCtx cx;
    cx.hir = hir;
    cx.thir = &thir;
    cx.sink = sink;
    cx.str_in = str_in;
    cx.db = db;
    cx.int_vars = NULL;
    cx.int_vars_len = 0;
    cx.int_vars_cap = 0;
    cx.return_type = thir.interner.t_unit;
    cx.in_loop = false;
    
    // Pass 1: Global types
    for (const AxHirItem *it = hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) {
            TypeId ret_ty = hir_type_to_typeid(&cx, it->fn.ret_type);
            
            AxType ft;
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
    
    // Pass 2: Typecheck bodies
    for (const AxHirItem *it = hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.body) {
            cx.int_vars_len = 0;
            cx.return_type = hir_type_to_typeid(&cx, it->fn.ret_type);
            
            for (const AxHirParam *p = it->fn.params; p; p = p->next) {
                if (p->symbol.v != 0) {
                    TypeId pty = hir_type_to_typeid(&cx, p->type);
                    AxSymbolTypeMap_insert(&thir.symbol_types, p->symbol, pty);
                }
            }
            
            check_block(&cx, it->fn.body, cx.return_type);
            default_int_vars(&cx);
        }
    }
    
    return thir;
}
static TypeId check_pat(TypeckCtx *cx, const AxHirPat *pat, TypeId expected) {
    if (!pat) return cx->thir->interner.t_unit;
    TypeId ty = expected;
    switch (pat->kind) {
        case AX_HIR_PAT_BINDING:
            if (pat->binding.symbol.v != 0) {
                AxSymbolTypeMap_insert(&cx->thir->symbol_types, pat->binding.symbol, ty);
            }
            break;
        case AX_HIR_PAT_LITERAL: {
            TypeId lit_ty = cx->thir->interner.t_i32;
            if (pat->literal.tok.kind == AX_TOK_KW_TRUE || pat->literal.tok.kind == AX_TOK_KW_FALSE) {
                lit_ty = cx->thir->interner.t_bool;
            } else if (pat->literal.tok.kind == AX_TOK_CHAR) {
                lit_ty = cx->thir->interner.t_char;
            } else if (pat->literal.tok.kind == AX_TOK_INT) {
                lit_ty = new_int_var(cx);
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

static TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected) {
    if (!expr) return cx->thir->interner.t_unit;
    TypeId ty = cx->thir->interner.t_error;
    switch (expr->kind) {
        case AX_HIR_EXPR_ERROR:
            ty = cx->thir->interner.t_error;
            break;
        case AX_HIR_EXPR_LITERAL: {
            if (expr->literal.kind == AX_TOK_KW_TRUE || expr->literal.kind == AX_TOK_KW_FALSE) {
                ty = cx->thir->interner.t_bool;
            } else if (expr->literal.kind == AX_TOK_CHAR) {
                ty = cx->thir->interner.t_char;
            } else if (expr->literal.kind == AX_TOK_INT) {
                ty = new_int_var(cx);
            }
            break;
        }
        case AX_HIR_EXPR_PATH:
            ty = lookup_path_type(cx, &expr->path.path);
            break;
        case AX_HIR_EXPR_BLOCK:
            ty = check_block(cx, &expr->block.block, expected);
            break;
        case AX_HIR_EXPR_IF: {
            if (expr->if_expr.let_pat) {
                TypeId cond_ty = check_expr(cx, expr->if_expr.cond, new_int_var(cx));
                check_pat(cx, expr->if_expr.let_pat, cond_ty);
            } else {
                TypeId cond_ty = check_expr(cx, expr->if_expr.cond, cx->thir->interner.t_bool);
                if (!unify_ty(cx, cond_ty, cx->thir->interner.t_bool)) {
                    type_error(cx, expr->if_expr.cond->span, AX_TYPE_MISMATCH);
                }
            }
            TypeId then_ty = check_block(cx, &expr->if_expr.block, expected);
            if (expr->if_expr.else_branch) {
                TypeId else_ty = check_expr(cx, expr->if_expr.else_branch, expected);
                if (!unify_ty(cx, then_ty, else_ty)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                ty = resolve_ty(cx, then_ty);
            } else {
                if (!unify_ty(cx, then_ty, cx->thir->interner.t_unit)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                ty = cx->thir->interner.t_unit;
            }
            break;
        }
        case AX_HIR_EXPR_LOOP: {
            bool old_loop = cx->in_loop;
            cx->in_loop = true;
            check_block(cx, &expr->loop.block, cx->thir->interner.t_unit);
            cx->in_loop = old_loop;
            ty = cx->thir->interner.t_never;
            break;
        }
        case AX_HIR_EXPR_WHILE: {
            bool old_loop = cx->in_loop;
            cx->in_loop = true;
            if (expr->while_expr.let_pat) {
                TypeId cond_ty = check_expr(cx, expr->while_expr.cond, new_int_var(cx));
                check_pat(cx, expr->while_expr.let_pat, cond_ty);
            } else {
                TypeId cond_ty = check_expr(cx, expr->while_expr.cond, cx->thir->interner.t_bool);
                if (!unify_ty(cx, cond_ty, cx->thir->interner.t_bool)) {
                    type_error(cx, expr->while_expr.cond->span, AX_TYPE_MISMATCH);
                }
            }
            check_block(cx, &expr->while_expr.block, cx->thir->interner.t_unit);
            cx->in_loop = old_loop;
            ty = cx->thir->interner.t_unit;
            break;
        }
        case AX_HIR_EXPR_JUMP: {
            if (expr->jump.jump_kind == AX_JUMP_RETURN) {
                if (expr->jump.expr) {
                    check_expr(cx, expr->jump.expr, cx->return_type);
                } else {
                    if (!unify_ty(cx, cx->thir->interner.t_unit, cx->return_type)) {
                        type_error(cx, expr->span, AX_TYPE_MISMATCH);
                    }
                }
                ty = cx->thir->interner.t_never;
            } else {
                ty = cx->thir->interner.t_never;
            }
            break;
        }
        case AX_HIR_EXPR_CALL: {
            TypeId callee_ty = check_expr(cx, expr->call.callee, TypeId_none());
            callee_ty = resolve_ty(cx, callee_ty);
            const AxType *ct = ax_type_get(&cx->thir->interner, callee_ty);
            if (ct->kind != AX_TY_FN && ct->kind != AX_TY_ERROR) {
                type_error(cx, expr->call.callee->span, AX_TYPE_NOT_CALLABLE);
                ty = cx->thir->interner.t_error;
                break;
            }
            if (ct->kind == AX_TY_ERROR) {
                ty = cx->thir->interner.t_error;
                for (const AxHirExpr *a = expr->call.args; a; a = a->next) {
                    check_expr(cx, a, TypeId_none());
                }
                break;
            }
            size_t argc = 0;
            for (const AxHirExpr *a = expr->call.args; a; a = a->next) argc++;
            if (argc != ct->fn.param_count) {
                type_error(cx, expr->call.callee->span, AX_TYPE_ARG_COUNT);
                ty = cx->thir->interner.t_error;
            } else {
                size_t i = 0;
                for (const AxHirExpr *a = expr->call.args; a; a = a->next) {
                    TypeId arg_ty = check_expr(cx, a, ct->fn.param_types[i]);
                    if (!unify_ty(cx, arg_ty, ct->fn.param_types[i])) {
                        type_error(cx, a->span, AX_TYPE_MISMATCH);
                    }
                    i++;
                }
                ty = ct->fn.ret_type;
            }
            break;
        }
        case AX_HIR_EXPR_BINARY: {
            TypeId left_ty = check_expr(cx, expr->binary.left, TypeId_none());
            TypeId right_ty = check_expr(cx, expr->binary.right, left_ty);
            AxAstBinOp op = expr->binary.op;
            if (op == AX_BINOP_LOGAND || op == AX_BINOP_LOGOR) {
                if (!unify_ty(cx, left_ty, cx->thir->interner.t_bool)) type_error(cx, expr->binary.left->span, AX_TYPE_MISMATCH);
                if (!unify_ty(cx, right_ty, cx->thir->interner.t_bool)) type_error(cx, expr->binary.right->span, AX_TYPE_MISMATCH);
                ty = cx->thir->interner.t_bool;
            } else if (op == AX_BINOP_EQ || op == AX_BINOP_NE) {
                if (!unify_ty(cx, left_ty, right_ty)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                left_ty = resolve_ty(cx, left_ty);
                const AxType *lt = ax_type_get(&cx->thir->interner, left_ty);
                if (lt->kind != AX_TY_INT_VAR && !ax_type_is_int(left_ty, &cx->thir->interner) && lt->kind != AX_TY_BOOL && lt->kind != AX_TY_CHAR && lt->kind != AX_TY_ERROR) {
                    type_error(cx, expr->binary.left->span, AX_TYPE_MISMATCH);
                }
                ty = cx->thir->interner.t_bool;
            } else if (op == AX_BINOP_LT || op == AX_BINOP_LE || op == AX_BINOP_GT || op == AX_BINOP_GE) {
                if (!unify_ty(cx, left_ty, right_ty)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                left_ty = resolve_ty(cx, left_ty);
                const AxType *lt = ax_type_get(&cx->thir->interner, left_ty);
                if (lt->kind != AX_TY_INT_VAR && !ax_type_is_int(left_ty, &cx->thir->interner) && lt->kind != AX_TY_CHAR && lt->kind != AX_TY_ERROR) {
                    type_error(cx, expr->binary.left->span, AX_TYPE_MISMATCH);
                }
                ty = cx->thir->interner.t_bool;
            } else if (op == AX_BINOP_ADD || op == AX_BINOP_SUB || op == AX_BINOP_MUL || op == AX_BINOP_DIV || op == AX_BINOP_REM) {
                if (!unify_ty(cx, left_ty, right_ty)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                left_ty = resolve_ty(cx, left_ty);
                const AxType *lt = ax_type_get(&cx->thir->interner, left_ty);
                if (lt->kind != AX_TY_INT_VAR && !ax_type_is_int(left_ty, &cx->thir->interner) && lt->kind != AX_TY_ERROR) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                ty = left_ty;
            } else if (op == AX_BINOP_SHL || op == AX_BINOP_SHR) {
                left_ty = resolve_ty(cx, left_ty);
                right_ty = resolve_ty(cx, right_ty);
                const AxType *lt = ax_type_get(&cx->thir->interner, left_ty);
                const AxType *rt = ax_type_get(&cx->thir->interner, right_ty);
                if (lt->kind != AX_TY_INT_VAR && !ax_type_is_int(left_ty, &cx->thir->interner) && lt->kind != AX_TY_ERROR) {
                    type_error(cx, expr->binary.left->span, AX_TYPE_MISMATCH);
                }
                if (rt->kind != AX_TY_INT_VAR && !ax_type_is_int(right_ty, &cx->thir->interner) && rt->kind != AX_TY_ERROR) {
                    type_error(cx, expr->binary.right->span, AX_TYPE_MISMATCH);
                }
                ty = left_ty;
            } else if (op == AX_BINOP_BITAND || op == AX_BINOP_BITOR || op == AX_BINOP_BITXOR) {
                if (!unify_ty(cx, left_ty, right_ty)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                left_ty = resolve_ty(cx, left_ty);
                const AxType *lt = ax_type_get(&cx->thir->interner, left_ty);
                if (lt->kind != AX_TY_INT_VAR && !ax_type_is_int(left_ty, &cx->thir->interner) && lt->kind != AX_TY_BOOL && lt->kind != AX_TY_ERROR) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                ty = left_ty;
            }
            break;
        }
        case AX_HIR_EXPR_UNARY: {
            TypeId inner_ty = check_expr(cx, expr->unary.expr, TypeId_none());
            if (expr->unary.op == AX_UNOP_NOT) {
                if (!unify_ty(cx, inner_ty, cx->thir->interner.t_bool)) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                ty = cx->thir->interner.t_bool;
            } else if (expr->unary.op == AX_UNOP_NEG) {
                inner_ty = resolve_ty(cx, inner_ty);
                const AxType *it = ax_type_get(&cx->thir->interner, inner_ty);
                if (it->kind == AX_TY_INT_VAR || ax_type_is_signed(inner_ty, &cx->thir->interner)) {
                    // ok
                } else if (ax_type_is_unsigned(inner_ty, &cx->thir->interner)) {
                    type_error(cx, expr->span, AX_TYPE_NEG_UNSIGNED);
                } else if (it->kind != AX_TY_ERROR) {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
                ty = inner_ty;
            } else if (expr->unary.op == AX_UNOP_DEREF) {
                ty = type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
            }
            break;
        }
        case AX_HIR_EXPR_CAST: {
            TypeId src_ty = check_expr(cx, expr->cast.expr, TypeId_none());
            TypeId dest_ty = hir_type_to_typeid(cx, expr->cast.type);
            src_ty = resolve_ty(cx, src_ty);
            dest_ty = resolve_ty(cx, dest_ty);
            if (TypeId_eq(src_ty, dest_ty)) {
                // ok
            } else if (ax_type_is_int(src_ty, &cx->thir->interner) || src_ty.v == cx->thir->interner.t_bool.v || src_ty.v == cx->thir->interner.t_char.v) {
                if (ax_type_is_int(dest_ty, &cx->thir->interner)) {
                    // ok
                } else {
                    type_error(cx, expr->span, AX_TYPE_MISMATCH);
                }
            } else if (src_ty.v != cx->thir->interner.t_error.v && dest_ty.v != cx->thir->interner.t_error.v) {
                type_error(cx, expr->span, AX_TYPE_MISMATCH);
            }
            ty = dest_ty;
            break;
        }
        default:
            ty = type_error(cx, expr->span, AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP);
            break;
    }
    
    if (TypeId_is_some(expected)) {
        if (!unify_ty(cx, ty, expected)) {
            type_error(cx, expr->span, AX_TYPE_MISMATCH);
        }
    }
    
    AxExprTypeMap_insert(&cx->thir->expr_types, expr, ty);
    return ty;
}

static TypeId check_block(TypeckCtx *cx, const AxHirBlock *block, TypeId expected) {
    TypeId ty = cx->thir->interner.t_unit;
    bool diverges = false;
    for (const AxHirStmt *s = block->stmts; s; s = s->next) {
        if (s->kind == AX_HIR_STMT_LET) {
            TypeId declared = hir_type_to_typeid(cx, s->let.type);
            if (s->let.expr) {
                TypeId init = check_expr(cx, s->let.expr, declared);
                if (TypeId_eq(resolve_ty(cx, init), cx->thir->interner.t_never)) diverges = true;
                if (TypeId_is_some(declared)) {
                    if (!unify_ty(cx, init, declared)) {
                        type_error(cx, s->let.expr->span, AX_TYPE_MISMATCH);
                    }
                } else {
                    declared = init;
                }
            } else {
                if (TypeId_is_none(declared)) {
                    type_error(cx, s->let.pat->span, AX_TYPE_UNKNOWN);
                    declared = cx->thir->interner.t_error;
                }
            }
            check_pat(cx, s->let.pat, declared);
        } else if (s->kind == AX_HIR_STMT_ASSIGN) {
            TypeId left = check_expr(cx, s->assign.left, TypeId_none());
            TypeId right = check_expr(cx, s->assign.right, left);
            if (TypeId_eq(resolve_ty(cx, right), cx->thir->interner.t_never)) diverges = true;
            ty = cx->thir->interner.t_unit;
        } else if (s->kind == AX_HIR_STMT_EXPR) {
            TypeId ety = check_expr(cx, s->expr_stmt.expr, TypeId_none());
            if (TypeId_eq(resolve_ty(cx, ety), cx->thir->interner.t_never)) diverges = true;
            if (s->expr_stmt.has_semi) {
                ty = cx->thir->interner.t_unit;
            } else {
                ty = ety;
            }
        }
    }
    
    if (diverges) {
        ty = cx->thir->interner.t_never;
    }
    
    if (TypeId_is_some(expected)) {
        if (!unify_ty(cx, ty, expected)) {
            // If the block is the body of a function, and it reaches the end with wrong type
            if (TypeId_eq(resolve_ty(cx, ty), cx->thir->interner.t_unit)) {
                type_error(cx, block->span, AX_TYPE_RETURN);
            } else {
                type_error(cx, block->span, AX_TYPE_MISMATCH);
            }
        }
    }
    
    return ty;
}

