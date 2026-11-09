# Red-Team Architectural Review: Proposal #13 (`P21` `E21.8` Complete Crypto Suite: `AES-CTR/CBC/KW`, `Argon2id`/`PBKDF2`, `SHA-3`/`Keccak`/`SHA-384`, Constant-Time `Base64`/`Hex` & Quarantined `std.crypto.legacy` `DES`/`3DES`/`MD5`/`SHA-1`)

**Scope**: Adversarial security review of owner directive (*"std đã có crypto hay hash/aes/des ... các loại chưa"* -> *"làm đi"*).

---

## Verdict: `ACCEPT WITH QUARANTINE ISOLATION, CONSTANT-TIME PADDING & STATIC AUDIT GUARDRAILS`

Use the remaining two free numeric IDs in `P21` (**`T948` and `T949`**) under **`E21.8` (`SPEC-127`)**, update `T928`/`T930`/`T931`/`T914`/`T321`, and wire weak-crypto detection into `P17` `E17.9` (`SPEC-151`).

---

## Critical Traps Caught & Mandatory Security Guardrails

1. **Quarantined `std.crypto.legacy` vs `T930` Blanket Exclusion**:
   - `T930` previously excluded `SHA-1`, `MD5`, and `DES` outright — which breaks **RFC 6455 WebSocket handshakes** (`Sec-WebSocket-Accept = Base64(SHA1(key + GUID))`), **RFC 6238 TOTP 2FA (`HMAC-SHA1`)**, Git object hashing, and legacy banking/EMV/HSM/PKCS#12 interoperability.
   - **Guardrail**: Keep `std.crypto` root strictly modern-only; place `Sha1`, `HmacSha1`, `Md5`, `Des`, and `TripleDes` (`TdesEde3Cbc`) inside **`std.crypto.legacy`**.
   - Implement `Des` / `TripleDes` using **constant-time bit-sliced S-boxes** (zero lookup-table cache-timing leaks!).
   - Wire `E17.9` Zero-Day Static Scanner (`SPEC-151`) to emit **`AX_VERIFY_WEAK_CRYPTO_PRIMITIVE`** whenever `std.crypto.legacy` primitives feed password storage, digital signature, or modern transport sinks without explicit `@suppress`.

2. **`AES-CBC` Padding Oracle Trap (Vaudenay / Lucky13) & `AES-ECB` Footgun**:
   - Add `Aes128Ctr`/`Aes256Ctr`, `Aes128Cbc`/`Aes256Cbc`, and RFC 3394 `AesKw` (Key Wrap).
   - **Guardrail**: `AesCbc` PKCS#7 unpadding MUST inspect all 16 bytes of the final block in **strict constant time** (`ct_eq`/`ct_select`), never branching early on invalid pad bytes. Do NOT expose multi-block `AesEcb` stream mode (only raw single-block `AesCipher.encrypt_block([u8; 16])` for building modes safely).

3. **Memory-Hard Password Hashing OOM & Residual-Secret Traps (`Argon2id` + `PBKDF2`)**:
   - Add RFC 9106 **`Argon2id`** (PHC string format) + RFC 8018 **`Pbkdf2HmacSha256` / `Pbkdf2HmacSha512`** in `std.crypto.password`.
   - **Guardrail**: Zeroize the entire `Argon2id` working memory blocks on completion/drop (`ZeroizeOnDrop`) and enforce bounded `max_memory_kib` / `max_time_cost` limits when verifying untrusted PHC strings to prevent memory-exhaustion DoS in `std.web` login endpoints.

4. **`SHA-3` vs `Keccak-256` Domain-Byte Confusion & Constant-Time `Base64`/`Hex`**:
   - Provide `Sha384` (needed for `TLS_AES_256_GCM_SHA384`) plus distinct types for FIPS 202 `Sha3_256`/`Sha3_512`/`Shake128`/`Shake256` (`0x06` pad) vs `Keccak256` (`0x01` pad) so developers never silently hash with the wrong Keccak padding.
   - Implement `std.encoding.hex` & `std.encoding.base64` (`Standard` + `UrlSafe`) using **branchless constant-time arithmetic** (no cache-indexed tables that leak secret keys or PEM bytes).
