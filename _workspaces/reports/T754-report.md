# T754 Report — E18.1 Deterministic Query Cycle Detection, Snapshot-Bound Diagnostics & Invalidation

## Summary

Implemented `compiler/query/engine/mod.ax` (`module compiler.query.engine`) and the `tests/run/query_cycles/` verification suite per `spec/SPEC-21-query-engine-semantic-db.md` (`§3 AXS-QRY-020..023`, `§4 AXS-QRY-030..033`, `§5 AXS-QRY-050..053`, `INV-QRY-002`):

1. **Tarjan SCC & Active-Stack Cycle Detection (`AXS-QRY-020..022`, `INV-QRY-002`)**:
   - Implemented `engine_handle_active_cycle` and `engine_rotate_cycle_canonical` to detect re-entrant `Computing` queries on the active `QueryStack` and rotate any cycle `[Q_0, Q_1, ..., Q_{m-1}]` to start at the unique minimum `(QueryKind.order_rank, SemanticKey)` under canonical lexicographical order, closing at `[Q_p, ..., Q_{m-1}, Q_0, ..., Q_{p-1}, Q_p]`.
   - Implemented `engine_compute_tarjan_sccs` to discover all cyclic strongly connected components across derived query slots in `CompilerDB`, canonicalizing member ordering and sorting discovered SCCs by `canonical_head`.
   - Enforced `AXS-QRY-020` distinction between legal recursion (`typeck_body` querying `item_signature` for runtime recursion; `engine_add_type_indirection_field` for recursive structs behind pointer/box indirection) and illegal query cycles (`AX_QUERY_CYCLE` for cyclic module re-exports via `engine_add_module_reexport_dep`, `AX_TYPE_CYCLE` for recursive type aliases and value-sized struct layout recursion, `AX_CTM_CYCLE` for mutually recursive `const` items, `AX_TRAIT_CYCLE` for cyclic trait obligations, and `AX_QUERY_DEPTH_LIMIT` for depth-limited trait solving).

2. **Cycle Recovery Fallbacks & Cascading-Error Suppression (`AXS-QRY-023`, `AXS-QRY-031`)**:
   - Implemented `engine_populate_poisoned_result_table` and poison predicates (`engine_sig_is_poisoned`, `engine_typeck_is_poisoned`, `engine_const_is_poisoned`, `engine_trait_is_error`, `engine_layout_is_poisoned`, `engine_mir_is_poisoned`, `engine_def_map_is_error`) to populate deterministic recovery values (`ErrorType`, `ConstValue.Poisoned`, `TraitResult.Error`, `LayoutResult.Poisoned`, `DefId.ERROR`, `MirBodyId.ERROR`).
   - Suppressed secondary `AX_TYP_MISMATCH` cascading diagnostics in `engine_execute_provider` (`QUERY_TYPECK_BODY`) whenever any upstream dependency is poisoned (`suppressed_cascades` counter), while continuing analysis of independent items in the same module.

3. **Snapshot-Bound Diagnostic Accumulation & Warm Replay (`AXS-QRY-030`)**:
   - Implemented `engine_replay_slot_diagnostics`, `engine_capture_snapshot_diags`, and `engine_snapshot_diags_equivalent` so diagnostics and cycle traces attached to `MemoEntry` slots are deterministically replayed in canonical `(SemanticKey, code)` order on warm memoized hits and green-reused subgraphs.

4. **Input-Revision Invalidation & Shallow Verification / Backdating (`AXS-QRY-032..033`)**:
   - Implemented `engine_set_source_file_input`, `engine_set_module_tree_input`, `engine_set_target_config_input`, `engine_set_package_graph_input`, and `engine_try_verify_green` to track transitive `MaybeDirty` invalidation waves (`invalidation_waves`, `total_slots_dirtied`), green-reuse untouched `Ready` and `Poisoned` slots outside the dirty cone, backdate unchanged re-evaluations (`backdated_verifications`), and re-evaluate `MaybeDirty` poisoned slots when upstream edits break a cycle (`Poisoned -> MaybeDirty -> Ready`).

## Files changed

- `compiler/query/engine/mod.ax`
- `tests/run/query_cycles/canonical_cycle_rotation.ax`
- `tests/run/query_cycles/canonical_cycle_rotation.stdout`
- `tests/run/query_cycles/cascade_suppression_recovery.ax`
- `tests/run/query_cycles/cascade_suppression_recovery.stdout`
- `tests/run/query_cycles/query_cycles_engine.test`
- `tests/run/query_cycles/query_cycles_oracle.py`
- `tests/run/query_cycles/query_cycles_probe.ax.in`
- `tests/run/query_cycles/snapshot_diag_invalidation.ax`
- `tests/run/query_cycles/snapshot_diag_invalidation.stdout`

## Verification

- Built compiler inside isolated worktree `build-snap-T754`:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T754`
  - `python build-snap-T754/tools/build_axiomc.py --root build-snap-T754 --out build-snap-T754/build` -> `BUILD-AXIOMC OK` (`axiomc2.exe`, `sha256=3f27878d500d0b49326a9b4e80f706f294422827a5186cdf9363c071c51ba797`)
- Executed `axtest.py -j 1` on `run/query_cycles` and targeted canaries inside `build-snap-T754`:
  - `python build-snap-T754/tools/axtest.py --root build-snap-T754 --build-dir build-snap-T754/build -j 1 run/query_cycles run/query_db run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`
  - Result: `WEAK-NATIVE 0`, `TOTAL 27 PASS 27 FAIL 0 SKIP 0 XFAIL 0` (including live `query_cycles_oracle.py` bundling `compiler.query.db` + `compiler.query.engine` + `query_cycles_probe.ax.in` across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`).
- Architecture check:
  - `python build-snap-T754/tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`

STATUS: COMPLETE round=0
