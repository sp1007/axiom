import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(r'size_t i = 1;\n            for \(const AxHirExpr \*a = expr->method_call\.args;', 
              r'size_t i = has_self ? 1 : 0;\n            for (const AxHirExpr *a = expr->method_call.args;', code)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
