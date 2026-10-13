import sys
import re

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

# We can replace the unify check to print kinds:
text = re.sub(
    r'if \(!unify_ty\(cx, ty, path_ty\)\) \{',
    r'''if (!unify_ty(cx, ty, path_ty)) {
                const AxType *ta = ax_type_get(&cx->thir->interner, resolve_ty(cx, ty));
                const AxType *tb = ax_type_get(&cx->thir->interner, resolve_ty(cx, path_ty));
                fprintf(stderr, "DEBUG PAT MISMATCH KINDS: %d vs %d\n", (int)ta->kind, (int)tb->kind);''',
    text
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
