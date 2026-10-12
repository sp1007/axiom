import sys

file = 'bootstrap/axiom0/src/driver/build_native/build.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''for (const AxHirItem *item = st->hir.items; item != NULL; item = item->next) {
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir_body = ax_mir_build(item, &st->thir, &st->hir_arena);
            if (mir_body) {
                const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, item);'''
r1 = '''extern AxMirBody* ax_pipeline_get_mir(const AxHirItem *it);

    for (const AxHirItem *item = st->hir.items; item != NULL; item = item->next) {
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir_body = ax_pipeline_get_mir(item);
            if (!mir_body) {
                mir_body = ax_mir_build(item, &st->thir, &st->hir_arena);
            }
            if (mir_body) {
                const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, item);'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
