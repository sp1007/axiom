import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

variant_insert = '''            TypeId en_ty = ax_intern_type(&thir.interner, &en);
            AxItemTypeMap_insert(&thir.item_types, it, en_ty);
            for (const AxHirVariantDecl *v = it->enum_decl.variants; v; v = v->next) {
                if (v->symbol.v != 0) {
                    AxSymbolTypeMap_insert(&thir.symbol_types, v->symbol, en_ty);
                }
            }'''

text = text.replace(
'''            TypeId en_ty = ax_intern_type(&thir.interner, &en);
            AxItemTypeMap_insert(&thir.item_types, it, en_ty);''', variant_insert)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
