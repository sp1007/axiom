import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

import re
text = re.sub(
    r'ax_interner_get\([^,]+, ([^)]+)\)',
    r'((\1).v == 0 ? (fprintf(stderr, "ZERO AT line %d\n", __LINE__), (StrView){0,0}) : ax_interner_get(cx->str_in, \1))',
    text
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
