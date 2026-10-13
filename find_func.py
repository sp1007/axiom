import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'd.code = AX_NAME_UNRESOLVED' in line:
        # Find the function name
        for j in range(i, -1, -1):
            if lines[j].startswith('static ') and '{' in lines[j]:
                print(lines[j].strip())
                break
