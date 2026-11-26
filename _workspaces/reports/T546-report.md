# T546 — report

## Round 0

### What changed
- `tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py`: `check_baseline_and_temp_cleanup` is now
  `check_temp_cleanup`. The `_workspaces/baseline-failures.txt` read and its "still has active lines" / CR checks are
  gone. The leftover-artifact check (`build/tmp_obj_link_driver_*`, `_gen_ref*`) is unchanged. Module docstring item 4
  now covers only the artifact check. The stdout marker is unchanged.
- `_workspaces/baseline-failures.txt`: removed the T546 line for `selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test`
  and the sentence about qa_t442 from the comment header. The header stays because T547's line remains.

### Evidence (inside `build-snap-T546`)
- `grep -n -i baseline tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py` returns nothing.
- Snapshot axiom0 built as Release with `-DCMAKE_C_FLAGS=-Wno-error=stringop-truncation`. This was needed because
  gcc at -O3 raises `-Werror=stringop-truncation` in the frozen `bootstrap/axiom0/src/link/pe/linker.c`; the
  warning exists at HEAD and has nothing to do with this task.
- `tools/build_axiomc.py` stage1 (axiom0 -> axiomc1) crashes at HEAD (rc 0xC00000FD/0xC0000005), both with the
  snapshot axiom0 and with the main-tree axiom0. This is an environment/HEAD problem outside this task (it matches T544,
  the interner defect).
- The stale `build/axiomc2.exe` of the main tree (Nov 17) fails 7 of 10 obj_link_driver tests with
  AX_TYPE_UNKNOWN_INTRINSIC, so I used `build-head-T428j/build/axiomc2.exe` (Nov 26) as `--compiler`. The oracle only
  uses the compiler for live builds of `main_42`.
- `python tools/axtest.py --compiler <that axiomc2.exe> --no-cache -j 2 --filter obj_link_driver --baseline _workspaces/baseline-failures.txt`
  gives `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`. It also prints
  `BASELINE NOW PASSING: selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test`, and that test passes while the
  snapshot baseline has 46 lines, so it no longer depends on baseline content.
- Mutation proof: creating `build-snap-T546/build/tmp_obj_link_driver_x` makes the test FAIL ("leftover temporary
  artifacts found"). After removing it, the test PASSES. The remaining check is therefore live.
- `python tools/archcheck.py`: 252 files scanned, 0 violations.
- The full taskgate (smoke set) was not run. It needs a compiler built from the snapshot, which cannot be built here
  (stage1 crash above). The change touches only a Python oracle that no other test or module references, so the
  affected set is the `selfhost/obj_link_driver` group (10 tests, all PASS).

### Decisions
- Did not add a narrower baseline check, as the task says.
- No `.test` file, bundle, generator or compiler change.

## Files changed
- tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py
- _workspaces/baseline-failures.txt

STATUS: COMPLETE round=0
