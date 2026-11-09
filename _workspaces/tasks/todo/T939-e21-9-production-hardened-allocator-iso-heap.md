---
id: T939
title: E21.9 — Production HardenedAllocator (IsoHeap): type-isolated partitions, quarantine & zero-on-free
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T933, T535]
priority: 249
status: todo
attempts: 0
paths: [std/alloc/hardened, tests/run/iso_heap]
spec: [spec/SPEC-128-allocators-pool-custom-concurrent.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-RT-121, REQ-RT-177]
---
# T939 — E21.9 — Production HardenedAllocator (IsoHeap): type-isolated partitions, quarantine & zero-on-free

## Goal
Implement the production `HardenedAllocator` (`IsoHeap`) in `std.alloc` with `TypeId`-segregated memory pools, non-reusable quarantine ring buffers, freelist pointer cookie encryption, zero-on-free scrubbing, and guard-page protection.

## Scope
- Implement `IsoHeap` in `std/alloc/hardened` conforming to the `Allocator` trait:
  * Type-isolated partitions: maintain independent heap arenas segregated by `TypeId(T)` (or object size and alignment bucket), preventing cross-type use-after-free type confusion.
  * Zero-on-free: deterministically scrub allocated memory chunks with zeros upon deallocation (`zeroize_memory`) before returning blocks to quarantine.
  * Quarantine ring: maintain a 64-slot FIFO quarantine buffer delaying memory reuse to frustrate immediate heap feng-shui and exploitation of dangling pointers.
  * XOR freelist cookies: encrypt linked freelist next pointers with a process-random 64-bit secret cookie, causing corrupted pointers to abort rather than hijack control flow.
  * Guard pages: place inaccessible virtual memory guard pages at arena boundaries and for allocations exceeding 32 KiB.
- Provide zero-allocation runtime panic aborts when heap metadata corruption or double-free conditions are detected.

## Acceptance
- [ ] Run tests in `tests/run/iso_heap` verify that memory returned from `deallocate` is completely zero-scrubbed.
- [ ] Tampering test verifies that corrupting freelist cookies triggers immediate process abort.
- [ ] Type segregation test verifies that allocations of different types reside in non-overlapping memory regions.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T939-report.md` with exact `## Files changed`.

## Out of scope
- Low-memory microcontroller allocators (handled in `SPEC-52` freestanding profiles).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T939/build` and `python tools/axtest.py --compiler build-snap-T939/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:25:00 created by axiom-architect (ADR-0039 P21 IsoHeap hardened allocator expansion)
