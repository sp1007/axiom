# T422c QA — std/async on the SPEC-34 API shape

## Round 0

Gate run by T422c-qa in snapshot `build-snap-T422c` (axiomc2 from the snapshot; `-j 2`).

### Environment / snapshot
- The gate started at HEAD `4b945b9f` + the 90-file change set (compiler `axiomc2` sha256 `23885c69…`, built 11:54 after
  T498e). While the gate ran, T498g was accepted (`c43df21b`, which changes `compiler/types/typeck.ax`: raw-memory
  intrinsics with an inferred `T`). I refreshed the snapshot (`taskctl.py snapshot T422c`: HEAD c43df21 + 92 files,
  36 generators / 60 bundles regenerated, no BUNDLES FAILED). Then I rebuilt the compiler there
  (`python tools/build_axiomc.py --out build --root .`: BUILD-AXIOMC OK, fixed point O1 OK, STAGE0-GUARD OK,
  sha256 `17c83e14…`; log `_workspaces/T422c_qa_axiomc.log`). I re-ran every focus suite below on that compiler.
- `taskctl.py changes T422c`: 90 `stage` lines and no REFUSED before my tests were added. After I added the 2 QA files
  below, they show as unlisted until this file lists them, which it does under `## Files changed`.
  `tests/std/async/structured/gen_tests.py` was already in the engineer's list.
- No changes outside `paths:`. The main tree has other dirty files (compiler/, tests/run/host/…), but they belong to other
  tasks, are not in the snapshot and are not listed. No selfhost bundle is listed.

### 1. taskgate (HEAD 4b945b9 compiler, the scope rule of axiom-qa.md)
`python tools/taskgate.py --task T422c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T422c.json`
(log `_workspaces/T422c_qa_taskgate.log`, wall 1982 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 39 | 105 | 100 | 0 | 2 | 3 | 0 |
| affected | 274 | 667 | 661 | 0 | 3 | 3 | 0 |
| smoke | 31 | 50 | 50 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 307 | 719 | 713 | 0 | 3 | 3 | 0 |

- Affected-set derivation (tools/axtest_affected.py):
  - changed std/async modules -> every test that uses them (the std, conformance, perf, run, ui and mir groups);
  - public names (`Send`, `Drop`, …) -> 57 selfhost ids.
- Smoke: seed 3927563707, 31 groups, always-includes `run/str/hello.ax` (Xin chào thế giới), `ui/typeck/type_unknown.ax`,
  `diff/002-arithmetic.ax`.
- BASELINE OK (no new failing id), WEAK-NATIVE 3 in the run / **0 in the task's own/changed tests**, archcheck clean
  (232 files, 0 violations), cache: mismatch none, TASKGATE exit 0.

### 2. Focus suites, fresh, on the rebuilt compiler (HEAD c43df21 + change set + QA test)
`python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt std/async/ std/fiber/ conformance/p11/e11_5_executors/ perf/p11_executor/ run/async/ ui/concurrency/ run/layout_fwd_pointee/`
- Result: **TOTAL 328 PASS 317 FAIL 0 SKIP 2 XFAIL 9, WEAK-NATIVE 0, BASELINE OK** (`_workspaces/T422c_qa_suites.log`).
- This run includes the ids the taskgate did not select:
  - 19 `ui/concurrency` ids;
  - `std/fiber/compile_live_fiber.test` and the two fiber `_xfail` files;
  - `check_conformance_bundles.test` and `check_perf_bundles.test`;
  - the 4 `run/layout_fwd_pointee` ids.
- SKIP 2: the native and native-O1 legs of `spec34_task_group_example` (`native-after: T422d`).
- XFAIL 9:
  - `spec34_local_executor_example` x3 (`xfail: T422e`);
  - `std/fiber/closure_generic_infer_xfail.ax` and `impl_generic_in_method_bound_xfail.ax`, x3 each (both already at HEAD).
- The 7 freshness generators, run with `--check` in the snapshot, all print OK: executor, structured, waker, waker_qa,
  e11_5 conformance ("match live std/async and std/fiber"), perf p11_executor, fiber.

### 3. Markers compared with HEAD (point 2 of the brief)
I diffed every `// xfail|native-after|skip|modes|requires|nocache` line under the 5 task test directories, HEAD against
the snapshot. The only additions are:
- `group_two_output_types.ax`: `modes: interp native`;
- `spec34_local_executor_example.ax`: `modes: interp native` and `xfail: T422e …`;
- `spec34_task_group_example.ax`: `modes: interp native` and `native-after: T422d`.

Nothing was removed or weakened. No test file was deleted. No `// stdout:`/`// exit:` expectation of an existing test
changed (`git diff -U0 -- tests | grep '^[-+]// *(stdout|exit|stderr…)'` is empty). T422d and T422e are both open in
`_workspaces/tasks/todo/`, so ADR-0046 is satisfied. `qa_t422c_drop_edges` (mine) is plain `modes: interp native`.

### 4. Deviations: verified repros (point 1)
| deviation | judgement | evidence |
|---|---|---|
| `Timeout<F, T>` (extra output param) | **forced (R1)** | `fn wrap<F: Future>(fut: F) -> Box2<F.Output>` gives `AX_NAME_UNRESOLVED` at `F.Output`. With `impl<F: Future<Output = T>, T> Future for Tm<F>`, a caller `let r: Poll<Result<i64, Er>> = t.poll(cx)` on `Tm<Ready>` gives `AX_TYPE_MISMATCH` (scratch repros r1a/r1b) |
| `TaskGroup<i64>` annotations (12 sites) | **forced (R2)** | `let mut g = G.new(); g.spawn(Ready{..})` with `impl<T> G<T> { fn spawn<F: Future<Output = T>>(..) }` gives `AX_TYPE_UNKNOWN` at `G.new()` (repro r2) |
| `GroupResults<T>` instead of `Vec<T>` | **forced (library state)** | `std/alloc/vec.ax` only has the type-erased free-function form (`vec_new<T>() -> Vec`, `vec_push<T>(v: mut_view<Vec>, …)`): no `Vec<T>` methods and no `vec[0]` |
| `Executor` is a Copy raw handle, not `Arc<ExecutorInner>` | **not compiler-forced; accepted as a recorded library decision** | `std/sync/arc.ax` exists. ADR-0042 scopes T422c to the generic shape (`TaskGroup<T>`, `Timeout<F>`, `spawn(fut)`), and the field is private in SPEC-34. The report records it (T421 design decision / T422 decision 10, revisit with E11.6). Follow-up for the architect, below |
| T422d: native `.await` on a generic `Future` impl | **real** | `spec34_task_group_example.ax` builds natively and the exe segfaults (rc 139); interp prints `OK spec34_task_group_example 30` |
| T422e: AsyncMutexGuard across `.await` | **real** | The standalone repro with the struct named `AsyncMutexGuard` gives `AX_ASYNC_GUARD_ACROSS_AWAIT: drop flag local is not initialized in bb0`. The identical program with the struct named `Held` builds (rc 0). The bundled test currently fails first on `AX_CONC_GUARD_ESCAPE` (`view(*m).lock()`), which T422e's scope names |

The resolved items are all in the code:
- `spawn(fut)` / `spawn_local(fut)` take no poll function (`task_poll_fn<F, T>` is formed inside the generic method);
- `impl<T> Future for TaskHandle<T>` and `LocalTaskHandle<T>`;
- `TaskJoin<T>`, generic `TaskGroup<T>.spawn(view(exec), fut)`, `GroupNext<T>` and `GroupJoinAll<T>`;
- generic `AsyncMutexLockFuture<T>`, `SendFuture<T>` and `RecvFuture<T>`;
- the workarounds are removed: typed `*mut ExecutorInner` / `*mut CancelState` fields, `Waker` fields instead of
  data/vtable pairs, no `mut_view(*self)`, direct fn-pointer field calls.

A raw-store/move idiom check (interp) confirms the premise of the new `Waker` fields: `(*p).d = D{2}` does not drop the
old bits, and `let old: D = (*p).d` moves them out. The output was `drop 1` and then `drop 2`, each exactly once.

### 5. Removed APIs (point 5)
`grep -rnE '\b(LocalTimeout|TimeoutOutcome|poll_deadline|group_poll_fn|group_request_cancel|results_get_ptr|results_drop_all|local_with_deadline|local_with_timeout)\b|\.adopt\(' std tests tools compiler`
finds 0 hits, tests/selfhost included. The only other `std.asyn` users (`tests/run/layout_fwd_pointee/std_module_waker_field.ax`
and 3 `ui/concurrency/spawn_contract` files) declare their own `std.asyn.*` modules and pass.

### 6. Native evidence (step 4a)
- Every touched or new run test is a generator bundle with an exact `// stdout:` line, and its `check()` prints
  `FAIL line N` and spins. It is not `assert`.
- Mutation in the snapshot only: in `group_two_output_types.ax`, `// stdout: … 30 100 33 0` was changed to `… 34 0`.
  `axtest -v group_two_output_types` then FAILs in all three legs, interp, native and native-O1 ("stdout differs at
  byte 34").
- I restored the file, and `gen_tests.py --check` prints OK.

### 7. Behaviour / stress (point 3)
- I built natively once per test and ran the exe 10 times at O0 and 10 times at -O1, comparing exact stdout and rc 0
  (`_workspaces/T422c_qa_stress.log`). Tests run:
  - executor: lost_wake_prevention, work_stealing_executor, work_stealing_spawn_tree, async_channel_pipeline,
    async_mutex_across_await, async_semaphore_limits, qa_cancel_waiters;
  - waker: join_waker_race; waker_qa: qa_wake_during_poll, qa_join_drop_vs_complete;
  - conformance: cancel_race_linearizes, asyncmutex_cancel_wakes_next, channel_cancel_safety;
  - structured: qa_nested_groups_races, group_two_output_types, qa_t422c_drop_edges.
- Result: **320/320 runs pass, 0 mismatches**, so no lost wakeup or flake was observed.
- Panics are contained through `tcb_poll_fn`: `task_panic_contained`, `group_sibling_cancel` and `group_generic_output`
  pass in all legs, and so does my section A. `join_blocking` is used by 58 test files, which all pass.

### 8. Adversarial test added (step 5)
`tests/std/async/structured/qa_t422c_drop_edges` (src + generated bundle, registered in `gen_tests.py`, interp/native/native-O1, exact stdout
`OK qa_t422c_drop_edges 1 3 40 50 1 0`). It tests the drop seams that the existing tests do not cover:
- **A.** `join_all` failure path with a Drop output type: two `Tracked` outputs are already collected and the third
  child panics. The result is `Err(Panicked)`, and the collected outputs and every capture are dropped (live 0).
- **B.** `Timeout<GroupJoinAll<Tracked>, _>` over a group of never-finishing children. The deadline fires, and dropping
  the Timeout drops the `GroupJoinAll`, then the group, which cancels and drains the children; all captures are dropped.
- **C.** `Timeout<TaskHandle<Tracked>, _>` that completes before the deadline gives `Ok(Ok(t))`.
- **D.** `LocalExecutor.spawn_local` with a `Tracked` output: `LocalTaskHandle<Tracked>.join()` driven by `run_until`.
  Dropping a pending local handle cancels it and drops its capture, and `active_task_count` returns to 0.
- **E.** `next()` after `cancel_all` yields `Some(Err(Cancelled))` and then `None`. A spawn into the cancelled group is
  refused with `GroupError.Cancelled`, and the refused future is dropped at once.

It passes in all three legs, and the 20 stress runs above pass too.

### 9. Spec / scope checks
- **Spec:** the behaviour matches SPEC-34:
  - AXS-EXEC-005: handles are futures;
  - AXS-EXEC-020: group spawn/next/join_all/drop-drain;
  - AXS-EXEC-024: Timeout polls the inner future first, `Err(TimeoutError)` on expiry, the inner future is dropped with
    the Timeout.
- **Recorded semantic choices:** the report records `Result<TaskId, GroupError>` from `spawn` and refusal before
  spawning.
- **Diagnostics and shortcuts:** no new diagnostics and no `BOOTSTRAP-SHORTCUT`.
- **Scope:** no edits under `compiler/`, `bootstrap/`, `docs/` or any shared file.

### Findings
None that fail the gate.

### Notes (not FAIL)
- N1: `task_panic(cx)` writes `FLAG_PANIC_REQUESTED` through `cx.waker().raw.data` without checking that the vtable is
  the task vtable. With a user waker (the `user_waker_vtable` style), it would write into foreign memory. This is
  pre-existing (moved unchanged from group.ax) and temporary until T536, but a vtable identity check would be cheap.
- N2: `GroupNext`, `GroupJoinAll` and `Timeout` re-wake themselves on every Pending (busy polling) until there is a
  timer and a child-completion wait queue (E11.6/T426). This is documented in the code.

### Follow-ups (for axiom-architect)
- F1 (R1): `F.Output` projections in signatures, and impl parameters fixed only through a bound
  (`impl<F: Future<Output = T>, T> Future for Tm<F>`). They block `Timeout<F>` and `TaskHandle<F.Output>`. Repros r1a/r1b
  are in §4. No task is filed yet; it is an extension of the T448 known limit.
- F2 (R2): infer an impl-level `T` from a method's `F: Future<Output = T>` bound (`TaskGroup.new()` + `spawn`).
- F3 (R3): spurious `AX_PAT_UNREACHABLE` on `Result.Err(E.A)` / `Result.Err(E.B)` arms. Confirm in T499c.
- F4 (R4): match-arm bindings are dropped at the end of the enclosing block, not at the end of the arm. Does this follow
  SPEC-12 drop scopes?
- F5 (R5): `drop_in_place<F>(address_of_mut((*tcb).future))` does not run F's destructor.
- F6: `Executor` as a Copy raw handle with `ExecutorInner` never freed, versus SPEC-34's `inner: Arc<ExecutorInner>`
  (the T421/T422-10 library decision). Decide whether E11.6 converges it, or amend SPEC-34.

## Files changed
- tests/std/async/structured/qa_t422c_drop_edges.ax
- tests/std/async/structured/src/qa_t422c_drop_edges.axsrc
- tests/std/async/structured/gen_tests.py

VERDICT: PASS round=0
