import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Ordering::Equal', 'Ordering.Equal')

with open('bootstrap/axiom0/src/syntax/parse.c', 'w', encoding='utf-8') as f:
    f.write(text)
