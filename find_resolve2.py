import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'name' in line and 'span' in line:
            print(f"Line {i+1}: {line.strip()}")
