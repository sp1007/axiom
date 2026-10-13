import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('case AX_HIR_EXPR_FIELD:')
idx1 = text.find('} else if (t->kind == AX_TY_ENUM)', idx1)
print(text[idx1:idx1+1500])
