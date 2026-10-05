#ifndef AX_KERNEL_HASH_H
#define AX_KERNEL_HASH_H

/* AXH64 v1 — the stable 64-bit hash of axiom0 (INV-KERN-007, ADR-0004 §4).
 *
 * The algorithm is specified in kernel/README.md ("Hash algorithm") and uses only wrapping 64-bit
 * multiply, add, xor and rotate on little-endian 8-byte words, so the result is identical on every
 * host and std/core/hash.ax (T069) can reproduce it bit for bit. Reference vectors:
 * tests/unit/kernel/hash_vectors.txt. It is a lookup hash, not a cryptographic or seeded one: never
 * use it where an attacker chooses the keys and a collision matters for security. */

#include "kernel/base.h"

/* Hash of a byte string. */
uint64_t ax_hash64(const void *bytes, size_t len);

/* Incremental hasher: writing the bytes of a string in any split gives exactly ax_hash64 of the
 * concatenation (e.g. write("ab"); write("c") == ax_hash64("abc")). */
typedef struct AxHasher {
    uint64_t h;
    uint64_t total_len;
    unsigned char buf[8];
    unsigned buf_len;
} AxHasher;

void ax_hasher_init(AxHasher *s);
void ax_hasher_write(AxHasher *s, const void *bytes, size_t len);
/* Integers are written as their little-endian bytes (4 or 8). */
void ax_hasher_write_u32(AxHasher *s, uint32_t v);
void ax_hasher_write_u64(AxHasher *s, uint64_t v);
/* Does not modify the state; may be called more than once. */
uint64_t ax_hasher_finish(const AxHasher *s);

/* Shorthands, all defined through the byte hash. */
uint64_t ax_hash_u32(uint32_t v);                /* ax_hash64(le32(v), 4)            */
uint64_t ax_hash_u64(uint64_t v);                /* ax_hash64(le64(v), 8)            */
uint64_t ax_hash_combine(uint64_t a, uint64_t b); /* ax_hash64(le64(a) ++ le64(b), 16) */

/* Wrapping rotate left, n in 0..63 (also used by tests and later phases). */
static inline uint64_t ax_rotl64(uint64_t x, unsigned n) {
    n &= 63u;
    return n == 0 ? x : (x << n) | (x >> (64u - n));
}

#endif /* AX_KERNEL_HASH_H */
