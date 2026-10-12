import sys

file = 'bootstrap/axiom0/src/mir/drop/drop.c'
with open(file, 'r') as f:
    content = f.read()

content = content.replace('if (m->kind == AX_HIR_ITEM_FN && ax_sv_eq_cstr(ax_interner_get((StrInterner*)interner, m->fn.name), "drop")) {', 'if (m->kind == AX_HIR_ITEM_FN) {')

with open(file, 'w') as f:
    f.write(content)
