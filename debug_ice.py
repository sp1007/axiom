import sys

with open('bootstrap/axiom0/src/kernel/interner.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'AX_ICE("ax_interner_get: invalid StrId %d (%zu strings)", (int)id.v, interner->strings_len);',
    'fprintf(stderr, "ICE ax_interner_get 0\\n"); AX_ICE("ax_interner_get: invalid StrId %d (%zu strings)", (int)id.v, interner->strings_len);'
)

with open('bootstrap/axiom0/src/kernel/interner.c', 'wb') as f:
    f.write(text.encode('utf-8'))
