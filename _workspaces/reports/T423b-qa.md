# T423b — QA report

## Round 0

### Scope and set-up
- Snapshot `build-snap-T423b` (HEAD 01ab1654 + this task's change set, refreshed after my tests were added: 44 files). Bootstrap/axiomc chain already built in the snapshot (`cmake --build build`: "ninja: no work to do", no warnings); axiomc2 is the compiler under test. Only `std/sys/windows/fiber.ax` and `tests/std/fiber/**` changed (no compiler, no `thread.ax`, no `tools/`, no shared files).
- `taskctl.py changes T423b`: no REFUSED line; all 33 files of the report's `## Files changed` are staged, no entry inside another task's paths. No selfhost bundle listed. `grep -rn "native-after: T423b" tests` is empty. `python tests/std/fiber/gen_tests.py --check` in the snapshot: `OK fiber bundles match live std/fiber`. No other bundle under `tests/` embeds `module std.sys.windows.fiber` (grep), so the generator covers every bundle that embeds the changed file.

### 1. Mechanism review (std/sys/windows/fiber.ax, ExitProcess hook)
- **Hook in front of the IAT entry and chaining with thread.ax, both orders.** The fiber installer first calls `__ax_host_thread_current_id()` (which runs `win_rt_get` -> `win_install_exit_hook`, thread.ax patches only IAT entries still equal to kernel32 `ExitProcess`), then patches by name via the ILT. So the order is always IAT -> fiber hook -> thread hook -> kernel32. The reverse order cannot occur: the thread hook is installed (once, at runtime creation) before the fiber hook can exist; and if the thread runtime cannot be created the fiber hook chains straight to kernel32 (`exit_hook_prev` = real entry). Verified by tests: a panic in a fiber on a spawned thread joins `Ok`, and a plain panic on a spawned thread (same process, hook installed) still joins `Err` (np_spawned_thread, qa_np_thread_first).
- **Is the ILT slot read after binding?** Both Axiom linkers (axiom0 `link/pe/linker.c` and `compiler/link/import.ax`) emit separate ILT and IAT in the writable `.idata`; no bound-import directory and no delay-load descriptor are emitted. The Windows loader reads the ILT only while snapping imports at load; it never reads it again for an already-loaded EXE, and `GetProcAddress` does not consult the EXE's tables. The stored value has bit 63 set, so any name-scanning installer treats it as an ordinal import and skips it (no dereference). Sound for the images Axiom produces. Residual risk (note, not a FAIL): external tools (dumpbin/debuggers/AV heuristics) see an odd ILT entry, and a future linker change that merges ILT and IAT, adds delay-load, or emits bound imports would need the hook revisited. Recorded as a follow-up.
- **Idempotent / no self-loop.** Per-thread `@thread_local` checked flag, plus `cur != hook_addr` before patching, plus the ILT flag check; `exit_hook_prev` returns 0 when no flagged entry exists and the hook guards `prev != hook_addr`, then falls back to a direct kernel32 call (never through the IAT). Racing first resumes: every installer writes the same two values in the order ILT then IAT; I enumerated the interleavings (a loser either reads the flagged ILT entry and skips, or reads the already hooked IAT entry and skips, or writes identical values). Live evidence: `qa_np_thread_first` (4 threads whose first fiber resume races, main thread had never resumed a fiber): 60 consecutive native runs of the exe, 60 x `OK qa_np_thread_first 801 802 803 804 -1 2`, rc=0; `np_spawned_thread` 30/30.
- **Per-thread safety.** `FIBER_CUR` is thread-local; the hook switches to `caller_fiber` of the slot running on the calling thread. A fiber panic on thread B cannot be caught by thread A. First resume on a spawned thread works (qa_np_thread_first).
- Dead-end noted by the engineer is accurate: process-wide `static mut` is rejected in bootstrap typeck, so image storage is the only way without touching the compiler; the follow-up it files is reasonable.

### 2. Behaviour (native, interp identical output)
- panic in fiber -> `resume` returns 2 (`Panicked`), message on stderr (`panic: explicit panic`, checked by running the native exe of np_main_thread: stderr shows it, stdout `OK np_main_thread 0 2 0 1010 0 1030 1040`, exit 0), later resume of the handle -> `-4` and `fiber_destroy` succeeds once then `-4` (np_host_contract), panic after yields (np_after_yields), nested panic returns 2 to the direct resumer only (np_nested), scheduler (np_scheduler), resume-after-panic -> exit 101 (np_resume_after_panic), panic outside a fiber -> exit 101 on main (qa_np_plain_after), join `Err` on a spawned thread (np_spawned_thread, qa_np_thread_first).
- Locals of a panicked fiber are not dropped (qa_np_drop_not_run: count 0 after panic and handle drop, 1 after a normally completing fiber; interp and native agree).

### 3. Known limitation: explicit `ExitProcess(101)` inside a fiber
Confirmed by hand (built `ex101.exe` from `qa_np_exit_passthrough` with `ExitProcess(101u32)`): the exit is contained as a panic (the program printed `panicked`, `in fiber`, `panicked`, `not reached` and exited 0). Documented in the report ("Known limitation") and in the source comment (`PANIC_EXIT_CODE ... the only exit the fiber hook contains`); the same limitation exists for the thread hook. Acceptable, recorded as a follow-up. Other exit codes pass through (qa_np_exit_passthrough: exit 3).

### 4. Evidence and mutation
- Mutation (snapshot only): `np_main_thread.ax` expected `.. 1040` -> `.. 1041`: FAIL in interp, native and native-O1 (`stdout differs at byte 39`, expected `1041`, actual `1040`). Restored (`cp` from backup).
- Pre-fix compiler/std: replaced snapshot `std/sys/windows/fiber.ax` with `git show HEAD:...`, regenerated bundles (`gen_tests.py`), ran `axtest --filter native_panic --no-cache -j 2`: `TOTAL 35 PASS 11 FAIL 24` — every native and native-O1 leg of all 12 native_panic tests fails (`interp exit 0, native exit 101; stderr: panic: explicit panic`; for the 101-expecting ones stdout differs: nothing printed). Restored the task's fiber.ax and regenerated: `gen_tests.py --check` OK and `diff` of fiber.ax against the main tree is empty.
- Native-evidence (step 4a): every native_panic test checks an exact `stdout:`, plus `exit:` 101 / 3 where relevant; interp and native run the same file and the runner's agreement check passes (WEAK-NATIVE 0 for the task's own tests).

### 5. Gate runs (all inside the snapshot, `-j 2`)
- `python tools/taskgate.py --task T423b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` (log `_workspaces/T423b_qa_taskgate.log`): exit 0, `TOTAL 161 PASS 155 FAIL 0 SKIP 0 XFAIL 6`, BASELINE OK, archcheck clean (232 files, 0 violations), failing ids none, CACHE mismatch none, WEAK-NATIVE 3 in the run / 0 in the task's own or changed tests. XFAIL 6 are the pre-existing `std/fiber/*_xfail` ids already in the affected set, not task tests.
  - Affected-set derivation (as printed): own tests (13 ids: all `tests/std/fiber/**` changed files + new `native_panic/*`), affected = `std/fiber/*` (gen_tests.py in the directory) + 17 `driver/dep_file/*` tests whose `cache-inputs` name `std/sys/windows/fiber.ax`; smoke 31 ids (every top-level group, plus Xin chao run test `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`, archcheck). The 10 unmatched `.axsrc` are generator inputs, not tests. No UNRESOLVED/MAP-NOTE/DEFERRED.
- `--filter std/thread --no-cache`: TOTAL 18 PASS 18. `--filter std/async --no-cache`: TOTAL 96 PASS 96. `--filter std/fiber --no-cache`: TOTAL 94 PASS 88 FAIL 0 XFAIL 6. `--filter panic --no-cache`: TOTAL 559 PASS 559 FAIL 0. WEAK-NATIVE 0 in all.
- No timeouts occurred; no leftover test processes (all runs finished normally).

### 6. Spec/scope checks
- Behaviour matches SPEC-34 AXS-EXEC-054/055.5 (resume returns 2, out 0) and 053.2 (no drop of the abandoned frames). No diagnostics added, no `BOOTSTRAP-SHORTCUT`, nothing under `bootstrap/axiom0`, no edit of a shared file (axtest.py, CMake, pipeline.c, codes.def). The task listed thread.ax/mod.ax as lockable paths but did not need them; reason (about 50 committed bundles embed thread.ax) is sound.
- Mode check: the only mode-restricted test is mine (`qa_np_exit_passthrough`, `modes: native`, reason: direct FFI is native-only, ADR-0002, accepted). Engineer's tests all run `interp native`.

### Findings
None (no FAIL).

### Follow-ups (for the architect, not FAILs)
1. Explicit `ExitProcess(101)`/process exit code 101 inside a fiber is contained as a panic natively (oracle: process exit 101). Same class as the thread hook; consider a dedicated panic exit path/marker in `axiom_panic` so hooks can distinguish a panic from a user exit.
2. Hook state is stored in the EXE's ILT entry (bit 63 set) and the thread runtime pointer in descriptor 0; fragile against a linker change (ILT merged with IAT, bound/delay-load imports, read-only `.idata` is tolerated via VirtualProtect). Replace by process-wide `static mut` once typeck supports it (engineer's follow-up; I agree).
3. Native `std.core.host.exit` is unresolved at link (`undefined symbol '__ax_host_exit'`), found while writing qa_np_exit_passthrough; tests must use direct kernel32 FFI for an exit code. Architect may want a task for the `exit` intrinsic natively.

## Files changed
- tests/std/fiber/gen_tests.py
- tests/std/fiber/native_panic/qa_np_thread_first.ax
- tests/std/fiber/native_panic/qa_np_three_deep.ax
- tests/std/fiber/native_panic/qa_np_drop_not_run.ax
- tests/std/fiber/native_panic/qa_np_exit_passthrough.ax
- tests/std/fiber/native_panic/qa_np_plain_after.ax
- tests/std/fiber/native_panic/src/qa_np_thread_first.axsrc
- tests/std/fiber/native_panic/src/qa_np_three_deep.axsrc
- tests/std/fiber/native_panic/src/qa_np_drop_not_run.axsrc
- tests/std/fiber/native_panic/src/qa_np_exit_passthrough.axsrc
- tests/std/fiber/native_panic/src/qa_np_plain_after.axsrc

(`tests/std/fiber/gen_tests.py` is also in the engineer's list; my edit adds five names, the `NATIVE_ONLY` set and two `EXPECT_EXIT` entries.)

VERDICT: PASS round=0
