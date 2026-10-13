import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

# Change Pass 1b to properly process impl and trait members without weird impl_pass logic
new_pass1b = '''    // Pass 1b: Function signatures
    for (const AxHirItem *top_it = hir->items; top_it; top_it = top_it->next) {
        const AxHirItem *to_check[3] = {top_it, NULL, NULL};
        if (top_it->kind == AX_HIR_ITEM_IMPL) to_check[1] = top_it->impl.members;
        if (top_it->kind == AX_HIR_ITEM_TRAIT) to_check[1] = top_it->trait.members;
        
        for (int list_idx = 0; list_idx < 2; list_idx++) {
            for (const AxHirItem *it = to_check[list_idx]; it; it = (list_idx == 0 ? NULL : it->next)) {
                if (it->kind == AX_HIR_ITEM_FN) {'''

idx1 = text.find('    // Pass 1b: Function signatures')
idx2 = text.find('            if (it->kind == AX_HIR_ITEM_FN) {')
if idx1 != -1 and idx2 != -1:
    text = text[:idx1] + new_pass1b + text[idx2 + len('            if (it->kind == AX_HIR_ITEM_FN) {'):]

# Wait, there's another loop inside Pass 1b, we need to match brace levels.
# Let's just use string replacement on the loop header.
