---
id: T927
title: E21.7 Serialization, binary wire model, schema evolution, compression & CAS conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T926]
priority: 237
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_7_serde_binary_data]
spec: [spec/SPEC-126-serialization-binary-data-model.md, tasks/0650, tasks/0742, tasks/0841, tasks/0842, tasks/0844]
covers: [REQ-STD-174, REQ-STD-175, REQ-RT-138, REQ-RT-164, REQ-RT-165, REQ-RT-746, REQ-RT-747, REQ-RT-748, REQ-RT-749, REQ-RT-750, REQ-RT-751, REQ-RT-752, REQ-RT-753, REQ-RT-754, REQ-RT-755]
---
# T927 — E21.7 Serialization, binary wire model, schema evolution, compression & CAS conformance suite

## Goal
Certify E21.7 exit criteria with an end-to-end conformance suite covering `Encode`/`Decode`, endian-explicit wire framing, v1 ↔ v2 schema evolution, zero-copy views, `CRC32C`/`XXH64`, `DEFLATE`/`LZ4` compression, and `CasStore`.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_7_serde_binary_data` verifying deterministic wire encoding across types, v1/v2 forward and backward schema compatibility (`REQ-STD-174`), and malformed/truncated wire frame rejection without panics or OOM.
- Verify `FromBytes`/`AsBytes` zero-copy view alignment checks, `CRC32C`/`XXH64` bit-flip detection, `DEFLATE`/`LZ4` corpus round-tripping, and `CasStore` Merkle verification (`REQ-STD-175`).
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_7_serde_binary_data` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T927-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T927/build` and `python tools/axtest.py --compiler build-snap-T927/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
