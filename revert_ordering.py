import sys

with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Ordering::Less', 'Ordering.Less')
text = text.replace('Ordering::Equal', 'Ordering.Equal')
text = text.replace('Ordering::Greater', 'Ordering.Greater')

with open('tests/run/trait2/test_derive.ax', 'w', encoding='utf-8') as f:
    f.write(text)
