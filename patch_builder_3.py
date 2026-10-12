import re

with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace my old patch (I need to find it and replace it)
old_code = r'''        callee\.constant\.kind = AX_MIR_CONST_FUNC;
        callee\.constant\.func = method_item;'''

new_code = '''        callee.constant.kind = AX_MIR_CONST_INT;
        callee.constant.val = method_item->fn.symbol.v;'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(code)
