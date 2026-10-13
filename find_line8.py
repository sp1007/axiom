import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

for i, line in enumerate(text.split('\n')):
    if 'type_error' in line:
        print(f"Line {i+1}: {line.strip()}")
