import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''                         if (b->kind == AX_TY_VIEW) fprintf(stderr, " b->pointee=%u", b->view.pointee.v);''',
'''                         fprintf(stderr, " b->pointee=%u", b->view.pointee.v);''')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
