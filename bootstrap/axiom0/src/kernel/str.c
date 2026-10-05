#include "kernel/str.h"

#include <stdio.h>
#include <string.h>

#include "kernel/hash.h"

StrView ax_sv_cstr(const char *cstr) {
    return cstr == NULL ? ax_sv("", 0) : ax_sv(cstr, strlen(cstr));
}

bool ax_sv_eq(StrView a, StrView b) {
    return a.len == b.len && (a.len == 0 || memcmp(a.ptr, b.ptr, a.len) == 0);
}

bool ax_sv_eq_cstr(StrView a, const char *cstr) {
    return ax_sv_eq(a, ax_sv_cstr(cstr));
}

int ax_sv_cmp(StrView a, StrView b) {
    size_t n = a.len < b.len ? a.len : b.len;
    int c = n == 0 ? 0 : memcmp(a.ptr, b.ptr, n); /* memcmp compares as unsigned char */
    if (c != 0) {
        return c < 0 ? -1 : 1;
    }
    return a.len < b.len ? -1 : (a.len > b.len ? 1 : 0);
}

bool ax_sv_starts_with(StrView s, StrView prefix) {
    return prefix.len <= s.len && ax_sv_eq(ax_sv(s.ptr, prefix.len), prefix);
}

bool ax_sv_ends_with(StrView s, StrView suffix) {
    return suffix.len <= s.len && ax_sv_eq(ax_sv(s.ptr + (s.len - suffix.len), suffix.len), suffix);
}

StrView ax_sv_slice(StrView s, size_t start, size_t len) {
    if (start > s.len) {
        start = s.len;
    }
    if (len > s.len - start) {
        len = s.len - start;
    }
    return ax_sv(s.ptr + start, len);
}

uint64_t ax_sv_hash(StrView s) {
    return ax_hash64(s.ptr, s.len);
}

StrView ax_sv_dup(AxArena *arena, StrView s) {
    char *p = ax_arena_alloc(arena, ax_add_size(s.len, 1), 1);
    if (s.len != 0) {
        memcpy(p, s.ptr, s.len);
    }
    p[s.len] = '\0';
    return ax_sv(p, s.len);
}

void ax_sb_init(StrBuf *b) {
    b->cap = 15;
    b->ptr = ax_xmalloc(b->cap + 1);
    b->ptr[0] = '\0';
    b->len = 0;
}

void ax_sb_free(StrBuf *b) {
    ax_xfree(b->ptr);
    b->ptr = NULL;
    b->len = 0;
    b->cap = 0;
}

void ax_sb_clear(StrBuf *b) {
    b->len = 0;
    b->ptr[0] = '\0';
}

void ax_sb_reserve(StrBuf *b, size_t additional) {
    AX_ASSERT(b->ptr != NULL);
    size_t need = ax_add_size(b->len, additional);
    if (need <= b->cap) {
        return;
    }
    size_t cap = b->cap * 2 > need ? b->cap * 2 : need;
    b->ptr = ax_xrealloc(b->ptr, ax_add_size(cap, 1));
    b->cap = cap;
}

void ax_sb_push_byte(StrBuf *b, char c) {
    ax_sb_reserve(b, 1);
    b->ptr[b->len++] = c;
    b->ptr[b->len] = '\0';
}

void ax_sb_push(StrBuf *b, StrView s) {
    if (s.len == 0) {
        return;
    }
    /* s may point into b itself: remember its offset, the reserve below may move the buffer */
    uintptr_t base = (uintptr_t)(void *)b->ptr;
    uintptr_t at = (uintptr_t)(const void *)s.ptr;
    bool inside = at >= base && at < base + b->len;
    size_t off = inside ? (size_t)(at - base) : 0;
    ax_sb_reserve(b, s.len);
    memmove(b->ptr + b->len, inside ? b->ptr + off : s.ptr, s.len);
    b->len += s.len;
    b->ptr[b->len] = '\0';
}

void ax_sb_push_cstr(StrBuf *b, const char *s) {
    ax_sb_push(b, ax_sv_cstr(s));
}

void ax_sb_push_u64(StrBuf *b, uint64_t v) {
    char tmp[20];
    size_t n = 0;
    do {
        tmp[n++] = (char)('0' + (int)(v % 10u));
        v /= 10u;
    } while (v != 0);
    ax_sb_reserve(b, n);
    while (n > 0) {
        b->ptr[b->len++] = tmp[--n];
    }
    b->ptr[b->len] = '\0';
}

void ax_sb_push_i64(StrBuf *b, int64_t v) {
    if (v < 0) {
        ax_sb_push_byte(b, '-');
        /* negate in unsigned arithmetic: also correct for INT64_MIN */
        ax_sb_push_u64(b, (uint64_t)0 - (uint64_t)v);
    } else {
        ax_sb_push_u64(b, (uint64_t)v);
    }
}

void ax_sb_push_hex(StrBuf *b, uint64_t v, unsigned digits) {
    static const char hex[] = "0123456789abcdef";
    AX_ASSERT(digits >= 1 && digits <= 16);
    ax_sb_reserve(b, digits);
    for (unsigned i = digits; i > 0; --i) {
        b->ptr[b->len++] = hex[(v >> (4u * (i - 1))) & 0xFu];
    }
    b->ptr[b->len] = '\0';
}

void ax_sb_appendf(StrBuf *b, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    va_list ap2;
    va_copy(ap2, ap);
    int n = vsnprintf(NULL, 0, fmt, ap);
    va_end(ap);
    if (n < 0) {
        va_end(ap2);
        AX_ICE("ax_sb_appendf: invalid format \"%s\"", fmt);
    }
    ax_sb_reserve(b, (size_t)n);
    vsnprintf(b->ptr + b->len, (size_t)n + 1, fmt, ap2);
    va_end(ap2);
    b->len += (size_t)n;
}

void ax_sb_truncate(StrBuf *b, size_t len) {
    AX_ASSERT(len <= b->len);
    b->len = len;
    b->ptr[len] = '\0';
}
