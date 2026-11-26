# T428a report: address-observable `async fn` locals live in place (ADR-0050)

## Design
1. **Lowering stays save/restore** (`compiler/mir/async_lower.ax`). The `poll` body is built exactly as before, so MIR
   verification and drop elaboration see in-place locals as ordinary locals (whole, per-leaf and enum-payload flags
   work unchanged). `bb_dispatch` carries one marker per in-place local: `StorageLive(slot)` with `place = (*_1).field`.
2. **Coalescing after drop elaboration** (`compiler/mir/drop.ax`, `drop_coalesce_inplace`, last step of
   `mir_drop_elaborate`, only for `async_lowered` bodies with markers): every place rooted at the slot becomes
   `(*_1).field..`; the save/restore moves, the markers and the slot's storage statements are removed. It is sound
   because the field is only written by the save and only read by the restore of its own slot. Index/bound locals of
   projections (a projection names a local, not a place) are refreshed from the field before each use. Every
   interpreter, native and -O1 path elaborates before it executes or optimizes, so no oracle or backend special case.
3. **Address-observable** = base of a `Ref` rvalue anywhere in the body (statics/TLS/const locals excluded).
   Such storage counts as live across a suspension while it is initialized and in scope (until `StorageDead`), not
   only while it is named again: user variables and parameters (borrowed in any way), temporaries turned into a raw
   pointer, temporaries borrowed inside the awaited expression. Without this a buffer reached only through its pointer
   after the `.await` stayed in the poll frame. Views are excluded (they never cross `.await`).
4. The `.await` destination: a whole-local destination whose address is observable stays in place; a destination that
   is a *part* of a local (`p.b = f.await`) keeps the rest of the local (HEAD's oracle lost it: 111 instead of 1111),
   so the ready block restores before it writes the destination.
5. `remap_place` copies projection arrays before renaming index locals (the builder shares one array between places).
6. No packing exists (one field per live local), so in-place fields never overlap. The cancellation drop glue is
   unchanged and drops the field once per state.
7. `inspect --emit=async-layout` prints `in_place=true|false` for every live local.

A first version rewrote places during lowering and used view drop flags; it leaked the second payload of a partially
moved enum local, which is why elaboration now runs first.

## Std drivers (scope item 2)
Polling never moves a future: `spawn_local` / `Executor.spawn` move it into the heap TCB once before queueing and
`tcb_poll_fn` polls `(*tcb).future` in place; `TaskGroup.spawn` forwards to `Executor.spawn`; `run_until` /
`Executor.block_on` / `std.future.block_on` poll their own parameter slot (`std.future.block_on` moves it only after
`Ready`). Cancellation/panic used to move it: fixed in round 1 (see below).

## Tests
`tests/run/async/addr_stable_locals/` (interp, native, native-O1, exact stdout):
`udp_recv_from_local` (the F1 repro), `tcp_local_stream`, `addr_before_first_await`, `loop_reawait_buffer`,
`cancel_inplace_drop_once`, `drop_flags_across_awaits` (moved / late / loop / parameter / partial / cancelled guards,
each dropped once), `pointer_only_use`, `borrowed_receiver`. Conformance: new `direct_slice_io_async_locals`;
`tcp_framing_split` now owns halves and buffers in the tasks (stdout unchanged).

On HEAD (`head/axiomc2_head.exe`, sha256 dd6c7b0b..): the seven programs other than `borrowed_receiver` and both
conformance tests fail in interp, native **and** native-O1 (`use of dangling pointer`, wrong values, or a crash).
`borrowed_receiver` fails on HEAD in interp only: natively the stale stack slot happens to survive.

## Verification (snapshot `build-snap-T428a`, HEAD cc4fef2 + this change set)
- `build_axiomc.py --stage 2`: `FIXED-POINT (O1) OK`, stage-0 guard OK, axiomc2 sha256 1eb724ab.. (`_workspaces/T428a_build3.log`).
- New and changed tests: 30 of 30 pass, `WEAK-NATIVE 0`.
- `run/async mir/async ui/async std/async conformance/p11 inspect`: 414 results, 408 pass, 6 fail
  (`_workspaces/T428a_suites.log`). Five are listed in `_workspaces/baseline-failures.txt` (T449a): four stale-bundle
  checks and the timing test `std/async/reactor/timer_wheel_100_timers.ax`. The sixth,
  `conformance/p11/e11_5_executors/check_conformance_bundles.test`, fails identically with the HEAD compiler (its
  generator never runs the compiler; the bundles lag std) but is **not** in the baseline file: see follow-up 4.
- `taskgate.py --task T428a ... -j 2` (`_workspaces/T428a_taskgate.log`): `TOTAL 466 PASS 464 FAIL 0 SKIP 2`, BASELINE OK,
  `TASKGATE T428a exit=0`; includes the affected selfhost groups (`mir`, `drop`, `lir`, `opt`, `own_mir_verify`, `interp`,
  `verify`, ...). WEAK-NATIVE 0 in own/changed tests (3 in other tests of the run).
- HEAD moved to 9135f012 (T461, `std/math` only) after these runs; the snapshot was not rebuilt on it.
- `archcheck.py`: 240 files, 0 violations.

## Pre-existing defects found (identical on HEAD, not changed here)
1. A value moved out (wholly, conditionally or partially) before an `.await` and still in scope after it is dropped
   twice: drop flags are not saved in the state, the restore re-arms them. Repro: `let g = G{..}; let a = g.get();
   if c { eat(g); } y().await;` drops `g` twice when `c`; the same for a tuple field moved before an `.await`.
2. A `static mut` used in an `async fn` is treated as a poll-frame copy: a change made by another function during a
   suspension is not seen (11011 instead of 11111). Likely cause (read, not tested): the `poll` copy of every source
   local gets kind `TEMP`, so a `STATIC` local becomes an ordinary one.
3. `Atomic` operations inside an `async fn` crash (native segfault; oracle `polling a completed Future`). Likely
   cause (read, not tested): `remap_stmt` does not rename the locals of `MIR_STMT_ATOMIC` and the liveness scan ignores
   that statement (REQ-ASY-082).
4. `e11_5_executors/check_conformance_bundles.test` is stale since T427 and missing from the baseline list.

## Spec deviations
none. SPEC-33 AXS-ASY-043 item 7 says "live across"; point 3 of the design reads it as storage-live, which REQ-ASY-122 needs.

## Round 1 (QA F1)
- `std/async/task.ax` `tcb_drop_future`: the copy `let mut tmp: [1]F = [*address_of_mut((*tcb).future)];` replaced by
  `drop_in_place<F>(address_of_mut((*tcb).future));` (intrinsic declared locally as in `std/async/channel.ax`). The
  future of a cancelled or panicked task is dropped where it was polled. `tcb_drop_payload`'s output copy is unchanged.
- Bundles regenerated with their own generators: `tests/std/async/{executor,structured,waker,waker_qa}`,
  `tests/conformance/p11/e11_5_executors`, `tests/conformance/p11/e11_6_async_io` (`taskgroup_async_io.ax`),
  `tests/perf/p11_executor`. The e11_5 and perf generators still used hand-written source lists that bundle
  `std/text/string.ax` next to `std.io` (both define `String`/`string_new`, AX_TYPE_MISMATCH at `io.ax:264`); they now
  use `tests/std/async/structured/bundle_closure.py` exactly as T449a did for std/async (`COMMON_PREREQS = []`, closure
  of the listed seeds and of the program's `use` lines). Every `gen_tests.py --check` prints OK.
- `_workspaces/baseline-failures.txt`: removed the 3 lines naming T428a (and their comment block).
- QA tests `qa_cancel_spawned_task`, `qa_cancel_spawned_intrusive`, `qa_shapes_across_awaits`,
  `qa_drop_moves_in_place`, `qa_cancel_every_suspension` pass in interp, native and native-O1.

### Verification (snapshot `build-snap-T428a`, HEAD 652ffe96 + this change set)
- `build_axiomc.py --stage 2`: `FIXED-POINT (O1) OK`, axiomc2 sha256 1eb724ab.. (`_workspaces/T428a_build_r1.log`, `_r1b.log`).
- Own + QA + e11_6 direct/framing tests: 45/45 PASS, WEAK-NATIVE 0.
- `run/async mir/async ui/async std/async conformance/p11 inspect/async_layout.test perf/p11_executor`
  (`_workspaces/T428a_suites_r1.log`): `TOTAL 467 PASS 461 FAIL 6`, WEAK-NATIVE 0. All bundle checks pass.
- `taskgate.py --task T428a` (`_workspaces/T428a_taskgate_r1.log`): `TOTAL 649 PASS 641 FAIL 6 SKIP 2`, archcheck clean,
  `TASKGATE T428a exit=1`: failing ids outside the baseline are exactly the 2 below.

### BLOCKER: 2 e11_5 tests cannot pass on current std (pre-existing, not caused by T428a)
`conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax` and `fiber_in_async_and_threads.ax` (3 results each)
fail to compile: `AX_TYPE_MISMATCH` at `std/io/io.ax:264` / `:282` (`Result.Ok(string_new())`). Both programs
`use std.thread.spawn` together with `std.asyn.executor`. Minimal repro against **live** std, identical with the HEAD
compiler (dd6c7b0b) and this task's compiler, no bundle involved:
```
use std.thread.spawn
use std.asyn.executor.Executor
fn main() -> i32 { 0i32 }
```
Cause: `std.io` and `std.text.string` both define `String` / `string_new`; since T426/T427 `std.asyn.executor` imports
`std.io` and `std.thread` imports `std.text.string`, and the two copies are not kept apart. The tests passed at HEAD
only because their bundles were stale (pre-T426 std). Not fixable inside this task's paths/locks (`std/io`,
`std/text`, or the resolver). Needed: the architect admits these 2 ids to `_workspaces/baseline-failures.txt` with a fix
task (std String unification or resolver fix), or names the owner of the fix; after that T428a's gate is green.

## Files changed
- _workspaces/baseline-failures.txt
- compiler/mir/async_lower.ax
- compiler/mir/drop.ax
- std/async/task.ax
- tests/conformance/p11/e11_5_executors/asyncmutex_cancel_wakes_next.ax
- tests/conformance/p11/e11_5_executors/cancel_race_linearizes.ax
- tests/conformance/p11/e11_5_executors/cancel_tree_groups.ax
- tests/conformance/p11/e11_5_executors/channel_cancel_safety.ax
- tests/conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax
- tests/conformance/p11/e11_5_executors/gen_tests.py
- tests/conformance/p11/e11_5_executors/local_cancel_drop_order.ax
- tests/conformance/p11/e11_5_executors/sibling_failure_isolation.ax
- tests/conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax
- tests/conformance/p11/e11_6_async_io/direct_slice_io_async_locals.ax
- tests/conformance/p11/e11_6_async_io/taskgroup_async_io.ax
- tests/conformance/p11/e11_6_async_io/tcp_framing_split.ax
- tests/perf/p11_executor/channel_ping_pong.ax
- tests/perf/p11_executor/gen_tests.py
- tests/perf/p11_executor/spawn_poll_throughput.ax
- tests/perf/p11_executor/steal_fanout_fanin.ax
- tests/run/async/addr_stable_locals/addr_before_first_await.ax
- tests/run/async/addr_stable_locals/borrowed_receiver.ax
- tests/run/async/addr_stable_locals/cancel_inplace_drop_once.ax
- tests/run/async/addr_stable_locals/drop_flags_across_awaits.ax
- tests/run/async/addr_stable_locals/loop_reawait_buffer.ax
- tests/run/async/addr_stable_locals/pointer_only_use.ax
- tests/run/async/addr_stable_locals/qa_cancel_every_suspension.ax
- tests/run/async/addr_stable_locals/qa_cancel_spawned_intrusive.ax
- tests/run/async/addr_stable_locals/qa_cancel_spawned_task.ax
- tests/run/async/addr_stable_locals/qa_drop_moves_in_place.ax
- tests/run/async/addr_stable_locals/qa_shapes_across_awaits.ax
- tests/run/async/addr_stable_locals/tcp_local_stream.ax
- tests/run/async/addr_stable_locals/udp_recv_from_local.ax
- tests/std/async/executor/async_channel_pipeline.ax
- tests/std/async/executor/async_mutex_across_await.ax
- tests/std/async/executor/async_semaphore_limits.ax
- tests/std/async/executor/local_executor_rc.ax
- tests/std/async/executor/lost_wake_prevention.ax
- tests/std/async/executor/qa_cancel_waiters.ax
- tests/std/async/executor/qa_handle_cancel_await.ax
- tests/std/async/executor/work_stealing_executor.ax
- tests/std/async/executor/work_stealing_spawn_tree.ax
- tests/std/async/structured/cancel_token_tree.ax
- tests/std/async/structured/deadline_timeout.ax
- tests/std/async/structured/group_deadline.ax
- tests/std/async/structured/group_drop_cancels.ax
- tests/std/async/structured/group_generic_output.ax
- tests/std/async/structured/group_governor_quota.ax
- tests/std/async/structured/group_join_all.ax
- tests/std/async/structured/group_sibling_cancel.ax
- tests/std/async/structured/group_two_output_types.ax
- tests/std/async/structured/handle_drop_vs_detach.ax
- tests/std/async/structured/qa_nested_groups_races.ax
- tests/std/async/structured/qa_t422c_drop_edges.ax
- tests/std/async/structured/resource_governor_limits.ax
- tests/std/async/structured/spec34_local_executor_example.ax
- tests/std/async/structured/spec34_task_group_example.ax
- tests/std/async/structured/task_panic_contained.ax
- tests/std/async/waker/cancel_self_waking.ax
- tests/std/async/waker/detached_output_drop.ax
- tests/std/async/waker/join_waker_race.ax
- tests/std/async/waker/user_waker_vtable.ax
- tests/std/async/waker_qa/qa_cancel_during_poll.ax
- tests/std/async/waker_qa/qa_group_drop_detached.ax
- tests/std/async/waker_qa/qa_join_drop_vs_complete.ax
- tests/std/async/waker_qa/qa_late_waker_drop.ax
- tests/std/async/waker_qa/qa_wake_during_poll.ax

STATUS: BLOCKED round=1: 2 e11_5 tests (spawn_affinity_vs_migration, fiber_in_async_and_threads) fail on pre-existing std.io/std.text.string String clash (live-std 3-line repro, HEAD too); baseline admission or fix task needed from the architect

## Orchestrator note (2026-11-26)
The blocker above was resolved by the architect (_workspaces/reports/unblock-T428a.md): the 2 e11_5 ids are admitted to the baseline with fix task T428g; no code change was needed. The round-1 change set stands as reported.

STATUS: COMPLETE round=1
