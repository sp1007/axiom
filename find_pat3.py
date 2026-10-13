import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx = text.find('static AxAstPat *parse_pat_no_or(Parser *p)')
idx = text.find('AX_TOK_IDENT', idx)
idx = text.find('AX_TOK_IDENT', idx + 10)
idx = text.find('AX_TOK_IDENT', idx + 10)
print(text[idx-200:idx+800])
