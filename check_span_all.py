with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()
    start = text.find('Ordering.Equal')
    while start != -1:
        print("Found Ordering.Equal at span", start, "..", start + 14)
        start = text.find('Ordering.Equal', start + 1)
