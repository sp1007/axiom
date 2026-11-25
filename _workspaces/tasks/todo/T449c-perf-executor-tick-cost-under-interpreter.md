---
id: T449c
title: Perf — cost per executor tick of the live std executor under the MIR interpreter (cancel_self_waking 60 s -> 144 s)
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T428a]
priority: 75
status: todo
attempts: 0
timeout_min: 240
paths: [tests/perf/p11_executor_interp_tick]
locks: [std/async/executor.ax, std/async/reactor.ax, std/async/timer.ax, std/async/task.ax, tests/std/async/waker]
spec: [spec/SPEC-34-executors-fibers.md, spec/SPEC-35-async-io.md]
covers: [REQ-ASY-060]
---
# T449c — Make an executor tick cheap when there is no I/O or timer work

## Why
`_workspaces/reports/T449a-qa.md` F3: measured alone under the MIR interpreter, `tests/std/async/waker/
cancel_self_waking.ax` grew from 60 s to 144 s (`join_waker_race` 26 s -> 43 s) when its bundle moved from the
pre-T423e/T426 executor to the live one, which polls the reactor, the timer wheel and I/O on every tick. Native runs
in < 1 s. The test timeout was raised to 420 s as headroom, not as a fix. The oracle is the reference executor for
async tests (REQ-ASY-060), so its per-tick cost multiplies across the whole async suite and the periodic full run.

## Scope
1. Profile one tick (count MIR steps per tick by function with the interpreter's existing step counters or
   `--interp-stats` if present; otherwise instrument a scratch build, not committed) for `cancel_self_waking`.
2. Remove avoidable per-tick work in std: e.g. skip `Reactor` polling when no I/O op is in flight and skip timer-wheel
   advancement when no timer is armed (constant-time checks of counters already kept), avoid re-scanning empty queues,
   avoid per-tick allocation. Behaviour (wake order, fairness, cancellation, deterministic scheduler order) must not
   change: every `tests/std/async/**` and `tests/conformance/p11/**` stdout stays identical.
3. Do not change `compiler/interp`. If the profile shows an interpreter hot spot, write it in the report's follow-ups
   with numbers (the architect creates a task).
4. Add `tests/perf/p11_executor_interp_tick/`: a deterministic MIR-step budget test (steps per 1,000 empty ticks, not
   wall time) so a future regression is caught; lower the `// timeout:` of `cancel_self_waking.ax` /
   `join_waker_race.ax` back toward 3x the new measured interp time.

## Acceptance
- [ ] `cancel_self_waking` interp time measured alone ≤ 70 s (report before/after with the same compiler and machine
      state) and identical stdout; `join_waker_race` not slower.
- [ ] `tests/std/async/**`, `tests/conformance/p11/**`, `tests/perf/p11_executor/**` pass with identical stdout.
- [ ] Normal gate. Report `_workspaces/reports/T449c-report.md` with an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T449a-qa.md F3)
