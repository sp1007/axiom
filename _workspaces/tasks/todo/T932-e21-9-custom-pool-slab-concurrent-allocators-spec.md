---
id: T932
title: E21.9 Canonical custom Allocator trait, slab/pool, scratch & thread-cached concurrent allocators specification (SPEC-128)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 242
status: todo
attempts: 0
paths: [spec/SPEC-128-allocators-pool-custom-concurrent.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0106, 0036, tasks/0280, tasks/0415]
covers: [REQ-RT-014, REQ-RT-023, REQ-RT-024, REQ-RT-025, REQ-RT-026, REQ-RT-027, REQ-RT-028, REQ-RT-029, REQ-RT-030, REQ-RT-031, REQ-RT-032, REQ-RT-033, REQ-RT-034, REQ-RT-035, REQ-RT-036, REQ-RT-037, REQ-RT-038, REQ-RT-039, REQ-RT-040, REQ-RT-041, REQ-RT-042, REQ-RT-043, REQ-RT-044, REQ-RT-045, REQ-RT-046, REQ-RT-047, REQ-RT-048, REQ-RT-049, REQ-RT-050, REQ-RT-051, REQ-RT-052, REQ-RT-053, REQ-RT-054, REQ-RT-055, REQ-RT-056, REQ-RT-057, REQ-RT-058, REQ-RT-059, REQ-RT-060, REQ-RT-135, REQ-RT-139, REQ-RT-140, REQ-RT-166, REQ-RT-167, REQ-RT-168, REQ-RT-169, REQ-RT-170, REQ-RT-171, REQ-RT-172, REQ-RT-177, REQ-RT-178]
---
# T932 — E21.9 Canonical custom Allocator trait, slab/pool, scratch & thread-cached concurrent allocators specification (SPEC-128)

## Goal
Consolidate the canonical specification for Axiom's complete allocator architecture—first-class `Allocator` trait composition, fallible allocation (`try_alloc`/`AllocError`), fixed-size pool and size-class slab allocators, scoped scratch allocators, thread-cached concurrent allocators, and fault-injecting test allocators—into `spec/SPEC-128-allocators-pool-custom-concurrent.md` (`AXS-ALC-*` rule IDs).

## Scope
- Write `spec/SPEC-128-allocators-pool-custom-concurrent.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ALC-NNN` rules.
- Specify the first-class `Allocator` capability contract (`alloc`, `alloc_zeroed`, `realloc`, `dealloc` over validated `Layout(size, align)`; `0106 §3-18`, `0036 §4-16`, `tasks/0280 §3-19`, `tasks/0415 §1-15`, `REQ-RT-135`, `REQ-RT-139`, `REQ-RT-140`), ensuring no mandatory global GC or hidden heap exists in freestanding/no-heap profiles (`REQ-RT-044`, `REQ-RT-169`, `REQ-RT-177`, `REQ-RT-178`).
- Specify allocator-parameterized containers (`Box<T, A>`, `Vec<T, A>`, `HashMap<K, V, A>`, `BTreeMap<K, V, A>`, `StringIn<A>`), fallible growth (`try_reserve`, `try_push` returning `Result<_, AllocError>`), and compile-time rejection of cross-allocator pointer/buffer mix-ups.
- Specify `FixedPoolAllocator<T>` (O(1) freelist, zero external fragmentation), `SlabAllocator` (size-class segregated caches), `ScratchScope` / `RingArena` (frame/request-scoped bulk reset invalidating live capabilities at compile time), `ThreadCacheAllocator` (per-thread magazine caches + lock-free remote free queue), and `TelemetryAllocator` / `FailAtAllocator` (deterministic OOM fault injection).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-128-allocators-pool-custom-concurrent.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ALC-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T932-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of pool, slab, scratch, and concurrent allocators (`T933`–`T934`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T932/build` and `python tools/axtest.py --compiler build-snap-T932/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
