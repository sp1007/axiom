# T422c report — std/async on the SPEC-34 API shape

## Summary

`std.asyn` (`std/async/`) now has the API that SPEC-34 specifies, written with the generic features
that T444–T449, T422a, T422b and T421a made available:

- `Executor.spawn(fut)` / `LocalExecutor.spawn_local(fut)`, **without a poll function**. The poll
  function is built inside the generic method as the value `task_poll_fn<F, T>` (FU-J fixed).
- **`impl<T> Future for TaskHandle<T>`** and **`impl<T> Future for LocalTaskHandle<T>`**
  (`Output = Result<T, TaskError>`). They replace the `i64`-only impls.
- `handle.join()` now returns a future (`TaskJoin<T>`, `Output = TaskResult<T>`), matching SPEC
  `async fn join(self)`. The old blocking spin join is kept as `join_blocking()` for code that does
  not run inside a task.
- **`TaskGroup<T>`** is generic:
  - `group.spawn(view(exec), fut)` spawns the child itself. `adopt(handle)` is gone. A refused child
    (group cancelled, failed or timed out, or governor quota full) is now refused *before* it is
    spawned: the future is simply dropped.
  - `next()` returns the future `GroupNext<T>` (`Output = Option<Result<T, TaskError>>`).
  - `join_all(self)` returns the future `GroupJoinAll<T>` (`Output = Result<GroupResults<T>, TaskError>`).
  - `try_next()` and `next_blocking()` return `Option<Result<T, TaskError>>`.
  - `GroupResults<T>` has methods (`len`, `is_empty`, `get_ptr`, `pop`), and its `Drop` drops the
    elements. This replaces `results_get_ptr` / `results_drop_all`.
- **`Timeout<F, T>`** is a generic deadline adapter over any future
  (`Output = Result<T, TimeoutError>`). It comes with `with_deadline`, `with_timeout_ns` and
  `with_timeout_ms` for any `F: Future`. The following are removed because the generic adapter
  covers them: `LocalTimeout`, `TimeoutOutcome`, `local_with_*` and `poll_deadline`.
- **One poll function for every task.** `tcb_poll_fn` now has the panic containment of the old
  `group_poll_fn` (`FLAG_PANIC_REQUESTED`, moved to `waker.ax`). `task_panic` moved to
  `std.asyn.task`. `group_poll_fn` and `group_request_cancel` are removed.
- **Compiler workarounds removed:**
  - `WorkerData.executor` and `ChildLink.state` are typed pointers again (FU-1 fixed by T444).
  - Wait-queue nodes in `sync.ax`, `channel.ax` and `cancel.ax`, and the TaskHandle join slot, store
    a real `Waker` field instead of `waker_data`/`waker_vt` pairs (FU-3 fixed by T444). A store
    through a raw pointer does not drop the old bits, so the old waker is moved out first.
  - Methods are called on `mut_view` receivers directly, without `mut_view(*self)` (FU-6 fixed by
    T445).
  - Fields are compared directly instead of through locals (`a.f < b.g`; FU-A fixed by T422a).
  - Function-pointer fields are called directly (`((*vt).wake)(data)`; FU-2 fixed by T422b).
  - The other `i64`-only futures are generic now: `AsyncMutexLockFuture<T>`, `SendFuture<T>` and
    `RecvFuture<T>`.
- **No deprecated wrappers are kept.** With the coordinator's approval, the three outside suites that
  used the old names were moved to the new API and regenerated with their own generators:
  `tests/conformance/p11/e11_5_executors`, `tests/perf/p11_executor`, and `tests/std/fiber` (only
  re-checked: its bundles embed no std/async file). So no old name is still needed anywhere.

## Deviation table (T421 "Design decisions", T422 "Deviations" 1–3, 7–10)

| deviation | status |
|---|---|
| T421: explicit `poll_fn` argument on `spawn` / `spawn_local` | **resolved**: `spawn(fut)` / `spawn_local(fut)`; the poll function is `task_poll_fn<F, T>` formed inside the generic method |
| T421: `TaskHandle<T>` is a `Future` only for `T = i64` (same for `LocalTaskHandle`) | **resolved**: `impl<T> Future for TaskHandle<T>` / `LocalTaskHandle<T>` |
| T421: `join()` is a blocking spin, not `async fn` | **resolved**: `join()` returns the future `TaskJoin<T>`; the blocking form is kept as `join_blocking()` (extra API for non-task code) |
| T421: `Executor` is a `Copy` raw handle, not `Arc<ExecutorInner>` | **kept** (not a compiler gap): `std.sync.arc` is not used from `std.asyn` (T422 decision 10). Tasks copy the handle to spawn children. Revisit with E11.6 |
| T421: idle workers `thread_yield` instead of parking on the futex | **kept**: not an API shape item. T424 measured the executor with it; parking belongs with the E11.6 reactor (T426) |
| T422-1: `TaskGroup` not generic | **resolved**: `TaskGroup<T>` |
| T422-2: `adopt(handle)` instead of `spawn(exec, fut)` | **resolved**: `group.spawn(view(exec), fut) -> Result<TaskId, GroupError>`. The spec's `spawn` returns nothing; the `Result` only adds the refusal reason |
| T422-3: `Timeout` not generic (task handles only) | **resolved with one kept detail**: `Timeout<F, T>` over any future. The output type is a second type parameter instead of `Timeout<F: Future>` (repro R1 below). Callers never write it: `with_deadline` / `with_timeout_*` infer it |
| T422-7: resource accounting units | unchanged (not a deviation from the spec text); `Tasks` is charged at `spawn`, released at collection |
| T422-8: uncollected outputs of a dropped group are leaked | **resolved** (by T421a's `default_task_drop` through the poll function, now the only poll function). Covered by `waker/detached_output_drop` F and `waker_qa/qa_group_drop_detached` |
| T422-9: `GroupResults<T>` generic only in its pointer; free `results_get_ptr` / `results_drop_all` | **resolved**: methods `len` / `is_empty` / `get_ptr` / `pop`, and `Drop` drops the elements. **Kept**: `join_all` returns `GroupResults<T>`, not the spec's `Vec<T>`, because std has no generic method-style `Vec<T>` (`std.alloc.vec` is the type-erased free-function form) |
| T422-10: no `Arc`; own refcounted cancel/governor states; `with_governor(view<ResourceGovernor>)` | **kept** (library, not a compiler gap): the same reason as `Executor` |
| T422-1 corollary: `next()` only for `i64` children (`GroupNext` concrete) | **resolved**: `GroupNext<T>` |
| T422-4 (not in the list, for completeness): cooperative panic containment | unchanged; T536 (ADR-0042 §2) |
| T422-5/6: `group_poll_fn` / `group_request_cancel` stand-ins | **resolved**: merged into `tcb_poll_fn` / `task_request_cancel` |

## Kept compiler-gap workarounds and minimal repros (for the architect)

- **R1 — `F.Output` and bound-only impl parameters.**
  - `fn spawn<F: Future>(self: view<Exec>, fut: F) -> Handle<F.Output>` gives `AX_NAME_UNRESOLVED`
    on `F.Output`. The same happens in `type Output = Result<F.Output, E>` of `impl<F: Future>`.
  - With `impl<F: Future<Output = T>, T> Future for Timeout<F>` (T fixed only through the bound),
    every caller of `t.poll(cx)` gets an unknown `T` (`AX_TYPE_UNKNOWN_FIELD` /
    `AX_TYPE_MISMATCH`). This holds even for a concrete `F` (`Timeout<PairFut>`) and with an
    annotated result.
  - Workaround: every std signature uses `<F: Future<Output = T>, T>`, and `Timeout` carries `T` in
    its type (`Timeout<F, T>` with an `output_marker: *const T` field).
  - The same applies to `GroupResults<T>` / `TaskGroup<T>`'s `output_marker`. `TaskGroup` needs no
    marker for layout; the marker only names `T` so that it is not a phantom parameter.
  - Owner: semantics (the T448 "known limit" extended to associated-type projections).
- **R2 — group output type from `spawn`.**
  - `let mut g = TaskGroup.new(); g.spawn(view(exec), fut_returning_i64);` with no other use of
    `g`'s results gives `AX_TYPE_UNKNOWN` on `TaskGroup.new()`. The impl-level `T` is not inferred
    from the method's `F: Future<Output = T>` bound: this is T448's documented limit (method-call
    bound check only for non-generic impls).
  - Tests write `TaskGroup<i64>` where nothing else fixes `T` (12 sites). When the result type is
    used later (`join_all` + arithmetic), inference already works (`group_join_all`).
- **T422d (filed during this task) — native `.await` on a generic `Future` impl.** Interp is correct.
  - Natively, standalone it fails with `AX_LINK_UNDEFINED_SYMBOL: poll`.
  - Inside a bundle it links to another `poll` and segfaults.
  - A concrete `impl Future for Wrap<i64>` works. Repro:
    ```axiom
    struct Wrap<T> { pub v: T, pub n: i32 }
    impl<T> Future for Wrap<T> { type Output = Result<T, Er>; fn poll(self: mut_view<Wrap<T>>, cx: mut_view<Context>) -> Poll<Result<T, Er>> { ... } }
    async fn outer() -> i64 { let r = Wrap { v: 41i64, n: 2i32 }.await; ... }   // block_on(outer())
    ```
  - Affects `handle.await` and `group.join_all().await` in async fns. `structured/spec34_task_group_example`
    carries `// native-after: T422d`. Hand-written futures that call `.poll()` directly work natively
    (`group_two_output_types` covers `TaskHandle<T>`, `TaskJoin<T>`, `GroupNext<T>` and
    `GroupJoinAll<T>` natively).
- **T422e (filed during this task) — `AsyncMutexGuard` held across `.await` is rejected.**
  - The error is `AX_ASYNC_GUARD_ACROSS_AWAIT: drop flag local is not initialized in bb0`.
  - The check is keyed on the type name: the same program with the struct renamed compiles and runs.
  - The `.lock()` receiver additionally gets `AX_CONC_GUARD_ESCAPE`. Repro:
    ```axiom
    struct AsyncMutexGuard<T> { pub v: T }   impl<T> Drop for AsyncMutexGuard<T> { ... }
    async fn hold() -> i64 { let mut h = Ready { n: 5i64 }.await; Pend { done: false }.await; h.v }  // Ready: Output = AsyncMutexGuard<i64>
    ```
  - `structured/spec34_local_executor_example` (SPEC-34 §6.1) carries
    `// xfail: T422e AsyncMutexGuard across await rejected`.
- **R3 — spurious `AX_PAT_UNREACHABLE`.** It fires on the second arm of
  `match r { Result.Ok(v) => .., Result.Err(E.A) => .., Result.Err(E.B) => .. }`. Run-time behaviour
  is correct. Tests use a nested `match e { .. }` instead. This is probably what T499c ("unify
  exhaustiveness checker", in progress) fixes; to be confirmed there.
- **R4 — match bindings are dropped at the end of the enclosing block, not at the end of the arm.**
  In `match g { G.Has(x) => { .. } }` the `x` (a `Drop` type) is dropped at function end (repro:
  `mdrop.ax` pattern, interp == native).
  - SPEC-12 drop scopes should be checked by the architect: is this intended (T445 restored it on
    purpose) or a gap?
  - `group_two_output_types` moves bindings into a local (`let owned = t;`) so that its live-count
    checks are exact.
- **R5 — `drop_in_place<F>(address_of_mut((*tcb).future))` does not run `F`'s destructor** (interp
  and native). `tcb_drop_future` / `tcb_drop_payload` therefore keep the existing move-into-`[1]F`
  idiom. Not investigated further. `drop_in_place<T>(ptr + i)` with plain pointer arithmetic works
  (used by `GroupResults` and `std.alloc.vec`).

## Decisions

- **`join()` vs `join_blocking()`.** `join()` became the SPEC future (`TaskJoin<T>`). The synchronous
  form is still needed by tests and by `main` code that is not running inside a task, so it was
  renamed, not removed.
- **Refusal before spawning.** The old `adopt` spawned the task and then refused it.
  `TaskGroup.spawn` checks cancellation and the quota before it spawns. A refused future is never
  polled, and its destructor runs immediately.
- **No deprecated wrappers.** The coordinator extended `paths` to the three outside suites, so their
  sources were migrated instead.
- **`Timeout` cancellation timing.** A `Timeout` that expires now drops its inner future (for a
  `TaskHandle`: cancels the task) when the `Timeout` is dropped, as SPEC-34 AXS-EXEC-024 states.
  Before, it cancelled at the moment of expiry. The tests drop the `Timeout` (it is consumed by
  `run_until`) before they check.

## Tests

All generated bundles come from the edited `src/*.axsrc` (or the program strings in
`executor/gen_tests.py`) by each directory's `gen_tests.py`. Every generator `--check` passes.

New tests:

| test | covers |
|---|---|
| `structured/group_two_output_types` | two live groups with different `T` (`i64`, `Tracked` 24 bytes with `Drop`), `next()` / `join_all()` futures, `GroupResults<Tracked>` drop and `pop`, `spawn(fut)` whose captured value needs drop (completed and cancelled), `TaskHandle<Tracked>` as a `Future` inside a parent task, `handle.join()` future. Exact drop accounting; interp, native, native-O1 |
| `structured/spec34_task_group_example` | SPEC-34 §6.2 (async fns, `group.spawn(view(exec), compute_chunk(..))`, `join_all().await`); interp; `native-after: T422d` |
| `structured/spec34_local_executor_example` | SPEC-34 §6.1 (`spawn_local` of async fns capturing `Rc`, `AsyncMutex` guard across `.await`, `h.await`); `xfail: T422e` |
| `structured/deadline_timeout` (rewritten) | `Timeout<F, T>` over task handles (pass-through, expiry, nested deadlines, budget narrowing) **and over user futures** (expiry drops the future; completion passes through) |

All existing tests of the 7 directories were moved to the new API. Their expected `stdout` is
unchanged; a refused `spawn` now never spawns.

## Results (snapshot `build-snap-T422c`, HEAD 4b945b9 + the change set below, `build/axiomc2.exe` BUILD-AXIOMC OK, fixed point O1 OK; `-j 2`)

- `std/async/ conformance/p11/e11_5_executors/ perf/p11_executor/ std/fiber/`:
  **TOTAL 240 PASS 229 FAIL 0 SKIP 2 XFAIL 9, WEAK-NATIVE 0** (`_workspaces/T422c_suites.log`).
  - SKIP 2: the native and native-O1 legs of `spec34_task_group_example` (`native-after: T422d`).
  - XFAIL 9 = 3 files x 3 legs:
    - `spec34_local_executor_example` (`xfail: T422e`);
    - the two existing `std/fiber/*_xfail.ax`, which are not mine.
  - Included and passing: every freshness check — `check_async_bundles`, `check_structured_bundles`,
    `check_waker_bundles`, `check_waker_qa_bundles`, `check_conformance_bundles`,
    `check_perf_bundles`, `check_fiber_bundles` — and the `compile_live_*` tests.
- `run/async/ ui/concurrency/ run/layout_fwd_pointee/`: TOTAL 85 PASS 85 FAIL 0.
- `--smoke`: TOTAL 48 PASS 48 FAIL 0. Its WEAK-NATIVE 3 come from pre-existing smoke picks, not from
  this change.
- The new and rewritten tests were also run by hand in interp, native and native-O1 with the exact
  stdout: `group_join_all`, `group_two_output_types`, `deadline_timeout`.
- Generators: every `gen_tests.py --check` in the 7 directories reports OK. No selfhost bundle and no
  file outside `paths` was touched.


## Files changed
- std/async/cancel.ax
- std/async/channel.ax
- std/async/executor.ax
- std/async/group.ax
- std/async/mod.ax
- std/async/sync.ax
- std/async/task.ax
- std/async/timeout.ax
- std/async/waker.ax
- tests/conformance/p11/e11_5_executors/asyncmutex_cancel_wakes_next.ax
- tests/conformance/p11/e11_5_executors/cancel_race_linearizes.ax
- tests/conformance/p11/e11_5_executors/cancel_tree_groups.ax
- tests/conformance/p11/e11_5_executors/channel_cancel_safety.ax
- tests/conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax
- tests/conformance/p11/e11_5_executors/local_cancel_drop_order.ax
- tests/conformance/p11/e11_5_executors/sibling_failure_isolation.ax
- tests/conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax
- tests/conformance/p11/e11_5_executors/src/asyncmutex_cancel_wakes_next.axsrc
- tests/conformance/p11/e11_5_executors/src/cancel_race_linearizes.axsrc
- tests/conformance/p11/e11_5_executors/src/cancel_tree_groups.axsrc
- tests/conformance/p11/e11_5_executors/src/channel_cancel_safety.axsrc
- tests/conformance/p11/e11_5_executors/src/fiber_in_async_and_threads.axsrc
- tests/conformance/p11/e11_5_executors/src/local_cancel_drop_order.axsrc
- tests/conformance/p11/e11_5_executors/src/sibling_failure_isolation.axsrc
- tests/conformance/p11/e11_5_executors/src/spawn_affinity_vs_migration.axsrc
- tests/perf/p11_executor/channel_ping_pong.ax
- tests/perf/p11_executor/spawn_poll_throughput.ax
- tests/perf/p11_executor/src/channel_ping_pong.axsrc
- tests/perf/p11_executor/src/spawn_poll_throughput.axsrc
- tests/perf/p11_executor/src/steal_fanout_fanin.axsrc
- tests/perf/p11_executor/steal_fanout_fanin.ax
- tests/std/async/executor/async_channel_pipeline.ax
- tests/std/async/executor/async_mutex_across_await.ax
- tests/std/async/executor/async_semaphore_limits.ax
- tests/std/async/executor/gen_tests.py
- tests/std/async/executor/local_executor_rc.ax
- tests/std/async/executor/lost_wake_prevention.ax
- tests/std/async/executor/qa_cancel_waiters.ax
- tests/std/async/executor/qa_handle_cancel_await.ax
- tests/std/async/executor/work_stealing_executor.ax
- tests/std/async/executor/work_stealing_spawn_tree.ax
- tests/std/async/structured/cancel_token_tree.ax
- tests/std/async/structured/deadline_timeout.ax
- tests/std/async/structured/gen_tests.py
- tests/std/async/structured/group_deadline.ax
- tests/std/async/structured/group_drop_cancels.ax
- tests/std/async/structured/group_generic_output.ax
- tests/std/async/structured/group_governor_quota.ax
- tests/std/async/structured/group_join_all.ax
- tests/std/async/structured/group_sibling_cancel.ax
- tests/std/async/structured/handle_drop_vs_detach.ax
- tests/std/async/structured/qa_nested_groups_races.ax
- tests/std/async/structured/resource_governor_limits.ax
- tests/std/async/structured/src/cancel_token_tree.axsrc
- tests/std/async/structured/src/deadline_timeout.axsrc
- tests/std/async/structured/src/group_deadline.axsrc
- tests/std/async/structured/src/group_drop_cancels.axsrc
- tests/std/async/structured/src/group_generic_output.axsrc
- tests/std/async/structured/src/group_governor_quota.axsrc
- tests/std/async/structured/src/group_join_all.axsrc
- tests/std/async/structured/src/group_sibling_cancel.axsrc
- tests/std/async/structured/src/handle_drop_vs_detach.axsrc
- tests/std/async/structured/src/qa_nested_groups_races.axsrc
- tests/std/async/structured/src/task_panic_contained.axsrc
- tests/std/async/structured/task_panic_contained.ax
- tests/std/async/waker/cancel_self_waking.ax
- tests/std/async/waker/detached_output_drop.ax
- tests/std/async/waker/join_waker_race.ax
- tests/std/async/waker/src/cancel_self_waking.axsrc
- tests/std/async/waker/src/detached_output_drop.axsrc
- tests/std/async/waker/src/join_waker_race.axsrc
- tests/std/async/waker/src/user_waker_vtable.axsrc
- tests/std/async/waker/user_waker_vtable.ax
- tests/std/async/waker_qa/qa_cancel_during_poll.ax
- tests/std/async/waker_qa/qa_group_drop_detached.ax
- tests/std/async/waker_qa/qa_join_drop_vs_complete.ax
- tests/std/async/waker_qa/qa_late_waker_drop.ax
- tests/std/async/waker_qa/qa_wake_during_poll.ax
- tests/std/async/waker_qa/src/qa_cancel_during_poll.axsrc
- tests/std/async/waker_qa/src/qa_group_drop_detached.axsrc
- tests/std/async/waker_qa/src/qa_join_drop_vs_complete.axsrc
- tests/std/async/waker_qa/src/qa_late_waker_drop.axsrc
- tests/std/async/waker_qa/src/qa_wake_during_poll.axsrc
- tests/std/async/structured/group_two_output_types.ax
- tests/std/async/structured/spec34_local_executor_example.ax
- tests/std/async/structured/spec34_task_group_example.ax
- tests/std/async/structured/src/group_two_output_types.axsrc
- tests/std/async/structured/src/spec34_local_executor_example.axsrc
- tests/std/async/structured/src/spec34_task_group_example.axsrc
- _workspaces/reports/T422c-report.md

STATUS: COMPLETE round=0
