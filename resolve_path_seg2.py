import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('static void resolve_path_seg')
if idx != -1:
    print(text[idx+1500:idx+3000])

