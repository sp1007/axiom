import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'if (path->symbol.v != 0) {',
    'if (path->symbol.v != 0) { fprintf(stderr, "Looking up symbol %llu (kind %d)\\n", (unsigned long long)path->symbol.v, it->kind);'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
