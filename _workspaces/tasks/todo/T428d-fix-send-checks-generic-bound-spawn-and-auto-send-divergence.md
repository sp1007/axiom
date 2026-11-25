---
id: T428d
title: Fix — Send checks: live `TaskGroup.spawn` rejects every future (generic `F: Send` bound ignored) and native/oracle disagree on future Send (`SocketAddr`, `SleepFuture`)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T449b]
priority: 30
status: todo
attempts: 0
timeout_min: 300
paths: [tests/ui/async/send_generic_bound, tests/run/async/send_futures_executor]
locks: [compiler/types/typeck.ax, compiler/traits/solver.ax, compiler/driver/pipeline.ax, std/async/timer.ax, tests/conformance/p11/e11_6_async_io/taskgroup_async_io.ax, tests/conformance/p11/e11_6_async_io/src/taskgroup_async_io.axsrc, tests/conformance/p11/e11_6_async_io/gen_tests.py, tests/conformance/p11/e11_6_async_io/check_conformance_bundles.test]
spec: [spec/SPEC-33-async.md, spec/SPEC-34-executors-fibers.md, spec/SPEC-30-concurrency.md]
covers: [REQ-ASY-042, REQ-ASY-092]
---
# T428d — Correct and mode-independent Send checking for spawned futures

## Why
Two defects found by T428 (`_workspaces/reports/T428-report.md`), merged because both are Send-obligation evaluation
bugs in the same checker and both block multi-threaded task tests from using the live std:
- **F3 (high)**: `async fn five(a: i64) -> i64 { a }` +
  `let mut group: TaskGroup<i64> = TaskGroup.new(); let _ = group.spawn(view(exec), five(5i64));` in a program that does
  `use std.asyn.group.TaskGroup` (live `--std-root std`) fails with `AX_CONC_CAPTURE_NOT_SEND` at
  `std/async/group.ax:285` (`exec.spawn(fut)` inside `spawn<F: Future<Output = T> + Send>`), for every future, in both
  `run --interp` and `build`. `Executor.spawn(five(5i64))` directly is fine. The spawn-capture check in
  `compiler/types/typeck.ax` (~12214 and the `HIR_EXPR_PATH` branch ~12440) does not honour the in-scope generic bound
  `F: Send` / `where T: Send` of the enclosing generic function. Every TaskGroup test of the repo is a bundle, which hides it.
- **F7 (low)**: the native pipeline reports `AX_ASYNC_FUTURE_NOT_SEND` (`compiler/traits/solver.ax` ~3002) for futures
  holding a `SocketAddr` ("explicit negative impl for `SocketAddr`" — std declares none; `SocketAddr` is
  `@derive(Copy)` plain data) or a `SleepFuture` ("field `wheel` is not `Send`") across `.await`, while the oracle pipeline
  reports nothing. A type-level check must not depend on the execution mode.

## Rules (architect, triage 2026-11-25)
1. A value whose type is a generic parameter (or an associated type projection) satisfies `Send` when an in-scope bound or
   `where` clause says so; the check is re-done on the monomorphic type only for types the user wrote, never to second-guess
   a bound already proven at the generic call site.
2. Auto-`Send` of a struct is the conjunction over its fields (SPEC-30); a negative impl is reported only when one is
   declared. Arrays/tuples of `Send` are `Send`.
3. The same Send/Sync obligations are checked, with the same diagnostics, by `run --interp`, `build` and `check`
   (one checker in the shared front half of `compiler/driver/pipeline.ax`).
4. `SleepFuture` is `Send`: its only non-`Send` field is `wheel: *mut TimerWheel`, and `TimerWheel` is internally locked
   (`TimerWheel.lock`) and outlives every registered timer. Add `unsafe impl Send for SleepFuture {}` in
   `std/async/timer.ax` with that justification as a comment.

## Scope
1. Fix rules 1–3 in `compiler/types/typeck.ax` / `compiler/traits/solver.ax` (and `compiler/driver/pipeline.ax` if the
   divergence is a pipeline-ordering issue). Find the root cause; do not special-case `TaskGroup`, `SocketAddr` or
   std modules.
2. Rule 4 in `std/async/timer.ax` (this task waits for T449a/T449b, which own `timer.ax` and the std-bundle regeneration).
3. Regression tests:
   - `tests/ui/async/send_generic_bound/`: a user generic `fn spawn_all<F: Future<Output = i64> + Send>(..)` forwarding to
     `Executor.spawn` (accepted); the same without `+ Send` (rejected with `AX_CONC_CAPTURE_NOT_SEND` at the user's call);
     a future holding, across `.await`, a local of a user struct with a raw-pointer field and no `unsafe impl Send`
     (rejected, same diagnostic in `--interp` and `build`);
     a future holding `SocketAddr` / `SleepFuture` across `.await` (accepted in both).
   - `tests/run/async/send_futures_executor/` (`modes: interp native`, exact `// stdout:`): live-std `TaskGroup.spawn`
     of async-fn futures on `Executor`; tasks that keep a `SocketAddr` and sleep across `.await` on `Executor`.
4. Direct form in the E11.6 suite: turn `tests/conformance/p11/e11_6_async_io/taskgroup_async_io.ax` into a plain live-std
   run test (its program comes from `src/taskgroup_async_io.axsrc`); delete the bundle generator `gen_tests.py`, the
   `src/` input and `check_conformance_bundles.test` when no bundle remains in the directory; keep the `stdout:` line.
   The bundled TaskGroup tests in `tests/std/async/structured` and `tests/conformance/p11/e11_5_executors` may be
   converted the same way only if their owners' files are free (not required here). Do not edit the suite `README.md`.

## Acceptance
- [ ] F3 repro accepted and runs in interp, native, native-O1; the `ui` cases give identical diagnostics in `--interp`
      and `build`; each case is shown failing on HEAD.
- [ ] `tests/ui/**`, `tests/typeck/**`, `tests/std/async/**`, `tests/conformance/p11/**`, `tests/run/async/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/types` and `compiler/traits`. Report
      `_workspaces/reports/T428d-report.md` with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T428 accept, `_workspaces/reports/triage-2026-11-25-T428.md`)
