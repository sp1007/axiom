import re

with open('tests/run/method/inherent_methods.ax', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('print(\"\\n\");', 'print(\"\\\\n\");')
# wait, actually the python string parsing ruined it. Let me just rewrite the whole test using write file tool!

