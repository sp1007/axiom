---
id: T531
title: E13.7 — image("mod") / image_self() overlay expressions, load-time slot HIR/MIR lowering & oracle module-map
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T526, T527, T530]
priority: 180
status: todo
attempts: 0
paths: [compiler/hir, compiler/types, compiler/mir, compiler/interp, tests/ui/module_rel, tests/run/module_rel_oracle]
spec: [spec/SPEC-56-module-relative-bindings.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0187, 0104, tasks/0336]
covers: [REQ-OWNER-005, REQ-CAP-132]
---
# T531 — E13.7 — image("mod") / image_self() overlay expressions, load-time slot HIR/MIR lowering & oracle module-map

## Goal
Implement `image("name") + offset` and `image_self() + offset` overlay expressions in HIR, `typeck`, MIR slot lowering, and the MIR oracle (`--interp`) simulated module map (`ADR-0001 §5`, `REQ-OWNER-005`).

## Scope
- Typecheck `image("name")` and `image_self()` in `compiler/types` as hosted-profile module-base descriptors valid inside `@at(...)` / `@addr(...)` overlay declarations (`static`, `static mut`, `extern fn`) and runtime `usize` offset calculations (`addr_of(target) - image_self()`).
- Reject placements (initializers or function bodies) at `image("foreign") + offset` (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`), while permitting overlays with `@repr(C)` / primitive layout and valid alignment.
- Lower module-relative overlays in `compiler/mir` to load-time resolved pointer slots populated by a compiler-generated module init table, with indirect call/place dereferencing through the resolved slot.
- Add a simulated process module table in `compiler/interp` so `--interp` resolves `image("game.exe") + off` and `image_self() + off` against registered mock modules and reports deterministic module-init failure when a module is missing.

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/module_rel` verify `image("mod") + off` and `image_self() + off` overlay rules and reject foreign placements.
- [ ] Oracle tests in `tests/run/module_rel_oracle` verify calling functions, reading/writing `@repr(C)` statics across simulated modules, computing `addr_of(sym) - image_self()`, and failing cleanly when a required module is absent.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T531-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T531/build` and `python tools/axtest.py --compiler build-snap-T531/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:06:00 created by T213 (P13 phase planning)
