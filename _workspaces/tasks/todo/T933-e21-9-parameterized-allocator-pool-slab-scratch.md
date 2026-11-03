---
id: T933
title: E21.9 Parameterized Allocator<A> collections, FixedPoolAllocator, SlabAllocator & ScratchScope
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T932]
priority: 243
status: todo
attempts: 0
paths: [std/alloc/pool, std/alloc/slab, std/alloc/scratch, tests/run/std_alloc_pool_slab]
spec: [spec/SPEC-128-allocators-pool-custom-concurrent.md, 0106, 0036, tasks/0280, tasks/0415]
covers: [REQ-RT-061, REQ-RT-062, REQ-RT-063, REQ-RT-064, REQ-RT-065, REQ-RT-066, REQ-RT-067, REQ-RT-068, REQ-RT-069, REQ-RT-070, REQ-RT-071, REQ-RT-072, REQ-RT-073, REQ-RT-074, REQ-RT-075, REQ-RT-076, REQ-RT-077, REQ-RT-078, REQ-RT-079, REQ-RT-080, REQ-RT-081, REQ-RT-082, REQ-RT-083, REQ-RT-084, REQ-RT-085, REQ-RT-086, REQ-RT-087, REQ-RT-088, REQ-RT-089, REQ-RT-090, REQ-RT-091, REQ-RT-092, REQ-RT-093, REQ-RT-135, REQ-RT-139, REQ-RT-140, REQ-RT-172]
---
# T933 — E21.9 Parameterized Allocator<A> collections, FixedPoolAllocator, SlabAllocator & ScratchScope

## Goal
Implement `FixedPoolAllocator`, `SlabAllocator`, `ScratchScope`, and allocator-parameterized containers (`BoxIn<T, A>`, `VecIn<T, A>`) with fallible `try_reserve`/`try_push` in `std.alloc` per `spec/SPEC-128-allocators-pool-custom-concurrent.md`.

## Scope
- Implement `std/alloc/pool` (`FixedPoolAllocator` with intrusive O(1) freelist, alignment-verified blocks, optional poison-on-free debug fill, and `BoxIn<T, A>` / `VecIn<T, A>` fallible `try_alloc`/`try_reserve`/`try_push` methods; `0106 §10-16`, `0036 §8-14`, `REQ-RT-135`, `REQ-RT-139`, `REQ-RT-140`).
- Implement `std/alloc/slab` (`SlabAllocator` with power-of-two and intermediate size classes `16..4096` bytes, per-page bitmaps, and empty-slab reclamation; `tasks/0280 §10-16`).
- Implement `std/alloc/scratch` (`ScratchScope` and `StackBufferAllocator<N>` backed by stack or caller-supplied byte slices with watermark checkpoint/rewind and capability-bound views that cannot escape the rewind scope).
- Add run tests in `tests/run/std_alloc_pool_slab`.

## Acceptance
- [ ] Run tests in `tests/run/std_alloc_pool_slab` verify `FixedPoolAllocator` O(1) reuse and exhaustion (`AllocError`), `SlabAllocator` size-class routing and page reclamation, `StackBufferAllocator` zero-OS-heap operation, and `VecIn<T, A>.try_push` rollback on OOM in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T933-report.md` with exact `## Files changed`.

## Out of scope
- Thread-cached concurrent allocator, `TelemetryAllocator`, and `FailAtAllocator` (`T934`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T933/build` and `python tools/axtest.py --compiler build-snap-T933/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
