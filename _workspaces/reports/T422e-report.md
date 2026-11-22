# T422e report — async guard across `.await` (round 0)

## Summary

Fixed all three parts of the `AsyncMutexGuard`-across-`.await` bug per `SPEC-33 AXS-ASY-035`, `SPEC-34 AXS-EXEC-030..031` / `§6.1`, and `SPEC-30 AXS-CONC-035`, eliminating all user-visible type-name and method-name heuristics:

1. **Verifier suspend-point diagnostic messages & structural `@no_suspend_hold` recursion (`compiler/verify/verifier.ax`)**:
   - Fixed the four `Suspend`-terminator diagnostics in `verify_own_step_bb` (`compiler/verify/verifier.ax`) that previously indexed into `VERIFY_TEXT_DATA` slots `60..63` (drop-flag / capability messages, producing `AX_ASYNC_GUARD_ACROSS_AWAIT: drop flag local is not initialized in bb0`). Appended dedicated texts at indices `148..151`:
     - `148`: `use of uninitialized future at .await` (`AX_VERIFY_UNINIT_USE`)
     - `149`: `use of moved future at .await` (`AX_VERIFY_USE_AFTER_MOVE`)
     - `150`: `value containing a view is held across an .await suspension point` (`AX_ASYNC_VIEW_ACROSS_AWAIT`)
     - `151`: `synchronous lock guard or @no_suspend_hold value is held across an .await suspension point` (`AX_ASYNC_GUARD_ACROSS_AWAIT`)
   - Extended `verify_type_is_guard` to recurse structurally through `TY_ARRAY`, `TY_SLICE`, `TY_ENUM` (including generic variant substitution from `AxType.args`, e.g. `Option<MutexGuard<T>>` returned by `Mutex.try_lock()`), and generic `TY_STRUCT` type parameters, as well as `@no_suspend_hold` enums.
   - Locals living across suspension points are already stored in the coroutine frame and initialized/dropped accurately; there was no drop-flag lowering defect.

2. **Marker-only `@no_suspend_hold` guard classification (`compiler/types/typeck.ax`, `std/sync/mutex.ax`, `std/sync/rwlock.ax`)**:
   - Removed `tc_sv_is_guard_name` (`*Guard` / `*GuardImpl` suffix heuristic) from `compiler/types/typeck.ax`; `tc_is_guard_struct` / `tc_mark_guard_structs` now mark a `struct` or `enum` **iff** it carries `@no_suspend_hold`.
   - Annotated `MutexGuardImpl<T>` (`std/sync/mutex.ax`), `RwLockReadGuardImpl<T>`, and `RwLockWriteGuardImpl<T>` (`std/sync/rwlock.ax`) with `@no_suspend_hold` (`MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>` type aliases inherit it), while `AsyncMutexGuard<T>` (`std/async/sync.ax`) remains unmarked per `SPEC-34 AXS-EXEC-031`.
   - Regenerated all `tests/std/sync` and `tests/conformance/p11/e11_3_threads_sync` bundles embedding `std/sync/{mutex,rwlock}.ax`, and added `@no_suspend_hold` to the local mock guard structs in `tests/ui/async/lock_guard_await/*`, `tests/conformance/p11/e11_4_async/async_ui_guard_across_await.ax`, `tests/conformance/p11/e11_1_concurrency/ui_lock_guard_escape.ax`, `tests/ui/concurrency/data_race/guard_escape_and_atomic_mut_view.ax`, and `tests/ui/concurrency/data_race/qa_arc_and_boundary_races.ax`.

3. **Type/attribute-based `AX_CONC_GUARD_ESCAPE` in `compiler/own/unsafe.ax`**:
   - Removed `conc_sv_is_guard_name` (`MutexGuard`..`WriteGuard` exact-name list) and removed the `.lock()` / `.read()` / `.write()` method-name heuristic (`CONC_STR` 45..47) in `conc_extract_region`.
   - `conc_type_is_guard` is now purely attribute/type-based (`@no_suspend_hold` on struct/enum definitions, recursive across tuples, arrays, slices, generic structs, and generic enums).
   - `conc_extract_region` marks a call/method result region `from_guard = true` only when the call's return type satisfies `conc_type_is_guard` (or propagates `from_guard` from a guard receiver/argument when the return type is a guard or contains a `view`/`mut_view`), so `AsyncMutex.lock()` -> `AsyncMutexLockFuture<T>` no longer triggers `AX_CONC_GUARD_ESCAPE` and plain scalar copies (`g.val() -> i64`) read from a guard do not falsely taint the scalar binding as a guard.
   - Anchored `let g = ...` guard bindings at `g`'s own lexical `scope_depth`, distinguished function parameters and value constructors from local bindings in `conc_expr_is_from_guard`, and avoided marking locks acquired *inside* a concurrent closure as outer-scope guard captures.

4. **SPEC-34 §6.1 (`spec34_local_executor_example.ax`)**:
   - Removed `xfail: T422e AsyncMutexGuard across await rejected` from `tests/std/async/structured/gen_tests.py` and regenerated `tests/std/async/structured/spec34_local_executor_example.ax`.
   - `spec34_local_executor_example.ax` now compiles cleanly and **PASSes** in `[interp]` (`OK spec34_local_executor_example 40`). Its native legs carry `native-after: T422d` (matching `spec34_task_group_example.ax` on the preceding line) because `increment_local` / `sum_both` `.await` generic `Future` impls (`AsyncMutexLockFuture<i64>`, `LocalTaskHandle<i64>`), which is tracked by `T422d` (widened to include `tests/std/async/structured`).

## Files changed
- compiler/own/unsafe.ax
- compiler/types/typeck.ax
- compiler/verify/verifier.ax
- std/sync/mutex.ax
- std/sync/rwlock.ax
- tests/conformance/p11/e11_1_concurrency/ui_lock_guard_escape.ax
- tests/conformance/p11/e11_3_threads_sync/arc_mutex_8thread_stress.ax
- tests/conformance/p11/e11_3_threads_sync/condvar_barrier_work_queue.ax
- tests/conformance/p11/e11_3_threads_sync/qa_condvar_broadcast_weak_stress.ax
- tests/conformance/p11/e11_3_threads_sync/rwlock_reader_writer_stress.ax
- tests/conformance/p11/e11_4_async/async_ui_guard_across_await.ax
- tests/run/async_guard_across_await/async_lock_method_and_user_mutex_guard_name.ax
- tests/run/async_guard_across_await/async_mutex_guard_name_held.ax
- tests/run/async_guard_across_await/drop_guard_once_after_resume.ax
- tests/run/async_guard_across_await/renamed_non_drop_guard.ax
- tests/std/async/structured/gen_tests.py
- tests/std/async/structured/spec34_local_executor_example.ax
- tests/std/sync/arc_mutex_threads.ax
- tests/std/sync/barrier_rendezvous.ax
- tests/std/sync/big_struct_sync.ax
- tests/std/sync/condvar_signaling.ax
- tests/std/sync/gen_tests.py
- tests/std/sync/once_cell_init.ax
- tests/std/sync/rwlock_readers_writer.ax
- tests/std/sync/ui_std_sync_guard_await_and_escape.ax
- tests/std/sync/ui_std_sync_guard_escape.ax
- tests/ui/async/lock_guard_await/lock_guard_dropped_pos.ax
- tests/ui/async/lock_guard_await/lock_guard_mutex_neg.ax
- tests/ui/async/lock_guard_await/lock_guard_rwlock_neg.ax
- tests/ui/async_guard_across_await/nested_tuple_enum_array_guard_neg.ax
- tests/ui/async_guard_across_await/no_suspend_hold_escape_neg.ax
- tests/ui/async_guard_across_await/no_suspend_hold_released_before_await_pos.ax
- tests/ui/async_guard_across_await/no_suspend_hold_sync_guard_neg.ax
- tests/ui/concurrency/data_race/guard_escape_and_atomic_mut_view.ax
- tests/ui/concurrency/data_race/qa_arc_and_boundary_races.ax
- _workspaces/reports/T422e-report.md

## Tests
All built and verified inside isolated snapshot `build-snap-T422e/` (`HEAD 4f2daaf08dc1` + T422e change set + 60 regenerated selfhost bundles):
- **Stage-2/3 build (`python tools/build_axiomc.py --out build --root . --stage 2`)**:
  - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == d32b19bbe7c6b6a2629b5afafb4feec0db87b0a63a6e2939148f684061cd41d8` (8,962,560 bytes)
  - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`
- **Targeted `--no-cache -j 2` suites**:
  - `async_guard_across_await` (4 run tests x `interp`/`native`/`native-O1` + 4 UI tests): `TOTAL 16 PASS 16 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - Native liveness spot-proof (in `build-snap-T422e` only): mutated `stdout:` directive of `async_mutex_guard_name_held.ax` (`name_held 5` -> `name_held 999`) -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1`); restored -> `TOTAL 3 PASS 3 FAIL 0`.
  - `ui/async`: `TOTAL 26 PASS 26 FAIL 0 SKIP 0 XFAIL 0` (incl. `lock_guard_await/*`).
  - `std/sync`: `TOTAL 26 PASS 26 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (incl. `ui_std_sync_guard_await_and_escape.ax` and `ui_std_sync_guard_escape.ax` against live `std.sync.Mutex` / `std.sync.RwLock`).
  - `std/async/structured`: `TOTAL 50 PASS 46 FAIL 0 SKIP 4 XFAIL 0`, `WEAK-NATIVE 0` (`spec34_local_executor_example.ax` `[interp]` PASS).
  - `ui/concurrency`: `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`.
  - `conformance/p11` (`e11_1`..`e11_5`): `TOTAL 144 PASS 144 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- **Full per-task gate (`python tools/taskgate.py --task T422e --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`)**:
  - `own`: 56 ids, 126 results (122 PASS, 0 FAIL, 4 SKIP)
  - `affected`: 394 ids, 820 results (815 PASS, 0 FAIL, 5 SKIP)
  - `smoke`: 32 ids, 55 results (55 PASS, 0 FAIL, 0 SKIP)
  - **Total (dedup)**: 425 ids, `TOTAL 874 PASS 869 FAIL 0 SKIP 5 XFAIL 0` (exit 0, wall 1925.9 s)
  - `WEAK-NATIVE`: `0 in the task's own/changed tests`
  - `Baseline`: `BASELINE OK`, `Failing ids: none`
  - `archcheck`: `clean (exit 0) archcheck: 232 files scanned, 0 violations`
  - `smoke-check`: `OK; est. worst-case draw 28 s`
  - `TASKGATE T422e exit=0`
- **Board & staging hygiene**:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T422e`: exit 0, 0 `REFUSED` lines (36 staged files).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0).

## Spec deviations
none

## Follow-ups
- `T422d` (already open and widened to include `tests/std/async/structured`) removes `// native-after: T422d` from `spec34_local_executor_example.ax` and `spec34_task_group_example.ax` once native `.await` on generic `Future` impls lands.

STATUS: COMPLETE round=0
