import sys

file = 'bootstrap/axiom0/src/interp/interp.c'
with open(file, 'r') as f:
    content = f.read()

content = content.replace('printf("unresolved function call: %llu\\n", (unsigned long long)func_val);', 'fprintf(stderr, "unresolved function call: %llu\\n", (unsigned long long)func_val);')

with open(file, 'w') as f:
    f.write(content)
