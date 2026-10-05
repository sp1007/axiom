#ifndef AX_KERNEL_INTERNER_H
#define AX_KERNEL_INTERNER_H

/* String interner: byte string -> StrId (INV-KERN-004; 0153 §9 AINTERN-20..23).
 *
 * Equal byte strings interned in one interner get the same StrId; different strings get different
 * ids. Ids are handed out densely in first-interning order starting at v = 1 (StrId v = 0 is none),
 * so they depend only on the sequence of intern calls, never on hashes or addresses. A StrId is an
 * identity of spelling only, not a SymbolId (0153 §10). The bytes are owned by the interner's arena
 * and stay valid (and NUL-terminated) until ax_interner_free. */

#include "kernel/arena.h"
#include "kernel/hashmap.h"
#include "kernel/id.h"
#include "kernel/str.h"

AX_DEFINE_ID(StrId);

static inline uint64_t ax_key_hash_sv(const StrView *k) {
    return ax_sv_hash(*k);
}
static inline bool ax_key_eq_sv(const StrView *a, const StrView *b) {
    return ax_sv_eq(*a, *b);
}

AX_DEFINE_HASHMAP(AxStrIdMap, StrView, StrId, ax_key_hash_sv, ax_key_eq_sv);

typedef struct StrInterner {
    AxArena bytes;    /* interned spellings */
    StrView *strings; /* index = StrId.v - 1 */
    size_t len;
    size_t cap;
    AxStrIdMap map;   /* spelling -> id; keys point into `bytes` */
} StrInterner;

void ax_interner_init(StrInterner *in);
void ax_interner_free(StrInterner *in);
StrId ax_intern(StrInterner *in, StrView s);
StrId ax_intern_cstr(StrInterner *in, const char *s);
/* Id of an already interned string, or none. Never adds. */
StrId ax_interner_lookup(const StrInterner *in, StrView s);
/* Spelling of an id; none or an unknown id is an ICE. */
StrView ax_interner_get(const StrInterner *in, StrId id);
size_t ax_interner_len(const StrInterner *in);

#endif /* AX_KERNEL_INTERNER_H */
