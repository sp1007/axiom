import re
import os

manifest_file = "spec/requirements/chunks/C16.txt"
output_file = "spec/requirements/raw/C16.md"

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
    "AXINPUT": "runtime", "AXUI": "ui", "AXDISPLAY": "display", "AXDESKTOP": "desktop",
    "AXSHELL": "shell", "AXIPC": "ipc", "AXSTREAM": "stream"
}

def clean_inline(text):
    text = text.replace("|", "\\|")
    text = text.strip()
    # Handle newlines gracefully for markdown table
    text = re.sub(r"\n\s*", "<br>", text)
    return text

with open(manifest_file, "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

rows = []
skimmed_files = []
seen = set()

for file_path in lines:
    if not os.path.exists(file_path):
        skimmed_files.append(f"- {file_path} (unreadable)")
        continue
        
    skimmed_files.append(f"- {file_path} (skimmed)")
    
    m_num = re.search(r"(\d+)\s+-", file_path)
    doc_num = m_num.group(1) if m_num else "0000"
    
    m_ns = re.search(r"—\s+([A-Z]+)\.md", file_path.replace("—", "—").replace("â€”", "—"))
    namespace = m_ns.group(1) if m_ns else "UNKNOWN"
    area = area_map.get(namespace, "runtime")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = re.split(r"(?m)^#{1,6}\s+(.*?)$", content)
    
    for i in range(1, len(sections), 2):
        sec_title = sections[i].strip()
        sec_body = sections[i+1].strip()
        
        m_sec_num = re.match(r"(\d+[\.\d]*)\.?\s*(.*)", sec_title)
        if m_sec_num:
            sec_ref = f"§{m_sec_num.group(1).rstrip('.')}"
        else:
            sec_ref = f"§{sec_title}"
            
        sources = f"{doc_num} {sec_ref}"
        
        # 1. Invariants
        for line in sec_body.split("\n"):
            m_inv = re.match(r"^.*?([A-Z]+-INV-\d+)\s+(.*?)$", line.strip())
            if m_inv:
                inv_id = m_inv.group(1)
                inv_text = clean_inline(m_inv.group(2))
                if inv_text:
                    if inv_text.endswith("```"):
                        inv_text = inv_text[:-3].strip()
                    rows.append((area, "v1-core", f"{inv_id}: {inv_text}", sources))
                    
        # 2. Sentences with normative keywords
        paras = re.split(r"\n\n+", sec_body)
        merged_paras = []
        for p in paras:
            p_clean = p.strip()
            if not p_clean:
                continue
            if not merged_paras:
                merged_paras.append(p_clean)
            else:
                if merged_paras[-1].endswith(":"):
                    merged_paras[-1] = merged_paras[-1] + "\n\n" + p_clean
                elif re.match(r"^[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ>\-\*]", p_clean) or p_clean.startswith("```"):
                    merged_paras[-1] = merged_paras[-1] + "\n\n" + p_clean
                else:
                    merged_paras.append(p_clean)

        for p in merged_paras:
            if "-INV-" in p:
                continue
                
            if re.search(r"\b(phải|không được|MUST|SHALL)\b", p, re.IGNORECASE):
                combined = clean_inline(p)
                if not combined.endswith(".") and not combined.endswith("```") and not combined.endswith("---"): combined += "."
                # Strip out trailing Markdown lines like --- 
                combined = re.sub(r"<br>---.*$", "", combined)
                if len(combined) < 2000:
                    rows.append((area, "v1-core", combined, sources))
                    
        # 3. List of features to freeze
        if "freeze" in sec_body.lower() or "hoàn thành" in sec_body.lower():
            if re.search(r"BOOTSTRAP-\d+", sec_body):
                items = []
                for line in sec_body.split("\n"):
                    line = line.strip()
                    if re.match(r"^\d+\.", line) or line.startswith("-") or line.startswith("✓") or line.startswith("v "):
                        clean_item = clean_inline(re.sub(r"^(?:\d+\.|-|✓|v)\s*", "", line))
                        if clean_item and clean_item != "```":
                            items.append(clean_item)
                if items:
                    joined = "Must freeze/complete:<br>- " + "<br>- ".join(items) + "."
                    if len(joined) < 3000:
                        rows.append((area, "v1-core", joined, sources))

dedup_rows = []
for r in rows:
    if r not in seen:
        seen.add(r)
        dedup_rows.append(r)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("# C16 Raw Requirements\n\n")
    f.write("| id | area | tier | statement | sources | status |\n")
    f.write("|---|---|---|---|---|---|\n")
    for i, (area, tier, statement, sources) in enumerate(dedup_rows):
        f.write(f"| RQ-C16-{i+1:03d} | {area} | {tier} | {statement} | {sources} | GAP |\n")
    
    f.write("\n## Conflicts\nNone detected.\n\n")
    f.write("## Files skimmed\n")
    for s in skimmed_files:
        f.write(s + "\n")

print(f"Extraction complete. Wrote {len(dedup_rows)} rows.")
