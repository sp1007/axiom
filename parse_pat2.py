import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('static AxAstPat *parse_pat_no_or(Parser *p)')
if idx != -1:
    print(text[idx:idx+1500])

