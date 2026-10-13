import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''                    AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                    if (v_id && v_id->v != 0) {
                        fprintf(stderr, "DEBUG resolve enum var: found %u\\n", v_id->v);
                        bind_node(env, seg, *v_id);
                    } else {
                        fprintf(stderr, "DEBUG resolve enum var ERROR v_id is null or 0\\n");
                    }''',
'''                    AxSymbolId *v_id = AxNodeMap_get(&env->rmap->node_map, v);
                    fprintf(stderr, "DEBUG resolve enum seg %.*s\\n", (int)seg->name.len, seg->name.ptr);
                    if (v_id && v_id->v != 0) {
                        fprintf(stderr, "DEBUG resolve enum var: found %u\\n", v_id->v);
                        bind_node(env, seg, *v_id);
                    } else {
                        fprintf(stderr, "DEBUG resolve enum var ERROR v_id is null or 0\\n");
                    }''')

with open('bootstrap/axiom0/src/resolve/resolve.c', 'w', encoding='utf-8') as f:
    f.write(text)
