---
id: T929
title: E21.8 Constant-time CtEq/CtSelect, ZeroizeOnDrop SecretBuf<T>, OS CSPRNG & deterministic ChaCha20Rng
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T928]
priority: 239
status: todo
attempts: 0
paths: [std/crypto/ct, std/crypto/secret, std/crypto/rng, tests/run/std_crypto_secret_rng]
spec: [spec/SPEC-127-crypto-primitives-secure-memory.md, tasks/0467, tasks/0839]
covers: [REQ-STD-172, REQ-RT-181, REQ-RT-182, REQ-RT-771, REQ-RT-772, REQ-RT-773, REQ-RT-774, REQ-RT-775, REQ-RT-776, REQ-RT-777, REQ-RT-778, REQ-RT-779, REQ-RT-780, REQ-RT-781, REQ-RT-782, REQ-RT-783, REQ-RT-784, REQ-RT-785]
---
# T929 — E21.8 Constant-time CtEq/CtSelect, ZeroizeOnDrop SecretBuf<T>, OS CSPRNG & deterministic ChaCha20Rng

## Goal
Implement constant-time primitives (`CtChoice`, `CtEq`, `CtSelect`), `ZeroizeOnDrop` `SecretBuf<T>`/`SecretBytes`, `OsRng` CSPRNG, and deterministic `ChaCha20Rng` in `std.crypto` per `spec/SPEC-127-crypto-primitives-secure-memory.md`.

## Scope
- Implement `std/crypto/ct` (`CtChoice`, `CtEq`, `CtSelect`, `ct_eq_bytes`, `ct_select_u8`/`u32`/`u64`, and value barrier helpers preventing branch conversion; `tasks/0467 §5-14`).
- Implement `std/crypto/secret` (`zeroize_bytes`, `Zeroize`, `SecretBytes`, `SecretKey32` with volatile/barrier wipe on `Drop`, optional page locking hook, and redacted debug output `"Secret([REDACTED])"`; `tasks/0467 §15-22`, `REQ-STD-172`).
- Implement `std/crypto/rng` (`RngCore`, `CryptoRng` marker trait, `OsRng` calling `BCryptGenRandom` on Windows and `getrandom` on Linux, and RFC 8439 `ChaCha20Rng` deterministic CSPRNG with explicit 32-byte seed; `tasks/0467 §23-28`).
- Add run tests in `tests/run/std_crypto_secret_rng`.

## Acceptance
- [ ] Run tests in `tests/run/std_crypto_secret_rng` verify `ct_eq_bytes`/`CtSelect` behavior across matching and mismatching slices, `SecretBytes` zeroization on `Drop` and redacted formatting, `OsRng` non-trivial entropy fill, and `ChaCha20Rng` RFC 8439 test vectors in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T929-report.md` with exact `## Files changed`.

## Out of scope
- SHA-256/512, BLAKE3, HMAC/HKDF, ChaCha20-Poly1305 AEAD, and Ed25519/X25519 (`T930`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T929/build` and `python tools/axtest.py --compiler build-snap-T929/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
