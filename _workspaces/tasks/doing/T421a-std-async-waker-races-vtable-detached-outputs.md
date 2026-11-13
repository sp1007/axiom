---
id: T421a
title: std/async follow-up — join-waker race, task_wake livelock, poll flag clobber, Waker vtable dispatch, detached task outputs dropped
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 25
status: doing
attempts: 1
timeout_min: 600
paths: [std/async, tests/std/async]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-33-async.md, spec/SPEC-34-executors-fibers.md, spec/SPEC-31-atomics.md]
covers: [REQ-TST-036, REQ-ASY-037, REQ-ASY-109]
started: 2026-11-13 16:42:56
agent: T421a-impl
---
# T421a — std/async: waker protocol and task-slot correctness

## Goal
The `std/async` executor/task/waker layer has no data race, livelock or leak on its contested paths, and `Waker`
operations dispatch through the `RawWaker` vtable as SPEC-33 requires (T422 FU-I and the T421/T422 notes;
ADR-0042 §2).

## Scope
- Join-waker slot (`std/async/task.ax`: `task_set_join_waker` vs `task_wake_join_waker`) is a racy plain-field
  protocol: replace it with an atomic state protocol (e.g. a state word with REGISTERING/WAKING bits, SPEC-31
  orderings) so a wake between "check done" and "register" is never lost and the waker is dropped exactly once.
- `std/async/waker.ax:task_wake` spins on a CAS and livelocks against a self-waking task under the oracle's
  round-robin scheduler (T422 decision 6): make it wait-free (single fetch_or of NOTIFIED, enqueue only on the
  IDLE -> NOTIFIED transition), then let `TaskHandle.cancel`/`Drop` use it again.
- `tcb_poll_fn`'s `store(TASK_POLLING)` clobbers the cancel/detach flag bits (T422 decision 5): use a CAS/fetch-and
  that preserves the flag bits, the way `group_poll_fn` does.
- `Waker.wake`, `wake_by_ref`, `clone`, `drop` must call the vtable entries of their `RawWaker` (not a hard-wired
  executor path), so a user-defined waker works; test with a counting user waker.
- Detached tasks: when a detached task completes, its output is dropped (destructor runs exactly once); when a
  `TaskHandle` is dropped after completion, the stored output is dropped.
- Keep the T421/T422 public API; compiler workarounds may stay (removed in T422c after T444/T446).
- Tests in `tests/std/async/` (stress: 1000 iterations of register/wake interleavings with threads; oracle livelock
  case; user waker vtable counts; detached `Drop` counter), interp + native + native-O1, exact `// stdout:`.

## Acceptance
- [ ] New tests pass in all modes, 5 consecutive runs of each threaded test without a flake.
- [ ] All existing `tests/std/async/**` pass; WEAK-NATIVE 0.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T421a-report.md` with exact `## Files changed`.

## Out of scope
- Panic capture through unwinding (T536, P13); generic API shape (T422c); `compiler/`; `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 FU-I, T421/T422 notes)
- 2026-11-13 16:42:56 started (attempt 1) T421a-impl
