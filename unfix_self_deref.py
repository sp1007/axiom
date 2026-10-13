import sys

with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('self == other', '*self == *other')
text = text.replace('self < other', '*self < *other')
text = text.replace('self > other', '*self > *other')
text = text.replace('-> u32 { self }', '-> u32 { *self }')
text = text.replace('state.write_u32(self);', 'state.write_u32(*self);')

with open('tests/run/trait2/test_derive.ax', 'w', encoding='utf-8') as f:
    f.write(text)
