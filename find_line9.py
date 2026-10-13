import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1420, 1460):
    line = lines[i].strip()
    if 'type_error' in line:
        print(f"Line {i+1}: {line}")
