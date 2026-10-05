#ifndef AX_KERNEL_ID_H
#define AX_KERNEL_ID_H

/* Typed IDs and ID tables (INV-KERN-001; 0171 AKERNEL-24; 0153 ACKERNEL-20/23).
 *
 *     AX_DEFINE_ID(FileId)                       // typedef struct FileId { uint32_t v; } FileId;
 *     AX_DEFINE_ID_TABLE(FileTable, FileId, SourceFile)
 *
 * Every ID kind is its own one-member struct, so the C type checker rejects passing a FileId where
 * a ModuleId is expected. `v == 0` is the "none" ID; a real ID has v = table index + 1, so the
 * first entry of every table gets v = 1. IDs are handed out in insertion order and never reused or
 * renumbered, which makes them deterministic (they never encode a memory address, INV-KERN-002).
 *
 * Tables are read only through Table_get(table, id); a none or out-of-range ID is an internal
 * compiler error. A pointer from Table_get is invalidated by the next Table_push. */

#include "kernel/base.h"

#define AX_DEFINE_ID(Name)                                                                        \
    typedef struct Name {                                                                         \
        uint32_t v;                                                                               \
    } Name;                                                                                       \
    AX_MAYBE_UNUSED static inline Name Name##_none(void) {                                                        \
        Name id = {0};                                                                            \
        return id;                                                                                \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Name##_is_none(Name id) {                                                  \
        return id.v == 0;                                                                         \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Name##_is_some(Name id) {                                                  \
        return id.v != 0;                                                                         \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Name##_eq(Name a, Name b) {                                                \
        return a.v == b.v;                                                                        \
    }                                                                                             \
    /* 0-based table index -> ID */                                                               \
    AX_MAYBE_UNUSED static inline Name Name##_from_index(size_t index) {                                          \
        AX_ASSERT(index < (size_t)UINT32_MAX);                                                    \
        Name id = {(uint32_t)(index + 1)};                                                        \
        return id;                                                                                \
    }                                                                                             \
    /* ID -> 0-based table index; none is an ICE */                                               \
    AX_MAYBE_UNUSED static inline size_t Name##_index(Name id) {                                                  \
        AX_ASSERT(id.v != 0);                                                                     \
        return (size_t)id.v - 1;                                                                  \
    }                                                                                             \
    typedef int Name##_id_defined_ /* swallow the trailing semicolon */

#define AX_DEFINE_ID_TABLE(Table, Id, T)                                                          \
    typedef struct Table {                                                                        \
        T *items;                                                                                 \
        size_t len;                                                                               \
        size_t cap;                                                                               \
    } Table;                                                                                      \
    AX_MAYBE_UNUSED static inline void Table##_init(Table *t) {                                                   \
        t->items = NULL;                                                                          \
        t->len = 0;                                                                               \
        t->cap = 0;                                                                               \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Table##_free(Table *t) {                                                   \
        ax_xfree(t->items);                                                                       \
        Table##_init(t);                                                                          \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline Id Table##_push(Table *t, T value) {                                            \
        if (t->len == t->cap) {                                                                   \
            t->items = (T *)ax_grow_array(t->items, &t->cap, sizeof(T), t->len + 1);              \
        }                                                                                         \
        t->items[t->len] = value;                                                                 \
        return Id##_from_index(t->len++);                                                         \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline bool Table##_contains(const Table *t, Id id) {                                  \
        return id.v != 0 && (size_t)id.v <= t->len;                                               \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline T *Table##_get(const Table *t, Id id) {                                         \
        if (!Table##_contains(t, id)) {                                                           \
            AX_ICE("%s: invalid id %u (table has %llu entries)", #Table, (unsigned)id.v, (unsigned long long)t->len);  \
        }                                                                                         \
        return &t->items[id.v - 1];                                                               \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline size_t Table##_len(const Table *t) {                                            \
        return t->len;                                                                            \
    }                                                                                             \
    /* iteration in ID order: for (Id id = Table_first(t); Id_is_some(id); id = Table_after(t, id)) */ \
    AX_MAYBE_UNUSED static inline Id Table##_first(const Table *t) {                                              \
        return t->len == 0 ? Id##_none() : Id##_from_index(0);                                    \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline Id Table##_after(const Table *t, Id id) {                                       \
        return (size_t)id.v < t->len ? Id##_from_index(id.v) : Id##_none();                       \
    }                                                                                             \
    typedef int Table##_table_defined_ /* swallow the trailing semicolon */

#endif /* AX_KERNEL_ID_H */
