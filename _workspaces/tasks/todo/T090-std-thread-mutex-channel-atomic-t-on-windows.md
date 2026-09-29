---
id: T090
title: std.thread, Mutex, channel, Atomic<T> on Windows
phase: P11-v1
owner: axiom-stdlib
reviewer: axiom-qa
depends: [T089]
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
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
