---
id: T428f
title: Fix — `std.asyn.timeout.Timeout` around pending I/O blocks forever natively under `LocalExecutor.block_on` (no timer registered, self-wake lost)
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T449b]
priority: 60
status: todo
attempts: 0
paths: [tests/std/async/timeout_io_block_on, tests/conformance/p11/e11_6_async_io/timeout_adapter_io.ax]
locks: [std/async/timeout.ax, std/async/timer.ax, std/async/executor.ax]
spec: [spec/SPEC-34-executors-fibers.md, spec/SPEC-35-async-io.md, spec/SPEC-33-async.md]
covers: [REQ-ASY-159, REQ-ASY-153]
---
# T428f — `Timeout` must wake at its deadline under every driver

## Why
T428 report F8: `Timeout<F, T>.poll` (`std/async/timeout.ax` ~117) returns `Pending` after `cx.waker().wake_by_ref()`
and registers no timer. Under `LocalExecutor.block_on`/`run_until` (`std/async/executor.ax` ~270) the waker is the null
waker, so the self-wake is lost; the reactor has an in-flight I/O op, `next_timer_delay_ns()` is `None`, and
`turn(None)` waits forever for an I/O completion that never comes — natively. The oracle returns immediately, so this
is also an interp/native divergence. The suite works around it with `with_io_timeout_ms` (timer-wheel based,
AXS-AIO-023). QA note N1 also asks for a file-read timeout case.

## Rules (architect, triage 2026-11-25)
1. A deadline adapter registers its deadline with the current timer wheel (as `SleepFuture` does, SPEC-34 AXS-EXEC-024;
   implement `Timeout` on an embedded `SleepFuture` / timer entry, cancelled on completion and on drop) and never relies
   on busy self-waking when a timer wheel is available. Without any timer wheel (no reactor) the self-wake fallback stays.
2. Executor drivers never block in `turn(None)` while a registered timer exists; a self-wake through the driver's waker
   during `poll` makes the driver re-poll without blocking (give `run_until`/`block_on` a real flag waker instead of the
   null waker if needed).
3. The oracle and native must agree: find why the oracle returns immediately and make both follow rules 1–2 (if the cause
   is in `compiler/interp/oracle.ax`, report it as a spec deviation; do not edit the oracle here — the architect files it).

## Scope
1. Implement rules 1–2 in `std/async/timeout.ax` (and `timer.ax`/`executor.ax` as needed).
2. Regression tests `tests/std/async/timeout_io_block_on/` (`modes: interp native`, exact `// stdout:`, `// timeout:` so
   HEAD fails instead of hanging): `with_timeout_ms(20, tcp_read)` under `LocalExecutor.block_on` and under
   `Executor.block_on` with no data → `Err(TimeoutError)` after ≥ 20 ms (lower bound only); same with data arriving first
   → `Ok`; the timer is cancelled on early completion (no leaked timer: `Reactor` timer count 0); a dropped pending
   `Timeout` leaves no timer.
3. Direct form in the E11.6 suite: new `tests/conformance/p11/e11_6_async_io/timeout_adapter_io.ax` — `std.asyn.timeout`
   `Timeout` around pending TCP/UDP reads and a file read (N1) under `block_on`, with buffer-safety checks as in
   `timeout_reads_buffer_safety.ax`. Do not edit the suite `README.md` (T311 updates it).

## Acceptance
- [ ] New tests pass in interp, native and native-O1 with `WEAK-NATIVE 0`; the native leg fails (timeout) on HEAD.
- [ ] `tests/std/async/**`, `tests/conformance/p11/**` pass; 10/10 repeated runs of the new directory at `-j 2`.
- [ ] Normal gate. Report `_workspaces/reports/T428f-report.md` with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T428 accept, `_workspaces/reports/triage-2026-11-25-T428.md`)
