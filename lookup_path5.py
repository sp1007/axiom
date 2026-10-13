import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('static TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path, AxGenericArgs *out_args) {')
if idx != -1:
    print(text[idx+3900:idx+5500])

