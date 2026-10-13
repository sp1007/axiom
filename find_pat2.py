import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

# Find parse_pat_no_or
idx = text.find('static AxAstPat *parse_pat_no_or(Parser *p)')
idx = text.find('AX_TOK_IDENT', idx)
print(text[idx:idx+800])
