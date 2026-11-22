# T498e QA

## Round 0

Gate of T498e (an indexed write never re-initialises a moved array; removal of dead `own.move.resolve_place`).
All builds/tests inside `build-snap-T498e` (HEAD f4a693b3 + this task's change set, stage-2 `axiomc2.exe` already built
there from the task's sources, `-j 2`, `--no-cache`). The main tree was not built or tested.

### Checks and evidence

1. Change set (`taskctl.py changes T498e`): 3 compiler files (`compiler/own/init.ax`, `mod.ax`, `move.ax`) + 13 engineer
   tests + report; no selfhost bundle listed. The only `REFUSED` line was for my own unlisted QA tests, resolved by listing them
   under `## Files changed` below.
2. Diff review (`git diff HEAD -- compiler`): `own_do_assign` and the 1-bit `own_bits_do_assign` both treat
   `had_deref || own_place_indexed(place)` as a read-check of the array node with no marking; `own_drop_replaces_element`
   (non-explicit DROP of an indexed place = in-place replace) is applied identically in the exact visitor
   (`own_visit_bb`) and the fast path (`own_bits_visit_bb`), so the fast path flags an error exactly when the exact visitor
   would report; the fallback therefore decides every rejected program. Explicit `drop(a[i])` keeps moving the whole array.
   Deref-first places (`(*v)[i] = ..`, `(*p)[i] = ..`, `v.hs[0] = ..` with `v: mut_view<W>`) keep their old path.
3. Own tests: `axtest --compiler build/axiomc2.exe --no-cache own_index_moved own_index_copy`: TOTAL 37 PASS 37 (engineer
   set, 11 ui + 2 run (x3 modes) + T498b set). With my additions `own_index_moved` alone: TOTAL 38 PASS 38 FAIL 0,
   WEAK-NATIVE 0.
4. HEAD comparison: the same `own_index_moved` set run with a HEAD-equivalent stage-2 compiler (the T498g snapshot's
   `axiomc2.exe`; its only compiler change is in `compiler/types/typeck.ax`, none in own/mir) gives TOTAL 38 PASS 20 FAIL 18:
   every ui test except `compound_write_after_move` (already rejected at HEAD through the read half of `op=`; a valid
   regression guard) FAILS at HEAD with "missing diagnostics ... AX_MOVE_USE_AFTER_MOVE/AX_INIT_USE_UNINIT", i.e. 17 ui tests
   prove the fix; all run tests pass at HEAD too (they are the no-false-positive set).
5. Native evidence (step 4a): every run test has an exact `stdout:` plus `exit: 0` and passes interp / native / native-O1
   (verified with `--verbose`; WEAK-NATIVE 0 for the task's own tests). Mutation: in the snapshot only, changed
   `D9\nD8` to `D9\nD0` in `qa_drop_replace_counts.ax`'s `stdout:` -> all three legs FAIL ("stdout differs at byte 22");
   file restored (diff clean) and re-verified PASS.
6. Soundness (all REJECT with the right code on the exact `//~` line): plain `hs[0] = mk()` (call destination), `hs[0].n = 5`,
   compound `hs[i].n += 2`, nested 2-D `g[1][0] = mk()`, drop-needing element replace, array in a struct field (field moved /
   whole struct moved / two levels deep `o.w.hs[0].n` after `o.w` moved / partly-moved struct), maybe-moved after a branch,
   loop-carried moved (two tests), maybe-uninit after a one-armed init (`AX_INIT_USE_UNINIT`), RHS that moves the array
   (`hs[1].n = eat(hs)`), call whose argument moves the array and whose destination is `hs[0]`, row move `let r = g[0]` then
   `g[1][0] = ..`, explicit `drop(ds[0])` then `ds[1] = D{..}`, 2-D drop-needing `g[1][0] = D{..}`.
7. No false positives (all PASS in the three modes with exact stdout): element write / replace on an owned array, Drop-type
   in-place replace (see drop counts below), 2-D, array in struct field, whole `hs = [..]` reinit after a move then indexed
   writes (also inside a loop and after a branch reinit), writes through `mut_view<[2]H>` (`(*a)[0].n = ..`),
   `mut_view<W>` (`w.hs[0].n = ..`) and a raw `*mut [2]H` (`(*p)[1].n = ..`), partially moved struct (`w.name` moved, then
   `w.hs[..] = ..` accepted, `w.hs` moved + reassigned whole, then writes accepted), struct field reinit (AOWN-37, engineer
   test), Copy arrays (`let b = a; a[0] = 10; a[1] += 5`, 2-D) via a direct run (exit 31 as computed), T498b `own_index_copy`
   cases (all PASS).
8. Drop counts (`qa_drop_replace_counts.ax`, native/interp/O1 agree): loop replace `ds[i] = ..` over 3 elements, dynamic
   index in a struct field array, 2-D array, replacement built from another element (`g[1][0] = D{ id: g[0][1].id + 100 }`);
   each replaced element's destructor runs exactly once at the assignment (D1..D6, D9, D8), the new elements are dropped once
   each at scope end in reverse local order (D16 D7 D107 D17 | D14 D15 | D10 D11 D12).
9. Fast vs exact agreement: every rejected program above is first flagged by the 1-bit pass and then reported by the exact
   visitor with the same code (`maybe_moved_branch`, loop tests, uninit, drop-replace, call destination); the accepted programs
   never trip the fast path (no spurious fallback diagnostics). Note on test design: the sink stops after the first error
   (`emit_own_diag`: `sink.errors > 0 -> return`), so a loop test has the indexed write first in source order (as in
   `moved_in_loop`); not a finding.
10. `resolve_place`: `grep -rnw resolve_place compiler std tests tools` finds nothing (matches only in the frozen C
   `bootstrap/axiom0/src/own/own.c` and its object, an unrelated C function; `sroa_/vec_resolve_place_*` are different
   names). `path_child` stays (used by `own_resolve_node`).
11. Fixed point: stage-2 axiomc2 in the snapshot was built from the task's sources (`FIXED-POINT (O1) OK` in the engineer
   report); the selfhost bundles regenerated by `snapshot` embed the new `compiler.own.init` and the affected selfhost
   groups pass (below).
12. taskgate (inside the snapshot, `python tools/taskgate.py --task T498e --compiler build/axiomc2.exe --build-dir build
   --exclude-requires axiom0-internal -j 2 --no-cache`, 583 s, log `_workspaces/T498e_qa_taskgate.log`):
   own 26 ids / 38 results, affected 81 ids / 129 results, smoke 30 ids / 49 results; total 111 ids,
   `TOTAL 178 PASS 178 FAIL 0 SKIP 0 XFAIL 0`, BASELINE OK, failing ids none, archcheck clean (232 files, 0 violations),
   WEAK-NATIVE 0 in the task's own/changed tests (15 pre-existing elsewhere), CACHE: none hit, no mismatch, no UNMATCHED /
   UNRESOLVED / DEFERRED. Affected-set derivation: map `compiler/own` -> tests/{conformance/adversarial, run/own, ui/own,
   verify/own, selfhost/cap, selfhost/own}, the bundle generator check for every bundle embedding `compiler.own.init`
   (driver, interp_opt, obj_link_driver, own, own_mir_verify), changed selfhost test files, exact dependencies of the new tests.
13. Selfhost groups `selfhost/own/`, `selfhost/own_mir_verify/`, `selfhost/mir/` (explicit run, `--baseline`):
   `TOTAL 17 PASS 17 FAIL 0`, BASELINE OK, WEAK-NATIVE 0 (log `_workspaces/T498e_qa_suites.log`). The engineer additionally
   reports `ui/ run/ selfhost/own` 3452 PASS (not re-run by me; covered by taskgate affected + smoke sets).
14. Spec check: behaviour matches SPEC-10 AXS-OWN-006 (clarified paragraph and the two table rows, hs[0] = mk() rejected,
   `hs = [..]` accepted); no new diagnostic code (AX_MOVE_USE_AFTER_MOVE / AX_INIT_USE_UNINIT existing); no BOOTSTRAP-SHORTCUT;
   no change under `bootstrap/axiom0`; no shared-file edit (`tools/axtest.py`, CMake, `pipeline.c`, `codes.def` untouched).
   No `docs/` change.
15. Mode check: no run test restricted to one mode; no `native-after`.
16. Column gap (item 5 of the request): the engineer's ui tests pin the line through `//~ ERROR` (exact code + line) but their
   `stderr-contains: <file>:<line>:` header is satisfied by the "moved here" note line (the line of the earlier move), so it
   is weak evidence; the real position check is the `//~` line, which my HEAD comparison shows is live (17 tests fail at HEAD
   on it). Column of the primary span is the right-hand side / statement start (reported deviation). Acceptable as a T498f
   follow-up (operand/place spans in `compiler/mir/builder.ax`); line is correct in all 20 ui tests. Not a FAIL.

### Findings

None blocking. Notes:
- N1 (note, T498f): primary span column is the RHS (or the statement start for drop-then-store/compound), not the indexed
  place; tighten the `stderr-contains` headers of `tests/ui/own_index_moved/*.ax` to `line:col` then, and drop the
  `stderr-contains` lines that currently match the note line.
- N2 (note, pre-existing, not caused by this task): `emit_own_diag` reports only the first own error per compilation, so a
  loop with both a loop-carried indexed write and a repeated move reports whichever comes first in visit order.

### Files changed
- tests/run/own_index_moved/qa_drop_replace_counts.ax
- tests/run/own_index_moved/qa_loop_reinit_then_write.ax
- tests/run/own_index_moved/qa_partial_move_other_field.ax
- tests/run/own_index_moved/qa_view_and_raw_writes.ax
- tests/ui/own_index_moved/qa_call_dest_after_arg_move.ax
- tests/ui/own_index_moved/qa_compound_drop_free_field_after_part_move.ax
- tests/ui/own_index_moved/qa_cond_move_later_in_loop.ax
- tests/ui/own_index_moved/qa_drop_2d_write_after_move.ax
- tests/ui/own_index_moved/qa_explicit_drop_then_index_write.ax
- tests/ui/own_index_moved/qa_maybe_uninit_index_write.ax
- tests/ui/own_index_moved/qa_nested_struct_array_moved.ax
- tests/ui/own_index_moved/qa_rhs_moves_array.ax
- tests/ui/own_index_moved/qa_row_move_then_write.ax

VERDICT: PASS round=0
