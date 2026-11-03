---
id: T557
title: E14.2 — Compile-time TypeInfo reflection intrinsics, visibility enforcement & layout queries
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T552, T556]
priority: 177
status: todo
attempts: 0
paths: [compiler/sema/reflect.ax, compiler/interp/reflect.ax, tests/run/reflect, tests/ui/reflect]
spec: [spec/SPEC-61-reflection-derive.md, tasks/0343, tasks/0296, tasks/0433]
covers: [REQ-CTM-043, REQ-CTM-045, REQ-CORE-622, REQ-CORE-623, REQ-CORE-624, REQ-CORE-625, REQ-CORE-626, REQ-CORE-627, REQ-CORE-628, REQ-CORE-629, REQ-CORE-630, REQ-CORE-631, REQ-CORE-632, REQ-CORE-633, REQ-CORE-634, REQ-CORE-635, REQ-CORE-636, REQ-CORE-637, REQ-CORE-638, REQ-CORE-639]
---
# T557 — E14.2 — Compile-time TypeInfo reflection intrinsics, visibility enforcement & layout queries

## Goal
Implement compile-time type reflection intrinsics (`type_info<T>()`, `type_name<T>()`, `fields_of<T>()`, `variants_of<T>()`, `attributes_of<T>()`, `offset_of<T, F>()`, `implements<T, Trait>()`) in `compiler/sema/reflect.ax` and `compiler/interp/reflect.ax`.

## Scope
- Implement deterministic compile-time reflection intrinsics returning structured `TypeInfo` descriptors for primitives, structs, enums, tuples, arrays, slices, views, pointers, functions, and traits in declaration order (`AREFLECT-26..27`).
- Enforce module visibility and representation rules on reflection queries: reject cross-module private field access (`AX_REFLECT_PRIVATE_FIELD`) unless invoked by a same-module or `@derive` authority on the target type's own definition, and restrict `offset_of` to fields with well-defined layout (`AMETA-31..37`).
- Ensure compile-time reflection descriptors exist purely at compile time and emit zero runtime type metadata unless explicitly materialized (`AMETA-25..28, 38..39`).

## Acceptance
- [ ] Positive and negative tests in `tests/run/reflect` and `tests/ui/reflect` verify `type_info<T>()`, declaration-order field/variant enumeration, `implements<T, Trait>()`, `offset_of`, visibility enforcement (`AX_REFLECT_PRIVATE_FIELD`), and zero runtime overhead when unused.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T557-report.md` with exact `## Files changed`.

## Out of scope
- Typed `@derive` expansion engine (`T558`) and `std.reflect` / `std.derive` library (`T559`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T557/build` and `python tools/axtest.py --compiler build-snap-T557/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:21:00 created by T214 (P14 phase planning)
