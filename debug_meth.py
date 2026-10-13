import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'return type_error(cx, expr->span, AX_NAME_UNRESOLVED);',
    'fprintf(stderr, "METH NOT FOUND: %s on ty %d\\n", mname.ptr, (int)base_ty.v); return type_error(cx, expr->span, AX_NAME_UNRESOLVED);'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
