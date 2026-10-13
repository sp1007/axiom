import sys
import re

def remove_line(file, pattern):
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(file, 'w', encoding='utf-8') as f:
        for line in lines:
            if pattern not in line:
                f.write(line)

remove_line('bootstrap/axiom0/src/resolve/resolve.c', 'DEBUG bind_node')
remove_line('bootstrap/axiom0/src/resolve/resolve.c', 'DEBUG lookup_name')
