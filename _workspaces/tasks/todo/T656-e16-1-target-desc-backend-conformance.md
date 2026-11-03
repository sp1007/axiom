---
id: T656
title: E16.1 — TargetDesc data tables, Machine IR verifier & target-independent LIR conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T655]
priority: 99
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_1_target_desc]
spec: [spec/SPEC-81-target-desc-isa-conformance.md, 0163, tasks/0518, tasks/0524, tasks/0784]
covers: [REQ-TGT-085, REQ-TGT-086, REQ-TGT-087, REQ-TGT-088, REQ-TGT-089, REQ-TGT-090, REQ-TGT-091, REQ-TGT-092, REQ-TGT-093, REQ-TGT-094, REQ-TGT-095, REQ-TGT-107, REQ-TGT-287, REQ-TGT-288, REQ-TGT-289, REQ-TGT-290, REQ-TGT-291, REQ-TGT-292, REQ-TGT-293, REQ-TGT-294, REQ-TGT-295]
---
# T656 — E16.1 — TargetDesc data tables, Machine IR verifier & target-independent LIR conformance suite

## Goal
Certify the E16.1 exit criterion (`ROADMAP.md` §3): declarative `TargetDesc` and `IsaTable` completeness, independent testability of instruction selection/register allocation/encoding, pre-encoding Machine IR verification, and target-independent LIR semantics preservation (`ABACKEND-61..100`).

## Scope
- Create `tests/conformance/p16/e16_1_target_desc` covering:
  - Declarative `TargetDesc` and `RegisterFile` inspection tests (register unit overlap, subregister alias resolution, caller/callee-saved sets, `TargetFingerprint` stability).
  - Independent stage tests for serialized Machine IR dumps (`--emit=lir`, `--emit=mc`), instruction selection, register allocation, legalizer expansion (checked overflow, atomics, volatile, strict FP), and encoding (`AMACHINE-96..100`).
  - Negative verifier tests proving that unavailable target features, illegal register classes, and unsupported atomic/width operations are rejected cleanly without silent miscompilation (`ABACKEND-65..70, 84..85`).
  - Optimization profile invariance (`-O0`, `-O1`, `-O2`, `-Oz`) differential tests against `--interp` proving that backend lowering never alters observable Axiom semantics (`AMACHINE-103..106`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_1_target_desc` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T656-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T654`–`T655`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:36:00 created by T216 (P16 phase planning)
