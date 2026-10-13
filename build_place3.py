import sys

with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('static AxMirPlace build_place')
if idx != -1:
    print(text[idx+4000:idx+5500])

