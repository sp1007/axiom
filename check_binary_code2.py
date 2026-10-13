import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('static TypeId check_binary')
if idx != -1:
    print(text[idx+2000:idx+4000])

