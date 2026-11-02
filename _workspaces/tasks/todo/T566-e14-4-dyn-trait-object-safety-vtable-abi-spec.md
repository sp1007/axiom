---
id: T566
title: E14.4 — Canonical dyn Trait object safety, fat-pointer coercion & vtable ABI specification (SPEC-63)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T214]
priority: 186
status: todo
attempts: 0
paths: [spec/SPEC-63-dyn-trait-vtables.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, tasks/0476, 0212]
covers: [REQ-CORE-3031, REQ-CORE-3032, REQ-CORE-3033, REQ-CORE-3034, REQ-CORE-3035]
---
# T566 — E14.4 — Canonical dyn Trait object safety, fat-pointer coercion & vtable ABI specification (SPEC-63)

## Goal
Define the canonical object-safety rules for `dyn Trait`, two-word fat-pointer representation (`data_ptr`, `vtable_ptr`) for `view<dyn Trait>`, `mut_view<dyn Trait>`, and `Box<dyn Trait>`, unsizing coercions, and vtable layout/drop ABI in `spec/SPEC-63-dyn-trait-vtables.md` (`AXS-DYN-*` rule IDs).

## Scope
- Write `spec/SPEC-63-dyn-trait-vtables.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-DYN-NNN` rules.
- Specify `dyn Trait` object-safety rules (`AX_DYN_NOT_OBJECT_SAFE`): every dispatchable method must take a receiver (`view<Self>`, `mut_view<Self>`, or `Box<Self>`), must not have generic type parameters, must not mention `Self` in value position outside the receiver, and the trait must not have associated constants or `Self: Sized` requirements (`0212`, `tasks/0476 §217.49-50`).
- Specify explicit and coercion-site unsizing from `view<T>` -> `view<dyn Trait>`, `mut_view<T>` -> `mut_view<dyn Trait>`, and `Box<T>` -> `Box<dyn Trait>`, preserving capability lifetimes and ownership without object headers on concrete types (`AMIR-60..63`).
- Specify the canonical vtable layout (`drop_in_place` fn ptr, `size: usize`, `align: usize`, supertrait vtable slots, and declaration-ordered method slots) and calling convention across `--interp` and native x86-64.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-63-dyn-trait-vtables.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-DYN-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T566-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or library implementation (handled by `T058`, `T567`, `T568`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:23:30 created by T214 (P14 phase planning)
