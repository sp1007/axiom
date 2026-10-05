#include <stdio.h>
#include <string.h>

#include "kernel/interner.h"
#include "unit.h"

/* INV-KERN-004 (interner part): identity, distinctness, deterministic id order. */

AX_TEST(kernel_interner_identity) {
    StrInterner in;
    ax_interner_init(&in);
    char a[] = "Vector";
    char b[] = "Vector"; /* same spelling, different buffer */
    StrId ia = ax_intern(&in, ax_sv(a, 6));
    StrId ib = ax_intern(&in, ax_sv(b, 6));
    AX_CHECK(StrId_is_some(ia));
    AX_CHECK(StrId_eq(ia, ib));
    AX_CHECK(StrId_eq(ax_intern_cstr(&in, "Vector"), ia));
    StrId ic = ax_intern_cstr(&in, "vector");
    AX_CHECK(!StrId_eq(ia, ic)); /* case sensitive, bytewise */
    AX_CHECK_EQ_INT(ax_interner_len(&in), 2);
    a[0] = 'X'; /* the interner owns its copy */
    AX_CHECK(ax_sv_eq_cstr(ax_interner_get(&in, ia), "Vector"));
    ax_interner_free(&in);
}

AX_TEST(kernel_interner_ids_in_first_intern_order) {
    StrInterner in;
    ax_interner_init(&in);
    const char *words[] = {"fn", "main", "let", "fn", "x", "main", "y"};
    unsigned expect[] = {1, 2, 3, 1, 4, 2, 5};
    for (size_t i = 0; i < AX_ARRAY_LEN(words); ++i) {
        AX_CHECK_EQ_INT(ax_intern_cstr(&in, words[i]).v, expect[i]);
    }
    AX_CHECK_EQ_INT(ax_interner_len(&in), 5);
    ax_interner_free(&in);
}

AX_TEST(kernel_interner_lookup_does_not_add) {
    StrInterner in;
    ax_interner_init(&in);
    AX_CHECK(StrId_is_none(ax_interner_lookup(&in, ax_sv_cstr("x"))));
    AX_CHECK_EQ_INT(ax_interner_len(&in), 0);
    StrId x = ax_intern_cstr(&in, "x");
    AX_CHECK(StrId_eq(ax_interner_lookup(&in, ax_sv_cstr("x")), x));
    AX_CHECK(StrId_is_none(ax_interner_lookup(&in, ax_sv_cstr("y"))));
    AX_CHECK_EQ_INT(ax_interner_len(&in), 1);
    ax_interner_free(&in);
}

AX_TEST(kernel_interner_empty_nul_and_utf8) {
    StrInterner in;
    ax_interner_init(&in);
    StrId empty = ax_intern(&in, ax_sv("", 0));
    AX_CHECK(StrId_is_some(empty)); /* the empty spelling is a real string, not "none" */
    AX_CHECK_EQ_INT(ax_interner_get(&in, empty).len, 0);
    StrId n1 = ax_intern(&in, ax_sv("a\0b", 3));
    StrId n2 = ax_intern(&in, ax_sv("a\0c", 3));
    StrId n3 = ax_intern(&in, ax_sv("a", 1));
    AX_CHECK(!StrId_eq(n1, n2) && !StrId_eq(n1, n3));
    StrView g = ax_sv_cstr("Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi");
    StrId gi = ax_intern(&in, g);
    StrView back = ax_interner_get(&in, gi);
    AX_CHECK(ax_sv_eq(back, g));
    AX_CHECK(back.ptr[back.len] == '\0'); /* stored NUL-terminated */
    ax_interner_free(&in);
}

AX_TEST(kernel_interner_many_strings_stable) {
    StrInterner in;
    ax_interner_init(&in);
    char buf[32];
    const char *first_ptr = NULL;
    StrId first = StrId_none();
    for (int i = 0; i < 20000; ++i) {
        int n = snprintf(buf, sizeof buf, "ident_%d", i);
        StrId id = ax_intern(&in, ax_sv(buf, (size_t)n));
        AX_CHECK_EQ_INT(id.v, i + 1);
        if (i == 0) {
            first = id;
            first_ptr = ax_interner_get(&in, id).ptr;
        }
    }
    /* spellings do not move when the interner grows */
    AX_CHECK(ax_interner_get(&in, first).ptr == first_ptr);
    int ok = 1;
    for (int i = 0; i < 20000; i += 7) {
        int n = snprintf(buf, sizeof buf, "ident_%d", i);
        ok &= ax_intern(&in, ax_sv(buf, (size_t)n)).v == (uint32_t)(i + 1);
        ok &= ax_sv_eq(ax_interner_get(&in, StrId_from_index((size_t)i)), ax_sv(buf, (size_t)n));
    }
    AX_CHECK(ok);
    AX_CHECK_EQ_INT(ax_interner_len(&in), 20000);
    ax_interner_free(&in);
}

/* INV-KERN-002: ids depend on the intern sequence only, not on the allocation history. */
AX_TEST(kernel_interner_deterministic_across_allocation_patterns) {
    const char *words[] = {"z", "a", "m", "a", "longer_identifier", "z", "b", ""};
    uint32_t ids1[8], ids2[8];
    StrInterner in1, in2;
    ax_interner_init(&in1);
    for (size_t i = 0; i < 8; ++i) {
        ids1[i] = ax_intern_cstr(&in1, words[i]).v;
    }
    void *junk = ax_xmalloc(77777);
    ax_interner_init(&in2);
    for (int i = 0; i < 100; ++i) {
        (void)ax_arena_alloc(&in2.bytes, 100, 8); /* different arena layout */
    }
    for (size_t i = 0; i < 8; ++i) {
        ids2[i] = ax_intern_cstr(&in2, words[i]).v;
    }
    AX_CHECK(memcmp(ids1, ids2, sizeof ids1) == 0);
    ax_xfree(junk);
    ax_interner_free(&in1);
    ax_interner_free(&in2);
}
