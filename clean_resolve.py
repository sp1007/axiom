import re
with open('bootstrap/axiom0/src/resolve/resolve.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'fprintf\(stderr, "\\nRESOLVE\.C UNRESOLVED:.*?emit_diag\(env, AX_NAME_UNRESOLVED, [a-z0-9_>:-]+\);', lambda m: m.group(0).split('emit_diag')[1], text)
text = text.replace('fprintf(stderr, "\\nRESOLVE.C UNRESOLVED:', '')

with open('bootstrap/axiom0/src/resolve/resolve.c', 'w', encoding='utf-8') as f:
    f.write(text)
