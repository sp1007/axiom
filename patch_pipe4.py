import sys

file = 'bootstrap/axiom0/src/driver/pipeline.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''m->fn.symbol.v = dummy_sym++;'''
r1 = '''m->fn.symbol.v = dummy_sym++;
                        fprintf(stderr, "pipeline assigned symbol %llu to %s\\n", (unsigned long long)m->fn.symbol.v, buf);'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
