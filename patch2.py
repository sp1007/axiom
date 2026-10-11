with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Add push_drop inside add_local
old_add_local = """    b->locals[id.v].mut = mut;
    b->locals[id.v].location = b->current_span;
    return id;"""
new_add_local = """    b->locals[id.v].mut = mut;
    b->locals[id.v].location = b->current_span;
    if (kind != AX_MIR_LOCAL_RETURN) {
        AxMirPlace place = { id, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        push_drop(b, place, ty);
    }
    return id;"""
content = content.replace(old_add_local, new_add_local)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
