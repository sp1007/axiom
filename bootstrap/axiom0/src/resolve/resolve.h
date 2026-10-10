#ifndef AX_RESOLVE_RESOLVE_H
#define AX_RESOLVE_RESOLVE_H

#include "syntax/ast.h"
#include "kernel/id.h"
#include "kernel/hashmap.h"
#include "kernel/hash.h"
#include "diag/diag.h"

AX_DEFINE_ID(AxSymbolId);

#define ax_resolve_hash_ptr(k) ax_hash_u64((uint64_t)(uintptr_t)*(k))
#define ax_resolve_eq_ptr(a, b) (*(a) == *(b))

typedef const void * AxNodePtr;
AX_DEFINE_HASHMAP(AxNodeMap, AxNodePtr, AxSymbolId, ax_resolve_hash_ptr, ax_resolve_eq_ptr);

typedef struct AxResolveMap {
    AxNodeMap node_map;
    AxNodeMap module_access_nodes;
    uint32_t next_symbol_v;
    uint32_t next_std_symbol_v;
    void *module_naming_ctx;
} AxResolveMap;

void ax_resolve_map_init(AxResolveMap *map);
void ax_resolve_map_free(AxResolveMap *map);

/* Returns a populated resolve map for the given AST. The arena is used for temporary structures. */
AxResolveMap ax_resolve(AxAst *ast, AxArena *arena, AxDiagSink *sink, StrInterner *interner);

/* Module-path naming hooks (T060, consumed by T054b mangling):
 * Returns the fully qualified module path (e.g. "std.core.prelude" or "math") for a symbol. */
StrView ax_resolve_symbol_module_path(const AxResolveMap *map, AxSymbolId sym);

/* Returns the fully qualified canonical name (e.g. "math.add" or "std.core.prelude.prelude_loaded"). */
StrView ax_resolve_symbol_canonical_name(const AxResolveMap *map, AxSymbolId sym);

#endif /* AX_RESOLVE_RESOLVE_H */
