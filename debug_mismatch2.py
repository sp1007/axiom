import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'if (!v->is_struct) fprintf(stderr, "MISMATCH expr %d\\n", expr->kind); return type_error(cx, expr->span, AX_TYPE_MISMATCH);',
    'if (!v->is_struct) return type_error(cx, expr->span, AX_TYPE_MISMATCH);'
)
text = text.replace(
    'if (!found_variant) fprintf(stderr, "MISMATCH expr %d\\n", expr->kind); return type_error(cx, expr->span, AX_TYPE_MISMATCH);',
    'if (!found_variant) return type_error(cx, expr->span, AX_TYPE_MISMATCH);'
)
text = text.replace(
    'return type_error(cx, expr->span, AX_TYPE_MISMATCH);',
    '{ fprintf(stderr, "MISMATCH expr %d line %d\\n", expr->kind, __LINE__); return type_error(cx, expr->span, AX_TYPE_MISMATCH); }'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
