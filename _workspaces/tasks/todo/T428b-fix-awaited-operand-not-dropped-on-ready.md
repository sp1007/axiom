---
id: T428b
title: Fix — an operand `.await`ed inside an `async fn` is not dropped when the await completes (AXS-ASY-043 item 3)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428a]
priority: 30
status: todo
attempts: 0
timeout_min: 300
paths: [tests/run/async/await_operand_drop, tests/conformance/p11/e11_6_async_io/direct_race_in_task.ax]
locks: [compiler/mir/async_lower.ax, compiler/mir/drop.ax, compiler/mir/builder.ax, tests/conformance/p11/e11_6_async_io/cancel_token_reads.ax]
spec: [spec/SPEC-33-async.md, spec/SPEC-35-async-io.md]
covers: [REQ-ASY-058, REQ-ASY-018]
---
# T428b — Drop the awaited sub-future when its `.await` completes

## Why
T428 report F5 (`_workspaces/reports/T428-report.md`): with
```
struct D { counter: *mut i64 }
impl Future for D { type Output = i64; fn poll(self: mut_view<D>, cx: mut_view<Context>) -> Poll<i64> { Poll.Ready(7i64) } }
impl Drop for D { fn drop(self: mut_view<D>) { unsafe { *self.counter = *self.counter + 1i64; } } }
async fn t(c: *mut i64) -> i64 { let v = D { counter: c }.await; v }
```
`block_on(D { .. })` increments the counter once, but `t(c)` run with `spawn_local` leaves it unchanged. SPEC-33
AXS-ASY-043 item 3 requires "`Poll.Ready(val)`: runs `Drop` glue on `(*self).sub_fut_k`". Consequence in std: an I/O
future that completes through an adapter (`CancelRace`, `with_io_timeout_ms`) inside a task never runs its `Drop`, so its
in-flight op is never cancelled (no zombie, `Reactor.in_flight_count` stays 1).

## Scope
1. In `compiler/mir/async_lower.ax` (ready block `bb_ready_k`; or in the await lowering of `compiler/mir/builder.ax` if the sub-future is already lost there) drop `(*self).sub_fut_k` exactly once after the output
   is moved out and before resuming, for every await (including awaits in loops, in `match`/`if` arms, nested awaits
   and awaits of async-fn futures). Verify the cancellation glue (AXS-ASY-044) still drops the sub-future of the current
   state exactly once and never one that already completed (no double drop: state-tag discipline).
2. Synchronous `.await` paths must agree: `block_on` on the same value and an `async fn` wrapper give the same drop count.
3. Regression tests `tests/run/async/await_operand_drop/` (`modes: interp native`, exact `// stdout:`): the repro above
   (drop count 1), await inside a loop (count = iterations), ready-first-poll vs pending-then-ready sub-future, a nested
   async fn whose own locals have `Drop` (reverse order), and a task dropped while suspended (sub-future dropped once).
   Each case that fails on HEAD is shown failing in the report.
4. Direct form in the E11.6 suite: new `tests/conformance/p11/e11_6_async_io/direct_race_in_task.ax` — a
   `CancellationToken` race and a `with_io_timeout_ms` race on a TCP read **inside spawned tasks**, plus a file read
   cancelled by a token inside a task (QA note N1), checking zombie accounting and `in_flight_count == 0`; and remove the
   workaround from `cancel_token_reads.ax` (race futures driven by `block_on` in `main`, comment "follow-up F5") so the
   races run in tasks, keeping its `stdout:`. Do not edit the suite `README.md` (T311 updates it).

## Acceptance
- [ ] All new tests pass in interp, native and native-O1 with `WEAK-NATIVE 0`; the repro fails on HEAD.
- [ ] `tests/run/async/**`, `tests/mir/async/**`, `tests/std/async/**`, `tests/conformance/p11/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/mir`. Report `_workspaces/reports/T428b-report.md` with an exact
      `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T428 accept, `_workspaces/reports/triage-2026-11-25-T428.md`)
