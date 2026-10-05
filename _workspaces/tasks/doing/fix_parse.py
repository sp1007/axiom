import re

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix 1: AX_TOK_GE -> AX_TOK_GT_EQ
code = code.replace('AX_TOK_GE', 'AX_TOK_GT_EQ')

# Fix 2: AX_TOK_KW_SELF_UPPER -> AX_TOK_KW_SELF_TYPE
code = code.replace('AX_TOK_KW_SELF_UPPER', 'AX_TOK_KW_SELF_TYPE')

# Fix 3: param name
code = code.replace('check(p, AX_TOK_KW_SELF)', 'check(p, AX_TOK_KW_SELF_VALUE)')
code = code.replace('ax_interner_get_or_add(p->interner, ax_sv_cstr("Self"))', 'ax_intern_cstr(p->interner, "Self")')
code = code.replace('ax_interner_get_or_add(p->interner, ax_sv_cstr("self"))', 'ax_intern_cstr(p->interner, "self")')
code = code.replace('param->name = 0;', 'param->name = (StrId){0};')

# Fix 4: string ABI (in parse_type and parse_item)
code = re.sub(
    r'type->fn\.abi = peek\(p\)->val\.str_val;',
    r'type->fn.abi = ax_intern(p->interner, ax_sv((const char*)peek(p)->val.str_val.bytes, peek(p)->val.str_val.len));',
    code
)
code = re.sub(
    r'item->fn\.abi = peek\(p\)->val\.str_val;',
    r'item->fn.abi = ax_intern(p->interner, ax_sv((const char*)peek(p)->val.str_val.bytes, peek(p)->val.str_val.len));',
    code
)
code = re.sub(
    r'item->extern_block\.abi = peek\(p\)->val\.str_val;',
    r'item->extern_block.abi = ax_intern(p->interner, ax_sv((const char*)peek(p)->val.str_val.bytes, peek(p)->val.str_val.len));',
    code
)

# Fix 5: Block assignments
code = code.replace('expr->block = *parse_block(p);', 'expr->block.block = *parse_block(p);')
code = code.replace('else_block->block = *parse_block(p);', 'else_block->block.block = *parse_block(p);')
code = code.replace('expr->closure.body->block = *parse_block(p);', 'expr->closure.body->block.block = *parse_block(p);')

# Fix 6: int_val
code = code.replace('peek(p)->val.int_val;', 'peek(p)->val.int_val.value;')

# Fix 7: ax_interner_get -> ax_intern for "import" and "var"
code = code.replace('ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("import"))',
                    'ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("import"))')
# Actually wait, ax_interner_get is declared in interner.h, and I might need to include it.
# parse.c includes lex.h and ast.h. lex.h includes kernel/interner.h. So it's fine.

with open('bootstrap/axiom0/src/syntax/parse.c', 'w', encoding='utf-8') as f:
    f.write(code)
