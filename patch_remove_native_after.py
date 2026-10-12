import glob
import re
for file in glob.glob('tests/run/drop/*.ax'):
    with open(file, 'r') as f:
        content = f.read()
    if '// native-after: T051\n' in content:
        content = content.replace('// native-after: T051\n', '')
        with open(file, 'w') as f:
            f.write(content)
