---
id: T949
title: E21.8 — Quarantined legacy crypto std.crypto.legacy (SHA-1, HMAC-SHA1, MD5, bit-sliced DES/3DES)
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T948]
priority: 251
status: todo
attempts: 0
paths: [std/crypto/legacy, tests/run/std_crypto_legacy]
spec: [spec/SPEC-127-crypto-primitives-secure-memory.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-172]
---
# T949 — E21.8 — Quarantined legacy crypto std.crypto.legacy (SHA-1, HMAC-SHA1, MD5, bit-sliced DES/3DES)

## Goal
Implement quarantined legacy cryptographic primitives in `std.crypto.legacy` (`Sha1`, `HmacSha1`, `Md5`, bit-sliced constant-time `Des` / `TripleDes`) required strictly for RFC 6455 WebSocket handshakes, RFC 6238 TOTP 2FA, Git object hashing, and legacy HSM/PKCS#12 compatibility.

## Scope
- Implement `std/crypto/legacy`:
  * `Sha1` (RFC 3174) and `HmacSha1` required for WebSocket `Sec-WebSocket-Accept` derivation and TOTP two-factor authentication tokens.
  * `Md5` (RFC 1321) for checksumming and legacy protocol negotiation.
  * `Des` and `TripleDes` (`TdesEde3Cbc`, 3DES) implemented strictly with **constant-time bit-sliced S-boxes** (ensuring zero lookup-table cache-line timing side channels).
- Isolate all legacy symbols within the `std.crypto.legacy` namespace so they are never imported by wildcard modern crypto imports.
- Tag all legacy exports with `@deprecated(since = "1.0.0", note = "Legacy algorithm quarantined for protocol backward compatibility; use std.crypto for modern security")`.

## Acceptance
- [ ] Run tests in `tests/run/std_crypto_legacy` verify official FIPS and RFC test vectors for SHA-1, HMAC-SHA1, MD5, DES, and Triple-DES across `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] WebSocket handshake verification test proves correct key derivation matching RFC 6455 test vectors.
- [ ] Constant-time bit-sliced DES execution verifies absence of secret-dependent table lookup addresses.
- [ ] Static analysis verification confirms that unauthorized use of legacy algorithms in modern default security sinks without `@suppress` is detected and rejected with `AX_VERIFY_WEAK_CRYPTO_PRIMITIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T949-report.md` with exact `## Files changed`.

## Out of scope
- Use of legacy algorithms in modern default security settings (flagged by `AX_VERIFY_WEAK_CRYPTO_PRIMITIVE` in `E17.9`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T949/build` and `python tools/axtest.py --compiler build-snap-T949/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:25:00 created by axiom-architect (ADR-0039 P21 quarantined legacy crypto expansion)
