STATUS: COMPLETE round=0

# T404 — E11.1: Concurrency & Data-Race Conformance Suite

## Summary

Implemented the Phase 11 Epic E11.1 concurrency and data-race conformance suite in `tests/conformance/p11/e11_1_concurrency/` against `spec/SPEC-30-concurrency.md`:

1. **Negative `ui` Conformance Tests (`Send != Share`, `!Send`, `!Share`, Escaping Views/Guards, Data-Race Conflicts, Atomics, Statics)**:
   - `tests/conformance/p11/e11_1_concurrency/ui_send_not_equal_share.ax`: Verifies `Send != Share` orthogonality (`OwnedHandle: Send + !Share` satisfies `Send` and fails `Share` with `AX_CONC_NOT_SHARE`; `ThreadPinned: !Send + Share` satisfies `Share` and fails `Send` with `AX_CONC_NOT_SEND`), `view<T>` marker rules (`view<T>: Send` and `view<T>: Share` iff `T: Share`), `mut_view<T>` marker rules (`mut_view<T>: Send` iff `T: Send`, unconditionally `!Share`), synchronization wrapper bounds (`Arc<T>`, `Mutex<T>`, `RwLock<T>`), structural derivation across structs/enums/tuples/arrays, generic boundary checks (`AXS-CONC-018`), `unsafe`-only positive `Send`/`Share` impls (`AX_CONC_SAFE_SEND_SHARE_IMPL`), and conflicting positive + negative impl rejection (`AX_TRAIT_OVERLAP`).
   - `tests/conformance/p11/e11_1_concurrency/ui_non_send_across_spawn.ax`: Verifies that `*mut T`, `*const T`, `Rc`, `LocalRc`, FFI opaque handles wrapping raw pointers (`AXS-CONC-038`), and explicit `!Send` types are rejected when captured across `spawn` (`AX_CONC_CAPTURE_NOT_SEND`) or returned from `spawn` (`AX_CONC_NOT_SEND`).
   - `tests/conformance/p11/e11_1_concurrency/ui_spawn_use_after_move.ax`: Verifies that owned `!Copy` bindings captured by `spawn` or `spawn_local` move into the spawned closure and any subsequent read or second `spawn` capture in the parent scope without re-initialization is rejected with `AX_MOVE_USE_AFTER_MOVE` (`AXS-CONC-022`, `AXS-CONC-025`).
   - `tests/conformance/p11/e11_1_concurrency/ui_non_share_interior_mut_across_threads.ax`: Verifies that `view<T>` of `!Share` interior-mutable or thread-pinned types (`Cell`, `RefCell`, `UnsafeCell`, `CellBox`, `Rc`, `ThreadLocal`, raw-pointer wrappers, `Arc<Cell>`, and explicit `impl !Share`) is rejected across `par_join`, `spawn_scoped`, and `share_view` (`AX_CONC_VIEW_NOT_SHARE`).
   - `tests/conformance/p11/e11_1_concurrency/ui_escaping_view_and_guard_captures.ax`: Verifies that non-static `view<T>`, `mut_view<T>`, implicit mutable stack borrows, and returned stack views are rejected across `spawn` and `spawn_local` (`AX_CONC_ESCAPING_VIEW`).
   - `tests/conformance/p11/e11_1_concurrency/ui_lock_guard_escape.ax`: Verifies that lock guards (`MutexGuard`, `RwLockReadGuard`, `RwLockWriteGuard`) and guard-derived views cannot be returned from a function, escape an inner lexical block scope, or cross `spawn_scoped` / `par_join` boundaries (`AX_CONC_GUARD_ESCAPE`), and that unsynchronized `mut_view` into `AtomicI32` is rejected (`AX_CONC_ATOMIC_MUT_VIEW`).
   - `tests/conformance/p11/e11_1_concurrency/ui_read_write_and_write_write_races.ax`: Verifies compile-time rejection (`AX_CONC_SHARED_MUT`) of concurrent `WRITE/WRITE`, `WRITE/READ`, and `READ/WRITE` conflicts across scalars, struct fields (`p.a`), whole struct vs. field (`CONTAINS`), tuple fields (`.0`), overlapping constant slice sub-ranges (`[0..3]` vs. `[2..4]`), dynamic array indices (`arr[i]` vs. `arr[j]`, `UNKNOWN` disjointness), dynamic slice ranges (`arr[0..i]` vs. `arr[j..4]`), `Arc<T>` without `Mutex`, and `unsafe` re-entry where safe `mut_view`/`view` capabilities are re-established from raw pointers (`AXS-CONC-037`, `ACONCUR-178`).
   - `tests/conformance/p11/e11_1_concurrency/ui_invalid_atomic_contracts.ax`: Verifies compile-time rejection of non-atomic payload types (`AX_CONC_INVALID_ATOMIC_TYPE`), `@repr(packed)` and `@align(2)` under-aligned atomics (`AX_CONC_INVALID_ATOMIC_ALIGNMENT`), non-atomic `mut_view` / private field access (`AX_CONC_ATOMIC_MUT_VIEW`), and invalid memory orderings on `load`, `store`, `compare_exchange`, `compare_exchange_weak`, `fence`, and `compiler_fence` (`AX_CONC_INVALID_ATOMIC_ORDERING`).
   - `tests/conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax`: Verifies compile-time rejection of process-global immutable `static` items with `!Share` types (`AX_CONC_UNSYNC_STATIC`), while allowing `@thread_local` statics without `Share` (`AXS-CONC-004`, `AXS-CONC-034`), rejecting safe read/write access to `static mut` (`AX_CONC_UNSYNC_STATIC`), and rejecting concurrent `mut_view` races on `static mut` inside `unsafe` (`AX_CONC_SHARED_MUT`).

2. **Positive `run` Conformance Tests (`modes: interp native`, checking `interp`, `native` `-O0`, and `native-O1`) & `-O1` MIR Inspection**:
   - `tests/conformance/p11/e11_1_concurrency/run_send_ownership_transfer.ax`: Verifies `Send` ownership transfer across `spawn`, `Copy` capture retention in parent, uncaptured `!Send` locals in enclosing scope (`AXS-CONC-021`), re-initializing a moved variable for a subsequent `spawn`, `Send + !Share` ownership transfer, `!Send` local task execution via `spawn_local`, and cooperative cancellation vs. panic lifecycle state separation (`Spawned -> Running -> Cancelled` vs. `Completed` / `Panicked`, `AXS-CONC-005..007`, `ACONCUR-179`).
   - `tests/conformance/p11/e11_1_concurrency/run_share_concurrent_read_views.ax`: Verifies concurrent `READ/READ` `view<T>` sharing across `par_join` and sibling `spawn_scoped` tasks, structural `Share` derivation, synchronization wrapper marker rules (`Mutex<T>: Send + Share` when `T: Send` even if `T: !Share`), and non-escaping lexical lock guard scopes.
   - `tests/conformance/p11/e11_1_concurrency/run_disjoint_struct_and_slice_mutation.ax`: Verifies parallel `mut_view` mutation of disjoint struct fields (`p.a` vs. `p.b`) with post-join parent read, nested disjoint struct paths (`tree.left.a` vs. `tree.right.b`), 3-way disjoint struct fields, disjoint tuple fields (`.0` vs. `.1`), disjoint constant array indices (`arr[0]` vs. `arr[3]`), non-overlapping constant slice ranges (`ms0[0..2]` vs. `ms0[2..4]`), and symbolic split slices (`ms[..mid]` vs. `ms[mid..]`).
   - `tests/conformance/p11/e11_1_concurrency/run_happens_before_and_domain_contracts.ax`: Verifies `Release`/`Acquire` atomic publication, `fence` and `compiler_fence` barriers, notification (`Relaxed`) vs. publication (`Release`/`Acquire`) distinction (`AXS-CONC-047`), explicit host-device GPU barrier synchronization (`AXS-CONC-050`), cross-process explicit byte serialization (`AXS-CONC-051`), and `@repr(C)` shared-memory contracts (`AXS-CONC-052`).
   - `tests/conformance/p11/e11_1_concurrency/mir_happens_before_and_zero_cost_erasure.ax` & `.test`: Verifies at `-O1` (`inspect --emit=mir-opt -O1`) that `Send`/`Share` bounds are completely erased with zero runtime witness parameters and that `atomic_store Release`, `atomic_fence Acquire`, `atomic_rmw add AcqRel`, `atomic_cmpxchg AcqRel Acquire`, `spin_loop_hint`, `atomic_load Acquire`, and `compiler_fence SeqCst` barriers are preserved in order without store/load hoisting or elimination across synchronization boundaries.

## Files changed

- tests/conformance/p11/e11_1_concurrency/README.md
- tests/conformance/p11/e11_1_concurrency/mir_happens_before_and_zero_cost_erasure.ax
- tests/conformance/p11/e11_1_concurrency/mir_happens_before_and_zero_cost_erasure.test
- tests/conformance/p11/e11_1_concurrency/run_disjoint_struct_and_slice_mutation.ax
- tests/conformance/p11/e11_1_concurrency/run_happens_before_and_domain_contracts.ax
- tests/conformance/p11/e11_1_concurrency/run_send_ownership_transfer.ax
- tests/conformance/p11/e11_1_concurrency/run_share_concurrent_read_views.ax
- tests/conformance/p11/e11_1_concurrency/ui_escaping_view_and_guard_captures.ax
- tests/conformance/p11/e11_1_concurrency/ui_invalid_atomic_contracts.ax
- tests/conformance/p11/e11_1_concurrency/ui_lock_guard_escape.ax
- tests/conformance/p11/e11_1_concurrency/ui_non_send_across_spawn.ax
- tests/conformance/p11/e11_1_concurrency/ui_non_share_interior_mut_across_threads.ax
- tests/conformance/p11/e11_1_concurrency/ui_read_write_and_write_write_races.ax
- tests/conformance/p11/e11_1_concurrency/ui_send_not_equal_share.ax
- tests/conformance/p11/e11_1_concurrency/ui_spawn_use_after_move.ax
- tests/conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T404` -> `snapshot D:\projects\compiler\new lang\build-snap-T404 (refreshed: HEAD a24ca52 + 16 changed, 0 deleted file(s) of T404)`
- `python build-snap-T404/tools/axtest.py -j 1 --root build-snap-T404 --build-dir build-snap-T404/build --compiler build-snap-T404/build/axiomc2.exe conformance/p11/e11_1_concurrency mir/concurrency ui/concurrency run/concurrency run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 79 PASS 79 FAIL 0 SKIP 0 XFAIL 0`
- Native-evidence liveness check (Rule 4a): mutated `// stdout: 735\n` -> `// stdout: 999\n` in `build-snap-T404/tests/conformance/p11/e11_1_concurrency/run_send_ownership_transfer.ax`, confirmed all 3 legs (`[interp]`, `[native]`, `[native-O1]`) failed (`TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0`), and restored snapshot via `taskctl.py snapshot T404`.
- `python tools/archcheck.py` -> `archcheck: 195 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T404` -> `0 REFUSED`

STATUS: COMPLETE round=0
