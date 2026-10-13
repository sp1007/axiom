import sys
import re

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = re.sub(
    r'if \(!unify_ty\(cx, ty, path_ty\)\) \{',
    r'''if (!unify_ty(cx, ty, path_ty)) {
                fprintf(stderr, "DEBUG PAT MISMATCH: unify failed\n");''',
    text
)

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
