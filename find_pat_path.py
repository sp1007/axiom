import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('case AX_HIR_PAT_PATH:', 1000)
idx2 = text.find('case AX_HIR_PAT_TUPLE:', idx1)
print(text[idx1:idx2])
