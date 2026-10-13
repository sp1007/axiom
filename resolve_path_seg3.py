import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('} else if (hkind == SYM_ITEM && head_node && ((const AxAstItem*)head_node)->kind == AX_ITEM_ENUM) {')
if idx != -1:
    print(text[idx:idx+1000])

