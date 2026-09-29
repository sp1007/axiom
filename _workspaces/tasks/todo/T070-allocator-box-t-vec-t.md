---
id: T070
title: Allocator, Box<T>, Vec<T>
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
depends: [T069, T065]
priority: 101
status: todo
attempts: 0
paths: [std/core/alloc, std/alloc, tests/std/alloc]
spec: [0087, 0106, 0210, tasks/0280, 0045]
---
# T070 — Allocator, Box<T>, Vec<T>

## Goal
Heap memory with explicit ownership.

## Scope
- Allocator trait + Windows heap backend via FFI, Box<T>, Vec<T> (push/pop/get/index/views/iteration later, drops elements), allocation-failure policy per spec.

## Acceptance
- [ ] run tests incl. drop counts and growth; leak check via allocator counters.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T070-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
