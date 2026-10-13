import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

lines = text.split('\n')
for i in range(1400, 1420):
    print(f"Line {i+1}: {lines[i]}")
