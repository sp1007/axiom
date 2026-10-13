import re

f = 'bootstrap/axiom0/src/resolve/resolve.c'
with open(f, 'r') as file:
    t = file.read()

t = re.sub(r'emit_diag\(env, AX_NAME_UNRESOLVED, seg->span\);', 'fprintf(stderr, "\\\\nUNRESOLVED: %.*s\\\\n", (int)seg->name_text.len, seg->name_text.ptr); emit_diag(env, AX_NAME_UNRESOLVED, seg->span);', t)
# wait, wait! The regex replace didn't work before because I replaced the already mangled file. I should `git restore` it first.
