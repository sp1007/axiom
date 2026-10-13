import sys
with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()
if 'DEBUG AMBIGUOUS method' in text:
    print('YES')
else:
    print('NO')
