#ifndef AX_KERNEL_STR_H
#define AX_KERNEL_STR_H

/* Byte strings. Axiom source text and identifiers are UTF-8 byte strings; nothing here depends on
 * the C locale or on NUL termination of the input (a StrView may contain NUL bytes).
 *
 * StrView — borrowed (ptr, len) slice; never owns memory.
 * StrBuf  — growable heap buffer, always NUL-terminated (ptr is never NULL after init). */

#include "kernel/arena.h"
#include "kernel/base.h"

typedef struct StrView {
    const char *ptr;
    size_t len;
} StrView;

static inline StrView ax_sv(const char *ptr, size_t len) {
    StrView s = {ptr, len};
    return s;
}
StrView ax_sv_cstr(const char *cstr); /* NULL gives the empty view */
bool ax_sv_eq(StrView a, StrView b);
bool ax_sv_eq_cstr(StrView a, const char *cstr);
/* Bytewise (unsigned) lexicographic order: <0, 0, >0. Locale independent. */
int ax_sv_cmp(StrView a, StrView b);
bool ax_sv_starts_with(StrView s, StrView prefix);
bool ax_sv_ends_with(StrView s, StrView suffix);
/* Sub-view [start, start + len) clamped to the view. */
StrView ax_sv_slice(StrView s, size_t start, size_t len);
/* AXH64 of the bytes. */
uint64_t ax_sv_hash(StrView s);
/* Copy into the arena with a trailing NUL (not counted in len). */
StrView ax_sv_dup(AxArena *arena, StrView s);

typedef struct StrBuf {
    char *ptr;
    size_t len;
    size_t cap; /* bytes available for content, excluding the NUL */
} StrBuf;

void ax_sb_init(StrBuf *b);
void ax_sb_free(StrBuf *b);
void ax_sb_clear(StrBuf *b);
void ax_sb_reserve(StrBuf *b, size_t additional);
void ax_sb_push_byte(StrBuf *b, char c);
void ax_sb_push(StrBuf *b, StrView s);
void ax_sb_push_cstr(StrBuf *b, const char *s);
/* Decimal, no locale. */
void ax_sb_push_u64(StrBuf *b, uint64_t v);
void ax_sb_push_i64(StrBuf *b, int64_t v);
/* Lowercase hexadecimal with exactly `digits` digits (1..16), zero padded. */
void ax_sb_push_hex(StrBuf *b, uint64_t v, unsigned digits);
/* printf-style append (vsnprintf); for messages and dumps, never for semantic values. */
void ax_sb_appendf(StrBuf *b, const char *fmt, ...) AX_PRINTF_LIKE(2, 3);
void ax_sb_truncate(StrBuf *b, size_t len);
static inline StrView ax_sb_view(const StrBuf *b) {
    return ax_sv(b->ptr, b->len);
}

#endif /* AX_KERNEL_STR_H */
