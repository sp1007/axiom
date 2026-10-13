import sys

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('    fprintf(stderr, "DEBUG find_method for %.*s\\n", (int)method_name.len, method_name.ptr);', '')
text = text.replace('            fprintf(stderr, "  impl self_type span=%u\\n", it->impl.self_type->span.start);', '')
text = text.replace('                    fprintf(stderr, "    member fn: %.*s\\n", (int)mn.len, mn.ptr);', '')
text = text.replace('                                fprintf(stderr, "DEBUG MATCH impl span=%u\\n", it->impl.self_type->span.start);', '')

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
