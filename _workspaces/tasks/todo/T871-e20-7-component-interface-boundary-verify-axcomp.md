---
id: T871
title: E20.7 @component_interface & @plugin_export boundary verifier, cross-component ownership/capability/allocator guard & .axcomp emitter
phase: P20-build-system-package-ecosystem
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318, T867, T870]
priority: 221
status: todo
attempts: 0
paths: [compiler/component/interface, compiler/component/verify, tests/run/component_interface]
spec: [spec/SPEC-115-dynamic-components-plugins-hot-reload.md, spec/SPEC-114-abi-stability-versioning-binary-compat.md, 0104, tasks/0583, tasks/0584, tasks/0739, tasks/0856]
covers: [REQ-ECO-8734]
---
# T871 — E20.7 @component_interface & @plugin_export boundary verifier, cross-component ownership/capability/allocator guard & .axcomp emitter

## Goal
Implement the `@component_interface` and `@plugin_export` semantic verifier, cross-component ownership/capability/allocator isolation checks, and `.axcomp` binary descriptor section emitter per `spec/SPEC-115-dynamic-components-plugins-hot-reload.md`.

## Scope
- Implement `compiler/component/interface` lowering `@component_interface` trait/function tables and `@plugin_export` entry points into versioned Stable Axiom ABI vtables and emitting the `.axcomp` descriptor section (component identity, SemVer, `AbiFingerprint`, state schema hash, and capability manifest; `tasks/0584 §325.3-15`, `tasks/0856 §8-19`).
- Implement `compiler/component/verify` enforcing cross-component safety rules (`tasks/0584 §325.10-21`, `tasks/0856 §16-18`, `REQ-ECO-8734`): rejecting raw pointer escapes or unleased `view`/`mut_view` storage across a component boundary, requiring `ComponentHandle<T>` or allocator-tagged `ComponentBox<T>` for cross-component owned values, and validating `@hot_reload_state` schema migration signatures.
- Add positive and negative run/diagnostic tests in `tests/run/component_interface`.

## Acceptance
- [ ] Run and diagnostic tests in `tests/run/component_interface` verify `@component_interface` vtable generation, `.axcomp` descriptor emission, compile-time rejection of raw pointer/unleased view leaks across component boundaries, and `@hot_reload_state` schema verification in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T871-report.md` with exact `## Files changed`.

## Out of scope
- Runtime dynamic component loading, epoch lease tracking, and live hot-reload execution (`T872`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T871/build` and `python tools/axtest.py --compiler build-snap-T871/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
