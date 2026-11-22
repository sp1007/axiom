# T423g report - smoke pools for `build_native` and `tools`; the gate reports `--smoke --check`

## Summary
`python tools/axtest.py --smoke --check` failed with `group build_native has no pool entry` and `group tools has no pool
entry`. Both pools are added and the check now prints `SMOKE-CHECK OK` (worst-case estimate 24 s, bound 1200 s, durations
recorded). `tools/taskgate.py` now runs the same check as part of every gate, prints its result, and fails the gate when
the change set ADDS a top-level `tests/<group>/` that has no pool entry. Only these two groups were reported by
`--smoke --check` (tests/modules/std_on_demand, tests/run/mem_generic_array, tests/run/own_index_moved,
tests/tools/build_axiomc_fallback are subdirectories of groups that already have pools, so nothing to add).

## Design / decisions
- `tests/smoke.list`: `pool build_native:` `build_native/qa_assert_and_backedge_fixups.ax` and
  `build_native/stress_4096_jumps.ax` (both 120 s timeout, but the recorded duration is small; the check bound holds);
  `pool tools:` `tools/build_axiomc_fallback/seed_works.test` and `.../stage1_failure_is_not_a_seed_failure.test` (fake stage
  driver, milliseconds, `cache-inputs:` declared, 60 s timeout).
- `tools/taskgate.py`: new `smoke_hygiene(root, tests, durations, changed, base_ref, known_at_base)` calls
  `axtest_affected.smoke_check` in-process (same code as `axtest.py --smoke --check`) and returns problems, notes, estimate,
  and `new_groups_without_pool`. A group is "new" when it appears in the change set (`tests/<g>/...`) and has no tracked file
  at the base ref (`HEAD`, or the base of `--range BASE..HEAD`; `git ls-tree`). Only new groups without a pool produce a gate
  `reasons` entry (exit 1) naming the group and the fix (`pool <g>: <light test id>`). Any other problem (also a pre-existing
  gap, a bad id, a bound overrun) is printed as `SMOKE-CHECK PROBLEM ...` but does not fail an unrelated task. When git cannot
  tell, the group is not treated as new (conservative, never a false failure). The result is in the JSON (`smoke_check`) and in
  the Markdown block (`markdown_smoke_lines`: line `smoke-check (tests/smoke.list): ...`).
- The smoke draw algorithm and `axtest.py` are untouched.

## Tests (`tests/tools/taskgate_smoke_check/*.test`, driver `driver.py`; a fake git repo per scenario, seconds, no compiler)
`cache-inputs:` name taskgate/axtest/axtest_affected/axtest_cache and the driver; exact `stdout: OK <scenario>\n`.
- `healthy_change_passes` - healthy list, change in a pooled group: ok, no gate reason.
- `new_group_without_pool_fails` - a new `tests/newgrp/` without a pool: problem reported, `new_groups_without_pool == [newgrp]`,
  failure message names the group and the `pool newgrp:` fix.
- `new_group_with_pool_passes` - the same group with its pool line passes.
- `preexisting_gap_is_printed_not_failing` - a group without pool that already exists at HEAD is reported, gate not failed.
- `range_base_decides_newness` - same group is new relative to `HEAD~1`, known relative to `HEAD`.
- `markdown_names_problems` - the Markdown lines contain `SMOKE-CHECK PROBLEM group newgrp has no pool entry` and `NEW-GROUP`.
Liveness proof (snapshot only, restored): replacing the `new_missing = [...]` line by `new_missing = []` makes
`driver.py new_group_without_pool_fails` fail (rc=1, `FAIL new_group_without_pool_fails: []`); restored, it prints OK.

## Evidence (inside `build-snap-T423g`)
- `python tools/axtest.py --smoke --check` -> `SMOKE-CHECK worst-case estimate 24 s ... SMOKE-CHECK OK`.
- `python tools/taskgate.py --task T423g --compiler ../build/axiomc2.exe --build-dir ../build --exclude-requires axiom0-internal -j 2 --seed 7`
  (logs `_workspaces/T423g_taskgate.log`, `_workspaces/T423g_taskgate2.log`): `TOTAL 61 PASS 58 FAIL 3`; the 6 own tests PASS; tool
  self-tests `tools/tests/taskgate` PASS (44 tests, 0 failures, taskgate normal flow still works); archcheck clean (0 violations);
  `smoke-check (tests/smoke.list): OK; est. worst-case draw 109 s`. The smoke draw includes a pick of both new pools
  (`build_native/stress_4096_jumps.ax` native PASS, `tools/build_axiomc_fallback/seed_works.test` PASS).
- Compiler caveat: the snapshot has no build of its own; the gate used the main-tree `build/axiomc2.exe` (this task changes no
  compiler/std file, only tools and tests).
- The 3 remaining failures are NOT caused by this task: `hir/basic.ax`, `resolve/simple.ax` (golden mismatch) and
  `obj/determinism/string_symbols.test` (`AX_TYPE_UNKNOWN_INTRINSIC`, stale main-tree `axiomc2.exe` older than HEAD std). They are
  untouched by the change set and fail identically with `--no-cache` on the unmodified tests with that compiler.

## Follow-ups
- `tests/smoke.list` header says the `hir`/`parse`/`resolve` pools hold ids from `_workspaces/baseline-failures.txt`; that file
  currently has no `hir/basic.ax`/`resolve/simple.ax` entry, so they only fail with a compiler that is out of date. Architect to
  confirm the pools and the baseline are still intended as described.
- The gate for tasks that add `tests/<group>/` now requires the pool line in `tests/smoke.list`; that file is an unlisted
  shared file for such tasks (add it to their `paths:`).

## Files changed
- tests/smoke.list
- tools/taskgate.py
- tests/tools/taskgate_smoke_check/driver.py
- tests/tools/taskgate_smoke_check/healthy_change_passes.test
- tests/tools/taskgate_smoke_check/markdown_names_problems.test
- tests/tools/taskgate_smoke_check/new_group_with_pool_passes.test
- tests/tools/taskgate_smoke_check/new_group_without_pool_fails.test
- tests/tools/taskgate_smoke_check/preexisting_gap_is_printed_not_failing.test
- tests/tools/taskgate_smoke_check/range_base_decides_newness.test

STATUS: COMPLETE round=0
