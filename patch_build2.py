import sys

file = 'bootstrap/axiom0/src/driver/build_native/build.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, item);
                if (!pty || pty->v == 0) continue;
                const AxType *fn_ty = ax_type_get(&st->thir.interner, *pty);'''
r1 = '''const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, item);
                const AxType *fn_ty = NULL;
                AxType dummy_fn_ty = {0};
                if (!pty || pty->v == 0) {
                    if (strncmp(ax_interner_get(&st->interner, item->fn.name).ptr, "drop_impl_", 10) == 0) {
                        dummy_fn_ty.kind = AX_TY_FN;
                        dummy_fn_ty.fn.is_unsafe = false;
                        dummy_fn_ty.fn.abi.v = 0;
                        dummy_fn_ty.fn.param_count = 1;
                        dummy_fn_ty.fn.param_types = malloc(sizeof(TypeId)); // leak for now
                        AxType ptr_t = { .kind = AX_TY_MUT_VIEW };
                        dummy_fn_ty.fn.param_types[0] = ax_intern_type((TypeInterner*)&st->thir.interner, &ptr_t);
                        dummy_fn_ty.fn.ret_type = ((TypeInterner*)&st->thir.interner)->t_unit;
                        fn_ty = &dummy_fn_ty;
                    } else {
                        continue;
                    }
                } else {
                    fn_ty = ax_type_get(&st->thir.interner, *pty);
                }'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
