---
id: T930
title: E21.8 SHA-256/SHA-512/BLAKE3 hashes, HMAC/HKDF, ChaCha20-Poly1305 AEAD & Ed25519/X25519 primitives
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T928, T929]
priority: 240
status: todo
attempts: 0
paths: [std/crypto/hash, std/crypto/mac_kdf, std/crypto/aead, std/crypto/sign, tests/run/std_crypto_primitives]
spec: [spec/SPEC-127-crypto-primitives-secure-memory.md, tasks/0467, tasks/0839]
covers: [REQ-STD-172, REQ-RT-184, REQ-RT-185, REQ-RT-186, REQ-RT-187, REQ-RT-786, REQ-RT-787, REQ-RT-788, REQ-RT-789, REQ-RT-790, REQ-RT-791, REQ-RT-792, REQ-RT-793, REQ-RT-794, REQ-RT-795, REQ-RT-796, REQ-RT-797, REQ-RT-798, REQ-RT-799, REQ-RT-800]
---
# T930 — E21.8 SHA-256/SHA-512/BLAKE3 hashes, HMAC/HKDF, ChaCha20-Poly1305 AEAD & Ed25519/X25519 primitives

## Goal
Implement `SHA-256`, `SHA-512`, `BLAKE3`, `HMAC-SHA256`, `HKDF-SHA256`, `ChaCha20-Poly1305` AEAD, and `X25519`/`Ed25519` in `std.crypto` per `spec/SPEC-127-crypto-primitives-secure-memory.md`.

## Scope
- Implement `std/crypto/hash` (`Sha256`, `Sha512`, and `Blake3` incremental streaming and one-shot digests; `tasks/0467 §29-33`, `tasks/0839 §9-12`).
- Implement `std/crypto/mac_kdf` (`HmacSha256` with constant-time `verify_tag` via `ct_eq_bytes` and RFC 5869 `HkdfSha256.extract`/`expand`).
- Implement `std/crypto/aead` (RFC 8439 `ChaCha20Poly1305` authenticated encryption and decryption with 96-bit nonce, AAD, constant-time Poly1305 tag check, and zeroization of output buffer on authentication failure; `REQ-STD-172`).
- Implement `std/crypto/sign` (RFC 7748 `X25519` Diffie-Hellman and RFC 8032 `Ed25519` keypair generation, signing, and strict verification).
- Add run tests in `tests/run/std_crypto_primitives`.

## Acceptance
- [ ] Run tests in `tests/run/std_crypto_primitives` verify FIPS 180-4 `SHA-256`/`SHA-512` vectors, official `BLAKE3` vectors, RFC 4231 `HMAC-SHA256`, RFC 5869 `HKDF-SHA256`, RFC 8439 `ChaCha20-Poly1305` (including tampered-tag rejection & buffer zeroization), RFC 7748 `X25519`, and RFC 8032 `Ed25519` vectors in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T930-report.md` with exact `## Files changed`.

## Out of scope
- Quarantined legacy algorithms (MD5, SHA-1, DES, 3DES) which are isolated in `std.crypto.legacy` (`T949`) rather than modern `std.crypto`.
- Extended suite primitives (SHA-3, Argon2id, AES modes, constant-time Base64/Hex) implemented in `T948`.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T930/build` and `python tools/axtest.py --compiler build-snap-T930/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
