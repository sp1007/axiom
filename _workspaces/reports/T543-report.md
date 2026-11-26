# T543 report — typed loads of fresh arena memory removed; opt harness interner maps zeroed

## Summary
- The 26 typed loads of freshly allocated arena memory in `compiler/opt/{inline,escape,ipa,sroa}` are gone. Each site now
  builds its value without reading uninitialised bytes. `MirStmt` sites call a new shared constructor; the one
  `MemOptStats` site uses a zero struct literal. The arena allocation at each site was dead (the statement is copied
  into the block by `mir_bb_push_stmt` / `inl_bb_push_stmt_ptr`) and is dropped.
- The seven opt probe harnesses now zero the installed interner map before use.
- A guard test fails if `*(arena_alloc_raw(` / `*(heap_alloc(` ever reappears under `compiler/`.
- The two baseline lines for this task and their comment block are removed.
- `compiler/interp`, `compiler/kernel/interner.ax` and `std/` were not touched.

## Constructor added
`compiler/mir/mir.ax`: `pub fn mir_stmt_new(kind: u8) -> MirStmt`. It builds a full struct literal and then calls
`mir_stmt_zero`, so every field has the same value `mir_stmt_zero` gives. All 25 `MirStmt` sites pass `MIR_STMT_ASSIGN`
(each site then calls `mir_stmt_reset` or `inline_remap_stmt`, as before). Each of the four opt modules gained
`use compiler.mir.mir.mir_stmt_new`.

## Sites changed (file:line after the edit; before = `unsafe { *(arena_alloc_raw(..) as *mut MirStmt) }`, after = `mir_stmt_new(MIR_STMT_ASSIGN)`)
- compiler/opt/escape/mod.ax: 5326 `st`, 6245 `ref_st`, 6269 `ref_st`, 6278 `cast_st`, 6405 `val_st`, 6449 `ref_st`,
  6472 `zst_st`, 6480 `box_st` (8 MirStmt sites)
- compiler/opt/escape/mod.ax: ~7454 `mstats: MemOptStats` — before `*(arena_alloc_raw(.., size_of<MemOptStats>(), ..) as
  *const MemOptStats)`, after a `MemOptStats { .. all 15 fields 0u32 }` literal (the following `memopt_stats_zero` call stays)
- compiler/opt/inline/mod.ax: 2595 `env_st`, 2608 `ast`, 2621 `ust`, 2654 `dst`, 2678 `rst` (5)
- compiler/opt/ipa/mod.ax: 1990 `init_st`, 2022 `tst`, 2038 `pst` (3)
- compiler/opt/sroa/mod.ax: 2235 `dummy_st`, 2287 `init_st`, 2312 `st`, 2330 `dst_drop`, 2403 `dst_d`, 2418 `fst`,
  2438 `fst`, 2454 `fst`, 2503 `dst_drop` (9)

Total 26. `grep -rnE "\*\(\s*(arena_alloc_raw|heap_alloc)\(" compiler/` now finds nothing. The earlier multiline-mode
search of `compiler/` found only these 26 sites, so there were no multi-line or `heap_alloc` forms and no site outside
`paths:`/`locks:`.

## Harness templates (7)
After `(*sess_ptr).interner.map_cap = smap_cap;` each template now runs a loop that writes `0u32` into all
`smap_cap` slots of `smap_ids` (hashes left alone, as the task allows):
tests/selfhost/opt/harness_opt_pipeline.ax.in, tests/conformance/p15/e15_3_loops_bce/e15_3_loops_bce_probe.ax.in,
tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_probe.ax.in,
tests/opt2/opt2_sroa_inline_probe.ax.in, tests/run/opt_bce/opt_bce_probe.ax.in,
tests/run/opt_ipa_devirt/opt_ipa_devirt_probe.ax.in, tests/run/static_items/opt_static_summary_alias_probe.ax.in.
The generated bundle `tests/selfhost/opt/qa_opt_pipeline.ax` was not edited; the snapshot regenerates it.

## Guard test
`tests/run/unsafe/oracle_ub_compiler_sites/`:
- `check_compiler_sites.py <root>` scans `compiler/**/*.ax` (multi-line, `//` comments ignored) and prints
  `file:line` for each hit; exit 1 on a hit.
- `no_typed_load_of_fresh_alloc.test` runs it on the repo (`nocache`, because it scans all of `compiler/`): PASS.
- `detector_catches_planted_pattern.test` runs `check_compiler_sites.py --plant`: it plants a one-line and a
  two-line copy of the pattern in a temp tree and requires both to be reported (`PLANT-DETECTED compiler/opt/planted.ax:2
  and :3`). The plant lives in a temp directory, so nothing has to be removed from the repo.

## Verification (snapshot build-snap-T543, build dir build-snap-T543/build)
- `python build-snap-T543/tools/build_axiomc.py --out build-snap-T543/build`: stage 1 OK, stage 2 == stage 3 at O1
  (`FIXED-POINT (O1) OK`, sha 22f99ce7...), stage-0 guard OK. Rerun with `--opt O0`: `FIXED-POINT (O0) OK`
  (sha f2f09092...). Logs: `_workspaces/T543_build.log`, `_workspaces/T543_build_O0.log`.
- `axtest.py --compiler build/axiomc2.exe --no-cache opt_lto_engine qa_opt_pipeline oracle_ub_compiler_sites`:
  6/6 PASS. `run/opt_lto/opt_lto_engine.test` passes; `selfhost/opt/qa_opt_pipeline.ax` passes in `[interp]`, `[native]`
  and `[native-O1]`; both guard tests pass. The UB detector is unchanged.
- `axtest.py --compiler build/axiomc2.exe opt2/ run/opt_ conformance/p15/ run/static_items selfhost/opt`: 420 run,
  420 PASS, 0 FAIL, WEAK-NATIVE 0. These cover the `tests/opt*` goldens, `run/opt_*`, all of `conformance/p15`, the
  selfhost opt group and all seven edited harnesses. No golden changed.
- Not run by me: `taskgate.py` (affected set + smoke + archcheck) — left to the QA gate, per the task's gate row. The
  baseline file no longer holds the two T543 ids, so the gate must pass without them.

## Notes
- Arena layout changes slightly (25 dead `MirStmt`-sized allocations no longer made per run); no optimisation result
  depends on it (goldens unchanged, fixed point holds).
- Side observation, out of scope (T544 covers interner sizes): none new.

## Files changed
- compiler/mir/mir.ax
- compiler/opt/inline/mod.ax
- compiler/opt/escape/mod.ax
- compiler/opt/ipa/mod.ax
- compiler/opt/sroa/mod.ax
- _workspaces/baseline-failures.txt
- tests/selfhost/opt/harness_opt_pipeline.ax.in
- tests/conformance/p15/e15_3_loops_bce/e15_3_loops_bce_probe.ax.in
- tests/conformance/p15/e15_4_inline_specialize_devirt/e15_4_inline_specialize_devirt_probe.ax.in
- tests/opt2/opt2_sroa_inline_probe.ax.in
- tests/run/opt_bce/opt_bce_probe.ax.in
- tests/run/opt_ipa_devirt/opt_ipa_devirt_probe.ax.in
- tests/run/static_items/opt_static_summary_alias_probe.ax.in
- tests/run/unsafe/oracle_ub_compiler_sites/check_compiler_sites.py
- tests/run/unsafe/oracle_ub_compiler_sites/no_typed_load_of_fresh_alloc.test
- tests/run/unsafe/oracle_ub_compiler_sites/detector_catches_planted_pattern.test
- _workspaces/reports/T543-report.md

STATUS: COMPLETE round=0
