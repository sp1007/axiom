---
id: T569
title: E14.4 — dyn Trait object safety, vtable layout & dynamic dispatch conformance suite
phase: P14-comptime-2-0-reflection-genera
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T058, T567, T568]
priority: 190
status: todo
attempts: 0
paths: [tests/conformance/p14/e14_4_dyn_trait]
spec: [spec/SPEC-63-dyn-trait-vtables.md, tasks/0476, 0212]
covers: [REQ-CORE-3049, REQ-CORE-3050, REQ-CORE-3051, REQ-CORE-3052]
---
# T569 — E14.4 — dyn Trait object safety, vtable layout & dynamic dispatch conformance suite

## Goal
Certify E14.4 exit criteria with an end-to-end conformance suite covering `dyn Trait` object-safety rules, `view<dyn Trait>` / `mut_view<dyn Trait>` / `Box<dyn Trait>` coercions, `.rdata` vtables, dynamic dispatch, and vtable-driven `Drop`.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p14/e14_4_dyn_trait` covering:
  - object-safety rejection diagnostics (`AX_DYN_NOT_OBJECT_SAFE`) for generic methods, `Self`-by-value returns/args, and associated constants;
  - capability lifetime enforcement on `view<dyn Trait>` and `mut_view<dyn Trait>` (preventing dangling trait-object views);
  - differential (`--interp` and native, `-O0` and `-O1`) execution of heterogeneous `Vec<Box<dyn Trait>>` and slice-of-`view<dyn Trait>` dispatch, supertrait upcasting, and deterministic destructor order on drop.

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p14/e14_4_dyn_trait` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T569-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T569/build` and `python tools/axtest.py --compiler build-snap-T569/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:23:30 created by T214 (P14 phase planning)
