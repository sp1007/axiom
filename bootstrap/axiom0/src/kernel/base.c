#include "kernel/base.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

_Noreturn void ax_ice_failv(const char *file, int line, const char *fmt, va_list ap) {
    /* One banner line (runner pattern ICE_BANNER_RE), then the location on its own line. */
    fputs("error: internal compiler error: ", stderr);
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\nnote: at %s:%d\n", file, line);
    fflush(stderr);
    abort();
}

_Noreturn void ax_ice_fail(const char *file, int line, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    ax_ice_failv(file, line, fmt, ap);
    /* not reached: ax_ice_failv never returns (va_end is therefore never executed) */
}

void *ax_xmalloc(size_t size) {
    void *p = malloc(size == 0 ? 1 : size);
    if (p == NULL) {
        AX_ICE("out of memory (%llu bytes)", (unsigned long long)size);
    }
    return p;
}

void *ax_xcalloc(size_t count, size_t size) {
    size_t total = ax_mul_size(count, size);
    void *p = calloc(total == 0 ? 1 : total, 1);
    if (p == NULL) {
        AX_ICE("out of memory (%llu bytes)", (unsigned long long)total);
    }
    return p;
}

void *ax_xrealloc(void *ptr, size_t size) {
    void *p = realloc(ptr, size == 0 ? 1 : size);
    if (p == NULL) {
        AX_ICE("out of memory (%llu bytes)", (unsigned long long)size);
    }
    return p;
}

void ax_xfree(void *ptr) {
    free(ptr);
}

size_t ax_mul_size(size_t a, size_t b) {
    if (a != 0 && b > SIZE_MAX / a) {
        AX_ICE("size overflow: %llu * %llu", (unsigned long long)a, (unsigned long long)b);
    }
    return a * b;
}

size_t ax_add_size(size_t a, size_t b) {
    if (b > SIZE_MAX - a) {
        AX_ICE("size overflow: %llu + %llu", (unsigned long long)a, (unsigned long long)b);
    }
    return a + b;
}

void *ax_grow_array(void *data, size_t *cap, size_t elem_size, size_t needed) {
    size_t old = *cap;
    if (needed <= old) {
        return data;
    }
    size_t want = old > SIZE_MAX / 2 ? SIZE_MAX : old * 2;
    if (want < 8) {
        want = 8;
    }
    if (want < needed) {
        want = needed;
    }
    size_t bytes = ax_mul_size(want, elem_size);
    unsigned char *p = ax_xrealloc(data, bytes);
    memset(p + old * elem_size, 0, bytes - old * elem_size);
    *cap = want;
    return p;
}
