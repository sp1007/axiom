---
id: T935
title: E21.9 Pool, slab, custom, concurrent & fault-injecting allocators conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T934, T939]
priority: 245
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_9_allocators]
spec: [spec/SPEC-128-allocators-pool-custom-concurrent.md, 0106, 0036, tasks/0280, tasks/0415]
covers: [REQ-RT-121, REQ-RT-122, REQ-RT-123, REQ-RT-124, REQ-RT-125, REQ-RT-126, REQ-RT-127, REQ-RT-128, REQ-RT-129, REQ-RT-130, REQ-RT-131, REQ-RT-014, REQ-RT-135, REQ-RT-139, REQ-RT-140, REQ-RT-166, REQ-RT-167, REQ-RT-168, REQ-RT-169, REQ-RT-170, REQ-RT-171, REQ-RT-172, REQ-RT-177, REQ-RT-178]
---
# T935 — E21.9 Pool, slab, custom, concurrent & fault-injecting allocators conformance suite

## Goal
Certify E21.9 exit criteria with an end-to-end allocator conformance suite covering `FixedPoolAllocator`, `SlabAllocator`, `ScratchScope`, `ThreadCacheAllocator`, `TelemetryAllocator`, and `FailAtAllocator` OOM safety.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_9_allocators` verifying custom allocator composition without mandatory global heap (`REQ-RT-044`, `REQ-RT-135`, `REQ-RT-139`, `REQ-RT-140`, `REQ-RT-177`, `REQ-RT-178`).
- Verify `FailAtAllocator` sweeping allocation failure points `1..N` across `VecIn`, `BTreeMap`, and `HashMap` mutations with `TelemetryAllocator` asserting zero leaked bytes and exact `Drop` count on already-constructed elements.
- Verify multi-threaded cross-thread producer/consumer stress on `ThreadCacheAllocator` and differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_9_allocators` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T935-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T935/build` and `python tools/axtest.py --compiler build-snap-T935/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
