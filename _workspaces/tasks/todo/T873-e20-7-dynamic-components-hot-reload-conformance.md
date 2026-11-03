---
id: T873
title: E20.7 Dynamic components, plugin discovery, cross-boundary ownership/capability isolation & hot-reload state migration conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T316, T318, T872]
priority: 223
status: todo
attempts: 0
paths: [tests/conformance/p20/e20_7_dynamic_components_hot_reload]
spec: [spec/SPEC-115-dynamic-components-plugins-hot-reload.md, 0104, tasks/0583, tasks/0584, tasks/0739, tasks/0856]
covers: [REQ-ECO-8734]
---
# T873 — E20.7 Dynamic components, plugin discovery, cross-boundary ownership/capability isolation & hot-reload state migration conformance suite

## Goal
Certify E20.7 exit criteria with an end-to-end conformance suite covering Axiom-to-Axiom dynamic plugins, version/capability negotiation, cross-boundary ownership/allocator safety, epoch lease unload guards, and live hot-reload with state hand-off.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_7_dynamic_components_hot_reload` verifying:
  - Axiom-to-Axiom dynamic component loading across v1.0 → v1.1 compatible interfaces and clean rejection of incompatible `AbiFingerprint` or ungranted capabilities (`REQ-ECO-8734`, `tasks/0584 §325.6-9`);
  - cross-boundary ownership and allocator safety (`ComponentBox<T>` deallocated by the originating component heap; stale `ComponentHandle<T>` generation detection after reload; `tasks/0584 §325.10-21`);
  - epoch lease safety preventing premature library unload while a borrowed `view` is live;
  - multi-epoch hot-reload (`v1` → `v2` → `v3`) preserving and migrating live application state, plus transactional rollback when `v3` migration returns an error (`tasks/0584 §325.22-24`, `tasks/0856 §26-40`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_7_dynamic_components_hot_reload` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T873-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T873/build` and `python tools/axtest.py --compiler build-snap-T873/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
