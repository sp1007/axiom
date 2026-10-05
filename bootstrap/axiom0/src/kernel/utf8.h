#ifndef AX_KERNEL_UTF8_H
#define AX_KERNEL_UTF8_H

/* UTF-8 decoding and validation per Unicode 15 §3.9 (Table 3-7, well-formed byte sequences):
 * no overlong forms, no surrogates U+D800..U+DFFF, nothing above U+10FFFF. Locale independent. */

#include "kernel/base.h"

#define AX_UTF8_REPLACEMENT 0xFFFDu

typedef struct AxUtf8Decoded {
    uint32_t cp;  /* the scalar value, or AX_UTF8_REPLACEMENT when !ok */
    uint32_t len; /* bytes consumed, >= 1 whenever input is non-empty, 0 for empty input */
    bool ok;
} AxUtf8Decoded;

/* Decode one scalar at s[0..n). On an ill-formed sequence `len` is the length of the maximal
 * subpart (the longest prefix of a well-formed sequence, at least 1 byte), so a decoder loop
 * replaces each maximal subpart with one U+FFFD (Unicode "best practice", §3.9 U+FFFD policy). */
AxUtf8Decoded ax_utf8_decode(const unsigned char *s, size_t n);

/* True if all of s[0..n) is well-formed. On failure *err_offset (if not NULL) receives the offset
 * of the first ill-formed sequence; on success it receives n. */
bool ax_utf8_validate(const unsigned char *s, size_t n, size_t *err_offset);

/* Encode a scalar value; returns 1..4, or 0 for a surrogate or a value above U+10FFFF. */
unsigned ax_utf8_encode(uint32_t cp, unsigned char out[4]);

/* Number of scalars in well-formed input; ill-formed maximal subparts count as one each. */
size_t ax_utf8_count(const unsigned char *s, size_t n);

static inline bool ax_utf8_is_continuation(unsigned char b) {
    return (b & 0xC0u) == 0x80u;
}

#endif /* AX_KERNEL_UTF8_H */
