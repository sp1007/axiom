import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('TypeId lookup_path_type(TypeckCtx *cx, const AxHirPath *path, AxGenericArgs *out_args) {')
print(text[idx1:idx1+1500])
