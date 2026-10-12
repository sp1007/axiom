import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

brace_old = '''            check_literal_ranges(&cx);
        }
    }

    finalize_types(&cx);'''

brace_new = '''            check_literal_ranges(&cx);
                }
            }
        }
    }

    finalize_types(&cx);'''

code = code.replace(brace_old, brace_new)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
