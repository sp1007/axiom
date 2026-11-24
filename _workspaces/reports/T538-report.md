# T538 — Native panic hook slot (replaces the ExitProcess IAT/ILT hooks) — report

## Summary
Native panics now have their own path. `axiom_panic` writes the message and then calls the process-wide panic hook if one is
registered, before `ExitProcess(101)`. The fiber and thread runtimes register their containment routine through a
linker-provided setter. They no longer patch the `ExitProcess` IAT entry. They no longer stash state in the import lookup
table (ILT) or in import descriptor 0.

A user `ExitProcess(101)` / exit 101 on a fiber or on a spawned thread now ends the process with 101; before, it was contained
as if it were a panic. Panics are still contained exactly as before:
- a panic on a running fiber makes `fiber_resume` return 2 (Panicked);
- a panic on a spawned thread makes `join` return `Err`;
- a panic on the main thread exits with 101.

Interp behaviour is unchanged: the oracle never runs these std modules.

## Design

### Linker / runtime stubs (`compiler/link/import.ax`, `compiler/link/linker.ax`)
New pieces:
- **`AXIOM_PANIC_HOOK_CODE`** (96 bytes): the hooked `axiom_panic` stub. It is the old stub plus
  `mov rax,[rip+__ax_panic_hook]; test rax,rax; jz; mov rcx,rbx; mov rdx,rsi; call rax`, placed before `mov ecx,101; call [ExitProcess]`.
  - Hook ABI: Win64, `hook(msg_ptr: *const u8, msg_len: usize)` (the return value is ignored). RSP is 16-aligned and the
    32-byte shadow space is inside the existing 0x48 frame.
  - The hook may return, which falls through to exit 101. It may also not return (`SwitchToFiber`, `ExitThread`).
  - The byte layout and relocation offsets are documented next to the table.
- **`AXIOM_PANIC_HOOK_SET_CODE`** (11 bytes): `__ax_panic_hook_set(hook) -> previous`, implemented as
  `mov rax,rcx; xchg [rip+__ax_panic_hook],rax; ret`. The exchange is atomic.
- **`linker_emit_panic_hook_slot(ctx)`**: called in all four finalize paths (EXE, EXE v2, DLL, DLL v2). It runs after inputs,
  archive members and DLL stubs are loaded, and before `<dll>$sym` rewriting. If any relocation names the setter
  (`__ax_panic_hook_set` or `<dll>$__ax_panic_hook_set`), it:
  - defines `__ax_panic_hook` as a zero qword in `.data`;
  - appends the hooked stub and points `axiom_panic` at it. This happens only if `axiom_panic` is the linker's own hook-free
    stub, which is detected by its bytes. The old 64 bytes stay as unreferenced dead code;
  - emits the setter stub.
- **Decision: images without a hook are byte-identical to before.** `linker_emit_runtime_stubs` and
  `linker_emit_dll_runtime_stubs` still emit the original 64-byte hook-free `AXIOM_PANIC_CODE`.
  - Reason: `tests/selfhost/link/qa_pe_headers_and_linker_diff` compares linked EXEs byte for byte against axiom0-linked
    goldens (the stub section is pinned at 343 bytes with 14 relocations). An unconditional stub change broke both of its
    sub-tests in my first run.
  - axiom0 is frozen and the goldens are outside the task's paths.
  - Only programs that link the std fiber/thread runtime get the hooked stub and the `.data` slot.
- **`--rt-obj` runtime object** (`pe_build_runtime_coff_obj`), which is used for gcc/ld cross-linking (INV-WLIB-003):
  - It always carries the hooked stub at offset 96. `__ax_host_print` moves to 192, `__ax_host_print_int` to 256, and
    `__ax_panic_hook_set` is at 384.
  - `.data` is now 8-aligned and holds `_tls_index` at 0 and `__ax_panic_hook` at 8.
- A first version also defined `__imp___ax_panic_hook_set` for `--emit=obj` thunks. Inspecting the objects showed that they
  reference the bare symbol, so nothing reached that code. It was removed before the final build and gate.

### Accessing the slot from Axiom (decision)
Axiom has no `extern` data declarations, so the task's fallback applies: a tiny host-provided setter.
- `std/sys/windows/thread.ax` declares `extern "C" { fn __ax_panic_hook_set(hook: usize) -> usize; }`. An extern without `@link` is
  named `KERNEL32.dll$__ax_panic_hook_set`, and the linker's existing `$`-rewrite binds it to the stub.
- In `--emit=obj` objects the call is bare `__ax_panic_hook_set`, which the runtime object defines.
- Verified with gcc/ld: `gcc -nostdlib ... axiom_rt.obj -lkernel32 -lsynchronization` runs the thread bundle with the same
  output and exit code (101).

### std (`std/sys/windows/thread.ax`, `std/sys/windows/fiber.ax`)
**thread.ax**
- The runtime pointer is now a process-wide `static mut WIN_THREAD_RT` (T537).
- Deleted: `pe_first_import_desc`, the descriptor-0 stash, `win_exit_process_hook`, `win_install_exit_hook`,
  `fn_exit_to_addr` / `addr_to_fn_exit`, the `orig_exit_process` field, and the `ExitProcess`, `GetModuleHandleA`,
  `GetProcAddress` and `VirtualProtect` imports.
- New `pub win_thread_panic_contain()`: on a live spawned thread of the runtime, it marks the slot panicked and calls
  `ExitThread(101)`, as the old hook did. Otherwise it returns.
- `win_rt_get` registers `win_thread_panic_hook` only when no hook is set yet. If the setter returns a non-zero previous hook,
  that hook is put back.
- New helpers: `win_panic_hook_set` and `win_panic_hook_to_addr`.

**fiber.ax**
- Deleted: `ILT_HOOKED_FLAG`, the ExitProcess/kernel32 name tables, `exe_first_import_desc`, `exit_hook_prev`,
  `win_fiber_exit_hook`, `win_fiber_install_exit_hook`, the unused imports, and `PANIC_EXIT_CODE`.
- New `win_fiber_panic_hook`:
  - a running fiber is marked Panicked and the hook calls `SwitchToFiber(caller)`;
  - otherwise it calls `win_thread_panic_contain()` and returns.
- It is registered once per process (process-wide `static mut FIBER_PANIC_HOOK_SET`). Registration first calls
  `__ax_host_thread_current_id()`, so the thread runtime has registered first and never overwrites the fiber hook.
  The fiber hook covers the thread case too, so the two hooks do not need to be chained.

`grep -n "ILT_HOOKED_FLAG\|ExitProcess" std/sys/windows/fiber.ax std/sys/windows/thread.ax` prints nothing.

## Tests
- `tests/std/fiber/native_panic/exit101_passthrough.ax` (source in `src/`, generated by `gen_tests.py`, native-only because it uses
  direct FFI):
  - a contained fiber panic prints `panicked`;
  - then `ExitProcess(101)` inside a fiber ends the process: stdout `panicked\nin fiber\n`, exit 101.
- `tests/std/thread/native_panic_hook/` has its own generator (`gen_tests.py` and `check_bundles.test`), which embeds the live
  thread.ax:
  - `nph_exit101_thread` (native): a spawned-thread panic joins `Err`, then `ExitProcess(101)` on a spawned thread ends the
    process with 101. Stdout `contained -1\n`.
  - `nph_panic_contained` (interp and native): two contained spawned-thread panics and one healthy thread, then a main-thread
    panic exits 101.
- `tests/run/panic_hook_slot/`:
  - `no_hook_panic.ax` (interp and native): no fiber or thread; exit 101, `stderr-contains: panic: explicit panic`.
  - `hook_registered_main_panic.ax` (interp and native, real std): the hook is registered; a main-thread panic still exits 101
    with the message.
  - `panic_hook_link.test` with `panic_hook_link_oracle.py` checks:
    - the rt obj symbols, their sections and relocations, with no `(bad)` from objdump;
    - a hook-free EXE has no `.data` section and exits 101;
    - a thread EXE has `.data` and exits 101 after the contained panic;
    - the gcc/ld cross-link of the thread bundle with `axiom_rt.obj` behaves the same;
    - a panic on a thread spawned inside an Axiom DLL is contained (C host, `probe=77`).
- All fiber bundles were regenerated by `tests/std/fiber/gen_tests.py`. Two changes:
  - new test entry;
  - the stale comment in `qa_np_exit_passthrough.axsrc` was updated.
- The existing native_panic and thread-panic tests are unchanged and pass.

## Results (final code, in `build-snap-T538`, Release clang Stage-0, `build_axiomc.py --stage 3`)
- Build: FIXED-POINT (O1) OK, axiomc2 == axiomc3, sha256 cb405fc4…; STAGE0-GUARD OK. Log: `_workspaces/T538_build3.log`.
- Freshness: `gen_tests.py --check` is OK in the snapshot for the nine widened directories, `tests/std/fiber` and
  `tests/std/thread/native_panic_hook`.
- Task gate (`python tools/taskgate.py --task T538 --compiler build/axiomc2.exe --build-dir build --exclude-requires
  axiom0-internal -j 2`, log `_workspaces/T538_taskgate3.log`): `TASKGATE T538 exit=0`, `TOTAL 486 PASS 482 FAIL 0 SKIP 4`,
  BASELINE OK, archcheck clean (232 files), smoke-check OK, WEAK-NATIVE 3 in the run / 0 in the task's own or changed tests.
- `axtest --no-cache -j 2` over `std/fiber std/thread std/async std/sync std/channel conformance/p11 conformance/p18
  perf/p11_executor run/concurrency/tls interp_big_args link/ obj/ panic`: `TOTAL 1118 PASS 1114 FAIL 0 SKIP 4`, WEAK-NATIVE 0
  (log `_workspaces/T538_suites3.log`). This includes `--filter panic` and the `selfhost/link` byte-diff test.
- Mutations (snapshot only, restored afterwards):
  - Thread-hook registration disabled: `nph_exit101_thread` and `nph_panic_contained` FAIL in native and native-O1. This was
    run on the previous build; the std sources are unchanged since.
  - DLL expectation `probe=77` changed to 78: `panic_hook_link.test` FAILs with the observed `probe=77`.
- Earlier failed gate: one run on the final compiler exited 1 on `panic_hook_link.test` only. The cause was a syntax error in the
  oracle's new DLL section (wrongly escaped newlines). Only the oracle was fixed, and the gate and suites above were run after it.

## Notes
- **Out-of-path bundle generators (unblocked).** The orchestrator widened `paths:` with the nine generator directories that
  embed `std/sys/windows/thread.ax`. Their bundles were regenerated in the main tree with each directory's own
  `gen_tests.py`, with no hand edits. That wrote 69 `.ax` files, listed below.
  - The nine directories: `tests/conformance/p11/e11_3_threads_sync`, `tests/conformance/p11/e11_5_executors`,
    `tests/perf/p11_executor`, `tests/std/async/{executor,structured,waker,waker_qa}`, `tests/std/channel` and `tests/std/sync`.
  - Every `gen_tests.py --check` passes in the main tree and in the refreshed snapshot.
- Hand-copied (not generated) thread.ax copies still hold the old IAT-hook code:
  - `tests/std/thread/{builder_and_detach,futex_sleep_yield_cancel,panic_containment,qa_thread_seam_and_reuse,scoped_threads,spawn_join_basic}.ax`
  - `tests/run/concurrency/tls/*` (6 files)
  - `tests/run/interp_big_args` (1 file)

  They still pass: a program that never references the setter keeps the hook-free stub, which calls ExitProcess through the
  IAT, so their own hook still works. Refreshing them is an optional follow-up.
  Until then, `tests/std/thread/*.ax` exercise the OLD containment code, so their PASS is not evidence for the new hook.
  The evidence is `native_panic_hook`, `native_panic`, `hook_registered_main_panic` and the regenerated bundles.
- `--emit=obj` objects do not carry std host-intrinsic bodies (heap, thread spawn). This was already the case before this
  task, so the cross-link check uses the native_panic_hook bundle, which embeds thread.ax as a user module.

## Files changed
- compiler/link/import.ax
- compiler/link/linker.ax
- std/sys/windows/fiber.ax
- std/sys/windows/thread.ax
- tests/std/fiber/gen_tests.py
- tests/std/fiber/fiber_affinity.ax
- tests/std/fiber/fiber_deep_stack.ax
- tests/std/fiber/fiber_drop_cleanup.ax
- tests/std/fiber/fiber_host_contract.ax
- tests/std/fiber/fiber_nested.ax
- tests/std/fiber/fiber_panic_contained.ax
- tests/std/fiber/fiber_ping_pong.ax
- tests/std/fiber/fiber_scheduler_rr.ax
- tests/std/fiber/fiber_stack_sizes.ax
- tests/std/fiber/qa_fiber_drop.ax
- tests/std/fiber/qa_fiber_foreign_collision.ax
- tests/std/fiber/qa_fiber_handle_reuse.ax
- tests/std/fiber/qa_fiber_many.ax
- tests/std/fiber/qa_fiber_nested3.ax
- tests/std/fiber/qa_fiber_resume_finished.ax
- tests/std/fiber/qa_fiber_values.ax
- tests/std/fiber/qa_fiber_yield_outside.ax
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
- tests/std/fiber/native_panic/exit101_passthrough.ax
- tests/std/fiber/native_panic/src/exit101_passthrough.axsrc
- tests/std/fiber/native_panic/src/qa_np_exit_passthrough.axsrc
- tests/std/thread/native_panic_hook/gen_tests.py
- tests/std/thread/native_panic_hook/check_bundles.test
- tests/std/thread/native_panic_hook/nph_exit101_thread.ax
- tests/std/thread/native_panic_hook/nph_panic_contained.ax
- tests/std/thread/native_panic_hook/src/nph_exit101_thread.axsrc
- tests/std/thread/native_panic_hook/src/nph_panic_contained.axsrc
- tests/run/panic_hook_slot/no_hook_panic.ax
- tests/run/panic_hook_slot/hook_registered_main_panic.ax
- tests/run/panic_hook_slot/panic_hook_link.test
- tests/run/panic_hook_slot/panic_hook_link_oracle.py
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
- tests/std/sync/arc_mutex_threads.ax
- tests/std/sync/barrier_rendezvous.ax
- tests/std/sync/big_struct_sync.ax
- tests/std/sync/condvar_signaling.ax
- tests/std/sync/once_cell_init.ax
- tests/std/sync/rwlock_readers_writer.ax

STATUS: COMPLETE round=0
