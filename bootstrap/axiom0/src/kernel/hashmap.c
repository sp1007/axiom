#include "kernel/hashmap.h"

#include <string.h>

#define AX_MAP_TOMBSTONE UINT32_MAX
/* Entry indexes are uint32_t and AX_MAP_NONE/AX_MAP_TOMBSTONE are reserved. */
#define AX_MAP_MAX_ENTRIES (UINT32_MAX - 2u)

void ax_rawmap_init(AxRawMap *m, size_t entry_size) {
    AX_ASSERT(entry_size > 0);
    memset(m, 0, sizeof *m);
    m->entry_size = entry_size;
}

void ax_rawmap_free(AxRawMap *m) {
    size_t entry_size = m->entry_size;
    ax_xfree(m->entries);
    ax_xfree(m->hashes);
    ax_xfree(m->alive);
    ax_xfree(m->index);
    ax_rawmap_init(m, entry_size);
}

void ax_rawmap_clear(AxRawMap *m) {
    m->len = 0;
    m->live = 0;
    m->index_used = 0;
    if (m->index != NULL) {
        memset(m->index, 0, (size_t)m->index_cap * sizeof(uint32_t));
    }
}

static void index_put(uint32_t *index, uint32_t cap, uint64_t hash, uint32_t entry) {
    uint32_t mask = cap - 1;
    uint32_t slot = (uint32_t)hash & mask;
    while (index[slot] != 0 && index[slot] != AX_MAP_TOMBSTONE) {
        slot = (slot + 1) & mask;
    }
    index[slot] = entry + 1;
}

/* Rebuild the index for the live entries with a capacity that keeps the load at most 1/2 after
 * one more insertion. Also drops every tombstone. */
static void index_rebuild(AxRawMap *m) {
    uint32_t cap = 8;
    while ((size_t)(m->live + 1) * 2 > cap) {
        AX_ASSERT(cap <= UINT32_MAX / 2);
        cap *= 2;
    }
    ax_xfree(m->index);
    m->index = ax_xcalloc(cap, sizeof(uint32_t));
    m->index_cap = cap;
    m->index_used = 0;
    for (uint32_t i = 0; i < m->len; ++i) {
        if (m->alive[i]) {
            index_put(m->index, cap, m->hashes[i], i);
            ++m->index_used;
        }
    }
}

/* Remove dead entries, keeping the relative order of the live ones, then rebuild the index. */
static void compact(AxRawMap *m) {
    uint32_t w = 0;
    for (uint32_t r = 0; r < m->len; ++r) {
        if (!m->alive[r]) {
            continue;
        }
        if (w != r) {
            memcpy(m->entries + (size_t)w * m->entry_size, m->entries + (size_t)r * m->entry_size,
                   m->entry_size);
            m->hashes[w] = m->hashes[r];
            m->alive[w] = 1;
        }
        ++w;
    }
    m->len = w;
    AX_ASSERT(w == m->live);
    index_rebuild(m);
}

uint32_t ax_rawmap_find(const AxRawMap *m, uint64_t hash, const void *key, AxKeyEqFn eq) {
    if (m->index_cap == 0 || m->live == 0) {
        return AX_MAP_NONE;
    }
    uint32_t mask = m->index_cap - 1;
    uint32_t slot = (uint32_t)hash & mask;
    for (;;) {
        uint32_t s = m->index[slot];
        if (s == 0) {
            return AX_MAP_NONE;
        }
        if (s != AX_MAP_TOMBSTONE) {
            uint32_t i = s - 1;
            if (m->hashes[i] == hash && eq(m->entries + (size_t)i * m->entry_size, key)) {
                return i;
            }
        }
        slot = (slot + 1) & mask;
    }
}

void *ax_rawmap_insert(AxRawMap *m, uint64_t hash, const void *key, AxKeyEqFn eq, bool *is_new) {
    uint32_t found = ax_rawmap_find(m, hash, key, eq);
    if (found != AX_MAP_NONE) {
        *is_new = false;
        return m->entries + (size_t)found * m->entry_size;
    }
    *is_new = true;
    /* Many removed entries: squeeze them out before growing (order of live entries is kept). */
    uint32_t dead = m->len - m->live;
    if (dead >= 8 && dead * 2 >= m->len) {
        compact(m);
    }
    if (m->len >= AX_MAP_MAX_ENTRIES) {
        AX_ICE("hash map overflow (%u entries)", (unsigned)m->len);
    }
    if (m->len == m->entries_cap) {
        size_t cap = m->entries_cap;
        m->entries = ax_grow_array(m->entries, &cap, m->entry_size, (size_t)m->len + 1);
        size_t cap2 = m->entries_cap;
        m->hashes = ax_grow_array(m->hashes, &cap2, sizeof(uint64_t), cap);
        size_t cap3 = m->entries_cap;
        m->alive = ax_grow_array(m->alive, &cap3, 1, cap);
        m->entries_cap = cap;
    }
    if (m->index_cap == 0 || (size_t)(m->index_used + 1) * 4 > (size_t)m->index_cap * 3) {
        index_rebuild(m);
    }
    uint32_t i = m->len++;
    ++m->live;
    unsigned char *e = m->entries + (size_t)i * m->entry_size;
    memset(e, 0, m->entry_size);
    m->hashes[i] = hash;
    m->alive[i] = 1;
    /* index_put may reuse a tombstone; count only a slot that was empty */
    uint32_t mask = m->index_cap - 1;
    uint32_t slot = (uint32_t)hash & mask;
    while (m->index[slot] != 0 && m->index[slot] != AX_MAP_TOMBSTONE) {
        slot = (slot + 1) & mask;
    }
    if (m->index[slot] == 0) {
        ++m->index_used;
    }
    m->index[slot] = i + 1;
    return e;
}

bool ax_rawmap_remove(AxRawMap *m, uint64_t hash, const void *key, AxKeyEqFn eq, void *out_entry) {
    if (m->index_cap == 0 || m->live == 0) {
        return false;
    }
    uint32_t mask = m->index_cap - 1;
    uint32_t slot = (uint32_t)hash & mask;
    for (;;) {
        uint32_t s = m->index[slot];
        if (s == 0) {
            return false;
        }
        if (s != AX_MAP_TOMBSTONE) {
            uint32_t i = s - 1;
            unsigned char *e = m->entries + (size_t)i * m->entry_size;
            if (m->hashes[i] == hash && eq(e, key)) {
                if (out_entry != NULL) {
                    memcpy(out_entry, e, m->entry_size);
                }
                m->index[slot] = AX_MAP_TOMBSTONE; /* still counted in index_used */
                m->alive[i] = 0;
                --m->live;
                return true;
            }
        }
        slot = (slot + 1) & mask;
    }
}

bool ax_rawmap_next(const AxRawMap *m, uint32_t *cursor, void **out_entry) {
    while (*cursor < m->len) {
        uint32_t i = (*cursor)++;
        if (m->alive[i]) {
            *out_entry = m->entries + (size_t)i * m->entry_size;
            return true;
        }
    }
    return false;
}
