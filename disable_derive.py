import sys

with open('tests/run/trait2/test_derive.ax', 'rb') as f:
    text = f.read().decode('utf-8')

# Comment out @derive
text = text.replace('@derive(Clone, Eq, PartialEq, Ord, Hash)', '//@derive(Clone, Eq, PartialEq, Ord, Hash)')

with open('tests/run/trait2/test_derive.ax', 'wb') as f:
    f.write(text.encode('utf-8'))
