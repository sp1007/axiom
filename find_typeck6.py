import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('static TypeId instantiate_path')
print(text[idx1:idx1+1500])
