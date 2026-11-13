# T440 report

## Summary

All 8 `undiagnosed:maybe-timeout` ids are **(b) load-only timeouts inside the oracle**, not compiler/std defects and
not oracle logic bugs. Every oracle passes alone; the failure is the oracle's own fixed per-step
`subprocess.run(..., timeout=180)` on the bundled `--interp` probe step (a whole compiler-module bundle interpreted:
68-145 s alone on the shared machine, i.e. 40-80 % of the 180 s limit). Under `-j 2` plus the other agents' load
that step crosses 180 s, `subprocess.TimeoutExpired` escapes `main()` and the runner shows the Python traceback seen
in T422-qa section 7. Reproduced before the fix: `e18_3` failed with the traceback after 180.6 s (axtest recorded
duration 180 568 ms = the 180 s step limit + start-up), the other 7 passed in that draw (which ids hit the limit
depends on the load at that moment).

Runner `--timeout-scale` could not help: it scales only the runner's own step timeout (the manifest `timeout:
900`), and `tools/axtest.py` passes nothing to the command, so the oracle's inner limits stayed at 180 s.

### Fix (oracle side only; `tools/axtest.py` is out of scope)
Each of the 8 oracles now has one **load-aware wall-clock budget** instead of fixed per-step timeouts
(identical helper block, placed before `main()`):
- `ORACLE_BUDGET_S` = 3 x the slowest wall time of the whole oracle measured at scale 1 in this task
  (alone run (a) and the pre-fix `-j 2` run (c0); table below), rounded down.
- multiplied by `AXTEST_TIMEOUT_SCALE` (env, default 1, invalid/<=0 -> 1); documented in the block header. This is
  the single env variable the task allows when the runner passes nothing; a follow-up asks the runner to export it.
- `bounded_run()` gives every subprocess step the time left until the shared deadline; a hang anywhere ends the run
  at the deadline (bounded, no infinite wait) with one line `TIMEOUT: <step> killed after Ns (budget B s x scale S)`
  and exit 1 (`guarded_main`), never a traceback.
- The manifest `timeout:` is kept above the budget (budget + >= 120 s) so the oracle reports first: raised for
  e18_2 (900 -> 960), e18_3 (900 -> 1130), e20_2 (900 -> 1530); the other five keep 900 (budget + 120 <= 900).
- One shared budget rather than per-step limits: the per-step times are dominated by one step (interp) whose share
  varies with load, and the tiny fixture steps (0.1-0.6 s) cannot sensibly get "3x measured" limits of 1-2 s on a
  loaded machine; a whole-oracle budget satisfies "<= 3x measured" exactly and still bounds every hang.

Negative proof of the timeout path (snapshot, e19_4):
- `AXTEST_TIMEOUT_SCALE=0.01` -> `TIMEOUT: budget exhausted before \`axiomc2.exe run --interp\`` rc=1, 6 s.
- `AXTEST_TIMEOUT_SCALE=0.05` -> `TIMEOUT: \`axiomc2.exe run --interp\` killed after 16s (budget 315s x scale 0.05)`
  rc=1, 16 s; afterwards no `axiomc2.exe` from `build-snap-T440` was left running (wmic count 0).
- `AXTEST_TIMEOUT_SCALE=bogus` -> scale 1.0 (lsp_vfs: budget 495).

### Per-id table
Compiler: `build-snap-T440/build/axiomc2.exe`, a byte copy (SHA-256 A21AEE32...0E89) of
`build-snap-T421a/build/axiomc2.exe` built 2026-11-13 18:18; the last commit touching `compiler/` or `bootstrap/`
is e0637c50 (16:42), and the commits after it (T438, T439, harness, T421a) touch only C tests, tools tests and
`std/async`, so it is HEAD-equivalent for `compiler/` at 7d84ada, the snapshot base of every measurement in this report.
After the last run, T437b was accepted (HEAD 961962d: `--dep-file` in `compiler/driver`, regenerated selfhost
bundles, `tests/selfhost/bundle_common.py`); the final snapshot refresh moved `build-snap-T440` to 961962d, so the
round-1 gate should use a stage-2 `axiomc2` of 961962d (this task's copy predates `--dep-file`). No compiler was
built by this task. Machine: 4 cores, 61-83 % CPU from other agents (T421a gate `-j 2`, T437b) during every run;
there was no idle window, so (a) "alone" = this id alone, the other agents still running.

Wall times in seconds. (a) = oracle alone, run directly with step timing (`timewrap.py`, unmodified oracle);
(c0) = pre-fix `axtest -j 2 --no-cache` over the 8 ids; (c1)-(c3) = post-fix, same command, three consecutive runs;
(b) = alone with `--timeout-scale 6` + `AXTEST_TIMEOUT_SCALE=6`. Slowest step = the step closest to its old limit.

| id | (a) alone | slowest step in (a) (old limit) | (c0) pre-fix -j 2 | budget (s) | (c1) | (c2) | (c3) | (b) | root cause | action |
|---|---|---|---|---|---|---|---|---|---|---|
| e18_1_query_engine | 161 PASS | interp 95.5 (180) | 157 PASS | 483 | 152 PASS | 151 PASS | 158 PASS | 139 PASS | load-only: interp step near 180 s limit | budget, line removed |
| e18_2_incremental | 214 PASS | interp 109.9 (180) | 278 PASS | 834 | 239 PASS | 268 PASS | 292 PASS | 206 PASS | load-only | budget, timeout 960, line removed |
| e18_3_parallel | 334 PASS | interp 144.5 (180) | **181 FAIL** (TimeoutExpired traceback at the 180 s interp step) | 1002 | 356 PASS | 422 PASS | 365 PASS | 383 PASS | load-only (reproduced) | budget, timeout 1130, line removed |
| e19_1_lsp_server | 143 PASS | interp 122.1 (180) | 170 PASS | 510 | 146 PASS | 199 PASS | 185 PASS | 168 PASS | load-only | budget, line removed |
| e19_2_formatter | 142 PASS | interp 88.7 (180); -O0 build 52.4 (120) | 173 PASS | 519 | 150 PASS | 201 PASS | 174 PASS | 185 PASS | load-only | budget, line removed |
| e19_4_diagnostics_ai | 90 PASS | interp 68.2 (180) | 105 PASS | 315 | 110 PASS | 99 PASS | 133 PASS | 99 PASS | load-only | budget, line removed |
| e20_2_package_manager_lockfile | 444 PASS | interp 126.6 (180); -O2 build 124.7 (240) | 469 PASS | 1407 | 453 PASS | 522 PASS | 479 PASS | 427 PASS | load-only | budget, timeout 1530, line removed |
| run/lsp_vfs/lsp_vfs_engine | 165 PASS | interp 94.4 (180) | 165 PASS | 495 | 142 PASS | 147 PASS | 210 PASS | 151 PASS | load-only | budget, line removed |

Run totals (wall of the whole `-j 2` run): c0 1025 s (TOTAL 8 PASS 7 FAIL 1), c1 935 s (8/8), c2 1024 s (8/8),
c3 1056 s (8/8); (b) run 1761 s (`-j 1`, 8/8). c1, c2, c3 are three consecutive runs with the final code
(2026-11-13 20:03-20:53, `axtest -j 2 --no-cache`, the T421a/T437b agents loading the machine); (b) ran 2026-11-14
00:12-00:41 (`-j 1 --timeout-scale 6`, `AXTEST_TIMEOUT_SCALE=6`, another gate running, CPU 85 %).
Budgets are 3 x the (a)/(c0) maximum, so none exceeds 3x a measured time. Headroom against the slowest time seen in
any run (budget / max): e18_1 483/161 = 3.0, e18_2 834/292 = 2.86, e18_3 1002/422 = 2.37, e19_1 510/199 = 2.56,
e19_2 519/201 = 2.58, e19_4 315/133 = 2.37, e20_2 1407/522 = 2.70, lsp_vfs 495/210 = 2.36: every oracle keeps
>= 2.3x margin over the worst loaded run observed (the old fixed 180 s interp limit had 1.2x at worst in (a)).
`e18_1` rc 143 in T422-qa (the interp child itself returned 143 = 128 + SIGTERM, not a Python `TimeoutExpired`):
not reproduced in any run here (e18_1 passed in all 6 runs: a, c0, c1, c2, c3, b); it points to an external termination of that process
during the loaded T422 gate, not to a compiler defect (no compiler code path exits 143). If it ever recurs, the
oracle now prints the child's stdout/stderr unchanged and a timeout prints a `TIMEOUT:` line, so the two cases are
distinguishable.

### Mutation proof (snapshot only, restored afterwards)
Command: `python <scratchpad>/mutate.py D:/projects/compiler/new lang/build-snap-T440` (2026-11-14 04:12-04:29).
For each oracle the last line of `EXPECTED_PROBE_STDOUT` was changed `...PASS\n` -> `...PASX\n` in the snapshot
copy, the oracle was run directly with the snapshot compiler, then the original bytes were written back
(`restored=True` = byte-identical; afterwards every changed `tests/` file of the snapshot has the same SHA-256 as
the main tree). The same constant is the expectation of the native `-O0/-O1/-O2` legs (exact stdout compare), so
the probe check is live for every mode; interp is simply the first leg to see it.

| oracle | rc | time | message |
|---|---|---|---|
| e18_1 | 1 | 111 s | `stdout mismatch for e18_1_query_engine_probe under --interp` |
| e18_2 | 1 | 162 s | `FAIL: --interp stdout mismatch` |
| e18_3 | 1 | 191 s | `FAIL: --interp stdout mismatch` |
| e19_1 | 1 | 132 s | `stdout mismatch for e19_1_lsp_server_probe under --interp` |
| e19_2 | 1 | 97 s | `stdout mismatch for e19_2_formatter_probe under --interp` |
| e19_4 | 1 | 77 s | `stdout mismatch for e19_4_diagnostics_ai_probe under --interp` |
| e20_2 | 1 | 184 s | `stdout mismatch for e20_2 probe under --interp` |
| lsp_vfs | 1 | 124 s | `stdout mismatch for lsp_vfs_probe under --interp` |

Timeout path (also re-checked by QA round 0): `AXTEST_TIMEOUT_SCALE=0.05` on e19_4 ->
`TIMEOUT: \`axiomc2.exe run --interp\` killed after 16s (budget 315s x scale 0.05)`, exit 1, no `axiomc2.exe` of
`build-snap-T440` left running; `0.01` -> `TIMEOUT: budget exhausted before ...`, exit 1; `bogus` -> scale 1.

## Files changed
- tests/conformance/p18/e18_1_query_engine/e18_1_query_engine_oracle.py
- tests/conformance/p18/e18_2_incremental/e18_2_incremental_oracle.py
- tests/conformance/p18/e18_2_incremental/e18_2_incremental_oracle.test
- tests/conformance/p18/e18_3_parallel/e18_3_parallel_oracle.py
- tests/conformance/p18/e18_3_parallel/e18_3_parallel_oracle.test
- tests/conformance/p19/e19_1_lsp_server/e19_1_lsp_server_oracle.py
- tests/conformance/p19/e19_2_formatter/e19_2_formatter_oracle.py
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_oracle.py
- tests/conformance/p20/e20_2_package_manager_lockfile/e20_2_package_manager_lockfile_oracle.py
- tests/conformance/p20/e20_2_package_manager_lockfile/e20_2_package_manager_lockfile_oracle.test
- tests/run/lsp_vfs/lsp_vfs_oracle.py
- _workspaces/baseline-failures.txt
- _workspaces/reports/T440-report.md

## Tests
All inside `build-snap-T440` (HEAD 7d84ada + the T440 changes), compiler `build/axiomc2.exe` (see above), id list
= the 8 ids, `--exclude-requires axiom0-internal`, `--build-dir build`, results as JSON (scratchpad `runs/c_*.json`):
- (a) each oracle alone via `timewrap.py` (step timing), unmodified code: 8/8 PASS (2026-11-13 19:13-19:53).
- (c0) pre-fix `python tools/axtest.py --compiler build/axiomc2.exe ... --no-cache -j 2 --id-file ids.txt`:
  `TOTAL 8 PASS 7 FAIL 1` (e18_3 TimeoutExpired traceback after 180.6 s).
- (c1) same command, post-fix: `TOTAL 8 PASS 8 FAIL 0 SKIP 0 XFAIL 0` (935 s).
- (c2) `TOTAL 8 PASS 8 FAIL 0 SKIP 0 XFAIL 0` (1024 s).
- (c3) `TOTAL 8 PASS 8 FAIL 0 SKIP 0 XFAIL 0` (1056 s). c1-c3 are the three consecutive `-j 2` passes the
  acceptance asks for; they finished before the usage-limit interruption, so round 1 did not repeat them.
- (b) `AXTEST_TIMEOUT_SCALE=6 ... -j 1 --timeout-scale 6`: `TOTAL 8 PASS 8 FAIL 0 SKIP 0 XFAIL 0` (1761 s).
  (A first (b) attempt at 20:53 was killed by the session interruption after 165 s: empty log, rc 127; it is not a
  test result and was simply re-run.)
- Mutation proof 8/8 FAIL as expected, timeout-path proof: see the section above.
- `py_compile` of the 8 edited oracles: OK. Gate scope (taskgate, smoke) is QA's.

Baseline: the 8 `T440 undiagnosed:maybe-timeout` lines and their `# --- T440 ...` header are removed from
`_workspaces/baseline-failures.txt` (no id stays: none is a compiler/std defect).
Architect inbox: QA's four notes (runner does not export `AXTEST_TIMEOUT_SCALE`; whole-oracle budget up to 1407 s
for e20_2; helper copied 8 times and e19_3/e19_5/e18_5/e18_6 still fixed; no `nocache:`/`cache-inputs:`) were
appended to `_workspaces/architect-inbox.txt` as 4 `T440 follow-up` lines. That file is shared, outside this task's
`paths:`/`locks:` and already carries other agents' uncommitted lines, so it is deliberately NOT listed under
`## Files changed` (the orchestrator/architect processes the inbox).

## Notes / decisions
- `selfhost/ast/qa_ast_*` (T422-qa): their failing step is the runner's own `axiom0 build` step with the 10 s
  default, which `--timeout-scale` already multiplies, so the existing rule (re-run alone with `--timeout-scale 6`)
  covers them; the env variable of this task is only needed for timeouts a test enforces itself (like these
  oracles). No edit there.
- The edit was applied by a one-shot script (`subprocess.run(` -> `bounded_run(`, per-step `timeout=` literals and
  the `timeout` parameter of `run_cmd` removed, helper inserted before `main()`, `main()` wrapped); every file was
  `py_compile`d and the diff reviewed. `e20_2`'s `git show HEAD:std/core/host.ax` (`check_output`, no timeout,
  0.1 s) is unchanged.

## Follow-ups (for the architect)
1. `tools/axtest.py` `program_env()` should export `AXTEST_TIMEOUT_SCALE=<--timeout-scale>` to every command it
   runs (one line), so the gate rule "re-run with `--timeout-scale 6`" also reaches oracle budgets. Until then a
   QA re-run must set `AXTEST_TIMEOUT_SCALE=6` in the environment as well (axiom-qa.md / axiom-testing wording).
2. The same fixed `timeout=180` per-step pattern exists in other oracles not on the baseline today:
   `e19_3_refactoring_vcs`, `e19_5_docgen_test_ux`, `e18_5_pass_contracts` (300), `e18_6_separate_compilation`;
   they will flake the same way under load. Move the helper into one shared module (e.g. next to
   `tests/selfhost/bundle_common.py`, locked by T437b now) and use it there.
3. Cache hygiene (ADR-0042 G1): these 8 oracles read `compiler/`, `std/` and `tests/selfhost/bundle_common.py` at
   run time but declare neither `nocache:` nor `cache-inputs:`; a cached PASS could survive a change of a bundled
   compiler module. T437b's `--dep-file` is the planned exact fix; until then they should be `nocache:` or list
   `cache-inputs:`. Not changed here (the ids were run with `--no-cache`).
4. `e18_2`/`e18_3` write their artifacts into `<build>/axtest_out/` instead of `{tmp}`; harmless today (one run at
   a time per snapshot), noted for hermeticity.

STATUS: COMPLETE round=1
