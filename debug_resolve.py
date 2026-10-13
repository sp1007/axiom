import re

f = 'bootstrap/axiom0/src/resolve/resolve.c'
with open(f, 'r') as file:
    t = file.read()

t = re.sub(r'emit_diag\(env, AX_NAME_UNRESOLVED, seg->span\);', 'fprintf(stderr, "\\nUNRESOLVED: %.*s\\n", (int)seg->name_text.len, seg->name_text.ptr); emit_diag(env, AX_NAME_UNRESOLVED, seg->span);', t)

with open(f, 'w') as file:
    file.write(t)
