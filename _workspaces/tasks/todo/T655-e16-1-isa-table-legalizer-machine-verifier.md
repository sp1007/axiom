---
id: T655
title: E16.1 — Table-driven ISA instruction descriptors, legalizer hooks & pre-encoding Machine IR verifier
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T654]
priority: 98
status: todo
attempts: 0
paths: [compiler/target/isa, compiler/backend/verify_mc, tests/mc/isa_table, tests/selfhost/backend, tests/selfhost/isel]
spec: [spec/SPEC-81-target-desc-isa-conformance.md, 0162, 0163, tasks/0518, tasks/0520, tasks/0524, tasks/0784]
covers: [REQ-TGT-022, REQ-TGT-023, REQ-TGT-024, REQ-TGT-025, REQ-TGT-026, REQ-TGT-027, REQ-TGT-028, REQ-TGT-029, REQ-TGT-030, REQ-TGT-031, REQ-TGT-032, REQ-TGT-033, REQ-TGT-034, REQ-TGT-035, REQ-TGT-036, REQ-TGT-044, REQ-TGT-045, REQ-TGT-046, REQ-TGT-047, REQ-TGT-048, REQ-TGT-049, REQ-TGT-050, REQ-TGT-051, REQ-TGT-052, REQ-TGT-053, REQ-TGT-057, REQ-TGT-058, REQ-TGT-108, REQ-TGT-109]
---
# T655 — E16.1 — Table-driven ISA instruction descriptors, legalizer hooks & pre-encoding Machine IR verifier

## Goal
Implement declarative `IsaTable` instruction descriptors, semantic-preserving target legalization hooks, and the pre-encoding Machine IR verifier in `compiler/target/isa` and `compiler/backend/verify_mc`.

## Scope
- Implement declarative `IsaTable` instruction definitions in `compiler/target/isa` (`tasks/0784 §562.17–25`): operand kinds (register classes, immediate width/range predicates, target addressing modes), explicit implicit register defs/uses (`RAX:RDX` for `idiv`, `RCX` for shifts, `NZCV`/`EFLAGS` condition-code defs/uses, call ABI clobber masks), side-effect flags (load, store, atomic, volatile, trap, barrier, branch, call, return), and required `TargetFeature` masks.
- Implement the target legalizer framework in `compiler/target/isa` (`AMACHINE-35..45`, `ABACKEND-64..70`): legal expansion of narrow/wide integer ops, checked arithmetic overflow preservation, strict IEEE-754 floating-point preservation, atomic/volatile/memory-ordering preservation (never silently lowering unsupported atomics to ordinary loads/stores), and explicit panic vs hardware-trap separation.
- Implement the target-parameterized Machine IR verifier in `compiler/backend/verify_mc` (`AMACHINE-68..69`, `ABACKEND-81`): verify before encoding that every instruction's operands match `IsaTable` register classes and addressing modes, no virtual registers remain after allocation, reserved registers are never clobbered illegally, condition-code and implicit-register liveness is respected, stack alignment holds at every call site, and every instruction's required target features are enabled in `TargetDesc`.
- Add positive and negative tests in `tests/mc/isa_table`, `tests/selfhost/backend`, and `tests/selfhost/isel`.

## Acceptance
- [ ] `compiler/backend/verify_mc` runs before instruction encoding on all targets and rejects malformed Machine IR (wrong register class, unexpanded illegal op, missing target feature, unallocated vreg, misaligned call frame) with deterministic diagnostics before reaching the encoder.
- [ ] Positive and negative tests in `tests/mc/isa_table`, `tests/selfhost/backend`, and `tests/selfhost/isel` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T655-report.md` with exact `## Files changed`.

## Out of scope
- Target-specific AArch64, WASM32, and RISC-V64 backends (`E16.3`, `E16.6`, `E16.7`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:36:00 created by T216 (P16 phase planning)
