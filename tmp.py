import sys

lines = open('bootstrap/axiom0/src/resolve/resolve.c').read().splitlines()
for i, line in enumerate(lines):
    if 'emit_diag(env, AX_NAME_UNRESOLVED' in line:
        lines[i] = f'        fprintf(stderr, "AX_NAME_UNRESOLVED at line {i+1}\\n");\n{line}'

open('bootstrap/axiom0/src/resolve/resolve.c', 'w').write('\n'.join(lines) + '\n')
