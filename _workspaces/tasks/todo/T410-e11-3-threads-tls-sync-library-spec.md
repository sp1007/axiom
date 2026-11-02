---
id: T410
title: E11.3 — Canonical threads, TLS & synchronization library specification (SPEC-32)
phase: P11-concurrency-async
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T400, T405]
priority: 131
status: todo
attempts: 0
paths: [spec/SPEC-32-threads-sync.md]
locks: [spec/INDEX.md, spec/SPEC-04-core-extensibility.md, spec/diagnostics.md]
spec: [0136, 0203, 0206, 0207, 0209, tasks/0278, tasks/0329, tasks/0621, tasks/0623, tasks/0837]
covers: [REQ-CONC-003, REQ-CONC-022, REQ-CONC-080, REQ-CONC-123, REQ-CONC-198]
---
# T410 — E11.3 — Canonical threads, TLS & synchronization library specification (SPEC-32)

## Goal
Write canonical `spec/SPEC-32-threads-sync.md` (`AXS-SYNC-*` rule IDs) defining `std.thread`, `@thread_local` TLS, `std.sync` (`Arc`, `Rc`, `Mutex`, `RwLock`, `Condvar`, `Once`, `Barrier`), `std.sync.channel`, and the host-interface threading intrinsics.

## Scope
- Write `spec/SPEC-32-threads-sync.md` with a Vietnamese `## Tóm tắt` section and numbered `AXS-SYNC-NNN` rules.
- Specify the host-interface intrinsic additions in `spec/SPEC-04-core-extensibility.md §11` (`host.thread_spawn`, `host.thread_join`, `host.thread_detach`, `host.thread_current_id`, `host.thread_yield`, `host.thread_sleep_ns`, `host.futex_wait`/`host.futex_wake` or SRWLock/Condvar primitives) for both Windows x64 (`CreateThread`, `WaitForSingleObject`, `WaitOnAddress`/`WakeByAddress*` or `SRWLOCK`/`CONDITION_VARIABLE`) and the deterministic MIR interpreter oracle.
- Specify `std.thread` (`Builder`, `Thread`, `JoinHandle<T>`, `spawn`, structured `scope`, explicit `detach`, child panic capture without unwinding parent, cooperative cancellation, no forced thread kill).
- Specify `@thread_local` static semantics (`!Share`, per-thread initialization/lifetime, COFF `.tls$` section and PE TLS directory emission on x86-64 Windows).
- Specify `std.sync` (`Arc<T>`, `Rc<T>`, `Mutex<T>` + `!Copy` `MutexGuard<T>`, `RwLock<T>` + `RwLockReadGuard<T>`/`RwLockWriteGuard<T>`, `Condvar`, `Once`/`OnceCell<T>`, `Barrier`) and `std.sync.channel` (bounded MPMC/MPSC/SPSC and unbounded channels with move ownership transfer).
- Update `spec/INDEX.md` and `spec/diagnostics.md`.

## Acceptance
- [ ] `spec/SPEC-32-threads-sync.md` exists with a Vietnamese `## Tóm tắt`, `AXS-SYNC-NNN` rule IDs, API signatures in canonical Axiom syntax, and happens-before contracts.
- [ ] `spec/SPEC-04-core-extensibility.md`, `spec/INDEX.md`, and `spec/diagnostics.md` are updated.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T410-report.md` with exact `## Files changed`.

## Out of scope
- Implementing `std/thread` or `std/sync` code (handled by `T090`, `T411`–`T413`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T410/build` and `python tools/axtest.py --compiler build-snap-T410/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
