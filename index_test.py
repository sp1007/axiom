with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()
    
print(f"Char at 626 is '{text[626]}', text: {text[626:650]}")
print(f"Char at 745 is '{text[745]}', text: {text[745:770]}")
print(f"Char at 971 is '{text[971]}', text: {text[971:990]}")
