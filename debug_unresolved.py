import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'emit_diag(env, AX_NAME_UNRESOLVED, p->span);',
    'fprintf(stderr, "DEBUG UNRESOLVED 1\\n"); emit_diag(env, AX_NAME_UNRESOLVED, p->span);'
)
text = text.replace(
    'emit_diag(env, AX_NAME_UNRESOLVED, seg->span);',
    'fprintf(stderr, "DEBUG UNRESOLVED 2\\n"); emit_diag(env, AX_NAME_UNRESOLVED, seg->span);'
)
text = text.replace(
    'emit_diag(env, AX_NAME_UNRESOLVED, f->span);',
    'fprintf(stderr, "DEBUG UNRESOLVED 3\\n"); emit_diag(env, AX_NAME_UNRESOLVED, f->span);'
)
text = text.replace(
    'emit_diag(env, AX_NAME_UNRESOLVED, e->span);',
    'fprintf(stderr, "DEBUG UNRESOLVED 4\\n"); emit_diag(env, AX_NAME_UNRESOLVED, e->span);'
)
text = text.replace(
    'd.code = AX_NAME_UNRESOLVED;',
    'fprintf(stderr, "DEBUG UNRESOLVED TYPECK\\n"); d.code = AX_NAME_UNRESOLVED;'
)

with open('bootstrap/axiom0/src/resolve/resolve.c', 'wb') as f:
    f.write(text.encode('utf-8'))
