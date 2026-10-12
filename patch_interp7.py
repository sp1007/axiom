import sys

file = 'bootstrap/axiom0/src/interp/interp.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t sym_v) {
    if (sym_v == 0) return NULL;
    
    for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {'''

r1 = '''static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t sym_v) {
    if (sym_v == 0) return NULL;
    fprintf(stderr, "interp searching for symbol %llu\\n", (unsigned long long)sym_v);
    for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) fprintf(stderr, "  interp sees symbol %llu\\n", (unsigned long long)it->fn.symbol.v);
'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
