import re
with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()
count = 0
in_func = False
for i, line in enumerate(lines):
    if "AxThir ax_typeck(" in line:
        in_func = True
        count = 0
    if in_func:
        old_count = count
        count += line.count('{')
        count -= line.count('}')
        if old_count != count:
            print(f"L{i+1}: {old_count} -> {count} | {line.strip()}")
        if count == 0:
            print(f"Closed at {i+1}")
            break
