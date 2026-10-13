import sys
import re

with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace any fprintf(stderr, "DEBUG...); with nothing.
text = re.sub(r'fprintf\s*\(\s*stderr\s*,\s*"DEBUG[^"]*"[^)]*\)\s*;', '', text)

with open('bootstrap/axiom0/src/resolve/resolve.c', 'w', encoding='utf-8') as f:
    f.write(text)
