#include "driver/driver.h"
#include "lex/lex.h"
#include "source/source.h"
#include "diag/diag.h"
#include "syntax/parse.h"
#include "resolve/resolve.h"
#include "syntax/ast.h"
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
    const AxResolveMap *map;
    int indent;
} DumpState;


static void d_resolved(DumpState *st, const void *node) {
    if (!st->map || !node) return;
    const AxSymbolId *sym = AxNodeMap_get(&st->map->node_map, node);
    if (sym && sym->v != 0) {
        fprintf(st->out, " @Sym(%u)", (unsigned)sym->v);
    }
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


static void d_expr(DumpState *st, const AxAstExpr *n);
static void d_pat(DumpState *st, const AxAstPat *n);
static void d_type(DumpState *st, const AxAstType *n);
static void d_stmt(DumpState *st, const AxAstStmt *n);
static void d_item(DumpState *st, const AxAstItem *n);
static void d_block(DumpState *st, const AxAstBlock *n);
static void d_path_seg(DumpState *st, const AxAstTypePathSegment *n);
static void d_generic_args(DumpState *st, const AxAstGenericArgs *n);
static void d_generic_params(DumpState *st, const AxAstGenericParams *n);
static void d_where_clause(DumpState *st, const AxAstWhereClause *n);
static void d_attr(DumpState *st, const AxAstAttr *n);
static void d_vis(DumpState *st, const AxAstVis *n);
static void d_dotted_name(DumpState *st, const AxAstDottedName *n);

static void d_dotted_name(DumpState *st, const AxAstDottedName *n) {
    if (!n) return;
    d_nl(st); d_list_begin(st, "DottedName"); d_resolved(st, n);
    for(size_t i=0; i<n->count; i++) {
        d_strid(st, n->segments[i]);
    }
    d_list_end(st);
}

static void d_vis(DumpState *st, const AxAstVis *n) {
    if (!n) return;
    d_nl(st); d_list_begin(st, "Vis"); d_resolved(st, n);
    switch(n->kind) {
        case AX_VIS_PRIVATE: fputs(" priv", st->out); break;
        case AX_VIS_PUB: fputs(" pub", st->out); break;
        case AX_VIS_PUB_PACKAGE: fputs(" pub_package", st->out); break;
        case AX_VIS_PUB_MODULE: fputs(" pub_module", st->out); break;
    }
    d_list_end(st);
}

static void d_attr(DumpState *st, const AxAstAttr *n) {
    while(n) {
        d_nl(st); d_list_begin(st, "Attr"); d_resolved(st, n);
        d_strid(st, n->name);
        for(AxAstAttrArg *a = n->args; a; a = a->next) {
            d_nl(st); d_list_begin(st, "AttrArg"); d_resolved(st, n);
            d_strid(st, a->name);
            d_expr(st, a->expr);
            d_list_end(st);
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_generic_args(DumpState *st, const AxAstGenericArgs *n) {
    if (!n) return;
    for(AxAstGenericArg *a = n->args; a; a = a->next) {
        d_nl(st); d_list_begin(st, "GenericArg"); d_resolved(st, n);
        d_strid(st, a->name);
        d_type(st, a->type);
        d_list_end(st);
    }
}

static void d_generic_params(DumpState *st, const AxAstGenericParams *n) {
    if (!n) return;
    for(AxAstGenericParam *a = n->params; a; a = a->next) {
        d_nl(st); d_list_begin(st, "GenericParam"); d_resolved(st, n);
        d_strid(st, a->name);
        d_type(st, a->bounds);
        d_list_end(st);
    }
}

static void d_where_clause(DumpState *st, const AxAstWhereClause *n) {
    if (!n) return;
    for(AxAstWherePred *a = n->preds; a; a = a->next) {
        d_nl(st); d_list_begin(st, "WherePred"); d_resolved(st, n);
        d_type(st, a->type);
        d_type(st, a->bounds);
        d_list_end(st);
    }
}

static void d_path_seg(DumpState *st, const AxAstTypePathSegment *n) {
    while(n) {
        d_nl(st); d_list_begin(st, "PathSegment"); d_resolved(st, n);
        d_strid(st, n->name);
        d_generic_args(st, n->generic_args);
        d_list_end(st);
        n = n->next;
    }
}

static void d_block(DumpState *st, const AxAstBlock *n) {
    d_nl(st); d_list_begin(st, "Block"); d_resolved(st, n);
    d_stmt(st, n->stmts);
    d_list_end(st);
}

static void d_type(DumpState *st, const AxAstType *n) {
    while(n) {
        d_nl(st);
        switch (n->kind) {
            case AX_TYPE_ERROR: d_list_begin(st, "TypeError"); d_resolved(st, n); break;
            case AX_TYPE_PATH: d_list_begin(st, "TypePath"); d_resolved(st, n); d_path_seg(st, n->path.segments); break;
            case AX_TYPE_TUPLE: d_list_begin(st, "TypeTuple"); d_resolved(st, n); d_type(st, n->tuple.elem_types); break;
            case AX_TYPE_ARRAY: d_list_begin(st, "TypeArray"); d_resolved(st, n); d_expr(st, n->array.count); d_type(st, n->array.elem); break;
            case AX_TYPE_SLICE: d_list_begin(st, "TypeSlice"); d_resolved(st, n); d_type(st, n->slice.elem); break;
            case AX_TYPE_VIEW: d_list_begin(st, "TypeView"); d_resolved(st, n); d_bool(st, n->view.is_mut); d_type(st, n->view.elem); break;
            case AX_TYPE_PTR: d_list_begin(st, "TypePtr"); d_resolved(st, n); d_bool(st, n->ptr.is_mut); d_type(st, n->ptr.elem); break;
            case AX_TYPE_FN: d_list_begin(st, "TypeFn"); d_resolved(st, n); d_bool(st, n->fn.is_unsafe); d_strid(st, n->fn.abi); d_type(st, n->fn.param_types); d_type(st, n->fn.ret_type); break;
            case AX_TYPE_DYN: d_list_begin(st, "TypeDyn"); d_resolved(st, n); d_type(st, n->dyn.bounds); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_pat_field(DumpState *st, const AxAstPatField *n) {
    while(n) {
        d_nl(st); d_list_begin(st, "PatField"); d_resolved(st, n);
        d_strid(st, n->name);
        d_pat(st, n->pat);
        d_list_end(st);
        n = n->next;
    }
}

static void d_pat(DumpState *st, const AxAstPat *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_PAT_ERROR: d_list_begin(st, "PatError"); d_resolved(st, n); break;
            case AX_PAT_WILDCARD: d_list_begin(st, "PatWildcard"); d_resolved(st, n); break;
            case AX_PAT_RANGE: d_list_begin(st, "PatRange"); d_resolved(st, n); d_bool(st, n->range.is_inclusive); d_pat(st, n->range.start); d_pat(st, n->range.end); break;
            case AX_PAT_LITERAL: d_list_begin(st, "PatLiteral"); d_resolved(st, n); d_bool(st, n->literal.is_negated); /* tok val later */ break;
            case AX_PAT_BINDING: d_list_begin(st, "PatBinding"); d_resolved(st, n); d_bool(st, n->binding.is_mut); d_strid(st, n->binding.name); break;
            case AX_PAT_PATH: d_list_begin(st, "PatPath"); d_resolved(st, n); d_path_seg(st, n->path.segments); d_pat(st, n->path.payload); break;
            case AX_PAT_TUPLE: d_list_begin(st, "PatTuple"); d_resolved(st, n); d_pat(st, n->tuple.elems); break;
            case AX_PAT_OR: d_list_begin(st, "PatOr"); d_resolved(st, n); d_pat(st, n->or_pat.pats); break;
            case AX_PAT_STRUCT: d_list_begin(st, "PatStruct"); d_resolved(st, n); d_path_seg(st, n->struct_pat.segments); d_pat_field(st, n->struct_pat.fields); d_bool(st, n->struct_pat.has_rest); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_expr(DumpState *st, const AxAstExpr *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_EXPR_ERROR: d_list_begin(st, "ExprError"); d_resolved(st, n); break;
            case AX_EXPR_LITERAL: d_list_begin(st, "ExprLiteral"); d_resolved(st, n); /* token */ break;
            case AX_EXPR_PATH: d_list_begin(st, "ExprPath"); d_resolved(st, n); d_path_seg(st, n->path.segments); break;
            case AX_EXPR_PAREN: d_list_begin(st, "ExprParen"); d_resolved(st, n); d_expr(st, n->paren.expr); break;
            case AX_EXPR_ARRAY: d_list_begin(st, "ExprArray"); d_resolved(st, n); d_expr(st, n->array.elems); d_expr(st, n->array.count); break;
            case AX_EXPR_TUPLE: d_list_begin(st, "ExprTuple"); d_resolved(st, n); d_expr(st, n->tuple.elems); break;
            case AX_EXPR_STRUCT: d_list_begin(st, "ExprStruct"); d_resolved(st, n); d_path_seg(st, n->struct_lit.segments); 
                for(AxAstFieldInit *f = n->struct_lit.fields; f; f = f->next) {
                    d_nl(st); d_list_begin(st, "FieldInit"); d_resolved(st, f); d_strid(st, f->name); d_expr(st, f->expr); d_list_end(st);
                }
                break;
            case AX_EXPR_BLOCK: d_list_begin(st, "ExprBlock"); d_resolved(st, n); d_block(st, &n->block.block); break;
            case AX_EXPR_IF: d_list_begin(st, "ExprIf"); d_resolved(st, n); d_pat(st, n->if_expr.let_pat); d_expr(st, n->if_expr.cond); d_block(st, &n->if_expr.block); d_expr(st, n->if_expr.else_branch); break;
            case AX_EXPR_MATCH: d_list_begin(st, "ExprMatch"); d_resolved(st, n); d_expr(st, n->match.expr); 
                for(AxAstMatchArm *a = n->match.arms; a; a = a->next) {
                    d_nl(st); d_list_begin(st, "MatchArm"); d_resolved(st, a); d_pat(st, a->pat); d_expr(st, a->guard); d_expr(st, a->body); d_list_end(st);
                }
                break;
            case AX_EXPR_LOOP: d_list_begin(st, "ExprLoop"); d_resolved(st, n); d_strid(st, n->loop.label); d_block(st, &n->loop.block); break;
            case AX_EXPR_WHILE: d_list_begin(st, "ExprWhile"); d_resolved(st, n); d_strid(st, n->while_expr.label); d_pat(st, n->while_expr.let_pat); d_expr(st, n->while_expr.cond); d_block(st, &n->while_expr.block); break;
            case AX_EXPR_FOR: d_list_begin(st, "ExprFor"); d_resolved(st, n); d_strid(st, n->for_expr.label); d_pat(st, n->for_expr.pat); d_expr(st, n->for_expr.iter); d_block(st, &n->for_expr.block); break;
            case AX_EXPR_UNSAFE: d_list_begin(st, "ExprUnsafe"); d_resolved(st, n); d_block(st, &n->unsafe_block.block); break;
            case AX_EXPR_VIEW: d_list_begin(st, "ExprView"); d_resolved(st, n); d_bool(st, n->view.is_mut); d_expr(st, n->view.expr); break;
            case AX_EXPR_COMPTIME: d_list_begin(st, "ExprComptime"); d_resolved(st, n); d_block(st, &n->comptime.block); break;
            case AX_EXPR_JUMP: d_list_begin(st, "ExprJump"); d_resolved(st, n); fprintf(st->out, " %d", (int)n->jump.jump_kind); d_strid(st, n->jump.label); d_expr(st, n->jump.expr); break;
            case AX_EXPR_CLOSURE: d_list_begin(st, "ExprClosure"); d_resolved(st, n); 
                for(AxAstParam *p = n->closure.params; p; p = p->next) {
                    d_nl(st); d_list_begin(st, "Param"); d_resolved(st, p); d_bool(st, p->is_mut); d_strid(st, p->name); d_type(st, p->type); d_list_end(st);
                }
                d_type(st, n->closure.ret_type); d_expr(st, n->closure.body); break;
            case AX_EXPR_RANGE: d_list_begin(st, "ExprRange"); d_resolved(st, n); d_bool(st, n->range.is_inclusive); d_expr(st, n->range.start); d_expr(st, n->range.end); break;
            case AX_EXPR_BINARY: d_list_begin(st, "ExprBinary"); d_resolved(st, n); fprintf(st->out, " %d", (int)n->binary.op); d_expr(st, n->binary.left); d_expr(st, n->binary.right); break;
            case AX_EXPR_UNARY: d_list_begin(st, "ExprUnary"); d_resolved(st, n); fprintf(st->out, " %d", (int)n->unary.op); d_expr(st, n->unary.expr); break;
            case AX_EXPR_CAST: d_list_begin(st, "ExprCast"); d_resolved(st, n); d_expr(st, n->cast.expr); d_type(st, n->cast.type); break;
            case AX_EXPR_POSTFIX: d_list_begin(st, "ExprPostfix"); d_resolved(st, n); d_expr(st, n->postfix.head); 
                for(AxAstPostfixSeg *s = n->postfix.segments; s; s = s->next) {
                    d_nl(st); d_list_begin(st, "PostfixSeg"); d_resolved(st, s); fprintf(st->out, " %d", (int)s->kind);
                    switch(s->kind) {
                        case AX_POSTFIX_FIELD: d_strid(st, s->field.name); d_generic_args(st, s->field.generic_args); break;
                        case AX_POSTFIX_TUPLE_INDEX: fprintf(st->out, " %u", s->tuple_index); break;
                        case AX_POSTFIX_CALL: d_expr(st, s->call.args); break;
                        case AX_POSTFIX_INDEX: d_expr(st, s->index.arg); break;
                        case AX_POSTFIX_TRY: break;
                        case AX_POSTFIX_AWAIT: break;
                        case AX_POSTFIX_ARROW: d_strid(st, s->arrow_name); break;
                    }
                    d_list_end(st);
                }
                break;
        }
        d_list_end(st);
        n = n->next;
    }
}


static void d_use_tree(DumpState *st, const AxAstUseTree *n) {
    if (!n) return;
    d_nl(st);
    d_list_begin(st, "UseTree"); d_resolved(st, n);
    d_dotted_name(st, &n->path);
    if (n->alias.v) {
        d_strid(st, n->alias);
    }
    if (n->subtrees) {
        // Assume subtrees is just a list? 
        d_use_tree(st, n->subtrees);
    }
    d_list_end(st);
    if (n->next) {
        d_use_tree(st, n->next);
    }
}

static void d_stmt(DumpState *st, const AxAstStmt *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_STMT_ERROR: d_list_begin(st, "StmtError"); d_resolved(st, n); break;
            case AX_STMT_LET: d_list_begin(st, "StmtLet"); d_resolved(st, n); d_pat(st, n->let.pat); d_type(st, n->let.type); d_expr(st, n->let.expr); if (n->let.else_block) d_block(st, n->let.else_block); break;
            case AX_STMT_ASSIGN: d_list_begin(st, "StmtAssign"); d_resolved(st, n); fprintf(st->out, " %d", (int)n->assign.op); d_expr(st, n->assign.left); d_expr(st, n->assign.right); break;
            case AX_STMT_EXPR: d_list_begin(st, "StmtExpr"); d_resolved(st, n); d_bool(st, n->expr_stmt.has_semi); d_expr(st, n->expr_stmt.expr); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static void d_item(DumpState *st, const AxAstItem *n) {
    while (n) {
        d_nl(st);
        switch (n->kind) {
            case AX_ITEM_ERROR: d_list_begin(st, "ItemError"); d_resolved(st, n); break;
            case AX_ITEM_MODULE: d_list_begin(st, "ItemModule"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_dotted_name(st, &n->module.path); break;
            case AX_ITEM_USE: d_list_begin(st, "ItemUse"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); 
                d_use_tree(st, n->use.tree);
                break;
            case AX_ITEM_FN: d_list_begin(st, "ItemFn"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_bool(st, n->fn.is_async); d_bool(st, n->fn.is_comptime); d_bool(st, n->fn.is_unsafe); d_strid(st, n->fn.abi); d_strid(st, n->fn.name); d_generic_params(st, n->fn.generic_params); 
                for(AxAstParam *p = n->fn.params; p; p = p->next) { d_nl(st); d_list_begin(st, "Param"); d_resolved(st, p); d_bool(st, p->is_mut); d_strid(st, p->name); d_type(st, p->type); d_list_end(st); }
                d_type(st, n->fn.ret_type); d_where_clause(st, n->fn.where_clause); if(n->fn.body) d_block(st, n->fn.body); break;
            case AX_ITEM_STRUCT: d_list_begin(st, "ItemStruct"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->struct_decl.name); d_generic_params(st, n->struct_decl.generic_params); d_where_clause(st, n->struct_decl.where_clause); d_bool(st, n->struct_decl.is_tuple); 
                if (n->struct_decl.is_tuple) { d_type(st, n->struct_decl.tuple_types); }
                else { for(AxAstFieldDecl *f = n->struct_decl.struct_fields; f; f = f->next) { d_nl(st); d_list_begin(st, "FieldDecl"); d_resolved(st, f); d_attr(st, f->attrs); d_vis(st, &f->vis); d_strid(st, f->name); d_type(st, f->type); d_list_end(st); } }
                break;
            case AX_ITEM_ENUM: d_list_begin(st, "ItemEnum"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->enum_decl.name); d_generic_params(st, n->enum_decl.generic_params); d_where_clause(st, n->enum_decl.where_clause); 
                for(AxAstVariantDecl *v = n->enum_decl.variants; v; v = v->next) { d_nl(st); d_list_begin(st, "VariantDecl"); d_resolved(st, v); d_attr(st, v->attrs); d_strid(st, v->name); d_bool(st, v->is_struct); if(v->is_struct) { for(AxAstFieldDecl *f = v->struct_fields; f; f = f->next) { d_nl(st); d_list_begin(st, "FieldDecl"); d_resolved(st, f); d_attr(st, f->attrs); d_vis(st, &f->vis); d_strid(st, f->name); d_type(st, f->type); d_list_end(st); } } else { d_type(st, v->tuple_types); } d_list_end(st); }
                break;
            case AX_ITEM_TRAIT: d_list_begin(st, "ItemTrait"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->trait.name); d_generic_params(st, n->trait.generic_params); d_type(st, n->trait.supertraits); d_where_clause(st, n->trait.where_clause); d_item(st, n->trait.members); break;
            case AX_ITEM_IMPL: d_list_begin(st, "ItemImpl"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_generic_params(st, n->impl.generic_params); d_type(st, n->impl.trait_path); d_type(st, n->impl.self_type); d_where_clause(st, n->impl.where_clause); d_item(st, n->impl.members); break;
            case AX_ITEM_TYPE_ALIAS: d_list_begin(st, "ItemTypeAlias"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->type_alias.name); d_generic_params(st, n->type_alias.generic_params); d_type(st, n->type_alias.type); break;
            case AX_ITEM_CONST: d_list_begin(st, "ItemConst"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->const_decl.name); d_type(st, n->const_decl.type); d_expr(st, n->const_decl.expr); break;
            case AX_ITEM_STATIC: d_list_begin(st, "ItemStatic"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_bool(st, n->static_decl.is_unsafe); d_bool(st, n->static_decl.is_mut); d_strid(st, n->static_decl.name); d_type(st, n->static_decl.type); d_expr(st, n->static_decl.expr); break;
            case AX_ITEM_EXTERN_BLOCK: d_list_begin(st, "ItemExternBlock"); d_resolved(st, n); d_attr(st, n->attrs); d_vis(st, &n->vis); d_strid(st, n->extern_block.abi); d_item(st, n->extern_block.members); break;
        }
        d_list_end(st);
        n = n->next;
    }
}

static int run_emit_resolved(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=resolved <file>\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    const char *path = pos_argv[1];
    
    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    
    int rc = ax_pipeline_run(&st, AX_STAGE_RESOLVE);

    DumpState dst = { io->out, &st.interner, &st.resolve_map, 0 };
    d_item(&dst, st.parse_res.ast.items);
    fputs("\n", dst.out);

    ax_pipeline_free(&st);
    free(pos_argv);
    return rc;
}

const AxEmitter axemit_resolved = {
    "resolved",
    "dump the resolved AST",
    run_emit_resolved
};
