#include <stdint.h>
#include <string.h>

#include "kernel/arena.h"
#include "kernel/hashmap.h"
#include "kernel/interner.h"
#include "unit.h"

/* Insertion-ordered HashMap (INV-KERN-007, INV-KERN-002; contract in kernel/README.md). */

AX_DEFINE_HASHMAP(KtMap, uint32_t, uint32_t, ax_key_hash_u32, ax_key_eq_u32);

/* Degenerate hashes force collisions: every key in one probe chain, or in 4 chains. */
static inline uint64_t kt_hash_const(const uint32_t *k) {
    (void)k;
    return 42;
}
static inline uint64_t kt_hash_mod4(const uint32_t *k) {
    return (uint64_t)(*k % 4u) << 32; /* also zero low bits: all keys start at slot 0 */
}
AX_DEFINE_HASHMAP(KtCollideMap, uint32_t, uint32_t, kt_hash_const, ax_key_eq_u32);
AX_DEFINE_HASHMAP(KtMod4Map, uint32_t, uint32_t, kt_hash_mod4, ax_key_eq_u32);

/* Keys visited by iteration, into out[]; returns the count. */
static size_t kt_keys(const KtMap *m, uint32_t *out, size_t cap) {
    size_t n = 0;
    uint32_t cur = 0;
    KtMapEntry *e;
    while (KtMap_next(m, &cur, &e)) {
        if (n < cap) {
            out[n] = e->key;
        }
        ++n;
    }
    return n;
}

AX_TEST(kernel_hashmap_insert_get) {
    KtMap m;
    KtMap_init(&m);
    AX_CHECK(KtMap_get(&m, 1) == NULL);
    AX_CHECK(!KtMap_remove(&m, 1, NULL));
    AX_CHECK(KtMap_insert(&m, 1, 10));
    AX_CHECK(KtMap_insert(&m, 2, 20));
    AX_CHECK(!KtMap_insert(&m, 1, 11)); /* existing key: value replaced */
    AX_CHECK_EQ_INT(KtMap_len(&m), 2);
    AX_CHECK_EQ_INT(*KtMap_get(&m, 1), 11);
    AX_CHECK_EQ_INT(*KtMap_get(&m, 2), 20);
    AX_CHECK(KtMap_contains(&m, 2));
    AX_CHECK(!KtMap_contains(&m, 3));
    *KtMap_get(&m, 2) = 21;
    AX_CHECK_EQ_INT(*KtMap_get(&m, 2), 21);
    AX_CHECK(KtMap_insert(&m, 0, 5)); /* key 0 is an ordinary key */
    AX_CHECK_EQ_INT(*KtMap_get(&m, 0), 5);
    KtMap_free(&m);
}

AX_TEST(kernel_hashmap_growth) {
    KtMap m;
    KtMap_init(&m);
    for (uint32_t i = 0; i < 100000; ++i) {
        AX_CHECK(KtMap_insert(&m, i * 2654435761u, i));
    }
    AX_CHECK_EQ_INT(KtMap_len(&m), 100000);
    int ok = 1;
    for (uint32_t i = 0; i < 100000; ++i) {
        uint32_t *v = KtMap_get(&m, i * 2654435761u);
        ok &= v != NULL && *v == i;
    }
    AX_CHECK(ok);
    /* iteration = insertion order */
    uint32_t cur = 0, expect = 0;
    KtMapEntry *e;
    ok = 1;
    while (KtMap_next(&m, &cur, &e)) {
        ok &= e->value == expect++;
    }
    AX_CHECK(ok);
    AX_CHECK_EQ_INT(expect, 100000);
    KtMap_free(&m);
}

AX_TEST(kernel_hashmap_collisions) {
    KtCollideMap c;
    KtCollideMap_init(&c);
    for (uint32_t i = 0; i < 300; ++i) {
        KtCollideMap_insert(&c, i, i + 1000);
    }
    int ok = 1;
    for (uint32_t i = 0; i < 300; ++i) {
        ok &= *KtCollideMap_get(&c, i) == i + 1000;
    }
    AX_CHECK(ok);
    AX_CHECK(KtCollideMap_get(&c, 300) == NULL);
    for (uint32_t i = 0; i < 300; i += 2) {
        AX_CHECK(KtCollideMap_remove(&c, i, NULL));
    }
    ok = 1;
    for (uint32_t i = 0; i < 300; ++i) {
        uint32_t *v = KtCollideMap_get(&c, i);
        ok &= (i % 2 == 0) ? v == NULL : (v != NULL && *v == i + 1000);
    }
    AX_CHECK(ok); /* tombstones do not break probe chains */
    AX_CHECK_EQ_INT(KtCollideMap_len(&c), 150);
    KtCollideMap_free(&c);

    KtMod4Map m;
    KtMod4Map_init(&m);
    for (uint32_t i = 0; i < 1000; ++i) {
        KtMod4Map_insert(&m, i, i);
    }
    for (uint32_t i = 0; i < 1000; i += 3) {
        KtMod4Map_remove(&m, i, NULL);
    }
    for (uint32_t i = 0; i < 1000; i += 3) {
        KtMod4Map_insert(&m, i, i + 1);
    }
    ok = 1;
    for (uint32_t i = 0; i < 1000; ++i) {
        ok &= *KtMod4Map_get(&m, i) == (i % 3 == 0 ? i + 1 : i);
    }
    AX_CHECK(ok);
    KtMod4Map_free(&m);
}

/* The documented contract: update keeps the position, delete removes from the order, re-insert
 * appends at the end. */
AX_TEST(kernel_hashmap_order_after_delete_reinsert) {
    KtMap m;
    KtMap_init(&m);
    uint32_t keys[] = {50, 10, 40, 20, 30};
    for (size_t i = 0; i < 5; ++i) {
        KtMap_insert(&m, keys[i], (uint32_t)i);
    }
    uint32_t out[16];
    AX_CHECK_EQ_INT(kt_keys(&m, out, 16), 5);
    AX_CHECK(out[0] == 50 && out[1] == 10 && out[2] == 40 && out[3] == 20 && out[4] == 30);

    KtMap_insert(&m, 40, 99); /* update: position kept */
    kt_keys(&m, out, 16);
    AX_CHECK(out[0] == 50 && out[1] == 10 && out[2] == 40 && out[3] == 20 && out[4] == 30);
    AX_CHECK_EQ_INT(*KtMap_get(&m, 40), 99);

    uint32_t removed = 0;
    AX_CHECK(KtMap_remove(&m, 10, &removed)); /* delete: gone from the order */
    AX_CHECK_EQ_INT(removed, 1);
    AX_CHECK_EQ_INT(kt_keys(&m, out, 16), 4);
    AX_CHECK(out[0] == 50 && out[1] == 40 && out[2] == 20 && out[3] == 30);

    KtMap_insert(&m, 10, 7); /* re-insert: appended at the end */
    AX_CHECK_EQ_INT(kt_keys(&m, out, 16), 5);
    AX_CHECK(out[0] == 50 && out[1] == 40 && out[2] == 20 && out[3] == 30 && out[4] == 10);
    AX_CHECK_EQ_INT(*KtMap_get(&m, 10), 7);

    KtMap_remove(&m, 50, NULL); /* delete the first */
    KtMap_remove(&m, 10, NULL); /* delete the last */
    KtMap_insert(&m, 60, 0);
    AX_CHECK_EQ_INT(kt_keys(&m, out, 16), 4);
    AX_CHECK(out[0] == 40 && out[1] == 20 && out[2] == 30 && out[3] == 60);
    KtMap_free(&m);
}

/* Many deletions trigger compaction; the order of the survivors must be unchanged. */
AX_TEST(kernel_hashmap_compaction_keeps_order) {
    KtMap m;
    KtMap_init(&m);
    for (uint32_t i = 0; i < 2000; ++i) {
        KtMap_insert(&m, i, i);
    }
    for (uint32_t i = 0; i < 2000; ++i) {
        if (i % 10 != 0) {
            KtMap_remove(&m, i, NULL);
        }
    }
    for (uint32_t i = 5000; i < 5100; ++i) {
        KtMap_insert(&m, i, i); /* insertions after mass removal compact the entry array */
    }
    AX_CHECK_EQ_INT(KtMap_len(&m), 300);
    static uint32_t out[400];
    AX_CHECK_EQ_INT(kt_keys(&m, out, 400), 300);
    int ok = 1;
    for (uint32_t i = 0; i < 200; ++i) {
        ok &= out[i] == i * 10;
    }
    for (uint32_t i = 0; i < 100; ++i) {
        ok &= out[200 + i] == 5000 + i;
    }
    AX_CHECK(ok);
    AX_CHECK(m.raw.len < 2100); /* dead entries were squeezed out */
    for (uint32_t i = 0; i < 2000; ++i) {
        ok &= (KtMap_get(&m, i) != NULL) == (i % 10 == 0);
    }
    AX_CHECK(ok);
    KtMap_free(&m);
}

AX_TEST(kernel_hashmap_remove_while_iterating) {
    KtMap m;
    KtMap_init(&m);
    for (uint32_t i = 0; i < 100; ++i) {
        KtMap_insert(&m, i, i);
    }
    uint32_t cur = 0, visited = 0;
    KtMapEntry *e;
    while (KtMap_next(&m, &cur, &e)) {
        uint32_t k = e->key;
        ++visited;
        if (k % 2 == 1) {
            KtMap_remove(&m, k, NULL); /* removing the current entry is allowed */
        }
        if (k + 1 < 100 && (k + 1) % 4 == 0) {
            KtMap_remove(&m, k + 1, NULL); /* so is removing a later one: it is skipped */
        }
    }
    AX_CHECK_EQ_INT(visited, 76); /* 4, 8, ..., 96 were removed before their turn */
    uint32_t out[100];
    size_t n = kt_keys(&m, out, 100);
    AX_CHECK_EQ_INT(n, 26); /* 0 and the keys 2 mod 4 */
    int ok = n > 0 && out[0] == 0;
    for (size_t i = 1; i < n; ++i) {
        ok &= out[i] % 4 == 2;
    }
    AX_CHECK(ok);
    KtMap_free(&m);
}

AX_TEST(kernel_hashmap_clear_and_reuse) {
    KtMap m;
    KtMap_init(&m);
    for (uint32_t i = 0; i < 50; ++i) {
        KtMap_insert(&m, i, i);
    }
    KtMap_clear(&m);
    AX_CHECK_EQ_INT(KtMap_len(&m), 0);
    AX_CHECK(KtMap_get(&m, 3) == NULL);
    uint32_t out[4];
    AX_CHECK_EQ_INT(kt_keys(&m, out, 4), 0);
    KtMap_insert(&m, 7, 1);
    KtMap_insert(&m, 3, 2);
    AX_CHECK_EQ_INT(kt_keys(&m, out, 4), 2);
    AX_CHECK(out[0] == 7 && out[1] == 3);
    KtMap_free(&m);
    KtMap_free(&m); /* free of a freed map is harmless */
    AX_CHECK_EQ_INT(KtMap_len(&m), 0);
}

/* INV-KERN-002: the same operation sequence gives the same iteration order whatever the heap and
 * arena did in between (different allocation patterns, hence different addresses). */
static void kt_build(KtMap *m, AxArena *noise, size_t noise_size, uint32_t *out, size_t *n) {
    KtMap_init(m);
    for (uint32_t i = 0; i < 3000; ++i) {
        KtMap_insert(m, (i * 7919u) % 10007u, i);
        if (noise_size != 0) {
            (void)ax_arena_alloc(noise, noise_size + i % 13u, 8);
        }
        if (i % 5 == 0) {
            KtMap_remove(m, ((i / 2) * 7919u) % 10007u, NULL);
        }
    }
    *n = kt_keys(m, out, 3000);
}

AX_TEST(kernel_hashmap_order_independent_of_allocation) {
    static uint32_t a[3000], b[3000];
    size_t na, nb;
    KtMap ma, mb;
    AxArena noise;
    ax_arena_init(&noise, 4096);
    void *hold = ax_xmalloc(12345); /* shift the heap state for the second map */
    kt_build(&ma, &noise, 0, a, &na);
    kt_build(&mb, &noise, 333, b, &nb);
    AX_CHECK_EQ_INT(na, nb);
    AX_CHECK(na > 0 && memcmp(a, b, na * sizeof a[0]) == 0);
    KtMap_free(&ma);
    KtMap_free(&mb);
    ax_xfree(hold);
    ax_arena_destroy(&noise);
}

AX_TEST(kernel_hashmap_string_keys) {
    AxStrIdMap m;
    AxStrIdMap_init(&m);
    char buf1[] = "alpha";
    char buf2[] = "alpha"; /* equal content, different address: same key */
    StrId one = {1}, two = {2};
    AX_CHECK(AxStrIdMap_insert(&m, ax_sv(buf1, 5), one));
    AX_CHECK(!AxStrIdMap_insert(&m, ax_sv(buf2, 5), two));
    AX_CHECK_EQ_INT(AxStrIdMap_len(&m), 1);
    AX_CHECK_EQ_INT(AxStrIdMap_get(&m, ax_sv_cstr("alpha"))->v, 2);
    AX_CHECK(AxStrIdMap_get(&m, ax_sv_cstr("alph")) == NULL);
    AX_CHECK(AxStrIdMap_insert(&m, ax_sv("", 0), one));
    AX_CHECK_EQ_INT(AxStrIdMap_get(&m, ax_sv("", 0))->v, 1);
    AxStrIdMap_free(&m);
}
