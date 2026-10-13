import re

def clean_typeck():
    f = 'bootstrap/axiom0/src/types/typeck.c'
    with open(f, 'r') as file:
        t = file.read()
    
    t = re.sub(r'\{?\s*fprintf\(stderr,\s*"\\nMISMATCH AT %d\\n",\s*\d+\);\s*return', 'return', t)
    t = re.sub(r'fprintf\(stderr,\s*"\\nDEBUG_NAME:[^\n]*\\n",[^)]*\);', '', t)
    
    with open(f, 'w') as file:
        file.write(t)

def clean_lower():
    f = 'bootstrap/axiom0/src/hir/lower.c'
    with open(f, 'r') as file:
        t = file.read()
        
    t = re.sub(r'printf\("lower_path:[^\n]*\\n",[^)]*\);', '', t)
    
    with open(f, 'w') as file:
        file.write(t)

clean_typeck()
clean_lower()
