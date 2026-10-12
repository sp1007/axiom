import sys

file = 'bootstrap/axiom0/src/driver/pipeline.c'
with open(file, 'r') as f:
    content = f.read()

s1 = '''static AxArena g_mir_arena;
static AxMirMap g_mir_map;
static bool g_mir_initialized = false;'''
r1 = '''static AxArena g_mir_arena;
static AxMirMap g_mir_map;
static bool g_mir_initialized = false;

AxMirBody* ax_pipeline_get_mir(const AxHirItem *it) {
    if (!g_mir_initialized) return NULL;
    AxMirBody **pb = AxMirMap_get(&g_mir_map, (AxHirItem*)it);
    return pb ? *pb : NULL;
}
'''

content = content.replace(s1, r1)

with open(file, 'w') as f:
    f.write(content)
