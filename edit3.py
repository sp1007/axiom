import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'rb') as f:
    text = f.read().decode('utf-8')

new_text = text.replace(
    'bind_node(env, seg, sym->id);',
    'bind_node(env, seg, sym->id); printf("bind_node: %p to %llu\\n", (void*)seg, (unsigned long long)sym->id.v);'
)
new_text = new_text.replace(
    'if (v_id && v_id->v != 0) bind_node(env, seg, *v_id);',
    'if (v_id && v_id->v != 0) { bind_node(env, seg, *v_id); printf("bind_node enum variant: %p to %llu\\n", (void*)seg, (unsigned long long)v_id->v); }'
)

with open('bootstrap/axiom0/src/resolve/resolve.c', 'wb') as f:
    f.write(new_text.encode('utf-8'))
