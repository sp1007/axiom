import sys

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'd.message = "unresolved name";',
    'char msg[256]; snprintf(msg, sizeof(msg), "unresolved name (typeck): %s (symbol %llu, strid %llu)", name.ptr ? name.ptr : "?", (unsigned long long)path->symbol.v, (unsigned long long)path->name.v); d.message = msg;'
)

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
