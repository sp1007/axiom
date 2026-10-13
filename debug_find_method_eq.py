import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''            if (self_ty.v == base_ty.v) {
                match = true;
            } else {
                const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
                const AxType *s = ax_type_get(&cx->thir->interner, self_ty);
                if (b->kind == AX_TY_VIEW && s->kind == AX_TY_VIEW) {
                     match = (b->view.pointee.v == s->view.pointee.v);
                } else if (b->kind == AX_TY_VIEW) {
                     if (b->view.pointee.v == self_ty.v) match = true;
                }
            }''',
'''            if (self_ty.v == base_ty.v) {
                match = true;
            } else {
                const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
                const AxType *s = ax_type_get(&cx->thir->interner, self_ty);
                if (b->kind == AX_TY_VIEW && s->kind == AX_TY_VIEW) {
                     match = (b->view.pointee.v == s->view.pointee.v);
                } else if (b->kind == AX_TY_VIEW) {
                     if (b->view.pointee.v == self_ty.v) match = true;
                     if (ax_sv_eq_cstr(method_name, "eq")) {
                         fprintf(stderr, "DEBUG find_method for eq: b->view.pointee.v=%u, self_ty.v=%u, match=%d\\n", b->view.pointee.v, self_ty.v, match);
                     }
                }
            }''')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
