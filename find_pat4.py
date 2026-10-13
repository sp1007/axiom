import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('static AxAstPat *parse_pat_no_or(Parser *p)')
idx2 = text.find('static AxAstPat *parse_pattern(Parser *p)')
if idx2 < idx1:
    idx2 = text.find('static AxAstBlock *parse_block(Parser *p)')

print(text[idx1:idx1+2000])
