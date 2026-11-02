---
id: T533
title: E13.7 — Module-relative bindings (@at(image("mod") + off)) host EXE + test DLL conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T531, T532]
priority: 182
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_7_module_relative]
spec: [spec/SPEC-56-module-relative-bindings.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0187, 0104, tasks/0336]
covers: [REQ-OWNER-005, REQ-FFI-042]
---
# T533 — E13.7 — Module-relative bindings (@at(image("mod") + off)) host EXE + test DLL conformance suite

## Goal
Certify the E13.7 exit criterion ("a test DLL loaded into a test host EXE calls host functions and reads host data through module-relative bindings; missing module → DllMain FALSE") for `REQ-OWNER-005`.

## Scope
- Build the end-to-end conformance suite in `tests/conformance/p13/e13_7_module_relative`:
  - A test host EXE (`game_host.exe`) with known functions and `@repr(C)` state whose module-relative RVAs are computed via `addr_of(item) - image_self()` (`REQ-OWNER-008`).
  - A test PE DLL (`mod_plugin.dll`) declaring `@at(image("game_host.exe") + RVA)` function and static overlays plus `@at(image_self() + RVA)` self-relative table overlays (`REQ-OWNER-005`), loaded dynamically into `game_host.exe`, calling host functions and mutating host state with ordinary syntax.
  - A negative test DLL (`bad_plugin.dll`) binding `@at(image("nonexistent_host.exe") + 0x1000)` where `LoadLibraryW` deterministically fails because `DllMain` returns `FALSE`.
- Verify matching behavior in `--interp` (via the oracle module map) and native Windows x64 execution.

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p13/e13_7_module_relative` pass in `--interp` and native execution (`0 WEAK-NATIVE`).
- [ ] Report `_workspaces/reports/T533-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T533/build` and `python tools/axtest.py --compiler build-snap-T533/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:06:00 created by T213 (P13 phase planning)
