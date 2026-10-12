import re

def fix(path):
    with open(path, 'r') as f:
        code = f.read()
    code = code.replace('self.x', '(*self).x').replace('self.y', '(*self).y')
    with open(path, 'w') as f:
        f.write(code)

fix('tests/ui/method/inherent_methods_err.ax')
fix('tests/run/method/inherent_methods.ax')
