import re

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace condition 1
code = re.sub(r'check\(p, AX_TOK_KW_SELF_TYPE\)', 
              r'(check(p, AX_TOK_KW_SELF_TYPE) || check(p, AX_TOK_KW_SELF_VALUE))', code)

# Replace condition 2
code = re.sub(r'tok->kind == AX_TOK_KW_SELF_TYPE', 
              r'(tok->kind == AX_TOK_KW_SELF_TYPE || tok->kind == AX_TOK_KW_SELF_VALUE)', code)

# Fix the ternary operators that were modified
code = re.sub(r'\(\(check\(p, AX_TOK_KW_SELF_TYPE\) \|\| check\(p, AX_TOK_KW_SELF_VALUE\)\)\) \? ax_intern_cstr\(p->interner, "Self"\) : peek\(p\)->val.ident_val',
              r'(check(p, AX_TOK_KW_SELF_TYPE) ? ax_intern_cstr(p->interner, "Self") : (check(p, AX_TOK_KW_SELF_VALUE) ? ax_intern_cstr(p->interner, "self") : peek(p)->val.ident_val))', code)

with open('bootstrap/axiom0/src/syntax/parse.c', 'w', encoding='utf-8') as f:
    f.write(code)
