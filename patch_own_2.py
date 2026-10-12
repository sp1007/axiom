import re

with open('bootstrap/axiom0/src/own/own.c', 'r', encoding='utf-8') as f:
    code = f.read()

# I will just revert and do it cleanly.
code = code.replace('''    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            // It's behind a pointer. The pointer itself is just used.
            AxMirPlace base = *place;
            base.proj_count = i;
            if (strcmp("check_use", "check_use") != 0) {
                check_use(v, &base, loc);
                return;
            } else {
                place = &base;
                break;
            }
        }
    }''', '')

code = code.replace('''    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            // It's behind a pointer. The pointer itself is just used.
            AxMirPlace base = *place;
            base.proj_count = i;
            if (strcmp("do_move", "check_use") != 0) {
                check_use(v, &base, loc);
                return;
            } else {
                place = &base;
                break;
            }
        }
    }''', '')

code = code.replace('''    for (size_t i = 0; i < place->proj_count; i++) {
        if (place->projs[i].kind == AX_MIR_PROJ_DEREF) {
            // It's behind a pointer. The pointer itself is just used.
            AxMirPlace base = *place;
            base.proj_count = i;
            if (strcmp("do_assign", "check_use") != 0) {
                check_use(v, &base, loc);
                return;
            } else {
                place = &base;
                break;
            }
        }
    }''', '')

# Actually let's just make resolve_place do the right thing! No!
# The right thing is in check_use, do_move, do_assign.

with open('bootstrap/axiom0/src/own/own.c', 'w', encoding='utf-8') as f:
    f.write(code)
