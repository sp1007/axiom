#include "resolve/resolve.h"
#include <string.h>

void ax_resolve_map_init(AxResolveMap *map) {
    AxNodeMap_init(&map->node_map);
    map->next_symbol_v = 1;
}

void ax_resolve_map_free(AxResolveMap *map) {
    AxNodeMap_free(&map->node_map);
}

typedef struct Env {
    AxResolveMap *rmap;
    AxArena *arena;
    AxDiagSink *sink;
    StrInterner *interner;
    const void **symbol_nodes;
    size_t symbol_nodes_cap;
} Env;

typedef enum SymbolKind { SYM_ITEM, SYM_MODULE, SYM_LOCAL } SymbolKind;
typedef struct Symbol { AxSymbolId id; const void *node; SymbolKind kind; } Symbol;

AX_DEFINE_HASHMAP(SymEnv, uint32_t, Symbol, ax_key_hash_u32, ax_key_eq_u32);

typedef struct Scope {
    struct Scope *parent;
    SymEnv bindings;
    bool is_module_scope;
} Scope;

static Scope *push_scope(Env *env, Scope *parent) {
    Scope *s = ax_arena_alloc(env->arena, sizeof(Scope), 8);
    s->parent = parent;
    s->is_module_scope = false;
    SymEnv_init(&s->bindings);
    return s;
}

static AxSymbolId new_symbol(Env *env, const void *node) {
    AxSymbolId id = { env->rmap->next_symbol_v++ };
    if (id.v >= env->symbol_nodes_cap) {
        size_t new_cap = env->symbol_nodes_cap == 0 ? 64 : env->symbol_nodes_cap * 2;
        const void **new_nodes = ax_arena_alloc(env->arena, sizeof(void*) * new_cap, 8);
        if (env->symbol_nodes) {
            memcpy(new_nodes, env->symbol_nodes, sizeof(void*) * env->symbol_nodes_cap);
        }
        env->symbol_nodes = new_nodes;
        env->symbol_nodes_cap = new_cap;
    }
    env->symbol_nodes[id.v] = node;
    return id;
}

static void bind_node(Env *env, const void *node, AxSymbolId sym) {
    if (node) AxNodeMap_insert(&env->rmap->node_map, node, sym);
}

static void emit_diag(Env *env, AxDiagCode code, Span span) {
    AxDiagnostic d = {0};
    d.code = code;
    d.severity = ax_diag_code_severity(code);
    d.message = ax_diag_code_default_message(code);
    d.primary = span;
    ax_diag_sink_report(env->sink, &d);
}

static Symbol *declare_name(Env *env, Scope *scope, StrId name, const void *node, Span span, SymbolKind kind) {
    AxSymbolId sym = new_symbol(env, node);
    if (name.v != 0) {
        if (scope->is_module_scope && SymEnv_contains(&scope->bindings, name.v)) {
            emit_diag(env, AX_NAME_DUPLICATE, span);
        } else {
            if (!scope->is_module_scope) {
                Scope *s = scope->parent;
                while (s) {
                    if (s->is_module_scope) {
                        if (SymEnv_contains(&s->bindings, name.v)) {
                            emit_diag(env, AX_NAME_SHADOW_MODULE, span);
                            break;
                        }
                    }
                    s = s->parent;
                }
            }
            Symbol s = { sym, node, kind };
            SymEnv_insert(&scope->bindings, name.v, s);
        }
    }
    bind_node(env, node, sym);
    return name.v != 0 ? SymEnv_get(&scope->bindings, name.v) : NULL;
}

static Symbol *lookup_name(Scope *scope, StrId name) {
    while (scope) {
        Symbol *sym = SymEnv_get(&scope->bindings, name.v);
        if (sym) return sym;
        scope = scope->parent;
    }
    return NULL;
}

static void resolve_type(Env *env, Scope *scope, const AxAstType *t);
static void resolve_expr(Env *env, Scope *scope, const AxAstExpr *e);
static void resolve_pat(Env *env, Scope *scope, const AxAstPat *p, bool is_decl);
static void resolve_stmt(Env *env, Scope *scope, const AxAstStmt *s);
static void resolve_block(Env *env, Scope *scope, const AxAstBlock *b);

static void resolve_path_seg(Env *env, Scope *scope, const AxAstTypePathSegment *seg) {
    if (!seg) return;
    Symbol *sym = lookup_name(scope, seg->name);
    if (sym) {
        bind_node(env, seg, sym->id);
    } else {
        emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
        return;
    }
    
    const void *head_node = sym->node;
    seg = seg->next;
    
    while (seg) {
        if (sym->kind == SYM_ITEM && head_node && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
            const AxAstItem *en = (const AxAstItem*)head_node;
            bool found = false;
            for(AxAstVariantDecl *v = en->enum_decl.variants; v; v = v->next) {
                if (v->name.v == seg->name.v) {
                    AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                    if (v_id && v_id->v != 0) bind_node(env, seg, *v_id);
                    head_node = v;
                    found = true;
                    break;
                }
            }
            if (!found) {
                emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
                break;
            }
        } else {
            // Field access or something else on a type path? Shouldn't happen in canonical syntax for types.
            // If it's a module, we would resolve it here, but T014 is single-module.
            emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
            break;
        }
        seg = seg->next;
    }
}

static void resolve_type(Env *env, Scope *scope, const AxAstType *t) {
    while (t) {
        switch (t->kind) {
            case AX_TYPE_PATH:
                resolve_path_seg(env, scope, t->path.segments);
                break;
            case AX_TYPE_TUPLE:
                resolve_type(env, scope, t->tuple.elem_types);
                break;
            case AX_TYPE_ARRAY:
                resolve_expr(env, scope, t->array.count);
                resolve_type(env, scope, t->array.elem);
                break;
            case AX_TYPE_SLICE:
            case AX_TYPE_VIEW:
            case AX_TYPE_PTR:
                resolve_type(env, scope, t->view.elem); // view/ptr/slice have elem at same offset
                break;
            case AX_TYPE_FN:
                resolve_type(env, scope, t->fn.param_types);
                resolve_type(env, scope, t->fn.ret_type);
                break;
            case AX_TYPE_DYN:
                resolve_type(env, scope, t->dyn.bounds);
                break;
            default: break;
        }
        t = t->next;
    }
}

static void resolve_pat_inner(Env *env, Scope *scope, SymEnv *pat_env, const AxAstPat *p, bool is_decl) {
    while (p) {
        switch (p->kind) {
            case AX_PAT_BINDING:
                if (is_decl) {
                    if (SymEnv_contains(pat_env, p->binding.name.v)) {
                        emit_diag(env, AX_NAME_DUPLICATE_BINDING, p->span);
                    } else {
                        Symbol *s = declare_name(env, scope, p->binding.name, p, p->span, SYM_LOCAL);
                        if (s) {
                            Symbol copied = *s;
                            SymEnv_insert(pat_env, p->binding.name.v, copied);
                        }
                    }
                } else {
                    Symbol *sym = lookup_name(scope, p->binding.name);
                    if (sym) bind_node(env, p, sym->id);
                    else emit_diag(env, AX_NAME_UNRESOLVED, p->span);
                }
                break;
            case AX_PAT_PATH:
            case AX_PAT_STRUCT:
                resolve_path_seg(env, scope, p->path.segments); // Struct has same offset
                if (p->kind == AX_PAT_PATH) {
                    resolve_pat_inner(env, scope, pat_env, p->path.payload, is_decl);
                } else {
                    for (AxAstPatField *f = p->struct_pat.fields; f; f = f->next) {
                        if (f->pat) resolve_pat_inner(env, scope, pat_env, f->pat, is_decl);
                        else if (is_decl) {
                            if (SymEnv_contains(pat_env, f->name.v)) {
                                emit_diag(env, AX_NAME_DUPLICATE_BINDING, f->span);
                            } else {
                                Symbol *s = declare_name(env, scope, f->name, f, f->span, SYM_LOCAL);
                                if (s) {
                                    Symbol copied = *s;
                                    SymEnv_insert(pat_env, f->name.v, copied);
                                }
                            }
                        }
                    }
                }
                break;
            case AX_PAT_TUPLE:
                resolve_pat_inner(env, scope, pat_env, p->tuple.elems, is_decl);
                break;
            case AX_PAT_OR: {
                SymEnv base_env; SymEnv_init(&base_env);
                resolve_pat_inner(env, scope, &base_env, p->or_pat.pats, is_decl);
                for (AxAstPat *alt = p->or_pat.pats->next; alt; alt = alt->next) {
                    SymEnv alt_env; SymEnv_init(&alt_env);
                    resolve_pat_inner(env, scope, &alt_env, alt, is_decl);
                    uint32_t cur = 0; void *raw_e;
                    while (ax_rawmap_next(&base_env.raw, &cur, &raw_e)) {
                        SymEnvEntry *e = (SymEnvEntry*)raw_e;
                        if (!SymEnv_contains(&alt_env, e->key)) {
                            emit_diag(env, AX_NAME_OR_PATTERN_MISMATCH, alt->span);
                        }
                    }
                    cur = 0;
                    while (ax_rawmap_next(&alt_env.raw, &cur, &raw_e)) {
                        SymEnvEntry *e = (SymEnvEntry*)raw_e;
                        if (!SymEnv_contains(&base_env, e->key)) {
                            emit_diag(env, AX_NAME_OR_PATTERN_MISMATCH, alt->span);
                        }
                    }
                }
                uint32_t cur = 0; void *raw_e;
                while (ax_rawmap_next(&base_env.raw, &cur, &raw_e)) {
                    SymEnvEntry *e = (SymEnvEntry*)raw_e;
                    if (SymEnv_contains(pat_env, e->key)) {
                        emit_diag(env, AX_NAME_DUPLICATE_BINDING, p->span);
                    } else {
                        SymEnv_insert(pat_env, e->key, e->value);
                    }
                }
                break;
            }
            case AX_PAT_RANGE:
                resolve_pat_inner(env, scope, pat_env, p->range.start, is_decl);
                resolve_pat_inner(env, scope, pat_env, p->range.end, is_decl);
                break;
            default: break;
        }
        p = p->next;
    }
}

static void resolve_pat(Env *env, Scope *scope, const AxAstPat *p, bool is_decl) {
    SymEnv pat_env; SymEnv_init(&pat_env);
    resolve_pat_inner(env, scope, &pat_env, p, is_decl);
}

static void resolve_expr(Env *env, Scope *scope, const AxAstExpr *e) {
    while (e) {
        switch (e->kind) {
            case AX_EXPR_PATH:
                resolve_path_seg(env, scope, e->path.segments);
                break;
            case AX_EXPR_PAREN:
                resolve_expr(env, scope, e->paren.expr);
                break;
            case AX_EXPR_ARRAY:
                resolve_expr(env, scope, e->array.elems);
                resolve_expr(env, scope, e->array.count);
                break;
            case AX_EXPR_STRUCT:
                resolve_path_seg(env, scope, e->struct_lit.segments);
                for(AxAstFieldInit *f = e->struct_lit.fields; f; f = f->next) {
                    if (f->expr) resolve_expr(env, scope, f->expr);
                    else {
                        // shorthand: name is resolved as an expression in current scope
                        Symbol *sym = lookup_name(scope, f->name);
                        if (sym) bind_node(env, f, sym->id);
                        else emit_diag(env, AX_NAME_UNRESOLVED, f->span);
                    }
                }
                break;
            case AX_EXPR_BLOCK:
                resolve_block(env, scope, &e->block.block);
                break;
            case AX_EXPR_UNSAFE:
                resolve_block(env, scope, &e->unsafe_block.block);
                break;
            case AX_EXPR_IF:
                if (e->if_expr.let_pat) {
                    Scope *if_scope = push_scope(env, scope);
                    resolve_pat(env, if_scope, e->if_expr.let_pat, true);
                    resolve_expr(env, scope, e->if_expr.cond);
                    resolve_block(env, if_scope, &e->if_expr.block);
                } else {
                    resolve_expr(env, scope, e->if_expr.cond);
                    resolve_block(env, scope, &e->if_expr.block);
                }
                if (e->if_expr.else_branch) resolve_expr(env, scope, e->if_expr.else_branch);
                break;
            case AX_EXPR_MATCH:
                resolve_expr(env, scope, e->match.expr);
                for (AxAstMatchArm *a = e->match.arms; a; a = a->next) {
                    Scope *arm_scope = push_scope(env, scope);
                    resolve_pat(env, arm_scope, a->pat, true);
                    if (a->guard) resolve_expr(env, arm_scope, a->guard);
                    resolve_expr(env, arm_scope, a->body);
                }
                break;
            case AX_EXPR_LOOP: {
                Scope *l_scope = push_scope(env, scope);
                if (e->loop.label.v != 0) declare_name(env, l_scope, e->loop.label, e, e->span, SYM_LOCAL);
                resolve_block(env, l_scope, &e->loop.block);
                break;
            }
            case AX_EXPR_WHILE: {
                Scope *l_scope = push_scope(env, scope);
                if (e->while_expr.label.v != 0) declare_name(env, l_scope, e->while_expr.label, e, e->span, SYM_LOCAL);
                if (e->while_expr.let_pat) {
                    Scope *w_scope = push_scope(env, l_scope);
                    resolve_pat(env, w_scope, e->while_expr.let_pat, true);
                    resolve_expr(env, l_scope, e->while_expr.cond);
                    resolve_block(env, w_scope, &e->while_expr.block);
                } else {
                    resolve_expr(env, l_scope, e->while_expr.cond);
                    resolve_block(env, l_scope, &e->while_expr.block);
                }
                break;
            }
            case AX_EXPR_FOR: {
                Scope *l_scope = push_scope(env, scope);
                if (e->for_expr.label.v != 0) declare_name(env, l_scope, e->for_expr.label, e, e->span, SYM_LOCAL);
                Scope *f_scope = push_scope(env, l_scope);
                resolve_pat(env, f_scope, e->for_expr.pat, true);
                resolve_expr(env, l_scope, e->for_expr.iter);
                resolve_block(env, f_scope, &e->for_expr.block);
                break;
            }
            case AX_EXPR_VIEW:
                resolve_expr(env, scope, e->view.expr);
                break;
            case AX_EXPR_COMPTIME:
                resolve_block(env, scope, &e->comptime.block);
                break;
            case AX_EXPR_JUMP:
                if (e->jump.label.v != 0) {
                    Symbol *sym = lookup_name(scope, e->jump.label);
                    if (sym) bind_node(env, e, sym->id);
                    else emit_diag(env, AX_NAME_UNRESOLVED, e->span);
                }
                if (e->jump.expr) resolve_expr(env, scope, e->jump.expr);
                break;
            case AX_EXPR_CLOSURE: {
                Scope *c_scope = push_scope(env, scope);
                for(AxAstParam *p = e->closure.params; p; p = p->next) {
                    declare_name(env, c_scope, p->name, p, p->span, SYM_LOCAL);
                    resolve_type(env, scope, p->type);
                }
                resolve_type(env, scope, e->closure.ret_type);
                resolve_expr(env, c_scope, e->closure.body);
                break;
            }
            case AX_EXPR_RANGE:
                resolve_expr(env, scope, e->range.start);
                resolve_expr(env, scope, e->range.end);
                break;
            case AX_EXPR_BINARY:
                resolve_expr(env, scope, e->binary.left);
                resolve_expr(env, scope, e->binary.right);
                break;
            case AX_EXPR_UNARY:
                resolve_expr(env, scope, e->unary.expr);
                break;
            case AX_EXPR_CAST:
                resolve_expr(env, scope, e->cast.expr);
                resolve_type(env, scope, e->cast.type);
                break;
            case AX_EXPR_POSTFIX: {
                resolve_expr(env, scope, e->postfix.head);
                
                const void *head_node = NULL;
                if (e->postfix.head->kind == AX_EXPR_PATH && e->postfix.head->path.segments) {
                    AxSymbolId *id = AxNodeMap_get(&env->rmap->node_map, e->postfix.head->path.segments);
                    if (id && id->v != 0 && id->v < env->symbol_nodes_cap) {
                        head_node = env->symbol_nodes[id->v];
                    }
                }
                
                for (AxAstPostfixSeg *s = e->postfix.segments; s; s = s->next) {
                    if (s->kind == AX_POSTFIX_FIELD && head_node) {
                        SymbolKind hkind = SYM_LOCAL;
                        if (e->postfix.head->kind == AX_EXPR_PATH && e->postfix.head->path.segments) {
                            Symbol *hsym = lookup_name(scope, e->postfix.head->path.segments->name);
                            if (hsym) hkind = hsym->kind;
                        }
                        if (hkind == SYM_ITEM && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
                            const AxAstItem *en = (const AxAstItem*)head_node;
                            bool found = false;
                            for(AxAstVariantDecl *v = en->enum_decl.variants; v; v = v->next) {
                                if (v->name.v == s->field.name.v) {
                                    AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                                    if (v_id && v_id->v != 0) bind_node(env, s, *v_id);
                                    head_node = v; // next segments (if any) apply to this variant
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                emit_diag(env, AX_NAME_UNRESOLVED, e->span); // AX_NAME_UNRESOLVED
                                head_node = NULL;
                            }
                        } else if (hkind == SYM_MODULE) {
                            emit_diag(env, AX_NAME_UNRESOLVED, e->span);
                            head_node = NULL;
                        } else {
                            head_node = NULL;
                        }
                    } else if (s->kind == AX_POSTFIX_CALL) {
                        resolve_expr(env, scope, s->call.args);
                        head_node = NULL;
                    } else if (s->kind == AX_POSTFIX_INDEX) {
                        resolve_expr(env, scope, s->index.arg);
                        head_node = NULL;
                    } else {
                        head_node = NULL;
                    }
                }
                break;
            }
            default: break;
        }
        e = e->next;
    }
}

static void resolve_stmt(Env *env, Scope *scope, const AxAstStmt *s) {
    while (s) {
        switch (s->kind) {
            case AX_STMT_LET:
                if (s->let.expr) resolve_expr(env, scope, s->let.expr);
                resolve_type(env, scope, s->let.type);
                resolve_pat(env, scope, s->let.pat, true);
                if (s->let.else_block) resolve_block(env, scope, s->let.else_block);
                break;
            case AX_STMT_ASSIGN:
                resolve_expr(env, scope, s->assign.left);
                resolve_expr(env, scope, s->assign.right);
                break;
            case AX_STMT_EXPR:
                resolve_expr(env, scope, s->expr_stmt.expr);
                break;
            default: break;
        }
        s = s->next;
    }
}

static void resolve_block(Env *env, Scope *parent, const AxAstBlock *b) {
    Scope *scope = push_scope(env, parent);
    resolve_stmt(env, scope, b->stmts);
}

static void resolve_generic_params(Env *env, Scope *scope, const AxAstGenericParams *gps) {
    if (!gps) return;
    for (AxAstGenericParam *gp = gps->params; gp; gp = gp->next) {
        declare_name(env, scope, gp->name, gp, gp->span, SYM_LOCAL);
    }
    for (AxAstGenericParam *gp = gps->params; gp; gp = gp->next) {
        resolve_type(env, scope, gp->bounds);
    }
}

static void resolve_where_clause(Env *env, Scope *scope, const AxAstWhereClause *w) {
    if (!w) return;
    for (AxAstWherePred *p = w->preds; p; p = p->next) {
        resolve_type(env, scope, p->type);
        resolve_type(env, scope, p->bounds);
    }
}

static void resolve_item_bodies(Env *env, Scope *scope, const AxAstItem *n) {
    while (n) {
        switch (n->kind) {
            case AX_ITEM_FN: {
                Scope *fn_scope = push_scope(env, scope);
                resolve_generic_params(env, fn_scope, n->fn.generic_params);
                resolve_where_clause(env, fn_scope, n->fn.where_clause);
                for(AxAstParam *p = n->fn.params; p; p = p->next) {
                    declare_name(env, fn_scope, p->name, p, p->span, SYM_LOCAL);
                    resolve_type(env, fn_scope, p->type);
                }
                resolve_type(env, fn_scope, n->fn.ret_type);
                if (n->fn.body) resolve_block(env, fn_scope, n->fn.body);
                break;
            }
            case AX_ITEM_STRUCT: {
                Scope *s_scope = push_scope(env, scope);
                resolve_generic_params(env, s_scope, n->struct_decl.generic_params);
                resolve_where_clause(env, s_scope, n->struct_decl.where_clause);
                if (n->struct_decl.is_tuple) {
                    resolve_type(env, s_scope, n->struct_decl.tuple_types);
                } else {
                    for(AxAstFieldDecl *f = n->struct_decl.struct_fields; f; f = f->next) {
                        resolve_type(env, s_scope, f->type);
                    }
                }
                break;
            }
            case AX_ITEM_ENUM: {
                Scope *e_scope = push_scope(env, scope);
                resolve_generic_params(env, e_scope, n->enum_decl.generic_params);
                resolve_where_clause(env, e_scope, n->enum_decl.where_clause);
                for(AxAstVariantDecl *v = n->enum_decl.variants; v; v = v->next) {
                    if (v->is_struct) {
                        for(AxAstFieldDecl *f = v->struct_fields; f; f = f->next) {
                            resolve_type(env, e_scope, f->type);
                        }
                    } else {
                        resolve_type(env, e_scope, v->tuple_types);
                    }
                }
                break;
            }
            case AX_ITEM_TRAIT: {
                Scope *t_scope = push_scope(env, scope);
                declare_name(env, t_scope, ax_intern_cstr(env->interner, "Self"), n, n->span, SYM_LOCAL);
                resolve_generic_params(env, t_scope, n->trait.generic_params);
                resolve_type(env, t_scope, n->trait.supertraits);
                resolve_where_clause(env, t_scope, n->trait.where_clause);
                resolve_item_bodies(env, t_scope, n->trait.members);
                break;
            }
            case AX_ITEM_IMPL: {
                Scope *i_scope = push_scope(env, scope);
                declare_name(env, i_scope, ax_intern_cstr(env->interner, "Self"), n, n->span, SYM_LOCAL);
                resolve_generic_params(env, i_scope, n->impl.generic_params);
                resolve_type(env, i_scope, n->impl.trait_path);
                resolve_type(env, i_scope, n->impl.self_type);
                resolve_where_clause(env, i_scope, n->impl.where_clause);
                resolve_item_bodies(env, i_scope, n->impl.members);
                break;
            }
            case AX_ITEM_TYPE_ALIAS: {
                Scope *a_scope = push_scope(env, scope);
                resolve_generic_params(env, a_scope, n->type_alias.generic_params);
                resolve_type(env, a_scope, n->type_alias.type);
                break;
            }
            case AX_ITEM_CONST:
                resolve_type(env, scope, n->const_decl.type);
                if (n->const_decl.expr) resolve_expr(env, scope, n->const_decl.expr);
                break;
            case AX_ITEM_STATIC:
                resolve_type(env, scope, n->static_decl.type);
                if (n->static_decl.expr) resolve_expr(env, scope, n->static_decl.expr);
                break;
            case AX_ITEM_EXTERN_BLOCK:
                resolve_item_bodies(env, scope, n->extern_block.members);
                break;
            default: break;
        }
        n = n->next;
    }
}

static void resolve_use_tree(Env *env, Scope *scope, const AxAstUseTree *tree, const AxAstItem *item) {
    while (tree) {
        const AxAstDottedName *path = &tree->path;
        if (path->count > 0) {
            Symbol *sym = lookup_name(scope, path->segments[0]);
            if (!sym) {
                emit_diag(env, AX_NAME_UNRESOLVED, path->span);
                tree = tree->next;
                continue;
            }
            
            const void *head_node = sym->node;
            AxSymbolId final_sym = sym->id;
            
            bool error = false;
            for (size_t i = 1; i < path->count; i++) {
                if (sym->kind == SYM_ITEM && head_node && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
                    const AxAstItem *en = (const AxAstItem*)head_node;
                    bool found = false;
                    for(AxAstVariantDecl *v = en->enum_decl.variants; v; v = v->next) {
                        if (v->name.v == path->segments[i].v) {
                            AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                            if (v_id && v_id->v != 0) {
                                final_sym = *v_id;
                            }
                            head_node = v;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        emit_diag(env, AX_NAME_UNRESOLVED, path->span);
                        error = true;
                        break;
                    }
                } else {
                    emit_diag(env, AX_NAME_UNRESOLVED, path->span);
                    error = true;
                    break;
                }
            }
            
            if (!error) {
                bind_node(env, tree, final_sym);
                bind_node(env, path, final_sym);
                if (item) bind_node(env, item, final_sym);
                
                StrId alias = tree->alias;
                if (alias.v == 0) {
                    alias = path->segments[path->count - 1];
                }
                
                if (SymEnv_contains(&scope->bindings, alias.v)) {
                    emit_diag(env, AX_NAME_DUPLICATE, tree->span);
                } else {
                    Symbol s = { final_sym, head_node, sym->kind };
                    SymEnv_insert(&scope->bindings, alias.v, s);
                }
            }
        }
        
        if (tree->subtrees) {
            resolve_use_tree(env, scope, tree->subtrees, NULL);
        }
        tree = tree->next;
    }
}

AxResolveMap ax_resolve(AxAst *ast, AxArena *arena, AxDiagSink *sink, StrInterner *interner) {
    AxResolveMap map;
    ax_resolve_map_init(&map);

    Env env = { &map, arena, sink, interner, NULL, 0 };
    
    Scope *prelude = push_scope(&env, NULL);
    prelude->is_module_scope = true;
    // Add prelude types
    const char *prelude_types[] = {
        "bool", "i32", "u32", "usize", "Option", "Result", 
        "Copy", "Drop", "Send", "Share", "f32", "f64", "char", "str",
        "u8", "i8", "u16", "i16", "u64", "i64"
    };
    for(size_t i=0; i<sizeof(prelude_types)/sizeof(prelude_types[0]); i++) {
        StrId id = ax_intern_cstr(interner, prelude_types[i]);
        declare_name(&env, prelude, id, NULL, (Span){0}, SYM_ITEM);
    }

    Scope *mod_scope = push_scope(&env, prelude);
    mod_scope->is_module_scope = true;

    // Phase A: Collect items
    const AxAstItem *it = ast->items;
    while (it) {
        switch (it->kind) {
            case AX_ITEM_FN: declare_name(&env, mod_scope, it->fn.name, it, it->span, SYM_ITEM); break;
            case AX_ITEM_MODULE:
                if (it->module.path.count > 0) {
                    declare_name(&env, mod_scope, it->module.path.segments[0], it, it->span, SYM_MODULE);
                }
                break;
            case AX_ITEM_STRUCT: declare_name(&env, mod_scope, it->struct_decl.name, it, it->span, SYM_ITEM); break;
            case AX_ITEM_ENUM: 
                declare_name(&env, mod_scope, it->enum_decl.name, it, it->span, SYM_ITEM);
                for(AxAstVariantDecl *v = it->enum_decl.variants; v; v = v->next) {
                    AxSymbolId sym = new_symbol(&env, v);
                    bind_node(&env, v, sym);
                }
                break;
            case AX_ITEM_TRAIT: declare_name(&env, mod_scope, it->trait.name, it, it->span, SYM_ITEM); break;
            case AX_ITEM_TYPE_ALIAS: declare_name(&env, mod_scope, it->type_alias.name, it, it->span, SYM_ITEM); break;
            case AX_ITEM_CONST: declare_name(&env, mod_scope, it->const_decl.name, it, it->span, SYM_ITEM); break;
            case AX_ITEM_STATIC: declare_name(&env, mod_scope, it->static_decl.name, it, it->span, SYM_ITEM); break;
            default: break;
        }
        it = it->next;
    }

    // Phase A.5: Resolve imports
    it = ast->items;
    while (it) {
        if (it->kind == AX_ITEM_USE) {
            resolve_use_tree(&env, mod_scope, it->use.tree, it);
        }
        it = it->next;
    }

    // Phase B: Resolve bodies
    resolve_item_bodies(&env, mod_scope, ast->items);

    return map;
}
