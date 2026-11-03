---
id: T559
title: E14.2 — Standard library std.reflect API & reflection-driven derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T558]
priority: 179
status: todo
attempts: 0
paths: [std/reflect, std/derive, tests/run/derive_std, tests/selfhost]
spec: [spec/SPEC-61-reflection-derive.md, tasks/0343, tasks/0296, tasks/0433]
covers: [REQ-CORE-660, REQ-CORE-661, REQ-CORE-662, REQ-CORE-663, REQ-CORE-664, REQ-CORE-665, REQ-CORE-666, REQ-CORE-667, REQ-CORE-668, REQ-CORE-669, REQ-CORE-670, REQ-CORE-671, REQ-CORE-672]
---
# T559 — E14.2 — Standard library std.reflect API & reflection-driven derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize)

## Goal
Implement the `std.reflect` compile-time reflection library and reflection-driven `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` implementations in `std/reflect` and `std/derive`, satisfying the P14 roadmap exit criterion.

## Scope
- Implement `std/reflect` (`TypeInfo`, `TypeKind`, `FieldInfo`, `VariantInfo`, `AttributeInfo`, `StructLayout`) wrapping the compile-time reflection intrinsics from `T557`.
- Implement reflection-driven derive generators in `std/derive` for `Debug`, `Eq`, `Ord`, `Hash`, `Clone`, `Default`, and structured `Serialize`/`Deserialize` (supporting field/variant attributes such as `@rename`, `@skip`, `@default` inspected at compile time via `attributes_of<T>()`).
- Verify that reflection-generated `Debug`, `Eq`, `Ord`, `Hash`, and `Serialize`/`Deserialize` implementations specialize down to direct field-by-field code with zero runtime reflection table overhead.

## Acceptance
- [ ] Differential (`--interp` and native) tests in `tests/run/derive_std` verify `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` on structs, generic structs, fieldless enums, and payload enums, including `@rename`/`@skip`/`@default` field attributes.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T559-report.md` with exact `## Files changed`.

## Out of scope
- E14.2 conformance suite (`T560`) and generators (`E14.3`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T559/build` and `python tools/axtest.py --compiler build-snap-T559/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:21:00 created by T214 (P14 phase planning)
