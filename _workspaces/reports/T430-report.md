# T430 report — optimizer probe bundles build clean

## Summary
All 15 T430 ids pass. Two independent root causes, both in the test harness (no `compiler/` or `std/` change).

## Root cause per group

### Group A — duplicate module in the probe bundle (all 15 ids)
- Symptom (T421-qa): probe build prints `warning[AX_NAME_SHADOW_MODULE]` and then fails. The warnings are harmless
  (10 of them, locals named `cap`, `mcap`, `out`, `len` shadowing module names, still built clean before and after).
  The real failure is the error: 126x `error[AX_NAME_DUPLICATE]: name defined twice in one scope`, the first at
  `use host_intrinsics.heap_alloc` in `module compiler.own.cap`. (T421-qa summarised this as `AX_NAME_UNRE...`.)
- Cause: commit 14ce54b1 (T417) added `("compiler.own.cap", "compiler")` to `got.CORE_MODULES` and
  `got.PIPELINE_MODULES` in `tests/selfhost/opt/gen_opt_tests.py`. Every oracle in scope builds its module list as
  `list(got.CORE_MODULES | PIPELINE_MODULES) + [("compiler.own.cap", "compiler"), ...]`, so `compiler.own.cap` was
  emitted twice into the bundle. Confirmed by assembling the bundle (`module compiler.own.cap` appears twice) and
  compiling it with axiomc2 (126 duplicate-name errors, all inside the second copy).
- Fix: removed the now-redundant `("compiler.own.cap", "compiler"),` line from the 15 oracle scripts (one line each;
  the shared base list already provides it, so module order/content is unchanged for the rest). The shared helper
  `tests/selfhost/bundle_common.py` and `gen_opt_tests.py` were NOT touched (out of paths). A follow-up would be to make
  `assemble_compiler_modules` reject duplicate module names with a clear message (see Follow-ups).
- After the fix an alias bundle (42.9k lines) compiles with rc=0 at -O0 in 60 s.

### Group B — build time vs. hard-coded timeouts (6 ids: opt_bce, opt_ipa_devirt, opt_loops, opt2_sroa_inline, e15_3, e15_4)
- After group A these bundles are 95-107k lines. Under the loaded 4-core machine a single `-O0` build took 5m27s
  (ipa_devirt) and `-O2 --verify-each` of opt_bce exceeded 300 s; the oracles passed `timeout=300` (e15_3: 600,
  e15_4: 900) to the build subprocess and the `.test` manifests allowed 900 s in total (1800 for e15_4).
- Fix: build-subprocess timeout raised to 1500 s in those 6 oracles; manifest `timeout:` raised to 5400 in the 6
  `.test` files (measured wall time: opt_loops 958 s, opt_bce 886 s, with `-j` 1 and the CPU shared with other tasks).
  Checks and expected strings are unchanged.

## Verification
- Compiler used: `build-snap-T452/build/axiomc2.exe` (built from HEAD plus T452's changes, read-only reuse; no
  compiler edit of mine is involved, the failures are in the generated bundles). No `build-snap-T430` build was made
  (a compiler build costs ~10 min of saturated CPU and the fix touches only test scripts).
- Run with a small stand-in runner (`tools/axtest.py` is currently broken in the main tree:
  `ModuleNotFoundError: axtest_affected`, owned by another task) that executes the manifest `cmd` and compares
  exit code and stdout exactly. Results (seconds):
  - PASS opt_alias_engine 199, opt_escape_engine 289, opt_loop_vec_engine 99, opt_lto_engine 86,
    opt_pgo_gc_engine 43, opt_slp_vec_engine 106 (first run; stdout/exit verified by hand, my runner
    compared with a stricter newline rule on that pass only).
  - PASS opt_bce_engine 886, opt_ipa_devirt_engine 344, opt_loops_engine 958, opt2_sroa_inline_engine 308,
    e15_2_conformance 319, e15_3_loops_bce_oracle 295, e15_4_inline_specialize_devirt_oracle 353,
    e15_5_conformance 118, e15_6_lto_pgo_gc_oracle 160.
  - opt_alias/escape/loop_vec/lto/pgo_gc/slp_vec each printed their exact expected line with rc=0.
- Mutation proof: in `opt_pgo_gc_oracle.py` changed `PROBE_SECTION_GC_AND_ROOTS=OK` to `...=MUTATED`: test FAILS
  (`stdout mismatch for opt_pgo_gc_probe under --interp`, rc=1). Reverted afterwards (diff of that file is again only the
  one removed line).
- `python tools/archcheck.py`: 229 files, 0 violations.
- Not run (resource limits): the complete suite and WEAK-NATIVE check; left to the QA gate. These edits change only
  oracle scripts and manifest timeouts, so no test other than the 15 ids is affected (the 15 oracles are not
  imported elsewhere; `opt_passmgr`/`opt_scalar`/`e15_1`/`e15_7` do not list `compiler.own.cap` and were not edited).
- All axiomc2/python processes I started were finished or killed; the axiomc2 still visible belongs to T452.

## Baseline
Removed the 16 T430 lines (header + 15 ids) and one blank line from `_workspaces/baseline-failures.txt`; nothing else.

## Follow-ups (not done, outside paths)
- `tests/selfhost/bundle_common.py::assemble_compiler_modules`: fail early on duplicate module names; otherwise the
  next addition to `CORE_MODULES`/`PIPELINE_MODULES` breaks every oracle that appends modules again.
- Probe bundle compile time (50-100k lines, 5-15 min at -O0/-O2) is a recurring cost for these 6 oracles; consider
  splitting or caching.
- `tools/axtest.py` imports a missing `tools/axtest_affected.py` (T437a in progress presumably).

## Files changed
- _workspaces/baseline-failures.txt
- _workspaces/reports/T430-report.md
- tests/run/opt_alias/opt_alias_oracle.py
- tests/run/opt_bce/opt_bce_oracle.py
- tests/run/opt_bce/opt_bce_engine.test
- tests/run/opt_escape/opt_escape_oracle.py
- tests/run/opt_ipa_devirt/opt_ipa_devirt_oracle.py
- tests/run/opt_ipa_devirt/opt_ipa_devirt_engine.test
- tests/run/opt_loop_vec/opt_loop_vec_oracle.py
- tests/run/opt_loops/opt_loops_oracle.py
- tests/run/opt_loops/opt_loops_engine.test
- tests/run/opt_lto/opt_lto_oracle.py
- tests/run/opt_pgo_gc/opt_pgo_gc_oracle.py
- tests/run/opt_slp_vec/opt_slp_vec_oracle.py
- tests/opt2/opt2_sroa_inline_oracle.py
- tests/opt2/opt2_sroa_inline_engine.test
- tests/conformance/p15/e15_2_alias_escape/e15_2_conformance_oracle.py
- tests/conformance/p15/e15_3_loops_bce/e15_3_loops_bce_oracle.py
- tests/conformance/p15/e15_3_loops_bce/e15_3_loops_bce_oracle.test
- tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_oracle.py
- tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_oracle.test
- tests/conformance/p15/e15_5_autovec/e15_5_conformance_oracle.py
- tests/conformance/p15/e15_6_lto_pgo_gc/e15_6_lto_pgo_gc_oracle.py

STATUS: COMPLETE round=0
