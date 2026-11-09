---
id: T411
title: E11.3 — std.sync primitives: Arc, Rc, Mutex, RwLock, Condvar, Once, Barrier
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T090]
priority: 133
status: done
attempts: 1
paths: [std/sync/arc.ax, std/sync/rc.ax, std/sync/mutex.ax, std/sync/rwlock.ax, std/sync/condvar.ax, std/sync/once.ax, std/sync/barrier.ax, std/sync/mod.ax, tests/std/sync]
locks: [std/sys/windows/thread.ax, std/core/host.ax, compiler/interp/oracle.ax, tests/selfhost]
spec: [spec/SPEC-32-threads-sync.md, 0136, 0207, 0209, tasks/0329, tasks/0621, tasks/0837]
covers: [REQ-CONC-010, REQ-CONC-015, REQ-CONC-044, REQ-CONC-045, REQ-CONC-046, REQ-CONC-047, REQ-CONC-070, REQ-CONC-071, REQ-CONC-105, REQ-CONC-106, REQ-CONC-180]
started: 2026-11-09 06:52:26
finished: 2026-11-09 11:47:46
---
# T411 — E11.3 — std.sync primitives: Arc, Rc, Mutex, RwLock, Condvar, Once, Barrier

## Goal
Implement the standard synchronization and reference-counting library `std.sync` (`Arc<T>`, `Rc<T>`, `Mutex<T>`, `RwLock<T>`, `Condvar`, `Once`, `OnceCell<T>`, `Barrier`) in Axiom for both native Windows x64 and the MIR interpreter oracle.

## Scope
- Implement `Rc<T>` (`!Send`, `!Share`, non-atomic reference count, `clone`, `strong_count`, `get_view`) and `Arc<T>` (`Send + Share` iff `T: Send + Share`, atomic Acquire/Release/AcqRel reference count, `clone`, `strong_count`, `get_view`, deterministic inner Drop on last release).
- Implement `Mutex<T>` (`Send + Share` iff `T: Send`) and `!Copy` `MutexGuard<T>` (yielding `view<T>`/`mut_view<T>` and automatically unlocking in `Drop.drop`), backed by Windows SRWLock / `WaitOnAddress` natively and oracle lock tracking in `[interp]`.
- Implement `RwLock<T>` (`Send + Share` iff `T: Send + Share`) with `!Copy` `RwLockReadGuard<T>` (`view<T>`) and `RwLockWriteGuard<T>` (`mut_view<T>`).
- Implement `Condvar` (`wait`, `wait_timeout_ms`, `notify_one`, `notify_all`), `Once` / `OnceCell<T>` (thread-safe single initialization), and `Barrier`.

## Acceptance
- [ ] `tests/std/sync/*.ax` (`modes: interp native`) tests `Arc<T>` + `Mutex<T>` multi-threaded mutation, `Rc<T>` single-threaded sharing and drop counting, `RwLock<T>` concurrent readers and exclusive writer, `Condvar` producer/consumer signaling, `Once`/`OnceCell` concurrent initialization, and `Barrier` rendezvous.
- [ ] `tests/selfhost/bundles_current.test` passes if any `compiler/interp` lock file was touched.
- [ ] Full test suite passes in `build-snap-T411` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T411-report.md` with exact `## Files changed`.

## Out of scope
- Channels (`T412`) and async-aware locks (`T421`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T411/build` and `python tools/axtest.py --compiler build-snap-T411/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-09 06:52:26 started (attempt 1) T411-impl
- 2026-11-09 11:47:46 accepted by QA -> done
