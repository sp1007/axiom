import sys
with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()

print("Span 126..134: '" + text[126:134] + "'")
print("Span 211..219: '" + text[211:219] + "'")
