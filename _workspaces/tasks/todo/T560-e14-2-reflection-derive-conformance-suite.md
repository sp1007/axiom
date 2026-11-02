---
id: T560
title: E14.2 — Reflection, typed codegen boundary & std derive conformance suite
phase: P14-comptime-2-0-reflection-genera
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T557, T558, T559]
priority: 180
status: todo
attempts: 0
paths: [tests/conformance/p14/e14_2_reflection_derive]
spec: [spec/SPEC-61-reflection-derive.md, tasks/0343, tasks/0433]
covers: [REQ-CORE-673, REQ-CORE-674, REQ-CORE-675, REQ-CORE-676, REQ-CORE-677, REQ-CORE-678, REQ-CORE-679, REQ-CORE-680, REQ-CORE-681, REQ-CORE-682]
---
# T560 — E14.2 — Reflection, typed codegen boundary & std derive conformance suite

## Goal
Certify E14.2 exit criteria with an end-to-end conformance suite covering compile-time reflection, visibility and layout boundaries, typed `@derive` verification, and reflection-based `derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` in `std`.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p14/e14_2_reflection_derive` covering:
  - compile-time `TypeInfo` queries across structs, enums, generics, and traits in declaration order;
  - negative tests for private cross-module reflection (`AX_REFLECT_PRIVATE_FIELD`), invalid `offset_of` on unspecified layouts, un-derivable field types (`AX_DERIVE_FIELD_BOUND`), and conflicting impls (`AX_DERIVE_CONFLICT`);
  - end-to-end differential (`--interp` and native) tests for reflection-driven `derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)`.

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p14/e14_2_reflection_derive` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T560-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T560/build` and `python tools/axtest.py --compiler build-snap-T560/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:21:00 created by T214 (P14 phase planning)
