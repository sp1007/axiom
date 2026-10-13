import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

idx1 = text.find('static AxAstPat *parse_pat_no_or(Parser *p) {')
print(text[idx1+1500:idx1+3500])
