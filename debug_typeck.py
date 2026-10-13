import re
f = 'bootstrap/axiom0/src/types/typeck.c'
with open(f, 'r') as file:
    t = file.read()
t = t.replace('d.code = AX_NAME_UNRESOLVED;', 'fprintf(stderr, "\\nUNRESOLVED PATH in typeck: %.*s\\n", (int)name.len, name.ptr); d.code = AX_NAME_UNRESOLVED;')
with open(f, 'w') as file:
    file.write(t)
