---
id: T536
title: E13.5 — async task panic capture via catch_unwind in group_poll_fn / tcb_poll_fn (replaces cooperative task_panic)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T523, T422c]
priority: 174
status: todo
attempts: 0
timeout_min: 600
paths: [std/async, tests/std/async/panic_capture]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-34-executors-fibers.md, spec/SPEC-33-async.md]
covers: [REQ-ASY-019]
---
# T536 — Async task panic capture through unwinding

## Goal
A real `panic` inside a spawned task is captured at the task boundary and surfaces as `TaskResult.Panicked` on join /
in the `TaskGroup`, the worker thread keeps running, and drops of the task's frames run in reverse order (SPEC-34,
REQ-ASY-019; ADR-0042 §2). Replaces the cooperative `task_panic(cx)` mechanism of T422.

## Scope
- `group_poll_fn` and `tcb_poll_fn` wrap the poll call in `std.panic.catch_unwind` (T522 oracle, T523 native landing
  pads); on a caught panic: mark the task `TASK_PANICKED`, store the payload, drop the future, wake the joiner.
- `task_panic(cx)` stays as a documented explicit API or is removed with its tests migrated (record the choice).
- Under `--panic abort` the previous behaviour (process abort) is kept and tested.
- Tests `tests/std/async/panic_capture/*` (interp, native, native-O1, `--panic unwind`; exact `// stdout:`): panicking
  child in a group, sibling continues, joiner sees `Panicked`, destructor order printed; abort-mode counterpart.

## Acceptance
- [ ] Tests pass in all modes; existing `tests/std/async/**` pass; WEAK-NATIVE 0.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T536-report.md` with exact `## Files changed`.

## Out of scope
- Unwinding machinery itself (T522, T523), `compiler/`, `docs/`.

## Notes
- Placed in P13 (after T523) because P11 has no unwinding; ADR-0042 §2 option (c).

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 decision 4)
