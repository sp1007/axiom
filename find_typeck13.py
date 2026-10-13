import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

for idx1, line in enumerate(text.split('\n')):
    if 'case AX_HIR_PAT_PATH:' in line:
        print(f"Line {idx1+1}: {line.strip()}")
