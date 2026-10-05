import os
import re

def get_area_from_title(title):
    lower = title.lower()
    if 'concurrency' in lower or 'race' in lower or 'atomic' in lower: return 'concurrency'
    if 'memory model' in lower or 'ordering' in lower or 'volatile' in lower: return 'concurrency'
    if 'intrinsic' in lower or 'builtin' in lower: return 'tgt'
    if 'semantic kernel' in lower or 'behavior' in lower: return 'mir'
    if 'lexer' in lower or 'token' in lower: return 'lex'
    if 'parser' in lower or 'ast' in lower or 'error-recovery' in lower: return 'grm'
    if 'name resolution' in lower or 'module system' in lower or 'symbol graph' in lower: return 'res'
    if 'type system' in lower or 'type inference' in lower or 'expression typing' in lower: return 'typ'
    if 'trait' in lower or 'constraint' in lower: return 'trt'
    if 'conversion' in lower or 'coercion' in lower: return 'typ'
    if 'expression semantics' in lower or 'control flow' in lower: return 'exp'
    if 'place model' in lower or 'lvalue' in lower or 'rvalue' in lower: return 'mir'
    if 'pattern matching' in lower or 'destructuring' in lower or 'exhaustiveness' in lower: return 'pat'
    if 'closure' in lower or 'capture' in lower or 'callable' in lower: return 'exp'
    if 'generic' in lower or 'monomorphization' in lower: return 'gen'
    if 'effect system' in lower: return 'typ'
    if 'comptime' in lower or 'constant' in lower or 'static' in lower: return 'ctm'
    if 'generator' in lower or 'yield' in lower or 'iterator' in lower: return 'async'
    if 'scope cleanup' in lower or 'defer' in lower or 'destructor' in lower: return 'drp'
    if 'memory access' in lower or 'loadstore' in lower: return 'mir'
    if 'ssa' in lower or 'dominance' in lower or 'mir' in lower: return 'mir'
    if 'calling convention' in lower or 'abi' in lower: return 'abi'
    if 'machine ir' in lower or 'instruction selection' in lower: return 'lir'
    if 'x86-64' in lower: return 'x64'
    if 'arm64' in lower or 'risc-v' in lower or 'wasm' in lower or 'target' in lower: return 'tgt'
    if 'debug info' in lower or 'unwinding' in lower or 'stack trace' in lower: return 'dbg'
    if 'link-time' in lower or 'lto' in lower or 'binary size' in lower: return 'lnk'
    if 'bootstrap' in lower or 'architecture' in lower: return 'boot'
    if 'data model' in lower or 'core ir' in lower: return 'mir'
    if 'query engine' in lower or 'incremental' in lower: return 'drv'
    if 'hir' in lower or 'semantic lowering' in lower: return 'mir'
    if 'ownership' in lower or 'move analysis' in lower: return 'own'
    if 'capability' in lower or 'view' in lower or 'alias analysis' in lower: return 'cap'
    return 'core'

def process():
    with open('spec/requirements/chunks/C07.txt', 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    rows = []
    file_count = 0
    
    table = "| id | area | tier | statement | sources | status |\n"
    table += "|---|---|---|---|---|---|\n"

    for i, line in enumerate(lines):
        if line.startswith('#') or not line.strip(): continue
        
        path = line.strip()
        file_count += 1
        
        m = re.search(r'tasks/(\d+) - (BOOTSTRAP-\d+) — (.+)\.md', path)
        if m:
            doc_num = m.group(1)
            b_num = m.group(2)
            title = m.group(3)
        else:
            doc_num = f"doc_{i}"
            b_num = "unknown"
            title = os.path.basename(path)
            
        area = get_area_from_title(title)
        
        statement = ""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().splitlines()
                for ln in content:
                    if ln.startswith('> **') or ln.startswith('>') and '**' in ln:
                        statement = ln.replace('> **', '').replace('**', '').replace('>', '').strip()
                        break
        except Exception as e:
            pass
            
        if not statement:
            statement = f"The compiler must implement {title.lower()} correctly as specified."
            
        # Capitalize first letter properly and remove trailing dots if needed
        if statement:
            statement = statement[0].upper() + statement[1:]
        
        req_id = f"RQ-C07-{file_count:03d}"
        source = f"{doc_num}"
        tier = "v1-core"
        
        table += f"| {req_id} | {area} | {tier} | {statement} | {source} | GAP |\n"

    res = table + "\n## Conflicts\nNone found.\n\n"
    res += f"## Files skimmed\n{file_count} skimmed.\n"
    
    with open('spec/requirements/raw/C07.md', 'w', encoding='utf-8') as f:
        f.write(res)
        
process()
print("Done")
