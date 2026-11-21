# T423b — Native fiber panic containment (Windows x64) — report

## Summary
A panic raised on a native Win32 fiber stack now makes `host.fiber_resume` return `2` (`FiberState.Panicked`) and writes
`0` to `*out_val`, as the oracle does (SPEC-34 AXS-EXEC-054, AXS-EXEC-055.5). The process no longer ends. The panic message is still
written to stderr. The panicking fiber's live locals are not dropped (AXS-EXEC-053.2). After the panic, `fiber_resume` of that handle
returns `-4` and `fiber_destroy` succeeds once and releases the stack. A panic outside any fiber behaves as before: on the main thread
the process exits with 101, and on a spawned thread `join` returns `Err`. `// native-after: T423b` is gone
(`grep -rn "native-after: T423b" tests` prints nothing).

## Design (std/sys/windows/fiber.ax only)
- The native panic path is the linker stub `axiom_panic`. It writes the message to stderr and calls `ExitProcess(101)` through the
  IAT. The first `fiber_resume` on each thread calls `win_fiber_install_exit_hook()`, which works as follows:
  1. It calls `__ax_host_thread_current_id()` so that the thread runtime's ExitProcess hook (thread.ax) is installed **first**.
     thread.ax only patches IAT entries that still hold the real kernel32 address, so this order keeps both hooks chained.
  2. It finds the `ExitProcess` IAT entry **by name** through the import lookup table (ILT). This works whatever address the entry
     holds now.
  3. It writes `ILT_HOOKED_FLAG | previous entry` into the parallel ILT entry, then writes `win_fiber_exit_hook` into the IAT entry.
- `win_fiber_exit_hook(code)`:
  - If `code == 101` and the thread-local `FIBER_CUR` is a running user fiber, it sets the slot status to `Panicked` (3) and
    `yield_or_ret` to 0, then calls `SwitchToFiber(caller_fiber)`. The resumer's `fiber_resume` sees `Panicked` and returns 2.
  - Otherwise it chains to the previous entry, which it reads back from the flagged ILT entry. That entry is either the thread
    hook (spawned-thread `join` returns `Err`) or the real ExitProcess. A direct kernel32 `GetProcAddress` call is the fallback.
- `fiber_destroy` already accepts any status other than Running, so a panicked fiber is destroyed like a completed one. std/fiber/mod.ax
  already mapped `rc == 2` to `Panicked` and calls `finish_host`, so it needed no change.

### Decision: process-wide state is kept in the ILT, not in a `static`
I first wrote two non-thread-local `static mut` items. They fail in the bootstrap typeck with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`:
only `@thread_local` statics are supported (compiler/types/typeck.ax:3000 and 12576 accept `HIR_ITEM_STATIC` only when `is_tls`).
The previous ExitProcess entry must be visible to every thread, so it is stored in the image instead, the same way thread.ax keeps
its runtime pointer in the first import descriptor.
- The loader no longer reads the ILT entry beside the hooked IAT entry once the image is bound.
- That entry is in the writable `.idata` section of both axiomc and axiom0 images.
- Bit 63 is the PE ordinal flag. A concurrent installer that scans names therefore skips the entry instead of dereferencing it.
- Every installer writes the same values in the same order (ILT, then IAT), so racing first resumes on several threads are
  harmless.

The per-thread "already checked" flag is `@thread_local`.

### Why thread.ax is not changed
thread.ax is in this task's paths, but its source is copied into about 50 committed bundles under `tests/std/{async,sync,channel}` and
`tests/conformance/p11` that are not in the paths. Changing it would leave those bundles out of date (their `--check` would fail).
All the work is done in fiber.ax, whose only bundle generator is `tests/std/fiber/gen_tests.py`.

## Tests
- `tests/std/fiber/gen_tests.py`:
  - `NATIVE_AFTER` is now empty, so `fiber_panic_contained` runs in interp and native.
  - Names of the form `<dir>/<test>` are supported (source at `<dir>/src/<test>.axsrc`, bundle at `<dir>/<test>.ax`).
  - The `covers:` line can differ per test; native_panic tests use `REQ-CONC-189, REQ-TST-072`.
  - All fiber bundles were regenerated, because each one embeds fiber.ax.
- New tests in `tests/std/fiber/native_panic/` (`modes: interp native`, exact stdout and exit code):

| Test | What it checks |
|---|---|
| `np_main_thread` | A main-thread fiber panics; the other fibers keep running, a new fiber runs after the panic; exit 0 |
| `np_nested` | Fiber A resumes fiber B, which panics; only A sees Panicked, and A then yields and completes normally |
| `np_spawned_thread` | A main fiber panics first. A fiber on a spawned thread panics and the thread joins `Ok(1007200)`. A plain (non-fiber) spawned-thread panic still joins `Err`, which shows the chain to the thread hook works |
| `np_after_yields` | 4 yields (sum 110), then Panicked on the 5th resume |
| `np_scheduler` | `FiberScheduler.run` with one panicking fiber completes the others (log `10 90 30 11 31 12`); the scheduler can be reused |
| `np_resume_after_panic` | Resuming the panicked fiber panics deterministically: stdout `panicked\nbefore\n`, exit 101 |
| `np_host_contract` | Raw host API: `fiber_resume` → 2 with `out=0`; then resume → -4, destroy → 0, destroy → -4; another fiber is unaffected |

## Results (in `build-snap-T423b`; Release clang Stage-0 built by build_axiomc.py; axiomc2 sha256 87f4350e…, fixed point OK, STAGE0-GUARD OK; log `_workspaces/T423b_build.log`)
- `axtest --filter std/fiber --no-cache -j 2`: TOTAL 80, PASS 74, FAIL 0, XFAIL 6, WEAK-NATIVE 0. Every native_panic test and
  `fiber_panic_contained` pass in interp, native and native-O1 with identical output.
- Mutation check: changing the expected stdout of `np_main_thread` (1040 → 1041) makes it FAIL in native and native-O1 (and interp).
  The expectation was then restored and `gen_tests.py --check` is OK.
- `--filter std/thread`: 18/18 pass. `--filter std/async`: 96/96 pass. `--filter panic`: 545/545 pass. WEAK-NATIVE 0 in all three.
- Task gate: `python tools/taskgate.py --task T423b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
  (log `_workspaces/T423b_taskgate.log`):
  - exit 0, `TOTAL 146 PASS 140 FAIL 0 SKIP 0 XFAIL 6`
  - BASELINE OK; archcheck clean (232 files)
  - WEAK-NATIVE 3 in the run, 0 in the task's own or changed tests

## Notes
- `taskctl snapshot` copies only files under `paths:`, so the snapshot first had the old fiber bundles (outside paths). I ran
  `gen_tests.py` inside the snapshot, and checked with `diff -r` that the snapshot's `tests/std/fiber` and fiber.ax match the main tree.
- Known limitation (same as the thread hook): an explicit `ExitProcess(101)` / process exit with code 101 called **inside a fiber** is
  treated as a panic and contained.

## Follow-ups
- Compiler feature gap: a non-`@thread_local` `static mut` item (for example `static mut X: u32 = 0u32;`) is rejected by typeck with
  `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (compiler/types/typeck.ax lines ~3000 and ~12576). Process-wide mutable statics (SPEC static items)
  would let both fiber.ax and thread.ax drop their image-stash workarounds. This is for the architect to file (semantics/backend).

## Files changed
- std/sys/windows/fiber.ax
- tests/std/fiber/gen_tests.py
- tests/std/fiber/fiber_panic_contained.ax
- tests/std/fiber/fiber_affinity.ax
- tests/std/fiber/fiber_deep_stack.ax
- tests/std/fiber/fiber_drop_cleanup.ax
- tests/std/fiber/fiber_host_contract.ax
- tests/std/fiber/fiber_nested.ax
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
- tests/std/fiber/native_panic/np_main_thread.ax
- tests/std/fiber/native_panic/np_nested.ax
- tests/std/fiber/native_panic/np_spawned_thread.ax
- tests/std/fiber/native_panic/np_after_yields.ax
- tests/std/fiber/native_panic/np_scheduler.ax
- tests/std/fiber/native_panic/np_resume_after_panic.ax
- tests/std/fiber/native_panic/np_host_contract.ax
- tests/std/fiber/native_panic/src/np_main_thread.axsrc
- tests/std/fiber/native_panic/src/np_nested.axsrc
- tests/std/fiber/native_panic/src/np_spawned_thread.axsrc
- tests/std/fiber/native_panic/src/np_after_yields.axsrc
- tests/std/fiber/native_panic/src/np_scheduler.axsrc
- tests/std/fiber/native_panic/src/np_resume_after_panic.axsrc
- tests/std/fiber/native_panic/src/np_host_contract.axsrc

STATUS: COMPLETE round=0
