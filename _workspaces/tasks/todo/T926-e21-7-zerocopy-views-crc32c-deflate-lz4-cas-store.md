---
id: T926
title: E21.7 Zero-copy validated binary views, CRC32C/XXH64 checksums, DEFLATE/LZ4 compression & CAS store
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T924, T925]
priority: 236
status: todo
attempts: 0
paths: [std/serde/zerocopy, std/compress, std/cas, tests/run/std_serde_compress_cas]
spec: [spec/SPEC-126-serialization-binary-data-model.md, tasks/0650, tasks/0841, tasks/0842, tasks/0844]
covers: [REQ-STD-174, REQ-STD-175, REQ-RT-164, REQ-RT-731, REQ-RT-732, REQ-RT-733, REQ-RT-734, REQ-RT-735, REQ-RT-736, REQ-RT-737, REQ-RT-738, REQ-RT-739, REQ-RT-740, REQ-RT-741, REQ-RT-742, REQ-RT-743, REQ-RT-744, REQ-RT-745]
---
# T926 — E21.7 Zero-copy validated binary views, CRC32C/XXH64 checksums, DEFLATE/LZ4 compression & CAS store

## Goal
Implement validated zero-copy binary views (`FromBytes`/`AsBytes`), `CRC32C`/`XXH64` frame checksums, native `DEFLATE`/`LZ4` compression, and content-addressed storage (`CasStore`) per `spec/SPEC-126-serialization-binary-data-model.md`.

## Scope
- Implement `std/serde/zerocopy` (`FromBytes`, `AsBytes`, `Unaligned<T>`, `try_ref_from_bytes<T>(buf: view<u8>) -> Result<view<T>, ZeroCopyError>` checking alignment, size, and layout invariants before borrowing; plus `crc32c` and `xxh64` frame integrity checksums; `tasks/0650 §15-22`, `tasks/0841 §10-15`, `REQ-STD-174`).
- Implement `std/compress` (pure-Axiom lossless `lz4` block/frame compressor & decompressor and RFC 1951/1952 `deflate`/`gzip` compressor & decompressor with bounded output limits preventing zip-bomb exhaustion; `tasks/0842 §3-9`, `REQ-STD-175`).
- Implement `std/cas` (`ContentHash`, chunked Merkle tree builder, and deduplicating `CasStore` with corrupt-blob detection on read; `tasks/0842 §10-14`, `tasks/0844 §1-10`, `REQ-STD-175`).
- Add run tests in `tests/run/std_serde_compress_cas`.

## Acceptance
- [ ] Run tests in `tests/run/std_serde_compress_cas` verify `try_ref_from_bytes` alignment/length rejection, `CRC32C`/`XXH64` standard test vectors (`"123456789"`), `LZ4` and `DEFLATE`/`gzip` round-trips + zip-bomb budget rejection, and `CasStore` Merkle deduplication/tamper rejection in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T926-report.md` with exact `## Files changed`.

## Out of scope
- Cryptographic AEAD and signatures (`E21.8`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T926/build` and `python tools/axtest.py --compiler build-snap-T926/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
