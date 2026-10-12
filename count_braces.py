with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i, line in enumerate(lines):
    if "AxThir ax_typeck(" in line:
        print(f"ax_typeck starts at {i+1}")
        count = 0
    count += line.count('{')
    count -= line.count('}')
    if count == 0 and "AxThir ax_typeck(" not in line and i > 600:
        print(f"function closed at {i+1}")
        break

print(f"Count at end: {count}")
