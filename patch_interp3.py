import sys

file = 'bootstrap/axiom0/src/interp/interp.c'
with open(file, 'r') as f:
    content = f.read()

content = content.replace('panic_interp(ctx, "unresolved function call");', 'printf("unresolved function call: %llu\\n", (unsigned long long)func_val); panic_interp(ctx, "unresolved function call");')

with open(file, 'w') as f:
    f.write(content)
