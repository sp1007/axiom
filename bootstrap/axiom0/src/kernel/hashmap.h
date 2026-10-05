#ifndef AX_KERNEL_HASHMAP_H
#define AX_KERNEL_HASHMAP_H

/* Insertion-ordered hash map (INV-KERN-007, ADR-0004 §4; contract in kernel/README.md).
 *
 *     static inline uint64_t u32_hash(const uint32_t *k) { return ax_hash_u32(*k); }
 *     static inline bool u32_eq(const uint32_t *a, const uint32_t *b) { return *a == *b; }
 *     AX_DEFINE_HASHMAP(U32Map, uint32_t, int, u32_hash, u32_eq)
 *
 *     U32Map m; U32Map_init(&m);
 *     U32Map_insert(&m, 7, 70);                 // true: new key
 *     int *v = U32Map_get(&m, 7);              // NULL when absent
 *     uint32_t cur = 0; U32MapEntry *e;
 *     while (U32Map_next(&m, &cur, &e)) { ... e->key, e->value ... }   // insertion order
 *     U32Map_free(&m);
 *
 * Layout ("index map"): entries live in a dense array in insertion order; an open-addressing index
 * (power-of-two table, linear probing, slots hold entry index + 1) finds them by hash.
 *
 * Iteration contract (observable, std HashMap T073 must match it):
 *   - iteration visits the live entries in the order their keys were first inserted;
 *   - inserting an existing key replaces the value and keeps the key's position;
 *   - removing a key deletes it from the order; inserting it again appends it at the end;
 *   - the order never depends on hash values, table capacity, pointer values or allocation history.
 * Removing entries while iterating with Name_next is allowed (the cursor stays valid); inserting
 * while iterating is not. Pointers returned by Name_get / Name_next are invalidated by insert. */

#include "kernel/base.h"
#include "kernel/hash.h"

/* Equality on raw key pointers (the key is the first member of an entry). */
typedef bool (*AxKeyEqFn)(const void *entry_key, const void *probe_key);

#define AX_MAP_NONE UINT32_MAX

typedef struct AxRawMap {
    unsigned char *entries; /* entry_size bytes each, insertion order, may contain dead entries */
    uint64_t *hashes;       /* hash of each entry's key */
    unsigned char *alive;   /* 1 = live, 0 = removed */
    size_t entry_size;
    uint32_t len;           /* entries used (live + dead) */
    uint32_t live;          /* live entries */
    size_t entries_cap;
    uint32_t *index;        /* 0 empty, AX_MAP_TOMBSTONE removed, else entry index + 1 */
    uint32_t index_cap;     /* 0 or a power of two */
    uint32_t index_used;    /* non-empty index slots (live + tombstones) */
} AxRawMap;

void ax_rawmap_init(AxRawMap *m, size_t entry_size);
void ax_rawmap_free(AxRawMap *m);
void ax_rawmap_clear(AxRawMap *m);
/* Entry index of the key, or AX_MAP_NONE. */
uint32_t ax_rawmap_find(const AxRawMap *m, uint64_t hash, const void *key, AxKeyEqFn eq);
/* Find or append the key. Returns the entry (zeroed when new; the caller writes key and value);
 * *is_new tells which. */
void *ax_rawmap_insert(AxRawMap *m, uint64_t hash, const void *key, AxKeyEqFn eq, bool *is_new);
/* Remove the key; copies the removed entry to out_entry (may be NULL). Returns false if absent. */
bool ax_rawmap_remove(AxRawMap *m, uint64_t hash, const void *key, AxKeyEqFn eq, void *out_entry);
/* Next live entry at or after *cursor (start with 0); advances the cursor. */
bool ax_rawmap_next(const AxRawMap *m, uint32_t *cursor, void **out_entry);
AX_MAYBE_UNUSED static inline void *ax_rawmap_entry(const AxRawMap *m, uint32_t i) {
    AX_ASSERT(i < m->len);
    return m->entries + (size_t)i * m->entry_size;
}

#define AX_DEFINE_HASHMAP(Name, K, V, HASH_FN, EQ_FN)                                             \
    typedef struct Name##Entry {                                                                  \
        K key;                                                                                    \
        V value;                                                                                  \
    } Name##Entry;                                                                                \
    typedef struct Name {                                                                         \
        AxRawMap raw;                                                                             \
    } Name;                                                                                       \
    AX_MAYBE_UNUSED static inline bool Name##_raw_eq_(const void *a, const void *b) {                             \
        return EQ_FN((const K *)a, (const K *)b);                                                 \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_init(Name *m) {                                                     \
        ax_rawmap_init(&m->raw, sizeof(Name##Entry));                                             \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_free(Name *m) {                                                     \
        ax_rawmap_free(&m->raw);                                                                  \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_clear(Name *m) {                                                    \
        ax_rawmap_clear(&m->raw);                                                                 \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline size_t Name##_len(const Name *m) {                                              \
        return m->raw.live;                                                                       \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline V *Name##_get(const Name *m, K key) {                                           \
        uint32_t i = ax_rawmap_find(&m->raw, HASH_FN(&key), &key, Name##_raw_eq_);                \
        return i == AX_MAP_NONE ? NULL : &((Name##Entry *)ax_rawmap_entry(&m->raw, i))->value;    \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Name##_contains(const Name *m, K key) {                                    \
        return ax_rawmap_find(&m->raw, HASH_FN(&key), &key, Name##_raw_eq_) != AX_MAP_NONE;       \
    }                                                                                             \
    /* true when the key was new; an existing key keeps its position and gets the new value */    \
    AX_MAYBE_UNUSED static inline bool Name##_insert(Name *m, K key, V value) {                                   \
        bool is_new;                                                                              \
        Name##Entry *e =                                                                          \
            (Name##Entry *)ax_rawmap_insert(&m->raw, HASH_FN(&key), &key, Name##_raw_eq_, &is_new); \
        e->key = key;                                                                             \
        e->value = value;                                                                         \
        return is_new;                                                                            \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Name##_remove(Name *m, K key, V *out_value) {                              \
        Name##Entry old;                                                                          \
        if (!ax_rawmap_remove(&m->raw, HASH_FN(&key), &key, Name##_raw_eq_, &old)) {              \
            return false;                                                                         \
        }                                                                                         \
        if (out_value != NULL) {                                                                  \
            *out_value = old.value;                                                               \
        }                                                                                         \
        return true;                                                                              \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Name##_next(const Name *m, uint32_t *cursor, Name##Entry **out) {          \
        void *e;                                                                                  \
        if (!ax_rawmap_next(&m->raw, cursor, &e)) {                                               \
            return false;                                                                         \
        }                                                                                         \
        *out = (Name##Entry *)e;                                                                  \
        return true;                                                                              \
    }                                                                                             \
    typedef int Name##_map_defined_ /* swallow the trailing semicolon */

/* Ready-made key helpers for the common key kinds. */
AX_MAYBE_UNUSED static inline uint64_t ax_key_hash_u32(const uint32_t *k) {
    return ax_hash_u32(*k);
}
AX_MAYBE_UNUSED static inline bool ax_key_eq_u32(const uint32_t *a, const uint32_t *b) {
    return *a == *b;
}
AX_MAYBE_UNUSED static inline uint64_t ax_key_hash_u64(const uint64_t *k) {
    return ax_hash_u64(*k);
}
AX_MAYBE_UNUSED static inline bool ax_key_eq_u64(const uint64_t *a, const uint64_t *b) {
    return *a == *b;
}

#endif /* AX_KERNEL_HASHMAP_H */
