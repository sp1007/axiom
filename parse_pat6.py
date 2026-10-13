import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('// PathPat')
if idx != -1:
    print(text[idx+1100:idx+2500])

