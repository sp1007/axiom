---
id: T925
title: E21.7 Encode/Decode traits, endian-explicit WireReader/WireWriter, varint & schema evolution codecs
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T924]
priority: 235
status: todo
attempts: 0
paths: [std/serde/core, std/serde/wire, std/serde/json, tests/run/std_serde_wire]
spec: [spec/SPEC-126-serialization-binary-data-model.md, tasks/0650, tasks/0742, tasks/0841]
covers: [REQ-STD-174, REQ-RT-138, REQ-RT-165, REQ-RT-716, REQ-RT-717, REQ-RT-718, REQ-RT-719, REQ-RT-720, REQ-RT-721, REQ-RT-722, REQ-RT-723, REQ-RT-724, REQ-RT-725, REQ-RT-726, REQ-RT-727, REQ-RT-728, REQ-RT-729, REQ-RT-730]
---
# T925 — E21.7 Encode/Decode traits, endian-explicit WireReader/WireWriter, varint & schema evolution codecs

## Goal
Implement `Encode`/`Decode` traits, endian-explicit `WireReader`/`WireWriter`, tagged schema-evolution binary codecs, and structured JSON serialization in `std.serde` per `spec/SPEC-126-serialization-binary-data-model.md`.

## Scope
- Implement `std/serde/core` (`Encode`, `Decode`, `Serializer`, `Deserializer`, `DecodeLimits` enforcing `max_depth`, `max_bytes`, and `max_collection_len` on untrusted inputs; `REQ-STD-174`, `REQ-RT-138`).
- Implement `std/serde/wire` (`WireWriter`, `WireReader`, `read_u16_le`/`be`, `read_u32_le`/`be`, `read_u64_le`/`be`, ZigZag + unsigned LEB128 varints, and tagged field-ID records supporting unknown-field skipping and default-field evolution across schema v1 ↔ v2; `tasks/0742 §19-28`, `tasks/0841 §6-14`).
- Implement `std/serde/json` (RFC 8259 compliant streaming JSON parser and canonical deterministic JSON writer with UTF-8 escape validation and exact number/string handling).
- Add run tests in `tests/run/std_serde_wire`.

## Acceptance
- [ ] Run tests in `tests/run/std_serde_wire` verify endian-explicit `WireReader`/`WireWriter`, LEB128/ZigZag boundary values, v1 ↔ v2 tagged schema evolution (unknown fields skipped, missing optional fields defaulted), `DecodeLimits` DoS protection on truncated/oversized inputs, and RFC 8259 JSON round-trips in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T925-report.md` with exact `## Files changed`.

## Out of scope
- Zero-copy binary views, checksums, compression, and CAS (`T926`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T925/build` and `python tools/axtest.py --compiler build-snap-T925/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
