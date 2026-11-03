---
id: T401
title: E11.1 — Closure & spawn capture verification (Send bounds, escaping views)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T089]
priority: 122
status: todo
attempts: 0
paths: [compiler/types, tests/ui/concurrency/spawn_capture, tests/run/concurrency/spawn_capture]
locks: [compiler/own/cap.ax, compiler/own/move.ax, compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-30-concurrency.md, 0091, 0105, 0111, 0116, 0126, 0160, tasks/0298, tasks/0488]
covers: [REQ-CONC-005, REQ-CONC-006, REQ-CONC-008, REQ-CONC-009, REQ-CONC-029, REQ-CONC-031, REQ-CONC-032, REQ-CONC-033, REQ-CONC-072, REQ-CONC-088, REQ-RES-044, REQ-TYP-069, REQ-TYP-106, REQ-CONC-125, REQ-CONC-132]
---
# T401 — E11.1 — Closure & spawn capture verification (Send bounds, escaping views)

## Goal
Enforce `Send`/`Share` derivation on closure environments and verify capture ownership and capability escape rules at `spawn` and `spawn_local` boundaries in `axiomc`.

## Scope
- Compute closure `Send` and `Share` properties in `compiler/types/typeck.ax` strictly from the closure's execution-relevant captured fields (`0116 §84`, `SPEC-30`).
- Enforce `move` capture ownership transfer for closures passed to cross-context `spawn` boundaries: mark captured `!Copy` variables as moved in the parent context without implicit copying (`0126 §11-12`).
- Reject escaping closures and `spawn` arguments that capture non-escaping `view<T>` or `mut_view<T>` capabilities whose provenance does not outlive the spawned execution context (`0111 §47`, `0131 §88`).
- Require `Send` on all captured values and return types crossing multi-threaded `spawn`, while permitting `!Send` captures in same-thread `spawn_local` subject to capability aliasing checks (`0160 §26`).
- Emit structured `AX_CONC_*` diagnostics identifying the offending captured variable, its type, and why `Send` or view-escape verification failed.

## Acceptance
- [ ] `tests/ui/concurrency/spawn_capture/*.ax` covers negative cases: `!Send` struct/raw-pointer captured in `spawn`, escaping `view<T>`/`mut_view<T>` in spawned closure, use-after-move of `!Copy` variable after `spawn`.
- [ ] `tests/run/concurrency/spawn_capture/*.ax` (`modes: interp native`) verifies valid `Send` closure captures, `Copy` captures, and `spawn_local` with `!Send` values.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T401` under `axiomc2.exe`; `archcheck.py`, `reqcov.py --strict`, and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T401-report.md` with exact `## Files changed`.

## Out of scope
- OS thread creation (`T090`) and async `Future` suspension-point analysis (`T417`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T401/build` and `python tools/axtest.py --compiler build-snap-T401/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
