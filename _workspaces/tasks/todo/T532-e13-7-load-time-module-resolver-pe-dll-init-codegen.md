---
id: T532
title: E13.7 — Load-time module resolver, indirect slot codegen & PE DLL/EXE initialiser failure hooks (REQ-OWNER-005)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T528, T531, T751]
priority: 181
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, compiler/link, tests/link/module_rel_dll, tests/selfhost]
spec: [spec/SPEC-56-module-relative-bindings.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0187, 0104, tasks/0336]
covers: [REQ-OWNER-005, REQ-FFI-119]
---
# T532 — E13.7 — Load-time module resolver, indirect slot codegen & PE DLL/EXE initialiser failure hooks (REQ-OWNER-005)

## Goal
Lower `image("mod") + offset` and `image_self() + offset` module-relative bindings to native x86-64 load-time slots initialized by the PE DLL (`DllMain`) and EXE startup initialisers of `T751` (`ADR-0001 §5–6`, `REQ-OWNER-005`).

## Scope
- Emit `.data` slot tables and descriptor metadata in `compiler/lir`, `compiler/target/x64`, and `compiler/obj` for every `@at(image("mod") + offset)` and `@at(image_self() + offset)` binding.
- Wire the module-relative binding resolver into the generated PE DLL `DllMain` (`DLL_PROCESS_ATTACH`) and EXE startup sequence (`compiler/link`, building on `T751`): resolve `image_self()` via `__ImageBase` and `image("mod")` via `GetModuleHandleW`, fill every slot with `base + offset`, and if any target module is not loaded, immediately return `FALSE` from `DllMain` (causing `LoadLibraryW` to fail cleanly) or abort EXE startup.
- Lower calls and static field accesses on module-relative overlays to indirect loads/calls through their resolved `.data` slots, treating foreign DLL slots as open-world barriers (`REQ-FFI-119`).

## Acceptance
- [ ] Native tests in `tests/link/module_rel_dll` compile a host EXE and a plugin PE DLL (`--kind dll`), verify that `image("host.exe") + off` and `image_self() + off` resolve at `LoadLibraryW` attach time, and verify that `LoadLibraryW` returns `NULL` (`DllMain` returns `FALSE`) when the DLL binds to a non-existent module `"missing_mod.dll"`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T532-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T532/build` and `python tools/axtest.py --compiler build-snap-T532/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:06:00 created by T213 (P13 phase planning)
