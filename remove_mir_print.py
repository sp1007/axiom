import sys

with open('bootstrap/axiom0/src/verify/verify.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace('ax_mir_print(stderr, body);', '')

with open('bootstrap/axiom0/src/verify/verify.c', 'wb') as f:
    f.write(text.encode('utf-8'))
