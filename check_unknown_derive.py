import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('if (strcmp(trait_name, "Copy") == 0)')
if idx != -1:
    print(text[idx:idx+1500])

