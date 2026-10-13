import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''            if (ax_sv_eq_cstr(method_name, "eq")) {
                fprintf(stderr, "DEBUG IMPL CHECK: self_ty=%u, base_ty=%u\\n", hir_type_to_typeid(cx, it->impl.self_type).v, base_ty.v);
            }''',
'''            if (ax_sv_eq_cstr(method_name, "eq")) {
                const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
                fprintf(stderr, "DEBUG IMPL CHECK: self_ty=%u, base_ty=%u, b->kind=%d", hir_type_to_typeid(cx, it->impl.self_type).v, base_ty.v, b->kind);
                if (b->kind == AX_TY_VIEW) fprintf(stderr, " b->pointee=%u", b->view.pointee.v);
                fprintf(stderr, "\\n");
            }''')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
