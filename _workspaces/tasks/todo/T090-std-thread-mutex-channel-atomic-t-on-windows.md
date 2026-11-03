---
id: T090
title: E11.3 — Host threading intrinsics & std.thread spawn/join/scope on Windows
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T211, T089, T401, T407, T408, T410]
priority: 132
status: todo
attempts: 0
paths: [std/thread, std/sys/windows/thread.ax, tests/std/thread, tests/selfhost]
locks: [std/core/host.ax, compiler/interp/oracle.ax, compiler/interp/interp.ax, compiler/types/typeck.ax, compiler/lir/builder.ax, tests/selfhost]
spec: [spec/SPEC-32-threads-sync.md, 0203, 0206, 0207, 0208, tasks/0329, tasks/0623]
covers: [REQ-CONC-219]
---
# T090 — E11.3 — Host threading intrinsics & std.thread spawn/join/scope on Windows

## Goal
Implement the host threading intrinsics (`std/core/host.ax`, `std/sys/windows/thread.ax`, and the MIR interpreter oracle) and `std.thread` (`spawn`, `Builder`, `JoinHandle<T>`, structured `scope`, `yield_now`, `sleep`, thread ID/name, and panic containment) per `spec/SPEC-32-threads-sync.md`.

## Scope
- Add `host.thread_*` intrinsics (`thread_spawn`, `thread_join`, `thread_detach`, `thread_current_id`, `thread_yield`, `thread_sleep_ns`, `futex_wait`, `futex_wake`) in `std/core/host.ax`, wire them in `compiler/types/typeck.ax` and `compiler/lir/builder.ax`, implement them on Windows x64 in `std/sys/windows/thread.ax` (`CreateThread`, `WaitForSingleObject`, `CloseHandle`, `SwitchToThread`, `Sleep`, `WaitOnAddress`, `WakeByAddressSingle`, `WakeByAddressAll`), and implement deterministic cooperative thread scheduling in `compiler/interp/oracle.ax` and `compiler/interp/interp.ax`.
- Implement `std/thread/mod.ax`: `Thread`, `ThreadId`, `Builder` (configurable stack size and thread name), `JoinHandle<T>` (`join() -> Result<T, ThreadPanic>`, explicit `detach()`), `spawn` (requiring `F: Send` and `T: Send`), `scope` (structured scoped threads that borrow parent stack data and join all child threads before `scope` returns), `yield_now()`, and `sleep(duration)`.
- Ensure a panic inside a child thread is caught at the thread boundary and returned as `Err(ThreadPanic)` from `JoinHandle.join()` without forcibly terminating or unwinding the parent thread prematurely.

## Acceptance
- [ ] `tests/std/thread/*.ax` (`modes: interp native`) verifies `thread.spawn` and `JoinHandle.join`, value return across threads, `Builder` stack size and name configuration, structured `thread.scope` borrowing stack locals, explicit `detach`, and child panic capture via `join()`.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T090` under `axiomc2.exe` (`WEAK-NATIVE 0`); build warning-free; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T090-report.md` with exact `## Files changed`.

## Out of scope
- `Arc`/`Rc`/`Mutex`/`RwLock`/`Condvar`/`Once`/`Barrier` (`T411`), channels (`T412`), and `@thread_local` COFF/PE `.tls` emission (`T413`).

## Notes
- Roadmap epic E11.3. Implemented in `compiler/` (Axiom) / `std/` — `axiom0` is frozen after T087 (ROADMAP R3).
- Refined by T211 as the first implementation slice of E11.3 after `T410` (`SPEC-32`), followed by `T411`–`T414`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:55 covers += REQ-CONC-219 (metadata only)
- 2026-11-03 00:10:00 refined scope, paths, locks, and dependencies in T211 (P11 phase planning)
