# T423g QA

## Round 0

Gate run in snapshot `build-snap-T423g/` only (last commit 25bd1a05 + exactly the task's change set). Snapshot compiler built there:
`python tools/build_axiomc.py --out build --stage 3` -> BUILD-AXIOMC OK, fixed point axiomc2_O1 == axiomc3_O1.
`taskctl changes T423g` lists 9 stage lines (report, smoke.list, taskgate.py, 7 files under tests/tools/taskgate_smoke_check); no REFUSED
line (only an "ignored line" notice for the `STATUS:` line in the report, harmless).

### Focus checks
1. New-group-only failure.
   - Six scenario tests (`driver.py <scenario>`) all print OK.
   - Mutation A: `new_missing = []` -> `new_group_without_pool_fails` FAIL (rc=1) and `range_base_decides_newness` FAIL.
   - Mutation B: drop the `known_at_base(g) is False` condition -> `preexisting_gap_is_printed_not_failing` FAIL.
   - Both restored byte-identical (cmp), scenarios OK again.
   - End to end: temp `tests/zznewgrp/a.ax` with a `--changed` list -> taskgate exit=1, reason names the group and the `pool zznewgrp: <light test id>` fix;
     the problem is printed as `SMOKE-CHECK PROBLEM group zznewgrp has no pool entry`. Temp dir removed.
   - Pre-existing gap: unit scenario shows it is reported and not a gate reason. Conservative when git cannot tell (None -> not new).
2. Normal tasks not broken.
   - taskgate on this task's change set with the snapshot compiler: `TOTAL 61 PASS 61 FAIL 0`, archcheck clean, baseline OK,
     tool self-tests PASS, `smoke-check ... OK`, exit 0. The 3 failures the engineer saw (hir/basic.ax, resolve/simple.ax,
     obj/determinism/string_symbols.test) were artifacts of the stale main-tree compiler: they pass with the snapshot compiler (hir=basic, resolve=simple, obj=string_symbols were drawn and passed).
   - Synthetic change set touching an existing group only (tests/lex): `TOTAL 62 PASS 62`, exit 0.
3. `python tools/axtest.py --smoke --check` -> `SMOKE-CHECK OK` (worst-case estimate 109 s, bound 1200 s). The 4 new pool ids
   (build_native/qa_assert_and_backedge_fixups.ax, build_native/stress_4096_jumps.ax, tools/build_axiomc_fallback/seed_works.test,
   tools/build_axiomc_fallback/stage1_failure_is_not_a_seed_failure.test) exist and pass (`--no-cache`: TOTAL 8 PASS 8, interp + native).
4. `tools/tests/taskgate/run_selftests.py` -> SELFTEST 44 tests, 0 failures.

No spec/docs/compiler files are touched; the smoke draw algorithm and axtest.py are unchanged. Acceptance bullets all met.

### Follow-ups (not FAIL)
- F1 (stale header): `tests/smoke.list` header says the hir/parse/resolve pools hold ids from `_workspaces/baseline-failures.txt`;
  the baseline has no `hir/`, `parse/`, `resolve/` entries any more. Architect: update the header comment (comment-only edit).
- F2 (needs orchestrator/architect action): a task that adds a NEW top-level `tests/<group>/` now needs `tests/smoke.list` in its `paths:`
  (else its gate fails and its fix round cannot edit the file; `taskctl changes` would REFUSE it). Queued todo tasks whose `paths:` name
  a `tests/<group>/` that does not exist yet and lack `tests/smoke.list`: T459 (abi), T470 (abi), T503 (ffi), T668a (mock), T698 (target),
  T943 (mock), T966 (target), T968 (target), T972 (types, target), T977 (target), T981 (agir), T982 (target). This is manageable: the
  architect adds `tests/smoke.list` to each of these `paths:` (or `locks:`) in one board pass; the failure message tells the engineer exactly what to add,
  so it is not a silent block. T459 is the nearest. Also worth noting in the axiom-qa/engineer guidance: "new tests group => add a pool line".

VERDICT: PASS round=0
