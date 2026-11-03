---
id: T931
title: E21.8 Cryptographic hashes, CSPRNG, AEAD, Ed25519 & constant-time secure memory conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T930]
priority: 241
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_8_crypto_secure_mem]
spec: [spec/SPEC-127-crypto-primitives-secure-memory.md, tasks/0467, tasks/0839]
covers: [REQ-STD-172, REQ-RT-179, REQ-RT-180, REQ-RT-181, REQ-RT-182, REQ-RT-184, REQ-RT-185, REQ-RT-186, REQ-RT-187, REQ-RT-801, REQ-RT-802, REQ-RT-803, REQ-RT-804, REQ-RT-805, REQ-RT-806, REQ-RT-807, REQ-RT-808, REQ-RT-809]
---
# T931 — E21.8 Cryptographic hashes, CSPRNG, AEAD, Ed25519 & constant-time secure memory conformance suite

## Goal
Certify E21.8 exit criteria with an end-to-end cryptographic and secure-memory conformance suite covering `CtEq`/`CtSelect`, `SecretBytes` zeroization, `OsRng`/`ChaCha20Rng`, `SHA-256`/`SHA-512`/`BLAKE3`, `HMAC`/`HKDF`, `ChaCha20-Poly1305`, and `Ed25519`/`X25519`.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_8_crypto_secure_mem` verifying Wycheproof/RFC vectors for `SHA-256`, `SHA-512`, `BLAKE3`, `HMAC-SHA256`, `HKDF-SHA256`, `ChaCha20-Poly1305`, `X25519`, and `Ed25519` (`REQ-STD-172`).
- Verify constant-time tag verification, `ChaCha20-Poly1305` tampered-ciphertext/AAD rejection with zeroed output, and `SecretBytes` `ZeroizeOnDrop` + redacted `Debug` formatting.
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_8_crypto_secure_mem` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T931-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T931/build` and `python tools/axtest.py --compiler build-snap-T931/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
