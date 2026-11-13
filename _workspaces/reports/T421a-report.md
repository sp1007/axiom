# T421a report

std/async follow-up (ADR-0042 §2, T422 FU-I, T421/T422 QA notes): join-waker race, `task_wake` livelock,
poll flag clobber, `Waker` vtable dispatch, outputs of detached / never-joined tasks. All changes are in
`std/async` and `tests/std/async`; no compiler change.

## Summary

For each defect a regression test was written first (new directory `tests/std/async/waker/`, same bundle
scheme as `tests/std/async/structured`), run against the unfixed sources to show the failure, then the fix.

| defect | test | before (HEAD std/async) | after |
|---|---|---|---|
| join-waker slot race (TaskHandle await loses the wake) | `join_waker_race` (1000 iterations, 2 workers, inner/outer delays swept) | native: `999 lost 1` (1 lost wake / 1000); native-O1: 0 / 1000 in that run (narrow window); interp: not measurable (test-side UAF, fixed in the test afterwards, see below) | `1000 lost 0` in all 3 modes, 5 runs |
| poll flag clobber (`store(TASK_POLLING)` erased the cancel flag) | `cancel_self_waking` (1000 cancels / handle drops of a self-waking task) | native: `clobbered 8`, native-O1: `clobbered 20` (of 1000); interp: TIMEOUT 180 s | `clobbered 0`, 1000 futures dropped exactly once, all modes, 5 runs |
| `task_wake` CAS livelock against a self-waking task (oracle) | `cancel_self_waking` (interp) | TIMEOUT (interp) | PASS |
| Waker ops hard-wired to the task header | `user_waker_vtable` (counting user waker; also used as join waker through an executor) | interp: `AX_UNSAFE_INTERP_UB` out-of-bounds (`ref_count.fetch_add` on the user data); native and native-O1: CRASH 0xC0000005 | counts `clone 4, wake_by_ref 1, wake 2, drop 4`, invariant originals+clones == wakes+drops |
| outputs of detached / never-joined tasks not dropped | `detached_output_drop` (detach before/after completion, handle dropped after/while running, join, TaskGroup dropped with uncollected outputs, LocalExecutor detach) | TIMEOUT in all 3 modes (a `check` fails: drop count stays below produced count, test spins) | drops == produced (300) in all modes, 5 runs |

Raw before/after logs are in the snapshot (`build-snap-T421a/after_run1.log`, `full_run1.log`, `rep_{3,4,5}.log`);
the before run was made with bundles generated in the snapshot from HEAD `std/async`.

## Design (std/async)

1. **State encoding, wait-free wake** (`waker.ax`). The scheduling state is now the low nibble
   (`TASK_STATE_MASK = 0xF`, flags above it): IDLE 0, POLLING 1, NOTIFIED 2 (a bit), POLLING|NOTIFIED 3
   (sticky wake permit while running), COMPLETED 0xA, CANCELLED 0xB, PANICKED 0xE (every terminal value
   contains bit 1). `task_wake` is a single `fetch_or(TASK_NOTIFIED)`; only the IDLE -> NOTIFIED
   transition enqueues. The CAS retry loop that livelocked is gone. Poll transitions are single RMWs that
   keep the flag bits: `task_begin_poll` (`fetch_sub(1)`: NOTIFIED -> POLLING, returns the prior word so the
   cancel flag set while queued is seen), `task_end_poll_pending` (`fetch_sub(1)`: POLLING -> IDLE or
   POLLING|NOTIFIED -> NOTIFIED + re-queue; a cancel flag without a wake also re-queues),
   `task_set_terminal`, `task_state`, `task_schedule`, `task_request_cancel` (flag + `task_wake`).
   `TaskHandle.cancel` / `Drop` (and `LocalTaskHandle`) use `task_request_cancel` again;
   `group_request_cancel` is kept as a thin alias of it.
2. **Join-waker slot** (`task.ax`). `TaskSlot.has_join_waker: bool` is replaced by `join_state: Atomic<u32>`
   with REGISTERING / WAKER_SET / COMPLETE bits. The handle registers under REGISTERING and publishes
   WAKER_SET with one CAS; the completer does `fetch_or(COMPLETE)` after publishing the terminal state and
   wakes the waker only when no registration is in progress; a registration that loses the race drops its
   own waker and returns false (`task_register_join_waker`), and the handle's poll re-reads the terminal
   state instead of returning Pending. A waker still set when the block is freed is dropped there. Each
   registered waker is consumed exactly once. The handle polls share `handle_poll_i64`.
3. **Flag-preserving poll functions**: `tcb_poll_fn` and `group_poll_fn` use the helpers above (no plain
   `store(TASK_POLLING)`), and publish terminal states through `task_finish` (terminal state, then join waker).
4. **Waker vtable dispatch** (`waker.ax`): `wake` (consumes via `waker_leak`, so `Drop` cannot run twice),
   `wake_by_ref`, `clone`, `Drop` call the `RawWaker`'s vtable entries through the existing
   `raw_waker_*` helpers (plus new `raw_waker_clone`); nothing assumes a task header. Added `will_wake`
   (SPEC-33 AXS-ASY-011). A waker with a null data pointer or null vtable is empty: every operation is a
   no-op (the `Waker.noop()` convention).
5. **Output drop on release** (`task.ax`, `group.ax`). The output type is unknown to type-erased code and a
   generic function cannot be taken as a function pointer (T422 FU-J), so the per-task poll function is
   the typed entry point: called with a **null Context** it drops the stored payload (`tcb_drop_payload`:
   future if still present, output if never taken). `default_task_drop` (last reference) calls it when
   `has_output` is set. This covers detached tasks (before or after completion), handles dropped after
   completion, and `TaskGroup` dropped with uncollected children (T422 decision 8 is resolved too).
   Contract (documented on `TaskControlBlock`): a custom poll function must wrap `tcb_poll_fn` /
   `group_poll_fn` or honour the null-Context call; every poll function in the tree does.

Public API kept (T421/T422): all existing names remain; new public items are additive. Behavioural change
visible to callers: the numeric values of `TASK_COMPLETED/CANCELLED/PANICKED` and the mask (`& 0x7` must
become `& TASK_STATE_MASK`). Nothing outside `std/async` and `tests/std/async` references these (T421/T422
QA isolation grep); the two tests that hard-coded `& 0x7u32` were updated (`lost_wake_prevention` now
expects the sticky POLLING|NOTIFIED permit instead of NOTIFIED; `qa_nested_groups_races` mask).

## Test-side fixes made while writing the tests

- `join_waker_race` / `cancel_self_waking`: main pins the task header it observes with its own reference
  (`ref_count.fetch_add` + `task_dec_ref`); the first version read the inner header after it could be
  freed (the interp oracle reported `use of dangling pointer` in the before run).
- `user_waker_vtable`: counters read through raw-pointer helpers (`view(unsafe { (*c).field })` is
  `AX_CAP_OUTLIVES_OWNER`, correct diagnostic).

## Tests

Compiler: reused read-only `build-snap-T452/build/axiomc2.exe` (stage-2 axiomc2 built for T452, now at
HEAD); snapshot `build-snap-T421a` (HEAD 888b283 + this change set); `axtest -j 2`, one run at a time.

- `tests/std/async` complete (executor + structured + waker): **TOTAL 80 PASS 80 FAIL 0, WEAK-NATIVE 0**.
- New tests (`tests/std/async/waker`, 4 run tests x interp/native/native-O1 + `check_waker_bundles.test`):
  5 consecutive runs (`after_run1`, the waker part of `full_run1`, `rep_3`..`rep_5`), each
  `TOTAL 13 PASS 13 FAIL 0, WEAK-NATIVE 0`; no flake.
- Native evidence: every new test has an exact `stdout:` with the measured counts (`lost 0`, `clobbered 0`,
  the four waker counters, drops - produced = 0); failures print `FAIL line <n>` and spin to the timeout (no
  `assert()`). The before run is the mutation proof: native FAILs with the stdout diff
  (`999 lost 1`, `clobbered 8` / `clobbered 20`) or crash.
- `axiomc2 check` of the live modules (`waker, task, executor, cancel, timeout, governor, group, mod`): rc 0.
- Bundles regenerated: `tests/std/async/executor` and `tests/std/async/structured` (they embed the live
  std/async sources), their `--check` tests pass.

## Decisions (for the architect)

- New state values instead of a separate notify flag: keeps one atomic word and makes wake, begin-poll and
  end-poll single wait-free RMWs; terminal values were chosen so `fetch_or(NOTIFIED)` is a no-op on them.
- Null-Context poll call as the type-erased drop entry: the only typed per-task code that exists today
  (FU-J/FU-F/FU-G prevent a generic drop function pointer and impl-level `T` drop glue). When T444/T446
  land (T422c), a `drop_output_fn` header field instantiated in `spawn<F, T>` can replace it.
- `group_request_cancel` kept (public API of T422) as an alias of `task_request_cancel`.
- Out of scope / unchanged: real panic capture (T536), generic API shape (T422c).

## Follow-ups

- No new compiler gap found. Workarounds kept: T421 FU-2 (function-pointer field call bound to a local),
  FU-3 (waker pairs instead of `Waker` fields), FU-6 (`mut_view(*cx).waker()` in the handle poll loop).
- Minor: `std/async/group.ax` still imports `TASK_IDLE`, `TASK_POLLING`, `TASK_NOTIFIED`, `task_wake`
  without using them (no warning reported by `axiomc2 check`); harmless, can be cleaned in T422c.

## Files changed
- std/async/waker.ax
- std/async/task.ax
- std/async/executor.ax
- std/async/group.ax
- std/async/mod.ax
- tests/std/async/waker/gen_tests.py
- tests/std/async/waker/check_waker_bundles.test
- tests/std/async/waker/src/join_waker_race.axsrc
- tests/std/async/waker/src/cancel_self_waking.axsrc
- tests/std/async/waker/src/user_waker_vtable.axsrc
- tests/std/async/waker/src/detached_output_drop.axsrc
- tests/std/async/waker/join_waker_race.ax
- tests/std/async/waker/cancel_self_waking.ax
- tests/std/async/waker/user_waker_vtable.ax
- tests/std/async/waker/detached_output_drop.ax
- tests/std/async/executor/gen_tests.py
- tests/std/async/executor/async_channel_pipeline.ax
- tests/std/async/executor/async_mutex_across_await.ax
- tests/std/async/executor/async_semaphore_limits.ax
- tests/std/async/executor/local_executor_rc.ax
- tests/std/async/executor/lost_wake_prevention.ax
- tests/std/async/executor/qa_cancel_waiters.ax
- tests/std/async/executor/qa_handle_cancel_await.ax
- tests/std/async/executor/work_stealing_executor.ax
- tests/std/async/executor/work_stealing_spawn_tree.ax
- tests/std/async/structured/src/qa_nested_groups_races.axsrc
- tests/std/async/structured/cancel_token_tree.ax
- tests/std/async/structured/deadline_timeout.ax
- tests/std/async/structured/group_deadline.ax
- tests/std/async/structured/group_drop_cancels.ax
- tests/std/async/structured/group_generic_output.ax
- tests/std/async/structured/group_governor_quota.ax
- tests/std/async/structured/group_join_all.ax
- tests/std/async/structured/group_sibling_cancel.ax
- tests/std/async/structured/handle_drop_vs_detach.ax
- tests/std/async/structured/qa_nested_groups_races.ax
- tests/std/async/structured/resource_governor_limits.ax
- tests/std/async/structured/task_panic_contained.ax
- _workspaces/reports/T421a-report.md

STATUS: COMPLETE round=0
