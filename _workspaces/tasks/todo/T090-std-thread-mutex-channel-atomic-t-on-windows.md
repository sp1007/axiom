---
id: T090
title: E11.3 std.thread, Mutex, channel, Atomic<T> on Windows
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
depends: [T211, T089]
priority: 132
status: todo
attempts: 0
paths: [std/thread, std/sync, tests/std/thread]
spec: [0203, 0206, 0207, 0208, 0329]
---
# T090 — std.thread, Mutex, channel, Atomic<T> on Windows

## Goal
Native threading library.

## Scope
- CreateThread-based spawn/join, Mutex (SRWLock), channels, Atomic<T> lowering (backend support via intrinsics).

## Acceptance
- [ ] Native stress tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T090-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Roadmap epic E11.3. Implemented in `compiler/` (Axiom) / `std/` — axiom0 is frozen after T087 (ROADMAP R3).
- The P11/P23 planning task may split this task further; keep its id for the first slice.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
