#include "kernel/arena.h"

#include <string.h>

struct AxArenaChunk {
    AxArenaChunk *next;
    size_t cap;  /* payload bytes */
    size_t used; /* bytes of payload consumed (offset of the next free byte) */
    max_align_t payload[];
};

void ax_arena_init(AxArena *a, size_t chunk_size) {
    a->head = NULL;
    a->current = NULL;
    a->chunk_size = chunk_size == 0 ? AX_ARENA_DEFAULT_CHUNK : chunk_size;
    a->bytes_requested = 0;
    a->chunk_count = 0;
}

void ax_arena_destroy(AxArena *a) {
    AxArenaChunk *c = a->head;
    while (c != NULL) {
        AxArenaChunk *next = c->next;
        ax_xfree(c);
        c = next;
    }
    ax_arena_init(a, a->chunk_size);
}

void ax_arena_reset(AxArena *a) {
    if (a->head == NULL) {
        a->bytes_requested = 0;
        return;
    }
    AxArenaChunk *c = a->head->next;
    while (c != NULL) {
        AxArenaChunk *next = c->next;
        ax_xfree(c);
        c = next;
    }
    a->head->next = NULL;
    a->head->used = 0;
    a->current = a->head;
    a->chunk_count = 1;
    a->bytes_requested = 0;
}

/* Offset in `c` where an object of `align` can start, at or after c->used. The address arithmetic
 * only computes padding; it never influences program output (INV-KERN-002). */
static size_t chunk_aligned_offset(const AxArenaChunk *c, size_t align) {
    uintptr_t base = (uintptr_t)(const void *)c->payload;
    uintptr_t at = base + c->used;
    uintptr_t aligned = (at + (uintptr_t)(align - 1)) & ~(uintptr_t)(align - 1);
    return (size_t)(aligned - base);
}

static AxArenaChunk *chunk_new(size_t payload) {
    size_t bytes = ax_add_size(sizeof(AxArenaChunk), payload);
    AxArenaChunk *c = ax_xmalloc(bytes);
    c->next = NULL;
    c->cap = payload;
    c->used = 0;
    return c;
}

void *ax_arena_alloc(AxArena *a, size_t size, size_t align) {
    AX_ASSERT(align != 0 && (align & (align - 1)) == 0 && align <= AX_ARENA_MAX_ALIGN);
    a->bytes_requested = ax_add_size(a->bytes_requested, size);
    AxArenaChunk *c = a->current;
    if (c != NULL) {
        size_t off = chunk_aligned_offset(c, align);
        if (off <= c->cap && size <= c->cap - off) {
            c->used = off + size;
            unsigned char *p = (unsigned char *)c->payload + off;
            memset(p, 0, size);
            return p;
        }
    }
    /* New chunk: large enough for this request even in the worst alignment case. */
    size_t need = ax_add_size(size, align - 1);
    size_t payload = need > a->chunk_size ? need : a->chunk_size;
    AxArenaChunk *n = chunk_new(payload);
    if (c == NULL) {
        a->head = n;
    } else {
        c->next = n;
    }
    a->current = n;
    ++a->chunk_count;
    size_t off = chunk_aligned_offset(n, align);
    AX_ASSERT(off <= n->cap && size <= n->cap - off);
    n->used = off + size;
    unsigned char *p = (unsigned char *)n->payload + off;
    memset(p, 0, size);
    return p;
}

void *ax_arena_alloc_array(AxArena *a, size_t count, size_t size, size_t align) {
    return ax_arena_alloc(a, ax_mul_size(count, size), align);
}

void *ax_arena_dup(AxArena *a, const void *src, size_t size) {
    void *p = ax_arena_alloc(a, size, 1);
    if (size != 0) {
        memcpy(p, src, size);
    }
    return p;
}

size_t ax_arena_bytes_requested(const AxArena *a) {
    return a->bytes_requested;
}

size_t ax_arena_chunk_count(const AxArena *a) {
    return a->chunk_count;
}
