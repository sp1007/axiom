# T498b report

## Summary
Fixed FU-T498-FNPTR-INDEX: reading a Copy field through an index of a non-Copy array
(`let a = hs[0].f; let b = hs[1].f;`, `hs: [2]H`, `H` not Copy) no longer marks `hs` moved, so the second
read and a later move of the whole array are accepted (SPEC-10 AXS-OWN-003). Moving a non-Copy element or
field out through an index still moves the whole array (no element-level tracking before v1, REQ-OWN-049)
and a later use reports `AX_MOVE_USE_AFTER_MOVE`.

Changes, all in `compiler/own/init.ax`:
- `own_bits_resolve` (1-bit fast path) and the new `own_resolve_node` (exact 4-state fallback, replaces
  `own.move.resolve_place` there) stop resolving at the first `INDEX`/`SUB_SLICE`: the node is the array's,
  a following `FIELD`/`DOWNCAST` is never applied to the array node. The fast path still reports a `DEREF`
  after the index through `out_had_deref`.
- New `own_operand_is_indexed_copy_read`: a COPY/MOVE operand whose place goes through an index and whose
  projected type is Copy (`type_is_copy`) only checks the array (initialised, not moved) and moves nothing,
  in both `own_bits_visit_operand` and `own_visit_operand`. The projected type comes from the new
  `own_place_type` (same walk as `mir_drop_place_type`; unknown type -> old conservative behaviour).
- The str interner reaches the solver through a new `OwnVisitor.str_in` field and a private `OwnTyEnv`
  (body, thir, str_in) threaded through `own_bits_visit_bb/rvalue/operand`; `own_check_exact_fallback`
  takes `str_in`.

Decision (deviation from the task wording "a COPY operand never moves"): the MIR builder
(`mb_operand_from_place`, `compiler/mir/builder.ax`) emits `COPY` for every type except `str` and non-Copy
arrays, so a non-Copy struct is moved with a `COPY` operand. Making `COPY` never move would silently accept
use-after-move of every struct. The checker therefore keeps relying on Copy-ness of the place: for places
without an index the existing path-node `is_copy` decides (unchanged), for indexed places the projected type
decides. This is the unambiguous part of the requirement and keeps every existing own/verify test green.

## Files changed
- compiler/own/init.ax
- tests/run/own_index_copy/copy_field_reads.ax
- tests/run/own_index_copy/nested_loop_2d.ax
- tests/ui/own_index_copy/move_element.ax
- tests/ui/own_index_copy/move_field.ax
- tests/ui/own_index_copy/move_twice_in_loop.ax
- _workspaces/reports/T498b-report.md

## Tests
Snapshot `build-snap-T498b` (HEAD 72494c8 + T498b).
- `python tools/build_axiomc.py --out build --stage 3`: `FIXED-POINT (O1) OK` (axiomc2 == axiomc3, sha256
  074e3c98...), `STAGE0-GUARD OK` (log `_workspaces/T498b_build.log`).
- New tests (`axtest --no-cache run/own_index_copy ui/own_index_copy`): TOTAL 9 PASS 9, WEAK-NATIVE 0. Run tests
  have exact `// stdout:` and run interp / native / native-O1: i32, `fn` pointer (the T422b QA repro), `[2]u8`
  and `view<[3]i32>` fields read twice through `hs[i]`, direct call `(hs[0].f)(1)`, nested `os[i].inner.f`,
  `g[i][j].n` on `[2][3]Cell`, reads in loops, then a move of the whole array. ui tests pin
  `AX_MOVE_USE_AFTER_MOVE` with the exact `line:col` (`stderr-contains`): element moved out by index, `str`
  field moved out by index, element moved by index in a loop (reported at the next iteration's read).
- Regression proof: the previous compilers in `_workspaces/artifacts/compiler-cache` (e.g.
  `axiomc2_O1_6c6ca8c93b58c7eb.exe`) reject both run tests with `AX_MOVE_USE_AFTER_MOVE`.
- `tools/taskgate.py --task T498b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  TASKGATE exit 0, `TOTAL 152 PASS 152 FAIL 0`, archcheck clean, BASELINE OK, WEAK-NATIVE 0 in own/changed tests
  (log `_workspaces/T498b_taskgate.log`).
- `axtest --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 2 ui selfhost/own selfhost/own_mir_verify
  selfhost/mir run/own run/array_copy run/fn_ptr_field_call run/closure`: `TOTAL 686 PASS 685 FAIL 0 SKIP 1`
  (WEAK-NATIVE 18, all pre-existing tests outside this change; log `_workspaces/T498b_suites.log`).

## Spec deviations
none (see the COPY decision above; it follows SPEC-10 AXS-OWN-003 rather than the operand kind).

## Follow-ups
1. The span of a use-after-move on a binary-op operand is the whole right-hand side (`s + hs[i].n` at 19:13 in
   `move_twice_in_loop.ax`) because the builder leaves `MirOperand.location` empty for those operands; a
   builder task could give operands their own span. Pre-existing, not changed here.
2. `own.move.resolve_place` (outside this task's paths) has no caller left in `compiler/`; it can be deleted
   or given the stop-at-index rule by a task owning `compiler/own/move.ax`.

STATUS: COMPLETE round=0
