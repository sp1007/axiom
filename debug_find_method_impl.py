import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL) {''',
'''    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL) {
            if (ax_sv_eq_cstr(method_name, "eq")) {
                fprintf(stderr, "DEBUG IMPL CHECK: self_ty=%u, base_ty=%u\\n", hir_type_to_typeid(cx, it->impl.self_type).v, base_ty.v);
            }''')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
