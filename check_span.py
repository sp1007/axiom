with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()

print("Char 102..106:", text[102:106])
print("Around it:", text[90:120])
