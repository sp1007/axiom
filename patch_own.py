import re

with open('bootstrap/axiom0/src/own/own.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Modify check_use, do_move, do_assign to stop if place has DEREF

def fix_func(func_name, code):
    old = r'static void ' + func_name + r'\(Visitor \*v, const AxMirPlace \*place, AxLocation loc\) \{\n    uint32_t node = resolve_place\(v->ctx, place\);'
    new = r'''static void ''' + func_name + r'''(Visitor *v, const AxMirPlace *place, AxLocation loc) {
    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            // It's behind a pointer. The pointer itself is just used.
            AxMirPlace base = *place;
            base.proj_count = i;
            if (strcmp("''' + func_name + r'''", "check_use") != 0) {
                check_use(v, &base, loc);
                return;
            } else {
                place = &base;
                break;
            }
        }
    }
    uint32_t node = resolve_place(v->ctx, place);'''
    return re.sub(old, new, code)

code = fix_func('check_use', code)
code = fix_func('do_move', code)
code = fix_func('do_assign', code)

with open('bootstrap/axiom0/src/own/own.c', 'w', encoding='utf-8') as f:
    f.write(code)
