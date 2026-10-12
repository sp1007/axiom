import re

with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    code = f.read()

old_code = r'''    \} else if \(expr->kind == AX_HIR_EXPR_FIELD\) \{
        AxMirPlace base = build_place\(b, expr->field\.base\);
        TypeId base_ty = \*AxExprTypeMap_get\(&b->thir->expr_types, expr->field\.base\);
        const AxType \*t = ax_type_get\(&b->thir->interner, base_ty\);
        uint32_t idx = 0;
        if \(t->kind == AX_TY_STRUCT\) \{
            for \(const AxHirFieldDecl \*fd = t->strct\.def->struct_decl\.struct_fields; fd; fd = fd->next, idx\+\+\) \{
                if \(fd->name\.v == expr->field\.name\.v\) break;
            \}
        \}
        
        AxMirProjection \*projs = ax_arena_alloc\(b->arena, sizeof\(AxMirProjection\) \* \(base\.proj_count \+ 1\), _Alignof\(AxMirProjection\)\);
        for \(size_t i = 0; i < base\.proj_count; i\+\+\) projs\[i\] = base\.projs\[i\];
        projs\[base\.proj_count\]\.kind = AX_MIR_PROJ_FIELD;
        projs\[base\.proj_count\]\.field_idx = idx;
        
        base\.projs = projs;
        base\.proj_count\+\+;
        return base;'''

new_code = '''    } else if (expr->kind == AX_HIR_EXPR_FIELD) {
        AxMirPlace base = build_place(b, expr->field.base);
        TypeId base_ty = *AxExprTypeMap_get(&b->thir->expr_types, expr->field.base);
        const AxType *t = ax_type_get(&b->thir->interner, base_ty);
        
        size_t deref_count = 0;
        while (t && (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW || t->kind == AX_TY_PTR)) {
            deref_count++;
            base_ty = (t->kind == AX_TY_PTR) ? t->ptr.pointee : t->view.pointee;
            t = ax_type_get(&b->thir->interner, base_ty);
        }
        
        uint32_t idx = 0;
        if (t && t->kind == AX_TY_STRUCT) {
            for (const AxHirFieldDecl *fd = t->strct.def->struct_decl.struct_fields; fd; fd = fd->next, idx++) {
                if (fd->name.v == expr->field.name.v) break;
            }
        }
        
        AxMirProjection *projs = ax_arena_alloc(b->arena, sizeof(AxMirProjection) * (base.proj_count + deref_count + 1), _Alignof(AxMirProjection));
        for (size_t i = 0; i < base.proj_count; i++) projs[i] = base.projs[i];
        
        for (size_t i = 0; i < deref_count; i++) {
            projs[base.proj_count + i].kind = AX_MIR_PROJ_DEREF;
        }
        
        projs[base.proj_count + deref_count].kind = AX_MIR_PROJ_FIELD;
        projs[base.proj_count + deref_count].field_idx = idx;
        
        base.projs = projs;
        base.proj_count += (deref_count + 1);
        return base;'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(code)
