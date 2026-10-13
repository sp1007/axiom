#include "own/unsafe/unsafe.h"
#include <string.h>

typedef struct {
    const AxHir *hir;
    const AxThir *thir;
    AxDiagSink *sink;
    const StrInterner *interner;
    int unsafe_depth;
} UnsafeChecker;

static void report_unsafe_required(UnsafeChecker *c, Span span) {
    AxDiagnostic d = {0};
    d.code = AX_UNSAFE_REQUIRED;
    d.severity = AX_DIAG_ERROR;
    d.message = ax_diag_code_default_message(AX_UNSAFE_REQUIRED);
    d.primary = span;
    ax_diag_sink_report(c->sink, &d);
}

static TypeId get_expr_ty(UnsafeChecker *c, const AxHirExpr *expr) {
    if (!expr) return (TypeId){0};
    const TypeId *ty = AxExprTypeMap_get(&c->thir->expr_types, (AxHirExpr*)expr);
    return ty ? *ty : (TypeId){0};
}

static void check_block(UnsafeChecker *c, const AxHirBlock *block);
static void check_expr(UnsafeChecker *c, const AxHirExpr *expr);

static void check_stmt(UnsafeChecker *c, const AxHirStmt *stmt) {
    if (!stmt) return;
    switch (stmt->kind) {
        case AX_HIR_STMT_LET:
            if (stmt->let.expr) {
                check_expr(c, stmt->let.expr);
            }
            break;
        case AX_HIR_STMT_ASSIGN:
            check_expr(c, stmt->assign.right);
            check_expr(c, stmt->assign.left);
            break;
        case AX_HIR_STMT_EXPR:
            check_expr(c, stmt->expr_stmt.expr);
            break;
        default:
            break;
    }
}

static void check_block(UnsafeChecker *c, const AxHirBlock *block) {
    if (!block) return;
    for (const AxHirStmt *s = block->stmts; s; s = s->next) {
        check_stmt(c, s);
    }
}

static bool is_callee_unsafe(UnsafeChecker *c, const AxHirExpr *callee) {
    if (!callee) return false;
    TypeId cty = get_expr_ty(c, callee);
    const AxType *ft = (cty.v != 0) ? ax_type_get(&c->thir->interner, cty) : NULL;
    if (ft) {
        if (ft->kind == AX_TY_BUILTIN_ADDRESS_OF ||
            ft->kind == AX_TY_BUILTIN_ADDRESS_OF_MUT ||
            ft->kind == AX_TY_BUILTIN_PTR_ADD ||
            ft->kind == AX_TY_BUILTIN_PTR_SUB ||
            ft->kind == AX_TY_BUILTIN_DROP_IN_PLACE ||
            ft->kind == AX_TY_BUILTIN_PTR_COPY ||
            ft->kind == AX_TY_BUILTIN_PTR_COPY_NONOVERLAPPING ||
            ft->kind == AX_TY_BUILTIN_PTR_WRITE_BYTES) {
            return true;
        }
        if (ft->kind == AX_TY_FN && ft->fn.is_unsafe) {
            return true;
        }
    }

    if (callee->kind == AX_HIR_EXPR_PATH && callee->path.path.name.v != 0) {
        StrId name = callee->path.path.name;
        for (const AxHirItem *it = c->hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_FN && it->fn.name.v == name.v) {
                if (it->fn.is_unsafe) return true;
            }
            if (it->kind == AX_HIR_ITEM_IMPL) {
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == name.v) {
                        if (m->fn.is_unsafe) return true;
                    }
                }
            }
        }
    }
    return false;
}

static void check_expr(UnsafeChecker *c, const AxHirExpr *expr) {
    if (!expr) return;

    switch (expr->kind) {
        case AX_HIR_EXPR_UNSAFE: {
            c->unsafe_depth++;
            check_block(c, &expr->unsafe_block.block);
            c->unsafe_depth--;
            break;
        }
        case AX_HIR_EXPR_BLOCK:
            check_block(c, &expr->block.block);
            break;
        case AX_HIR_EXPR_CLOSURE: {
            int saved = c->unsafe_depth;
            c->unsafe_depth = 0; // Closures do not inherit unsafe context
            check_expr(c, expr->closure.body);
            c->unsafe_depth = saved;
            break;
        }
        case AX_HIR_EXPR_UNARY: {
            if (expr->unary.op == AX_UNOP_DEREF) {
                TypeId op_ty = get_expr_ty(c, expr->unary.expr);
                const AxType *t = (op_ty.v != 0) ? ax_type_get(&c->thir->interner, op_ty) : NULL;
                if (t && t->kind == AX_TY_PTR) {
                    if (c->unsafe_depth == 0) {
                        report_unsafe_required(c, expr->span);
                    }
                }
            }
            check_expr(c, expr->unary.expr);
            break;
        }
        case AX_HIR_EXPR_FIELD: {
            TypeId base_ty = get_expr_ty(c, expr->field.base);
            const AxType *t = (base_ty.v != 0) ? ax_type_get(&c->thir->interner, base_ty) : NULL;
            if (t && t->kind == AX_TY_PTR) {
                if (c->unsafe_depth == 0) {
                    report_unsafe_required(c, expr->span);
                }
            }
            check_expr(c, expr->field.base);
            break;
        }
        case AX_HIR_EXPR_BINARY: {
            if (expr->binary.op == AX_BINOP_ADD || expr->binary.op == AX_BINOP_SUB) {
                TypeId lty = get_expr_ty(c, expr->binary.left);
                TypeId rty = get_expr_ty(c, expr->binary.right);
                const AxType *lt = (lty.v != 0) ? ax_type_get(&c->thir->interner, lty) : NULL;
                const AxType *rt = (rty.v != 0) ? ax_type_get(&c->thir->interner, rty) : NULL;
                if ((lt && lt->kind == AX_TY_PTR) || (rt && rt->kind == AX_TY_PTR)) {
                    if (c->unsafe_depth == 0) {
                        report_unsafe_required(c, expr->span);
                    }
                }
            }
            check_expr(c, expr->binary.left);
            check_expr(c, expr->binary.right);
            break;
        }
        case AX_HIR_EXPR_CALL: {
            if (is_callee_unsafe(c, expr->call.callee)) {
                if (c->unsafe_depth == 0) {
                    report_unsafe_required(c, expr->span);
                }
            }
            check_expr(c, expr->call.callee);
            for (const AxHirExpr *arg = expr->call.args; arg; arg = arg->next) {
                check_expr(c, arg);
            }
            break;
        }
        case AX_HIR_EXPR_METHOD_CALL: {
            // Check if method is unsafe
            const AxHirItem **method_item_ptr = AxExprMethodMap_get(&c->thir->expr_methods, (AxHirExpr*)expr);
            if (method_item_ptr && *method_item_ptr && (*method_item_ptr)->fn.is_unsafe) {
                if (c->unsafe_depth == 0) {
                    report_unsafe_required(c, expr->span);
                }
            }
            check_expr(c, expr->method_call.receiver);
            for (const AxHirExpr *arg = expr->method_call.args; arg; arg = arg->next) {
                check_expr(c, arg);
            }
            break;
        }
        case AX_HIR_EXPR_IF:
            check_expr(c, expr->if_expr.cond);
            check_block(c, &expr->if_expr.block);
            if (expr->if_expr.else_branch) {
                check_expr(c, expr->if_expr.else_branch);
            }
            break;
        case AX_HIR_EXPR_MATCH: {
            check_expr(c, expr->match.expr);
            for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
                if (arm->guard) check_expr(c, arm->guard);
                check_expr(c, arm->body);
            }
            break;
        }
        case AX_HIR_EXPR_LOOP:
            check_block(c, &expr->loop.block);
            break;
        case AX_HIR_EXPR_WHILE:
            check_expr(c, expr->while_expr.cond);
            check_block(c, &expr->while_expr.block);
            break;
        case AX_HIR_EXPR_FOR:
            check_expr(c, expr->for_expr.iter);
            check_block(c, &expr->for_expr.block);
            break;
        case AX_HIR_EXPR_TUPLE:
            for (const AxHirExpr *e = expr->tuple.elems; e; e = e->next) {
                check_expr(c, e);
            }
            break;
        case AX_HIR_EXPR_ARRAY:
            for (const AxHirExpr *e = expr->array.elems; e; e = e->next) {
                check_expr(c, e);
            }
            break;
        case AX_HIR_EXPR_STRUCT:
            for (const AxHirFieldInit *f = expr->struct_lit.fields; f; f = f->next) {
                check_expr(c, f->expr);
            }
            break;
        case AX_HIR_EXPR_VIEW:
            check_expr(c, expr->view.expr);
            break;
        case AX_HIR_EXPR_CAST:
            check_expr(c, expr->cast.expr);
            break;
        case AX_HIR_EXPR_INDEX:
            check_expr(c, expr->index.base);
            check_expr(c, expr->index.arg);
            break;
        case AX_HIR_EXPR_TRY:
            check_expr(c, expr->try_expr.expr);
            break;
        case AX_HIR_EXPR_AWAIT:
            check_expr(c, expr->await_expr.expr);
            break;
        case AX_HIR_EXPR_JUMP:
            if (expr->jump.expr) check_expr(c, expr->jump.expr);
            break;
        case AX_HIR_EXPR_RANGE:
            if (expr->range.start) check_expr(c, expr->range.start);
            if (expr->range.end) check_expr(c, expr->range.end);
            break;
        default:
            break;
    }
}

void ax_unsafe_check(const AxHir *hir, const AxThir *thir, AxDiagSink *sink, const StrInterner *interner) {
    if (!hir || !thir || !sink) return;
    UnsafeChecker c = {
        .hir = hir,
        .thir = thir,
        .sink = sink,
        .interner = interner,
        .unsafe_depth = 0
    };

    for (const AxHirItem *it = hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.body) {
            c.unsafe_depth = it->fn.is_unsafe ? 1 : 0;
            check_block(&c, it->fn.body);
        } else if (it->kind == AX_HIR_ITEM_IMPL) {
            for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                if (m->kind == AX_HIR_ITEM_FN && m->fn.body) {
                    c.unsafe_depth = m->fn.is_unsafe ? 1 : 0;
                    check_block(&c, m->fn.body);
                }
            }
        } else if (it->kind == AX_HIR_ITEM_STATIC && it->static_decl.expr) {
            c.unsafe_depth = it->static_decl.is_unsafe ? 1 : 0;
            check_expr(&c, it->static_decl.expr);
        } else if (it->kind == AX_HIR_ITEM_CONST && it->const_decl.expr) {
            c.unsafe_depth = 0;
            check_expr(&c, it->const_decl.expr);
        }
    }
}
