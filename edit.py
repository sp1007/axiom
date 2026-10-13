import sys

with open('bootstrap/axiom0/src/hir/lower.c', 'rb') as f:
    text = f.read().decode('utf-8')

new_text = text.replace(
    'p.symbol = get_symbol(ctx, last);\n    p.name = last->name;\n    p.generic_args = lower_generic_args(ctx, last->generic_args);\n    return p;',
    'p.symbol = get_symbol(ctx, last);\n    p.name = last->name;\n    p.generic_args = lower_generic_args(ctx, last->generic_args);\n    printf("lower_path: first name %llu, last name %llu, symbol %llu\\n", (unsigned long long)seg->name.v, (unsigned long long)last->name.v, (unsigned long long)p.symbol.v);\n    return p;'
)

with open('bootstrap/axiom0/src/hir/lower.c', 'wb') as f:
    f.write(new_text.encode('utf-8'))
