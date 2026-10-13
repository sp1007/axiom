import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

import re
text = re.sub(
    r'return type_error\(cx, expr->span, AX_NAME_UNRESOLVED\);',
    r'{ fprintf(stderr, "Unresolved method or field on expr kind %d\\n", (int)expr->kind); return type_error(cx, expr->span, AX_NAME_UNRESOLVED); }',
    text
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
