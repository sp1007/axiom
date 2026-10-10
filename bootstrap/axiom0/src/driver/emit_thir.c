#include "driver/driver.h"
#include "lex/lex.h"
#include "source/source.h"
#include "diag/diag.h"
#include "syntax/parse.h"
#include "syntax/ast.h"
#include "resolve/resolve.h"
#include "hir/hir.h"
#include "hir/lower.h"
#include "types/types.h"
#include "kernel/arena.h"
#include "kernel/str.h"
#include "kernel/interner.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <inttypes.h>

typedef struct DumpState {
    FILE *out;
    StrInterner *interner;
    int indent;
    const AxThir *thir;
    FileId filter_file;
} DumpState;


static void d_typeid(DumpState *st, TypeId id) {
    if (TypeId_is_none(id)) {
        fputs(" <Type None>", st->out);
        return;
    }
    const AxType *t = ax_type_get(&st->thir->interner, id);
    fputs(" <Type ", st->out);
    switch ((int)t->kind) {
        case AX_TY_ERROR: fputs("error", st->out); break;
        case AX_TY_UNIT: fputs("()", st->out); break;
        case AX_TY_NEVER: fputs("never", st->out); break;
        case AX_TY_BOOL: fputs("bool", st->out); break;
        case AX_TY_CHAR: fputs("char", st->out); break;
        case AX_TY_I8: fputs("i8", st->out); break;
        case AX_TY_I16: fputs("i16", st->out); break;
        case AX_TY_I32: fputs("i32", st->out); break;
        case AX_TY_I64: fputs("i64", st->out); break;
        case AX_TY_ISIZE: fputs("isize", st->out); break;
        case AX_TY_U8: fputs("u8", st->out); break;
        case AX_TY_U16: fputs("u16", st->out); break;
        case AX_TY_U32: fputs("u32", st->out); break;
        case AX_TY_U64: fputs("u64", st->out); break;
        case AX_TY_USIZE: fputs("usize", st->out); break;
        case AX_TY_STR: fputs("Str", st->out); break;
        case AX_TY_BUILTIN_LEN: fputs("<builtin:len>", st->out); break;
        case AX_TY_BUILTIN_PRINT: fputs("<builtin:print>", st->out); break;
        case AX_TY_BUILTIN_PRINT_INT: fputs("<builtin:print_int>", st->out); break;
        case AX_TY_FN: 
            fputs("fn(", st->out);
            for(size_t i=0; i<t->fn.param_count; i++) {
                if (i > 0) fputs(", ", st->out);
                d_typeid(st, t->fn.param_types[i]);
            }
            fputs(") -> ", st->out);
            d_typeid(st, t->fn.ret_type);
            break;
        case AX_TY_INT_VAR:
            fprintf(st->out, "?int%u", t->int_var.var_id);
            break;
    }
    fputs(">", st->out);
}

static void d_nl(DumpState *st) {
    fputs("\n", st->out);
    for (int i = 0; i < st->indent; ++i) {
        fputs("  ", st->out);
    }
}

static void d_list_begin(DumpState *st, const char *name) {
    fputs("(", st->out);
    fputs(name, st->out);
    st->indent++;
}

static void d_list_end(DumpState *st) {
    st->indent--;
    fputs(")", st->out);
}

static void d_strid(DumpState *st, StrId id) {
    if (id.v == 0) {
        fputs(" \"\"", st->out);
        return;
    }
    StrView name = ax_interner_get(st->interner, id);
    fputs(" \"", st->out);
    fwrite(name.ptr, 1, name.len, st->out);
    fputs("\"", st->out);
}

static void d_bool(DumpState *st, bool b) {
    fputs(b ? " true" : " false", st->out);
}

static void d_symbol(DumpState *st, AxSymbolId sym) {
    if (sym.v) {
        fprintf(st->out, " @%" PRIu32, sym.v);
    }
}

static void d_expr(DumpState *st, const AxHirExpr *n);
static void d_pat(DumpState *st, const AxHirPat *n);
static void d_type(DumpState *st, const AxHirType *n);
static void d_stmt(DumpState *st, const AxHirStmt *n);
static void d_item(DumpState *st, const AxHirItem *n);
static void d_block(DumpState *st, const AxHirBlock *n);
static void d_generic_args(DumpState *st, const AxHirGenericArgs *n);
static void d_generic_params(DumpState *st, const AxHirGenericParams *n);
static void d_where_clause(DumpState *st, const AxHirWhereClause *n);
static void d_attr(DumpState *st, const AxHirAttr *n);
static void d_vis(DumpState *st, const AxHirVis *n);
static void d_dotted_name(DumpState *st, const AxAstDottedName *n);

static void d_path(DumpState *st, const AxHirPath *p) {
    if (!p) return;
    d_symbol(st, p->symbol);
    d_generic_args(st, p->generic_args);
}

static void d_dotted_name(DumpState *st, const AxAstDottedName *n) {
    if (!n) return;
    d_nl(st); d_list_begin(st, "DottedName");
    for(size_t i=0; i<n->count; i++) {
        d_strid(st, n->segments[i]);
    }
    d_list_end(st);
}

static void d_vis(DumpState *st, const AxHirVis *n) {
    if (!n) return;
    d_nl(st); d_list_begin(st, "Vis");
    switch(n->kind) {
        case AX_HIR_VIS_PRIVATE: fputs(" priv", st->out); break;
        case AX_HIR_VIS_PUB: fputs(" pub", st->out); break;
        case AX_HIR_VIS_PUB_PACKAGE: fputs(" pub_package", st->out); break;
        case AX_HIR_VIS_PUB_MODULE: fputs(" pub_module", st->out); break;
    }
    d_list_end(st);
}

static void d_attr(DumpState *st, const AxHirAttr *n) {
    while(n) {
        d_nl(st); d_list_begin(st, "Attr");
        d_strid(st, n->name);
        for(AxHirAttrArg *a = n->args; a; a = a->next) {
            d_nl(st); d_list_begin(st, "AttrArg");
            d_strid(st, a->name);
            d_expr(st, a->expr);
            d_list_end(st);
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_generic_args(DumpState *st, const AxHirGenericArgs *n) {
    if (!n) return;
    for(AxHirGenericArg *a = n->args; a; a = a->next) {
        d_nl(st); d_list_begin(st, "GenericArg");
        d_strid(st, a->name);
        d_type(st, a->type);
        d_list_end(st);
    }
}

static void d_generic_params(DumpState *st, const AxHirGenericParams *n) {
    if (!n) return;
    for(AxHirGenericParam *a = n->params; a; a = a->next) {
        d_nl(st); d_list_begin(st, "GenericParam");
        d_strid(st, a->name);
        d_type(st, a->bounds);
        d_list_end(st);
    }
}

static void d_where_clause(DumpState *st, const AxHirWhereClause *n) {
    if (!n) return;
    for(AxHirWherePred *a = n->preds; a; a = a->next) {
        d_nl(st); d_list_begin(st, "WherePred");
        d_type(st, a->type);
        d_type(st, a->bounds);
        d_list_end(st);
    }
}

static void d_block(DumpState *st, const AxHirBlock *n) {
    d_nl(st); d_list_begin(st, "Block");
    d_stmt(st, n->stmts);
    d_list_end(st);
}

static void d_type(DumpState *st, const AxHirType *n) {
    while(n) {
        d_nl(st);
        switch (n->kind) {
            case AX_HIR_TYPE_ERROR: d_list_begin(st, "TypeError"); break;
            case AX_HIR_TYPE_PATH: d_list_begin(st, "TypePath"); d_path(st, &n->path.path); break;
            case AX_HIR_TYPE_TUPLE: d_list_begin(st, "TypeTuple"); d_type(st, n->tuple.elem_types); break;
            case AX_HIR_TYPE_ARRAY: d_list_begin(st, "TypeArray"); d_expr(st, n->array.count); d_type(st, n->array.elem); break;
            case AX_HIR_TYPE_SLICE: d_list_begin(st, "TypeSlice"); d_type(st, n->slice.elem); break;
            case AX_HIR_TYPE_VIEW: d_list_begin(st, "TypeView"); d_bool(st, n->view.is_mut); d_type(st, n->view.elem); break;
            case AX_HIR_TYPE_PTR: d_list_begin(st, "TypePtr"); d_bool(st, n->ptr.is_mut); d_type(st, n->ptr.elem); break;
            case AX_HIR_TYPE_FN: d_list_begin(st, "TypeFn"); d_bool(st, n->fn.is_unsafe); d_strid(st, n->fn.abi); d_type(st, n->fn.param_types); d_type(st, n->fn.ret_type); break;
            case AX_HIR_TYPE_DYN: d_list_begin(st, "TypeDyn"); d_type(st, n->dyn.bounds); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_pat_field(DumpState *st, const AxHirPatField *n) {
    while(n) {
        d_nl(st); d_list_begin(st, "PatField");
        d_strid(st, n->name);
        d_pat(st, n->pat);
        d_list_end(st);
        n = n->next;
    }
}

static void d_pat(DumpState *st, const AxHirPat *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_HIR_PAT_ERROR: d_list_begin(st, "PatError"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } break;
            case AX_HIR_PAT_WILDCARD: d_list_begin(st, "PatWildcard"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } break;
            case AX_HIR_PAT_RANGE: d_list_begin(st, "PatRange"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_bool(st, n->range.is_inclusive); d_pat(st, n->range.start); d_pat(st, n->range.end); break;
            case AX_HIR_PAT_LITERAL: d_list_begin(st, "PatLiteral"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_bool(st, n->literal.is_negated); break;
            case AX_HIR_PAT_BINDING: d_list_begin(st, "PatBinding"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_bool(st, n->binding.is_mut); d_symbol(st, n->binding.symbol); break;
            case AX_HIR_PAT_PATH: d_list_begin(st, "PatPath"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_path(st, &n->path.path); d_pat(st, n->path.payload); break;
            case AX_HIR_PAT_TUPLE: d_list_begin(st, "PatTuple"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_pat(st, n->tuple.elems); break;
            case AX_HIR_PAT_OR: d_list_begin(st, "PatOr"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_pat(st, n->or_pat.pats); break;
            case AX_HIR_PAT_STRUCT: d_list_begin(st, "PatStruct"); { TypeId *ty = (TypeId*)AxPatTypeMap_get(&st->thir->pat_types, (const AxHirPat*)n); if (ty) d_typeid(st, *ty); } d_path(st, &n->struct_pat.path); d_pat_field(st, n->struct_pat.fields); d_bool(st, n->struct_pat.has_rest); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_expr(DumpState *st, const AxHirExpr *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_HIR_EXPR_ERROR: d_list_begin(st, "ExprError"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } break;
            case AX_HIR_EXPR_LITERAL: d_list_begin(st, "ExprLiteral"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } break;
            case AX_HIR_EXPR_PATH: d_list_begin(st, "ExprPath"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_path(st, &n->path.path); break;
            case AX_HIR_EXPR_ARRAY: d_list_begin(st, "ExprArray"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->array.elems); d_expr(st, n->array.count); break;
            case AX_HIR_EXPR_TUPLE: d_list_begin(st, "ExprTuple"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->tuple.elems); break;
            case AX_HIR_EXPR_STRUCT: d_list_begin(st, "ExprStruct"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_path(st, &n->struct_lit.path); 
                for(AxHirFieldInit *f = n->struct_lit.fields; f; f = f->next) {
                    d_nl(st); d_list_begin(st, "FieldInit"); d_strid(st, f->name); d_expr(st, f->expr); d_list_end(st);
                }
                break;
            case AX_HIR_EXPR_BLOCK: d_list_begin(st, "ExprBlock"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_block(st, &n->block.block); break;
            case AX_HIR_EXPR_IF: d_list_begin(st, "ExprIf"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_pat(st, n->if_expr.let_pat); d_expr(st, n->if_expr.cond); d_block(st, &n->if_expr.block); d_expr(st, n->if_expr.else_branch); break;
            case AX_HIR_EXPR_MATCH: d_list_begin(st, "ExprMatch"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->match.expr); 
                for(AxHirMatchArm *a = n->match.arms; a; a = a->next) {
                    d_nl(st); d_list_begin(st, "MatchArm"); d_pat(st, a->pat); d_expr(st, a->guard); d_expr(st, a->body); d_list_end(st);
                }
                break;
            case AX_HIR_EXPR_LOOP: d_list_begin(st, "ExprLoop"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_strid(st, n->loop.label); d_block(st, &n->loop.block); break;
            case AX_HIR_EXPR_WHILE: d_list_begin(st, "ExprWhile"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_strid(st, n->while_expr.label); d_pat(st, n->while_expr.let_pat); d_expr(st, n->while_expr.cond); d_block(st, &n->while_expr.block); break;
            case AX_HIR_EXPR_FOR: d_list_begin(st, "ExprFor"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_strid(st, n->for_expr.label); d_pat(st, n->for_expr.pat); d_expr(st, n->for_expr.iter); d_block(st, &n->for_expr.block); break;
            case AX_HIR_EXPR_UNSAFE: d_list_begin(st, "ExprUnsafe"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_block(st, &n->unsafe_block.block); break;
            case AX_HIR_EXPR_VIEW: d_list_begin(st, "ExprView"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_bool(st, n->view.is_mut); d_expr(st, n->view.expr); break;
            case AX_HIR_EXPR_COMPTIME: d_list_begin(st, "ExprComptime"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_block(st, &n->comptime.block); break;
            case AX_HIR_EXPR_JUMP: d_list_begin(st, "ExprJump"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } fprintf(st->out, " %d", (int)n->jump.jump_kind); d_strid(st, n->jump.label); d_expr(st, n->jump.expr); break;
            case AX_HIR_EXPR_CLOSURE: d_list_begin(st, "ExprClosure"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } 
                for(AxHirParam *p = n->closure.params; p; p = p->next) {
                    d_nl(st); d_list_begin(st, "Param"); d_bool(st, p->is_mut); d_symbol(st, p->symbol); d_type(st, p->type); d_list_end(st);
                }
                d_type(st, n->closure.ret_type); d_expr(st, n->closure.body); break;
            case AX_HIR_EXPR_RANGE: d_list_begin(st, "ExprRange"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_bool(st, n->range.is_inclusive); d_expr(st, n->range.start); d_expr(st, n->range.end); break;
            case AX_HIR_EXPR_BINARY: d_list_begin(st, "ExprBinary"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } fprintf(st->out, " %d", (int)n->binary.op); d_expr(st, n->binary.left); d_expr(st, n->binary.right); break;
            case AX_HIR_EXPR_UNARY: d_list_begin(st, "ExprUnary"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } fprintf(st->out, " %d", (int)n->unary.op); d_expr(st, n->unary.expr); break;
            case AX_HIR_EXPR_CAST: d_list_begin(st, "ExprCast"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->cast.expr); d_type(st, n->cast.type); break;
            case AX_HIR_EXPR_FIELD: d_list_begin(st, "ExprField"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->field.base); d_strid(st, n->field.name); d_generic_args(st, n->field.generic_args); break;
            case AX_HIR_EXPR_TUPLE_INDEX: d_list_begin(st, "ExprTupleIndex"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->tuple_index.base); fprintf(st->out, " %u", n->tuple_index.tuple_index); break;
            case AX_HIR_EXPR_CALL: d_list_begin(st, "ExprCall"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->call.callee); d_expr(st, n->call.args); break;
            case AX_HIR_EXPR_METHOD_CALL: d_list_begin(st, "ExprMethodCall"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->method_call.receiver); d_strid(st, n->method_call.method_name); d_generic_args(st, n->method_call.generic_args); d_expr(st, n->method_call.args); break;
            case AX_HIR_EXPR_INDEX: d_list_begin(st, "ExprIndex"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->index.base); d_expr(st, n->index.arg); break;
            case AX_HIR_EXPR_TRY: d_list_begin(st, "ExprTry"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->try_expr.expr); break;
            case AX_HIR_EXPR_AWAIT: d_list_begin(st, "ExprAwait"); { TypeId *ty = (TypeId*)AxExprTypeMap_get(&st->thir->expr_types, (const AxHirExpr*)n); if (ty) d_typeid(st, *ty); } d_expr(st, n->await_expr.expr); break;
        }
        d_list_end(st);
        n = n->next;
    }
}


static void d_use_tree(DumpState *st, const AxHirUseTree *n) {
    if (!n) return;
    d_nl(st);
    d_list_begin(st, "UseTree");
    d_dotted_name(st, &n->path);
    if (n->alias.v) {
        d_strid(st, n->alias);
    }
    if (n->subtrees) {
        d_use_tree(st, n->subtrees);
    }
    d_list_end(st);
    if (n->next) {
        d_use_tree(st, n->next);
    }
}

static void d_stmt(DumpState *st, const AxHirStmt *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_HIR_STMT_ERROR: d_list_begin(st, "StmtError"); break;
            case AX_HIR_STMT_LET: d_list_begin(st, "StmtLet"); d_pat(st, n->let.pat); d_type(st, n->let.type); d_expr(st, n->let.expr); if (n->let.else_block) d_block(st, n->let.else_block); break;
            case AX_HIR_STMT_ASSIGN: d_list_begin(st, "StmtAssign"); d_expr(st, n->assign.left); d_expr(st, n->assign.right); break;
            case AX_HIR_STMT_EXPR: d_list_begin(st, "StmtExpr"); d_bool(st, n->expr_stmt.has_semi); d_expr(st, n->expr_stmt.expr); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_item(DumpState *st, const AxHirItem *n) {
    while (n) {
        if (st->filter_file.v != 0 && n->span.file.v != 0 && n->span.file.v != st->filter_file.v) {
            n = n->next;
            continue;
        }
        d_nl(st);
        switch (n->kind) {
            case AX_HIR_ITEM_ERROR: d_list_begin(st, "ItemError"); break;
            case AX_HIR_ITEM_MODULE: d_list_begin(st, "ItemModule"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_dotted_name(st, &n->module.path); break;
            case AX_HIR_ITEM_USE: d_list_begin(st, "ItemUse"); d_attr(st, n->attrs); d_vis(st, &n->vis); 
                d_use_tree(st, n->use.tree);
                break;
            case AX_HIR_ITEM_FN: d_list_begin(st, "ItemFn"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_bool(st, n->fn.is_async); d_bool(st, n->fn.is_comptime); d_bool(st, n->fn.is_unsafe); d_strid(st, n->fn.abi); d_strid(st, n->fn.name); d_generic_params(st, n->fn.generic_params); 
                for(AxHirParam *p = n->fn.params; p; p = p->next) { d_nl(st); d_list_begin(st, "Param"); d_bool(st, p->is_mut); d_symbol(st, p->symbol); d_type(st, p->type); d_list_end(st); }
                d_type(st, n->fn.ret_type); d_where_clause(st, n->fn.where_clause); if(n->fn.body) d_block(st, n->fn.body); break;
            case AX_HIR_ITEM_STRUCT: d_list_begin(st, "ItemStruct"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->struct_decl.name); d_generic_params(st, n->struct_decl.generic_params); d_where_clause(st, n->struct_decl.where_clause); d_bool(st, n->struct_decl.is_tuple); 
                if (n->struct_decl.is_tuple) { d_type(st, n->struct_decl.tuple_types); }
                else { for(AxHirFieldDecl *f = n->struct_decl.struct_fields; f; f = f->next) { d_nl(st); d_list_begin(st, "FieldDecl"); d_attr(st, f->attrs); d_vis(st, &f->vis); d_strid(st, f->name); d_type(st, f->type); d_list_end(st); } }
                break;
            case AX_HIR_ITEM_ENUM: d_list_begin(st, "ItemEnum"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->enum_decl.name); d_generic_params(st, n->enum_decl.generic_params); d_where_clause(st, n->enum_decl.where_clause); 
                for(AxHirVariantDecl *v = n->enum_decl.variants; v; v = v->next) { d_nl(st); d_list_begin(st, "VariantDecl"); d_attr(st, v->attrs); d_strid(st, v->name); d_bool(st, v->is_struct); if(v->is_struct) { for(AxHirFieldDecl *f = v->struct_fields; f; f = f->next) { d_nl(st); d_list_begin(st, "FieldDecl"); d_attr(st, f->attrs); d_vis(st, &f->vis); d_strid(st, f->name); d_type(st, f->type); d_list_end(st); } } else { d_type(st, v->tuple_types); } d_list_end(st); }
                break;
            case AX_HIR_ITEM_TRAIT: d_list_begin(st, "ItemTrait"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->trait.name); d_generic_params(st, n->trait.generic_params); d_type(st, n->trait.supertraits); d_where_clause(st, n->trait.where_clause); d_item(st, n->trait.members); break;
            case AX_HIR_ITEM_IMPL: d_list_begin(st, "ItemImpl"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_generic_params(st, n->impl.generic_params); d_type(st, n->impl.trait_path); d_type(st, n->impl.self_type); d_where_clause(st, n->impl.where_clause); d_item(st, n->impl.members); break;
            case AX_HIR_ITEM_TYPE_ALIAS: d_list_begin(st, "ItemTypeAlias"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->type_alias.name); d_generic_params(st, n->type_alias.generic_params); d_type(st, n->type_alias.type); break;
            case AX_HIR_ITEM_CONST: d_list_begin(st, "ItemConst"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->const_decl.name); d_type(st, n->const_decl.type); d_expr(st, n->const_decl.expr); break;
            case AX_HIR_ITEM_STATIC: d_list_begin(st, "ItemStatic"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_bool(st, n->static_decl.is_unsafe); d_bool(st, n->static_decl.is_mut); d_strid(st, n->static_decl.name); d_type(st, n->static_decl.type); d_expr(st, n->static_decl.expr); break;
            case AX_HIR_ITEM_EXTERN_BLOCK: d_list_begin(st, "ItemExternBlock"); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->extern_block.abi); d_item(st, n->extern_block.members); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static int run_emit_thir(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=thir <file>\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    const char *path = pos_argv[1];
    
    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    
    int rc = ax_pipeline_run(&st, AX_STAGE_TYPECK);
    if (rc != 0) { ax_pipeline_free(&st); free(pos_argv); return rc; }

    DumpState dst = { io->out, &st.interner, 0, &st.thir, st.file };
    d_item(&dst, st.hir.items);
    fputs("\n", dst.out);

    ax_pipeline_free(&st);
    free(pos_argv);
    return rc;
}

const AxEmitter axemit_thir = {
    "thir",
    "dump the typed HIR",
    run_emit_thir
};
