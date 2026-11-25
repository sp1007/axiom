---
id: T449a
title: Baseline fix — std/async stale bundles, timer_wheel_100_timers flake, timer/timeout missing waker import
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 20
status: todo
attempts: 0
paths: [std/async/timer.ax, std/async/timeout.ax, tests/std/async/reactor, tests/std/async/executor, tests/std/async/structured, tests/std/async/waker, tests/std/async/waker_qa]
locks: [_workspaces/baseline-failures.txt]
spec: [spec/SPEC-35-async-io.md, spec/SPEC-34-executors-fibers.md]
covers: [REQ-ASY-154, REQ-TST-072]
---
# T449a — Baseline fix: std/async stale bundles, timer flake, missing waker import

## Why
The T427 gate (`_workspaces/reports/T427-qa.md` §5, §8) found failures at HEAD f9ecfc8d that are not caused by
T427 and were admitted to `_workspaces/baseline-failures.txt` on 2026-11-25 with this task as their fix task:
- `std/async/executor/check_async_bundles`, `std/async/structured/check_structured_bundles`,
  `std/async/waker/check_waker_bundles`, `std/async/waker_qa/check_waker_qa_bundles`: the committed bundles are
  older than the live `std/` sources they concatenate (`gen_tests.py --check` reports e.g.
  `qa_handle_cancel_await.ax actual=127224 vs expected=132469`). A later std change (T423e/T538/T426 era) made them
  stale; these generators are not in `tests/selfhost/generated-files.txt`, so the harness does not refresh them
  (harness side: T449b).
- `std/async/reactor/timer_wheel_100_timers.ax` [interp]: load-dependent failure under `-j 2` ("stdout differs at
  byte 30"), passes alone. The test is wall-clock based (`monotonic_ns() + 2 s`, 120 timers). Owner rule: a
  timing-dependent test is never baselined as "flaky" permanently; it is made deterministic.
- Not a baseline id, same area: `std/async/timer.ax:459` and `std/async/timeout.ax:128` call `cx.waker()` (an
  inherent method defined in `std/async/waker.ax`) without importing the waker module. A program that imports only
  `std.net` / `std.io.async_io` (no executor) fails in std with `AX_TYPE_UNKNOWN_FIELD`. Repro: a module with only
  `use std.net.AsyncTcpStream` + `use std.net.SocketAddr`, then `axiomc2 check`.

## Scope
1. Add the missing waker import(s) to `std/async/timer.ax` and `std/async/timeout.ax` (whatever makes
   `Context.waker` visible; no behaviour change). Add a regression test under `tests/std/async/reactor/` (a `check`
   or `run` test that imports only `std.net`/`std.asyn.timer` without any executor) that fails before the fix.
2. Make `timer_wheel_100_timers.ax` deterministic without weakening what it checks (REQ-ASY-154: many timers on one
   wheel, firing order by deadline, same thread, no OS thread per timer). Acceptable approaches: deadlines spaced
   far enough apart relative to scheduler jitter that ordering is unambiguous, ordering checked by deadline rank
   with ties allowed only for equal deadlines, or a virtual/injected clock if the timer API already allows one.
   Do not merely raise the timeout. Demonstrate stability: 10 consecutive `--filter std/async/reactor -j 2
   --no-cache` runs with 0 failures (log in the report).
3. After steps 1–2 (which change bundled std sources), regenerate the four bundle directories with their
   `gen_tests.py` and confirm `gen_tests.py --check` passes in each. Do not hand-edit bundles.
4. Remove the 5 ids admitted for T449a from `_workspaces/baseline-failures.txt` in the same change.

## Acceptance
- [ ] The 4 bundle checks pass; every test in the 4 bundle directories passes in all its modes.
- [ ] `timer_wheel_100_timers` passes 10/10 under `-j 2 --no-cache` (interp and native); expectation unchanged in
      strength (exact stdout still checked).
- [ ] New no-executor import test passes; it fails on HEAD before the fix (state the observed diagnostic).
- [ ] The 5 T449a lines are removed from `_workspaces/baseline-failures.txt`.
- [ ] Normal gate. Report `_workspaces/reports/T449a-report.md` with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T427 accept, `_workspaces/reports/triage-2026-11-25-T427.md`)
