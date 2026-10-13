import os
import glob

for root, _, files in os.walk('.'):
    for f in files:
        if 'T056' in f:
            print(os.path.join(root, f))
