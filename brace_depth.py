import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i, line in enumerate(lines):
    # strip comments and strings naively
    line = re.sub(r'//.*', '', line)
    line = re.sub(r'".*?"', '""', line)
    
    if re.match(r'^(static |AxThir |TypeId |bool |void |uint32_t |size_t ).*\(.*\) \{', line):
        print(f"Function {line.strip()} at line {i+1} starts at depth {count}")
    
    count += line.count('{')
    count -= line.count('}')

