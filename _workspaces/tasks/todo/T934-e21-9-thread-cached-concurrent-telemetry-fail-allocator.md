---
id: T934
title: E21.9 Thread-cached concurrent allocator, TelemetryAllocator & deterministic FailAtAllocator
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T932, T933]
priority: 244
status: todo
attempts: 0
paths: [std/alloc/concurrent, std/alloc/telemetry, std/alloc/fail_inject, tests/run/std_alloc_concurrent]
spec: [spec/SPEC-128-allocators-pool-custom-concurrent.md, 0106, 0036, tasks/0280, tasks/0415]
covers: [REQ-RT-094, REQ-RT-095, REQ-RT-096, REQ-RT-097, REQ-RT-098, REQ-RT-099, REQ-RT-100, REQ-RT-101, REQ-RT-102, REQ-RT-103, REQ-RT-104, REQ-RT-105, REQ-RT-106, REQ-RT-107, REQ-RT-108, REQ-RT-109, REQ-RT-110, REQ-RT-111, REQ-RT-112, REQ-RT-113, REQ-RT-114, REQ-RT-115, REQ-RT-116, REQ-RT-117, REQ-RT-118, REQ-RT-119, REQ-RT-120, REQ-RT-014, REQ-RT-135, REQ-RT-139, REQ-RT-140]
---
# T934 — E21.9 Thread-cached concurrent allocator, TelemetryAllocator & deterministic FailAtAllocator

## Goal
Implement the multi-threaded `ThreadCacheAllocator` (per-thread magazine caches + cross-thread remote free list), `TelemetryAllocator` accounting wrapper, and deterministic `FailAtAllocator` OOM fault injector in `std.alloc` per `spec/SPEC-128-allocators-pool-custom-concurrent.md`.

## Scope
- Implement `std/alloc/concurrent` (`ThreadCacheAllocator` with per-thread size-class magazines, atomic MPSC remote-free list for cross-thread deallocations where thread B frees an object allocated by thread A, and bounded central span depot; `0106 §17-22`, `tasks/0280 §17-24`).
- Implement `std/alloc/telemetry` (`TelemetryAllocator<A>` tracking `live_bytes`, `peak_bytes`, `alloc_count`, `dealloc_count`, `realloc_count`, and leak-check assertions on scope exit).
- Implement `std/alloc/fail_inject` (`FailAtAllocator<A>` and `ByteBudgetAllocator<A>` that deterministically return `Result.Err(AllocError)` on the N-th allocation or above a byte ceiling so `Drop` and rollback paths under OOM are exhaustively testable).
- Add multi-threaded and OOM fault-injection run tests in `tests/run/std_alloc_concurrent`.

## Acceptance
- [ ] Run tests in `tests/run/std_alloc_concurrent` verify `ThreadCacheAllocator` producer-consumer cross-thread allocation/deallocation without leaks, `TelemetryAllocator` zero-leak accounting (`live_bytes == 0` after `Drop`), and `FailAtAllocator` N-th allocation OOM rollback across collections in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T934-report.md` with exact `## Files changed`.

## Out of scope
- GPU device allocators (`P22 E22.2`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T934/build` and `python tools/axtest.py --compiler build-snap-T934/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
