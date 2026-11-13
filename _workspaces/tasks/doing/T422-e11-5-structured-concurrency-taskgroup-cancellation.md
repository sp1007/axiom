---
id: T422
title: E11.5 — Structured concurrency TaskGroup, cooperative CancellationToken & deadlines
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T421]
priority: 145
status: doing
attempts: 1
paths: [std/async/group.ax, std/async/cancel.ax, std/async/timeout.ax, std/async/governor.ax, tests/std/async/structured]
locks: [std/async/mod.ax]
spec: [spec/SPEC-34-executors-fibers.md, 0126, 0127, 0135, 0202, 0205, tasks/0277, tasks/0620, tasks/0834, tasks/0836]
covers: [REQ-CONC-040, REQ-ASY-019, REQ-ASY-109, REQ-CONC-100, REQ-CONC-150, REQ-CONC-155, REQ-CONC-188, REQ-CONC-199]
started: 2026-11-13 05:22:12
agent: T422-impl
---
# T422 — E11.5 — Structured concurrency TaskGroup, cooperative CancellationToken & deadlines

## Goal
Implement structured concurrency (`TaskGroup`), cooperative `CancellationToken`, `Deadline`/`Timeout` propagation, task panic containment, and `ResourceGovernor` accounting in `std.async`.

## Scope
- Implement `TaskGroup` in `std/async/group.ax`: child tasks spawned into a `TaskGroup` cannot outlive the group scope; exiting the group awaits all children; an unhandled error or panic in a child cancels remaining siblings and reports the failure deterministically (`REQ-CONC-040, 150, 155`, `REQ-ASY-019`).
- Implement `CancellationSource` and `CancellationToken` in `std/async/cancel.ax` with hierarchical child tokens, cooperative `.is_cancelled()`, and `cancelled()` Future awaiting (`REQ-ASY-110..113`).
- Implement `Deadline` and `with_deadline` / `Timeout<F>` in `std/async/timeout.ax` (`REQ-ASY-153, 159`) and `ResourceGovernor` task/memory quota tracking in `std/async/governor.ax` (`REQ-ASY-167`).
- Ensure explicit `task.detach()` is required when a caller intentionally releases a `TaskHandle` without awaiting it, while dropping an un-awaited structured handle cancels and cleans up task state (`REQ-ASY-109`, `REQ-CONC-100, 199`).

## Acceptance
- [ ] `tests/std/async/structured/*.ax` (`modes: interp native`) verifies that `TaskGroup` joins all children before scope exit, cancels sibling tasks and runs their `Future` destructors when one child fails, propagates `CancellationToken` across nested tasks, enforces `Deadline` budgets, captures child task panics into `TaskResult::Panicked`, and tracks `ResourceGovernor` task limits.
- [ ] Full test suite passes in `build-snap-T422` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T422-report.md` with exact `## Files changed`.

## Out of scope
- Stackful `Fiber` execution (`T423`) and OS IOCP async I/O (`T426`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T422/build` and `python tools/axtest.py --compiler build-snap-T422/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-13 05:22:12 started (attempt 1) T422-impl
