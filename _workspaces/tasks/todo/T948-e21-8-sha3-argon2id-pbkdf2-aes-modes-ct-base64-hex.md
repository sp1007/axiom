---
id: T948
title: E21.8 — Extended crypto suite: SHA-3, Argon2id, PBKDF2, AES-CTR/CBC/KW & constant-time Base64/Hex
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T938]
priority: 250
status: todo
attempts: 0
paths: [std/crypto/hash, std/crypto/password, std/crypto/cipher, std/encoding, tests/run/std_crypto_extended]
spec: [spec/SPEC-127-crypto-primitives-secure-memory.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-172, REQ-RT-184]
---
# T948 — E21.8 — Extended crypto suite: SHA-3, Argon2id, PBKDF2, AES-CTR/CBC/KW & constant-time Base64/Hex

## Goal
Implement extended modern cryptographic primitives in `std.crypto`: `SHA-384`, `SHA-3`/`SHAKE`/`Keccak`, memory-hard password hashing (`Argon2id`, `PBKDF2`) with DoS protection, symmetric block cipher modes (`AES-CTR`, `AES-CBC`, `AES-KW`), and branchless constant-time `std.encoding.{base64, hex}`.

## Scope
- Implement extended digest algorithms in `std/crypto/hash`:
  * `Sha384` (required for `TLS_AES_256_GCM_SHA384`).
  * FIPS 202 `Sha3_256`, `Sha3_512`, `Shake128`, `Shake256` (using domain padding `0x06`).
  * Separate `Keccak256` primitive (using domain padding `0x01`) to eliminate padding confusion.
- Implement memory-hard password hashing in `std/crypto/password`:
  * RFC 9106 `Argon2id` emitting and verifying standard PHC string formatting (`$argon2id$v=19$m=...,t=...,p=...$`).
  * RFC 8018 `Pbkdf2HmacSha256` and `Pbkdf2HmacSha512`.
  * Guarantee zeroization of internal matrix/state buffers on completion or early exit (`ZeroizeOnDrop`).
  * Enforce strict configurable resource limits (`max_memory_kib`, `max_time_cost`) on PHC verification to prevent memory exhaustion DoS attacks.
- Implement symmetric modes in `std/crypto/cipher`:
  * `Aes128Ctr` and `Aes256Ctr` with 128-bit counter incrementing.
  * `Aes128Cbc` and `Aes256Cbc` with constant-time PKCS#7 unpadding verifying all 16 bytes via `ct_eq`/`ct_select` without early branch exits (preventing Vaudenay / Lucky13 padding oracles).
  * RFC 3394 `AesKw` (AES Key Wrap) for secure cryptographic key encapsulation.
- Implement branchless constant-time string encodings in `std/encoding`:
  * `std.encoding.hex` (lowercase and uppercase).
  * `std.encoding.base64` (`Standard` with `=` padding and `UrlSafe` unpadded) using bit-manipulation arithmetic instead of lookup tables that cause cache-timing side channels.

## Acceptance
- [ ] Run tests in `tests/run/std_crypto_extended` verify official test vectors for SHA-384, SHA-3, SHAKE, Keccak-256, Argon2id, PBKDF2, AES-CTR, AES-CBC, and AES-KW across `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] PKCS#7 unpadding oracle test verifies constant execution time regardless of invalid padding byte positions.
- [ ] Base64/Hex encoding and decoding test vectors pass with zero cache-line memory lookups.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T948-report.md` with exact `## Files changed`.

## Out of scope
- Multi-block `AES-ECB` stream mode (deliberately omitted as a hazardous cryptographic footgun; only raw single-block primitives exist).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T948/build` and `python tools/axtest.py --compiler build-snap-T948/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:25:00 created by axiom-architect (ADR-0039 P21 complete crypto expansion)
