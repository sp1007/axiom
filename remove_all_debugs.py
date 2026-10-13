import os
import re

for root, _, files in os.walk('bootstrap/axiom0/src'):
    for file in files:
        if file.endswith('.c'):
            path = os.path.join(root, file)
            with open(path, 'rb') as f:
                text = f.read().decode('utf-8')
            
            # Use regex to strip lines that contain fprintf(stderr, "DEBUG ...
            new_text = re.sub(r'\(fprintf\(stderr, "DEBUG.*?\\n", __LINE__\),\s*', '', text)
            new_text = re.sub(r'fprintf\(stderr, "DEBUG.*?\\n".*?\);', '', new_text)
            
            if new_text != text:
                with open(path, 'wb') as f:
                    f.write(new_text.encode('utf-8'))
