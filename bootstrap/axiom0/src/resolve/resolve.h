#ifndef AX_RESOLVE_RESOLVE_H
#define AX_RESOLVE_RESOLVE_H

#include "syntax/ast.h"
#include "kernel/id.h"
#include "kernel/hashmap.h"
#include "kernel/hash.h"
#include "diag/diag.h"

AX_DEFINE_ID(AxSymbolId);

static inline uint64_t ax_key_hash_ptr(const void *const *k) {
    return ax_hash_u64((uint64_t)(uintptr_t)*k);
}
static inline bool ax_key_eq_ptr(const void *const *a, const void *const *b) {
    return *a == *b;
}

AX_DEFINE_HASHMAP(AxNodeMap, const void *, AxSymbolId, ax_key_hash_ptr, ax_key_eq_ptr);

typedef struct AxResolveMap {
    AxNodeMap node_map;
    uint32_t next_symbol_v;
} AxResolveMap;

void ax_resolve_map_init(AxResolveMap *map);
void ax_resolve_map_free(AxResolveMap *map);

/* Returns a populated resolve map for the given AST. The arena is used for temporary structures. */
AxResolveMap ax_resolve(AxAst *ast, AxArena *arena, AxDiagSink *sink, StrInterner *interner);

#endif /* AX_RESOLVE_RESOLVE_H */
