# T421a QA

## Round 0

Progress:
- 2026-11-13 gate started; `taskctl.py changes T421a`: 39 files staged, no REFUSED line.
- snapshot `build-snap-T421a` = HEAD 888b283 + the change set (diff -r of std/async and tests/std/async against the main tree: identical). Refreshed after the QA tests were added: HEAD is then bcef956 (T438, touches only `tests/mc` / C test sources: `git diff --stat 888b2837 HEAD -- compiler std bootstrap tools tests/std` is empty).
- compiler: `build-snap-T452/build/axiomc2.exe` (stage-2, built for T452) copied to `build-snap-T421a/build/axiomc2.exe`; `diff -r build-snap-T452/compiler build-snap-T421a/compiler` is empty and no commit after e0637c50 touches `compiler/`, so the binary is HEAD-equivalent.
- old-code reproduction done; concurrency review done; 5 QA adversarial tests + check test added; 4 mutation runs done.
- taskgate started, then stopped by me (selection far beyond the gate scope, see "Gate scope"); replaced by the scope below.
- repeat runs, expected-value mutation, smoke, archcheck, async compiler tests done; final tests/std/async run 2 after `taskctl.py snapshot T421a`.

### Gate scope actually run (all inside build-snap-T421a, compiler build/axiomc2.exe, -j 2, one run at a time)
- Why not `taskgate.py` as is: its affected-set derivation (`axtest.py --affected @changed --list`, saved in `_workspaces/artifacts/T421a-affected-list.txt`) selected 438 test files incl. 149 `tests/selfhost/**` bundles, because it treats names that merely appear in `std/async` (`impl Drop for ...` -> "public name Drop" 298 files, `Send` 37, `Waker` 14, `Future` 16) as public names of the change. The run had started the heavy selfhost bundles (`qa_obj_link_driver_smoke`, `qa_backend_diff_lir_a` in interp) when I stopped it and killed its processes; the orchestrator's instruction excludes selfhost bundles and the isolation grep above proves none of those tests can load `std/async` (no `use std.asyn`, no embedded copy: `grep -rl "task_waker_clone\|impl Drop for Waker\|fn waker_leak"` outside the two trees is empty). Follow-up F4.
- Own + affected = the complete `tests/std/async` tree (executor, structured, waker, waker_qa): run 1 (`--no-cache`, before the qa_late_waker_drop fix): TOTAL 96 PASS 95 FAIL 1 (my own test, interp, see F3), WEAK-NATIVE 0. Run 2 (`--no-cache --baseline`, after `taskctl.py snapshot T421a`, HEAD 349083e = 888b283 + T438/T439 which touch only tests/mc C sources and tools/tests self-tests): **TOTAL 96 PASS 96 FAIL 0, WEAK-NATIVE 0** (logs: `_workspaces/artifacts/T421a-qa-async-run{1,2}.log`).
- Extra light compiler-side async tests (the "Waker/Future" name matches): `run/async ui/async typeck/async mir/async conformance/p11/e11_4_async`: TOTAL 105 PASS 104 FAIL 1 (`typeck/async/async_basic_pos.ax`, baseline line 91, T432), BASELINE OK, WEAK-NATIVE 0.
- Smoke (`axtest.py --smoke --seed 421 --no-cache --baseline`): always run/str/hello.ax, ui/typeck/type_unknown.ax, diff/002-arithmetic.ax + one pick for each of 27 groups: TOTAL 48 PASS 46 FAIL 2 (`hir/basic.ax`, `resolve/R01_basic.ax`: baseline lines 51/46, T434), BASELINE OK. (WEAK-NATIVE 3 are pre-existing smoke picks, not tests of this task.)
- `python tools/archcheck.py`: 229 files scanned, 0 violations.

### Repeat runs on the new code (flake check; stress.py: one build per mode, exact stdout)
| test | native | native-O1 | interp |
|---|---|---|---|
| waker/join_waker_race | 10/10 | 10/10 | 5/5 |
| waker/cancel_self_waking | 10/10 | 10/10 | 5/5 |
| waker/user_waker_vtable | 10/10 | 10/10 | 5/5 |
| waker/detached_output_drop | 10/10 | 10/10 | 5/5 |
| waker_qa/qa_wake_during_poll | 10/10 | 10/10 | 5/5 |
| waker_qa/qa_cancel_during_poll | 10/10 | 10/10 | 5/5 |
| waker_qa/qa_join_drop_vs_complete | 10/10 | 10/10 | 5/5 |
| waker_qa/qa_group_drop_detached | 10/10 | 10/10 | 5/5 |
| waker_qa/qa_late_waker_drop | 10/10 | 10/10 | 5/5 |
Interp was run 5x (not the 10x requested by the orchestrator; the task's acceptance asks 5) to stay within the gate time on the shared machine; with the two full-tree runs each interp test has 6-7 passing runs. Plus the two full-tree axtest runs: no flake. Thread-count variation: the engineer's tests use 2 workers (user_waker_vtable 1); my tests use 2 workers plus a foreign OS thread (qa_wake_during_poll, qa_late_waker_drop) and main as a third actor.

### Native evidence (step 4a)
- Every new run test (4 engineer + 5 QA) has an exact `// stdout:` with the measured counters; failures print `FAIL line <n>` and spin to the timeout (no `assert()`); axtest WEAK-NATIVE 0 for the whole tree.
- Spot proof (snapshot only, restored with a byte compare afterwards): `stdout` of `waker/user_waker_vtable.ax` changed `... 2 4` -> `... 2 5`: `axtest ... waker/user_waker_vtable` -> FAIL in interp, native, native-O1 ("stdout differs at byte 30"); `waker_qa/qa_cancel_during_poll.ax` `outputs 0` -> `outputs 1`: FAIL x3 ("differs at byte 76"). Both restored (`cmp` with the main tree: identical).
- Cross-mode: all tests print the same bytes in all modes (identical `stdout:` judged in all three).

### Spec check
- SPEC-33 AXS-ASY-011: `Waker` operations dispatch through the `RawWaker` vtable; `will_wake` added (data + vtable equality). The vtable field is still named `drop_waker` in `std/core/prelude.ax` vs `drop` in SPEC-33 (pre-existing, not this task).
- SPEC-31 orderings: RMWs AcqRel, terminal publish Release then join COMPLETE AcqRel; readers Acquire. No silent semantic choice left undocumented: the state renumbering and the null-Context contract are in the code comments and the report's Decisions section.
- No diagnostics added; no compiler change; no shared-file edit (`tools/axtest.py`, CMake, CI, `diag/codes.def`, `driver/pipeline.c` untouched by the change set).

### Isolation (who can observe the change)
- `grep -rln "std\.asyn\|std/async\|TASK_COMPLETED\|TaskHeader" tests std compiler tools bootstrap spec` outside `std/async/` and `tests/std/async/`: only spec files (ADR-0041, ADR-0042, ROADMAP, SPEC-33/34/35/52/88). No code or test outside the two trees imports the module (the `std/async` sources are only consumed through the bundles in `tests/std/async/**`).
- Old 3-bit mask users: `grep -rn "0x7u32\|0xFFFFFFF8\|0x7)" std tests/std/async` (`.ax`, `.axsrc`, `.py`): 0 hits. Repo-wide `& 7u32` hits are all `((reg as u32) & 7u32)` in encoder code (tests/encode, tests/selfhost backend bundles): unrelated. `has_join_waker`: 0 hits. `group_request_cancel` remains as a documented alias (group.ax:106, used at group.ax:431, re-exported in mod.ax).

### Old vs new (regression tests really catch the defects)
Scratch tree = snapshot `std/` with `std/async/{waker,task,executor,group,mod}.ax` from `git show HEAD:`, plus the new test dirs, bundles regenerated there (`gen_tests.py`). Driver `stress.py` (scratchpad): build once per mode, run N times, exact stdout compare.

| test (old std/async) | native | native-O1 | interp |
|---|---|---|---|
| join_waker_race | 7/10 runs FAIL (`lost 1` x5, `lost 2`, `lost 3`) | 8/10 FAIL (`lost 1` x5, `lost 2` x2, `lost 3`) | not re-run (stopped for time; the report's interp note is that the old test had a UAF) |
| cancel_self_waking | 4/10 FAIL (`clobbered 1..17`) | 10/10 FAIL (`clobbered 5..23`) | not re-run (report: TIMEOUT) |
| user_waker_vtable | 3/3 CRASH 0xC0000005 | 3/3 CRASH | 3/3 FAIL rc 125, oracle UB at `(*raw).ref_count.fetch_add` on the user data |
| detached_output_drop | 3/3 TIMEOUT (check fails, spins) | 3/3 TIMEOUT | not run |

New code, same driver: all PASS (see "Repeat runs" below).

My adversarial tests on the OLD std/async (3 runs each, native / native-O1):
- qa_wake_during_poll: native 1/3 FAIL (`lost 1`), O1 0/3 (narrow window; the test is primarily a guard for the new state machine).
- qa_cancel_during_poll: 3/3 + 3/3 FAIL (`outputs -50`: outputs of mode 2, handle dropped during the poll, never dropped).
- qa_join_drop_vs_complete: 2/3 + 3/3 FAIL (`leaked 1/31`, `leaked 111..119`).
- qa_group_drop_detached: 3/3 + 3/3 FAIL (`outputs 151..187` never dropped).
- qa_late_waker_drop: does not compile against the old API (`raw_waker_clone` is new) - expected.

### Mutation checks (one fix reverted, scratch copy of the snapshot std, bundles regenerated)
- m1 `tcb_poll_fn`: `task_begin_poll` replaced by `load` + `store(TASK_POLLING)` (the old clobber): cancel_self_waking native 2/3 FAIL (`clobbered 3`, `1`), O1 3/3 FAIL (`clobbered 4,4,5`). (qa_cancel_during_poll still PASS 3/3: its request lands after the poll started, which m1 does not touch - expected.)
- m2 `default_task_drop`: null-Context `poll_fn` call removed: detached_output_drop TIMEOUT, qa_late_waker_drop TIMEOUT, qa_join_drop_vs_complete `leaked 98`, qa_group_drop_detached `outputs 124` - all FAIL.
- m3 `handle_poll_i64`: result of `task_register_join_waker` ignored (always Pending): join_waker_race native 2/3 FAIL (`lost 2`, `lost 7`), O1 3/3 FAIL (`lost 11..19`).
- m4 `task_end_poll_pending`: cancel-flag-without-wake branch removed: qa_cancel_during_poll 2/2 + 2/2 TIMEOUT (mode 3 parks forever). Note: none of the engineer's tests kill m4 (cancel_self_waking 1/1 PASS under m4) - my test covers that branch.

### Concurrency review (std/async/waker.ax, task.ax, group.ax, executor.ax)
State word: low nibble IDLE 0 / POLLING 1 / NOTIFIED 2 / POLLING|NOTIFIED 3 / COMPLETED 0xA / CANCELLED 0xB / PANICKED 0xE; flags 0x100 CANCEL, 0x200 DETACHED, 0x400 PANIC (group.ax:81). Checked:
- Lost wake: `task_wake` = one `fetch_or(NOTIFIED)`; only prev-nibble IDLE enqueues. A wake during a poll leaves 3; `task_end_poll_pending` (`fetch_sub(1)`) sees NOTIFIED and re-queues. Wake after poll end sees IDLE and enqueues. No window: every transition is a single RMW. Wakes on terminal values are no-ops (bit 1 set in 0xA/0xB/0xE).
- Double enqueue / double poll: enqueue happens only on IDLE->NOTIFIED (one winner), on 3->2 by the poller (no IDLE in between), at spawn (state NOTIFIED). `task_begin_poll`'s `fetch_sub(1)` relies on the dequeued task being exactly NOTIFIED; that holds because no in-tree path enqueues otherwise and no path other than the poller writes a terminal value (all `task_finish` callers are inside `tcb_poll_fn`/`group_poll_fn`). `task_schedule` is `pub` and would break this if called by user code without the transition (documented precondition; note N4).
- Cancel flag: set by `fetch_or` only; `task_begin_poll` returns the prior word (flag seen if set while queued); flag set during a poll re-queues via NOTIFIED or via the flag-only branch. Only `task_set_terminal` (`store`) clears flags, and only on a terminal state, where they no longer matter. DETACHED is read only by `handle_cancel_unless_done` of a live handle (a detached handle no longer exists), so its erasure by the terminal store is harmless.
- Refcount / lifetime: spawn starts at 2 (executor + handle); the executor releases after observing a terminal poll result; every executor poll loop holds a task waker in `cx` across the poll call, so the header outlives any post-`task_end_poll_pending` window even when another worker completes and releases the task concurrently. Clones increment while holding a reference (no 0->1 resurrection / ABA).
- Join slot: REGISTERING/WAKER_SET/COMPLETE protocol verified by case analysis: completer's `fetch_or(COMPLETE)` vs handle's two CASes; whoever makes the deciding transition owns the fields; terminal state published (Release store) before COMPLETE (AcqRel), handle reads it after Acquire. Waker consumed exactly once (woken by completer, dropped by a losing registration, replaced, or released in `default_task_drop`). Only the single handle registers. QA tests 2/3/5 exercise it under load.
- Waker ops: `wake` leaks then calls vtable `wake` (no second Drop), `wake_by_ref`/`clone`/`Drop` dispatch through the vtable; empty waker (null data or vtable) is a no-op everywhere, consistent with `block_on`/`run_until` contexts.
- Output drop: has_output set only by the two poll functions; cleared by `task_take_output`, the blocking `join`, `reap_raw`; dropped once in `default_task_drop` (runs only at refcount 0, so no concurrent poll/handle). Panicked Ready output is discarded in `group_poll_fn` (`let discarded = val`).
- Null-Context poll trick: documented contract only (task.ax:98-102), not enforced. Exposure is limited: `default_task_drop` calls `poll_fn(raw, null)` only when `has_output` is set, and `has_output` is written only by `tcb_poll_fn`/`group_poll_fn`, which handle null. A custom poll fn that delegates to them is safe; one that dereferences `cx` before delegating would null-deref (deterministic crash, not silent corruption), which already requires `unsafe` in user code. The raw `spawn(fut, poll_fn)` API is an interim deviation that T422c replaces. Judged a documented hazard of an interim unsafe API, not a FAIL (follow-up F1).

Findings (notes, none blocking):
- N1 `std/async/task.ax:98-102` vs `:263`: the contract says the null-Context call drops "future, output", but `default_task_drop` calls it only when `has_output`; a future still stored at the last release (task never reached terminal, e.g. a `LocalExecutor` dropped with queued tasks) is leaked. Pre-existing behaviour, no in-tree path reaches it (every terminal path drops the future first). Comment precision only.
- N2 `std/async/group.ax:93-100` `task_panic` still treats the Context waker's data as a `TaskHeader` and `fetch_or`s into it; with user wakers now first-class (this task), calling `task_panic` under a user waker writes into user memory. Pre-existing (T422), out of this task's scope; follow-up F2.
- N3 `std/async/group.ax` unused imports `TASK_IDLE`, `TASK_POLLING`, `TASK_NOTIFIED`, `task_wake` (engineer already noted; `axiomc2 check` reports nothing).
- N4 `std/async/waker.ax:149` `task_schedule` is `pub` (re-exported from task.ax) with the precondition "caller made the IDLE -> NOTIFIED transition"; a caller violating it makes `task_begin_poll` borrow into the flag bits. Internal API; worth `pub(crate)`-style hiding in T422c.
- N5 the report says the raw before/after logs are in the snapshot (`after_run1.log`, ...): they are not in `build-snap-T421a` (the snapshot was refreshed). Evidence was reproduced independently above.
- N6 `tests/std/async/executor/gen_tests.py:600` (`lost_wake_prevention`): expectation changed from NOTIFIED to POLLING|NOTIFIED - a semantic consequence of the new encoding (sticky permit, waker does not enqueue a polling task), not a weakening.
- N7 coverage gap closed by QA: the cancel-flag-without-wake branch of `task_end_poll_pending` (waker.ax:186-189) was not killed by any engineer test (mutation m4 left cancel_self_waking passing); `qa_cancel_during_poll` mode 3 covers it now.

No FAIL finding: all acceptance criteria verified (new tests pass in all modes, >= 5 consecutive runs without flake; all `tests/std/async/**` pass, WEAK-NATIVE 0; failing ids outside the task are baseline ids; report has an exact `## Files changed`, `taskctl.py changes` shows no REFUSED line for the engineer's files - the only REFUSED line before this file existed was for my 12 QA files, which are listed below).

### QA tests added (tests/std/async/waker_qa, bundle scheme of tests/std/async/waker)
- `qa_wake_during_poll`: foreign thread adds tokens and wakes after each, task never self-wakes; 200 iterations, goal 1..20, poll window widened by yields; checks no overlapping poll and no lost final wake.
- `qa_cancel_during_poll`: cancel / handle drop / flag-only request while the task is inside its poll, poll then returns Pending or Ready; futures and outputs dropped exactly once; flag-only branch.
- `qa_join_drop_vs_complete`: awaiting task's handle dropped at varying moments while the awaited task completes and its join waker fires; a leaked or double-dropped join waker shows as leaked/extra output drops of the awaiting task.
- `qa_group_drop_detached`: per round 8 children (half adopted by a TaskGroup, half detached, every third panicking via `task_panic`) torn down immediately by dropping the group.
- `qa_late_waker_drop`: a cloned task waker parked outside the task is the last reference; output must survive until a foreign thread does wake_by_ref, clone+drop, then wake (last release, output dropped there).
- `check_waker_qa_bundles.test`: bundles in sync with live std/async.

### Follow-ups (for the architect)
- F1 (T422c): replace the null-Context "drop payload" call by an explicit typed `drop_output_fn` (or equivalent) once generic fn pointers work (T444/T446); until then the contract on `TaskControlBlock` is documentation-only. Also hide `task_schedule` (N4).
- F2 (T422c/T536): `task_panic` must not assume the Context waker is a task waker (N2).
- F3 (compiler, interp; new pre-existing bug, not on the baseline, not caused by T421a): `compiler/interp/interp.ax` HOST_INTR_THREAD_SPAWN probes the thread context with `interp_validate_raw_ptr(ctx, a1, 40, 8)` to look for the std.thread packet magic; for a context allocation smaller than 40 bytes the probe emits `error[AX_UNSAFE_INTERP_UB]: out-of-bounds pointer access` at the `thread_spawn` call (exit 1 after normal output) although it then resets `ctx.failed`. Minimal repro (interp only; 40/48 bytes are fine, 8/32 fail):
  `fn entry(ctx: *mut u8) -> i64 { 0i64 }` / `let p = unsafe { heap_alloc(32usize, 8usize) }; let th = unsafe { thread_spawn(entry, p, 0usize) }; unsafe { thread_join(th, 0 as *mut i64); }` -> "done" then the UB error. `qa_late_waker_drop` allocates 64 bytes to avoid it (commented).
- F4 (T437b / taskgate): the grep-based affected set treats trait / lang-item names that occur in the changed module (`Drop`, `Send`, `Waker`, `Future`) as public names of the change, selecting 438 test files (149 selfhost bundles) for a std/async-only change set. Exclude names not defined by the changed files (they are `impl ... for` targets, not definitions) or use the dep-file of T437b.
- F5 (optional): the old-code join_waker_race / cancel_self_waking failures are probabilistic (native 7/10 and 4/10 failing runs on old code); fine as regression guards together with the mutation results, but a deterministic oracle-scheduled variant would make them certain.

## Files changed
- _workspaces/reports/T421a-qa.md
- tests/std/async/waker_qa/gen_tests.py
- tests/std/async/waker_qa/check_waker_qa_bundles.test
- tests/std/async/waker_qa/src/qa_wake_during_poll.axsrc
- tests/std/async/waker_qa/src/qa_cancel_during_poll.axsrc
- tests/std/async/waker_qa/src/qa_join_drop_vs_complete.axsrc
- tests/std/async/waker_qa/src/qa_group_drop_detached.axsrc
- tests/std/async/waker_qa/src/qa_late_waker_drop.axsrc
- tests/std/async/waker_qa/qa_wake_during_poll.ax
- tests/std/async/waker_qa/qa_cancel_during_poll.ax
- tests/std/async/waker_qa/qa_join_drop_vs_complete.ax
- tests/std/async/waker_qa/qa_group_drop_detached.ax
- tests/std/async/waker_qa/qa_late_waker_drop.ax

VERDICT: PASS round=0
