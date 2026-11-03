---
id: T556
title: E14.2 — Canonical compile-time reflection API, @derive framework & typed codegen boundary specification (SPEC-61)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T214, T550]
priority: 176
status: done
attempts: 1
paths: [spec/SPEC-61-reflection-derive.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-60-comptime-2-0.md, 0102, 0140, tasks/0343, tasks/0296, tasks/0433]
covers: [REQ-CTM-019, REQ-CTM-020, REQ-CTM-021, REQ-CTM-022, REQ-CTM-039, REQ-CTM-040, REQ-CORE-602, REQ-CORE-603, REQ-CORE-604, REQ-CORE-605, REQ-CORE-606, REQ-CORE-607, REQ-CORE-608, REQ-CORE-609, REQ-CORE-610, REQ-CORE-611, REQ-CORE-612, REQ-CORE-613, REQ-CORE-614, REQ-CORE-615, REQ-CORE-616, REQ-CORE-617, REQ-CORE-618, REQ-CORE-619, REQ-CORE-620, REQ-CORE-621]
started: 2026-11-03 11:17:37
finished: 2026-11-03 11:28:37
---
# T556 — E14.2 — Canonical compile-time reflection API, @derive framework & typed codegen boundary specification (SPEC-61)

## Goal
Define the canonical compile-time reflection data model (`TypeInfo`, `StructInfo`, `EnumInfo`, `FieldInfo`, `VariantInfo`, `TraitInfo`), the reflection-driven `@derive` framework, and the typed code generation boundary (prohibiting textual macros and arbitrary AST/HIR/MIR mutation) in `spec/SPEC-61-reflection-derive.md` (`AXS-RFL-*` rule IDs).

## Scope
- Write `spec/SPEC-61-reflection-derive.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-RFL-NNN` rules.
- Specify compile-time reflection (`type_info<T>() -> TypeInfo`) as the default zero-runtime-overhead introspection model, and explicit opt-in rules when runtime metadata is requested (`AMETA-24..39`, `AREFLECT-20..30`).
- Specify visibility and encapsulation rules (`AMETA-33..34`: reflection respects module privacy and cannot silently expose private fields across package boundaries), deterministic declaration-order field/variant enumeration, and layout query contracts (`size_of`, `align_of`, `offset_of` obeying `@repr` contracts).
- Specify the typed `@derive` framework (`AMETA-40..70`): `@derive(Trait)` executes a deterministic compile-time derive handler producing typed semantic declarations that re-enter normal name resolution, type checking, ownership, capability, and concurrency verification, with provenance tracking for diagnostics and no textual macro expansion.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-61-reflection-derive.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-RFL-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T556-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or `std` implementation (handled by `T557`–`T559`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:21:00 created by T214 (P14 phase planning)
- 2026-11-03 11:17:37 started (attempt 1) 
- 2026-11-03 11:28:37 accepted by QA -> done
