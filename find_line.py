import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

lines = text.split('\n')
start = max(0, 1437 - 10)
end = min(len(lines), 1437 + 10)
for i in range(start, end):
    print(f"Line {i+1}: {lines[i]}")
