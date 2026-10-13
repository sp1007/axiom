import sys
import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'fprintf\(stderr, "DEBUG MATCH impl span=%u mname=%\.\*s method_name=%\.\*s\\n"[^\)]+\);', '', text)
text = re.sub(r'fprintf\(stderr, "DEBUG find_method for %\.\*s\\n"[^\)]+\);', '', text)
text = re.sub(r'fprintf\(stderr, "  impl self_type span=%u\\n"[^\)]+\);', '', text)
text = re.sub(r'fprintf\(stderr, "    member fn: %\.\*s\\n"[^\)]+\);', '', text)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(text)
