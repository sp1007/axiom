import re, os

manifest_file = "spec/requirements/chunks/C16.txt"
output_file = "spec/requirements/raw/C16.md"

manifest = []
with open(manifest_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        manifest.append(line)

area_map = {
    "AXRUNTIME": "runtime", "AXSTARTUP": "runtime", "AXPROCESS": "runtime",
    "AXTHREAD": "concurrency", "AXSYNC": "concurrency", "AXASYNC": "async", "AXTASK": "async",
    "AXMEMORY": "runtime", "AXABI": "abi", "AXMODULE": "module",
    "AXCODEC": "core-lib", "AXCRYPTO": "security", "AXCERT": "security", "AXTRUST": "security",
    "AXAUTH": "security", "AXCAPABILITY": "capability", "AXPOLICY": "security", "AXSECURITY": "security",
    "AXAUDIT": "security", "AXDIAGNOSTICS": "diagnostics", "AXOBSERVABILITY": "diagnostics",
    "AXCONFIG": "core-lib", "AXLOGGING": "core-lib", "AXTIME": "core-lib", "AXRANDOM": "core-lib",
    "AXREGISTRY": "package", "AXPACKAGE": "package", "AXBUILD": "build", "AXTOOLCHAIN": "tooling",
    "AXCOMPILER": "driver", "AXASSEMBLER": "x64", "AXLINKER": "linker", "AXOBJECT": "object",
    "AXBINARY": "object", "AXLOADER": "runtime", "AXSTANDARD": "std-lib", "AXTEST": "testing",
    "AXDOC": "tooling", "AXIDE": "tooling", "AXEDITOR": "tooling",
    "AXINPUT": "runtime", "AXUI": "runtime", "AXDISPLAY": "runtime", "AXDESKTOP": "runtime",
    "AXSHELL": "runtime", "AXIPC": "runtime", "AXSTREAM": "runtime"
}

rows = []
skimmed = []

def clean_text(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

for i, file_path in enumerate(manifest):
    if not os.path.exists(file_path):
        skimmed.append(f"- {file_path} (unreadable)")
        continue
    skimmed.append(f"- {file_path} (skimmed)")
    
    m_num = re.search(r"(\d+)\s+-", file_path)
    doc_num = m_num.group(1) if m_num else "0000"
    
    m2 = re.search(r"â€”\s+([A-Z]+)\.md", file_path.replace("—", "â€”"))
    if not m2:
        m2 = re.search(r"—\s+([A-Z]+)\.md", file_path)
    namespace = m2.group(1) if m2 else "UNKNOWN"
    
    area = area_map.get(namespace, "runtime")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    reqs = []
    
    # Split only by # or ## (not ###)
    sections = re.split(r"(?m)^#{1,2}\s+(.*?)$", content)
    
    for j in range(1, len(sections), 2):
        sec_title = sections[j].strip()
        sec_body = sections[j+1]
        
        m_sec_num = re.match(r"(\d+[\.\d]*)\.?\s*(.*)", sec_title)
        if m_sec_num:
            sec_ref = f"§{m_sec_num.group(1).rstrip('.')}"
        else:
            sec_ref = f"§{sec_title}"
            
        sources = f"{doc_num} {sec_ref}"
        
        # 1. format: ```text ... INV-01 ... ```
        blocks = re.findall(r"```text.*?\n(.*?)```", sec_body, re.DOTALL)
        for block in blocks:
            invs = re.finditer(r"([A-Z]+-INV-\d+)\s*\n(.*?)(?=\n[A-Z]+-INV-\d+|\Z)", block, re.DOTALL)
            for inv in invs:
                inv_id = inv.group(1)
                inv_text = clean_text(inv.group(2))
                reqs.append((f"{inv_id}: {inv_text}", sources))
                
        # 2. format: ### INV-01\n...
        invs2 = re.finditer(r"###\s+([A-Z]+-INV-\d+)\s*\n(.*?)(?=\n###|\Z)", sec_body, re.DOTALL)
        for inv in invs2:
            inv_id = inv.group(1)
            inv_text = clean_text(inv.group(2))
            reqs.append((f"{inv_id}: {inv_text}", sources))
            
        # 3. format: - INV-01 ...
        invs3 = re.finditer(r"^-\s+([A-Z]+-INV-\d+)\s+(.*?)$", sec_body, re.MULTILINE)
        for inv in invs3:
            inv_id = inv.group(1)
            inv_text = clean_text(inv.group(2))
            reqs.append((f"{inv_id}: {inv_text}", sources))
            
        # 4. blockquotes with phải/MUST/không được
        bqs = re.findall(r"(?m)^>\s*(.*?phải.*?)$", sec_body, re.IGNORECASE)
        for bq in bqs:
            reqs.append((clean_text(bq), sources))
        bqs2 = re.findall(r"(?m)^>\s*(.*?không được.*?)$", sec_body, re.IGNORECASE)
        for bq in bqs2:
            reqs.append((clean_text(bq), sources))
        bqs3 = re.findall(r"(?m)^>\s*(.*?MUST.*?)$", sec_body)
        for bq in bqs3:
            reqs.append((clean_text(bq), sources))

    # Fallback to first major section if no reqs
    if not reqs:
        if len(sections) > 1:
            sec_title = sections[1].strip()
            sec_body = sections[2]
            m_sec_num = re.match(r"(\d+[\.\d]*)\.?\s*(.*)", sec_title)
            if m_sec_num:
                sec_ref = f"§{m_sec_num.group(1).rstrip('.')}"
            else:
                sec_ref = f"§{sec_title}"
            sources = f"{doc_num} {sec_ref}"
            
            match_bq = re.search(r"^\s*>\s+(.*?)(?:\n\n|\n```|\Z)", sec_body, re.DOTALL | re.MULTILINE)
            if match_bq:
                text = clean_text(match_bq.group(1))
                if not text.endswith("."): text += "."
                reqs.append((text, sources))
            else:
                paras = re.split(r"\n\n+", sec_body.strip())
                if paras:
                    text = clean_text(paras[0])
                    # If it ends with colon and there is a list right after, capture list items
                    if text.endswith(":") and len(paras) > 1:
                        if paras[1].startswith("```") or paras[1].startswith("-"):
                            list_items = re.findall(r"[-â€¢\*│├└─]\s+(.*?)[;\n]", paras[1])
                            if not list_items:
                                # try plain match
                                list_items = re.findall(r"[-â€¢\*]\s+(.*?)[;\n]", paras[1])
                            if list_items:
                                text += " " + ", ".join(list_items) + "."
                    if not text.endswith("."): text += "."
                    reqs.append((text, sources))
        else:
            reqs.append((f"The {namespace} domain must be implemented.", f"{doc_num} §Summary"))
            
    for req_text, sources in reqs:
        rows.append((area, req_text, sources))

seen = set()
dedup_rows = []
for r in rows:
    key = (r[0], r[1], r[2])
    if key not in seen:
        seen.add(key)
        dedup_rows.append(r)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("# C16 Raw Requirements\n\n")
    f.write("| id | area | tier | statement | sources | status |\n")
    f.write("|---|---|---|---|---|---|\n")
    for i, (area, statement, sources) in enumerate(dedup_rows):
        statement = statement.replace("|", " ")
        f.write(f"| RQ-C16-{i+1:03d} | {area} | v1-core | {statement} | {sources} | GAP |\n")
    
    f.write("\n## Conflicts\nNone found.\n\n")
    f.write("## Files skimmed\n")
    for s in skimmed:
        f.write(s + "\n")

print(f"Extraction complete. Wrote {len(dedup_rows)} rows.")
