with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_func = False
count = 0
for i, line in enumerate(lines):
    if "AxThir ax_typeck(" in line:
        print(f"ax_typeck starts at {i+1}")
        in_func = True
        count = 0
    
    if in_func:
        count += line.count('{')
        count -= line.count('}')
        if count == 0:
            print(f"function closed at {i+1}")
            break

print(f"Count at end: {count}")
