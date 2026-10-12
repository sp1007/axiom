import re

with open('bootstrap/axiom0/src/hir/lower.c', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(r'(param->is_mut = ast_param->is_mut;)', r'\1\n            param->name = ast_param->name;', code)

with open('bootstrap/axiom0/src/hir/lower.c', 'w', encoding='utf-8') as f:
    f.write(code)
