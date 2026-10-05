#include "kernel/hash.h"

#include <string.h>

/* AXH64 v1 constants (kernel/README.md, "Hash algorithm"). Changing any of them, the rotation
 * counts or the step order changes every hash: that requires an ADR and new reference vectors. */
#define AXH_K1 UINT64_C(0x9E3779B97F4A7C15)
#define AXH_K2 UINT64_C(0xC2B2AE3D27D4EB4F)
#define AXH_K3 UINT64_C(0x165667B19E3779F9)
#define AXH_SEED UINT64_C(0x27D4EB2F165667C5)
#define AXH_M UINT64_C(0x9FB21C651E98DF25)

static uint64_t load_le64(const unsigned char *p, unsigned n) {
    uint64_t w = 0;
    for (unsigned i = 0; i < n; ++i) {
        w |= (uint64_t)p[i] << (8u * i);
    }
    return w;
}

static uint64_t axh_round(uint64_t h, uint64_t w) {
    uint64_t m = ax_rotl64(w * AXH_K2, 31) * AXH_K1;
    return ax_rotl64(h ^ m, 27) * AXH_K1 + AXH_K3;
}

static uint64_t axh_fold(uint64_t h) {
    return h ^ ax_rotl64(h, 15) ^ ax_rotl64(h, 40);
}

static uint64_t axh_avalanche(uint64_t h) {
    h = axh_fold(h) * AXH_M;
    h = axh_fold(h) * AXH_K2;
    return axh_fold(h);
}

void ax_hasher_init(AxHasher *s) {
    s->h = AXH_SEED;
    s->total_len = 0;
    memset(s->buf, 0, sizeof s->buf);
    s->buf_len = 0;
}

void ax_hasher_write(AxHasher *s, const void *bytes, size_t len) {
    const unsigned char *p = bytes;
    s->total_len += (uint64_t)len; /* wrapping, as specified */
    while (len > 0) {
        if (s->buf_len == 0 && len >= 8) {
            s->h = axh_round(s->h, load_le64(p, 8));
            p += 8;
            len -= 8;
            continue;
        }
        s->buf[s->buf_len++] = *p++;
        --len;
        if (s->buf_len == 8) {
            s->h = axh_round(s->h, load_le64(s->buf, 8));
            s->buf_len = 0;
        }
    }
}

void ax_hasher_write_u32(AxHasher *s, uint32_t v) {
    unsigned char b[4];
    for (unsigned i = 0; i < 4; ++i) {
        b[i] = (unsigned char)(v >> (8u * i));
    }
    ax_hasher_write(s, b, 4);
}

void ax_hasher_write_u64(AxHasher *s, uint64_t v) {
    unsigned char b[8];
    for (unsigned i = 0; i < 8; ++i) {
        b[i] = (unsigned char)(v >> (8u * i));
    }
    ax_hasher_write(s, b, 8);
}

uint64_t ax_hasher_finish(const AxHasher *s) {
    uint64_t h = s->h;
    if (s->buf_len > 0) {
        h = axh_round(h, load_le64(s->buf, s->buf_len)); /* tail, zero-extended */
    }
    h ^= s->total_len * AXH_K3;
    return axh_avalanche(h);
}

uint64_t ax_hash64(const void *bytes, size_t len) {
    AxHasher s;
    ax_hasher_init(&s);
    ax_hasher_write(&s, bytes, len);
    return ax_hasher_finish(&s);
}

uint64_t ax_hash_u32(uint32_t v) {
    AxHasher s;
    ax_hasher_init(&s);
    ax_hasher_write_u32(&s, v);
    return ax_hasher_finish(&s);
}

uint64_t ax_hash_u64(uint64_t v) {
    AxHasher s;
    ax_hasher_init(&s);
    ax_hasher_write_u64(&s, v);
    return ax_hasher_finish(&s);
}

uint64_t ax_hash_combine(uint64_t a, uint64_t b) {
    AxHasher s;
    ax_hasher_init(&s);
    ax_hasher_write_u64(&s, a);
    ax_hasher_write_u64(&s, b);
    return ax_hasher_finish(&s);
}
