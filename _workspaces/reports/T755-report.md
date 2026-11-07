# T755 — E18.1: Query Engine, Cycle Recovery & Semantic Database Conformance Suite

## Summary
Implemented the Phase 18 (`E18.1`) end-to-end conformance suite in `tests/conformance/p18/e18_1_query_engine/` verifying the demand-driven semantic database (`compiler/query/db/mod.ax`), cycle recovery & Tarjan SCC engine (`compiler/query/engine/mod.ax`), deterministic `inspect --emit=query-graph` output, and incremental green reuse / snapshot-bound diagnostic replay per `SPEC-21` (`AXS-QRY-001..053`, `INV-QRY-003`):

1. **Bundled `compiler.query.db` + `compiler.query.engine` End-to-End Conformance Oracle (`e18_1_query_engine_oracle.test`, `e18_1_query_engine_oracle.py`, `e18_1_query_engine_probe.ax.in`)**:
   - Bundles the live `compiler/query/db/mod.ax` and `compiler/query/engine/mod.ax` implementation modules with `e18_1_query_engine_probe.ax.in` and executes the resulting probe across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`, plus deterministic PE build reproducibility (`sha256` match across clean builds).
   - Verifies multi-module demand-driven `CompilerDB` evaluation (`core::math`, `core::app`, `core::unused`), session isolation, header/body firewall (`item_signature` vs `typeck_body` / `mir_body`), and deterministic `emit_query_graph_text` sorted by `(QueryKind, SemanticKey)`.
   - Verifies all 5 cycle/depth diagnostic codes (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`), canonical `SemanticKey` cycle rotation across entry permutations, Tarjan SCC discovery, cascading error suppression on poisoned recovery values, and cold vs warm snapshot-bound diagnostic replay.
2. **Multi-Module Demand-Driven Isolation, Memoization & Fine-Grained Green Reuse (`demand_driven_isolation_and_memo.ax` + `.stdout`)**:
   - Exercises a 3-module workspace (`core::math`, `core::app`, `core::unused`) across Revisions `R1..R4`, verifying unqueried modules remain `Absent` (`hits=0, misses=0`), second-call memo hits in the same revision, body-only edits (`R2`) backdating `item_signature` (`changed_at=R1 < verified_at=R2`) so downstream callers stay green (`0` recomputations), signature-changing edits (`R3`) propagating `changed_at=R3` to direct dependents while leaving unrelated items green, and multi-session `CompilerDB` isolation.
3. **Canonical Cycle Diagnostics, Tarjan SCC Ordering & Cascading Error Suppression (`cycle_recovery_and_cascade_suppression.ax` + `.stdout`)**:
   - Exercises all 5 cycle/depth diagnostics (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`) with canonical JSON diagnostic fields (`code`, `severity`, `primary_span`, `notes`, `cycle_path`), verifies identical canonical cycle rotation (`A -> B -> C -> A`) across all 3 entry permutations (`A`, `B`, `C`), and proves downstream queries reading `Poisoned` recovery values (`TyError`, `ConstError`, `TraitResult::Ambiguous`, `ErrorStub`) suppress secondary cascading errors (`0` secondary diagnostics).
4. **Snapshot-Bound Cold vs Warm Diagnostic Replay & Cycle-Breaking Revision Invalidation (`snapshot_diag_replay_and_invalidation.ax` + `.stdout`)**:
   - Verifies `RevisionSnapshot` immutability across concurrent inputs, cold (`R1`) vs warm (`R2` unchanged inputs, `R3` unrelated module edit) byte-for-byte diagnostic equivalence via `SnapshotDiagnosticBuffer` replay (`0` misses on warm revisions, `0` duplicate emissions inside the same snapshot), and cycle-breaking edit (`R4`) invalidating `Poisoned` entries so the resolved acyclic graph transitions to `Ready` with `0` diagnostics.

## Files changed
- `tests/conformance/p18/e18_1_query_engine/cycle_recovery_and_cascade_suppression.ax`
- `tests/conformance/p18/e18_1_query_engine/cycle_recovery_and_cascade_suppression.stdout`
- `tests/conformance/p18/e18_1_query_engine/demand_driven_isolation_and_memo.ax`
- `tests/conformance/p18/e18_1_query_engine/demand_driven_isolation_and_memo.stdout`
- `tests/conformance/p18/e18_1_query_engine/e18_1_query_engine_oracle.py`
- `tests/conformance/p18/e18_1_query_engine/e18_1_query_engine_oracle.test`
- `tests/conformance/p18/e18_1_query_engine/e18_1_query_engine_probe.ax.in`
- `tests/conformance/p18/e18_1_query_engine/snapshot_diag_replay_and_invalidation.ax`
- `tests/conformance/p18/e18_1_query_engine/snapshot_diag_replay_and_invalidation.stdout`

## Verification
- Snapshot refresh: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T755` -> `OK`.
- Test suite (`-j 1`):
  `python build-snap-T755/tools/axtest.py --root build-snap-T755 --build-dir build-snap-T755/build -j 1 conformance/p18/e18_1_query_engine run/query_db run/query_cycles run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`
  -> `TOTAL 40 PASS 40 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- Architecture check: `python build-snap-T755/tools/archcheck.py` -> `OK`.
- Scope / path ownership check: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T755` -> `0 REFUSED`.

STATUS: COMPLETE round=0
