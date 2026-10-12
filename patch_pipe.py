import sys

file = 'bootstrap/axiom0/src/driver/pipeline.c'
with open(file, 'r') as f:
    content = f.read()

s1 = """static void stage_typeck(AxDriverState *st) {
    if (st->sink.errors > 0) return;"""

r1 = """static void stage_typeck(AxDriverState *st) {
    if (st->sink.errors > 0) return;
    
    // BOOTSTRAP-SHORTCUT T131: Link impl members to the main AST item list to ensure they are typechecked.
    // This avoids memory leaks and bypasses the need for complex module resolution of methods for now.
    AxHirItem *tail = st->hir.items;
    if (tail) {
        while (tail->next) tail = tail->next;
        for (AxHirItem *it = st->hir.items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_IMPL && it->impl.members) {
                tail->next = it->impl.members;
                while (tail->next) tail = tail->next;
            }
        }
    }
"""

content = content.replace(s1, r1)

s2 = """        ax_mir_drop_elaborate(body, &st->thir, &st->sink, &st->interner);"""
r2 = """        ax_mir_drop_elaborate(body, &st->thir, &st->hir, &st->sink, &st->interner);"""
content = content.replace(s2, r2)

with open(file, 'w') as f:
    f.write(content)
