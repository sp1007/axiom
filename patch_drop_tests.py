import os
import glob
import re

drop_tests = glob.glob('tests/run/drop/*.ax')
for file in drop_tests:
    with open(file, 'r') as f:
        content = f.read()
    
    content = re.sub(r'let x: i64 = (\d+);\s*print_int\(x\);\s*print\("\\n"\);', r'print("\1\\n");', content)
    
    with open(file, 'w') as f:
        f.write(content)
