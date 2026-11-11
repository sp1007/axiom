# T414 Report — E11.3: Multi-threaded stress & synchronization conformance suite

## Summary
Task T414 establishes the native multi-threaded stress and synchronization conformance suite for exit criterion `E11.3` per `spec/SPEC-32-threads-sync.md` and requirements `REQ-CONC-036`, `REQ-CONC-037`, `REQ-CONC-038`, `REQ-CONC-039`, `REQ-CONC-081`, and `REQ-CONC-187`.

All 8 conformance tests (7 high-contention run tests and 1 negative compile-time UI test) plus the bundle freshness test pass cleanly across all supported execution modes (`[interp]`, `[native]`, and `[native-O1]`) with zero test failures and zero weak-native runs.

### Deliverables & Coverage
1. **`arc_mutex_8thread_stress.ax`** (`REQ-CONC-036`, `REQ-CONC-039`, `REQ-CONC-187`):
   - 8 concurrent threads mutating a shared 8-slot ring buffer under high contention (`Arc<Mutex<RingState>>`).
   - Verifies 160 total increments, ring slot checksum, `Mutex.try_lock_ptr` when unheld, and `Arc` strong/weak reference counting.
2. **`rwlock_reader_writer_stress.ax`** (`REQ-CONC-036`, `REQ-CONC-039`, `REQ-CONC-187`):
   - Multi-phase reader-heavy and writer-heavy synchronization stress over `Arc<RwLock<DataInvariant>>`.
   - Phase 1: 4 concurrent readers verifying mathematical invariant `a + b == sum`.
   - Phase 2: Writer mutation updating version and invariants, verified by subsequent read.
   - Phase 3: 4 concurrent writers competing for exclusive lock access, advancing version to 6.
   - Phase 4: `RwLock.try_read_ptr` and `try_write_ptr` mutual exclusion while locked and successful acquisition when unlocked.
3. **`condvar_barrier_work_queue.ax`** (`REQ-CONC-036`, `REQ-CONC-039`, `REQ-CONC-187`):
   - Work queue signaling and coordination via `Arc<Mutex<i64>>` and `Arc<Condvar>`.
   - Worker thread waits on `Condvar.wait_ptr` until producer signals data.
   - `Condvar.wait_timeout_ms_ptr` verifying timed-out result semantics.
   - `Barrier` rendezvous across 4 concurrent threads running 3 barrier phases, verifying exactly 1 leader elected per phase (3 total leaders).
4. **`once_concurrent_init_stress.ax`** (`REQ-CONC-036`, `REQ-CONC-039`, `REQ-CONC-187`):
   - Part 1: 8 racing threads invoking `Once.call_once_ptr` concurrently; exactly 1 runs the initialization closure while 7 block and observe publication.
   - Part 2: 8 racing threads calling `OnceCell.set_ptr`; exactly 1 thread succeeds (`Result.Ok(_)`) and 7 receive `Result.Err(_)`.
5. **`channel_mpmc_drop_stress.ax`** (`REQ-CONC-038`, `REQ-CONC-187`):
   - Part 1: Bounded MPMC pipeline with 4 producers sending 100 total items to 4 consumers across capacity-4 channel with drop-tracking payload.
   - Part 2: Bounded channel teardown drop verification: receiver dropped with unread items in buffer, verifying channel destruction drains and drops all remaining items.
   - Part 3: Unbounded 2-producer -> 2-worker -> 2-consumer forwarding pipeline (40 items) with drop verification.
6. **`scoped_threads_and_panic_containment.ax`** (`REQ-CONC-037`, `REQ-CONC-081`, `REQ-CONC-187`):
   - Part 1: `std.thread.scope` borrowing stack array and disjoint mutable variables across concurrent threads with automatic unjoined thread joining at scope exit.
   - Part 2: Panic containment at `JoinHandle` boundary: panicking child thread catches `ThreadPanic` in `Result.Err` without unwinding host process, verifying thread ID and message.
   - Part 3: Sibling assertion failure alongside healthy worker thread, followed by subsequent clean thread spawn.
7. **`tls_and_local_key_stress.ax`** (`REQ-CONC-036`, `REQ-CONC-039`, `REQ-CONC-187`):
   - `@thread_local static mut` multi-thread isolation: 4 worker threads independently mutate thread-local state without affecting main thread or siblings.
   - `std.thread.LocalKey<T>` thread-exit destructor cleanup: thread detachment executes `Drop` destructor hook on thread exit (`DDDD`).
8. **`sync_negative_conformance.ax`** (`REQ-CONC-036`, `REQ-CONC-037`, `REQ-CONC-038`, `REQ-CONC-039`):
   - Compile-time UI rejection of invalid `@thread_local` declarations (`AX_TYPE_INVALID_TLS_DECL`).
   - Rejection of `!Send` and `!Share` crossing thread boundaries (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`).
   - Rejection of capturing `!Send` primitives (`Rc`, `MutexGuard`, `RwLockWriteGuard`, `LocalKey`) in `spawn` closures (`AX_CONC_CAPTURE_NOT_SEND`).
   - Rejection of non-static stack views escaping into `spawn` (`AX_CONC_ESCAPING_VIEW`).
9. **Bundle Generator & Freshness Check**:
   - `gen_tests.py`: generates all 7 multi-module test bundles by assembling live standard library sources (`std/sync/*.ax`, `std/thread/*.ax`, `std/sys/windows/*.ax`).
   - `check_conformance_bundles.test`: automated regression check ensuring test bundles never diverge from live std sources.

## Files changed
- tests/conformance/p11/e11_3_threads_sync/README.md
- tests/conformance/p11/e11_3_threads_sync/arc_mutex_8thread_stress.ax
- tests/conformance/p11/e11_3_threads_sync/channel_mpmc_drop_stress.ax
- tests/conformance/p11/e11_3_threads_sync/check_conformance_bundles.test
- tests/conformance/p11/e11_3_threads_sync/condvar_barrier_work_queue.ax
- tests/conformance/p11/e11_3_threads_sync/gen_tests.py
- tests/conformance/p11/e11_3_threads_sync/once_concurrent_init_stress.ax
- tests/conformance/p11/e11_3_threads_sync/rwlock_reader_writer_stress.ax
- tests/conformance/p11/e11_3_threads_sync/scoped_threads_and_panic_containment.ax
- tests/conformance/p11/e11_3_threads_sync/sync_negative_conformance.ax
- tests/conformance/p11/e11_3_threads_sync/tls_and_local_key_stress.ax

## Verification & Test Results

### 1. Conformance Suite Results (`axtest.py`)
```powershell
python tools/axtest.py --root build-snap-T414 --compiler build-snap-T414/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 conformance/p11/e11_3_threads_sync
```
- `conformance/p11/e11_3_threads_sync/arc_mutex_8thread_stress.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/rwlock_reader_writer_stress.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/condvar_barrier_work_queue.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/once_concurrent_init_stress.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/channel_mpmc_drop_stress.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/scoped_threads_and_panic_containment.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/tls_and_local_key_stress.ax`: PASS [interp, native, native-O1]
- `conformance/p11/e11_3_threads_sync/sync_negative_conformance.ax`: PASS [ui]
- `conformance/p11/e11_3_threads_sync/check_conformance_bundles.test`: PASS [cmd]
- Summary: `TOTAL 23 PASS 23 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)

### 2. Live Standard Library Source Freshness
```powershell
python tests/conformance/p11/e11_3_threads_sync/gen_tests.py --check
```
- Output: `OK conformance bundles match live std sources`
- Exit Code: 0

### 3. Requirements Coverage Gate
```powershell
python .claude/skills/axiom-tasks/scripts/reqcov.py --strict
```
- Output: `requirements: 32309`, `gaps: 0`, `COVERAGE OK`
- Exit Code: 0

### 4. Harness & Environment Integrity Gate
```powershell
python .claude/skills/axiom-tasks/scripts/harness_check.py
```
- Output: `HARNESS OK`
- Exit Code: 0

### 5. Taskctl Changes Gate
```powershell
python .claude/skills/axiom-tasks/scripts/taskctl.py changes T414
```
- Output: `0 REFUSED`, all modified files staged in task paths/locks.
- Exit Code: 0

STATUS: COMPLETE round=0
