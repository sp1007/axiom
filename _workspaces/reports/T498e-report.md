# T498e report

## Summary
SPEC-10 AXS-OWN-006 (triage-1122 clarification): a write through an index never reinitialises anything
and requires the array place to be definitely `OWNED`.

`compiler/own/init.ax` (both solvers — the exact 4-state visitor and the 1-bit fast path, kept identical
so the fast path triggers the exact fallback exactly when the visitor reports):
- `own_do_assign` / `own_bits_do_assign`: when the destination place goes through `MIR_PROJ_INDEX` /
  `SUB_SLICE` before any deref (`own_place_indexed`, from T498b), the place is checked like a read of the
  array node (`own_check_use`: moved / maybe-moved / partial -> `AX_MOVE_USE_AFTER_MOVE` with the "moved
  here" label; uninit -> `AX_INIT_USE_UNINIT`) and no node is marked. Covers `Assign` statements and the
  `Call` / `Suspend` destination (`hs[0] = mk()` writes the call result straight into `hs[0]`).
- New `own_drop_replaces_element`: for an element type that needs drop the MIR builder lowers
  `a[i] = v` as `DROP(a[i])` then the store (SPEC-03 AXS-SEM-043). Before this change the drop moved the
  whole array and the store re-marked it `OWNED`; now a non-explicit `DROP` of an indexed place is an
  in-place replacement: it checks the array like a read and marks nothing. Before drop elaboration (the
  own check runs on pre-elaboration MIR) this is the only producer of such drops. An explicit
  `drop(a[i])` (`drop_is_explicit`) keeps moving the element out, i.e. the whole array (REQ-OWN-049,
  T498b semantics).
- Writes through a view / raw-pointer deref keep their previous handling (the `had_deref` branch).
- Whole assignment `hs = [...]` and field reinitialisation of a non-indexed struct (AOWN-37) are
  unchanged.

`compiler/own/move.ax`, `compiler/own/mod.ax`: removed the dead `resolve_place` and its re-export.
`grep -rnw resolve_place compiler tests` (excluding generated selfhost bundles, which are regenerated
by the harness) finds nothing; `path_child` stays (used by `own_resolve_node`).

Compiler sources: stage-2/stage-3 fixed point holds (`FIXED-POINT (O1) OK`, sha256 9689e919...), so the
compiler itself never writes through an index of a moved/uninit array.

## Files changed
- compiler/own/init.ax
- compiler/own/move.ax
- compiler/own/mod.ax
- tests/ui/own_index_moved/field_write_after_move.ax
- tests/ui/own_index_moved/elem_write_after_move.ax
- tests/ui/own_index_moved/drop_elem_write_after_move.ax
- tests/ui/own_index_moved/nested_2d_write_after_move.ax
- tests/ui/own_index_moved/compound_write_after_move.ax
- tests/ui/own_index_moved/struct_field_array_moved.ax
- tests/ui/own_index_moved/struct_whole_moved.ax
- tests/ui/own_index_moved/maybe_moved_branch.ax
- tests/ui/own_index_moved/moved_in_loop.ax
- tests/ui/own_index_moved/element_moved_then_other_write.ax
- tests/ui/own_index_moved/uninit_index_write.ax
- tests/run/own_index_moved/index_writes_owned.ax
- tests/run/own_index_moved/field_reinit_not_indexed.ax

## Tests
All in `build-snap-T498e` (clang Release axiom0 -> `tools/build_axiomc.py`, axiomc2, `-j 2`):
- build: `BUILD-AXIOMC OK`, `FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`.
- `axtest.py --compiler build/axiomc2.exe own_index_moved own_index_copy`: TOTAL 37 PASS 37 FAIL 0,
  WEAK-NATIVE 0 (new run tests pass interp / native / native-O1 with exact `stdout:`; the drop-needing
  replacement prints the old element's drop at the assignment).
- `tools/taskgate.py --task T498e --compiler build/axiomc2.exe -j 2`: TASKGATE exit=0, axtest TOTAL 157
  PASS 157 FAIL 0, BASELINE OK, failing ids none, archcheck clean, WEAK-NATIVE 0 in the task's own tests
  (log `_workspaces/T498e_taskgate.log`).
- `axtest.py --gate --filter ui/ --filter run/ --filter selfhost/own -j 2`: TOTAL 3452 PASS 3452 FAIL 0
  (WEAK-NATIVE 122 are pre-existing tests outside this task; log `_workspaces/T498e_suites.log`).

## Spec deviations
Diagnostic column. AXS-OWN-006 says the span is the indexed place. The own check only has the MIR
statement / terminator location, which the MIR builder sets to the right-hand side for a plain store
(`hs[0].n = 5u32` -> col of `5u32`; `hs[0] = mk()` -> col of `mk()`) and to the whole statement for the
drop-then-store and compound forms (col of `hs`). The line is always the indexed write; the UI tests pin
`file:line:` (and the exact `//~ ERROR` code on that line), not the column. Carrying the destination
place span needs a `compiler/mir/builder.ax` change (outside this task's paths; T498f already owns
operand spans in `builder.ax`).

## Follow-ups
- T498f (existing): when it fixes operand spans, also give the assignment destination its place span
  (`MirStmt.location` / call terminator for `a[i] = f()`), then tighten the `stderr-contains` lines of
  `tests/ui/own_index_moved/*.ax` to `line:col`.

STATUS: COMPLETE round=0
