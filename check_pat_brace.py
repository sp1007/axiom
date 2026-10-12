import re
with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()
count = 0
in_check_pat = False
for i, line in enumerate(lines):
    if "static TypeId check_pat(" in line:
        in_check_pat = True
        count = 0
    if in_check_pat:
        count += line.count('{')
        count -= line.count('}')
        if count == 0:
            print(f"check_pat closes at {i+1}")
            break
