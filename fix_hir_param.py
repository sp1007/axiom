import re

with open('bootstrap/axiom0/src/hir/hir.h', 'r', encoding='utf-8') as f:
    code = f.read()

# Add name to AxHirParam
code = code.replace('''struct AxHirParam {
    Span span;
    bool is_mut;
    AxSymbolId symbol;
    AxHirType *type;
    AxHirParam *next;
};''', '''struct AxHirParam {
    Span span;
    bool is_mut;
    StrId name;
    AxSymbolId symbol;
    AxHirType *type;
    AxHirParam *next;
};''')

with open('bootstrap/axiom0/src/hir/hir.h', 'w', encoding='utf-8') as f:
    f.write(code)

with open('bootstrap/axiom0/src/hir/lower.c', 'r', encoding='utf-8') as f:
    code2 = f.read()

# Add param->name = ast_param->name;
code2 = code2.replace('param->span = ast_param->span;\n            param->is_mut = ast_param->is_mut;', 
                      'param->span = ast_param->span;\n            param->is_mut = ast_param->is_mut;\n            param->name = ast_param->name;')

with open('bootstrap/axiom0/src/hir/lower.c', 'w', encoding='utf-8') as f:
    f.write(code2)
