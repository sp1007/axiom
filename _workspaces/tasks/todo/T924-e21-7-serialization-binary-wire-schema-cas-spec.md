---
id: T924
title: E21.7 Canonical serialization, binary wire framing, schema evolution & compression/CAS specification (SPEC-126)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 234
status: todo
attempts: 0
paths: [spec/SPEC-126-serialization-binary-data-model.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0650, tasks/0742, tasks/0841, tasks/0842, tasks/0844]
covers: [REQ-STD-174, REQ-STD-175, REQ-RT-138, REQ-RT-164, REQ-RT-165, REQ-RT-701, REQ-RT-702, REQ-RT-703, REQ-RT-704, REQ-RT-705, REQ-RT-706, REQ-RT-707, REQ-RT-708, REQ-RT-709, REQ-RT-710, REQ-RT-711, REQ-RT-712, REQ-RT-713, REQ-RT-714, REQ-RT-715]
---
# T924 — E21.7 Canonical serialization, binary wire framing, schema evolution & compression/CAS specification (SPEC-126)

## Goal
Consolidate the canonical specification for Axiom's serialization and binary data model—`Encode`/`Decode` contracts, explicit-endian wire framing, forward/backward schema evolution, zero-copy validated binary views, and lossless compression / content-addressed storage—into `spec/SPEC-126-serialization-binary-data-model.md` (`AXS-SER-*` rule IDs).

## Scope
- Write `spec/SPEC-126-serialization-binary-data-model.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SER-NNN` rules.
- Specify the strict separation between in-memory language representation (`@repr(Axiom)` / `@repr(C)`) and external wire/storage representation (`tasks/0650 §3-14`, `tasks/0742 §2-18`, `tasks/0841 §1-15`, `REQ-STD-174`, `REQ-RT-138`): never raw-memcpying arbitrary structs with padding, pointers, or handles to disk/network.
- Specify `Encode`/`Decode` traits, `WireReader`/`WireWriter` with explicit endianness (`LittleEndian`, `BigEndian`), LEB128/varint, length-bounded decoding budgets (`max_depth`, `max_bytes`, `max_elements` to prevent OOM/DoS on untrusted inputs), tagged field ids for forward/backward-compatible schema evolution, and canonical JSON/binary codecs (`tasks/0742 §19-32`).
- Specify `@zerocopy` Pod/ByteView validation rules (alignment, no padding bytes, valid discriminant check before constructing a typed `view<T>`), integrity checksums (`CRC32C`, `XXH64`), lossless compression (`DEFLATE`/`Zlib`, `LZ4`), and content-addressed storage (`CasStore`, Merkle blob/tree digests; `tasks/0842 §1-14`, `tasks/0844 §1-10`, `REQ-STD-175`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-126-serialization-binary-data-model.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SER-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T924-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of wire codecs, zero-copy views, compression, and CAS (`T925`–`T926`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T924/build` and `python tools/axtest.py --compiler build-snap-T924/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
