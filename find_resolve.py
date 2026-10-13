import sys

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'ax_source_db_span_text' in line:
            print(f"Line {i+1}: {line.strip()}")
