# E11.1 — Concurrency & Data-Race Conformance Suite (`tests/conformance/p11/e11_1_concurrency`)

Governing specification: `spec/SPEC-30-concurrency.md` (Phase 11, Epic E11.1, Task `T404`).

## Suite Inventory

| Test File | Mode | Purpose |
|---|---|---|
| `ui_send_not_equal_share.ax` | `ui` | Negative compile-time checks proving `Send != Share` orthogonality, `view<T>` / `mut_view<T>` marker rules, sync wrapper (`Arc`, `Mutex`, `RwLock`) bounds, structural derivation, generic boundary checks, and `unsafe`-only positive `Send`/`Share` impls. |
| `ui_non_send_across_spawn.ax` | `ui` | Negative compile-time checks rejecting `!Send` raw pointers (`*mut T`, `*const T`), FFI opaque handles, `Rc`/`LocalRc`, and explicit `!Send` types across `spawn` captures and `JoinHandle` return types (`AX_CONC_CAPTURE_NOT_SEND`, `AX_CONC_NOT_SEND`). |
| `ui_spawn_use_after_move.ax` | `ui` | Negative compile-time checks rejecting use-after-move in the parent scope or a second `spawn` after an owned `!Copy` binding has been moved into `spawn` or `spawn_local` (`AX_MOVE_USE_AFTER_MOVE`). |
| `ui_non_share_interior_mut_across_threads.ax` | `ui` | Negative compile-time checks rejecting `view<T>` of `!Share` interior-mutable and thread-pinned types (`Cell`, `RefCell`, `UnsafeCell`, `CellBox`, `Rc`, `ThreadLocal`, raw-pointer wrappers, `Arc<Cell>`, explicit `!Share`) across `par_join`, `spawn_scoped`, and `share_view` (`AX_CONC_VIEW_NOT_SHARE`). |
| `ui_escaping_view_and_guard_captures.ax` | `ui` | Negative compile-time checks rejecting non-static `view<T>`, `mut_view<T>`, and implicit mutable borrows escaping into `spawn`, `spawn_local`, or returned views (`AX_CONC_ESCAPING_VIEW`). |
| `ui_lock_guard_escape.ax` | `ui` | Negative compile-time checks rejecting lock guards (`MutexGuard`, `RwLockReadGuard`, `RwLockWriteGuard`) or guard-derived views escaping function return, inner lexical block scope, or concurrency boundaries (`AX_CONC_GUARD_ESCAPE`), plus unsynchronized `mut_view` into `AtomicI32` (`AX_CONC_ATOMIC_MUT_VIEW`). |
| `ui_read_write_and_write_write_races.ax` | `ui` | Negative compile-time checks rejecting `READ/WRITE`, `WRITE/READ`, and `WRITE/WRITE` races across scalars, struct fields, containing places (`CONTAINS`), tuples, overlapping constant slices (`OVERLAP`), dynamic indices/slices (`UNKNOWN` disjointness), `Arc<T>` without `Mutex`, and `unsafe` safe-view re-entry (`AX_CONC_SHARED_MUT`, `AX_CONC_VIEW_NOT_SHARE`). |
| `ui_invalid_atomic_contracts.ax` | `ui` | Negative compile-time checks rejecting invalid atomic payload types (`AX_CONC_INVALID_ATOMIC_TYPE`), under-aligned/packed atomics (`AX_CONC_INVALID_ATOMIC_ALIGNMENT`), non-atomic `mut_view` / private field access (`AX_CONC_ATOMIC_MUT_VIEW`), and invalid memory orderings (`AX_CONC_INVALID_ATOMIC_ORDERING`). |
| `ui_unsync_mutable_statics.ax` | `ui` | Negative compile-time checks rejecting process-global immutable `static` items with `!Share` types (`AX_CONC_UNSYNC_STATIC`), rejecting safe access to `static mut` (`AX_CONC_UNSYNC_STATIC`), and rejecting concurrent `mut_view` races on `static mut` inside `unsafe` (`AX_CONC_SHARED_MUT`). |
| `run_send_ownership_transfer.ax` | `run` (`interp`, `native` `-O0`, `native-O1`) | Positive runtime conformance for `Send` ownership transfer across `spawn`, `Copy` capture retention in parent, uncaptured `!Send` outer locals, `Send + !Share` transfer, `!Send` local task execution via `spawn_local`, and cooperative cancellation vs panic lifecycle state separation. |
| `run_share_concurrent_read_views.ax` | `run` (`interp`, `native` `-O0`, `native-O1`) | Positive runtime conformance for concurrent read-only `view<T>` (`READ/READ`) across `par_join` and sibling `spawn_scoped` tasks, structural `Share` derivation, sync wrapper marker rules (`Mutex<T>: Share` when `T: Send`), and non-escaping lexical lock guard scopes. |
| `run_disjoint_struct_and_slice_mutation.ax` | `run` (`interp`, `native` `-O0`, `native-O1`) | Positive runtime conformance for parallel `mut_view` mutation of disjoint struct fields (`p.a` vs `p.b`), nested disjoint struct paths (`tree.left.a` vs `tree.right.b`), 3-way disjoint fields, disjoint tuple fields (`.0` vs `.1`), disjoint constant array indices (`arr[0]` vs `arr[3]`), and non-overlapping slice ranges (`ms0[0..2]` vs `ms0[2..4]`, `ms[..mid]` vs `ms[mid..]`). |
| `run_happens_before_and_domain_contracts.ax` | `run` (`interp`, `native` `-O0`, `native-O1`) | Positive runtime conformance for `Release`/`Acquire` atomic publication, `fence` / `compiler_fence` barriers, notification (`Relaxed`) vs publication (`Release`/`Acquire`) distinction, explicit host-device GPU barrier synchronization, cross-process byte serialization, and `@repr(C)` shared-memory contracts. |
| `mir_happens_before_and_zero_cost_erasure.ax` (`.test`) | `inspect` (`--emit=mir-opt -O1`) | Verifies zero-cost `Send`/`Share` marker erasure and happens-before barrier preservation (`atomic_store Release`, `atomic_fence Acquire`, `atomic_rmw add AcqRel`, `atomic_cmpxchg AcqRel Acquire`, `spin_loop_hint`, `atomic_load Acquire`, `compiler_fence SeqCst`) under `-O1` optimization. |

## Rule & Invariant Traceability Matrix

| Spec Rule / Invariant / Requirement | Covered By |
|---|---|
| `AXS-CONC-001` .. `AXS-CONC-008` | `run_send_ownership_transfer.ax`, `run_share_concurrent_read_views.ax`, `ui_unsync_mutable_statics.ax` |
| `AXS-CONC-010` .. `AXS-CONC-019` | `ui_send_not_equal_share.ax`, `ui_non_share_interior_mut_across_threads.ax`, `run_send_ownership_transfer.ax`, `run_share_concurrent_read_views.ax`, `mir_happens_before_and_zero_cost_erasure.ax` |
| `AXS-CONC-020` .. `AXS-CONC-026` | `ui_non_send_across_spawn.ax`, `ui_spawn_use_after_move.ax`, `ui_escaping_view_and_guard_captures.ax`, `run_send_ownership_transfer.ax`, `run_share_concurrent_read_views.ax` |
| `AXS-CONC-030` .. `AXS-CONC-038` | `ui_read_write_and_write_write_races.ax`, `ui_unsync_mutable_statics.ax`, `ui_lock_guard_escape.ax`, `ui_non_send_across_spawn.ax`, `run_disjoint_struct_and_slice_mutation.ax` |
| `AXS-CONC-040` .. `AXS-CONC-047` | `ui_invalid_atomic_contracts.ax`, `run_happens_before_and_domain_contracts.ax`, `mir_happens_before_and_zero_cost_erasure.ax` |
| `AXS-CONC-050` .. `AXS-CONC-052` | `run_happens_before_and_domain_contracts.ax` |
| `ACONC-20` .. `ACONC-30`, `ACONC-76` | All 14 files in `tests/conformance/p11/e11_1_concurrency/` |
| `ACONCUR-140` .. `ACONCUR-155`, `ACONCUR-158`, `ACONCUR-163` .. `ACONCUR-165`, `ACONCUR-174` .. `ACONCUR-179`, `ACONCUR-184` .. `ACONCUR-196` | All 14 files in `tests/conformance/p11/e11_1_concurrency/` |
| `REQ-CONC-016`, `REQ-CONC-018`, `REQ-CONC-085` .. `REQ-CONC-087`, `REQ-CONC-089`, `REQ-CONC-094`, `REQ-CONC-158` .. `REQ-CONC-164`, `REQ-CONC-176`, `REQ-CONC-181` .. `REQ-CONC-183`, `REQ-CONC-192`, `REQ-CONC-193`, `REQ-CONC-197`, `REQ-CONC-202` .. `REQ-CONC-207` | All 14 files in `tests/conformance/p11/e11_1_concurrency/` |
