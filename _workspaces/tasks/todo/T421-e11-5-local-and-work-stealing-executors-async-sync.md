---
id: T421
title: E11.5 — Single-thread LocalExecutor, multi-thread work-stealing Executor & async sync
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T420, T412, T088, T418]
priority: 144
status: todo
attempts: 0
paths: [std/async/executor.ax, std/async/task.ax, std/async/waker.ax, std/async/sync.ax, std/async/channel.ax, std/async/mod.ax, tests/std/async/executor, tests/selfhost]
spec: [spec/SPEC-34-executors-fibers.md, 0202, 0205, tasks/0277, tasks/0278, tasks/0620, tasks/0621, tasks/0835, tasks/0836]
covers: [REQ-CONC-034, REQ-CONC-035, REQ-CONC-049, REQ-ASY-037, REQ-ASY-041, REQ-ASY-054, REQ-ASY-076, REQ-ASY-086, REQ-ASY-102, REQ-ASY-108, REQ-ASY-129, REQ-ASY-130, REQ-CONC-130, REQ-CONC-147, REQ-CONC-148, REQ-CONC-184, REQ-CONC-190]
---
# T421 — E11.5 — Single-thread LocalExecutor, multi-thread work-stealing Executor & async sync

## Goal
Implement `std.async` single-thread `LocalExecutor`, multi-thread work-stealing `Executor`, `TaskHandle<T>`, atomic `Waker` state machine, and async-aware synchronization primitives (`AsyncMutex`, `AsyncSemaphore`, async channels).

## Scope
- Implement `TaskControlBlock` and atomic wake state machine (`IDLE`, `POLLING`, `NOTIFIED`, `COMPLETED`, `CANCELLED`) in `std/async/task.ax` and `std/async/waker.ax` guaranteeing idempotent `wake()` and zero lost wakeups (`tasks/0620 §9-11`).
- Implement `LocalExecutor` in `std/async/executor.ax` supporting `spawn_local<F: Future>(f)` (allowing `!Send` futures pinned to the creation thread) and `run_until(main_future)`.
- Implement multi-threaded work-stealing `Executor` in `std/async/executor.ax` with per-worker Chase-Lev / ring queues, cross-worker stealing of `Send` tasks (`spawn<F: Future + Send>(f) -> TaskHandle<F.Output>`), and `block_on`.
- Implement `AsyncMutex<T>` (whose `AsyncMutexGuard<T>` is safe to hold across `.await` and wakes the next waiter on Drop/cancellation without losing lock ownership), `AsyncSemaphore`, and async `Sender<T>`/`Receiver<T>` in `std/async/sync.ax` and `std/async/channel.ax`.

## Acceptance
- [ ] `tests/std/async/executor/*.ax` (`modes: interp native`) tests `LocalExecutor` with `!Send` (`Rc<T>`) tasks, multi-thread work-stealing `Executor` across 4 worker threads, lost-wake prevention under concurrent `wake()` during `poll()`, `AsyncMutex` held across `.await`, and async channel producer/consumer pipelines.
- [ ] Full test suite passes in `build-snap-T421` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T421-report.md` with exact `## Files changed`.

## Out of scope
- Structured `TaskGroup` and cancellation tokens (`T422`); stackful `Fiber` (`T423`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T421/build` and `python tools/axtest.py --compiler build-snap-T421/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
