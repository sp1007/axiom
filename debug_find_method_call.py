import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('const AxHirItem *method_item = find_method(cx, opnd, mname, &trait_res);',
'''const AxHirItem *method_item = find_method(cx, opnd, mname, &trait_res);
    fprintf(stderr, "DEBUG find_method for opnd kind=%d (var=%d), returned %p\\n", ax_type_get(&cx->thir->interner, opnd)->kind, opnd.v, method_item);
''')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
