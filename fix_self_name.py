import re

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace condition
old_ternary = r'\(check\(p, AX_TOK_KW_SELF_TYPE\) \|\| check\(p, AX_TOK_KW_SELF_VALUE\)\) \? ax_intern_cstr\(p->interner, "Self"\) : peek\(p\)->val.ident_val'
new_ternary = r'(check(p, AX_TOK_KW_SELF_TYPE) ? ax_intern_cstr(p->interner, "Self") : (check(p, AX_TOK_KW_SELF_VALUE) ? ax_intern_cstr(p->interner, "self") : peek(p)->val.ident_val))'

code = re.sub(old_ternary, new_ternary, code)

with open('bootstrap/axiom0/src/syntax/parse.c', 'w', encoding='utf-8') as f:
    f.write(code)
