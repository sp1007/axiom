with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i, line in enumerate(lines):
    count += line.count('{')
    count -= line.count('}')
    if count < 0:
        print(f"Negative count at {i+1}")
        break

print(f"End count: {count}")
