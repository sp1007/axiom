#include "kernel/utf8.h"

AxUtf8Decoded ax_utf8_decode(const unsigned char *s, size_t n) {
    AxUtf8Decoded r = {AX_UTF8_REPLACEMENT, 0, false};
    if (n == 0) {
        return r;
    }
    unsigned char b0 = s[0];
    r.len = 1;
    if (b0 < 0x80u) {
        r.cp = b0;
        r.ok = true;
        return r;
    }
    unsigned need;          /* continuation bytes after the lead */
    unsigned char lo = 0x80u, hi = 0xBFu; /* allowed range of the second byte (Table 3-7) */
    uint32_t cp;
    if (b0 >= 0xC2u && b0 <= 0xDFu) {
        need = 1;
        cp = b0 & 0x1Fu;
    } else if (b0 >= 0xE0u && b0 <= 0xEFu) {
        need = 2;
        cp = b0 & 0x0Fu;
        if (b0 == 0xE0u) {
            lo = 0xA0u; /* no overlong */
        } else if (b0 == 0xEDu) {
            hi = 0x9Fu; /* no surrogates */
        }
    } else if (b0 >= 0xF0u && b0 <= 0xF4u) {
        need = 3;
        cp = b0 & 0x07u;
        if (b0 == 0xF0u) {
            lo = 0x90u; /* no overlong */
        } else if (b0 == 0xF4u) {
            hi = 0x8Fu; /* <= U+10FFFF */
        }
    } else {
        return r; /* 80..C1, F5..FF: never a lead byte */
    }
    for (unsigned i = 1; i <= need; ++i) {
        if (i >= n) {
            return r; /* truncated: maximal subpart = what we have consumed so far */
        }
        unsigned char b = s[i];
        unsigned char l = i == 1 ? lo : 0x80u;
        unsigned char h = i == 1 ? hi : 0xBFu;
        if (b < l || b > h) {
            return r;
        }
        cp = (cp << 6) | (uint32_t)(b & 0x3Fu);
        r.len = i + 1;
    }
    r.cp = cp;
    r.ok = true;
    return r;
}

bool ax_utf8_validate(const unsigned char *s, size_t n, size_t *err_offset) {
    size_t i = 0;
    while (i < n) {
        AxUtf8Decoded d = ax_utf8_decode(s + i, n - i);
        if (!d.ok) {
            if (err_offset != NULL) {
                *err_offset = i;
            }
            return false;
        }
        i += d.len;
    }
    if (err_offset != NULL) {
        *err_offset = n;
    }
    return true;
}

unsigned ax_utf8_encode(uint32_t cp, unsigned char out[4]) {
    if (cp < 0x80u) {
        out[0] = (unsigned char)cp;
        return 1;
    }
    if (cp < 0x800u) {
        out[0] = (unsigned char)(0xC0u | (cp >> 6));
        out[1] = (unsigned char)(0x80u | (cp & 0x3Fu));
        return 2;
    }
    if (cp >= 0xD800u && cp <= 0xDFFFu) {
        return 0;
    }
    if (cp < 0x10000u) {
        out[0] = (unsigned char)(0xE0u | (cp >> 12));
        out[1] = (unsigned char)(0x80u | ((cp >> 6) & 0x3Fu));
        out[2] = (unsigned char)(0x80u | (cp & 0x3Fu));
        return 3;
    }
    if (cp <= 0x10FFFFu) {
        out[0] = (unsigned char)(0xF0u | (cp >> 18));
        out[1] = (unsigned char)(0x80u | ((cp >> 12) & 0x3Fu));
        out[2] = (unsigned char)(0x80u | ((cp >> 6) & 0x3Fu));
        out[3] = (unsigned char)(0x80u | (cp & 0x3Fu));
        return 4;
    }
    return 0;
}

size_t ax_utf8_count(const unsigned char *s, size_t n) {
    size_t count = 0;
    size_t i = 0;
    while (i < n) {
        i += ax_utf8_decode(s + i, n - i).len;
        ++count;
    }
    return count;
}
