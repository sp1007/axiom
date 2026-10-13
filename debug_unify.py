import sys
import re

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = re.sub(
    r'if \(!unify_ty\(cx, ty, path_ty\)\) \{',
    r'''if (!unify_ty(cx, ty, path_ty)) {
                fprintf(stderr, "DEBUG PAT MISMATCH: unify failed for ");
                print_type(cx->thir, ty);
                fprintf(stderr, " and ");
                print_type(cx->thir, path_ty);
                fprintf(stderr, "\n");''',
    text
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
