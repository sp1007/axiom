import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('case AX_ITEM_ENUM:')
if idx1 == -1:
    idx1 = text.find('item->kind = AX_ITEM_ENUM;')
print(text[idx1-200:idx1+1000])
