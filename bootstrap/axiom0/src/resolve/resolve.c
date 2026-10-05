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

typedef struct Symbol {
    AxSymbolId id;
    const void *node;
} Symbol;

AX_DEFINE_HASHMAP(SymEnv, uint32_t, Symbol, ax_key_hash_u32, ax_key_eq_u32);

typedef struct Scope {
    struct Scope *parent;
    SymEnv bindings;
    bool is_module_scope;
} Scope;

static Scope *push_scope(Env *env, Scope *parent) {
    Scope *s = ax_arena_alloc(env->arena, sizeof(Scope), 8);
    s->parent = parent;
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

static Symbol *declare_name(Env *env, Scope *scope, StrId name, const void *node) {
    AxSymbolId sym = new_symbol(env, node);
    if (name.v != 0) {
        if (SymEnv_contains(&scope->bindings, name.v)) {
            emit_diag(env, AX_NAME_DUPLICATE, node ? ((const AxAstExpr*)node)->span : (Span){0});
        } else {
            if (!scope->is_module_scope) {
                Scope *s = scope->parent;
                while (s) {
                    if (s->is_module_scope && SymEnv_contains(&s->bindings, name.v)) {
                        emit_diag(env, AX_NAME_SHADOW_MODULE, node ? ((const AxAstExpr*)node)->span : (Span){0});
                        break;
                    }
                    s = s->parent;
                }
            }
            Symbol s = { sym, node };
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
        if (head_node && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
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

static void resolve_pat(Env *env, Scope *scope, const AxAstPat *p, bool is_decl) {
    while (p) {
        switch (p->kind) {
            case AX_PAT_BINDING:
                if (is_decl) {
                    declare_name(env, scope, p->binding.name, p);
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
                    resolve_pat(env, scope, p->path.payload, is_decl);
                } else {
                    for (AxAstPatField *f = p->struct_pat.fields; f; f = f->next) {
                        if (f->pat) resolve_pat(env, scope, f->pat, is_decl);
                        else if (is_decl) declare_name(env, scope, f->name, f);
                    }
                }
                break;
            case AX_PAT_TUPLE:
                resolve_pat(env, scope, p->tuple.elems, is_decl);
                break;
            case AX_PAT_OR:
                resolve_pat(env, scope, p->or_pat.pats, is_decl);
                break;
            case AX_PAT_RANGE:
                resolve_pat(env, scope, p->range.start, is_decl);
                resolve_pat(env, scope, p->range.end, is_decl);
                break;
            default: break;
        }
        p = p->next;
    }
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
            case AX_EXPR_UNSAFE:
            case AX_EXPR_COMPTIME:
                resolve_block(env, scope, &e->block.block);
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
            case AX_EXPR_LOOP:
                resolve_block(env, scope, &e->loop.block);
                break;
            case AX_EXPR_WHILE:
                if (e->while_expr.let_pat) {
                    Scope *w_scope = push_scope(env, scope);
                    resolve_pat(env, w_scope, e->while_expr.let_pat, true);
                    resolve_expr(env, scope, e->while_expr.cond);
                    resolve_block(env, w_scope, &e->while_expr.block);
                } else {
                    resolve_expr(env, scope, e->while_expr.cond);
                    resolve_block(env, scope, &e->while_expr.block);
                }
                break;
            case AX_EXPR_FOR: {
                Scope *f_scope = push_scope(env, scope);
                resolve_pat(env, f_scope, e->for_expr.pat, true);
                resolve_expr(env, scope, e->for_expr.iter);
                resolve_block(env, f_scope, &e->for_expr.block);
                break;
            }
            case AX_EXPR_VIEW:
                resolve_expr(env, scope, e->view.expr);
                break;
            case AX_EXPR_CLOSURE: {
                Scope *c_scope = push_scope(env, scope);
                for(AxAstParam *p = e->closure.params; p; p = p->next) {
                    declare_name(env, c_scope, p->name, p);
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
                        if (((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
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

static void resolve_item_bodies(Env *env, Scope *scope, const AxAstItem *n) {
    while (n) {
        switch (n->kind) {
            case AX_ITEM_FN: {
                Scope *fn_scope = push_scope(env, scope);
                for(AxAstParam *p = n->fn.params; p; p = p->next) {
                    declare_name(env, fn_scope, p->name, p);
                    resolve_type(env, scope, p->type);
                }
                resolve_type(env, scope, n->fn.ret_type);
                if (n->fn.body) resolve_block(env, fn_scope, n->fn.body);
                break;
            }
            case AX_ITEM_STRUCT:
                if (n->struct_decl.is_tuple) {
                    resolve_type(env, scope, n->struct_decl.tuple_types);
                } else {
                    for(AxAstFieldDecl *f = n->struct_decl.struct_fields; f; f = f->next) {
                        resolve_type(env, scope, f->type);
                    }
                }
                break;
            case AX_ITEM_ENUM:
                for(AxAstVariantDecl *v = n->enum_decl.variants; v; v = v->next) {
                    if (v->is_struct) {
                        for(AxAstFieldDecl *f = v->struct_fields; f; f = f->next) {
                            resolve_type(env, scope, f->type);
                        }
                    } else {
                        resolve_type(env, scope, v->tuple_types);
                    }
                }
                break;
            case AX_ITEM_TRAIT:
                resolve_type(env, scope, n->trait.supertraits);
                resolve_item_bodies(env, push_scope(env, scope), n->trait.members); // Assuming members have their own scope
                break;
            case AX_ITEM_IMPL:
                resolve_type(env, scope, n->impl.trait_path);
                resolve_type(env, scope, n->impl.self_type);
                resolve_item_bodies(env, push_scope(env, scope), n->impl.members);
                break;
            case AX_ITEM_TYPE_ALIAS:
                resolve_type(env, scope, n->type_alias.type);
                break;
            case AX_ITEM_CONST:
                resolve_type(env, scope, n->const_decl.type);
                if (n->const_decl.expr) resolve_expr(env, scope, n->const_decl.expr);
                break;
            case AX_ITEM_STATIC:
                resolve_type(env, scope, n->static_decl.type);
                if (n->static_decl.expr) resolve_expr(env, scope, n->static_decl.expr);
                break;
            default: break;
        }
        n = n->next;
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
        declare_name(&env, prelude, id, NULL);
    }

    Scope *mod_scope = push_scope(&env, prelude);
    mod_scope->is_module_scope = true;

    // Phase A: Collect items
    const AxAstItem *it = ast->items;
    while (it) {
        switch (it->kind) {
            case AX_ITEM_FN: declare_name(&env, mod_scope, it->fn.name, it); break;
            case AX_ITEM_STRUCT: declare_name(&env, mod_scope, it->struct_decl.name, it); break;
            case AX_ITEM_ENUM: 
                declare_name(&env, mod_scope, it->enum_decl.name, it);
                for(AxAstVariantDecl *v = it->enum_decl.variants; v; v = v->next) {
                    AxSymbolId sym = new_symbol(&env, v);
                    bind_node(&env, v, sym);
                }
                break;
            case AX_ITEM_TRAIT: declare_name(&env, mod_scope, it->trait.name, it); break;
            case AX_ITEM_TYPE_ALIAS: declare_name(&env, mod_scope, it->type_alias.name, it); break;
            case AX_ITEM_CONST: declare_name(&env, mod_scope, it->const_decl.name, it); break;
            case AX_ITEM_STATIC: declare_name(&env, mod_scope, it->static_decl.name, it); break;
            default: break;
        }
        it = it->next;
    }

    // Phase B: Resolve bodies
    resolve_item_bodies(&env, mod_scope, ast->items);

    return map;
}
