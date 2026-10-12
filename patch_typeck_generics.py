import re

with open("bootstrap/axiom0/src/types/typeck.c", "r") as f:
    text = f.read()

# 1. Add new_ty_var
new_ty_var_code = """
static TypeId new_ty_var(TypeckCtx *cx) {
    if (cx->int_vars_len == cx->int_vars_cap) {
        cx->int_vars = ax_grow_array(cx->int_vars, &cx->int_vars_cap, sizeof(IntTypeVar), cx->int_vars_len + 1);
    }
    uint32_t var_id = (uint32_t)cx->int_vars_len;
    cx->int_vars[cx->int_vars_len].resolved_to = TypeId_none();
    cx->int_vars_len++;

    AxType t;
    memset(&t, 0, sizeof(t));
    t.kind = AX_TY_VAR;
    t.int_var.var_id = var_id;
    return ax_intern_type(&cx->thir->interner, &t);
}
"""
text = text.replace("static TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path);", new_ty_var_code + "\nstatic TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path);")

# 2. Modify resolve_ty
text = text.replace("if (t->kind == AX_TY_INT_VAR) {", "if (t->kind == AX_TY_INT_VAR || t->kind == AX_TY_VAR) {")

# 3. Modify unify_ty
unify_ty_code = """
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

    if (ta->kind == AX_TY_INT_VAR) {"""
text = text.replace("    // AXS-SEM-020: an integer type variable can only become an integer type.\n    if (ta->kind == AX_TY_INT_VAR) {", unify_ty_code)

# 4. subst_ty implementation
subst_ty_code = """
static TypeId subst_ty(TypeckCtx *cx, TypeId ty, AxGenericArgs *args) {
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
        TypeId elem = subst_ty(cx, t->array.elem, args);
        if (elem.v == t->array.elem.v) return ty;
        AxType new_t = *t;
        new_t.array.elem = elem;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_SLICE) {
        TypeId elem = subst_ty(cx, t->slice.elem, args);
        if (elem.v == t->slice.elem.v) return ty;
        AxType new_t = *t;
        new_t.slice.elem = elem;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) {
        TypeId pointee = subst_ty(cx, t->view.pointee, args);
        if (pointee.v == t->view.pointee.v) return ty;
        AxType new_t = *t;
        new_t.view.pointee = pointee;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_PTR) {
        TypeId pointee = subst_ty(cx, t->ptr.pointee, args);
        if (pointee.v == t->ptr.pointee.v) return ty;
        AxType new_t = *t;
        new_t.ptr.pointee = pointee;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_TUPLE) {
        bool changed = false;
        TypeId *fields = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->tuple.field_count, _Alignof(TypeId));
        for (size_t i = 0; i < t->tuple.field_count; i++) {
            fields[i] = subst_ty(cx, t->tuple.fields[i], args);
            if (fields[i].v != t->tuple.fields[i].v) changed = true;
        }
        if (!changed) return ty;
        AxType new_t = *t;
        new_t.tuple.fields = fields;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_FN) {
        bool changed = false;
        TypeId ret = subst_ty(cx, t->fn.ret_type, args);
        if (ret.v != t->fn.ret_type.v) changed = true;
        TypeId *param_types = NULL;
        if (t->fn.param_count > 0) {
            param_types = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->fn.param_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->fn.param_count; i++) {
                param_types[i] = subst_ty(cx, t->fn.param_types[i], args);
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
        if (t->strct.arg_count > 0) {
            sargs = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->strct.arg_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->strct.arg_count; i++) {
                sargs[i] = subst_ty(cx, t->strct.args[i], args);
                if (sargs[i].v != t->strct.args[i].v) changed = true;
            }
        }
        if (!changed) return ty;
        AxType new_t = *t;
        new_t.strct.args = sargs;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    if (t->kind == AX_TY_ENUM) {
        bool changed = false;
        TypeId *eargs = NULL;
        if (t->enm.arg_count > 0) {
            eargs = ax_arena_alloc(&cx->thir->interner.arena, sizeof(TypeId) * t->enm.arg_count, _Alignof(TypeId));
            for (size_t i = 0; i < t->enm.arg_count; i++) {
                eargs[i] = subst_ty(cx, t->enm.args[i], args);
                if (eargs[i].v != t->enm.args[i].v) changed = true;
            }
        }
        if (!changed) return ty;
        AxType new_t = *t;
        new_t.enm.args = eargs;
        return ax_intern_type(&cx->thir->interner, &new_t);
    }
    return ty;
}
"""
text = text.replace("static TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected);", subst_ty_code + "\nstatic TypeId check_expr(TypeckCtx *cx, const AxHirExpr *expr, TypeId expected);")

# 5. Populate AX_TY_PARAM for STRUCT/ENUM
struct_param_code = """
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
                    st.strct.args[i] = ax_intern_type(&thir.interner, &pt);
                    i++;
                }
            } else {
                st.strct.args = NULL;
            }

            size_t count = 0;
"""
text = text.replace("""            size_t count = 0;
            for (const AxHirFieldDecl *f = it->struct_decl.struct_fields; f; f = f->next) count++;""", struct_param_code + """            for (const AxHirFieldDecl *f = it->struct_decl.struct_fields; f; f = f->next) count++;""")

enum_param_code = """
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
                    en.enm.args[i] = ax_intern_type(&thir.interner, &pt);
                    i++;
                }
            } else {
                en.enm.args = NULL;
            }

            size_t vcount = 0;
"""
text = text.replace("""            size_t vcount = 0;
            for (const AxHirVariantDecl *v = it->enum_decl.variants; v; v = v->next) vcount++;""", enum_param_code + """            for (const AxHirVariantDecl *v = it->enum_decl.variants; v; v = v->next) vcount++;""")

# 6. Instantiate path lookup
instantiate_code = """
static TypeId instantiate_path(TypeckCtx *cx, TypeId ty, const AxHirItem *it, const AxHirPath *path) {
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
            type_error(cx, path->span, AX_TYPE_MISMATCH); // TODO: specific error for wrong generic args count
            return cx->thir->interner.t_error;
        }
        size_t i = 0;
        for (AxHirGenericArg *a = path->generic_args->args; a; a = a->next) {
            gargs.args[i++] = hir_type_to_typeid(cx, a->type);
        }
    } else {
        for (size_t i = 0; i < param_count; i++) {
            gargs.args[i] = new_ty_var(cx);
        }
    }
    
    // We can't store expr_substs here because we don't have the expression! 
    // Wait, the task says: "When type-checking paths, handle explicit generic arguments (`path->generic_args`), or create new type variables for inference if they are absent."
    // We will just do substitution here, and we can also attach substs if we know the expr?
    // Let's modify lookup_path_type to take generic args out, wait, lookup_path_type can take `path` and do the instantiation!
    // But how do we return `AxGenericArgs` out to store in `expr_substs`?
    // We can just add it to `expr_substs` inside `check_expr_kind` for `AX_HIR_EXPR_PATH`!
    return subst_ty(cx, ty, &gargs);
}
"""

text = text.replace("static TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path) {", instantiate_code + "\nstatic TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path, AxGenericArgs *out_args) {")

text = text.replace("TypeId t = lookup_path_type(cx, &ht->path.path);", "TypeId t = lookup_path_type(cx, &ht->path.path, NULL);")
text = text.replace("left = lookup_path_type(cx, &s->assign.left->path.path);", "left = lookup_path_type(cx, &s->assign.left->path.path, NULL);")

# Update lookup_path_type calls in check_expr_kind
text = text.replace("TypeId t = lookup_path_type(cx, &expr->path.path);", """
            AxGenericArgs gargs = {0};
            TypeId t = lookup_path_type(cx, &expr->path.path, &gargs);
            if (gargs.count > 0) {
                AxExprSubstMap_insert(&cx->thir->expr_substs, expr, gargs);
            }
""")

# We need to change `return *it_t;` inside lookup_path_type to `return instantiate_path(cx, *it_t, it, path, out_args)`
# Wait, instantiate_path should write to `out_args`! Let's redefine instantiate_path
instantiate_code = """
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
            type_error(cx, path->span, AX_TYPE_MISMATCH);
            return cx->thir->interner.t_error;
        }
        size_t i = 0;
        for (AxHirGenericArg *a = path->generic_args->args; a; a = a->next) {
            gargs.args[i++] = hir_type_to_typeid(cx, a->type);
        }
    } else {
        for (size_t i = 0; i < param_count; i++) {
            gargs.args[i] = new_ty_var(cx);
        }
    }
    
    if (out_args) *out_args = gargs;
    return subst_ty(cx, ty, &gargs);
}
"""
text = text.replace("static TypeId instantiate_path(TypeckCtx *cx, TypeId ty, const AxHirItem *it, const AxHirPath *path) {", instantiate_code + "\n//")

text = text.replace("if (it_t) return *it_t;", "if (it_t) return instantiate_path(cx, *it_t, it, path, out_args);")

with open("bootstrap/axiom0/src/types/typeck.c", "w") as f:
    f.write(text)
