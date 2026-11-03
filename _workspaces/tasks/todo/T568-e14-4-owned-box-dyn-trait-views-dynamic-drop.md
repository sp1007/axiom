---
id: T568
title: E14.4 — Owned Box<dyn Trait>, view<dyn Trait>, mut_view<dyn Trait> & dynamic drop glue integration
phase: P14-comptime-2-0-reflection-genera
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T058, T567]
priority: 189
status: todo
attempts: 0
paths: [std/box, compiler/mir/drop.ax, tests/run/dyn_box, tests/selfhost]
spec: [spec/SPEC-63-dyn-trait-vtables.md, spec/SPEC-12-drop.md, 0212]
covers: [REQ-CORE-3045, REQ-CORE-3046, REQ-CORE-3047, REQ-CORE-3048]
---
# T568 — E14.4 — Owned Box<dyn Trait>, view<dyn Trait>, mut_view<dyn Trait> & dynamic drop glue integration

## Goal
Support owned `Box<dyn Trait>` trait objects, reborrowing to `view<dyn Trait>` / `mut_view<dyn Trait>`, heterogeneous collections (`Vec<Box<dyn Trait>>`), and vtable-driven `drop_in_place` + sized deallocation in `compiler/mir/drop.ax` and `std/box`.

## Scope
- Support unsizing `Box<T>` -> `Box<dyn Trait>` and borrowing `view(box_dyn)` -> `view<dyn Trait>` / `mut_view(box_dyn)` -> `mut_view<dyn Trait>` in `std/box` and `compiler/mir/drop.ax`.
- Implement dynamic drop elaboration for `Box<dyn Trait>`: invoke the vtable's `drop_in_place(data_ptr)` slot to run the underlying concrete type's destructor, then deallocate the heap block using the vtable's `(size, align)` metadata when `size > 0`.

## Acceptance
- [ ] Differential (`--interp` and native) tests in `tests/run/dyn_box` verify `Box<dyn Trait>` creation, heterogeneous `Vec<Box<dyn Trait>>` dispatch, `mut_view<dyn Trait>` reborrowing, and exact destructor invocation + heap deallocation when `Box<dyn Trait>` values are dropped or overwritten.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T568-report.md` with exact `## Files changed`.

## Out of scope
- E14.4 conformance suite (`T569`) and index auto-deref (`E14.5`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T568/build` and `python tools/axtest.py --compiler build-snap-T568/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:23:30 created by T214 (P14 phase planning)
