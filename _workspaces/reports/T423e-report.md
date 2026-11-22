# T423e report — Self-entry placeholder resolved by identity, not by name

## Summary
Isolated the root cause of the two-module `__ax_thread_self_entry` rewrite failure and replaced the compiler's hardcoded function-name check (`__ax_thread_self_entry` / `__ax_fiber_self_entry`) with item-identity detection via `@lang("self_entry")` on the resolved `HirItem`.

### Root cause
When two or more modules in the same compilation unit declared non-generic functions named `__ax_thread_self_entry`:
1. `mb_prepare_mono` (`compiler/mir/builder.ax`) registered a `MonoInstance` for each non-generic `HIR_ITEM_FN`, prepending to `eng.instances_head` so the *later*-bundled module's item appeared first in the instance list.
2. `mb_dedup_mono_names` (`compiler/mir/builder.ax:12920-12950`) saw `cnt[name] >= 2` (required so duplicate non-generic function names across modules do not collide in `.text` at link time) and mutated the later module's `HirItem.name` in place to `__ax_thread_self_entry$s<sym>`, decrementing `cnt[name]` to `1` so the earlier module kept `__ax_thread_self_entry`.
3. Both the MIR interpreter (`is_self_entry_fn_item` in `compiler/interp/interp.ax`) and the LIR builder (`lb_format_fn_item_sym_name` in `compiler/lir/builder.ax`) already resolved the `MIR_OP_CONST` operand's `HirItem` by `SymbolId`, **but then tested `(*item).name` against the hardcoded strings `"__ax_thread_self_entry"` and `"__ax_fiber_self_entry"`**. For the module whose `HirItem.name` had been deduplicated to `__ax_thread_self_entry$s<sym>`, that string check returned `false`, leaving the function pointer pointing at the dummy placeholder `{ 0i64 }` instead of the enclosing generic trampoline (`Completed` with null `result_ptr` in interp, null-deref access violation natively).
4. In addition, `exec_assign_repeat` (`compiler/interp/interp.ax`) read `(*stmt).rvalue.use_op.constant.val` directly instead of calling `resolve_const_op_val`, which missed rewriting `[placeholder; N]` repeat rvalues in the interpreter.

### Fix
- Marked self-entry placeholders with `@lang("self_entry")` (`HirItem.attrs` is preserved across `mb_dedup_mono_names`).
- Replaced `INTERP_SELF_ENTRY_BYTES` / `INTERP_FIBER_SELF_ENTRY_BYTES` in `compiler/interp/interp.ax` (`is_self_entry_fn_item`) and `is_thread_self_entry_name` / `is_fiber_self_entry_name` in `compiler/lir/builder.ax` (`has_self_entry_attr` in `lb_format_fn_item_sym_name`) with an exact `@lang("self_entry")` attribute check on the `SymbolId`-resolved `HirItem`. Removed all placeholder function-name lists from the compiler.
- Routed `MIR_RVALUE_REPEAT` constant operands through `resolve_const_op_val` in `compiler/interp/interp.ax` so `[placeholder; N]` agrees between interp and native.
- Updated `std/thread/mod.ax` and `std/fiber/mod.ax` to declare `@lang("self_entry") fn __ax_thread_self_entry(ctx: *mut u8) -> i64` (retiring the `__ax_fiber_self_entry` workaround name in `std.fiber`), fixed `tests/std/channel/gen_tests.py` to read live `ROOT` sources instead of `git show HEAD:...`, and regenerated/updated the test bundles that inline `std/thread/mod.ax` and `std/fiber/mod.ax`.

## Files changed
- compiler/interp/interp.ax
- compiler/lir/builder.ax
- std/fiber/mod.ax
- std/thread/mod.ax
- tests/conformance/p11/e11_3_threads_sync/arc_mutex_8thread_stress.ax
- tests/conformance/p11/e11_3_threads_sync/channel_mpmc_drop_stress.ax
- tests/conformance/p11/e11_3_threads_sync/condvar_barrier_work_queue.ax
- tests/conformance/p11/e11_3_threads_sync/once_concurrent_init_stress.ax
- tests/conformance/p11/e11_3_threads_sync/qa_condvar_broadcast_weak_stress.ax
- tests/conformance/p11/e11_3_threads_sync/rwlock_reader_writer_stress.ax
- tests/conformance/p11/e11_3_threads_sync/scoped_threads_and_panic_containment.ax
- tests/conformance/p11/e11_3_threads_sync/tls_and_local_key_stress.ax
- tests/conformance/p11/e11_5_executors/asyncmutex_cancel_wakes_next.ax
- tests/conformance/p11/e11_5_executors/cancel_race_linearizes.ax
- tests/conformance/p11/e11_5_executors/cancel_tree_groups.ax
- tests/conformance/p11/e11_5_executors/channel_cancel_safety.ax
- tests/conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax
- tests/conformance/p11/e11_5_executors/fiber_switch_conformance.ax
- tests/conformance/p11/e11_5_executors/local_cancel_drop_order.ax
- tests/conformance/p11/e11_5_executors/sibling_failure_isolation.ax
- tests/conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax
- tests/perf/p11_executor/channel_ping_pong.ax
- tests/perf/p11_executor/fiber_switch_overhead.ax
- tests/perf/p11_executor/spawn_poll_throughput.ax
- tests/perf/p11_executor/steal_fanout_fanin.ax
- tests/run/concurrency/tls/qa_tls_borrow_mut_in_shared_panic.ax
- tests/run/concurrency/tls/qa_tls_borrow_shared_in_mut_panic.ax
- tests/run/concurrency/tls/qa_tls_key_identity.ax
- tests/run/concurrency/tls/qa_tls_reentrant_borrow_edge.ax
- tests/run/concurrency/tls/tls_local_key_drop.ax
- tests/run/concurrency/tls/tls_threads.ax
- tests/run/interp_big_args/qa_fiber_big_capture.ax
- tests/run/self_entry_placeholder/bug_two_modules_order_ab.ax
- tests/run/self_entry_placeholder/bug_two_modules_order_ba.ax
- tests/run/self_entry_placeholder/plain_fn_not_placeholder.ax
- tests/run/self_entry_placeholder/three_modules_order_abc.ax
- tests/run/self_entry_placeholder/three_modules_order_cba.ax
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
- tests/std/channel/channel_big_struct.ax
- tests/std/channel/channel_boundary_edge.ax
- tests/std/channel/channel_bounded_basic.ax
- tests/std/channel/channel_move_only_drop.ax
- tests/std/channel/channel_mpmc_threads.ax
- tests/std/channel/channel_mpsc_threads.ax
- tests/std/channel/channel_spsc_threads.ax
- tests/std/channel/channel_unbounded_basic.ax
- tests/std/channel/gen_tests.py
- tests/std/fiber/fiber_affinity.ax
- tests/std/fiber/fiber_deep_stack.ax
- tests/std/fiber/fiber_drop_cleanup.ax
- tests/std/fiber/fiber_host_contract.ax
- tests/std/fiber/fiber_nested.ax
- tests/std/fiber/fiber_panic_contained.ax
- tests/std/fiber/fiber_ping_pong.ax
- tests/std/fiber/fiber_scheduler_rr.ax
- tests/std/fiber/fiber_stack_sizes.ax
- tests/std/fiber/native_panic/np_after_yields.ax
- tests/std/fiber/native_panic/np_host_contract.ax
- tests/std/fiber/native_panic/np_main_thread.ax
- tests/std/fiber/native_panic/np_nested.ax
- tests/std/fiber/native_panic/np_resume_after_panic.ax
- tests/std/fiber/native_panic/np_scheduler.ax
- tests/std/fiber/native_panic/np_spawned_thread.ax
- tests/std/fiber/native_panic/qa_np_drop_not_run.ax
- tests/std/fiber/native_panic/qa_np_exit_passthrough.ax
- tests/std/fiber/native_panic/qa_np_plain_after.ax
- tests/std/fiber/native_panic/qa_np_thread_first.ax
- tests/std/fiber/native_panic/qa_np_three_deep.ax
- tests/std/fiber/qa_fiber_drop.ax
- tests/std/fiber/qa_fiber_foreign_collision.ax
- tests/std/fiber/qa_fiber_handle_reuse.ax
- tests/std/fiber/qa_fiber_many.ax
- tests/std/fiber/qa_fiber_nested3.ax
- tests/std/fiber/qa_fiber_resume_finished.ax
- tests/std/fiber/qa_fiber_values.ax
- tests/std/fiber/qa_fiber_yield_outside.ax
- tests/std/sync/arc_mutex_threads.ax
- tests/std/sync/barrier_rendezvous.ax
- tests/std/sync/big_struct_sync.ax
- tests/std/sync/condvar_signaling.ax
- tests/std/sync/once_cell_init.ax
- tests/std/sync/rwlock_readers_writer.ax
- tests/std/thread/builder_and_detach.ax
- tests/std/thread/futex_sleep_yield_cancel.ax
- tests/std/thread/panic_containment.ax
- tests/std/thread/qa_thread_seam_and_reuse.ax
- tests/std/thread/scoped_threads.ax
- tests/std/thread/spawn_join_basic.ax

## Tests
All builds and tests executed in isolated snapshot `build-snap-T423e` (`HEAD 49e3f942` + 121 task files + 60 regenerated selfhost bundles):
- **Stage-2/3 fixed-point build**: `python tools/build_axiomc.py --out build --root . --stage 2` -> `STAGE1 OK`, `SEED-A (O1) OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`, `FIXED-POINT (O1) OK` (`sha256=7638b79fb9084646c72208d01d67787dcf05a46118426f2f02baf5e17560e2ff`, 8,973,312 bytes), `STAGE0-GUARD OK`.
- **New placeholder suite (`--no-cache`)**: `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter run/self_entry_placeholder` -> `TOTAL 15 PASS 15 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (5 tests x `interp`, `native`, `native-O1`: two modules in both orders, three modules in both orders incl. `[placeholder; 2]` repeat array, plain unmarked `__ax_thread_self_entry` / `__ax_fiber_self_entry`, non-matching `@lang("not_self_entry")`, and arbitrary custom `@lang("self_entry")` fn names).
- **Mutation liveness check**: mutating `2232` -> `2233` in `build-snap-T423e/tests/run/self_entry_placeholder/bug_two_modules_order_ab.ax` made `interp`, `native`, and `native-O1` all FAIL (`TOTAL 3 PASS 0 FAIL 3`); restoring returned `PASS 3 FAIL 0`.
- **Bundle freshness checks (`--check`)**: all 10 `gen_tests.py --check` scripts (`tests/std/fiber`, `tests/std/async/{executor,structured,waker,waker_qa}`, `tests/std/channel`, `tests/std/sync`, `tests/conformance/p11/{e11_3_threads_sync,e11_5_executors}`, `tests/perf/p11_executor`) exited 0.
- **Full per-task gate (`-j 2`)**: `python tools/taskgate.py --task T423e --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` -> `TASKGATE T423e exit=0`, `TOTAL 911 PASS 889 FAIL 0 SKIP 16 XFAIL 6` (`own` 101 ids / 280 results: 274 PASS, 0 FAIL, 6 pre-existing tracked XFAIL; `affected` 412 ids / 847 results: 831 PASS, 0 FAIL, 16 SKIP, incl. `tests/std/{thread,fiber,async,channel,sync}` and `selfhost/{interp,interp_opt,lir,mir}`; `smoke` 32 ids / 51 results: 51 PASS), `WEAK-NATIVE: 0` in own/changed tests, `BASELINE OK`, `Failing ids: none`, `unmatched changed files: none`, `archcheck: clean` (232 files scanned, 0 violations).
- **Harness hygiene**: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423e` -> exit 0 (122 staged, 0 `REFUSED`); `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
