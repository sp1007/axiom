# T423j QA

## Round 0

### Change set (`taskctl.py changes T423j`)
Stages `_workspaces/baseline-failures.txt`, `_workspaces/reports/T423j-report.md`, `tests/link/dll/gnu_ld_run_oracle.py`.
No REFUSED line (the `STATUS:` line in the report is only reported as ignored). Matches the report's `## Files changed`.
`compiler/driver/pipeline.ax` is untouched, so no fixed-point rerun is required (acceptance item is conditional).

### Diff reviewed (snapshot `build-snap-T423j`, Release, `build/axiomc2.exe` from HEAD e71dd6fd)
- Oracle: one entry `("iocp", [win_sys_dir / "iocp.ax"])` added to `provider_specs`, plus a comment. No skip list, no
  exclusion list. `iocp.ax` is the module that defines `__ax_host_aio_*`; this is consistent with the report's root
  cause (the compiler adds providers only for linked exe/dll, not for `--emit=obj`).
- Baseline: the `link/dll/gnu_ld_run.test` line is removed and the comment rewritten. The other admitted line
  (`forbid_unsafe_constructs_neg`) is untouched.

### Checks and evidence
1. `python tools/axtest.py --no-cache -j 2 -v --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal link/dll/gnu_ld_run.test`
   -> `PASS link/dll/gnu_ld_run.test`, `TOTAL 1 PASS 1 FAIL 0`, UNCACHEABLE 1 (no cache), 145 s.
2. Direct run of the oracle: `python tests/link/dll/gnu_ld_run_oracle.py build/axiomc2.exe <tmp> .` ->
   `GNU-LD-RUN-ORACLE ok (1143 native run tests verified)` (before the fix: 5/1143 failed). The oracle compares exit
   code and stdout bytes of the GNU-ld-linked exe with the self-linked PE for every case, so the native leg is a real
   observable check (not an assert-only test).
3. `nm` of the built `axiom_host_rt.lib`: `T __ax_host_aio_close` and `T __ax_host_aio_cancel` are exported.
4. Negative proof (snapshot only): deleted the `iocp` provider line, re-ran the test with `--no-cache` ->
   `FAIL link/dll/gnu_ld_run.test: exit code 1, expected 0` (oracle raises), `TOTAL 1 PASS 0 FAIL 1`.
   Restored the file from the main tree (`git diff HEAD --stat` shows the original +2 lines again).
5. Native-evidence (4a): the task adds no new run tests; the touched oracle is the evidence mechanism and was proven
   live by check 4.
6. taskgate: `python tools/taskgate.py --task T423j --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423j.json`
   (log `_workspaces/T423j_qa_taskgate.log`): exit 0, `TOTAL 63 PASS 63 FAIL 0 SKIP 0 XFAIL 0`, failing ids none,
   archcheck clean (252 files, 0 violations), BASELINE OK, smoke-check OK, 0 UNMATCHED / UNRESOLVED / MAP-NOTE /
   DEFERRED, no CACHE-MISMATCH (cache: 12 miss, verification sample 12/12, mismatch none), WEAK-NATIVE 0 in the task's
   own/changed tests (3 in the run, none from this task).

### Affected-set derivation
Rule `test` (changed file lies in the test's directory): the 5 `tests/link/dll` tests (`gnu_ld_run`, `pe_dll`,
`qa_dll_boundary`, `qa_t431_tls_and_std_reachability_bounds`, `rt_tls_and_std_reachability`), all PASS. `_workspaces/*`
files are no-ops. Smoke: 35 ids across 32 groups (seed 2309164488), including `run/str/hello.ax` (Xin chao),
`ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`, archcheck; all PASS.

### Boundary / adversarial check
Seam: oracle provider archive vs. objects from `--emit=obj`. Beyond the engineer's evidence I inspected the exported
archive symbols (check 3) and removed the new entry to prove the test fails without it (check 4). No duplicate-symbol
conflict between `iocp` and `thread`/`fiber` providers appeared (link succeeded for all 1143 cases). No extra test file
was needed; the oracle itself is the test and was mutated.

### Spec check
Test-infrastructure-only change; no compiler/bootstrap/shared-file edits (pipeline.ax, axtest.py, CMake, codes.def
untouched), no diagnostics, no BOOTSTRAP-SHORTCUT. Lock `_workspaces/baseline-failures.txt` is declared by the task.

### Findings
None.

### Pre-existing failures (not in baseline)
None appeared in this gate's scope (the two known ones, `selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test`
and `selfhost/stage1/stage1_bootstrap.test`, were not selected).

### Files changed
- _workspaces/reports/T423j-qa.md

### Follow-ups
None.

VERDICT: PASS round=0
