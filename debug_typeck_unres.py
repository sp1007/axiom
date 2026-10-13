import sys

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'return type_error(cx, path->span, AX_NAME_UNRESOLVED);',
    'fprintf(stderr, "Unresolved path: name=%s symbol=%llu strid=%llu\\n", name.ptr ? name.ptr : "?", (unsigned long long)path->symbol.v, (unsigned long long)path->name.v); return type_error(cx, path->span, AX_NAME_UNRESOLVED);'
)

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
