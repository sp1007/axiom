with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()
    
print(f"626 context: {text[600:650]}")
print(f"745 context: {text[720:770]}")
print(f"971 context: {text[950:990]}")
