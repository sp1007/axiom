import sys

file = 'bootstrap/axiom0/src/interp/interp.c'
with open(file, 'r') as f:
    content = f.read()

r1 = '''static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t symbol_val) {
    fprintf(stderr, "find_func_by_symbol looking for %llu\\n", (unsigned long long)symbol_val);
    for (AxHirItem *it = ctx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) fprintf(stderr, "  saw fn symbol %llu\\n", (unsigned long long)it->fn.symbol.v);
        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == symbol_val) return it;
    }
    return NULL;
}'''
content = content.replace('static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t symbol_val) {\n    for (AxHirItem *it = ctx->hir->items; it; it = it->next) {\n        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == symbol_val) return it;\n    }\n    return NULL;\n}', r1)

with open(file, 'w') as f:
    f.write(content)
