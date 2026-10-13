import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('static const AxHirItem *find_method')
if idx != -1:
    print(text[idx+1500:idx+3000])

