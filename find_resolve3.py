import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('if (it->kind == AX_ITEM_ENUM) {')
print(text[idx1:idx1+1000])
