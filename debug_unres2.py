import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'char msg[256]; snprintf(msg, sizeof(msg), "unresolved name (typeck): %s", path ? ax_source_db_span_text(cx->db, path->span).ptr : "?"); d.message = msg;',
    'char msg[256]; snprintf(msg, sizeof(msg), "unresolved name (typeck): %s (symbol %llu)", path ? ax_source_db_span_text(cx->db, path->span).ptr : "?", path ? (unsigned long long)path->symbol.v : 0); d.message = msg;'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
