---
id: T654
title: E16.1 — Declarative TargetDesc registry, RegisterFile subregister/alias tables & ABI table engine
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T066, T313, T653]
priority: 97
status: todo
attempts: 0
paths: [compiler/target/desc, compiler/abi/table, tests/run/target_desc, tests/selfhost/abi]
spec: [spec/SPEC-81-target-desc-isa-conformance.md, 0163, tasks/0518, tasks/0524, tasks/0784]
covers: [REQ-TGT-012, REQ-TGT-013, REQ-TGT-014, REQ-TGT-015, REQ-TGT-016, REQ-TGT-017, REQ-TGT-018, REQ-TGT-019, REQ-TGT-020, REQ-TGT-021, REQ-TGT-054, REQ-TGT-055, REQ-TGT-056]
---
# T654 — E16.1 — Declarative TargetDesc registry, RegisterFile subregister/alias tables & ABI table engine

## Goal
Implement the data-driven `TargetDesc` registry, hierarchical `RegisterFile` (register units, classes, subregister aliases, reserved vs allocatable sets), `TargetFeatureSet` validation, and table-driven `CallConvDesc` ABI engine in `compiler/target/desc` and `compiler/abi/table`.

## Scope
- Implement declarative `TargetDesc` records and lookup by canonical triple (`x86_64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `aarch64-android`, `aarch64-windows`, `wasm32`, `riscv64-linux`), computing a deterministic `TargetFingerprint` for incremental/codegen caches in `compiler/target/desc`.
- Implement `RegisterFile` data tables with explicit `RegUnit` bitmasks, subregister/superregister alias queries, register class membership, reserved architectural registers, and caller/callee-saved sets (`AMACHINE-23..30`).
- Implement explicit `TargetFeatureSet` dependency graphs and compile-time feature gating (`AMACHINE-65..67`: never silently emit instructions for unavailable CPU features or insert implicit runtime dispatch).
- Implement the table-driven `CallConvDesc` ABI classification engine in `compiler/abi/table` so calling conventions are driven by declarative parameter/return register lists, aggregate classification rules, stack alignment, shadow-space/red-zone sizes, and `sret` conventions rather than scattered target `if` chains (`0163 §1`).
- Add unit and selfhost tests in `tests/run/target_desc` and `tests/selfhost/abi`.

## Acceptance
- [ ] All registered `TargetDesc` entries pass structural invariant validation (register unit disjointness, alias symmetry, ABI register class consistency, feature DAG acyclicity).
- [ ] Positive and negative tests in `tests/run/target_desc` and `tests/selfhost/abi` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); outputs deterministic across runs.
- [ ] Report `_workspaces/reports/T654-report.md` with exact `## Files changed`.

## Out of scope
- Declarative `IsaTable` instruction descriptors and pre-encoding Machine IR verification (`T655`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:36:00 created by T216 (P16 phase planning)
