import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

for i in range(1430, 1445):
    print(text.split('\n')[i].strip())
