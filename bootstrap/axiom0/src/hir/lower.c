#include "hir/lower.h"
#include <string.h>

typedef struct LowerCtx {
    AxArena *arena;
    const AxResolveMap *rmap;
    AxDiagSink *sink;
} LowerCtx;

static void emit_not_supported(LowerCtx *ctx, Span span) {
    AxDiagnostic d = {0};
    d.code = AX_NAME_NOT_YET_SUPPORTED;
    d.severity = ax_diag_code_severity(d.code);
    d.message = ax_diag_code_default_message(d.code);
    d.primary = span;
    ax_diag_sink_report(ctx->sink, &d);
}

static AxSymbolId get_symbol(LowerCtx *ctx, const void *node) {
    AxSymbolId *sym = AxNodeMap_get(&ctx->rmap->node_map, node);
    if (sym) return *sym;
    AxSymbolId zero = {0};
    return zero;
}

static AxHirPath lower_path(LowerCtx *ctx, const AxAstTypePathSegment *seg) {
    AxHirPath p = {0};
    if (!seg) return p;
    p.span = seg->span; // span of the first segment
    const AxAstTypePathSegment *last = seg;
    while (last->next) {
        last = last->next;
        // span should cover the whole path?
        p.span.end = last->span.end;
    }
    p.symbol = get_symbol(ctx, last);
    // TODO: generic args on path. We just take them from the last segment for now.
    // p.generic_args = lower_generic_args(ctx, last->generic_args);
    return p;
}

// Forward decls
static AxHirExpr *lower_expr(LowerCtx *ctx, const AxAstExpr *e);
static AxHirPat *lower_pat(LowerCtx *ctx, const AxAstPat *p);
static AxHirType *lower_type(LowerCtx *ctx, const AxAstType *t);
static AxHirStmt *lower_stmt(LowerCtx *ctx, const AxAstStmt *s);
static AxHirBlock lower_block(LowerCtx *ctx, const AxAstBlock *b);
static AxHirGenericArgs *lower_generic_args(LowerCtx *ctx, const AxAstGenericArgs *g);
static AxHirAttr *lower_attrs(LowerCtx *ctx, const AxAstAttr *a);
static AxHirVis lower_vis(LowerCtx *ctx, const AxAstVis *v);


static AxHirGenericArgs *lower_generic_args(LowerCtx *ctx, const AxAstGenericArgs *g) {
    if (!g) return NULL;
    AxHirGenericArgs *hg = ax_arena_alloc(ctx->arena, sizeof(AxHirGenericArgs), 8);
    hg->span = g->span;
    AxHirGenericArg **tail = &hg->args;
    for (AxAstGenericArg *a = g->args; a; a = a->next) {
        AxHirGenericArg *ha = ax_arena_alloc(ctx->arena, sizeof(AxHirGenericArg), 8);
        ha->span = a->span;
        ha->name = a->name;
        ha->type = lower_type(ctx, a->type);
        *tail = ha;
        tail = &ha->next;
    }
    *tail = NULL;
    return hg;
}

static AxHirGenericParams *lower_generic_params(LowerCtx *ctx, const AxAstGenericParams *g) {
    if (!g) return NULL;
    AxHirGenericParams *hg = ax_arena_alloc(ctx->arena, sizeof(AxHirGenericParams), 8);
    hg->span = g->span;
    AxHirGenericParam **tail = &hg->params;
    for (AxAstGenericParam *a = g->params; a; a = a->next) {
        AxHirGenericParam *ha = ax_arena_alloc(ctx->arena, sizeof(AxHirGenericParam), 8);
        ha->span = a->span;
        ha->name = a->name;
        ha->bounds = lower_type(ctx, a->bounds);
        *tail = ha;
        tail = &ha->next;
    }
    *tail = NULL;
    return hg;
}

static AxHirWhereClause *lower_where_clause(LowerCtx *ctx, const AxAstWhereClause *w) {
    if (!w) return NULL;
    AxHirWhereClause *hw = ax_arena_alloc(ctx->arena, sizeof(AxHirWhereClause), 8);
    hw->span = w->span;
    AxHirWherePred **tail = &hw->preds;
    for (AxAstWherePred *p = w->preds; p; p = p->next) {
        AxHirWherePred *hp = ax_arena_alloc(ctx->arena, sizeof(AxHirWherePred), 8);
        hp->span = p->span;
        hp->type = lower_type(ctx, p->type);
        hp->bounds = lower_type(ctx, p->bounds);
        *tail = hp;
        tail = &hp->next;
    }
    *tail = NULL;
    return hw;
}

static AxHirAttr *lower_attrs(LowerCtx *ctx, const AxAstAttr *a) {
    AxHirAttr *head = NULL;
    AxHirAttr **tail = &head;
    for (; a; a = a->next) {
        AxHirAttr *ha = ax_arena_alloc(ctx->arena, sizeof(AxHirAttr), 8);
        ha->span = a->span;
        ha->name = a->name;
        AxHirAttrArg **arg_tail = &ha->args;
        for (AxAstAttrArg *arg = a->args; arg; arg = arg->next) {
            AxHirAttrArg *harg = ax_arena_alloc(ctx->arena, sizeof(AxHirAttrArg), 8);
            harg->span = arg->span;
            harg->name = arg->name;
            harg->expr = lower_expr(ctx, arg->expr);
            *arg_tail = harg;
            arg_tail = &harg->next;
        }
        *arg_tail = NULL;
        *tail = ha;
        tail = &ha->next;
    }
    *tail = NULL;
    return head;
}

static AxHirVis lower_vis(LowerCtx *ctx, const AxAstVis *v) {
    (void)ctx;
    AxHirVis hv = {0};
    if (v) {
        hv.span = v->span;
        hv.kind = (AxHirVisKind)v->kind; // they match exactly
    }
    return hv;
}

static AxHirType *lower_type(LowerCtx *ctx, const AxAstType *t) {
    AxHirType *head = NULL;
    AxHirType **tail = &head;
    for (; t; t = t->next) {
        AxHirType *ht = ax_arena_alloc(ctx->arena, sizeof(AxHirType), 8);
        ht->span = t->span;
        switch (t->kind) {
            case AX_TYPE_ERROR: ht->kind = AX_HIR_TYPE_ERROR; break;
            case AX_TYPE_PATH:
                ht->kind = AX_HIR_TYPE_PATH;
                ht->path.path = lower_path(ctx, t->path.segments);
                
                // Generic args on type path
                const AxAstTypePathSegment *last = t->path.segments;
                while (last && last->next) last = last->next;
                if (last) ht->path.path.generic_args = lower_generic_args(ctx, last->generic_args);
                break;
            case AX_TYPE_TUPLE:
                ht->kind = AX_HIR_TYPE_TUPLE;
                ht->tuple.elem_types = lower_type(ctx, t->tuple.elem_types);
                break;
            case AX_TYPE_ARRAY:
                ht->kind = AX_HIR_TYPE_ARRAY;
                ht->array.count = lower_expr(ctx, t->array.count);
                ht->array.elem = lower_type(ctx, t->array.elem);
                break;
            case AX_TYPE_SLICE:
                ht->kind = AX_HIR_TYPE_SLICE;
                ht->slice.elem = lower_type(ctx, t->slice.elem);
                break;
            case AX_TYPE_VIEW:
                ht->kind = AX_HIR_TYPE_VIEW;
                ht->view.is_mut = t->view.is_mut;
                ht->view.elem = lower_type(ctx, t->view.elem);
                break;
            case AX_TYPE_PTR:
                ht->kind = AX_HIR_TYPE_PTR;
                ht->ptr.is_mut = t->ptr.is_mut;
                ht->ptr.elem = lower_type(ctx, t->ptr.elem);
                break;
            case AX_TYPE_FN:
                ht->kind = AX_HIR_TYPE_FN;
                ht->fn.is_unsafe = t->fn.is_unsafe;
                ht->fn.abi = t->fn.abi;
                ht->fn.param_types = lower_type(ctx, t->fn.param_types);
                ht->fn.ret_type = lower_type(ctx, t->fn.ret_type);
                break;
            case AX_TYPE_DYN:
                ht->kind = AX_HIR_TYPE_DYN;
                ht->dyn.bounds = lower_type(ctx, t->dyn.bounds);
                break;
        }
        *tail = ht;
        tail = &ht->next;
    }
    *tail = NULL;
    return head;
}

static AxHirPat *lower_pat(LowerCtx *ctx, const AxAstPat *p) {
    AxHirPat *head = NULL;
    AxHirPat **tail = &head;
    for (; p; p = p->next) {
        AxHirPat *hp = ax_arena_alloc(ctx->arena, sizeof(AxHirPat), 8);
        hp->span = p->span;
        switch (p->kind) {
            case AX_PAT_ERROR: hp->kind = AX_HIR_PAT_ERROR; break;
            case AX_PAT_WILDCARD: hp->kind = AX_HIR_PAT_WILDCARD; break;
            case AX_PAT_RANGE:
                hp->kind = AX_HIR_PAT_RANGE;
                hp->range.is_inclusive = p->range.is_inclusive;
                hp->range.start = lower_pat(ctx, p->range.start);
                hp->range.end = lower_pat(ctx, p->range.end);
                break;
            case AX_PAT_LITERAL:
                hp->kind = AX_HIR_PAT_LITERAL;
                hp->literal.tok = p->literal.tok;
                hp->literal.is_negated = p->literal.is_negated;
                break;
            case AX_PAT_BINDING:
                hp->kind = AX_HIR_PAT_BINDING;
                hp->binding.is_mut = p->binding.is_mut;
                hp->binding.symbol = get_symbol(ctx, p); // pattern node itself gets the symbol
                break;
            case AX_PAT_PATH:
                hp->kind = AX_HIR_PAT_PATH;
                hp->path.path = lower_path(ctx, p->path.segments);
                hp->path.payload = lower_pat(ctx, p->path.payload);
                break;
            case AX_PAT_TUPLE:
                hp->kind = AX_HIR_PAT_TUPLE;
                hp->tuple.elems = lower_pat(ctx, p->tuple.elems);
                break;
            case AX_PAT_OR:
                hp->kind = AX_HIR_PAT_OR;
                hp->or_pat.pats = lower_pat(ctx, p->or_pat.pats);
                break;
            case AX_PAT_STRUCT:
                hp->kind = AX_HIR_PAT_STRUCT;
                hp->struct_pat.path = lower_path(ctx, p->struct_pat.segments);
                hp->struct_pat.has_rest = p->struct_pat.has_rest;
                AxHirPatField **ftail = &hp->struct_pat.fields;
                for (AxAstPatField *f = p->struct_pat.fields; f; f = f->next) {
                    AxHirPatField *hf = ax_arena_alloc(ctx->arena, sizeof(AxHirPatField), 8);
                    hf->span = f->span;
                    hf->name = f->name;
                    hf->pat = lower_pat(ctx, f->pat); // could be NULL
                    *ftail = hf;
                    ftail = &hf->next;
                }
                *ftail = NULL;
                break;
        }
        *tail = hp;
        tail = &hp->next;
    }
    *tail = NULL;
    return head;
}

static AxHirExpr *lower_postfix(LowerCtx *ctx, const AxAstExpr *e) {
    AxHirExpr *head = lower_expr(ctx, e->postfix.head);
    
    for (AxAstPostfixSeg *seg = e->postfix.segments; seg; seg = seg->next) {
        AxHirExpr *next = ax_arena_alloc(ctx->arena, sizeof(AxHirExpr), 8);
        next->span = seg->span;
        
        switch (seg->kind) {
            case AX_POSTFIX_FIELD:
                next->kind = AX_HIR_EXPR_FIELD;
                next->field.base = head;
                next->field.name = seg->field.name;
                next->field.generic_args = lower_generic_args(ctx, seg->field.generic_args);
                break;
            case AX_POSTFIX_TUPLE_INDEX:
                next->kind = AX_HIR_EXPR_TUPLE_INDEX;
                next->tuple_index.base = head;
                next->tuple_index.tuple_index = seg->tuple_index;
                break;
            case AX_POSTFIX_CALL:
                if (head->kind == AX_HIR_EXPR_FIELD) {
                    next->kind = AX_HIR_EXPR_METHOD_CALL;
                    next->method_call.receiver = head->field.base;
                    next->method_call.method_name = head->field.name;
                    next->method_call.generic_args = head->field.generic_args;
                    next->method_call.args = lower_expr(ctx, seg->call.args);
                } else {
                    next->kind = AX_HIR_EXPR_CALL;
                    next->call.callee = head;
                    next->call.args = lower_expr(ctx, seg->call.args);
                }
                break;
            case AX_POSTFIX_INDEX:
                next->kind = AX_HIR_EXPR_INDEX;
                next->index.base = head;
                next->index.arg = lower_expr(ctx, seg->index.arg);
                break;
            case AX_POSTFIX_TRY:
                emit_not_supported(ctx, seg->span);
                next->kind = AX_HIR_EXPR_ERROR;
                break;
            case AX_POSTFIX_AWAIT:
                emit_not_supported(ctx, seg->span);
                next->kind = AX_HIR_EXPR_ERROR;
                break;
            case AX_POSTFIX_ARROW:
                emit_not_supported(ctx, seg->span);
                next->kind = AX_HIR_EXPR_ERROR;
                break;
        }
        head = next;
    }
    return head;
}

static AxHirMatchArm *lower_match_arms(LowerCtx *ctx, const AxAstMatchArm *a) {
    AxHirMatchArm *head = NULL;
    AxHirMatchArm **tail = &head;
    for (; a; a = a->next) {
        AxHirMatchArm *ha = ax_arena_alloc(ctx->arena, sizeof(AxHirMatchArm), 8);
        ha->span = a->span;
        ha->pat = lower_pat(ctx, a->pat);
        ha->guard = lower_expr(ctx, a->guard);
        ha->body = lower_expr(ctx, a->body);
        *tail = ha;
        tail = &ha->next;
    }
    *tail = NULL;
    return head;
}

static AxHirExpr *lower_expr(LowerCtx *ctx, const AxAstExpr *e) {
    AxHirExpr *head = NULL;
    AxHirExpr **tail = &head;
    for (; e; e = e->next) {
        AxHirExpr *he = ax_arena_alloc(ctx->arena, sizeof(AxHirExpr), 8);
        he->span = e->span;
        switch (e->kind) {
            case AX_EXPR_ERROR: he->kind = AX_HIR_EXPR_ERROR; break;
            case AX_EXPR_LITERAL: he->kind = AX_HIR_EXPR_LITERAL; he->literal = e->literal; break;
            case AX_EXPR_PATH:
                he->kind = AX_HIR_EXPR_PATH;
                he->path.path = lower_path(ctx, e->path.segments);
                
                const AxAstTypePathSegment *last = e->path.segments;
                while (last && last->next) last = last->next;
                if (last) he->path.path.generic_args = lower_generic_args(ctx, last->generic_args);
                break;
            case AX_EXPR_PAREN:
                // Drop paren, just lower inner expr, but keep the paren's span maybe?
                // Actually it's cleaner to just return the inner lowered expr directly.
                // Wait, since we are doing a linked list of exprs, we shouldn't just skip `he`.
                // Let's just return inner, but set its next to whatever this one would have.
                // Actually in Axiom Exprs are usually single unless it's an arg list.
                {
                    AxHirExpr *inner = lower_expr(ctx, e->paren.expr);
                    if (inner) {
                        *tail = inner;
                        while(inner->next) inner = inner->next;
                        tail = &inner->next;
                    }
                    continue; // Skip the rest of loop to not advance `tail` wrongly
                }
                break;
            case AX_EXPR_ARRAY:
                he->kind = AX_HIR_EXPR_ARRAY;
                he->array.elems = lower_expr(ctx, e->array.elems);
                he->array.count = lower_expr(ctx, e->array.count);
                break;
            case AX_EXPR_STRUCT:
                he->kind = AX_HIR_EXPR_STRUCT;
                he->struct_lit.path = lower_path(ctx, e->struct_lit.segments);
                AxHirFieldInit **fitail = &he->struct_lit.fields;
                for (AxAstFieldInit *f = e->struct_lit.fields; f; f = f->next) {
                    AxHirFieldInit *hf = ax_arena_alloc(ctx->arena, sizeof(AxHirFieldInit), 8);
                    hf->span = f->span;
                    hf->name = f->name;
                    hf->expr = lower_expr(ctx, f->expr);
                    *fitail = hf;
                    fitail = &hf->next;
                }
                *fitail = NULL;
                break;
            case AX_EXPR_BLOCK:
                he->kind = AX_HIR_EXPR_BLOCK;
                he->block.block = lower_block(ctx, &e->block.block);
                break;
            case AX_EXPR_IF:
                he->kind = AX_HIR_EXPR_IF;
                he->if_expr.let_pat = lower_pat(ctx, e->if_expr.let_pat);
                he->if_expr.cond = lower_expr(ctx, e->if_expr.cond);
                he->if_expr.block = lower_block(ctx, &e->if_expr.block);
                
                AxHirExpr *else_branch = lower_expr(ctx, e->if_expr.else_branch);
                if (else_branch && else_branch->kind != AX_HIR_EXPR_BLOCK) {
                    AxHirExpr *block_wrap = ax_arena_alloc(ctx->arena, sizeof(AxHirExpr), 8);
                    block_wrap->kind = AX_HIR_EXPR_BLOCK;
                    block_wrap->span = else_branch->span;
                    
                    AxHirStmt *stmt = ax_arena_alloc(ctx->arena, sizeof(AxHirStmt), 8);
                    stmt->kind = AX_HIR_STMT_EXPR;
                    stmt->span = else_branch->span;
                    stmt->expr_stmt.expr = else_branch;
                    stmt->expr_stmt.has_semi = false;
                    
                    block_wrap->block.block.span = else_branch->span;
                    block_wrap->block.block.stmts = stmt;
                    
                    he->if_expr.else_branch = block_wrap;
                } else {
                    he->if_expr.else_branch = else_branch;
                }
                break;
            case AX_EXPR_MATCH:
                he->kind = AX_HIR_EXPR_MATCH;
                he->match.expr = lower_expr(ctx, e->match.expr);
                he->match.arms = lower_match_arms(ctx, e->match.arms);
                break;
            case AX_EXPR_LOOP:
                he->kind = AX_HIR_EXPR_LOOP;
                he->loop.label = e->loop.label;
                he->loop.block = lower_block(ctx, &e->loop.block);
                break;
            case AX_EXPR_WHILE:
                he->kind = AX_HIR_EXPR_WHILE;
                he->while_expr.label = e->while_expr.label;
                he->while_expr.let_pat = lower_pat(ctx, e->while_expr.let_pat);
                he->while_expr.cond = lower_expr(ctx, e->while_expr.cond);
                he->while_expr.block = lower_block(ctx, &e->while_expr.block);
                break;
            case AX_EXPR_FOR:
                he->kind = AX_HIR_EXPR_FOR;
                he->for_expr.label = e->for_expr.label;
                he->for_expr.pat = lower_pat(ctx, e->for_expr.pat);
                he->for_expr.iter = lower_expr(ctx, e->for_expr.iter);
                he->for_expr.block = lower_block(ctx, &e->for_expr.block);
                break;
            case AX_EXPR_UNSAFE:
                he->kind = AX_HIR_EXPR_UNSAFE;
                he->unsafe_block.block = lower_block(ctx, &e->unsafe_block.block);
                break;
            case AX_EXPR_VIEW:
                he->kind = AX_HIR_EXPR_VIEW;
                he->view.is_mut = e->view.is_mut;
                he->view.expr = lower_expr(ctx, e->view.expr);
                break;
            case AX_EXPR_COMPTIME:
                he->kind = AX_HIR_EXPR_COMPTIME;
                he->comptime.block = lower_block(ctx, &e->comptime.block);
                break;
            case AX_EXPR_JUMP:
                he->kind = AX_HIR_EXPR_JUMP;
                he->jump.jump_kind = e->jump.jump_kind;
                he->jump.label = e->jump.label;
                he->jump.expr = lower_expr(ctx, e->jump.expr);
                break;
            case AX_EXPR_CLOSURE:
                he->kind = AX_HIR_EXPR_CLOSURE;
                AxHirParam **ctail = &he->closure.params;
                for (AxAstParam *p = e->closure.params; p; p = p->next) {
                    AxHirParam *hp = ax_arena_alloc(ctx->arena, sizeof(AxHirParam), 8);
                    hp->span = p->span;
                    hp->is_mut = p->is_mut;
                    hp->symbol = get_symbol(ctx, p);
                    hp->type = lower_type(ctx, p->type);
                    *ctail = hp;
                    ctail = &hp->next;
                }
                *ctail = NULL;
                he->closure.ret_type = lower_type(ctx, e->closure.ret_type);
                he->closure.body = lower_expr(ctx, e->closure.body);
                break;
            case AX_EXPR_RANGE:
                he->kind = AX_HIR_EXPR_RANGE;
                he->range.is_inclusive = e->range.is_inclusive;
                he->range.start = lower_expr(ctx, e->range.start);
                he->range.end = lower_expr(ctx, e->range.end);
                break;
            case AX_EXPR_BINARY:
                he->kind = AX_HIR_EXPR_BINARY;
                he->binary.op = e->binary.op;
                he->binary.left = lower_expr(ctx, e->binary.left);
                he->binary.right = lower_expr(ctx, e->binary.right);
                break;
            case AX_EXPR_UNARY:
                he->kind = AX_HIR_EXPR_UNARY;
                he->unary.op = e->unary.op;
                he->unary.expr = lower_expr(ctx, e->unary.expr);
                break;
            case AX_EXPR_CAST:
                he->kind = AX_HIR_EXPR_CAST;
                he->cast.expr = lower_expr(ctx, e->cast.expr);
                he->cast.type = lower_type(ctx, e->cast.type);
                break;
            case AX_EXPR_POSTFIX:
                {
                    AxHirExpr *desugared = lower_postfix(ctx, e);
                    if (desugared) {
                        *tail = desugared;
                        while (desugared->next) desugared = desugared->next;
                        tail = &desugared->next;
                    }
                    continue;
                }
        }
        *tail = he;
        tail = &he->next;
    }
    *tail = NULL;
    return head;
}

static AxHirStmt *lower_stmt(LowerCtx *ctx, const AxAstStmt *s) {
    AxHirStmt *head = NULL;
    AxHirStmt **tail = &head;
    for (; s; s = s->next) {
        AxHirStmt *hs = ax_arena_alloc(ctx->arena, sizeof(AxHirStmt), 8);
        hs->span = s->span;
        switch (s->kind) {
            case AX_STMT_ERROR: hs->kind = AX_HIR_STMT_ERROR; break;
            case AX_STMT_LET:
                hs->kind = AX_HIR_STMT_LET;
                hs->let.pat = lower_pat(ctx, s->let.pat);
                hs->let.type = lower_type(ctx, s->let.type);
                hs->let.expr = lower_expr(ctx, s->let.expr);
                if (s->let.else_block) {
                    AxHirBlock *eb = ax_arena_alloc(ctx->arena, sizeof(AxHirBlock), 8);
                    *eb = lower_block(ctx, s->let.else_block);
                    hs->let.else_block = eb;
                }
                break;
            case AX_STMT_ASSIGN:
                hs->kind = AX_HIR_STMT_ASSIGN;
                hs->assign.left = lower_expr(ctx, s->assign.left);
                if (s->assign.op == AX_ASSIGN_EQ) {
                    hs->assign.right = lower_expr(ctx, s->assign.right);
                } else {
                    AxHirExpr *right = ax_arena_alloc(ctx->arena, sizeof(AxHirExpr), 8);
                    right->kind = AX_HIR_EXPR_BINARY;
                    right->span = s->span; // could use a better span if available
                    
                    AxAstBinOp binop = 0;
                    switch(s->assign.op) {
                        case AX_ASSIGN_ADD: binop = AX_BINOP_ADD; break;
                        case AX_ASSIGN_SUB: binop = AX_BINOP_SUB; break;
                        case AX_ASSIGN_MUL: binop = AX_BINOP_MUL; break;
                        case AX_ASSIGN_DIV: binop = AX_BINOP_DIV; break;
                        case AX_ASSIGN_REM: binop = AX_BINOP_REM; break;
                        case AX_ASSIGN_BITAND: binop = AX_BINOP_BITAND; break;
                        case AX_ASSIGN_BITOR: binop = AX_BINOP_BITOR; break;
                        case AX_ASSIGN_BITXOR: binop = AX_BINOP_BITXOR; break;
                        case AX_ASSIGN_SHL: binop = AX_BINOP_SHL; break;
                        case AX_ASSIGN_SHR: binop = AX_BINOP_SHR; break;
                        default: break;
                    }
                    right->binary.op = binop;
                    // Note: duplicating AST to lower again for RHS
                    right->binary.left = lower_expr(ctx, s->assign.left);
                    right->binary.right = lower_expr(ctx, s->assign.right);
                    hs->assign.right = right;
                }
                break;
            case AX_STMT_EXPR:
                hs->kind = AX_HIR_STMT_EXPR;
                hs->expr_stmt.has_semi = s->expr_stmt.has_semi;
                hs->expr_stmt.expr = lower_expr(ctx, s->expr_stmt.expr);
                break;
        }
        *tail = hs;
        tail = &hs->next;
    }
    *tail = NULL;
    return head;
}

static AxHirBlock lower_block(LowerCtx *ctx, const AxAstBlock *b) {
    AxHirBlock hb = {0};
    if (b) {
        hb.span = b->span;
        hb.stmts = lower_stmt(ctx, b->stmts);
    }
    return hb;
}

static AxHirUseTree *lower_use_tree(LowerCtx *ctx, const AxAstUseTree *tree) {
    AxHirUseTree *head = NULL;
    AxHirUseTree **tail = &head;
    for (; tree; tree = tree->next) {
        AxHirUseTree *ht = ax_arena_alloc(ctx->arena, sizeof(AxHirUseTree), 8);
        ht->span = tree->span;
        ht->path = tree->path;
        ht->alias = tree->alias;
        ht->subtrees = lower_use_tree(ctx, tree->subtrees);
        *tail = ht;
        tail = &ht->next;
    }
    *tail = NULL;
    return head;
}

static AxHirItem *lower_item(LowerCtx *ctx, const AxAstItem *n) {
    AxHirItem *head = NULL;
    AxHirItem **tail = &head;
    for (; n; n = n->next) {
        AxHirItem *hi = ax_arena_alloc(ctx->arena, sizeof(AxHirItem), 8);
        hi->span = n->span;
        hi->attrs = lower_attrs(ctx, n->attrs);
        hi->vis = lower_vis(ctx, &n->vis);
        switch (n->kind) {
            case AX_ITEM_ERROR: hi->kind = AX_HIR_ITEM_ERROR; break;
            case AX_ITEM_MODULE:
                hi->kind = AX_HIR_ITEM_MODULE;
                hi->module.path = n->module.path;
                break;
            case AX_ITEM_USE:
                hi->kind = AX_HIR_ITEM_USE;
                hi->use.tree = lower_use_tree(ctx, n->use.tree);
                break;
            case AX_ITEM_FN:
                hi->kind = AX_HIR_ITEM_FN;
                hi->fn.is_async = n->fn.is_async;
                hi->fn.is_comptime = n->fn.is_comptime;
                hi->fn.is_unsafe = n->fn.is_unsafe;
                hi->fn.abi = n->fn.abi;
                hi->fn.name = n->fn.name;
                hi->fn.symbol = get_symbol(ctx, n);
                hi->fn.generic_params = lower_generic_params(ctx, n->fn.generic_params);
                
                AxHirParam **ptail = &hi->fn.params;
                for (AxAstParam *p = n->fn.params; p; p = p->next) {
                    AxHirParam *hp = ax_arena_alloc(ctx->arena, sizeof(AxHirParam), 8);
                    hp->span = p->span;
                    hp->is_mut = p->is_mut;
                    hp->symbol = get_symbol(ctx, p); // parameter node gets symbol
                    hp->type = lower_type(ctx, p->type);
                    *ptail = hp;
                    ptail = &hp->next;
                }
                *ptail = NULL;
                
                hi->fn.ret_type = lower_type(ctx, n->fn.ret_type);
                hi->fn.where_clause = lower_where_clause(ctx, n->fn.where_clause);
                if (n->fn.body) {
                    AxHirBlock *b = ax_arena_alloc(ctx->arena, sizeof(AxHirBlock), 8);
                    *b = lower_block(ctx, n->fn.body);
                    hi->fn.body = b;
                }
                break;
            case AX_ITEM_STRUCT:
                hi->kind = AX_HIR_ITEM_STRUCT;
                hi->struct_decl.name = n->struct_decl.name;
                hi->struct_decl.generic_params = lower_generic_params(ctx, n->struct_decl.generic_params);
                hi->struct_decl.where_clause = lower_where_clause(ctx, n->struct_decl.where_clause);
                hi->struct_decl.is_tuple = n->struct_decl.is_tuple;
                if (n->struct_decl.is_tuple) {
                    hi->struct_decl.tuple_types = lower_type(ctx, n->struct_decl.tuple_types);
                } else {
                    AxHirFieldDecl **ftail = &hi->struct_decl.struct_fields;
                    for (AxAstFieldDecl *f = n->struct_decl.struct_fields; f; f = f->next) {
                        AxHirFieldDecl *hf = ax_arena_alloc(ctx->arena, sizeof(AxHirFieldDecl), 8);
                        hf->attrs = lower_attrs(ctx, f->attrs);
                        hf->vis = lower_vis(ctx, &f->vis);
                        hf->span = f->span;
                        hf->name = f->name;
                        hf->type = lower_type(ctx, f->type);
                        *ftail = hf;
                        ftail = &hf->next;
                    }
                    *ftail = NULL;
                }
                break;
            case AX_ITEM_ENUM:
                hi->kind = AX_HIR_ITEM_ENUM;
                hi->enum_decl.name = n->enum_decl.name;
                hi->enum_decl.generic_params = lower_generic_params(ctx, n->enum_decl.generic_params);
                hi->enum_decl.where_clause = lower_where_clause(ctx, n->enum_decl.where_clause);
                AxHirVariantDecl **vtail = &hi->enum_decl.variants;
                for (AxAstVariantDecl *v = n->enum_decl.variants; v; v = v->next) {
                    AxHirVariantDecl *hv = ax_arena_alloc(ctx->arena, sizeof(AxHirVariantDecl), 8);
                    hv->attrs = lower_attrs(ctx, v->attrs);
                    hv->span = v->span;
                    hv->name = v->name;
                    hv->is_struct = v->is_struct;
                    if (v->is_struct) {
                        AxHirFieldDecl **ftail = &hv->struct_fields;
                        for (AxAstFieldDecl *f = v->struct_fields; f; f = f->next) {
                            AxHirFieldDecl *hf = ax_arena_alloc(ctx->arena, sizeof(AxHirFieldDecl), 8);
                            hf->attrs = lower_attrs(ctx, f->attrs);
                            hf->vis = lower_vis(ctx, &f->vis);
                            hf->span = f->span;
                            hf->name = f->name;
                            hf->type = lower_type(ctx, f->type);
                            *ftail = hf;
                            ftail = &hf->next;
                        }
                        *ftail = NULL;
                    } else {
                        hv->tuple_types = lower_type(ctx, v->tuple_types);
                    }
                    *vtail = hv;
                    vtail = &hv->next;
                }
                *vtail = NULL;
                break;
            case AX_ITEM_TRAIT:
                hi->kind = AX_HIR_ITEM_TRAIT;
                hi->trait.name = n->trait.name;
                hi->trait.generic_params = lower_generic_params(ctx, n->trait.generic_params);
                hi->trait.supertraits = lower_type(ctx, n->trait.supertraits);
                hi->trait.where_clause = lower_where_clause(ctx, n->trait.where_clause);
                hi->trait.members = lower_item(ctx, n->trait.members);
                break;
            case AX_ITEM_IMPL:
                hi->kind = AX_HIR_ITEM_IMPL;
                hi->impl.generic_params = lower_generic_params(ctx, n->impl.generic_params);
                hi->impl.trait_path = lower_type(ctx, n->impl.trait_path);
                hi->impl.self_type = lower_type(ctx, n->impl.self_type);
                hi->impl.where_clause = lower_where_clause(ctx, n->impl.where_clause);
                hi->impl.members = lower_item(ctx, n->impl.members);
                break;
            case AX_ITEM_TYPE_ALIAS:
                hi->kind = AX_HIR_ITEM_TYPE_ALIAS;
                hi->type_alias.name = n->type_alias.name;
                hi->type_alias.generic_params = lower_generic_params(ctx, n->type_alias.generic_params);
                hi->type_alias.type = lower_type(ctx, n->type_alias.type);
                break;
            case AX_ITEM_CONST:
                hi->kind = AX_HIR_ITEM_CONST;
                hi->const_decl.name = n->const_decl.name;
                hi->const_decl.type = lower_type(ctx, n->const_decl.type);
                hi->const_decl.expr = lower_expr(ctx, n->const_decl.expr);
                break;
            case AX_ITEM_STATIC:
                hi->kind = AX_HIR_ITEM_STATIC;
                hi->static_decl.is_unsafe = n->static_decl.is_unsafe;
                hi->static_decl.is_mut = n->static_decl.is_mut;
                hi->static_decl.name = n->static_decl.name;
                hi->static_decl.type = lower_type(ctx, n->static_decl.type);
                hi->static_decl.expr = lower_expr(ctx, n->static_decl.expr);
                break;
            case AX_ITEM_EXTERN_BLOCK:
                hi->kind = AX_HIR_ITEM_EXTERN_BLOCK;
                hi->extern_block.abi = n->extern_block.abi;
                hi->extern_block.members = lower_item(ctx, n->extern_block.members);
                break;
        }
        *tail = hi;
        tail = &hi->next;
    }
    *tail = NULL;
    return head;
}

AxHir ax_lower_ast(AxArena *arena, const AxAst *ast, const AxResolveMap *rmap, AxDiagSink *sink) {
    LowerCtx ctx = { arena, rmap, sink };
    AxHir hir = {0};
    hir.items = lower_item(&ctx, ast->items);
    return hir;
}
