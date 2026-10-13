import sys

with open('bootstrap/axiom0/src/hir/lower.c', 'rb') as f:
    text = f.read().decode('utf-8')

new_text = text.replace(
    'printf("lower_path: first name %llu, last name %llu, symbol %llu\\n", (unsigned long long)seg->name.v, (unsigned long long)last->name.v, (unsigned long long)p.symbol.v);',
    'printf("lower_path: seg %p (name %llu), last %p (name %llu), symbol %llu\\n", (void*)seg, (unsigned long long)seg->name.v, (void*)last, (unsigned long long)last->name.v, (unsigned long long)p.symbol.v);'
)

with open('bootstrap/axiom0/src/hir/lower.c', 'wb') as f:
    f.write(new_text.encode('utf-8'))
