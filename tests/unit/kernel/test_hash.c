#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "kernel/hash.h"
#include "kernel/str.h"
#include "unit.h"

/* AXH64 v1 known-answer tests (INV-KERN-007). The vectors in hash_vectors.txt are produced by the
 * independent Python implementation gen_hash_vectors.py, so this test cross-checks two
 * implementations of the algorithm written down in kernel/README.md. */

static unsigned char seq_byte(size_t i) {
    return (unsigned char)((i * 7u + 3u) % 256u);
}

/* hash_vectors.txt lives next to this file. CMake compiles sources by absolute path, so __FILE__
 * gives its directory; when run from the repository root the relative path also works. */
static FILE *open_vectors(void) {
    char path[4096];
    const char *self = __FILE__;
    const char *slash = NULL;
    for (const char *p = self; *p != '\0'; ++p) {
        if (*p == '/' || *p == '\\') {
            slash = p;
        }
    }
    if (slash != NULL && (size_t)(slash - self) + 32 < sizeof path) {
        size_t dir = (size_t)(slash - self) + 1;
        memcpy(path, self, dir);
        strcpy(path + dir, "hash_vectors.txt");
        FILE *f = fopen(path, "rb");
        if (f != NULL) {
            return f;
        }
    }
    return fopen("tests/unit/kernel/hash_vectors.txt", "rb");
}

static int hex_digit(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    return -1;
}

AX_TEST(kernel_hash_vectors) {
    FILE *f = open_vectors();
    AX_CHECK(f != NULL);
    if (f == NULL) {
        return;
    }
    static char line[8192];
    static unsigned char key[4096];
    int count = 0, saw_empty = 0, saw_one_byte = 0, saw_greeting = 0, saw_1k = 0;
    while (fgets(line, sizeof line, f) != NULL) {
        size_t n = strlen(line);
        while (n > 0 && (line[n - 1] == '\n' || line[n - 1] == '\r')) {
            line[--n] = '\0';
        }
        if (n == 0 || line[0] == '#') {
            continue;
        }
        AX_CHECK(n > 17 && line[16] == ' ');
        if (n <= 17) {
            continue;
        }
        uint64_t want = 0;
        for (int i = 0; i < 16; ++i) {
            int d = hex_digit(line[i]);
            AX_CHECK(d >= 0);
            want = (want << 4) | (uint64_t)(d < 0 ? 0 : d);
        }
        const char *kind = line + 17;
        size_t klen = 0;
        if (strncmp(kind, "hex ", 4) == 0) {
            const char *h = kind + 4;
            if (strcmp(h, "-") != 0) {
                size_t hl = strlen(h);
                AX_CHECK(hl % 2 == 0 && hl / 2 <= sizeof key);
                for (size_t i = 0; i + 1 < hl && klen < sizeof key; i += 2) {
                    key[klen++] = (unsigned char)(hex_digit(h[i]) * 16 + hex_digit(h[i + 1]));
                }
            }
            saw_empty |= klen == 0;
            saw_one_byte |= klen == 1;
        } else if (strncmp(kind, "text ", 5) == 0) {
            klen = strlen(kind + 5);
            AX_CHECK(klen <= sizeof key);
            memcpy(key, kind + 5, klen);
            saw_greeting |= strcmp(kind + 5, "Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi") == 0;
        } else if (strncmp(kind, "seq ", 4) == 0) {
            klen = (size_t)strtoul(kind + 4, NULL, 10);
            AX_CHECK(klen <= sizeof key);
            if (klen > sizeof key) {
                klen = sizeof key;
            }
            for (size_t i = 0; i < klen; ++i) {
                key[i] = seq_byte(i);
            }
            saw_1k |= klen == 1024;
        } else {
            ax_unit_failf(__FILE__, __LINE__, "unknown vector kind: %s", kind);
            continue;
        }
        uint64_t got = ax_hash64(key, klen);
        if (got != want) {
            ax_unit_failf(__FILE__, __LINE__, "hash of [%s]: got %016llx, expected %016llx", kind,
                          (unsigned long long)got, (unsigned long long)want);
        }
        ++count;
    }
    fclose(f);
    AX_CHECK(count >= 32);
    AX_CHECK(saw_empty);
    AX_CHECK(saw_one_byte);
    AX_CHECK(saw_greeting);
    AX_CHECK(saw_1k);
}

/* A few vectors compiled in, so a missing or damaged vector file cannot hide a regression. */
AX_TEST(kernel_hash_builtin_vectors) {
    AX_CHECK(ax_hash64("", 0) == UINT64_C(0xd8e728ed68f180e9));
    AX_CHECK(ax_hash64("a", 1) == UINT64_C(0xda2e93eede955e3f));
    AX_CHECK(ax_hash64("abc", 3) == UINT64_C(0x050282dd1361d4b1));
    AX_CHECK(ax_hash64("abcdefgh", 8) == UINT64_C(0x6652d639d2991029));
}

AX_TEST(kernel_hash_streaming_equals_oneshot) {
    unsigned char buf[300];
    for (size_t i = 0; i < sizeof buf; ++i) {
        buf[i] = seq_byte(i);
    }
    for (size_t len = 0; len <= sizeof buf; len += 13) {
        uint64_t one = ax_hash64(buf, len);
        for (size_t split = 0; split <= len; split += 5) {
            AxHasher s;
            ax_hasher_init(&s);
            ax_hasher_write(&s, buf, split);
            ax_hasher_write(&s, buf + split, len - split);
            AX_CHECK(ax_hasher_finish(&s) == one);
        }
        /* byte at a time */
        AxHasher s;
        ax_hasher_init(&s);
        for (size_t i = 0; i < len; ++i) {
            ax_hasher_write(&s, buf + i, 1);
        }
        AX_CHECK(ax_hasher_finish(&s) == one);
        AX_CHECK(ax_hasher_finish(&s) == one); /* finish does not consume */
    }
}

AX_TEST(kernel_hash_integer_shorthands) {
    unsigned char le4[4] = {0x07, 0, 0, 0};
    unsigned char le8[8] = {0x07, 0, 0, 0, 0, 0, 0, 0};
    AX_CHECK(ax_hash_u32(7) == ax_hash64(le4, 4));
    AX_CHECK(ax_hash_u64(7) == ax_hash64(le8, 8));
    AX_CHECK(ax_hash_u64(7) == UINT64_C(0x078b539bc05a6987));
    AX_CHECK(ax_hash_u32(7) == UINT64_C(0x9c51ebe90fbb1bd5));
    unsigned char le16[16] = {0x01, 0, 0, 0, 0, 0, 0, 0, 0x02, 0, 0, 0, 0, 0, 0, 0};
    AX_CHECK(ax_hash_combine(1, 2) == ax_hash64(le16, 16));
    AX_CHECK(ax_hash_combine(1, 2) != ax_hash_combine(2, 1));
    AX_CHECK(ax_sv_hash(ax_sv("abc", 3)) == ax_hash64("abc", 3));
}

AX_TEST(kernel_hash_length_is_mixed_in) {
    /* zero padding of the tail must not make "a" and "a\0" collide */
    AX_CHECK(ax_hash64("a\0", 2) != ax_hash64("a", 1));
    AX_CHECK(ax_hash64("\0", 1) != ax_hash64("", 0));
    unsigned char z[16] = {0};
    for (size_t i = 0; i < 16; ++i) {
        AX_CHECK(ax_hash64(z, i) != ax_hash64(z, i + 1));
    }
}

AX_TEST(kernel_hash_rotl) {
    AX_CHECK(ax_rotl64(1, 0) == 1);
    AX_CHECK(ax_rotl64(1, 63) == UINT64_C(0x8000000000000000));
    AX_CHECK(ax_rotl64(UINT64_C(0x8000000000000000), 1) == 1);
    AX_CHECK(ax_rotl64(UINT64_C(0x0123456789abcdef), 64) == UINT64_C(0x0123456789abcdef));
}

AX_TEST(kernel_hash_low_bits_spread) {
    /* the map uses the low bits: 4096 consecutive integers must fill most of 4096 buckets */
    static unsigned char used[4096];
    memset(used, 0, sizeof used);
    size_t distinct = 0;
    for (uint32_t i = 0; i < 4096; ++i) {
        size_t b = (size_t)(ax_hash_u32(i) & 4095u);
        distinct += used[b] == 0;
        used[b] = 1;
    }
    AX_CHECK(distinct > 2400); /* random expectation ~2589 */
}
