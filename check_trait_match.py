import sys
with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('''                        if (!match && base_path->symbol.v == 0) {
                            StrView it_name = ax_interner_get(cx->str_in, it->trait.name);
                            StrView name = ax_source_db_span_text(cx->db, base_path->span);
                            if (ax_sv_eq(it_name, name)) match = true;
                        }''',
'''                        if (!match) {
                            StrView it_name = ax_interner_get(cx->str_in, it->trait.name);
                            StrView name = ax_source_db_span_text(cx->db, base_path->span);
                            if (name.ptr == NULL || name.len == 0) {
                                if (base_path->symbol.v != 0) {
                                    // Wait, base_path->symbol.v is the symbol ID, NOT the string ID!
                                    // But resolve.c creates symbols, it doesn't give us the string ID here!
                                    // Wait, is there a way to get the string from base_path?
                                }
                            }
                            if (name.ptr != NULL && name.len > 0 && ax_sv_eq(it_name, name)) match = true;
                        }''')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
