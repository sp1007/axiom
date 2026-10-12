import sys

file = 'bootstrap/axiom0/src/mir/drop/drop.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''const AxType *ty = ax_type_get(&thir->interner, ty_id);
    
    AxHirItem *drop_fn = NULL;
    if (ty && ty->kind == AX_TY_STRUCT) {'''

r1 = '''const AxType *ty = ax_type_get(&thir->interner, ty_id);
    
    AxHirItem *drop_fn = NULL;
    if (ty) fprintf(stderr, "expand_drop: place_type kind=%d\\n", ty->kind);
    else fprintf(stderr, "expand_drop: ty is NULL\\n");
    if (ty && ty->kind == AX_TY_STRUCT) {'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
