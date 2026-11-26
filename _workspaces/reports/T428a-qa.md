# T428a QA gate

## Round 0

Snapshot `build-snap-T428a` = HEAD 9135f012 (T461) + the T428a change set, refreshed twice with
`taskctl.py snapshot T428a` (before the gate, and again after adding the QA tests: "HEAD 9135f01 + 18 changed";
bundles regenerated: 36 generators, 60 files, no BUNDLES FAILED). Logs: `_workspaces/artifacts/T428a-qa/`.

### Checks and evidence

1. **Change set.** `taskctl.py changes T428a`: 13 entries staged (both compiler files, 10 tests, report), no
   `REFUSED` line. Only lock/path files edited (`compiler/mir/async_lower.ax`, `compiler/mir/drop.ax`,
   `tcp_framing_split.ax` are locks; tests under paths). No shared-file edits, no `bootstrap/axiom0` change.
2. **Build / fixed point** (rebuilt on HEAD 9135f01 sources): `python tools/build_axiomc.py --out build --stage 3`
   in the snapshot -> axiomc1 rebuilt (std/math changed), seeded A/B/C rebuilt, `FIXED-POINT (O1) OK`
   sha256(axiomc2_O1) == sha256(axiomc3_O1) == 1eb724ab506ec8c1..., `STAGE0-GUARD OK` (6 smoke programs incl.
   Xin chào thế giới), `BUILD-AXIOMC OK` (`build.log`). HEAD-only compiler for comparisons: `git archive 9135f012`
   into a scratch dir, `build_axiomc.py --stage 2` -> `FIXED-POINT (O1) OK` sha256 dd6c7b0b... (= the cached HEAD
   seed `axiomc2_O1_0963dde821e1b0d0.exe`).
3. **taskgate** (before the QA tests were added):
   `python tools/taskgate.py --task T428a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428a.json`
   -> `TOTAL 466 PASS 464 FAIL 0 SKIP 2 XFAIL 0`, BASELINE OK, archcheck clean (252 files, 0 violations),
   WEAK-NATIVE 0 in own/changed tests (3 elsewhere), cache verification sample n=20 mismatch none,
   `TASKGATE T428a exit=0`, wall 1397 s. Parts: own 9 ids / 27 results; affected 217 ids / 414 results; smoke 33 ids.
   Affected-set derivation: `map compiler/mir -> tests/mir, tests/run/drop, tests/verify, tests/selfhost/{mir,drop}`
   (rule `tools/affected_map.txt`), `generator check of a bundle embedding compiler.mir.drop` (10 selfhost
   `bundles_current.test`), 30 changed test files (own tests + 20 regenerated selfhost bundles: abi, backend,
   driver, drop, interp, interp_opt, lir, mir, obj_link_driver, opt, own_mir_verify, verify). UNMATCHED none,
   UNRESOLVED none, no CACHE-MISMATCH.
4. **Acceptance suites** (taskgate does not select them; run separately after the QA tests were added):
   `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 2 --baseline _workspaces/baseline-failures.txt run/async mir/async ui/async std/async conformance/p11 inspect/async_layout.test perf/p11_executor`
   -> `TOTAL 457 PASS 444 FAIL 13`, `WEAK-NATIVE 0` (`suites.log`). The failures:
   - 5 in the HEAD baseline (T449a): the 4 std/async `check_*_bundles.test` and `timer_wheel_100_timers.ax [interp]`.
   - `conformance/p11/e11_5_executors/check_conformance_bundles.test` and `perf/p11_executor/check_perf_bundles.test`:
     not in the baseline, but they fail identically at HEAD (`gen_tests.py --check` in the `git archive 9135f012`
     tree: the same 8 resp. 3 files, the same lengths, e.g. `cancel_tree_groups.ax actual=180116 vs expected=185361`).
     Generators read std only, so T428a cannot affect them. New pre-existing ids, see follow-ups.
   - `qa_cancel_spawned_task.ax` and `qa_cancel_spawned_intrusive.ax` (all three modes): the QA tests for scope
     item 2, caused by the unfixed std driver -> **finding F1**.
   All 8 engineer tests, `direct_slice_io_async_locals`, `tcp_framing_split` and the other 3 QA tests pass in
   interp, native and native-O1.
5. **Fails on HEAD.** With the HEAD compiler (dd6c7b0b) the engineer's tests and my `qa_shapes_across_awaits`,
   `qa_drop_moves_in_place`, `qa_cancel_every_suspension` all fail: oracle `AX_UNSAFE_INTERP_UB use of dangling
   pointer`, native wrong values (`qa_shapes`: `branch=1,2`, then segfault 139; `qa_drops`: `reassign =6`
   instead of `=12`, `heap n=0`; `qa_cancel`: `d5:1000` instead of `d5:1101`, `ready=1014` instead of 1020).
6. **Layout / verifier.** `axiomc2 inspect --emit=async-layout` prints `in_place=true` for address-observable
   locals (`udp_recv_from_local.rx`: `live local2: [16]u8 ... in_place=true`; `qa_cancel` `outer`: guards
   in place, plain integers `in_place=false`); in-place fields do not overlap other live fields (offsets checked
   by hand for `outer`: 160/176/192 vs 208..232). `tests/inspect/async_layout.test` passes. Verifier: every run
   passes the default build pipeline; note that `verify_mir_own`/`verify_mir_cap` skip `async_lowered` bodies
   (pre-existing, unchanged).
7. **Native evidence.** Every new/touched test is `modes: interp native` with an exact `stdout:`; the runner
   reports `WEAK-NATIVE 0`. Mutation proof: `pointer_only_use.ax` expectation `via=1207` -> `via=1208` in the
   snapshot, `axtest --no-cache` -> `FAIL [interp]`, `FAIL [native]`, `FAIL [native-O1]` ("stdout differs at
   byte 7"), file restored (`cmp` with main tree OK).
8. **Determinism.** Each of the 9 passing addr_stable_locals oracle tests run 8x: one stdout hash each.
9. **Spec.** Behaviour matches ADR-0050 / SPEC-33 AXS-ASY-043 item 7 and AXS-ASY-005 item 4, except the std
   executor contract of AXS-ASY-005 item 4 ("std executors ... never move a future after its first poll"), see F1.
   No new diagnostics. The "storage-live" reading of "live across" (report design point 3) is sound and is what
   REQ-ASY-122 needs; note it for the architect (SPEC-33 text says "live across").

### Findings

**F1 (FAIL) — scope item 2 not done: cancelling a spawned task moves its polled future.**
`std/async/task.ax:197` `tcb_drop_future`: `let mut tmp: [1]F = [*address_of_mut((*tcb).future)];` copies a
polled, pending state machine out of the TCB and drops the copy. Every in-place local is therefore dropped at
another address, and writes made through pointers into it during the drop land in the stale TCB copy.
Repro (tests added under the task's paths):
- `tests/run/async/addr_stable_locals/qa_cancel_spawned_task.ax` (the engineer's own proposed test): expected
  `sub drop | guard 43 here=1`, got `sub drop | guard 42 here=0` in interp, native, native-O1.
- `tests/run/async/addr_stable_locals/qa_cancel_spawned_intrusive.ax`: an intrusive list node in an async local
  unlinks itself in `Drop`; after `cancel()` the head still points into the freed TCB: oracle
  `AX_UNSAFE_INTERP_UB use of dangling pointer` (line 83), native `dangling node, val=7`, exit 1.
Verification of the proposed fix (scratch copy of std only, never the main tree):
`drop_in_place<F>(address_of_mut((*tcb).future));` (+ `@intrinsic unsafe fn drop_in_place<T>(p: *mut T) {}`)
makes both tests pass in all three modes (`guard 43 here=1`, `list empty`).
Decision on the deferral: not acceptable. The task text says "fix it in this task only if one does — then add the
file to the change set", ADR-0050 / AXS-ASY-005 item 4 now state the contract normatively, and no task owns the
fix. The stated blocker does not hold: T449a's `paths:` do not include `std/async/task.ax` (only timer.ax,
timeout.ax and test dirs). The real coupling is that the change makes these bundle checks stale:
`e11_6_async_io/check_conformance_bundles.test` (`taskgroup_async_io.ax`, checked: `gen_tests.py --check` with the
fixed task.ax reports it out of date; that is the one currently passing), plus the already-stale std/async
(T449a), e11_5 and perf/p11_executor bundles. Required for round 1: add `std/async/task.ax` to the change set
(the orchestrator/architect adds it to `locks:`, together with `tests/conformance/p11/e11_6_async_io/taskgroup_async_io.ax`
so the bundle can be regenerated with `gen_tests.py`), or sequence T428a after T449a; the std/async bundles stay
T449a's. Run T449a's regeneration after this lands, or let T449a be gated on the new task.ax.

### Pre-existing defects (reproduced identically on HEAD 9135f012 build, dd6c7b0b; not caused by T428a)

Scratch programs in the QA scratchpad (`adv/def*.ax`), run with `run --interp`, `build -O0`, `build -O1`:
1. **Double drop of values moved out before `.await`** (report item 1): `let g = Guard{..}; let a = g.get();
   if c { eat(g); } Nap.await` -> `d1 d1` (c = true) in all modes on HEAD and with T428a; also unborrowed
   (`d2 d2`) and partial tuple move (`d3 d3 d4`). Related: a deferred-init local (`let g: Guard; if c { g = ..;
   g.get() } ..await`) with c = false is dropped although never initialized: HEAD `d0`/`d1`, T428a interp `d0`,
   native `d1441152`/`d48` (now reads the uninitialized in-place field; the defect is the same missing drop flag).
2. **`static mut` in an async fn is a private copy** (report item 2): expected `1211 1211`, got `1010 201` on
   HEAD and with T428a, all modes.
3. **Atomics in an async fn crash** (report item 3): `AtomicI64` local used across `.await`: oracle
   `AX_UNSAFE_INTERP_UB null pointer dereference`, native exit 139, on HEAD and with T428a.
4. **`e11_5_executors/check_conformance_bundles.test`** fails at HEAD (`gen_tests.py --check` in the HEAD
   archive) and is not in `_workspaces/baseline-failures.txt`; the same holds for
   **`perf/p11_executor/check_perf_bundles.test`** (3 bundles out of date), newly found here.
5. **Self-aliasing aggregate assignment** (new): `arr = [arr[2], arr[0], arr[1]]` gives `3,3,3` and
   `pair = Pair { a: pair.b, b: pair.a }` gives `8,8` even in synchronous `main`, on HEAD, interp and native
   (the aggregate is built in the destination). Removed from my test; needs its own fix task.
6. **Non-deterministic oracle panic** (new): `async fn c_ret_tuple() -> (Guard, i64)` followed by an async fn that
   passes a `Guard` to a nested async fn: `run --interp` prints `panic: polling a completed Future state machine`
   in some runs and not others (6 runs: HEAD 2/6, T428a 2/6 on the minimal pair; always on the larger program),
   native always correct. Same on HEAD.
7. `verify_mir_own` / `verify_mir_cap` return early for `async_lowered` bodies, so the coalesced `poll` bodies
   are only checked by the structural verifier.

### Files changed
- tests/run/async/addr_stable_locals/qa_shapes_across_awaits.ax
- tests/run/async/addr_stable_locals/qa_drop_moves_in_place.ax
- tests/run/async/addr_stable_locals/qa_cancel_every_suspension.ax
- tests/run/async/addr_stable_locals/qa_cancel_spawned_task.ax
- tests/run/async/addr_stable_locals/qa_cancel_spawned_intrusive.ax

### Follow-ups (for the architect)
- F1 fix in round 1 (locks above); after it, `e11_6` bundle regeneration.
- Defects 1-3 (drop flags across `.await`, `static mut`, atomics in async fns): fix tasks (REQ-ASY-082 for atomics).
- Admit or fix `e11_5_executors/check_conformance_bundles.test` and `perf/p11_executor/check_perf_bundles.test`
  (stale since T427/T538-era std changes; outside the T449a/T449b list).
- Defect 5 (aggregate assignment aliasing its own destination) and defect 6 (oracle non-determinism): new fix tasks.
- SPEC-33 AXS-ASY-043 item 7: say "storage-live (initialized and in scope) across" instead of "live across".

VERDICT: FAIL round=0

## Round 1

Gate of the round-1 change set (report "Round 1 (QA F1)" + orchestrator note; architect unblock
`_workspaces/reports/unblock-T428a.md`). All builds and tests ran inside `build-snap-T428a` only.

### Checks performed and evidence
1. **Change set.** `taskctl.py changes T428a`: 69 staged paths, no `REFUSED` line (one "ignored line" note: the
   `STATUS: BLOCKED` line after `## Files changed` is skipped as expected). Snapshot vs main tree: every listed
   file is byte-identical (`cmp`); the main tree's other dirty files (`compiler/interp/*`, `compiler/link`,
   `compiler/obj`, other tasks) are not in the snapshot.
2. **Snapshot / build.** Gated first on HEAD 538d26c; HEAD then moved to 93488dd (T461a, link/obj only), so the
   snapshot was refreshed (`taskctl snapshot T428a`: "HEAD 93488dd + 70 changed", bundles regenerated
   "36 generator(s), 60 file(s)", no BUNDLES FAILED) and everything below was re-run on 93488dd.
   `build_axiomc.py --out build --stage 3 --force` (full chain axiom0 -> c1 -> c2 -> c3):
   - on 538d26c: `FIXED-POINT (O1) OK` sha256 1eb724ab.. (same as the engineer's) (`_workspaces/T428a_qa_r1_build.log`);
   - on 93488dd: `FIXED-POINT (O1) OK` sha256(axiomc2_O1) == sha256(axiomc3_O1) == f993ba9d.. (9282560 bytes)
     (`_workspaces/T428a_qa_r1_build2.log`). No warnings.
3. **F1 (round 0) fixed.** `std/async/task.ax:195` `tcb_drop_future` now calls
   `drop_in_place<F>(address_of_mut((*tcb).future))` (intrinsic declared at line 46, as in `std/async/channel.ax`);
   the moving copy `let mut tmp: [1]F = [*address_of_mut((*tcb).future)];` is gone from `std/` and from every
   bundle under `tests/` (grep: 0 hits; the 46 bundles that embed `tcb_drop_future` are all in generator-checked
   dirs). `qa_cancel_spawned_task.ax` and `qa_cancel_spawned_intrusive.ax`: PASS [interp], [native], [native-O1]
   (`--no-cache` on 538d26c, and again in the 93488dd suite run).
4. **Bundles are generator output.** In the snapshot and in the main tree, `gen_tests.py --check` prints OK for
   `tests/std/async/{executor,structured,waker,waker_qa}`, `conformance/p11/e11_3_threads_sync`, `e11_5_executors`,
   `e11_6_async_io` and `perf/p11_executor`. No `src/*.axsrc` changed, and for every regenerated `.ax` under
   `tests/{conformance,perf,std}` the `stdout/stderr/exit/modes/covers` header lines are identical to HEAD (md5 of
   the directive lines), so no expectation was weakened. Switching the e11_5 and perf generators to
   `bundle_closure.py` (`COMMON_PREREQS = []`) matches the T449a scheme. Note: it does not help the 2 T428g tests,
   because they `use std.thread.spawn` themselves, so the closure still bundles `std.text.string` next to `std.io`.
5. **Baseline.** `git diff HEAD -- _workspaces/baseline-failures.txt`: the 3 lines naming T428a (e11_6/e11_5/perf
   bundle checks) and their comment block are removed; the architect's 2 lines
   `conformance/p11/e11_5_executors/{spawn_affinity_vs_migration,fiber_in_async_and_threads}.ax ... T428g` are
   present. No other baseline line names an async/p11/perf dir.
6. **taskgate** (93488dd, `_workspaces/T428a_qa_r1_taskgate2.log`, JSON `_workspaces/artifacts/taskgate-T428a.json`):
   change set 90 files (working tree vs HEAD, incl. the regenerated selfhost bundles); 292 affected ids derived
   (mir 91, run 66, selfhost 35, std 34, verify 29, driver 17, conformance 13, perf 5, modules 1, ui 1) through the
   `compiler/mir` map row, `std.async` references (`tcb_poll_fn`) and changed test files; smoke seed 3265875265
   (one per group + `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`); unmatched none, no
   UNRESOLVED / MAP-NOTE / DEFERRED / CACHE-MISMATCH. Cache: 0 cached (fully fresh compiler), 112 miss, 213 uncacheable.
   `TOTAL 653 PASS 645 FAIL 6 SKIP 2 XFAIL 0`; failing ids = exactly the 2 T428g baseline ids (3 modes each);
   `BASELINE OK`; archcheck 252 files, 0 violations; smoke-check OK; WEAK-NATIVE 0 in own/changed tests (3 elsewhere,
   pre-existing); `TASKGATE T428a exit=0`. (The same run on 538d26c gave the identical totals,
   `_workspaces/T428a_qa_r1_taskgate.log`.)
7. **Requested suites** `run/async`, `mir/async`, `ui/async`, `std/async`, `conformance/p11`, `perf/p11_executor`
   (448 ids: 81 / 3 / 22 / 154 / 175 / 13), `axtest --id-file ... --gate -j 2 --exclude-requires axiom0-internal
   --baseline` on 93488dd (`_workspaces/T428a_qa_r1_suites2.log`): `TOTAL 448 PASS 442 FAIL 6 SKIP 0 XFAIL 0`,
   `WEAK-NATIVE 0`, `BASELINE OK`. The 6 failures are the 2 T428g ids (AX_TYPE_MISMATCH `Result.Ok(string_new())`,
   the std.io / std.text.string `String` clash), in interp, native and native-O1. These are the only failures in
   those dirs. (Same result on 538d26c, `_workspaces/T428a_qa_r1_suites.log`.)
8. **Native evidence / mutation.** In the snapshot only: `udp_recv_from_local.ax` `// stdout: rx=3084 tail=77\n`
   -> `rx=3085`, `axtest --no-cache --filter run/async/addr_stable_locals/udp_recv_from_local` -> FAIL [interp],
   FAIL [native], FAIL [native-O1] ("stdout differs at byte 6"); file restored (`cmp` with the main tree OK).
9. **Adversarial test (step 5): the other `tcb_drop_future` callers.** The F1 tests cover only the cancel path.
   New `tests/run/async/addr_stable_locals/qa_r1_panic_pending_inplace.ax` covers the panic-containment path
   (SPEC-34 AXS-EXEC-007): the task is polled twice while pending (with an address check that the in-place local
   did not move), then its third poll calls `task_panic` and returns Pending, so `tcb_poll_fn` drops the future of a
   PANICKED task. The awaited future's Drop writes through its pointer into the in-place `Guard`, whose Drop must
   then see the write at the same address. Expected `polls=2 moved=0 / sub drop | guard 45 here=1 / result=panicked`.
   It PASSes in interp, native and native-O1. Against a scratch std holding HEAD's moving `task.ax` it prints
   `guard 44 here=0` in interp and native, so it catches the F1 bug. (My first draft expected `polls=3`, an error in
   my own expectation: two `try_tick`s give two polls. I fixed it before the gate runs, and the drop part matched
   on the first run.) Executor shutdown does not drop pending tasks (`LocalExecutor.shutdown` only frees the
   reactor), so there is no shutdown path to test.
10. **Spec / scope / shared files.** The fix implements ADR-0050 / SPEC-33 AXS-ASY-005 item 4 ("never move a
    future after its first poll") with no interpreter or backend special case. No new diagnostics, no
    `bootstrap/axiom0` change, no shared-file edit (`tools/axtest.py`, CMake, `diag/codes.def`, `driver/pipeline.c`).
    All edited paths are under `paths:`/`locks:`. No single-mode run test was added.

### Findings
None.

### Notes / follow-ups (not blocking)
- Accept-time REGATE risk: T461a (93488dd) changed `tests/selfhost/{backend,driver,encode}` bundles that this change
  set also regenerates. This gate already ran on 93488dd with regenerated bundles, so no REGATE is expected
  unless HEAD moves again.
- The round-0 pre-existing defects are filed by the architect (T428g-T428l); nothing new was found this round.

### Files changed
- tests/run/async/addr_stable_locals/qa_r1_panic_pending_inplace.ax

VERDICT: PASS round=1
