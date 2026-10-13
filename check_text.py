import sys

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()
    if 'type_error_real' in text:
        print("YES")
    else:
        print("NO")
