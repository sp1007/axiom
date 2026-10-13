import sys

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1430, 1445):
    print(f"Line {i+1}: {lines[i].strip()}")
