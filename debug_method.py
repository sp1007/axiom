import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'return type_error(cx, expr->span, AX_NAME_UNRESOLVED);',
    'if (expr->kind == AX_HIR_EXPR_METHOD_CALL) { fprintf(stderr, "Method unresolved: %s on base type ID %llu\\n", mname.ptr, (unsigned long long)base_ty.v); } return type_error(cx, expr->span, AX_NAME_UNRESOLVED);'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
