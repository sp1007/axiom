import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('en.enm.variant_count = vcount;')
if idx != -1:
    print(text[idx:idx+2500])

