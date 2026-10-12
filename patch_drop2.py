import sys

file = 'bootstrap/axiom0/src/mir/drop/drop.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''if (drop_fn) {'''
r1 = '''if (drop_fn) {
        fprintf(stderr, "expand_drop: found drop_fn for struct\\n");'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
