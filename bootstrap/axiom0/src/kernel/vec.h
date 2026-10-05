#ifndef AX_KERNEL_VEC_H
#define AX_KERNEL_VEC_H

/* Type-safe growable array.
 *
 *     AX_DEFINE_VEC(U32Vec, uint32_t)
 *     U32Vec v = U32Vec_new();          // or U32Vec_init(&v)
 *     U32Vec_push(&v, 7);
 *     uint32_t x = U32Vec_get(&v, 0);   // bounds-checked (AX_ICE when out of range)
 *     U32Vec_free(&v);
 *
 * The struct exposes `data`, `len`, `cap` for read access; mutate through the functions. Elements
 * are stored contiguously; a pointer from Name_at() is invalidated by any call that may grow the
 * vector. Growth policy is ax_grow_array (deterministic, capacity doubles, minimum 8). Heap backed:
 * a Vec is for builders and tables; phase data that is never freed early belongs in an Arena. */

#include "kernel/base.h"

#include <string.h>

#define AX_DEFINE_VEC(Name, T)                                                                    \
    typedef struct Name {                                                                         \
        T *data;                                                                                  \
        size_t len;                                                                               \
        size_t cap;                                                                               \
    } Name;                                                                                       \
    AX_MAYBE_UNUSED static inline Name Name##_new(void) {                                                         \
        Name v = {NULL, 0, 0};                                                                    \
        return v;                                                                                 \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_init(Name *v) {                                                     \
        v->data = NULL;                                                                           \
        v->len = 0;                                                                               \
        v->cap = 0;                                                                               \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_free(Name *v) {                                                     \
        ax_xfree(v->data);                                                                        \
        Name##_init(v);                                                                           \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_reserve(Name *v, size_t additional) {                               \
        v->data = (T *)ax_grow_array(v->data, &v->cap, sizeof(T), ax_add_size(v->len, additional)); \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline size_t Name##_push(Name *v, T value) {                                          \
        if (v->len == v->cap) {                                                                   \
            Name##_reserve(v, 1);                                                                 \
        }                                                                                         \
        v->data[v->len] = value;                                                                  \
        return v->len++;                                                                          \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline T *Name##_at(const Name *v, size_t i) {                                         \
        AX_ASSERT(i < v->len);                                                                    \
        return &v->data[i];                                                                       \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline T Name##_get(const Name *v, size_t i) {                                         \
        return *Name##_at(v, i);                                                                  \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_set(Name *v, size_t i, T value) {                                   \
        *Name##_at(v, i) = value;                                                                 \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline T *Name##_last(const Name *v) {                                                 \
        AX_ASSERT(v->len > 0);                                                                    \
        return &v->data[v->len - 1];                                                              \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline T Name##_pop(Name *v) {                                                         \
        AX_ASSERT(v->len > 0);                                                                    \
        return v->data[--v->len];                                                                 \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_truncate(Name *v, size_t new_len) {                                 \
        AX_ASSERT(new_len <= v->len);                                                             \
        v->len = new_len;                                                                         \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_clear(Name *v) {                                                    \
        v->len = 0;                                                                               \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline size_t Name##_len(const Name *v) {                                              \
        return v->len;                                                                            \
    }                                                                                             \
    AX_MAYBE_UNUSED static inline void Name##_remove_ordered(Name *v, size_t i) {                                 \
        AX_ASSERT(i < v->len);                                                                    \
        memmove(&v->data[i], &v->data[i + 1], (v->len - i - 1) * sizeof(T));                      \
        --v->len;                                                                                 \
    }                                                                                             \
    typedef int Name##_vec_defined_ /* swallow the trailing semicolon */

#endif /* AX_KERNEL_VEC_H */
