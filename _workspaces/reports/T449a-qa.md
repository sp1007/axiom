# T449a QA

## Round 0

Gate run entirely inside `build-snap-T449a/` (HEAD 9135f012 + the T449a change set; refreshed once with
`taskctl.py snapshot T449a` after I added my tests: "HEAD 9135f01 + 49 changed"). Compiler: `build/axiomc2.exe`
built there by `python tools/build_axiomc.py --out build --stage 2` (re-run by me: REBUILT because
`std/async/timeout.ax`, `timer.ax` changed; `FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`, sha256 dd6c7b0bc8b8d4bd).
Nothing was built or tested in the main tree.

### 1. Change set (`taskctl.py changes T449a`)
50 `stage` lines (baseline file, report, 2 std files, 4 generators + `bundle_closure.py`, 34 regenerated bundles
plus my 4 added test files, 2 reactor tests), no `REFUSED`. The only "ignored line" is the `STATUS:` line of the report. Four unlisted files
under the task's paths are my own tests (listed under Files changed). `timer.ax`/`timeout.ax` are in `paths:`;
`_workspaces/baseline-failures.txt` is in `locks:`. No change under `compiler/`, `bootstrap/`, `tools/`.

### 2. Special checks requested

**(1) timer_wheel_100_timers still as strong as before; 10 consecutive passes.**
- Diff read. The 120 timers, the reverse-shuffled spawn (`(i*37)%120`), the 100 us deadline spacing, the strict
  rank-order check `got != k`, the same-thread check, the 60 s drop-cancel check, `remaining_timers == 0` and the
  exact stdout `OK timer_wheel_100_timers 120 1 1 0\n` are unchanged. The lead time was 2 s (fixed), is now 1 s
  and doubles (1,2,4,8,16 s) only when the new explicit `setup_ok` guard (all 120 timers registered on the wheel
  via `try_tick` until the ready queue is empty, none completed) fails; if it never succeeds the test prints FAIL
  and returns 1. The timeout was not raised (still `timeout: 60`). The check is strictly stronger than "hope
  the 2 s margin holds" and no property was dropped.
- Mutation proof (snapshot only, restored afterwards): `std/async/timer.ax:72` `if tw_entry_less(...)` changed to
  `if false && tw_entry_less(...)` (heap sift-up disabled, timers fire out of order). Result:
  `FAIL timer_wheel_100_timers.ax [interp]/[native]/[native-O1]: stdout differs at byte 30` (the ordered flag), and
  my virtual-clock test `qa_timer_only_import` also FAILs in the 3 modes. Native legs are live.
- Stability, run by me: `for i in 1..10: python tools/axtest.py --compiler build/axiomc2.exe --build-dir build
  --no-cache -j 2 --filter std/async/reactor` -> 10 of 10 runs `TOTAL 24 PASS 24 FAIL 0` (24 = the whole reactor
  directory incl. `timer_wheel_100_timers` in interp, native, native-O1; this includes my 2 new tests). Machine was
  shared with other agents during the runs.

**(2) 420 s timeout of `waker/cancel_self_waking` and `waker/join_waker_race`.** Measured alone, MIR interp,
same compiler, same machine state:

| test | committed (stale) bundle at HEAD | regenerated bundle | native (regenerated) |
|---|---|---|---|
| cancel_self_waking | 60 s | 144 s | < 1 s (build 1 s) |
| join_waker_race | 26 s | 43 s | not measured (passes) |

Compile/check of the new bundle is 1 s, so the growth is pure interpreter execution. The test source is
unchanged; what changed is the std copy inside the bundle: the stale bundle held the pre-T423e/T426 executor, the
regenerated one holds the live executor (which now also polls reactor/timer/io on every tick). The two import lines
this task adds to `timer.ax`/`timeout.ax` execute nothing, so the slowdown is not caused by T449a; the old budget (180 s)
only looked sufficient because the bundle was stale. Both tests carry no wall-clock assertion and exact stdout is still
compared (`OK cancel_self_waking 500 1000 clobbered 0`, `OK join_waker_race 1000 lost 0`), native passes in < 1 s. 420 s
is about 2.9x the measured 144 s, which is a defensible headroom under `-j 2` on the shared machine (the engineer saw a
timeout at 180 s under load). Judged justified, not hiding a regression of this task. Note (not a FAIL): the 2.4x interp
slowdown of the live executor is a real performance characteristic of HEAD std/interp; see Follow-up F3.

**(3) bundle_closure.py and the 4 generators.**
- `python tests/std/async/{executor,structured,waker,waker_qa}/gen_tests.py --check` -> `OK ... bundles match live
  std/async` in all 4 (at HEAD all 4 fail: "content out of date"). `--check` regenerates in memory and compares bytes,
  so the committed bundles are exactly the generator output (not hand-edited). The generators' `--check`/write logic is
  untouched (diff shows only the import, the empty `COMMON_PREREQS`, the closure call and the 2 timeouts).
- Every one of the 133 results of the 4 bundle dirs + reactor (executor 29, structured 51, waker 13, waker_qa 16,
  reactor 24) PASS in interp, native and native-O1 in the taskgate "own" part (`PASS 133 FAIL 0`), so the bundles compile
  and run. Bundles carry exact `// stdout:` lines (native evidence ok); WEAK-NATIVE 0 in the task's own tests
  (the 3 WEAK-NATIVE of the run are outside the task's tests).
- `bundle_closure.py` read in full: longest-prefix `use` resolution, `std.core.*` skipped, imports before importers,
  cycle-guarded DFS, deterministic (sorted walk). Raises on a seed file with no `module` line. My adversarial test
  `qa_bundle_order` (below) confirms: each std module once per bundle, imports precede importers, deterministic output,
  unknown seed rejected, >= 20 bundles inspected: `OK bundle structure 34` (34 bundles inspected).
- Also ran all 13 `gen_tests.py --check` generators in the tree, snapshot vs `git archive HEAD`:
  executor/structured/waker/waker_qa HEAD fail -> snapshot OK; e11_3, channel, fiber, num, sync, native_panic_hook OK
  in both; e11_5, perf/p11_executor fail in both; **e11_6 OK at HEAD, FAIL in snapshot** (finding F1).

**(4) The 5 removed baseline lines** are exactly `std/async/{executor/check_async_bundles,structured/check_structured_bundles,
waker/check_waker_bundles,waker_qa/check_waker_qa_bundles}.test` and `std/async/reactor/timer_wheel_100_timers.ax`
(`git diff` of the baseline: only these 5 lines removed; no `T449a` text remains). All 5 ids pass: the 4 `check_*` in the 133
own results (and by hand `gen_tests.py --check` OK), `timer_wheel_100_timers` 10/10 x 3 modes.

### 3. Regression test proves the fix
`tests/std/async/reactor/timer_import_without_executor.ax`: `axiomc2 check --std-root <git archive HEAD>/std` on it prints
`error[AX_TYPE_UNKNOWN_FIELD] ... <std>/async/timer.ax:459:21 let w = cx.waker();` (and the same at timeout.ax:128); with the
fixed std: 0 errors; passes interp/native/native-O1 with exact stdout.

### 4. Gate scope (taskgate) and results
`python tools/taskgate.py --task T449a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2
--extra ...` from inside the snapshot: **exit 0**, wall 1990 s.
`TOTAL 863 PASS 862 FAIL 0 SKIP 1 XFAIL 0`; archcheck clean (252 files, 0 violations); baseline OK, failing ids: none; tool
self-tests pass; WEAK-NATIVE 0 in own/changed tests; smoke-check OK. UNMATCHED: none; no UNRESOLVED / MAP-NOTE / DEFERRED
lines; cache: CACHED 3, hits 21, verification sample n=20 of 21, mismatch none, rejected {}.
Parts: own 51 ids / 133 results PASS 133; affected 314 ids / 807 results PASS 806 SKIP 1 (one SKIP among affected; not
attributable from the taskgate output, not in any task-owned test; no FAIL); smoke 33 ids / 56 results PASS 56 (3 cached).
Groups touched: conformance 38, driver 18, mir 4, modules 6, perf 5, run 42, selfhost 57, std 130, typeck 6, ui 21, plus
one smoke pick for each other top-level group (abi, build_native, diff, encode, fuzz, hir, inspect, lex, link, link2, lir,
mc, obj, opt, opt2, parse, programs, resolve, tools, unit, verify). Affected-set derivation is in the taskgate Markdown block
(`_workspaces/artifacts/taskgate-T449a.out` in the snapshot; rules: std-module/public-name reference, derived from the 2 std
files and 4 generators). Note on the derivation: the affected-set rule only selects `.ax` files that textually reference a std
module, so the `cmd:`-style `check_*bundles.test` tests of other directories (e11_5, e11_6, perf) were not selected; I ran them
by hand (next section). My `--extra` ids lacked the `.ax` suffix and were reported `UNKNOWN-ID`; those tests were run by hand
(7/7 PASS in the 3 modes plus the 3 modes of the bundle-order check) and are inside the "own" part anyway because they are
under the task's paths.

### 5. Stale bundle directories outside the task (what fails at HEAD vs with this change)
`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -j 2 <ids>` in the snapshot:

| id | at HEAD (git archive, `gen_tests.py --check`) | with T449a | in baseline? |
|---|---|---|---|
| `conformance/p11/e11_5_executors/check_conformance_bundles.test` | FAIL (8 bundles, e.g. `fiber_in_async_and_threads.ax actual=154593 vs expected=159838`) | FAIL, identical | no |
| `perf/p11_executor/check_perf_bundles.test` | FAIL (3 bundles, e.g. `channel_ping_pong.ax actual=171180 vs expected=176425`) | FAIL, identical | no |
| `conformance/p11/e11_6_async_io/check_conformance_bundles.test` | **PASS** | **FAIL** `taskgroup_async_io.ax: out of date (length actual=250213 vs expected=250586)` | no |
| `conformance/p11/e11_3_threads_sync/check_conformance_bundles.test` | PASS | PASS | n/a |

Only the committed e11_6 bundle file `taskgroup_async_io.ax` (a stand-alone bundle, still passes when run) is stale; its
test run is unaffected, only the freshness check fails.

### Findings
- **F1 (caused by this change; handled by routing, not by a code change in T449a):** `conformance/p11/e11_6_async_io/
  check_conformance_bundles.test` passes at HEAD and fails with this change: the new `use std.asyn.waker.waker_leak` lines in
  `std/async/timer.ax` / `timeout.ax` make `taskgroup_async_io.ax` stale by 373 characters. Cannot be fixed inside T449a's
  `paths:` (`tests/conformance/p11/e11_6_async_io` is not owned). The report predicted it (T428d / T428a round 1). Required
  before `taskctl accept`: the orchestrator adds this id to `_workspaces/baseline-failures.txt` with the fix task that
  regenerates the directory (T428a round 1), together with e11_5 and perf/p11_executor below; without that line the accept would
  introduce a failing id outside the baseline.
- **F2 (pre-existing at HEAD, not caused by T449a):** `e11_5_executors/check_conformance_bundles.test` and
  `perf/p11_executor/check_perf_bundles.test` fail identically at HEAD (same 5245-character delta as the 4 fixed dirs; same
  cause) and are not in the baseline. They are candidates for the same T428a r1 / T449b routing; they can adopt
  `bundle_closure.bundle_sources` (`from bundle_closure import bundle_sources`).
- No other findings. No file:line defects in the task's code.

Notes (not FAIL): (a) the `waker_leak` import is a workaround for the lack of a bare `use module` form, the comment in both std files
explains it. (b) bundle sizes shrank (executor bundle 177684 -> 172439 chars) because `std.text.string`/`std.thread` are no
longer bundled; confirmed not imported by any std/async module. (c) `tests/std/async/structured/__pycache__` appears locally after
running the generators and is not in the change set.

### Follow-ups
- F3 (architect, performance): the interpreter run of `waker/cancel_self_waking` grew 60 s -> 144 s (and `join_waker_race` 26 s -> 43 s)
  once the bundle contains the live executor; a performance look at the reactor/timer polling cost per tick under the MIR
  interpreter is worthwhile (the 420 s timeout is headroom, not a fix).
- F4 (harness): `taskgate`'s affected-set rule does not select `cmd:`-based `check_*bundles.test` tests of directories outside the changed
  tests (here e11_5/e11_6/perf); a std change that makes a bundle stale is only caught by the periodic full run unless the QA
  runs the generators by hand as above. T449b (harness regeneration of std bundles) would close that.

### Cleanup
No QA process left running. Mutations of `std/async/timer.ax` and `tests/std/async/reactor/qa_timer_only_import.ax` in the snapshot
were restored (the snapshot `git diff HEAD -- std/async/timer.ax` equals the engineer's 3 inserted lines; the tests pass).

## Files changed
- tests/std/async/reactor/qa_timer_only_import.ax
- tests/std/async/reactor/qa_timeout_only_import.ax
- tests/std/async/structured/qa_bundle_order_check.py
- tests/std/async/structured/qa_bundle_order.test

VERDICT: PASS round=0
