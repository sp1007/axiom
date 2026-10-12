import sys

file = 'bootstrap/axiom0/src/interp/interp.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t sym_v) {
    if (sym_v == 0) return NULL;
    
    StrId target_name = {0};
    for (const AxAstItem *it = ctx->ast->items; it; it = it->next) {'''

r1 = '''static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t sym_v) {
    if (sym_v == 0) return NULL;
    
    for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == (uint32_t)sym_v) {
            return (AxHirItem*)it;
        }
    }

    StrId target_name = {0};
    for (const AxAstItem *it = ctx->ast->items; it; it = it->next) {'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
