import sys

with open('bootstrap/axiom0/src/hir/lower.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('case AX_ITEM_ENUM:')
print(text[idx1-200:idx1+1500])
