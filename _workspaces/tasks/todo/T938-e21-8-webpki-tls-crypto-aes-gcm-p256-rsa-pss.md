---
id: T938
title: E21.8 — WebPKI & TLS 1.3 crypto primitives (AES-GCM, ECDSA P-256, RSA-PSS verification)
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T930]
priority: 248
status: todo
attempts: 0
paths: [std/crypto/cipher, std/crypto/curve, std/crypto/rsa, tests/run/std_crypto_webpki]
spec: [spec/SPEC-127-crypto-primitives-secure-memory.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-172, REQ-RT-184]
---
# T938 — E21.8 — WebPKI & TLS 1.3 crypto primitives (AES-GCM, ECDSA P-256, RSA-PSS verification)

## Goal
Implement mandatory WebPKI and TLS 1.3 cryptographic primitives in `std.crypto`: `AES-128-GCM` / `AES-256-GCM` with hardware acceleration and constant-time fallback, `ECDSA P-256` key exchange and signature verification, and `RSA-PSS` signature verification.

## Scope
- Implement `std/crypto/cipher` for AES-GCM:
  * Provide `Aes128Gcm` and `Aes256Gcm` authenticated encryption with 96-bit nonces and 128-bit authentication tags.
  * Use `@multiversion` hardware acceleration: AES-NI + `PCLMULQDQ` on x86-64, ARMv8 Cryptographic Extensions on AArch64.
  * Implement constant-time bit-sliced software AES fallback and constant-time GHASH polynomial multiplication to prevent cache-timing attacks when hardware instructions are absent.
- Implement `std/crypto/curve` for NIST curve `secp256r1` (`P-256`):
  * Complete projective Weierstrass coordinates with complete addition formulas.
  * Implement ECDH key agreement and ECDSA signature generation / verification with RFC 6979 deterministic nonce generation.
- Implement `std/crypto/rsa` for RSA signature verification:
  * Fast constant-time Montgomery multiplication for 2048-bit, 3072-bit, and 4096-bit modulus sizes.
  * RFC 8017 `RSA-PSS` verification with SHA-256 and MGF1 masking.

## Acceptance
- [ ] Conformance tests in `tests/run/std_crypto_webpki` verify NIST CAVP and RFC test vectors for AES-GCM (128/256), ECDSA P-256, and RSA-PSS across `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Tampered ciphertext and invalid tag test cases fail closed with zero buffer leakage.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T938-report.md` with exact `## Files changed`.

## Out of scope
- Arbitrary bignum arithmetic library (only fixed-size fields needed for P-256 / RSA).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T938/build` and `python tools/axtest.py --compiler build-snap-T938/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:25:00 created by axiom-architect (ADR-0039 P21 WebPKI crypto expansion)
