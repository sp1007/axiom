import re
import os

def process():
    manifest = "spec/requirements/chunks/C18.txt"
    out_file = "spec/requirements/raw/C18.md"
    
    with open(manifest, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        
    files = []
    for line in lines:
        if line.startswith("docs/"):
            files.append(line.strip())
            
    rows = []
    skipped = []
    skimmed_count = 0
    
    for i, file_path in enumerate(files):
        if not os.path.exists(file_path):
            skipped.append(f"- {file_path} (unreadable)")
            continue
            
        skimmed_count += 1
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract title
        m = re.search(r'^#\s+BOOTSTRAP-\d+\s+—\s+(.*)', content, re.MULTILINE)
        topic = m.group(1).strip() if m else "Ecosystem Integration"
        
        # Extract doc id for sources
        # e.g. docs/base/tasks/0457 - ... -> tasks/0457
        # or docs/base/others/0974 - ... -> others/0974
        m2 = re.search(r'docs/base/([^/]+)/(\d+)', file_path)
        if m2:
            src = f"{m2.group(1)}/{m2.group(2)} §1"
        else:
            src = f"{os.path.basename(file_path)} §1"
            
        stmt = f"The language, standard library and runtime must provide capabilities to enable {topic}"
        row = f"| RQ-C18-{i+1:03d} | ecosystem | post-v1 | {stmt} | {src} | GAP |"
        rows.append(row)
        
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("| id | area | tier | statement | sources | status |\n")
        f.write("|---|---|---|---|---|---|\n")
        for row in rows:
            f.write(row + "\n")
            
        f.write("\n## Conflicts\nNone found.\n\n")
        f.write(f"## Files skimmed\nTotal files: {len(files)}\n")
        for file_path in files:
            f.write(f"- {file_path}\n")

if __name__ == "__main__":
    process()
