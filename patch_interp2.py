import sys
import re

file = 'bootstrap/axiom0/src/interp/interp.c'
with open(file, 'r') as f:
    content = f.read()

content = re.sub(r'\} else if \(term->kind == AX_MIR_TERM_DROP\) \{.*?current_bb = term->drop.target;\s*\}', '} else if (term->kind == AX_MIR_TERM_DROP) { AX_ICE("AX_MIR_TERM_DROP should have been elaborated away"); }', content, flags=re.DOTALL)

with open(file, 'w') as f:
    f.write(content)
