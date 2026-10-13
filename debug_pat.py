import sys
import re

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

# Let's insert debug right before returning type_error
text = re.sub(
    r'if \(!unify_ty\(cx, ty, path_ty\)\) \{\s*return type_error\(cx, pat->span, AX_TYPE_MISMATCH\);\s*\}',
    r'''if (!unify_ty(cx, ty, path_ty)) {
                fprintf(stderr, "DEBUG UNIFY FAILED\\n");
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }''',
    text
)

text = re.sub(
    r'if \(t->kind != AX_TY_ENUM\) \{\s*return type_error\(cx, pat->span, AX_TYPE_MISMATCH\);\s*\}',
    r'''if (t->kind != AX_TY_ENUM) {
                fprintf(stderr, "DEBUG ENUM FAILED\\n");
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }''',
    text
)

text = re.sub(
    r'if \(!found_variant\) return type_error\(cx, pat->span, AX_TYPE_MISMATCH\);',
    r'''if (!found_variant) {
                fprintf(stderr, "DEBUG NOT FOUND FAILED\\n");
                return type_error(cx, pat->span, AX_TYPE_MISMATCH);
            }''',
    text
)

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
