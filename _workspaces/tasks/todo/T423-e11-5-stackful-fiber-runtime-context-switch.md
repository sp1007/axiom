---
id: T423
title: E11.5 — Stackful Fiber runtime & cooperative context switching
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T420, T090]
priority: 146
status: todo
attempts: 0
paths: [std/fiber, std/sys/windows/fiber.ax, tests/std/fiber]
locks: [std/core/host.ax, compiler/interp/oracle.ax, compiler/interp/interp.ax, compiler/types/typeck.ax, compiler/lir/builder.ax, tests/selfhost]
spec: [spec/SPEC-34-executors-fibers.md, 0204, 0205, tasks/0277, tasks/0836]
covers: [REQ-CONC-151, REQ-CONC-189]
---
# T423 — E11.5 — Stackful Fiber runtime & cooperative context switching

## Goal
Implement stackful `Fiber<T>` execution (`std.fiber`) with explicit stack budgets, cooperative `resume`/`yield_now`, thread-pinned default affinity, Windows Win32 fiber host backing, and deterministic oracle coroutine simulation.

## Scope
- Declare `host.fiber_create`, `host.fiber_resume`, `host.fiber_yield`, and `host.fiber_destroy` in `std/core/host.ax`, implement them natively in `std/sys/windows/fiber.ax` (`ConvertThreadToFiberEx`, `CreateFiberEx`, `SwitchToFiber`, `DeleteFiber`), and implement deterministic stackful coroutine switching in `compiler/interp/oracle.ax` and `compiler/interp/interp.ax`.
- Implement `std/fiber/mod.ax`: `FiberBuilder` (explicit stack commit/reserve size), `Fiber<Y, R>` (`resume() -> FiberState<Y, R>`, `yield_val(y)`), and `FiberScheduler` for cooperative same-thread fiber scheduling.
- Enforce default thread-pinned affinity (`Fiber` is `!Send` and `!Share` by default so thread-local references and stack views never migrate across OS threads, `0204 §11-13`, `REQ-CONC-151, 189`) and deterministic Drop of live stack values when a completed or unwound fiber is destroyed.

## Acceptance
- [ ] `tests/std/fiber/*.ax` (`modes: interp native`) verifies multi-step `resume`/`yield_val` ping-pong, deep call-stack suspension across helper functions, `FiberScheduler` round-robin execution of multiple fibers, custom stack sizes, and deterministic Drop cleanup on fiber completion.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T423` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T423-report.md` with exact `## Files changed`.

## Out of scope
- Language-level stackless `yield` generators (Phase 14 `E14.3`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T423/build` and `python tools/axtest.py --compiler build-snap-T423/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
