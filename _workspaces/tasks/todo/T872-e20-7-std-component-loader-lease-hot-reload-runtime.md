---
id: T872
title: E20.7 std.component dynamic plugin loader, version/capability negotiator, epoch lease table & state-hand-off hot-reload runtime
phase: P20-build-system-package-ecosystem
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318, T870, T871]
priority: 222
status: todo
attempts: 0
paths: [std/component/loader, std/component/hot_reload, tests/run/component_hot_reload]
spec: [spec/SPEC-115-dynamic-components-plugins-hot-reload.md, 0104, tasks/0583, tasks/0584, tasks/0739, tasks/0856]
covers: [REQ-ECO-8734]
---
# T872 — E20.7 std.component dynamic plugin loader, version/capability negotiator, epoch lease table & state-hand-off hot-reload runtime

## Goal
Implement the `std.component` dynamic component discovery/loader, load-time ABI/version/capability negotiator, generational handle and epoch lease tracker, and state-migrating hot-reload runtime per `spec/SPEC-115-dynamic-components-plugins-hot-reload.md`.

## Scope
- Implement `std/component/loader` discovering and loading native Axiom component artifacts (`.dll`/`.so`/`.dylib`), reading `.axcomp` metadata before executing component init code, verifying `AbiFingerprint`, SemVer compatibility, and granted host capabilities, and binding `@component_interface` dispatch tables (`tasks/0584 §325.6-19`, `tasks/0856 §8-24`, `REQ-ECO-8734`).
- Implement `std/component/hot_reload` providing generational `ComponentHandle<T>` tables, epoch lease reference counting (refusing physical library unload while any lease or borrow is active; `tasks/0584 §325.19-21`), and the transactional hot-reload state machine (`Quiesce` → `ExportState` → `LoadNewEpoch` → `MigrateState` → `Resume` with automatic rollback to the previous epoch on schema/migration failure; `tasks/0584 §325.22-24`).
- Add end-to-end plugin load, unload-guard, and hot-reload state migration tests in `tests/run/component_hot_reload`.

## Acceptance
- [ ] Run tests in `tests/run/component_hot_reload` verify dynamic plugin discovery/loading, ABI/capability mismatch rejection prior to init, active-lease unload protection, and multi-epoch hot-reload with state migration and failure rollback in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T872-report.md` with exact `## Files changed`.

## Out of scope
- SDK and sysroot bundling (`T874`–`T877`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T872/build` and `python tools/axtest.py --compiler build-snap-T872/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
