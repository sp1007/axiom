# T423f QA

## Round 0

Scope: `tools/build_axiomc.py` seeded-A fallback to the full chain + 8 `tests/tools/build_axiomc_fallback/*` tests. All
building/testing was done inside `build-snap-T423f/` (HEAD 5e38733 + this change set), `-j 2`, no broad process kills.

### Checks and evidence
1. Change set: `taskctl.py changes T423f` lists the report, 8 tests, driver and `tools/build_axiomc.py`; no generated
   bundles listed. The only REFUSED line is for my own added test (see "Files changed" below), resolved by listing it there.
   `harness_check.py`: HARNESS OK.
2. Marker coupling: `tools/bootstrap.py:1015` prints exactly `bootstrap: FAIL seeded A (%s, seed -> A) rc=%d` to
   `sys.stderr` (resolved at call time, so the tee in `run_bootstrap` sees it); B/C/fixed-point messages are
   `FAIL seeded B` (1059), `FAIL seeded C` (1113), `FAIL seeded fixed-point mismatch` (1137), so the marker with the
   trailing ` A` is unambiguous and A-only. `bootstrap.py` is unchanged in the snapshot (diff empty). The tests drive the REAL
   `bootstrap.main` (only `run_stage_build`, bundle loader, stage-0 builder and the final `version` smoke are faked), so a
   rewording of the line in `bootstrap.py` makes `auto_seed_fails` fail loudly: the coupling is guarded, not fragile.
   Residual (note, not a finding): a seed binary that crashes or times out on stage A also takes the fallback; that is
   the intended and safe outcome (the full chain result is what is cached).
3. Eligibility logic read: `fallback_ok = eff_seed == "auto" and not --full-chain and not --trust-root`; `--force` leaves
   `eff_seed` unset, so no seeded stage exists. Explicit `--seed <path>` -> `fallback_ok False` -> `bootstrap.main` rc
   returned unchanged. The rerun drops `--seed`, adds `--full-chain`, keeps `--reuse-existing`/cache dir, so the existing
   publish-to-cache path makes the fallback result the next seed (asserted: cache grows 1 -> 2 and a third build is
   seeded again without notice). Stage-1 / later-stage / smoke-guard failures are not retried (tests below).
4. New tests: `python tools/axtest.py --filter tools/build_axiomc_fallback --no-cache -j 2` -> `TOTAL 8 PASS 8` (12 s).
   Existing self-tests: `python -m unittest discover -s tools/tests/build_axiomc` -> 41 OK.
5. Mutations (snapshot only, restored and diffed against the main tree afterwards):
   - M1 `fallback_ok = False` -> `auto_seed_fails`, `auto_literal_seed_fails`, `fallback_then_chain_stage_fails` FAIL (3/8).
   - M2 `fallback_ok = bool(eff_seed)` (explicit seeds fall back) -> `explicit_seed_fails` FAIL.
   - M3 marker `"bootstrap: FAIL seeded"` (any seeded stage) -> `later_seeded_stage_failure_is_not_retried` FAIL.
   - M4 marker `"bootstrap: FAIL"` (any bootstrap failure) -> `later_seeded_stage_failure_is_not_retried` and
     `stage1_failure_is_not_a_seed_failure` FAIL.
   Every behavioural requirement of the focus list is therefore pinned by at least one test that goes red when violated.
6. Adversarial test added (not in the engineer's set): `force_never_seeds_or_falls_back` -- `--force` after a primed cache
   with a seed that would fail on A: no `SEED:` line, no notice, calls `stage1, stage2` only, rc 0. Passes.
7. Real stale-seed end-to-end: not re-run (7 min); the engineer's log in the report shows the real sequence (seed hit,
   `FAIL seeded A` with `AX_TYPE_UNKNOWN_INTRINSIC` for `host.fiber_*`, notice, `REUSED axiomc1`, `STAGE2 (O1) OK`, new
   cache entry) and the explicit-seed run failing with exit 1. The scripted equivalent (items 4-5) exercises the same code
   path through the real `bootstrap.main`; accepted as evidence.
8. Taskgate (inside the snapshot, after refreshing it with the added test):
   `python tools/taskgate.py --task T423f --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423f.json`
   exit 0, 40 s: own+affected 9 ids (`tools` group, rule: `cache-inputs:`), tool self-tests `tools/tests/build_axiomc`
   `tools` changed, smoke 29 groups (seed 1823197350, always-includes run/str/hello.ax, ui/typeck/type_unknown.ax,
   diff/002-arithmetic.ax), `TOTAL 61 PASS 61 FAIL 0`, `Failing ids: none`, BASELINE OK, archcheck clean (232 files, 0
   violations), self-tests PASS (41), no unmatched files, WEAK-NATIVE 0 in the task's own/changed tests (3 elsewhere in the
   smoke run, unrelated), `CACHE-MISMATCH` none (miss 16, dep_source exact). Full log: `_workspaces/T423f_qa_taskgate.log`.
   The tests are Python `cmd:` tests with exact stdout and a non-zero-exit/negative case each, so step 4a (native
   evidence) does not apply; liveness is proven by the mutations above.

### Findings
None blocking.

### Notes / follow-ups
- `tests/smoke.list` lacks a `tools` pool entry (`axtest.py --smoke --check` reports `group tools has no pool entry`; it
  already reports `build_native` before this task, so the check was already red). Judged a follow-up, not a gate finding:
  the gate draws only from existing pools, `tests/smoke.list` is outside this task's paths, and nothing fails. Suggested for
  the architect: add `pool tools: tools/build_axiomc_fallback/seed_works.test` (and a `build_native` line) to `tests/smoke.list`.
- Cache note: the `.test` manifests declare `cache-inputs:` for build_axiomc.py, bootstrap.py and driver.py, which is correct
  since the driver imports both tools.

## Files changed
- tests/tools/build_axiomc_fallback/driver.py
- tests/tools/build_axiomc_fallback/force_never_seeds_or_falls_back.test

VERDICT: PASS round=0
