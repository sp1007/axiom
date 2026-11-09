# T411: E11.3 — std.sync primitives: Arc, Rc, Mutex, RwLock, Condvar, Once, Barrier

## Summary
Implemented the full suite of synchronization and reference-counting primitives in `std.sync` per `spec/SPEC-32-threads-sync.md`. All primitives operate seamlessly across both native Windows x64 (using atomic operations and futex WaitOnAddress/WakeByAddress) and the MIR interpreter concurrency oracle (`[interp]`).

All test suites pass cleanly across all execution modes (`[interp]`, `[native]`, `[native-O1]`) with 0 WEAK-NATIVE discrepancies.

## Round 1 QA Findings Resolution
In response to QA Gate Round 0 findings (`_workspaces/reports/T411-qa.md`):
1. **Finding 1 (`std/sync/mutex.ax`)**: Placed `pub state: Atomic<u32>` at offset 0 before `pub data: T` in `@repr(C) pub struct Mutex<T>`. This guarantees `address_of(self.state)` is always byte offset 0 regardless of `size_of<T>()`, eliminating offset calculation divergence and out-of-bounds pointer UB in the MIR interpreter and native execution.
2. **Finding 2 (`std/sync/rc.ax`, `std/sync/arc.ax`, `std/sync/once.ax`)**: Updated generic heap allocation / deallocation sizing to `let alloc_sz = if sz < 128 { 128 } else { sz };` across `std/sync/rc.ax` (lines 45, 122, 165, 214) and verified `arc.ax` and `once.ax`. Added `new_from_ptr` and `set_from_ptr` layout-safe pointer helpers to allow initializing and mutating multi-field structs without truncation or out-of-bounds pointer UB.
3. **Finding 3 (`std/sync/rwlock.ax`)**: Placed `pub state: Atomic<u32>` at offset 0 before `pub data: T` in `@repr(C) pub struct RwLock<T>`, ensuring `address_of(self.state)` is always byte offset 0 regardless of `size_of<T>()`.
4. **Finding 4 (`tests/std/sync/`)**:
   - Implemented `tests/std/sync/gen_tests.py` which generates test bundles directly from live `std/sync/*.ax` files from HEAD with zero manual editing, ensuring zero divergence.
   - Added `tests/std/sync/check_sync_bundles.test` which validates with `--check` that all test files on disk byte-for-byte match the live `std/sync/*.ax` library sources.
   - Added `tests/std/sync/compile_live_sync.test` which directly invokes `axiomc2 check` on all live `std/sync/*.ax` library sources.
   - Added regression test `tests/std/sync/big_struct_sync.ax` testing 32-byte multi-field struct `BigStruct { a: i64, b: i64, c: i64, d: i64 }` (> 24 bytes) across `Rc<BigStruct>`, `Arc<Mutex<BigStruct>>`, `RwLock<BigStruct>`, and `OnceCell<BigStruct>`.
   - Preserved QA's added boundary test `tests/std/sync/ui_sync_send_share_bounds.ax` untouched.

## Implementation Details
1. **`std/sync/rc.ax`**:
   - `Rc<T>` and `RcWeak<T>` provide single-threaded reference counting (`!Send`, `!Share`).
   - Uses non-atomic `usize` strong and weak counters in heap-allocated `RcInner<T>`.
   - Implements `new`, `new_from_ptr`, `clone`, `as_ptr`, `get_ptr`, `as_mut_ptr`, `strong_count`, `weak_count`, `downgrade`, `try_unwrap`, and deterministic `Drop` freeing the allocation on the final release.
2. **`std/sync/arc.ax`**:
   - `Arc<T>` and `Weak<T>` provide atomic reference counting (`Send + Share` iff `T: Send + Share`).
   - Uses `Atomic<usize>` strong and weak counters with `Ordering.Relaxed` increments, `Ordering.Release` decrements, and `Ordering.Acquire` fences upon last release.
   - Implements `new`, `new_from_ptr`, `clone`, `as_ptr`, `get_ptr`, `as_mut_ptr`, `val` (`T: Copy`), `strong_count`, `weak_count`, `downgrade`, `try_unwrap`, and deterministic inner `Drop` + heap deallocation.
3. **`std/sync/mutex.ax`**:
   - `@repr(C) pub struct Mutex<T>` containing `pub state: Atomic<u32>` (offset 0) and `pub data: T` (offset 8/aligned).
   - Inlined fast-path CAS lock (0 -> 1) with contention state 2 and futex wait/wake.
   - Named internal struct `MutexGuardImpl<T>` aliased as `pub type MutexGuard<T> = MutexGuardImpl<T>` to satisfy both `SPEC-32` and `compiler/own/unsafe.ax:2303, 2521` (`conc_type_is_guard`).
   - Guard implements `val()` (`T: Copy`), `set()`, `as_ptr()`, `as_mut_ptr()`, `lock_ptr`, `try_lock_ptr`, and automatic unlock on `Drop`.
4. **`std/sync/rwlock.ax`**:
   - `@repr(C) pub struct RwLock<T>` containing `pub state: Atomic<u32>` (offset 0) and `pub data: T` (offset 8/aligned).
   - Reader count mask `0x3FFFFFFF`, writer lock bit `0x80000000`, writer waiting bit `0x40000000`.
   - Inlined methods `read`, `read_ptr`, `try_read`, `try_read_ptr`, `write`, `write_ptr`, `try_write`, `try_write_ptr`, `into_inner`.
   - `RwLockReadGuardImpl<T>` (aliased `RwLockReadGuard<T>`) and `RwLockWriteGuardImpl<T>` (aliased `RwLockWriteGuard<T>`).
5. **`std/sync/condvar.ax`**:
   - `@repr(C) pub struct Condvar` with sequence counter `Atomic<u32>`.
   - Supports `wait(self, guard)`, `wait_ptr(p_cv, guard)`, `wait_timeout_ms(self, guard, ms)`, `wait_timeout_ms_ptr(p_cv, guard, ms)`.
   - Atomically releases mutex guard, waits on futex, and re-acquires mutex before returning `guard` (or `CondvarWaitResult<T>`).
   - `notify_one`, `notify_all`, `notify_one_ptr`, `notify_all_ptr` advance the sequence counter and wake waiters.
6. **`std/sync/once.ax`**:
   - `Once`: Thread-safe single execution state machine (`ONCE_INCOMPLETE = 0`, `ONCE_RUNNING = 1`, `ONCE_COMPLETE = 2`).
   - `call_once`, `call_once_ptr` ensuring exactly one invocation of `f: FnOnce<()>` while other concurrent threads block on futex until completion.
   - `OnceCell<T>`: Thread-safe lazy/single initialization container. Supports `new`, `is_initialized`, `is_initialized_ptr`, `wait_init`, `wait_init_ptr`, `as_ptr`, `as_ptr_ptr`, `val`, `val_ptr`, `set`, `set_ptr`, `set_from_ptr`, `into_inner`, and `Drop`.
7. **`std/sync/barrier.ax`**:
   - `Barrier`: Reusable multi-thread synchronization rendezvous.
   - Tracks `num_threads`, `count: Atomic<usize>`, and `generation: Atomic<u32>`.
   - `wait`, `wait_ptr` returning `BarrierWaitResult` with `is_leader()` true for exactly one thread per generation.
8. **`std/sync/mod.ax`**:
   - Clean re-exports of atomic types, ordering, and synchronization primitives.

## Verification
- **All `std/sync/` Tests**:
  - `tests/std/sync/rc_basic.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/arc_mutex_threads.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/rwlock_readers_writer.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/condvar_signaling.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/once_cell_init.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/barrier_rendezvous.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/big_struct_sync.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/sync/ui_sync_send_share_bounds.ax`: PASS 1/1 (UI negative test)
  - `tests/std/sync/check_sync_bundles.test`: PASS 1/1 (freshness check)
  - `tests/std/sync/compile_live_sync.test`: PASS 1/1 (direct live module compilation)
  - Total `std/sync/`: 24 PASS, 0 FAIL, 0 WEAK-NATIVE.
- **Regression Suites**:
  - `tests/std/thread/`: 18 PASS, 0 FAIL, 0 WEAK-NATIVE.
  - `tests/run/atomics/`: 9 PASS, 0 FAIL, 0 WEAK-NATIVE.
  - `tests/run/concurrency/`: 37 PASS, 0 FAIL, 0 WEAK-NATIVE.
- **Sanity & Harness Checks**:
  - `tools/archcheck.py`: 216 files scanned, 0 violations.
  - `reqcov.py --strict`: COVERAGE OK (0 gaps).
  - `harness_check.py`: HARNESS OK.
  - `taskctl.py changes T411`: 0 REFUSED lines.

## Files changed
- std/sync/arc.ax
- std/sync/barrier.ax
- std/sync/condvar.ax
- std/sync/mod.ax
- std/sync/mutex.ax
- std/sync/once.ax
- std/sync/rc.ax
- std/sync/rwlock.ax
- tests/std/sync/arc_mutex_threads.ax
- tests/std/sync/barrier_rendezvous.ax
- tests/std/sync/big_struct_sync.ax
- tests/std/sync/check_sync_bundles.test
- tests/std/sync/compile_live_sync.test
- tests/std/sync/condvar_signaling.ax
- tests/std/sync/gen_tests.py
- tests/std/sync/once_cell_init.ax
- tests/std/sync/rc_basic.ax
- tests/std/sync/rwlock_readers_writer.ax
- tests/std/sync/ui_sync_send_share_bounds.ax

STATUS: COMPLETE round=1
