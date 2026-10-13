import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('check_pat(TypeckCtx')
print(text[idx1-200:idx1+200])
