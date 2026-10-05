#ifndef AX_KERNEL_ARENA_H
#define AX_KERNEL_ARENA_H

/* Arena: aligned bump allocator over a list of heap chunks (INV-KERN-003; tasks/0260 ABOOT-49..53).
 *
 * Phase data (AST, HIR, MIR of one function, ...) is allocated here and released as a whole at the
 * phase boundary with ax_arena_reset (keep the first chunk for reuse) or ax_arena_destroy (free
 * everything). There is no per-object free. Memory returned by the arena is zeroed, so the content
 * of a fresh object never depends on what the allocator handed out before (determinism).
 *
 * An arena address is storage only, never identity: phases refer to their objects by typed IDs
 * (0153 §13). Allocation never fails (out of memory is an ICE). */

#include "kernel/base.h"

typedef struct AxArenaChunk AxArenaChunk;

typedef struct AxArena {
    AxArenaChunk *head;     /* first chunk (kept by reset) */
    AxArenaChunk *current;  /* chunk being bumped; newest */
    size_t chunk_size;      /* default payload size of a new chunk */
    size_t bytes_requested; /* sum of sizes requested since init/reset (statistics, tests) */
    size_t chunk_count;
} AxArena;

#define AX_ARENA_DEFAULT_CHUNK ((size_t)64 * 1024)
/* Largest supported alignment (a power of two). */
#define AX_ARENA_MAX_ALIGN ((size_t)4096)

/* chunk_size 0 selects AX_ARENA_DEFAULT_CHUNK. No memory is allocated until the first alloc. */
void ax_arena_init(AxArena *a, size_t chunk_size);
/* Free every chunk; the arena is empty and may be reused (as after init with the same chunk size). */
void ax_arena_destroy(AxArena *a);
/* Drop all objects; keep the first chunk's memory for reuse, free the others. */
void ax_arena_reset(AxArena *a);

/* `size` zeroed bytes aligned to `align` (power of two, 1..AX_ARENA_MAX_ALIGN). A request larger
 * than the chunk size gets a dedicated chunk. size 0 returns a valid aligned pointer. */
void *ax_arena_alloc(AxArena *a, size_t size, size_t align);
/* count * size bytes (overflow checked). */
void *ax_arena_alloc_array(AxArena *a, size_t count, size_t size, size_t align);
/* Copy `size` bytes into the arena (alignment 1). */
void *ax_arena_dup(AxArena *a, const void *src, size_t size);

size_t ax_arena_bytes_requested(const AxArena *a);
size_t ax_arena_chunk_count(const AxArena *a);

#define AX_ARENA_NEW(arena, T) ((T *)ax_arena_alloc((arena), sizeof(T), _Alignof(T)))
#define AX_ARENA_NEW_ARRAY(arena, T, n)                                                           \
    ((T *)ax_arena_alloc_array((arena), (n), sizeof(T), _Alignof(T)))

#endif /* AX_KERNEL_ARENA_H */
