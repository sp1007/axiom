import sys

file = 'bootstrap/axiom0/src/driver/build_native/build.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''ax_lir_lower_abi(lir_body, &st->thir.interner, &ax_abi_win64, fn_ty);'''
r1 = '''ax_lir_lower_abi(lir_body, &st->thir.interner, &ax_abi_win64, fn_ty);
                      fprintf(stderr, "LIR for %s:\\n", ax_interner_get(&st->interner, item->fn.name).ptr);
                      ax_lir_print(stderr, lir_body);'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
