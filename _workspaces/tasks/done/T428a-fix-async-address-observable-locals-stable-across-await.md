---
id: T428a
title: Fix — address of an `async fn` local is not stable across `.await` (address-observable locals live in place, ADR-0050)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 15
status: done
attempts: 1
timeout_min: 300
paths: [tests/run/async/addr_stable_locals, tests/conformance/p11/e11_6_async_io/direct_slice_io_async_locals.ax]
locks: [compiler/mir/async_lower.ax, compiler/mir/drop.ax, std/async/task.ax, tests/std/async/executor, tests/std/async/structured, tests/std/async/waker, tests/std/async/waker_qa, tests/conformance/p11/e11_5_executors, tests/conformance/p11/e11_6_async_io, tests/perf/p11_executor, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0050-async-address-observable-locals-in-place.md, spec/SPEC-33-async.md, spec/SPEC-35-async-io.md]
covers: [REQ-ASY-122, REQ-ASY-047, REQ-ASY-157]
started: 2026-11-26 05:40:06
unblocks: 1
finished: 2026-11-26 10:13:55
---
# T428a — Address-observable `async fn` locals must be stable across `.await`

## Why
T428 (`_workspaces/reports/T428-report.md` F1, confirmed by `T428-qa.md`) found a spec violation of SPEC-35
AXS-AIO-012 item 2 and SPEC-33 AXS-ASY-005 item 3 (REQ-ASY-122):

```
async fn rx(b: *const AsyncUdpSocket) -> i64 {
    let mut buf: [16]u8 = [0u8; 16];
    let n = match unsafe { view(*b).recv_from(address_of_mut(buf[0]), 16usize).await } {
        Result.Ok(p) => p.0,
        Result.Err(_) => return -1i64,
    };
    (n as i64) * 1000i64 + (buf[0] as i64)
}
```
spawned with `LocalExecutor.spawn_local` and fed one datagram `"TIM"`: the oracle reports
`AX_UNSAFE_INTERP_UB use of dangling pointer` at `std/net/mod.ax:799` (the completion copy into the stale destination);
native prints `3000` instead of `3084`. Same root cause: `mut_view(local_stream).read_exact(..)/write_all(..).await` inside
an `async fn` (`ReadExactFuture` keeps a pointer to the local stream → oracle UB at `std/io/async_io.ax:723`).

Root cause: `compiler/mir/async_lower.ax` saves live locals into `(*self).live_v` on suspension and moves them back into
poll-frame locals on resume (ready block, "restore live locals"), so a local's address differs between polls.

## Rule (ADR-0050, SPEC-33 AXS-ASY-043 item 7, AXS-ASY-005 item 4)
A local that is the base of an address-of / borrow rvalue anywhere in the MIR body (conservative test) and is live across
at least one `.await` lives in place in its state field for its whole lifetime: every use in every synchronous segment
is rewritten to `(*self).live_v`; it is never saved/restored. Placing *all* cross-await locals in place is an allowed
simplification. Layout packing must not overlap such a field with another live field. Cancellation drop glue
(AXS-ASY-044) keeps dropping the field exactly once per state.

## Scope
1. Implement the rule in `compiler/mir/async_lower.ax` (and `compiler/mir/drop.ax` only if the drop glue must follow).
   Both the oracle and native run the same MIR, so no interpreter or backend special case is allowed.
2. Check that every std driver (`LocalExecutor.spawn_local`/`block_on`/`run_until`, `Executor.spawn`/`block_on`,
   `std.future.block_on`, `TaskGroup.spawn`) never moves a future after its first poll; record the result in the report
   (fix it in this task only if one does — then add the file to the change set and say so).
3. Regression tests `tests/run/async/addr_stable_locals/` (`modes: interp native`, exact `// stdout:`): the repro above
   (UDP `recv_from` into an async-local array), TCP `read`/`read_exact`/`write_all` on an async-local stream and buffer,
   a local whose address is taken before the first `.await` and read after the third, a loop that re-awaits with the same
   local buffer, and a cancelled (dropped while pending) future with an in-place local whose `Drop` runs exactly once.
   Each must fail on HEAD (oracle UB or wrong native value) and pass after the fix.
4. Direct form in the E11.6 suite: new `tests/conformance/p11/e11_6_async_io/direct_slice_io_async_locals.ax` (slice
   `read`/`recv_from`/`read_exact`/`write_all` into async-fn locals inside spawned tasks), and remove the workaround from
   `tcp_framing_split.ax` (split halves and scratch areas owned by `main` → owned by the tasks), keeping its `stdout:`.
   Do not edit the suite `README.md` (the P11 gate T311 updates its "Implementation limits" list).

## Acceptance
- [ ] All new tests pass in interp, native and native-O1; `WEAK-NATIVE 0` for them; they fail on HEAD (show it in the report).
- [ ] `tests/run/async/**`, `tests/mir/async/**`, `tests/ui/async/**`, `tests/std/async/**`, `tests/conformance/p11/**` pass.
- [ ] `--emit async-layout` (or the existing layout report) shows the in-place fields; MIR verifier clean.
- [ ] Normal gate including the selfhost groups of `compiler/mir`. Report `_workspaces/reports/T428a-report.md` with an exact
      `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T428 accept, `_workspaces/reports/triage-2026-11-25-T428.md`)
- 2026-11-25 19:38:31 started (attempt 1) T428a-impl
- 2026-11-26 01:42:03 block: round-1 fix done; taskgate fails on 2 e11_5 tests (spawn_affinity_vs_migration, fiber_in_async_and_threads) that cannot compile on live std: std.io vs std.text.string String/string_new collision when std.thread.spawn + executor imported; pre-existing (hidden by stale bundles); needs baseline entry + fix task
- 2026-11-26 04:17:41 unblocked (cycle 1) 
- 2026-11-26 05:40:06 started (attempt 1) T428a-qa
- 2026-11-26 10:13:55 accepted by QA -> done
