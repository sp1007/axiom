import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('case AX_HIR_PAT_PATH:', 1000)
print("Found AX_HIR_PAT_PATH at", idx1)

old_code = '''            StrView name = ax_source_db_span_text(cx->db, pat->path.path.span);
            StrView vname = name;
            const char *dot = NULL;
            for (size_t i = 0; i < name.len; i++) {
                if (name.ptr[i] == '.') dot = name.ptr + i;
            }
            if (dot) {
                vname.ptr = dot + 1;
                vname.len = name.len - (dot - name.ptr) - 1;
            }

            bool found_variant = false;
            size_t vidx = 0;
            for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                StrView var_name = ax_interner_get(cx->str_in, v->name);
                if (ax_sv_eq(var_name, vname)) {'''

new_code = '''            bool found_variant = false;
            size_t vidx = 0;
            for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                if (v->symbol.v != 0 && v->symbol.v == pat->path.path.symbol.v) {
                    found_variant = true;
                    break;
                }
                vidx++;
            }
            if (!found_variant) {
                StrView name = ax_source_db_span_text(cx->db, pat->path.path.span);
                StrView vname = name;
                const char *dot = NULL;
                for (size_t i = 0; i < name.len; i++) {
                    if (name.ptr[i] == '.') dot = name.ptr + i;
                }
                if (dot) {
                    vname.ptr = dot + 1;
                    vname.len = name.len - (dot - name.ptr) - 1;
                }
                vidx = 0;
                for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                    StrView var_name = ax_interner_get(cx->str_in, v->name);
                    if (ax_sv_eq(var_name, vname) || (name.len == 0 && v->name.v == pat->path.path.name.v)) {
                        found_variant = true;
                        break;
                    }
                    vidx++;
                }
            }
            
            if (found_variant) {
                const AxHirVariantDecl *v = t->enm.def->enum_decl.variants;
                for (size_t i = 0; i < vidx; i++) v = v->next;'''

if old_code in text:
    print("Old code found!")
else:
    print("Old code NOT found!")
    
text = text.replace(old_code, new_code)
with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
