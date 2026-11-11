# E11.3 — Multi-Threaded Stress & Synchronization Conformance Suite (`tests/conformance/p11/e11_3_threads_sync`)

Governing specification: `spec/SPEC-32-threads-sync.md` (Phase 11, Epic E11.3, Task `T414`).

## Suite Inventory

| Test File | Test Kind | Execution Modes | Purpose & Covered Rules |
|---|---|---|---|
| `arc_mutex_8thread_stress.ax` | `run` | `interp`, `native`, `native-O1` | 8-thread `Arc<Mutex<T>>` high-contention counter & ring buffer mutation stress (`AXS-SYNC-030`, `AXS-SYNC-031`, `AXS-SYNC-010`..`012`, `AXS-SYNC-051`). Verifies mutual exclusion, slot invariant conservation, checksum integrity, `try_lock`, and `Arc` strong/weak reference lifecycle across 8 concurrent OS threads. |
| `rwlock_reader_writer_stress.ax` | `run` | `interp`, `native`, `native-O1` | Reader-heavy (6 readers, 2 writers) and writer-heavy (4 writers) `RwLock<T>` contention stress (`AXS-SYNC-032`, `AXS-SYNC-051`). Proves zero torn reads across concurrent readers (`a + b == sum`), serialized exclusive mutation across writers, and `try_read`/`try_write` behavior. |
| `condvar_barrier_work_queue.ax` | `run` | `interp`, `native`, `native-O1` | `Condvar` bounded work queue (2 producers, 2 consumers, 8-slot ring buffer) with predicate loops + multi-generation `Barrier` rendezvous (`AXS-SYNC-033`, `AXS-SYNC-035`, `AXS-SYNC-051`). Verifies backpressure, cooperative shutdown notification, exact item processing, multi-phase barrier reuse without deadlock/ABA, and `wait_timeout_ms` timeout expiration. |
| `once_concurrent_init_stress.ax` | `run` | `interp`, `native`, `native-O1` | 8-thread concurrent initialization race for `Once` and `OnceCell<T>` (`AXS-SYNC-034`, `AXS-SYNC-051`). Proves that `Once.call_once` executes its closure exactly once across racing threads, `OnceCell.set` admits exactly 1 winner while returning rejected values to 7 losers, and initialized data is published with `Happens-Before` visibility. |
| `channel_mpmc_drop_stress.ax` | `run` | `interp`, `native`, `native-O1` | Multi-Producer Multi-Consumer (MPMC) bounded and unbounded channel pipelines with drop-tracked payloads (`AXS-SYNC-040`..`AXS-SYNC-044`, `AXS-SYNC-051`). Proves backpressure in bounded ring buffers, graceful shutdown on last sender drop, receiver teardown draining and dropping all unread items, and exact ownership accounting (`constructed == dropped`) without leaks or double-drops. |
| `scoped_threads_and_panic_containment.ax` | `run` | `interp`, `native`, `native-O1` | Structured concurrency `std.thread.scope` + child thread panic containment via `JoinHandle` (`AXS-SYNC-014`, `AXS-SYNC-015`, `AXS-SYNC-051`). Proves concurrent scoped borrowing of parent stack slices (`view<[i64]>`) and disjoint mutable variables (`mut_view<i64>`) with automatic joining of unjoined children at scope exit; proves child panic (`panic(...)`, `assert(false)`) is caught at the thread boundary and returned as `Result.Err(ThreadPanic)` without corrupting healthy sibling threads or unwinding the parent. |
| `tls_and_local_key_stress.ax` | `run` | `interp`, `native`, `native-O1` | `@thread_local` statics and `LocalKey<T>` multi-thread isolation + thread-exit `Drop` cleanup (`AXS-SYNC-020`..`AXS-SYNC-024`, `AXS-SYNC-051`). Proves each thread observes independent static state without cross-thread data races, and verifies that registered thread-local `Drop` destructors execute deterministically when child threads terminate. |
| `sync_negative_conformance.ax` | `ui` | compile check | Negative compile-time conformance cases (`AXS-SYNC-050`, `AXS-SYNC-051`). Verifies rejection of: `!Send` / `!Share` capture in `spawn` (`AX_CONC_CAPTURE_NOT_SEND`, `AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`), escaping non-static views (`AX_CONC_ESCAPING_VIEW`), escaping `@thread_local` views (`AX_CONC_TLS_ESCAPE`), invalid `@thread_local` declarations (`AX_TYPE_INVALID_TLS_DECL`), and unsynchronized mutable statics (`AX_CONC_UNSYNC_STATIC`). |
| `qa_condvar_broadcast_weak_stress.ax` | `run` | `interp`, `native`, `native-O1` | QA boundary test: `Condvar.notify_all` broadcast across 4 concurrent waiting threads, single-thread `Barrier` boundary rendezvous, and `Arc` weak reference downgrade, upgrade, and post-drop expiration (`AXS-SYNC-030`, `AXS-SYNC-033`, `AXS-SYNC-035`, `AXS-SYNC-051`). |
| `check_conformance_bundles.test` | `cmd` | python `--check` | Verifies all generated test bundles in this directory are byte-for-byte identical to the output of `gen_tests.py` using live `std/` sources. |

## Requirement Traceability Matrix (`T414` Primary & `E11.3` Complete)

| Requirement ID | Summary (`spec/requirements/CATALOG.md`) | Conformance Test File(s) |
|---|---|---|
| `REQ-CONC-036` | Thread completion `Happens-Before` and result ownership transfer via `JoinHandle.join()`. | `arc_mutex_8thread_stress.ax`, `rwlock_reader_writer_stress.ax`, `condvar_barrier_work_queue.ax`, `once_concurrent_init_stress.ax`, `tls_and_local_key_stress.ax`, `sync_negative_conformance.ax`, `qa_condvar_broadcast_weak_stress.ax` |
| `REQ-CONC-037` | Value-based panic reporting via `JoinHandle.join() -> Result.Err(ThreadPanic)` without implicit parent unwinding. | `scoped_threads_and_panic_containment.ax`, `sync_negative_conformance.ax` |
| `REQ-CONC-038` | Explicit thread detachment and task-bound resource lifecycle. | `channel_mpmc_drop_stress.ax`, `scoped_threads_and_panic_containment.ax`, `sync_negative_conformance.ax` |
| `REQ-CONC-039` | Resource safety and deterministic drop execution across thread lifecycle and channel teardown. | `arc_mutex_8thread_stress.ax`, `rwlock_reader_writer_stress.ax`, `condvar_barrier_work_queue.ax`, `once_concurrent_init_stress.ax`, `channel_mpmc_drop_stress.ax`, `tls_and_local_key_stress.ax`, `sync_negative_conformance.ax`, `qa_condvar_broadcast_weak_stress.ax` |
| `REQ-CONC-081` | Panic propagation and failure containment without corrupting sibling threads or uncoordinated parent process termination. | `scoped_threads_and_panic_containment.ax` |
| `REQ-CONC-187` | Memory ordering and release/acquire synchronization across thread joins, scopes, locks, and channels. | `arc_mutex_8thread_stress.ax`, `rwlock_reader_writer_stress.ax`, `condvar_barrier_work_queue.ax`, `once_concurrent_init_stress.ax`, `channel_mpmc_drop_stress.ax`, `scoped_threads_and_panic_containment.ax`, `tls_and_local_key_stress.ax`, `qa_condvar_broadcast_weak_stress.ax` |

## `SPEC-32` Rule Traceability Matrix (`AXS-SYNC-*`)

| Spec Rule | Summary | Tested In |
|---|---|---|
| `AXS-SYNC-001`..`004` | Host threading intrinsics, Windows x64 lowering, and MIR interpreter cooperative scheduler. | All 7 run tests |
| `AXS-SYNC-010`..`013` | `std.thread` types, `spawn`, move captures, `join()` completion, and linear handle ownership. | `arc_mutex_8thread_stress.ax`, `rwlock_reader_writer_stress.ax`, `condvar_barrier_work_queue.ax`, `once_concurrent_init_stress.ax`, `channel_mpmc_drop_stress.ax`, `scoped_threads_and_panic_containment.ax`, `tls_and_local_key_stress.ax` |
| `AXS-SYNC-014` | Structured concurrency `std.thread.scope`, scoped stack borrows, and mandatory join-before-return barrier. | `scoped_threads_and_panic_containment.ax` |
| `AXS-SYNC-015` | Child thread panic containment at `JoinHandle` boundary (`Result.Err(ThreadPanic)`). | `scoped_threads_and_panic_containment.ax` |
| `AXS-SYNC-016` | Cooperative cancellation protocol and prohibition of forced thread killing. | `scoped_threads_and_panic_containment.ax`, `condvar_barrier_work_queue.ax` |
| `AXS-SYNC-020`..`024` | `@thread_local` static identity, `!Share` isolation, `LocalKey<T>` scoped access, thread-exit `Drop` cleanup, and x64 TLS lowering. | `tls_and_local_key_stress.ax`, `sync_negative_conformance.ax` |
| `AXS-SYNC-030` | `Rc<T>` single-threaded vs `Arc<T>` atomic reference counting, strong/weak counts, and conditional auto-traits. | `arc_mutex_8thread_stress.ax`, `sync_negative_conformance.ax` |
| `AXS-SYNC-031` | `Mutex<T>` data protection, 3-state futex locking, `try_lock`, and lock-to-unlock `Happens-Before`. | `arc_mutex_8thread_stress.ax`, `condvar_barrier_work_queue.ax`, `sync_negative_conformance.ax` |
| `AXS-SYNC-032` | `RwLock<T>` reader-heavy and writer-heavy synchronization, shared-read/exclusive-write exclusivity, and `try_read`/`try_write`. | `rwlock_reader_writer_stress.ax`, `sync_negative_conformance.ax` |
| `AXS-SYNC-033` | `Condvar` wait/notify protocol, mandatory predicate loop, and `wait_timeout_ms`. | `condvar_barrier_work_queue.ax` |
| `AXS-SYNC-034` | `Once` and `OnceCell<T>` one-time initialization race, single winner, and happens-before publication. | `once_concurrent_init_stress.ax` |
| `AXS-SYNC-035` | `Barrier` reusable multi-thread rendezvous, generation progression, and leader election. | `condvar_barrier_work_queue.ax` |
| `AXS-SYNC-040`..`044` | Channels move-only ownership transfer, bounded backpressure, MPMC topologies, receiver drop drain, and exact drop accounting. | `channel_mpmc_drop_stress.ax`, `sync_negative_conformance.ax` |
| `AXS-SYNC-050` | Canonical diagnostic taxonomy (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, `AX_CONC_CAPTURE_NOT_SEND`, `AX_CONC_ESCAPING_VIEW`, `AX_CONC_TLS_ESCAPE`, `AX_TYPE_INVALID_TLS_DECL`, `AX_CONC_UNSYNC_STATIC`). | `sync_negative_conformance.ax` |
| `AXS-SYNC-051` | Concurrency & multi-threaded stress verification matrix across interpreter and native targets. | All files in this suite |
