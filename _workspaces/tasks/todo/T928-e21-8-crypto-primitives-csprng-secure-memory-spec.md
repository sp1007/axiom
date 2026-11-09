---
id: T928
title: E21.8 Canonical cryptographic hashes, CSPRNG, AEAD/signatures & constant-time secure memory specification (SPEC-127)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 238
status: todo
attempts: 0
paths: [spec/SPEC-127-crypto-primitives-secure-memory.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0467, tasks/0839]
covers: [REQ-STD-172, REQ-RT-179, REQ-RT-180, REQ-RT-181, REQ-RT-182, REQ-RT-184, REQ-RT-185, REQ-RT-186, REQ-RT-187, REQ-RT-756, REQ-RT-757, REQ-RT-758, REQ-RT-759, REQ-RT-760, REQ-RT-761, REQ-RT-762, REQ-RT-763, REQ-RT-764, REQ-RT-765, REQ-RT-766, REQ-RT-767, REQ-RT-768, REQ-RT-769, REQ-RT-770]
---
# T928 — E21.8 Canonical cryptographic hashes, CSPRNG, AEAD/signatures & constant-time secure memory specification (SPEC-127)

## Goal
Consolidate the canonical specification for Axiom's cryptographic primitives and secure memory model—constant-time operations, zeroize-on-drop secret buffers, OS CSPRNG vs seedable PRNG, cryptographic hashes/MACs/KDFs, AEAD, and Ed25519/X25519—into `spec/SPEC-127-crypto-primitives-secure-memory.md` (`AXS-CRY-*` rule IDs).

## Scope
- Write `spec/SPEC-127-crypto-primitives-secure-memory.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-CRY-NNN` rules.
- Specify constant-time comparison and selection (`CtChoice`, `ct_eq`, `ct_select`, barrier semantics preventing branch/table-lookup secret leakage; `tasks/0467 §3-14`) and `Secret<T>` / `SecretBytes` (`ZeroizeOnDrop` guaranteed not to be dead-store-eliminated on `Drop`, redacted `Debug`/`Display` formatting, no implicit `Copy`; `tasks/0467 §15-22`, `tasks/0839 §1-8`, `REQ-STD-172`).
- Specify the strict type separation between cryptographic random number generators (`CryptoRng` / `OsRng` backed by Windows `BCryptGenRandom` and Linux `getrandom`, failing closed on entropy failure) and deterministic seedable PRNGs (`SeedableRng` / `ChaCha20Rng` for reproducible simulation; `tasks/0467 §23-28`).
- Specify standard cryptographic hashes (`SHA-256`, `SHA-512`, `BLAKE3`, `SHA-384`, `SHA-3`/`SHAKE`/`Keccak`), message authentication and key derivation (`HMAC-SHA256`, `HKDF-SHA256`, `Argon2id`, `PBKDF2`), authenticated encryption (`ChaCha20-Poly1305`, `AES-128/256-GCM`, `AES-CTR/CBC/KW`), asymmetric primitives (`X25519`, `Ed25519`, `ECDSA P-256`, `RSA-PSS`), branchless constant-time `std.encoding.{base64, hex}`, and quarantined legacy cryptography (`std.crypto.legacy` with `Sha1`, `HmacSha1`, `Md5`, bit-sliced `Des`/`TripleDes`; `tasks/0839 §9-18`, `REQ-STD-172`, `ADR-0039`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-127-crypto-primitives-secure-memory.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-CRY-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T928-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of constant-time secret memory, RNG, hashes, AEAD, and Ed25519 (`T929`–`T930`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T928/build` and `python tools/axtest.py --compiler build-snap-T928/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
