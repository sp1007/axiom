#include <stdint.h>
#include <string.h>

#include "kernel/str.h"
#include "unit.h"

AX_TEST(kernel_str_view_basics) {
    StrView e = ax_sv_cstr(NULL);
    AX_CHECK_EQ_INT(e.len, 0);
    AX_CHECK(ax_sv_eq(e, ax_sv("", 0)));
    StrView a = ax_sv_cstr("std.core.hash");
    AX_CHECK_EQ_INT(a.len, 13);
    AX_CHECK(ax_sv_eq_cstr(a, "std.core.hash"));
    AX_CHECK(!ax_sv_eq_cstr(a, "std.core"));
    AX_CHECK(ax_sv_starts_with(a, ax_sv_cstr("std.")));
    AX_CHECK(!ax_sv_starts_with(ax_sv_cstr("st"), ax_sv_cstr("std")));
    AX_CHECK(ax_sv_ends_with(a, ax_sv_cstr(".hash")));
    AX_CHECK(ax_sv_ends_with(a, e));
    AX_CHECK(!ax_sv_ends_with(ax_sv_cstr("sh"), ax_sv_cstr("hash")));
    StrView mid = ax_sv_slice(a, 4, 4);
    AX_CHECK(ax_sv_eq_cstr(mid, "core"));
    AX_CHECK_EQ_INT(ax_sv_slice(a, 10, 100).len, 3); /* clamped */
    AX_CHECK_EQ_INT(ax_sv_slice(a, 100, 1).len, 0);
    /* embedded NUL bytes are content */
    AX_CHECK(!ax_sv_eq(ax_sv("a\0b", 3), ax_sv("a\0c", 3)));
    AX_CHECK(ax_sv_eq(ax_sv("a\0b", 3), ax_sv("a\0b", 3)));
}

AX_TEST(kernel_str_view_cmp_bytewise) {
    AX_CHECK(ax_sv_cmp(ax_sv_cstr("a"), ax_sv_cstr("b")) < 0);
    AX_CHECK(ax_sv_cmp(ax_sv_cstr("b"), ax_sv_cstr("a")) > 0);
    AX_CHECK(ax_sv_cmp(ax_sv_cstr("ab"), ax_sv_cstr("ab")) == 0);
    AX_CHECK(ax_sv_cmp(ax_sv_cstr("ab"), ax_sv_cstr("abc")) < 0);
    AX_CHECK(ax_sv_cmp(ax_sv_cstr(""), ax_sv_cstr("a")) < 0);
    AX_CHECK(ax_sv_cmp(ax_sv_cstr("Z"), ax_sv_cstr("a")) < 0);
    /* bytes >= 0x80 sort after ASCII (unsigned comparison, no locale) */
    AX_CHECK(ax_sv_cmp(ax_sv_cstr("\xc3\xa0"), ax_sv_cstr("z")) > 0);
}

AX_TEST(kernel_str_dup_into_arena) {
    AxArena a;
    ax_arena_init(&a, 0);
    char src[] = "x\0y";
    StrView d = ax_sv_dup(&a, ax_sv(src, 3));
    src[0] = 'q';
    AX_CHECK_EQ_INT(d.len, 3);
    AX_CHECK(d.ptr[0] == 'x' && d.ptr[1] == '\0' && d.ptr[2] == 'y' && d.ptr[3] == '\0');
    StrView e = ax_sv_dup(&a, ax_sv(NULL, 0));
    AX_CHECK(e.len == 0 && e.ptr != NULL && e.ptr[0] == '\0');
    ax_arena_destroy(&a);
}

AX_TEST(kernel_strbuf_push) {
    StrBuf b;
    ax_sb_init(&b);
    AX_CHECK_EQ_STR(b.ptr, "");
    ax_sb_push_cstr(&b, "Xin ch\xc3\xa0o");
    ax_sb_push_byte(&b, ' ');
    ax_sb_push(&b, ax_sv_cstr("th\xe1\xba\xbf gi\xe1\xbb\x9bi"));
    AX_CHECK_EQ_STR(b.ptr, "Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi");
    AX_CHECK_EQ_INT(b.len, 22);
    ax_sb_truncate(&b, 3);
    AX_CHECK_EQ_STR(b.ptr, "Xin");
    ax_sb_clear(&b);
    AX_CHECK_EQ_INT(b.len, 0);
    for (int i = 0; i < 1000; ++i) {
        ax_sb_push_byte(&b, (char)('a' + i % 26));
    }
    AX_CHECK_EQ_INT(b.len, 1000);
    AX_CHECK(b.ptr[1000] == '\0' && b.ptr[999] == (char)('a' + 999 % 26));
    ax_sb_free(&b);
}

AX_TEST(kernel_strbuf_self_append) {
    StrBuf b;
    ax_sb_init(&b);
    ax_sb_push_cstr(&b, "abcdefgh");
    for (int i = 0; i < 6; ++i) {
        ax_sb_push(&b, ax_sb_view(&b)); /* doubles, forcing reallocations */
    }
    AX_CHECK_EQ_INT(b.len, 8 * 64);
    int ok = 1;
    for (size_t i = 0; i < b.len; ++i) {
        ok &= b.ptr[i] == "abcdefgh"[i % 8];
    }
    AX_CHECK(ok);
    ax_sb_push(&b, ax_sv(b.ptr + 2, 3)); /* interior slice of itself */
    AX_CHECK(memcmp(b.ptr + b.len - 3, "cde", 3) == 0);
    ax_sb_free(&b);
}

AX_TEST(kernel_strbuf_numbers) {
    StrBuf b;
    ax_sb_init(&b);
    ax_sb_push_u64(&b, 0);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_u64(&b, UINT64_MAX);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_i64(&b, -1);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_i64(&b, INT64_MIN);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_i64(&b, INT64_MAX);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_hex(&b, 0xabcULL, 4);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_hex(&b, UINT64_MAX, 16);
    ax_sb_push_byte(&b, ' ');
    ax_sb_push_hex(&b, 0x12345ULL, 2); /* only the low digits */
    AX_CHECK_EQ_STR(b.ptr, "0 18446744073709551615 -1 -9223372036854775808 9223372036854775807 "
                           "0abc ffffffffffffffff 45");
    ax_sb_free(&b);
}

AX_TEST(kernel_strbuf_appendf) {
    StrBuf b;
    ax_sb_init(&b);
    ax_sb_appendf(&b, "%s=%d", "x", 42);
    ax_sb_appendf(&b, "%s", "");
    AX_CHECK_EQ_STR(b.ptr, "x=42");
    char big[300];
    memset(big, 'z', sizeof big - 1);
    big[sizeof big - 1] = '\0';
    ax_sb_appendf(&b, "[%s]", big);
    AX_CHECK_EQ_INT(b.len, 4 + 2 + 299);
    AX_CHECK(b.ptr[b.len - 1] == ']' && b.ptr[b.len] == '\0');
    ax_sb_free(&b);
}
