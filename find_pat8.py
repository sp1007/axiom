import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('if (consume(p, AX_TOK_LPAREN)) {')
print(text[idx1:idx1+1000])
