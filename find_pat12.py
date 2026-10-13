import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('field->pat = p_pat;')
print(text[idx1:idx1+1000])
