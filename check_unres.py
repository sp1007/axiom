import sys
with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('''        {
    fprintf(stderr, "DEBUG unresolved path segment: %s\\n", ax_interner_get(env->interner, seg->name).ptr);
    emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
}''',
'''        {
    fprintf(stderr, "DEBUG unresolved path segment: %s\\n", ax_interner_get(env->interner, seg->name).ptr);
    emit_diag(env, AX_NAME_UNRESOLVED, seg->span);
}''')
# Wait, I ALREADY added DEBUG unresolved path segment: %s earlier?!
