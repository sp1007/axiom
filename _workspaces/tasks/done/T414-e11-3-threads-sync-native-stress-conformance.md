---
id: T414
title: E11.3 — Multi-threaded stress & synchronization conformance suite
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T410, T090, T411, T412, T413]
priority: 136
status: done
attempts: 1
paths: [tests/conformance/p11/e11_3_threads_sync]
spec: [spec/SPEC-32-threads-sync.md, 0203, 0206, 0207, 0209, tasks/0329, tasks/0623]
covers: [REQ-CONC-036, REQ-CONC-037, REQ-CONC-038, REQ-CONC-039, REQ-CONC-081, REQ-CONC-187]
started: 2026-11-10 22:21:13
finished: 2026-11-11 08:15:06
---
# T414 — E11.3 — Multi-threaded stress & synchronization conformance suite

## Goal
Verify the `E11.3` exit criterion ('native stress suite') with multi-threaded stress and conformance tests covering threads, scoped threads, locks, channels, `Arc`, and TLS.

## Scope
- Create `tests/conformance/p11/e11_3_threads_sync/` testing all `AXS-SYNC-*` rules under both `[interp]` and multi-threaded `[native]` / `[native-O1]` execution.
- Include high-contention native stress tests: 8-thread `Arc<Mutex<T>>` counter & ring mutation, reader-heavy and writer-heavy `RwLock<T>` stress, `Condvar` bounded work queue, `Once` concurrent init race, MPMC bounded/unbounded channel pipeline with drop-counter payloads, scoped threads borrowing parent stack data, child thread panic containment via `JoinHandle`, and `@thread_local` isolation.

## Acceptance
- [ ] All stress and conformance tests in `tests/conformance/p11/e11_3_threads_sync/` pass deterministically in `[interp]`, `[native]`, and `[native-O1]` under `axiomc2.exe` (`WEAK-NATIVE 0`, `0 FAIL`).
- [ ] Full test suite passes in `build-snap-T414` under `axiomc2.exe`; `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T414-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or std source files.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T414/build` and `python tools/axtest.py --compiler build-snap-T414/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-10 22:21:13 started (attempt 1) T414-impl
- 2026-11-11 08:15:06 accepted by QA -> done
