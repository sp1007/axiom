import sys
import re

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

# Revert my changes in check_pat
text = re.sub(
    r'bool found_variant = false;\s*size_t vidx = 0;\s*for \(const AxHirVariantDecl \*v = t->enm\.def->enum_decl\.variants; v; v = v->next\) \{\s*if \(v->symbol\.v == pat->path\.path\.symbol\.v\) \{',
    r'''StrView name = ax_source_db_span_text(cx->db, pat->path.path.span);
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
                if (ax_sv_eq(var_name, vname)) {''',
    text
)

# And in check_expr for AX_HIR_EXPR_PATH!
text = re.sub(
    r'bool found_variant = false;\s*size_t vidx = 0;\s*for \(const AxHirVariantDecl \*v = t->enm\.def->enum_decl\.variants; v; v = v->next\) \{\s*if \(v->symbol\.v == expr->path\.symbol\.v\) \{',
    r'''StrView name = ax_source_db_span_text(cx->db, expr->span);
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
                if (ax_sv_eq(var_name, vname)) {''',
    text
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
