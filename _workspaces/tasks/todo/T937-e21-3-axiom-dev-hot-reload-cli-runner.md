---
id: T937
title: E21.3 — Stateful live hot-reload CLI runner axiom dev --hot & transactional state migration
phase: P21-standard-library-completion
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T909, T910, T872]
priority: 247
status: todo
attempts: 0
paths: [compiler/driver, std/os/dev, tests/run/dev_hot_reload]
spec: [spec/SPEC-122-os-fs-process-signals-ipc.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-ECO-8734]
---
# T937 — E21.3 — Stateful live hot-reload CLI runner axiom dev --hot & transactional state migration

## Goal
Implement the `axiom dev --hot` CLI command, integrating native filesystem change notifications (`FsWatcher`), child process IPC, and transactional component state migration with automatic clean process restart fallback.

## Scope
- Implement `axiom dev --hot [entrypoint.ax]` in `compiler/driver`:
  * Use `std.fs.FsWatcher` (`T909`) to watch workspace source trees with debouncing.
  * Spawn the running application inside an isolated child worker process communicating via IPC pipe or local domain socket.
- Support live code reloading using `E20.7` dynamic component facilities (`T872`):
  * When recompiling modified components, trigger transactional state serialization/deserialization across hot-swapped modules.
  * Detect ABI incompatibilities (layout changes, modified vtables) and automatically perform an immediate, clean child-process restart without crashing the host terminal runner.
- Maintain persistent terminal UX with clear ANSI status banners (compilation time, reload status, error diagnostic logs).

## Acceptance
- [ ] Run tests in `tests/run/dev_hot_reload` verify modifying source files triggers incremental recompilation and state-preserving hot reload.
- [ ] Fallback test verifies that introducing a structural ABI change cleanly restarts the child process without terminal abort.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T937-report.md` with exact `## Files changed`.

## Out of scope
- Remote debugging protocol (handled in LSP / P19).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T937/build` and `python tools/axtest.py --compiler build-snap-T937/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:25:00 created by axiom-architect (ADR-0039 P21 hot reload runner expansion)
