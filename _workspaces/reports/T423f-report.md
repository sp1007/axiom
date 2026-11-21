# T423f report - `build_axiomc.py` seeded bootstrap falls back to the full chain

## Summary
`python tools/build_axiomc.py --out <dir>` no longer dies with `bootstrap: FAIL seeded A` when the cached seed cannot
type-check the new compiler/std sources (new host intrinsic, new syntax). When the seed was chosen by `auto`, the same
invocation prints `bootstrap: seeded A failed, falling back to full chain` and reruns the full `axiom0 -> c1 -> c2`
chain (stage 1 is reused); the resulting compiler is stored in the compiler cache and is the next seed, exactly as a
cache-miss full chain does today. An explicit `--seed <path>` still fails hard.

## Design / decisions
- Implemented entirely in `tools/build_axiomc.py` (`run_bootstrap`, `_StderrTee`); `tools/bootstrap.py` is not in this
  task's paths and is unchanged. The failure is recognised by its stable stderr line `bootstrap: FAIL seeded A`
  (printed by `run_seeded_for_opt` for the A stage only); stderr is tee'd, so the original diagnostics stay visible.
- Fallback eligibility: `eff_seed == "auto"` (default selection, or a literal `--seed auto`: same policy, decided here)
  and not `--full-chain` / `--trust-root`. An explicit path is never retried.
- Only seeded A falls back. A failure of seeded B (A -> B), C, the B == C fixed point or the stage-0 smoke parity guard is
  a real compiler bug/non-determinism and keeps failing (tests prove this). A stage-1 failure happens before any seed is
  used and is not retried either.
- The rerun is `bootstrap.main(<same argv> without --seed, plus --full-chain)`: same `--reuse-existing`, same cache dir,
  so stage 1 is `REUSED` and the full-chain result is published to the cache by the existing code path.
- If the full chain itself fails, its non-zero rc is returned (both failures are on stderr).

## Tests (`tests/tools/build_axiomc_fallback/*.test`, driver `driver.py`; seconds, no compiler)
`driver.py <scenario>` builds a fake repo, fakes `bootstrap.run_stage_build` (a stage can fail with a compile error),
fakes the stage-0 builder and the final `version` smoke, and calls `build_axiomc.main` end to end with a private cache.
Each manifest is a `cmd:` test with `cache-inputs:` (build_axiomc.py, bootstrap.py, driver.py), exact `stdout: OK <name>`.
- `auto_seed_fails` - default seed fails on A: notice exactly once, rc 0, calls `stage1, seedA, stage2`, new seed cached,
  a following build is seeded again without fallback.
- `auto_literal_seed_fails` - literal `--seed auto` behaves the same.
- `explicit_seed_fails` - explicit `--seed <path>` fails: rc != 0, no notice, no full chain, cache untouched.
- `seed_works` - working seed: `seedA, stage2, stage3`, no notice, `[seeded B==C]`.
- `later_seeded_stage_failure_is_not_retried` - A ok, B fails: rc != 0, no notice, no full chain.
- `stage1_failure_is_not_a_seed_failure` - stage-1 failure: rc != 0, no notice.
- `fallback_then_chain_stage_fails` - A fails, full chain stage 2 fails: one notice, rc != 0, nothing published.
- `full_chain_never_falls_back` - `--full-chain`: no seed lookup, no notice.
Liveness proof (mutation, main tree, restored afterwards): forcing `fallback_ok = False` makes `auto_seed_fails` and
`auto_literal_seed_fails` FAIL (rc=1); forcing fallback for every seed makes `explicit_seed_fails` FAIL (rc=0 instead of
non-zero) while `later_seeded_stage_failure_is_not_retried` still passes (marker check is A-only).

## Evidence
- `python tools/axtest.py --filter tools/build_axiomc_fallback --no-cache -j 2`: `TOTAL 8 PASS 8 FAIL 0`.
- `python -m unittest discover -s tools/tests/build_axiomc`: 41 tests OK (existing T444c/T487 self-tests unchanged).
- Real stale seed, in the snapshot (stage 0 built clang Release by `build_axiomc.py`; private cache holding the oldest
  cached O1 compiler `axiomc2_O1_641e71e2ac2ed37f.exe`):
  `python tools/build_axiomc.py --out build --cache-dir seedcache` (6m41s total):
  ```
  STAGE1 OK: ...axiomc1.exe (29286912 bytes, wall=183.55s)
  SEED: hit ...seedcache\axiomc2_O1_641e71e2ac2ed37f.exe (cache hit ...)
  bootstrap: FAIL seeded A (O1, seed -> A) rc=1        (stderr; error[AX_TYPE_UNKNOWN_INTRINSIC] x4: host.fiber_*)
  bootstrap: seeded A failed, falling back to full chain
  REUSED ...axiomc1.exe
  STAGE2 (O1) OK: ...dir_stage2_O1\axiomc2.exe (8821248 bytes, wall=138.46s)
  BUILD-AXIOMC OK: ...axiomc2.exe size=8821248 sha256=87f4350e...
  ```
  and the new compiler was added to the cache (`seedcache/axiomc2_O1_b64ea0de4626c290.exe`).
- Same stale seed passed explicitly (`--seed seedcache/axiomc2_O1_641e71e2ac2ed37f.exe`, fresh out dir):
  `bootstrap: FAIL seeded A ... rc=1`, no fallback line, process exit 1.
- Gate (`python tools/taskgate.py --task T423f --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
  in `build-snap-T423f`): exit 0; own 8, affected 8 (rule: `cache-inputs:` of the own tests; tool self-tests
  `tools/tests/build_axiomc` because `tools/build_axiomc.py` changed), smoke 31 ids (all groups); `TOTAL 58 PASS 58 FAIL 0`;
  archcheck clean (232 files, 0 violations); self-tests PASS (41); BASELINE OK; WEAK-NATIVE 0 in own/changed tests; no
  UNMATCHED source files (the unmatched list holds only snapshot scratch: `seedcache/`, `taskgate-T423f.log`).
  The tests are Python `cmd:` tests, so the native-evidence rule (step 4a) does not apply to them.

## Follow-ups for the architect
- `tests/tools/` is a new top-level test group. `python tools/axtest.py --smoke --check` reports `group tools has no pool
  entry` (it already reports `group build_native has no pool entry`, so the check was failing before this task).
  `tests/smoke.list` is outside this task's paths; suggested line: `pool tools: tools/build_axiomc_fallback/seed_works.test`
  (and a `build_native` pool line). The gate itself is not affected (smoke draws only from existing pools).
- `bootstrap.py` prints the failure on stderr only; the fallback relies on the text `bootstrap: FAIL seeded A`. If that
  message is ever reworded, `auto_seed_fails` fails loudly (it asserts the notice), so the coupling is guarded.

## Files changed
- tools/build_axiomc.py
- tests/tools/build_axiomc_fallback/driver.py
- tests/tools/build_axiomc_fallback/auto_seed_fails.test
- tests/tools/build_axiomc_fallback/auto_literal_seed_fails.test
- tests/tools/build_axiomc_fallback/explicit_seed_fails.test
- tests/tools/build_axiomc_fallback/seed_works.test
- tests/tools/build_axiomc_fallback/later_seeded_stage_failure_is_not_retried.test
- tests/tools/build_axiomc_fallback/stage1_failure_is_not_a_seed_failure.test
- tests/tools/build_axiomc_fallback/fallback_then_chain_stage_fails.test
- tests/tools/build_axiomc_fallback/full_chain_never_falls_back.test

STATUS: COMPLETE round=0
