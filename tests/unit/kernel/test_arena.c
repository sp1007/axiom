#include <stdint.h>
#include <string.h>

#include "kernel/arena.h"
#include "unit.h"

/* INV-KERN-003: arena growth, alignment, zeroing, reset and free-all. */

static int is_aligned(const void *p, size_t align) {
    return ((uintptr_t)p & (uintptr_t)(align - 1)) == 0;
}

AX_TEST(kernel_arena_alignment) {
    AxArena a;
    ax_arena_init(&a, 256);
    for (size_t align = 1; align <= AX_ARENA_MAX_ALIGN; align *= 2) {
        (void)ax_arena_alloc(&a, 1, 1); /* misalign the bump pointer on purpose */
        void *p = ax_arena_alloc(&a, 24, align);
        AX_CHECK(is_aligned(p, align));
    }
    double *d = AX_ARENA_NEW(&a, double);
    AX_CHECK(is_aligned(d, _Alignof(double)));
    long long *ll = AX_ARENA_NEW_ARRAY(&a, long long, 5);
    AX_CHECK(is_aligned(ll, _Alignof(long long)));
    ax_arena_destroy(&a);
}

AX_TEST(kernel_arena_zeroed_and_distinct) {
    AxArena a;
    ax_arena_init(&a, 128);
    unsigned char *prev = NULL;
    for (int i = 0; i < 200; ++i) {
        unsigned char *p = ax_arena_alloc(&a, 40, 8);
        for (int j = 0; j < 40; ++j) {
            AX_CHECK(p[j] == 0);
        }
        memset(p, 0xAB, 40);
        AX_CHECK(p != prev);
        if (prev != NULL) {
            AX_CHECK(prev[0] == 0xAB && prev[39] == 0xAB); /* earlier objects stay intact */
        }
        prev = p;
    }
    ax_arena_destroy(&a);
}

AX_TEST(kernel_arena_growth_adds_chunks) {
    AxArena a;
    ax_arena_init(&a, 1024);
    AX_CHECK_EQ_INT(ax_arena_chunk_count(&a), 0);
    (void)ax_arena_alloc(&a, 16, 8);
    AX_CHECK_EQ_INT(ax_arena_chunk_count(&a), 1);
    for (int i = 0; i < 100; ++i) {
        (void)ax_arena_alloc(&a, 100, 8);
    }
    AX_CHECK(ax_arena_chunk_count(&a) >= 10);
    AX_CHECK_EQ_INT(ax_arena_bytes_requested(&a), 16 + 100 * 100);
    ax_arena_destroy(&a);
    AX_CHECK_EQ_INT(ax_arena_chunk_count(&a), 0);
    AX_CHECK_EQ_INT(ax_arena_bytes_requested(&a), 0);
}

AX_TEST(kernel_arena_large_allocation) {
    AxArena a;
    ax_arena_init(&a, 64);
    unsigned char *big = ax_arena_alloc(&a, 100000, 64);
    AX_CHECK(is_aligned(big, 64));
    big[0] = 1;
    big[99999] = 2;
    unsigned char *small = ax_arena_alloc(&a, 8, 8);
    small[0] = 3;
    AX_CHECK(big[0] == 1 && big[99999] == 2);
    ax_arena_destroy(&a);
}

AX_TEST(kernel_arena_reset_keeps_first_chunk) {
    AxArena a;
    ax_arena_init(&a, 512);
    unsigned char *first = ax_arena_alloc(&a, 32, 16);
    for (int i = 0; i < 50; ++i) {
        (void)ax_arena_alloc(&a, 100, 8);
    }
    AX_CHECK(ax_arena_chunk_count(&a) > 1);
    memset(first, 0x5A, 32);
    ax_arena_reset(&a);
    AX_CHECK_EQ_INT(ax_arena_chunk_count(&a), 1);
    AX_CHECK_EQ_INT(ax_arena_bytes_requested(&a), 0);
    unsigned char *again = ax_arena_alloc(&a, 32, 16);
    AX_CHECK(again == first); /* the first chunk's memory is reused ... */
    for (int j = 0; j < 32; ++j) {
        AX_CHECK(again[j] == 0); /* ... and handed out zeroed */
    }
    ax_arena_reset(&a);
    ax_arena_reset(&a); /* idempotent */
    AX_CHECK_EQ_INT(ax_arena_chunk_count(&a), 1);
    ax_arena_destroy(&a);
    ax_arena_reset(&a); /* reset of an empty arena is a no-op */
    AX_CHECK_EQ_INT(ax_arena_chunk_count(&a), 0);
    (void)ax_arena_alloc(&a, 8, 8); /* usable after destroy */
    ax_arena_destroy(&a);
}

AX_TEST(kernel_arena_dup_and_zero_size) {
    AxArena a;
    ax_arena_init(&a, 0);
    const char msg[] = "Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi";
    char *copy = ax_arena_dup(&a, msg, sizeof msg);
    AX_CHECK(memcmp(copy, msg, sizeof msg) == 0);
    AX_CHECK(copy != msg);
    void *z = ax_arena_alloc(&a, 0, 16);
    AX_CHECK(z != NULL && is_aligned(z, 16));
    void *e = ax_arena_dup(&a, NULL, 0);
    AX_CHECK(e != NULL);
    int *arr = AX_ARENA_NEW_ARRAY(&a, int, 0);
    AX_CHECK(arr != NULL);
    ax_arena_destroy(&a);
}
