import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = text.replace(
    'd.message = "unresolved name";',
    'char msg[256]; snprintf(msg, sizeof(msg), "unresolved name (typeck): %s", path ? ax_source_db_span_text(cx->db, path->span).ptr : "?"); d.message = msg;'
)
text = text.replace(
    'return type_error(cx, expr->span, AX_NAME_UNRESOLVED);',
    '{ char msg[256]; snprintf(msg, sizeof(msg), "unresolved name expr %d (line %d)", expr->kind, __LINE__); AxDiagnostic d = {0}; d.code = AX_NAME_UNRESOLVED; d.severity = AX_DIAG_ERROR; d.message = msg; d.primary = expr->span; ax_diag_sink_report(cx->sink, &d); return cx->thir->interner.t_error; }'
)

with open('bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
