import re
f = 'bootstrap/axiom0/src/resolve/resolve.c'
with open(f, 'r') as file:
    t = file.read()
t = re.sub(r'emit_diag\(env, AX_NAME_UNRESOLVED, (.*?)\);', r'fprintf(stderr, "\\nUNRESOLVED span\\n"); emit_diag(env, AX_NAME_UNRESOLVED, \1);', t)
with open(f, 'w') as file:
    file.write(t)
