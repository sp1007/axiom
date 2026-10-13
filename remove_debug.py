import sys, re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'DEBUG IMPL CHECK[^\n]+\n', '', text)
text = re.sub(r'DEBUG find_method[^\n]+\n', '', text)
text = re.sub(r'DEBUG OP FAIL[^\n]+\n', '', text)
text = re.sub(r'fprintf\(stderr, "DEBUG resolve_path_seg[^\n]+\n', '', text)

text = text.replace(
'''            if (ax_sv_eq_cstr(method_name, "eq")) {
                const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
                
                if (b->kind == AX_TY_VIEW) ;
                
            }''', '')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'fprintf\(stderr, "DEBUG resolve_path_seg[^\n]+\n', '', text)

with open('bootstrap/axiom0/src/resolve/resolve.c', 'w', encoding='utf-8') as f:
    f.write(text)
