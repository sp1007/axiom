import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'type_error' in line and 'return' not in line:
            print(f"Line {i+1}: {line.strip()}")
