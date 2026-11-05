---
id: T058
title: E14.4 — dyn Trait object-safety checker, unsizing coercion & MIR/oracle dynamic dispatch
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T214, T566]
priority: 187
status: todo
attempts: 0
paths: [compiler/traits, compiler/mir, compiler/interp, tests/run/dyn, tests/ui/dyn]
locks: [compiler/syntax, compiler/hir, compiler/types, compiler/verify, compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-63-dyn-trait-vtables.md, tasks/0476, 0212]
covers: [REQ-CORE-3036, REQ-CORE-3037, REQ-CORE-3038, REQ-CORE-3039, REQ-CORE-3040]
---
# T058 — E14.4 — dyn Trait object-safety checker, unsizing coercion & MIR/oracle dynamic dispatch

## Goal
Implement `dyn Trait` object-safety verification, unsizing coercion (`view<T>` / `mut_view<T>` -> `view<dyn Trait>` / `mut_view<dyn Trait>`), MIR vtable construction/dispatch lowering, and oracle (`--interp`) dynamic dispatch per `spec/SPEC-63-dyn-trait-vtables.md`.

## Scope
- Implement object-safety verification in `compiler/traits` (`AX_DYN_NOT_OBJECT_SAFE`, diagnosing generic methods, `Self`-by-value parameters/returns, and associated constants when forming `dyn Trait`).
- Lower unsizing coercions to explicit MIR fat-pointer construction (`MirRvalue.UnsizeDyn` pairing the data pointer with the `(TypeId, TraitId)` vtable descriptor) and lower `dyn Trait` method calls to `MirTerminator.CallDyn` (or vtable slot projection + indirect call) in `compiler/mir`.
- Execute `dyn Trait` fat-pointer creation, method dispatch, and supertrait upcasting in `compiler/interp` (`--interp`).

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/dyn` verify `AX_DYN_NOT_OBJECT_SAFE` and capability lifetime tracking across `view<dyn Trait>` and `mut_view<dyn Trait>`.
- [ ] Run tests in `tests/run/dyn` verify polymorphic dispatch across multiple concrete types, `mut_view<dyn Trait>` state mutation, and default trait methods via `dyn Trait`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T058-report.md` with exact `## Files changed`.

## Out of scope
- Native LIR/x86-64 `.rdata` vtable emission (`T567`) and `Box<dyn Trait>` dynamic drop glue (`T568`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Roadmap epic E14.4 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; refined by T214 so `T058` covers object-safety, MIR unsizing/dispatch, and oracle execution while `T567`–`T568` cover native vtable emission and `Box<dyn Trait>` drop glue.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T058/build` and `python tools/axtest.py --compiler build-snap-T058/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 02:23:30 refined scope, phase (`P14-comptime-2-0-reflection-genera`), covers, and dependencies in T214 (P14 phase planning)
