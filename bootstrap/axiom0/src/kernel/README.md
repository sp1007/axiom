Typed ids, arenas, vectors, hash maps, strings, interner, hash and UTF-8 helpers. Layer: lowest (depends on nothing).

## Hash algorithm (AXH64 v1)
The deterministic 64-bit hash of axiom0 uses only wrapping 64-bit multiply, add, xor, and rotate on little-endian 8-byte words.

1. **State initialization**: `h = 0x27D4EB2F165667C5` (SEED).
2. **Chunking**: The input is processed in 8-byte chunks, read as little-endian `uint64_t`. If the last chunk is less than 8 bytes, it is zero-extended to 8 bytes.
3. **Round function**: For each 8-byte chunk `w`:
   - `m = rotl(w * 0xC2B2AE3D27D4EB4F, 31) * 0x9E3779B97F4A7C15`
   - `h = rotl(h ^ m, 27) * 0x9E3779B97F4A7C15 + 0x165667B19E3779F9`
   where `rotl(x, n)` is a left rotation of `x` by `n` bits.
4. **Length combination**: After all chunks are processed, incorporate the total length (in bytes) as a wrapping 64-bit integer: `h ^= total_len * 0x165667B19E3779F9`.
5. **Avalanche**:
   - `fold(x) = x ^ rotl(x, 15) ^ rotl(x, 40)`
   - `h = fold(h) * 0x9FB21C651E98DF25`
   - `h = fold(h) * 0xC2B2AE3D27D4EB4F`
   - return `fold(h)`

## HashMap iteration contract
Insertion-ordered hash map (open addressing, deterministic iteration).
Contract (observable, std HashMap T073 must match it):
- iteration visits the live entries in the order their keys were first inserted;
- inserting an existing key replaces the value and keeps the key's position;
- removing a key deletes it from the order; inserting it again appends it at the end;
- the order never depends on hash values, table capacity, pointer values or allocation history.
