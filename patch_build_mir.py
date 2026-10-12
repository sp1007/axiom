import sys

file = 'bootstrap/axiom0/src/driver/build_native/build.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''fprintf(stderr, "LIR for %s:\\n", ax_interner_get(&st->interner, item->fn.name).ptr);'''
r1 = '''fprintf(stderr, "MIR for %s:\\n", ax_interner_get(&st->interner, item->fn.name).ptr);
        ax_mir_print(stderr, mir_body);
        fprintf(stderr, "LIR for %s:\\n", ax_interner_get(&st->interner, item->fn.name).ptr);'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
