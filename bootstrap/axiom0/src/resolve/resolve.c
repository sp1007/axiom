#include "resolve/resolve.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct NamingCtx {
    char **module_paths;
    char **canonical_names;
    size_t cap;
} NamingCtx;

void ax_resolve_map_init(AxResolveMap *map) {
    AxNodeMap_init(&map->node_map);
    AxNodeMap_init(&map->module_access_nodes);
    map->next_symbol_v = 1;
    map->next_std_symbol_v = 10000;
    map->module_naming_ctx = NULL;
}

void ax_resolve_map_free(AxResolveMap *map) {
    AxNodeMap_free(&map->module_access_nodes);
    AxNodeMap_free(&map->node_map);
    if (map->module_naming_ctx) {
        NamingCtx *ctx = (NamingCtx*)map->module_naming_ctx;
        for (size_t i = 0; i < ctx->cap; i++) {
            if (ctx->module_paths && ctx->module_paths[i]) free(ctx->module_paths[i]);
            if (ctx->canonical_names && ctx->canonical_names[i]) free(ctx->canonical_names[i]);
        }
        if (ctx->module_paths) free(ctx->module_paths);
        if (ctx->canonical_names) free(ctx->canonical_names);
        free(ctx);
        map->module_naming_ctx = NULL;
    }
}

StrView ax_resolve_symbol_module_path(const AxResolveMap *map, AxSymbolId sym) {
    if (!map || sym.v == 0) return (StrView){0, 0};
    NamingCtx *ctx = (NamingCtx*)map->module_naming_ctx;
    if (!ctx || sym.v >= ctx->cap || !ctx->module_paths || !ctx->module_paths[sym.v]) return (StrView){0, 0};
    return ax_sv_cstr(ctx->module_paths[sym.v]);
}

StrView ax_resolve_symbol_canonical_name(const AxResolveMap *map, AxSymbolId sym) {
    if (!map || sym.v == 0) return (StrView){0, 0};
    NamingCtx *ctx = (NamingCtx*)map->module_naming_ctx;
    if (!ctx || sym.v >= ctx->cap || !ctx->canonical_names || !ctx->canonical_names[sym.v]) return (StrView){0, 0};
    return ax_sv_cstr(ctx->canonical_names[sym.v]);
}

typedef enum SymbolKind {
    SYM_ITEM,
    SYM_MODULE,
    SYM_LOCAL
} SymbolKind;

typedef struct Module Module;

typedef struct Symbol {
    AxSymbolId id;
    const void *node;
    SymbolKind kind;
    AxAstVisKind vis;
    Module *def_module;
} Symbol;

AX_DEFINE_HASHMAP(SymEnv, uint32_t, Symbol, ax_key_hash_u32, ax_key_eq_u32);

typedef struct Scope {
    struct Scope *parent;
    SymEnv bindings;
    bool is_module_scope;
} Scope;

typedef struct ModuleUseItem {
    const AxAstItem *item;
    struct ModuleUseItem *next;
} ModuleUseItem;

struct Module {
    StrId name;
    char full_path[256];
    Scope *scope;
    Module *parent;
    Module *next;
    SymEnv submodules;
    SymEnv exports;
    bool is_std;
    ModuleUseItem *use_items;
};

typedef struct Env {
    AxResolveMap *rmap;
    AxArena *arena;
    AxDiagSink *sink;
    StrInterner *interner;
    const void **symbol_nodes;
    size_t symbol_nodes_cap;
    Module *root_module;
    Module *modules_list;
    Module *current_module;
    Scope *prelude_scope;
    NamingCtx *naming;
    AxNodeMap resolved_use_trees;
    const AxAst *ast;
} Env;

static Scope *push_scope(Env *env, Scope *parent) {
    Scope *s = ax_arena_alloc(env->arena, sizeof(Scope), 8);
    s->parent = parent;
    s->is_module_scope = false;
    SymEnv_init(&s->bindings);
    return s;
}

static AxSymbolId new_symbol(Env *env, const void *node) {
    bool is_std = (env->current_module && env->current_module->is_std);
    if (!env->rmap->next_std_symbol_v) {
        env->rmap->next_std_symbol_v = 10000;
    }
    uint32_t val = is_std ? env->rmap->next_std_symbol_v++ : env->rmap->next_symbol_v++;
    AxSymbolId id = { val };
    if (id.v >= env->symbol_nodes_cap) {
        size_t new_cap = env->symbol_nodes_cap == 0 ? 64 : env->symbol_nodes_cap * 2;
        while (new_cap <= id.v) new_cap *= 2;
        const void **new_nodes = ax_arena_alloc(env->arena, sizeof(void*) * new_cap, 8);
        if (env->symbol_nodes) {
            memcpy(new_nodes, env->symbol_nodes, sizeof(void*) * env->symbol_nodes_cap);
        }
        env->symbol_nodes = new_nodes;
        env->symbol_nodes_cap = new_cap;
    }
    env->symbol_nodes[id.v] = node;

    /* Expand naming metadata table */
    if (env->naming) {
        if (id.v >= env->naming->cap) {
            size_t new_cap = env->naming->cap == 0 ? 64 : env->naming->cap * 2;
            while (new_cap <= id.v) new_cap *= 2;
            env->naming->module_paths = realloc(env->naming->module_paths, new_cap * sizeof(char *));
            env->naming->canonical_names = realloc(env->naming->canonical_names, new_cap * sizeof(char *));
            for (size_t i = env->naming->cap; i < new_cap; i++) {
                env->naming->module_paths[i] = NULL;
                env->naming->canonical_names[i] = NULL;
            }
            env->naming->cap = new_cap;
        }
    }

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

static void record_symbol_naming(Env *env, AxSymbolId sym, const char *mod_path, const char *canon_name) {
    if (!env->naming || sym.v >= env->naming->cap) return;
    if (mod_path) {
        if (env->naming->module_paths[sym.v]) free(env->naming->module_paths[sym.v]);
        env->naming->module_paths[sym.v] = strdup(mod_path);
    }
    if (canon_name) {
        if (env->naming->canonical_names[sym.v]) free(env->naming->canonical_names[sym.v]);
        env->naming->canonical_names[sym.v] = strdup(canon_name);
    }
}

static Module *create_module(Env *env, const char *full_path, StrId name, Module *parent) {
    Module *m = ax_arena_alloc(env->arena, sizeof(Module), 8);
    m->name = name;
    snprintf(m->full_path, sizeof(m->full_path), "%s", full_path);
    m->scope = push_scope(env, env->prelude_scope);
    m->scope->is_module_scope = true;
    m->parent = parent;
    m->next = env->modules_list;
    env->modules_list = m;
    SymEnv_init(&m->submodules);
    SymEnv_init(&m->exports);
    m->use_items = NULL;
    m->is_std = (strncmp(full_path, "std", 3) == 0 && (full_path[3] == '.' || full_path[3] == '\0'));
    return m;
}

static Module *get_or_create_module(Env *env, const AxAstDottedName *path) {
    if (!path || path->count == 0) return env->root_module;
    Module *curr = env->root_module;
    char path_buf[256] = "";

    for (size_t i = 0; i < path->count; i++) {
        StrId seg = path->segments[i];
        StrView sv = ax_interner_get(env->interner, seg);
        if (i == 0) {
            snprintf(path_buf, sizeof(path_buf), "%.*s", (int)sv.len, sv.ptr);
        } else {
            size_t cur_len = strlen(path_buf);
            snprintf(path_buf + cur_len, sizeof(path_buf) - cur_len, ".%.*s", (int)sv.len, sv.ptr);
        }

        Symbol *existing = SymEnv_get(&curr->submodules, seg.v);
        if (existing) {
            curr = (Module*)existing->node;
        } else {
            Module *next_mod = create_module(env, path_buf, seg, curr);
            Module *saved = env->current_module;
            env->current_module = next_mod;
            Symbol s = { new_symbol(env, next_mod), next_mod, SYM_MODULE, AX_VIS_PUB, curr };
            env->current_module = saved;
            SymEnv_insert(&curr->submodules, seg.v, s);

            /* Also register top-level modules in root module's scope */
            if (curr == env->root_module) {
                SymEnv_insert(&env->root_module->scope->bindings, seg.v, s);
            }
            curr = next_mod;
        }
    }
    return curr;
}

static Symbol *declare_name_vis(Env *env, Scope *scope, StrId name, const void *node, Span span, SymbolKind kind, AxAstVisKind vis) {
    AxSymbolId sym = new_symbol(env, node);
    if (name.v != 0) {
        if (scope->is_module_scope && SymEnv_contains(&scope->bindings, name.v)) {
            emit_diag(env, AX_NAME_DUPLICATE, span);
        } else {
            if (!scope->is_module_scope) {
                bool shadowed = false;
                Scope *s = scope->parent;
                while (s) {
                    if (s->is_module_scope) {
                        if (SymEnv_contains(&s->bindings, name.v)) {
                            emit_diag(env, AX_NAME_SHADOW_MODULE, span);
                            shadowed = true;
                            break;
                        }
                    }
                    s = s->parent;
                }
                if (!shadowed && env->current_module && env->current_module->name.v == name.v) {
                    emit_diag(env, AX_NAME_SHADOW_MODULE, span);
                    shadowed = true;
                }
                if (!shadowed && env->root_module && SymEnv_contains(&env->root_module->submodules, name.v)) {
                    emit_diag(env, AX_NAME_SHADOW_MODULE, span);
                    shadowed = true;
                }
            }
            Symbol s = { sym, node, kind, vis, env->current_module };
            SymEnv_insert(&scope->bindings, name.v, s);
        }
    }
    bind_node(env, node, sym);
    return name.v != 0 ? SymEnv_get(&scope->bindings, name.v) : NULL;
}

static Symbol *declare_name(Env *env, Scope *scope, StrId name, const void *node, Span span, SymbolKind kind) {
    return declare_name_vis(env, scope, name, node, span, kind, AX_VIS_PRIVATE);
}

static Symbol *lookup_name(Env *env, Scope *scope, StrId name) {
    /* 1. Walk lexical scopes up to module / prelude */
    Scope *s = scope;
    while (s) {
        Symbol *sym = SymEnv_get(&s->bindings, name.v);
        if (sym) return sym;
        s = s->parent;
    }

    /* 2. Check sibling submodules if current module has a parent */
    if (env->current_module && env->current_module->parent) {
        Symbol *sym = SymEnv_get(&env->current_module->parent->submodules, name.v);
        if (sym) return sym;
    }

    /* 3. Check top-level submodules in root */
    if (env->root_module) {
        Symbol *sym = SymEnv_get(&env->root_module->submodules, name.v);
        if (sym) return sym;
    }

    /* 4. Check prelude scope */
    if (env->prelude_scope) {
        Symbol *sym = SymEnv_get(&env->prelude_scope->bindings, name.v);
        if (sym) return sym;
    }

    return NULL;
}

static bool check_visibility(Env *env, Module *from_mod, const Symbol *target, Span span) {
    if (!target || !target->def_module) return true;
    if (target->def_module == from_mod) return true;

    if (target->vis == AX_VIS_PRIVATE || target->vis == AX_VIS_PUB_MODULE) {
        emit_diag(env, AX_NAME_PRIVATE, span);
        return false;
    }

    if (target->vis == AX_VIS_PUB_PACKAGE) {
        if (from_mod && (from_mod->is_std != target->def_module->is_std)) {
            emit_diag(env, AX_NAME_PRIVATE, span);
            return false;
        }
        if (from_mod) {
            const char *dot_from = strchr(from_mod->full_path, '.');
            const char *dot_target = strchr(target->def_module->full_path, '.');
            size_t pkg_from_len = dot_from ? (size_t)(dot_from - from_mod->full_path) : strlen(from_mod->full_path);
            size_t pkg_target_len = dot_target ? (size_t)(dot_target - target->def_module->full_path) : strlen(target->def_module->full_path);
            if (pkg_from_len != pkg_target_len || memcmp(from_mod->full_path, target->def_module->full_path, pkg_from_len) != 0) {
                emit_diag(env, AX_NAME_PRIVATE, span);
                return false;
            }
        }
    }

    return true;
}

static void resolve_type(Env *env, Scope *scope, const AxAstType *t);
static void resolve_expr(Env *env, Scope *scope, const AxAstExpr *e);
static void resolve_pat(Env *env, Scope *scope, const AxAstPat *p, bool is_decl);
static void resolve_stmt(Env *env, Scope *scope, const AxAstStmt *s);
static void resolve_block(Env *env, Scope *scope, const AxAstBlock *b);

static void resolve_path_seg(Env *env, Scope *scope, const AxAstTypePathSegment *seg) {
    if (!seg) return;
    Symbol *sym = lookup_name(env, scope, seg->name);
    if (sym) {
        bind_node(env, seg, sym->id);
    } else {
        emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
        return;
    }

    const void *head_node = sym->node;
    SymbolKind hkind = sym->kind;
    Module *curr_mod = (hkind == SYM_MODULE) ? (Module*)head_node : NULL;
    seg = seg->next;

    while (seg) {
        if (hkind == SYM_MODULE && curr_mod) {
            /* Look for submodule or exported item in curr_mod */
            Symbol *sub = SymEnv_get(&curr_mod->submodules, seg->name.v);
            if (sub) {
                bind_node(env, seg, sub->id);
                curr_mod = (Module*)sub->node;
                head_node = sub->node;
                hkind = SYM_MODULE;
            } else {
                Symbol *exp = SymEnv_get(&curr_mod->exports, seg->name.v);
                if (exp) {
                    check_visibility(env, env->current_module, exp, seg->span);
                    bind_node(env, seg, exp->id);
                    head_node = exp->node;
                    hkind = exp->kind;
                    curr_mod = NULL;
                } else if (SymEnv_contains(&curr_mod->scope->bindings, seg->name.v)) {
                    /* Exists but is private */
                    emit_diag(env, AX_NAME_PRIVATE, seg->span);
                    break;
                } else {
                    emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
                    break;
                }
            }
        } else if (hkind == SYM_ITEM && head_node && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
            const AxAstItem *en = (const AxAstItem*)head_node;
            bool found = false;
            for (AxAstVariantDecl *v = en->enum_decl.variants; v; v = v->next) {
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
        } else if (head_node) {
            const AxAstItem *target_item = (const AxAstItem*)head_node;
            const AxAstItem *found_member = NULL;
            if (target_item->kind == AX_ITEM_IMPL) {
                for (const AxAstItem *m = target_item->impl.members; m; m = m->next) {
                    StrId mname = {0};
                    if (m->kind == AX_ITEM_FN) mname = m->fn.name;
                    else if (m->kind == AX_ITEM_TYPE_ALIAS) mname = m->type_alias.name;
                    else if (m->kind == AX_ITEM_CONST) mname = m->const_decl.name;
                    if (mname.v == seg->name.v) {
                        found_member = m;
                        break;
                    }
                }
                if (!found_member && target_item->impl.trait_path && target_item->impl.trait_path->kind == AX_TYPE_PATH) {
                    StrId tr_name = target_item->impl.trait_path->path.segments->name;
                    Symbol *tr_sym = lookup_name(env, scope, tr_name);
                    if (tr_sym && tr_sym->node) {
                        const AxAstItem *tr = (const AxAstItem*)tr_sym->node;
                        if (tr->kind == AX_ITEM_TRAIT) {
                            for (const AxAstItem *m = tr->trait.members; m; m = m->next) {
                                StrId mname = {0};
                                if (m->kind == AX_ITEM_FN) mname = m->fn.name;
                                else if (m->kind == AX_ITEM_TYPE_ALIAS) mname = m->type_alias.name;
                                else if (m->kind == AX_ITEM_CONST) mname = m->const_decl.name;
                                if (mname.v == seg->name.v) {
                                    found_member = m;
                                    break;
                                }
                            }
                        }
                    }
                }
            } else if (target_item->kind == AX_ITEM_TRAIT) {
                for (const AxAstItem *m = target_item->trait.members; m; m = m->next) {
                    StrId mname = {0};
                    if (m->kind == AX_ITEM_FN) mname = m->fn.name;
                    else if (m->kind == AX_ITEM_TYPE_ALIAS) mname = m->type_alias.name;
                    else if (m->kind == AX_ITEM_CONST) mname = m->const_decl.name;
                    if (mname.v == seg->name.v) {
                        found_member = m;
                        break;
                    }
                }
            } else if (target_item->kind == AX_ITEM_STRUCT) {
                StrId sname = target_item->struct_decl.name;
                for (const AxAstItem *it = env->ast ? env->ast->items : NULL; it; it = it->next) {
                    if (it->kind == AX_ITEM_IMPL && it->impl.self_type && it->impl.self_type->kind == AX_TYPE_PATH) {
                        if (it->impl.self_type->path.segments->name.v == sname.v) {
                            for (const AxAstItem *m = it->impl.members; m; m = m->next) {
                                StrId mname = {0};
                                if (m->kind == AX_ITEM_FN) mname = m->fn.name;
                                else if (m->kind == AX_ITEM_TYPE_ALIAS) mname = m->type_alias.name;
                                else if (m->kind == AX_ITEM_CONST) mname = m->const_decl.name;
                                if (mname.v == seg->name.v) {
                                    found_member = m;
                                    break;
                                }
                            }
                            if (found_member) break;
                            if (it->impl.trait_path && it->impl.trait_path->kind == AX_TYPE_PATH) {
                                StrId tr_name = it->impl.trait_path->path.segments->name;
                                Symbol *tr_sym = lookup_name(env, scope, tr_name);
                                if (tr_sym && tr_sym->node) {
                                    const AxAstItem *tr = (const AxAstItem*)tr_sym->node;
                                    if (tr->kind == AX_ITEM_TRAIT) {
                                        for (const AxAstItem *m = tr->trait.members; m; m = m->next) {
                                            StrId mname = {0};
                                            if (m->kind == AX_ITEM_FN) mname = m->fn.name;
                                            else if (m->kind == AX_ITEM_TYPE_ALIAS) mname = m->type_alias.name;
                                            else if (m->kind == AX_ITEM_CONST) mname = m->const_decl.name;
                                            if (mname.v == seg->name.v) {
                                                found_member = m;
                                                break;
                                            }
                                        }
                                    }
                                }
                                if (found_member) break;
                            }
                        }
                    }
                }
            }

            if (found_member) {
                AxSymbolId *mid = AxNodeMap_get(&env->rmap->node_map, found_member);
                AxSymbolId sym_id;
                if (mid && mid->v != 0) {
                    sym_id = *mid;
                } else {
                    sym_id = new_symbol(env, found_member);
                    bind_node(env, found_member, sym_id);
                }
                bind_node(env, seg, sym_id);
                head_node = found_member;
                hkind = SYM_ITEM;
            } else {
                emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
                break;
            }
        } else {
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
                resolve_type(env, scope, t->view.elem);
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
                    Symbol *sym = lookup_name(env, scope, p->binding.name);
                    if (sym) bind_node(env, p, sym->id);
                    else emit_diag(env, AX_NAME_UNRESOLVED, p->span);
                }
                break;
            case AX_PAT_PATH:
            case AX_PAT_STRUCT:
                resolve_path_seg(env, scope, p->path.segments);
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
            case AX_EXPR_STRUCT: {
                resolve_path_seg(env, scope, e->struct_lit.segments);
                for (AxAstFieldInit *f = e->struct_lit.fields; f; f = f->next) {
                    if (f->expr) resolve_expr(env, scope, f->expr);
                    else {
                        Symbol *sym = lookup_name(env, scope, f->name);
                        if (sym) bind_node(env, f, sym->id);
                        else emit_diag(env, AX_NAME_UNRESOLVED, f->span);
                    }
                }
                break;
            }
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
                    Symbol *sym = lookup_name(env, scope, e->jump.label);
                    if (sym) bind_node(env, e, sym->id);
                    else emit_diag(env, AX_NAME_UNRESOLVED, e->span);
                }
                if (e->jump.expr) resolve_expr(env, scope, e->jump.expr);
                break;
            case AX_EXPR_CLOSURE: {
                Scope *c_scope = push_scope(env, scope);
                for (AxAstParam *p = e->closure.params; p; p = p->next) {
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
                SymbolKind hkind = SYM_LOCAL;
                Module *curr_mod = NULL;

                if (e->postfix.head->kind == AX_EXPR_PATH && e->postfix.head->path.segments) {
                    AxSymbolId *id = AxNodeMap_get(&env->rmap->node_map, e->postfix.head->path.segments);
                    if (id && id->v != 0 && id->v < env->symbol_nodes_cap) {
                        head_node = env->symbol_nodes[id->v];
                        Symbol *hsym = lookup_name(env, scope, e->postfix.head->path.segments->name);
                        if (hsym) {
                            hkind = hsym->kind;
                            if (hkind == SYM_MODULE) curr_mod = (Module*)hsym->node;
                        }
                    }
                }

                for (AxAstPostfixSeg *s = e->postfix.segments; s; s = s->next) {
                    if (s->kind == AX_POSTFIX_FIELD && head_node) {
                        if (hkind == SYM_MODULE && curr_mod) {
                            Symbol *sub = SymEnv_get(&curr_mod->submodules, s->field.name.v);
                            if (sub) {
                                bind_node(env, s, sub->id);
                                curr_mod = (Module*)sub->node;
                                head_node = sub->node;
                                hkind = SYM_MODULE;
                            } else {
                                Symbol *exp = SymEnv_get(&curr_mod->exports, s->field.name.v);
                                if (exp) {
                                    check_visibility(env, env->current_module, exp, s->span);
                                    bind_node(env, s, exp->id);
                                    AxNodeMap_insert(&env->rmap->module_access_nodes, s, exp->id);
                                    head_node = exp->node;
                                    hkind = exp->kind;
                                    curr_mod = NULL;
                                } else if (SymEnv_contains(&curr_mod->scope->bindings, s->field.name.v)) {
                                    emit_diag(env, AX_NAME_PRIVATE, s->span);
                                    head_node = NULL;
                                } else {
                                    emit_diag(env, AX_NAME_UNRESOLVED, e->span);
                                    head_node = NULL;
                                }
                            }
                        } else if (hkind == SYM_ITEM && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
                            const AxAstItem *en = (const AxAstItem*)head_node;
                            bool found = false;
                            for (AxAstVariantDecl *v = en->enum_decl.variants; v; v = v->next) {
                                if (v->name.v == s->field.name.v) {
                                    AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                                    if (v_id && v_id->v != 0) bind_node(env, s, *v_id);
                                    head_node = v;
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                emit_diag(env, AX_NAME_UNRESOLVED, e->span);
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

static void resolve_single_item_body(Env *env, Scope *scope, const AxAstItem *n) {
    if (!n) return;
    switch (n->kind) {
        case AX_ITEM_FN: {
            Scope *fn_scope = push_scope(env, scope);
            resolve_generic_params(env, fn_scope, n->fn.generic_params);
            resolve_where_clause(env, fn_scope, n->fn.where_clause);
            for (AxAstParam *p = n->fn.params; p; p = p->next) {
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
                SymEnv field_names; SymEnv_init(&field_names);
                for (AxAstFieldDecl *f = n->struct_decl.struct_fields; f; f = f->next) {
                    if (SymEnv_contains(&field_names, f->name.v)) {
                        emit_diag(env, AX_NAME_DUPLICATE, f->span);
                    } else {
                        Symbol s = {0};
                        SymEnv_insert(&field_names, f->name.v, s);
                    }
                    resolve_type(env, s_scope, f->type);
                }
            }
            break;
        }
        case AX_ITEM_ENUM: {
            Scope *e_scope = push_scope(env, scope);
            resolve_generic_params(env, e_scope, n->enum_decl.generic_params);
            resolve_where_clause(env, e_scope, n->enum_decl.where_clause);
            for (AxAstVariantDecl *v = n->enum_decl.variants; v; v = v->next) {
                if (v->is_struct) {
                    for (AxAstFieldDecl *f = v->struct_fields; f; f = f->next) {
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
            for (const AxAstItem *m = n->trait.members; m; m = m->next) resolve_single_item_body(env, t_scope, m);
            break;
        }
        case AX_ITEM_IMPL: {
            Scope *i_scope = push_scope(env, scope);
            declare_name(env, i_scope, ax_intern_cstr(env->interner, "Self"), n, n->span, SYM_LOCAL);
            resolve_generic_params(env, i_scope, n->impl.generic_params);
            resolve_type(env, i_scope, n->impl.trait_path);
            resolve_type(env, i_scope, n->impl.self_type);
            resolve_where_clause(env, i_scope, n->impl.where_clause);
            for (const AxAstItem *m = n->impl.members; m; m = m->next) resolve_single_item_body(env, i_scope, m);
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
            for (const AxAstItem *m = n->extern_block.members; m; m = m->next) resolve_single_item_body(env, scope, m);
            break;
        default: break;
    }
}

/* Recursive use-tree resolution with cycle detection */
typedef struct VisitedImport {
    Module *mod;
    StrId name;
} VisitedImport;

enum UseRes {
    USE_RES_OK = 0,
    USE_RES_ERR = 1,
    USE_RES_CYCLE = 2,
};

static const AxAstUseTree *find_tree_defining_name(const AxAstUseTree *tree, StrId name) {
    for (const AxAstUseTree *t = tree; t; t = t->next) {
        if (t->subtrees) {
            const AxAstUseTree *sub = find_tree_defining_name(t->subtrees, name);
            if (sub) return sub;
        }
        StrId alias = t->alias.v != 0 ? t->alias : (t->path.count > 0 ? t->path.segments[t->path.count - 1] : (StrId){0});
        if (alias.v == name.v) return t;
    }
    return NULL;
}

static int resolve_use_item(Env *env, Module *mod, const AxAstUseTree *tree, StrId prefix[], size_t prefix_len, const AxAstItem *use_item, VisitedImport visited[], size_t vis_count) {
    if (AxNodeMap_contains(&env->resolved_use_trees, tree)) return USE_RES_OK;

    /* Assemble combined segments */
    size_t full_len = prefix_len + tree->path.count;
    StrId *full_segs = ax_arena_alloc(env->arena, full_len * sizeof(StrId), _Alignof(StrId));
    for (size_t i = 0; i < prefix_len; i++) full_segs[i] = prefix[i];
    for (size_t i = 0; i < tree->path.count; i++) full_segs[prefix_len + i] = tree->path.segments[i];

    if (tree->subtrees) {
        for (const AxAstUseTree *sub = tree->subtrees; sub; sub = sub->next) {
            resolve_use_item(env, mod, sub, full_segs, full_len, use_item, visited, vis_count);
        }
        AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
        return USE_RES_OK;
    }

    if (full_len == 0) return USE_RES_OK;

    StrId target_alias = tree->alias.v != 0 ? tree->alias : (full_len > 0 ? full_segs[full_len - 1] : (StrId){0});

    /* Cycle check */
    for (size_t v = 0; v < vis_count; v++) {
        if (visited[v].mod == mod && visited[v].name.v == target_alias.v) {
            emit_diag(env, AX_NAME_IMPORT_CYCLE, tree->span);
            AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
            return USE_RES_CYCLE;
        }
    }

    if (vis_count < 64) {
        visited[vis_count].mod = mod;
        visited[vis_count].name = target_alias;
        vis_count++;
    }

    /* Resolve leftmost segment */
    Symbol *sym = lookup_name(env, mod->scope, full_segs[0]);
    if (!sym) {
        emit_diag(env, AX_NAME_UNRESOLVED_IMPORT, tree->span);
        AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
        return USE_RES_ERR;
    }

    const void *head_node = sym->node;
    SymbolKind hkind = sym->kind;
    Module *curr_mod = (hkind == SYM_MODULE) ? (Module*)head_node : NULL;
    Symbol final_sym = *sym;

    for (size_t i = 1; i < full_len; i++) {
        StrId seg = full_segs[i];
        if (hkind == SYM_MODULE && curr_mod) {
            Symbol *submod = SymEnv_get(&curr_mod->submodules, seg.v);
            if (submod) {
                if (!check_visibility(env, mod, submod, tree->span)) {
                    AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                    return USE_RES_ERR;
                }
                curr_mod = (Module*)submod->node;
                head_node = submod->node;
                hkind = SYM_MODULE;
                final_sym = *submod;
            } else {
                Symbol *exp = SymEnv_get(&curr_mod->exports, seg.v);
                if (!exp && curr_mod->use_items) {
                    for (ModuleUseItem *mui = curr_mod->use_items; mui; mui = mui->next) {
                        const AxAstUseTree *matching = find_tree_defining_name(mui->item->use.tree, seg);
                        if (matching) {
                            bool in_cycle = false;
                            for (size_t v = 0; v < vis_count; v++) {
                                if (visited[v].mod == curr_mod && visited[v].name.v == seg.v) {
                                    in_cycle = true;
                                    break;
                                }
                            }
                            if (in_cycle) {
                                emit_diag(env, AX_NAME_IMPORT_CYCLE, tree->span);
                                AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                                return USE_RES_CYCLE;
                            }
                            int sub_res = resolve_use_item(env, curr_mod, matching, NULL, 0, mui->item, visited, vis_count);
                            if (sub_res == USE_RES_CYCLE) {
                                emit_diag(env, AX_NAME_IMPORT_CYCLE, tree->span);
                                AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                                return USE_RES_CYCLE;
                            }
                            exp = SymEnv_get(&curr_mod->exports, seg.v);
                            if (!exp) {
                                Symbol *bnd = SymEnv_get(&curr_mod->scope->bindings, seg.v);
                                if (bnd) exp = bnd;
                            }
                            break;
                        }
                    }
                }
                if (exp) {
                    if (!check_visibility(env, mod, exp, tree->span)) {
                        AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                        return USE_RES_ERR;
                    }
                    head_node = exp->node;
                    hkind = exp->kind;
                    final_sym = *exp;
                    curr_mod = NULL;
                } else if (SymEnv_contains(&curr_mod->scope->bindings, seg.v)) {
                    /* Exists but private */
                    emit_diag(env, AX_NAME_PRIVATE, tree->span);
                    AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                    return USE_RES_ERR;
                } else {
                    emit_diag(env, AX_NAME_UNRESOLVED_IMPORT, tree->span);
                    AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                    return USE_RES_ERR;
                }
            }
        } else if (hkind == SYM_ITEM && head_node && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {
            const AxAstItem *en = (const AxAstItem*)head_node;
            bool found = false;
            for (AxAstVariantDecl *v = en->enum_decl.variants; v; v = v->next) {
                if (v->name.v == seg.v) {
                    AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                    if (v_id) {
                        final_sym.id = *v_id;
                        final_sym.node = v;
                        final_sym.kind = SYM_ITEM;
                        final_sym.vis = AX_VIS_PUB;
                        final_sym.def_module = curr_mod;
                    }
                    head_node = v;
                    found = true;
                    break;
                }
            }
            if (!found) {
                emit_diag(env, AX_NAME_UNRESOLVED_IMPORT, tree->span);
                AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
                return USE_RES_ERR;
            }
        } else {
            emit_diag(env, AX_NAME_UNRESOLVED_IMPORT, tree->span);
            AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
            return USE_RES_ERR;
        }
    }

    /* Check visibility of single segment */
    if (full_len == 1) {
        if (!check_visibility(env, mod, &final_sym, tree->span)) {
            AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
            return USE_RES_ERR;
        }
    }

    bind_node(env, tree, final_sym.id);
    bind_node(env, &tree->path, final_sym.id);

    StrId alias = tree->alias;
    if (alias.v == 0) {
        alias = full_segs[full_len - 1];
    }

    if (SymEnv_contains(&mod->scope->bindings, alias.v)) {
        emit_diag(env, AX_NAME_DUPLICATE, tree->span);
    } else {
        SymEnv_insert(&mod->scope->bindings, alias.v, final_sym);

        /* If pub use or pub(package) use, export it as re-export */
        if (use_item && use_item->vis.kind != AX_VIS_PRIVATE) {
            Symbol reexport = final_sym;
            reexport.vis = use_item->vis.kind;
            reexport.def_module = mod;
            SymEnv_insert(&mod->exports, alias.v, reexport);
        }
    }

    AxNodeMap_insert(&env->resolved_use_trees, tree, (AxSymbolId){1});
    return USE_RES_OK;
}

AxResolveMap ax_resolve(AxAst *ast, AxArena *arena, AxDiagSink *sink, StrInterner *interner) {
    AxResolveMap map;
    ax_resolve_map_init(&map);

    NamingCtx *naming = calloc(1, sizeof(NamingCtx));
    map.module_naming_ctx = naming;

    Env env = {0};
    env.rmap = &map;
    env.arena = arena;
    env.sink = sink;
    env.interner = interner;
    env.naming = naming;
    env.ast = ast;
    AxNodeMap_init(&env.resolved_use_trees);

    /* 1. Setup prelude scope */
    Scope *prelude = push_scope(&env, NULL);
    prelude->is_module_scope = true;
    env.prelude_scope = prelude;

    const char *prelude_types[] = {
        "bool", "i32", "u32", "usize", "isize", 
        "Copy", "Drop", "Send", "Share", "f32", "f64", "char", "str",
        "u8", "i8", "u16", "i16", "u64", "i64", "len", "Str", "print", "print_int", "drop"
    };
    for (size_t i = 0; i < sizeof(prelude_types)/sizeof(prelude_types[0]); i++) {
        StrId id = ax_intern_cstr(interner, prelude_types[i]);
        declare_name(&env, prelude, id, NULL, (Span){0}, SYM_ITEM);
    }
    const char *fn_traits[] = { "Fn", "FnMut", "FnOnce", "Callable" };
    for (size_t i = 0; i < sizeof(fn_traits)/sizeof(fn_traits[0]); i++) {
        StrId id = ax_intern_cstr(interner, fn_traits[i]);
        Symbol s = { (AxSymbolId){ 10100 + (uint32_t)i }, NULL, SYM_ITEM, AX_VIS_PUB, NULL };
        SymEnv_insert(&prelude->bindings, id.v, s);
    }

    /* 2. Setup root module */
    env.root_module = create_module(&env, "", (StrId){0}, NULL);
    env.current_module = env.root_module;

    /* 3. Pass 1: Collect modules and declarations */
    const AxAstItem *it = ast->items;
    while (it) {
        if (it->kind == AX_ITEM_MODULE) {
            env.current_module = get_or_create_module(&env, &it->module.path);
            AxSymbolId sym = new_symbol(&env, env.current_module);
            bind_node(&env, it, sym);
        } else if (it->kind == AX_ITEM_USE) {
            ModuleUseItem *mui = ax_arena_alloc(env.arena, sizeof(ModuleUseItem), 8);
            mui->item = it;
            mui->next = env.current_module->use_items;
            env.current_module->use_items = mui;
        } else {
            StrId name = {0};
            SymbolKind kind = SYM_ITEM;

            switch (it->kind) {
                case AX_ITEM_FN: name = it->fn.name; break;
                case AX_ITEM_STRUCT: name = it->struct_decl.name; break;
                case AX_ITEM_ENUM: name = it->enum_decl.name; break;
                case AX_ITEM_TRAIT: name = it->trait.name; break;
                case AX_ITEM_TYPE_ALIAS: name = it->type_alias.name; break;
                case AX_ITEM_CONST: name = it->const_decl.name; break;
                case AX_ITEM_STATIC: name = it->static_decl.name; break;
                default: break;
            }

            if (name.v != 0) {
                Symbol *s = declare_name_vis(&env, env.current_module->scope, name, it, it->span, kind, it->vis.kind);
                if (s) {
                    SymEnv_insert(&env.current_module->exports, name.v, *s);

                    /* Record symbol module path and canonical name */
                    StrView n_sv = ax_interner_get(interner, name);
                    char canon[512];
                    if (env.current_module->full_path[0]) {
                        snprintf(canon, sizeof(canon), "%s.%.*s", env.current_module->full_path, (int)n_sv.len, n_sv.ptr);
                    } else {
                        snprintf(canon, sizeof(canon), "%.*s", (int)n_sv.len, n_sv.ptr);
                    }
                    record_symbol_naming(&env, s->id, env.current_module->full_path, canon);
                }

                if (it->kind == AX_ITEM_ENUM) {
                    for (AxAstVariantDecl *v = it->enum_decl.variants; v; v = v->next) {
                        AxSymbolId vsym = new_symbol(&env, v);
                        bind_node(&env, v, vsym);
                        StrView v_sv = ax_interner_get(interner, v->name);
                        char vcanon[512];
                        if (env.current_module->full_path[0]) {
                            snprintf(vcanon, sizeof(vcanon), "%s.%.*s.%.*s", env.current_module->full_path, (int)ax_interner_get(interner, name).len, ax_interner_get(interner, name).ptr, (int)v_sv.len, v_sv.ptr);
                        } else {
                            snprintf(vcanon, sizeof(vcanon), "%.*s.%.*s", (int)ax_interner_get(interner, name).len, ax_interner_get(interner, name).ptr, (int)v_sv.len, v_sv.ptr);
                        }
                        record_symbol_naming(&env, vsym, env.current_module->full_path, vcanon);
                    }
                }
            }
        }
        it = it->next;
    }

    /* 5. Pass 2: Resolve imports */
    env.current_module = env.root_module;
    it = ast->items;
    while (it) {
        if (it->kind == AX_ITEM_MODULE) {
            env.current_module = get_or_create_module(&env, &it->module.path);
        } else if (it->kind == AX_ITEM_USE) {
            VisitedImport visited[64];
            size_t vis_count = 0;
            for (const AxAstUseTree *tree = it->use.tree; tree; tree = tree->next) {
                if (AxNodeMap_contains(&env.resolved_use_trees, tree)) continue;
                resolve_use_item(&env, env.current_module, tree, NULL, 0, it, visited, vis_count);
            }
        }
        it = it->next;
    }

    /* 4. Prelude module implicit export: if std.core.prelude exists, export its pub items to prelude scope */
    for (Module *m = env.modules_list; m; m = m->next) {
        if (strcmp(m->full_path, "std.core.prelude") == 0) {
            uint32_t cur = 0; void *raw_e;
            while (ax_rawmap_next(&m->exports.raw, &cur, &raw_e)) {
                SymEnvEntry *e = (SymEnvEntry*)raw_e;
                if (e->value.vis == AX_VIS_PUB) {
                    SymEnv_insert(&prelude->bindings, e->key, e->value);
                }
            }
            break;
        }
    }

    /* 6. Pass 3: Resolve bodies */
    env.current_module = env.root_module;
    it = ast->items;
    while (it) {
        if (it->kind == AX_ITEM_MODULE) {
            env.current_module = get_or_create_module(&env, &it->module.path);
        } else {
            resolve_single_item_body(&env, env.current_module->scope, it);
        }
        it = it->next;
    }

    AxNodeMap_free(&env.resolved_use_trees);
    return map;
}
