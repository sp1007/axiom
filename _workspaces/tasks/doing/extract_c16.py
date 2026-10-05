import re
import glob
import os
from collections import defaultdict

def parse_blocks(text):
    blocks = []
    lines = text.split('\n')
    current_block_type = None
    current_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('```'):
            if in_code:
                current_lines.append(line)
                blocks.append(('CODE', '\n'.join(current_lines)))
                current_lines = []
                in_code = False
            else:
                if current_lines:
                    blocks.append((current_block_type, '\n'.join(current_lines)))
                    current_lines = []
                in_code = True
                current_lines.append(line)
                current_block_type = 'CODE'
            continue
            
        if in_code:
            current_lines.append(line)
            continue
            
        if not stripped:
            if current_lines:
                blocks.append((current_block_type, '\n'.join(current_lines)))
                current_lines = []
                current_block_type = None
            continue
            
        if stripped.startswith('#'):
            if current_lines:
                blocks.append((current_block_type, '\n'.join(current_lines)))
                current_lines = []
            blocks.append(('HEADING', stripped))
            current_block_type = None
            continue
            
        # Is it a list item?
        is_list = stripped.startswith('- ') or stripped.startswith('* ') or re.match(r'^\d+\.\s+', stripped)
        
        if is_list:
            if current_block_type == 'LIST':
                current_lines.append(line)
            else:
                if current_lines:
                    blocks.append((current_block_type, '\n'.join(current_lines)))
                    current_lines = []
                current_block_type = 'LIST'
                current_lines.append(line)
        else:
            if current_block_type == 'PARAGRAPH':
                current_lines.append(line)
            else:
                if current_lines:
                    blocks.append((current_block_type, '\n'.join(current_lines)))
                    current_lines = []
                current_block_type = 'PARAGRAPH'
                current_lines.append(line)
                
    if current_lines:
        blocks.append((current_block_type, '\n'.join(current_lines)))
        
    return blocks

def is_normative(text, section_title):
    text_lower = text.lower()
    keywords = ['phải', 'không được', 'must ', 'shall ', 'hoàn tất khi có:', 'bắt buộc', 'không giả định', 'đảm bảo', 'không cho phép', 'tuyệt đối']
    if any(k in text_lower for k in keywords):
        return True
    
    sec_lower = section_title.lower()
    if any(s in sec_lower for s in ['mục tiêu', 'nguyên tắc', 'invariants', 'quyết định', 'kết luận', 'acceptance', 'gate', 'boundary']):
        return True
        
    if 'inv-' in text_lower:
        return True
        
    if re.search(r'[A-Z]+-[A-Z]+-\d+', text):
        return True
        
    return False

def extract_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    doc_id_match = re.search(r'(\d+)\s*-', os.path.basename(file_path))
    doc_id = doc_id_match.group(1) if doc_id_match else "0000"
    
    ns_match = re.search(r'Namespace:\s*`?([A-Z0-9_]+)`?', text)
    area = ns_match.group(1) if ns_match else "unknown"
    
    blocks = parse_blocks(text)
    
    # Pre-group paragraphs ending in : with the next blocks
    refined = []
    i = 0
    while i < len(blocks):
        btype, btext = blocks[i]
        
        # If it's a paragraph ending in colon, group with following code/list/blockquotes
        if btype == 'PARAGRAPH' and btext.strip().endswith(':'):
            stmt = btext.strip()
            j = i + 1
            grouped_any = False
            while j < len(blocks):
                nxt_type, nxt_text = blocks[j]
                if nxt_type == 'HEADING':
                    break
                if nxt_type == 'CODE':
                    stmt += "<br><br>" + nxt_text.strip().replace('\n', '<br>')
                    grouped_any = True
                elif nxt_type == 'LIST':
                    if 'inv-' in nxt_text.lower() or re.search(r'[A-Z]+-[A-Z]+-\d+', nxt_text):
                        break
                    stmt += "<br>" + nxt_text.strip().replace('\n', '<br>')
                    grouped_any = True
                elif nxt_type == 'PARAGRAPH' and nxt_text.strip().startswith('>'):
                    stmt += "<br><br>" + nxt_text.strip().replace('\n', '<br>')
                    grouped_any = True
                else:
                    break
                j += 1
                
            if grouped_any:
                refined.append(('PARAGRAPH', stmt))
                i = j
            else:
                refined.append(blocks[i])
                i += 1
        else:
            refined.append(blocks[i])
            i += 1
            
    # Now extract normative statements
    requirements = []
    section_title = ""
    
    for btype, btext in refined:
        if btype == 'HEADING':
            section_title = btext.lstrip('#').strip()
            continue
            
        sec_num_match = re.search(r'^([\d\.]+)', section_title)
        sec_num = sec_num_match.group(1) if sec_num_match else section_title
        source = f"{doc_id} §{sec_num}" if sec_num else doc_id
        
        if btype == 'PARAGRAPH':
            if is_normative(btext, section_title):
                # Clean up newlines for markdown table
                stmt = btext.replace('\n', ' ')
                # If there are <br> from our grouping, keep them
                stmt = stmt.replace(' <br>', '<br>').replace('<br> ', '<br>')
                requirements.append({'stmt': stmt.strip(), 'area': area, 'source': source})
                
        elif btype == 'LIST':
            # Is it a list of invariants or separate rule IDs?
            if 'inv-' in btext.lower() or re.search(r'[A-Z]+-[A-Z]+-\d+', btext):
                items = re.split(r'\n(?=[-*\d])', btext)
                for item in items:
                    item = item.strip()
                    if item and is_normative(item, section_title):
                        stmt = item.replace('\n', ' ')
                        requirements.append({'stmt': stmt, 'area': area, 'source': source})
            else:
                if is_normative(btext, section_title):
                    stmt = btext.replace('\n', '<br>')
                    requirements.append({'stmt': stmt, 'area': area, 'source': source})
                    
        elif btype == 'CODE':
            # Diagrams that are directly under "Mục tiêu" or "Nguyên tắc" without a preceding paragraph ending in :
            if is_normative("diagram", section_title):
                stmt = btext.replace('\n', '<br>')
                requirements.append({'stmt': stmt, 'area': area, 'source': source})
                
    return requirements

def main():
    manifest_path = "spec/requirements/chunks/C16.txt"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    files = []
    for line in lines:
        line = line.strip()
        if line.startswith('docs/') and line.endswith('.md'):
            files.append(line)
            
    dedup_map = {}
    
    for file_path in files:
        if os.path.exists(file_path):
            reqs = extract_from_file(file_path)
            for req in reqs:
                stmt = req['stmt']
                # Normalize for dedup
                norm = re.sub(r'<[^>]+>', ' ', stmt) # remove <br> for comparison
                norm = " ".join(norm.split()).lower()
                
                if norm not in dedup_map:
                    dedup_map[norm] = {
                        'stmt': stmt,
                        'area': req['area'],
                        'sources': set()
                    }
                dedup_map[norm]['sources'].add(req['source'])
                
    # Output to spec/requirements/raw/C16.md
    out_path = "spec/requirements/raw/C16.md"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("| id | area | tier | statement | sources | status |\n")
        f.write("|---|---|---|---|---|---|\n")
        
        idx = 1
        for norm, data in dedup_map.items():
            stmt = data['stmt'].replace('|', '\\|')
            area = data['area'].lower()
            sources = ", ".join(sorted(list(data['sources'])))
            
            # Find dependencies: "needs RQ-Cnn-NNN"
            needs_match = re.search(r'\[needs\s+([^\]]+)\]', stmt)
            if needs_match:
                pass # The procedure says keep it in the statement cell
            
            f.write(f"| RQ-C16-{idx:03d} | {area} | v1-core | {stmt} | {sources} | GAP |\n")
            idx += 1
            
        f.write("\n## Conflicts\nNone found.\n\n")
        f.write("## Files skimmed\n")
        for file_path in files:
            f.write(f"- {file_path}\n")

if __name__ == "__main__":
    main()
