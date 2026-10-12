import re

with open('bootstrap/axiom0/src/own/own.c', 'r', encoding='utf-8') as f:
    code = f.read()

def patch_func(name, inner):
    # match static void name(Visitor *v, const AxMirPlace *place, AxLocation loc) { [any whitespace] uint32_t node = resolve_place(v->ctx, place);
    pattern = r'static void ' + name + r'\(Visitor \*v, const AxMirPlace \*place, AxLocation loc\) \{[\s\n]*uint32_t node = resolve_place\(v->ctx, place\);'
    
    new = f'''static void {name}(Visitor *v, const AxMirPlace *place, AxLocation loc) {{
    AxMirPlace base = *place;
    for (size_t i = 0; i < place->proj_count; i++) {{
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {{
            base.proj_count = i;
            {inner}
        }}
    }}
    uint32_t node = resolve_place(v->ctx, place);'''
    return re.sub(pattern, new, code)

code = patch_func('check_use', 'place = &base; break;')
code = patch_func('do_move', 'check_use(v, &base, loc); return;')
code = patch_func('do_assign', 'check_use(v, &base, loc); return;')

with open('bootstrap/axiom0/src/own/own.c', 'w', encoding='utf-8') as f:
    f.write(code)
