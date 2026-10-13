import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'if (it->kind == AX_HIR_ITEM_STRUCT) {',
    'if (it->kind == AX_HIR_ITEM_STRUCT) { fprintf(stderr, "Struct %s symbol %llu\\n", ax_interner_get(cx.str_in, it->struct_decl.name).ptr, (unsigned long long)it->struct_decl.symbol.v);'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
