import sys

with open('bootstrap/axiom0/src/syntax/parse.c', 'rb') as f:
    text = f.read().decode('utf-8')

# Revert Clone
text = text.replace(
    'snprintf(fbuf, sizeof(fbuf), "%s: Clone.clone(view(self.%s)), ", fname, fname);',
    'snprintf(fbuf, sizeof(fbuf), "%s: self.%s.clone(), ", fname, fname);'
)

# Revert Ord
text = text.replace(
    'snprintf(fbuf, sizeof(fbuf), "let c = Ord.cmp(view(self.%s), view(other.%s)); match c { Ordering.Equal => {}, _ => return c, }; ", fname, fname);',
    'snprintf(fbuf, sizeof(fbuf), "let c = self.%s.cmp(view(other.%s)); match c { Ordering.Equal => {}, _ => return c, }; ", fname, fname);'
)

# Revert Hash
text = text.replace(
    'snprintf(fbuf, sizeof(fbuf), "Hash.hash(view(self.%s), state); ", fname);',
    'snprintf(fbuf, sizeof(fbuf), "self.%s.hash(state); ", fname);'
)

with open('bootstrap/axiom0/src/syntax/parse.c', 'wb') as f:
    f.write(text.encode('utf-8'))

with open('tests/run/trait2/test_derive.ax', 'rb') as f:
    text = f.read().decode('utf-8')
text = text.replace('let b = eq(view(p1), view(p2));', 'let b = p1.eq(view(p2));')
with open('tests/run/trait2/test_derive.ax', 'wb') as f:
    f.write(text.encode('utf-8'))
