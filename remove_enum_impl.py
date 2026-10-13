import sys

with open('tests/run/trait2/test_derive.ax', 'r', encoding='utf-8') as f:
    text = f.read()

impl_str = '''impl PartialEq for Ordering {
    fn eq(self: view<Ordering>, other: view<Ordering>) -> bool {
        let a = *self as u32;
        let b = *other as u32;
        a == b
    }
}
impl Eq for Ordering {}'''

text = text.replace(impl_str, '')

with open('tests/run/trait2/test_derive.ax', 'w', encoding='utf-8') as f:
    f.write(text)
