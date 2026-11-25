---
id: T428e
title: Fix — multi-worker `Executor` + reactor: unsynchronized reactor counters (data race) and I/O starved while tasks are runnable
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T428d, T449b]
priority: 60
status: todo
attempts: 0
paths: [tests/std/async/executor_reactor_mt]
locks: [std/async/reactor.ax, std/async/executor.ax, tests/conformance/p11/e11_6_async_io/taskgroup_async_io.ax]
spec: [spec/SPEC-34-executors-fibers.md, spec/SPEC-35-async-io.md, spec/SPEC-30-concurrency.md]
covers: [REQ-ASY-168, REQ-ASY-165]
---
# T428e — Multi-worker Executor and reactor integration

## Why
Two related defects of the multi-worker `Executor` ↔ `Reactor` integration found by T428
(`_workspaces/reports/T428-report.md`), merged because they are fixed in the same two files and tested by the same
two-worker I/O scenarios:
- **F4 (medium)**: with `Executor.new(2)` and socket I/O the oracle race detector reports `AX_UNSAFE_INTERP_UB
  unsynchronized data race` on `Reactor.in_flight_count`: `register_op`/`turn` write it under `Reactor.lock`, but
  `has_pending_work()` / `in_flight_count()` (`std/async/reactor.ax` ~164–169) read it without the lock from the executor
  idle loop (`std/async/executor.ax` worker loop ~620), and `has_pending_work` also reads the timer wheel without its lock.
- **F6 (medium)**: the worker loop turns the reactor only when no task is runnable, so tasks that wait with `yield_now`
  loops starve I/O completions forever (`LocalExecutor` turns every 32 ticks and does not have the problem).

## Rules (architect, triage 2026-11-25)
1. Every reactor field read by more than one thread is either atomic (`Atomic<usize>` with documented orderings) or read
   under `Reactor.lock`; the timer-wheel emptiness check takes the wheel lock (or an atomic `active` count). No
   "benign race" exceptions: the oracle race detector is the judge (SPEC-30).
2. Fairness: a worker that has polled tasks for `REACTOR_TURN_INTERVAL` (32, as `LocalExecutor`) consecutive times without
   turning the reactor performs a non-blocking turn (`turn(Some(0))` / `poll_nonblocking`) before the next task; at most
   one worker at a time turns with a non-zero timeout. Record the constant and the rule as one sentence in the report
   (the architect folds it into SPEC-34).

## Scope
1. Implement rules 1–2 in `std/async/reactor.ax` and `std/async/executor.ax`.
2. Regression tests `tests/std/async/executor_reactor_mt/` (`modes: interp native`, exact `// stdout:`):
   `Executor.new(2)` with 4 tasks doing TCP echo while `main` polls `in_flight_count()` (no race report in interp);
   2 workers where one task spins on `yield_now()` until a UDP datagram arrives that another task receives (completes;
   hangs on HEAD — use `// timeout:`); timers + I/O with 2 workers. Each must fail on HEAD in at least one mode.
3. Direct form in the E11.6 suite: switch `taskgroup_async_io.ax` (live-std after T428d) to `Executor.new(2)` and let
   `main` observe the reactor while the group runs (remove the "one worker" workaround, follow-up F4); keep `stdout:`.
   Do not edit the suite `README.md` (T311 updates it).

## Acceptance
- [ ] New tests pass in interp, native and native-O1 with `WEAK-NATIVE 0`; 10/10 repeated runs of the directory at `-j 2`
      without a failure (concurrency tests must be deterministic in their checked output).
- [ ] `tests/std/async/**`, `tests/conformance/p11/**`, `tests/perf/p11_executor` pass.
- [ ] Normal gate. Report `_workspaces/reports/T428e-report.md` with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T428 accept, `_workspaces/reports/triage-2026-11-25-T428.md`)
