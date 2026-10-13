import sys
import re

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'rb') as f:
    text = f.read().decode('utf-8')

text = re.sub(
    r'StrView name = ax_source_db_span_text\(cx->db, path->span\);',
    r'''StrView name = ax_source_db_span_text(cx->db, path->span);
    fprintf(stderr, "DEBUG LOOKUP: %.*s\n", (int)name.len, name.ptr);''',
    text
)

with open('build-snap-T056/bootstrap/axiom0/src/types/typeck.c', 'wb') as f:
    f.write(text.encode('utf-8'))
