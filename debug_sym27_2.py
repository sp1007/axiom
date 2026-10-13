import sys

with open('build-snap-T056/bootstrap/axiom0/src/resolve/resolve.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'static AxSymbolId new_symbol(Env *env, const void *node) {\n    AxSymbolId id = { ++env->sym_counter };',
    'static AxSymbolId new_symbol(Env *env, const void *node) {\n    AxSymbolId id = { ++env->sym_counter };\n    if (id.v == 27) fprintf(stderr, "Symbol 27 allocated! node kind %d\\n", node ? ((int)((const AxAstItem*)node)->kind) : -1);'
)

with open('build-snap-T056/bootstrap/axiom0/src/resolve/resolve.c', 'wb') as f:
    f.write(text.encode('utf-8'))
