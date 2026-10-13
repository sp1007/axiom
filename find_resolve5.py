import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('bind_node enum variant:')
print(text[idx1-200:idx1+200])
