import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('else if (check(p, AX_TOK_IDENT) || (check(p, AX_TOK_KW_SELF_TYPE) || check(p, AX_TOK_KW_SELF_VALUE)) || check(p, AX_TOK_KW_MUT)) {')
if idx != -1:
    print(text[idx:idx+1500])

