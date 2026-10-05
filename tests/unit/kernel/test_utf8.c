#include <string.h>

#include "kernel/utf8.h"
#include "unit.h"

static AxUtf8Decoded dec(const char *s, size_t n) {
    return ax_utf8_decode((const unsigned char *)s, n);
}

AX_TEST(kernel_utf8_decode_valid) {
    AxUtf8Decoded d = dec("A", 1);
    AX_CHECK(d.ok && d.cp == 0x41 && d.len == 1);
    d = dec("\0", 1);
    AX_CHECK(d.ok && d.cp == 0 && d.len == 1);
    d = dec("\xc3\xa0", 2); /* à */
    AX_CHECK(d.ok && d.cp == 0xE0 && d.len == 2);
    d = dec("\xe1\xba\xbf", 3); /* ế */
    AX_CHECK(d.ok && d.cp == 0x1EBF && d.len == 3);
    d = dec("\xf0\x9f\x98\x80", 4); /* U+1F600 */
    AX_CHECK(d.ok && d.cp == 0x1F600 && d.len == 4);
    d = dec("\xc2\x80", 2);
    AX_CHECK(d.ok && d.cp == 0x80);
    d = dec("\xdf\xbf", 2);
    AX_CHECK(d.ok && d.cp == 0x7FF);
    d = dec("\xe0\xa0\x80", 3);
    AX_CHECK(d.ok && d.cp == 0x800);
    d = dec("\xed\x9f\xbf", 3);
    AX_CHECK(d.ok && d.cp == 0xD7FF);
    d = dec("\xee\x80\x80", 3);
    AX_CHECK(d.ok && d.cp == 0xE000);
    d = dec("\xef\xbf\xbf", 3);
    AX_CHECK(d.ok && d.cp == 0xFFFF);
    d = dec("\xf0\x90\x80\x80", 4);
    AX_CHECK(d.ok && d.cp == 0x10000);
    d = dec("\xf4\x8f\xbf\xbf", 4);
    AX_CHECK(d.ok && d.cp == 0x10FFFF);
    d = dec("", 0);
    AX_CHECK(!d.ok && d.len == 0);
}

/* Ill-formed input: ok = false, cp = U+FFFD, len = maximal subpart (Unicode §3.9). */
AX_TEST(kernel_utf8_decode_invalid) {
    struct {
        const char *s;
        size_t n;
        unsigned len;
    } cases[] = {
        {"\x80", 1, 1},             /* lone continuation */
        {"\xbf", 1, 1},
        {"\xc0\x80", 2, 1},         /* overlong 2-byte lead */
        {"\xc1\xbf", 2, 1},
        {"\xe0\x80\x80", 3, 1},     /* overlong 3-byte: E0 needs A0..BF */
        {"\xe0\x9f\xbf", 3, 1},
        {"\xed\xa0\x80", 3, 1},     /* surrogate U+D800 */
        {"\xed\xbf\xbf", 3, 1},     /* surrogate U+DFFF */
        {"\xf0\x80\x80\x80", 4, 1}, /* overlong 4-byte */
        {"\xf4\x90\x80\x80", 4, 1}, /* > U+10FFFF */
        {"\xf5\x80\x80\x80", 4, 1}, /* never a lead */
        {"\xff", 1, 1},
        {"\xc3", 1, 1},             /* truncated */
        {"\xe1\xba", 2, 2},         /* truncated after a valid prefix: maximal subpart 2 */
        {"\xf0\x9f\x98", 3, 3},
        {"\xe1\xbaZ", 3, 2},        /* bad third byte */
        {"\xf0\x9f\x41", 3, 2},
        {"\xc3\x41", 2, 1},
    };
    for (size_t i = 0; i < AX_ARRAY_LEN(cases); ++i) {
        AxUtf8Decoded d = dec(cases[i].s, cases[i].n);
        if (d.ok || d.cp != AX_UTF8_REPLACEMENT || d.len != cases[i].len) {
            ax_unit_failf(__FILE__, __LINE__, "case %zu: ok=%d cp=%x len=%u (want len %u)", i,
                          (int)d.ok, (unsigned)d.cp, (unsigned)d.len, cases[i].len);
        }
    }
}

AX_TEST(kernel_utf8_validate_and_count) {
    const char *g = "Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi";
    size_t off = 99;
    AX_CHECK(ax_utf8_validate((const unsigned char *)g, strlen(g), &off));
    AX_CHECK_EQ_INT(off, 22);
    AX_CHECK_EQ_INT(ax_utf8_count((const unsigned char *)g, strlen(g)), 17);
    AX_CHECK(ax_utf8_validate((const unsigned char *)"", 0, NULL));
    const char *bad = "ok\xc3\xa0\xed\xa0\x80tail";
    AX_CHECK(!ax_utf8_validate((const unsigned char *)bad, strlen(bad), &off));
    AX_CHECK_EQ_INT(off, 4);
    /* "ok" + à + 3 maximal subparts of 1 byte (ED, A0, 80) + "tail" */
    AX_CHECK_EQ_INT(ax_utf8_count((const unsigned char *)bad, strlen(bad)), 2 + 1 + 3 + 4);
    AX_CHECK(!ax_utf8_validate((const unsigned char *)"abc\xe1\xba", 5, &off));
    AX_CHECK_EQ_INT(off, 3);
}

AX_TEST(kernel_utf8_encode_roundtrip_all_scalars) {
    unsigned char buf[4];
    int ok = 1;
    for (uint32_t cp = 0; cp <= 0x10FFFFu; ++cp) {
        unsigned n = ax_utf8_encode(cp, buf);
        if (cp >= 0xD800u && cp <= 0xDFFFu) {
            ok &= n == 0;
            continue;
        }
        unsigned want = cp < 0x80u ? 1 : cp < 0x800u ? 2 : cp < 0x10000u ? 3 : 4;
        ok &= n == want;
        AxUtf8Decoded d = ax_utf8_decode(buf, n);
        ok &= d.ok && d.cp == cp && d.len == n;
    }
    AX_CHECK(ok);
    AX_CHECK_EQ_INT(ax_utf8_encode(0x110000u, buf), 0);
    AX_CHECK_EQ_INT(ax_utf8_encode(0xFFFFFFFFu, buf), 0);
    AX_CHECK(ax_utf8_is_continuation(0x80) && ax_utf8_is_continuation(0xBF));
    AX_CHECK(!ax_utf8_is_continuation(0x7F) && !ax_utf8_is_continuation(0xC0));
}
