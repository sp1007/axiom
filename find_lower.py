import sys

with open('bootstrap/axiom0/src/hir/lower.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('AxHirVariantDecl *lower_variant')
if idx1 == -1: idx1 = text.find('lower_variant')
print(text[idx1-200:idx1+1500])
