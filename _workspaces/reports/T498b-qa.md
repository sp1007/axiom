# T498b QA

## Round 0

### Change set
`taskctl.py changes T498b`: only `stage` lines (report, `compiler/own/init.ax`, the 2 run and 3 ui tests of the engineer); no REFUSED. Shared-file check: nothing outside `paths:`.

### Review of the fix (compiler/own/init.ax)
- `own_bits_resolve` / new `own_resolve_node` stop at the first INDEX/SUB_SLICE: the node is the array's and a following FIELD/DOWNCAST is no longer applied to it (fixes `hs[i].1` read as `hs.1`). `DEREF` after an index is still reported by `out_had_deref` (fast path).
- `own_operand_is_indexed_copy_read`: only an operand whose place goes through an index (before any deref) AND whose projected type is Copy (`type_is_copy`) is turned into a pure read (`own_check_use`), never a move. Unknown type (0) falls back to the old conservative path (moves). Non-indexed places keep the unchanged path-node `is_copy` decision.
- The deviation from the task wording ("a COPY operand never moves") is justified: `mb_operand_from_place` emits COPY for non-Copy structs too (verified below with plain-struct tests: use after whole-struct move and after field move are still rejected). Sound, documented in the report ("Spec deviations: none", COPY decision paragraph). Accepted.
- Pre-existing, not caused by this task (identical in the old compiler): assigning through an index after the array was moved (`let t = hs; hs[0].n = 5; hs[1].n`, also `hs[0] = mk()`) is accepted (re-initialises the whole array node). See Follow-ups.

### Adversarial probing (scratch dir; NEW = snapshot axiomc2, OLD = compiler-cache `axiomc2_O1_6c6ca8c93b58c7eb.exe`, whose `compiler/own/init.ax` hash equals HEAD's)
All 14 negative cases gave the same diagnostics (`AX_MOVE_USE_AFTER_MOVE`, same line:col) in NEW and OLD, i.e. no use-after-move was lost: `hs[0]` moved then `hs[j].f` read; partial move `hs[0].name` then `hs[1].n`; whole use after indexed move; plain struct (no index) moved then `.n` / `.f` read; field moved then whole; branch move then read after the join; loop read then move; 2-D `g[0][1]` moved then `g[1][0].n`; array held in a struct field (`w.hs[0].name` then `w.hs[1].n`, and then `w`); tuple array; function-argument move through an index; enum scrutinee `match es[0]` moving the array. Positive cases (OLD rejected with `AX_MOVE_USE_AFTER_MOVE`, NEW accepts and prints the right values in interp, native and `-O1`): re-init `hs = [...]` after `take(hs[0])` (plain, in a loop, in a branch); by-value parameter array with dynamic index; Copy-field reads of a Copy-fields-only (non-Copy) struct through an index; `view` deref + index; uninitialised array read still `AX_INIT_USE_UNINIT`.

### Tests added by QA (main tree, kept)
Run (exact stdout, interp / native / native-O1) and ui (`stderr-contains` exact line:col plus `//~ ERROR`): see `## Files changed`. Against the reverted-init.ax proxy compiler: the 3 run tests FAIL in all three modes (`AX_MOVE_USE_AFTER_MOVE` at build) and `ui/own_index_copy/move_field.ax` FAILs (wrong location); the 8 QA ui tests pass on both (they guard that moves are still diagnosed).

### Mutation (step 4 / 4a)
- Reverted-init proxy: `python tools/axtest.py --compiler ../_workspaces/artifacts/compiler-cache/axiomc2_O1_6c6ca8c93b58c7eb.exe --no-cache -j 2 run/own_index_copy ui/own_index_copy` -> `TOTAL 20 PASS 10 FAIL 10` (all 9 run results and `move_field.ax` fail as listed above).
- Native-liveness mutation in the snapshot only: changed `// stdout: 7 21` to `8 21` in `tests/run/own_index_copy/copy_field_reads.ax` -> `TOTAL 3 PASS 0 FAIL 3` (interp, native, native-O1 each "stdout differs at byte 0"); file restored (`stdout: 7 21` again).
- Native evidence: every run test of the task has an exact `// stdout:` (plus `exit: 0`) and runs in all three modes; `WEAK-NATIVE 0` in own/changed tests.

### Build / suites (inside `build-snap-T498b`)
- Fixed point in the snapshot: `axiomc2.exe` and `axiomc3.exe` sha256 `074e3c98...` equal (the report's value); `STAGE0-GUARD OK` in `_workspaces/T498b_build.log`. `bootstrap/axiom0` untouched.
- New + QA tests, `--no-cache`: `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 run/own_index_copy ui/own_index_copy` -> `TOTAL 20 PASS 20 FAIL 0`.
- taskgate: `python tools/taskgate.py --task T498b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T498b.json` (log `_workspaces/T498b_qa_taskgate.log`): `TASKGATE T498b exit=0`, `TOTAL 159 PASS 159 FAIL 0`, archcheck clean (232 files, 0 violations), BASELINE OK, WEAK-NATIVE 15 in the run, 0 in the task's own/changed tests; cache mismatch none, sample 20 of 45 hits; no UNMATCHED/UNRESOLVED/MAP-NOTE/DEFERRED entries.

| part | ids | results | PASS | FAIL |
|---|---|---|---|---|
| own | 14 | 20 | 20 | 0 |
| affected (rule: map compiler/own -> conformance/adversarial, selfhost/cap, own, + generator-check of bundles embedding compiler.own.init: driver, interp_opt, obj_link_driver, own_mir_verify; changed tests) | 69 | 111 | 111 | 0 |
| smoke (31 ids over all top-level groups; always: run/str/hello.ax, ui/typeck/type_unknown.ax, diff/002-arithmetic.ax) | 31 | 48 | 48 | 0 |

- Extra selfhost/own groups: `axtest ... selfhost/own selfhost/own_mir_verify selfhost/mir run/own ui/own` -> `TOTAL 80 PASS 80 FAIL 0`, BASELINE OK, WEAK-NATIVE 0 (38 cache hits, bundles of own/own_mir_verify were misses = run fresh in the gate; log `_workspaces/T498b_qa_suites.log`).
- Scope/spec: change confined to the own checker; no new diagnostics; no BOOTSTRAP-SHORTCUT; all new run tests are `modes: interp native native-O1` (default), no single-mode test.

### Findings
None blocking.

### Follow-ups
1. (pre-existing, same in HEAD) Assigning through an index after the whole array was moved is accepted and re-initialises the whole array node: `let t = hs; hs[0].n = 5; let u = hs[1].n;` and `hs[0] = mk();` compile. With element-level tracking post-v1 (REQ-OWN-049) this should be `AX_MOVE_USE_AFTER_MOVE` for the field assignment; architect to decide the intended rule.
2. `own.move.resolve_place` has no caller left (engineer's follow-up 2).
3. The binary-op operand span (engineer's follow-up 1) is a builder matter.

## Files changed
- tests/run/own_index_copy/qa_reinit_and_dynamic_index.ax
- tests/ui/own_index_copy/qa_2d_move_then_copy_read.ax
- tests/ui/own_index_copy/qa_branch_move_then_copy_read.ax
- tests/ui/own_index_copy/qa_loop_fnptr_read_then_move.ax
- tests/ui/own_index_copy/qa_move_elem_then_fnptr_other_index.ax
- tests/ui/own_index_copy/qa_nested_struct_array_field_move.ax
- tests/ui/own_index_copy/qa_partial_name_then_copy_read.ax
- tests/ui/own_index_copy/qa_plain_struct_copy_field_after_move.ax
- tests/ui/own_index_copy/qa_plain_struct_field_move_then_whole.ax
- _workspaces/reports/T498b-qa.md

VERDICT: PASS round=0
