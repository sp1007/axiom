import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('if (consume(p, AX_TOK_LPAREN)) {\n                pat->kind = AX_PAT_PATH;')
if idx1 == -1:
    idx1 = text.find('pat->kind = AX_PAT_PATH;')
print(text[idx1-200:idx1+1000])
