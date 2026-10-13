import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

for line in text.split('\n'):
    if 'AX_TYPE_MISMATCH' in line:
        print(line.strip())
