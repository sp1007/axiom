import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the field access logic
old_code = r'''        case AX_HIR_EXPR_FIELD: \{
            TypeId obj_ty = check_expr\(cx, expr->field\.base, TypeId_none\(\)\);
            if \(\!is_error\(cx, obj_ty\)\) \{
                const AxType \*t = ax_type_get\(&cx->thir->interner, obj_ty\);
                if \(t->kind == AX_TY_STRUCT\) \{'''

new_code = '''        case AX_HIR_EXPR_FIELD: {
            TypeId obj_ty = check_expr(cx, expr->field.base, TypeId_none());
            if (!is_error(cx, obj_ty)) {
                TypeId base_ty = obj_ty;
                const AxType *t = ax_type_get(&cx->thir->interner, base_ty);
                while (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW || t->kind == AX_TY_PTR) {
                    base_ty = (t->kind == AX_TY_PTR) ? t->ptr.pointee : t->view.pointee;
                    t = ax_type_get(&cx->thir->interner, base_ty);
                }
                if (t->kind == AX_TY_STRUCT) {'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
