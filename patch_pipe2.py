import sys

file = 'bootstrap/axiom0/src/driver/pipeline.c'
with open(file, 'r') as f:
    content = f.read()

s1 = 'if (it->kind == AX_HIR_ITEM_IMPL && it->impl.members) {'
r1 = '''if (it->kind == AX_HIR_ITEM_IMPL && it->impl.members) {
                static int drop_count = 0;
                for (AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        char buf[32];
                        sprintf(buf, "drop_impl_%d", drop_count++);
                        m->fn.name = ax_interner_intern(&st->interner, ax_sv_from_cstr(buf));
                    }
                }'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
