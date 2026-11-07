# T753 report

## Summary
Implemented `compiler/query/db/mod.ax` (`module compiler.query.db`) for E18.1 (`CompilerDB` tables, demand-driven `QueryStack`, dependency DAG recording, and deterministic `inspect --emit=query-graph`) per `spec/SPEC-21-query-engine-semantic-db.md` (`AXS-QRY-001..013`, `AXS-QRY-020..033`, `INV-QRY-001`):

- **Session-Isolated `CompilerDB` & Immutable `DatabaseSnapshot` (`AXS-QRY-001`, `0153 §3`, `tasks/0533`)**:
  - Encapsulated all input tables, derived query memoization tables, dependency DAG arrays, active `QueryStack`, and snapshot-bound diagnostic accumulators inside `CompilerDB` with zero global mutable state.
  - Added `RevisionId` monotonic revision counter (`R0`, `R1`, ...) and `DatabaseSnapshot` (`query_db_snapshot`) binding an immutable revision view to `session_id` and `current_revision`.
- **Input Query Tables vs Derived Query Tables (`AXS-QRY-002`, `AXS-QRY-004`, `AXS-QRY-032`)**:
  - Implemented the 4 input tables (`SourceFileInput`, `ModuleTreeInput`, `TargetConfigInput`, `PackageGraphInput`) with `Durability` classification (`DURABILITY_LOW`, `DURABILITY_MEDIUM`, `DURABILITY_HIGH`), `Fingerprint128` (128-bit domain-separated `AXH64` content hashes), and `changed_at` revision stamps.
  - Implemented the 10 derived semantic queries (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `const_eval`, `mir_body`, `layout_of`, `effect_summary`).
- **Session-Scoped Typed 32-Bit IDs & Canonical `SemanticKey` (`AXS-QRY-003`)**:
  - Defined 32-bit compact typed IDs (`SourceFileId`, `ModuleId`, `PackageId`, `UnitKey`, `DefId`, `SymbolId`, `TypeId`, `HirId`, `MirBodyId`, `RegionId`, `TraitGoalKey`, `ConstEvalKey`) with `0` = `NONE` and `0xFFFF_FFFF` = `ERROR`.
  - Implemented `SemanticKey` (`package_name`, `module_path`, `item_namespace`, `disambiguator_index`, `canonical_name`, `canonical_type_args`) and `semantic_key_cmp` / `query_key_cmp` providing a total lexicographical order independent of `DefId` or arena allocation order.
- **Demand-Driven `QueryStack`, Automatic Dependency DAG Recording & Memoization (`AXS-QRY-010..012`, `AXS-QRY-033`)**:
  - Implemented `MemoEntry` (`Vacant`, `Computing`, `Ready`, `Poisoned`, `MaybeDirty`) with `verified_at`, `changed_at`, `memo_hits`, `memo_misses`, `provider_runs`, `green_reuses`, forward `dependencies: Vec<QueryKey>` (`deps_offset`, `deps_len`), and reverse `dependents` edges.
  - Enforced the **Header/Body Firewall (`AXS-QRY-004`)**: checking caller `f` (`query_typeck_body(f)`) queries `item_signature(g)` for callees `g` without evaluating `typeck_body(g)` or `mir_body(g)` (unless `g` requires CTFE body evaluation), and `query_db_check_module_signatures` checks all item signatures in a module without evaluating unreferenced function bodies.
  - Implemented shallow verification and backdating (`AXS-QRY-033`) so body-only edits inside a callee keep `item_signature` and `resolve_module` `changed_at` unchanged and reuse caller `typeck_body` green without re-running its provider.
- **Cycle Detection, Canonical Rotation & Snapshot-Bound Diagnostics (`AXS-QRY-020..031`)**:
  - Implemented active `QueryStack` cycle detection (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`), rotating cycle traces to start at the lexicographically smallest `(QueryKind, SemanticKey)` (`AXS-QRY-022`), poisoning all cycle participants (`AXS-QRY-023`), replaying diagnostics deterministically on warm hits (`AXS-QRY-030`), and suppressing cascading `AX_TYP_MISMATCH` errors when upstream inputs are poisoned (`AXS-QRY-031`).
- **Deterministic `inspect --emit=query-graph` Formatter (`AXS-QRY-013`)**:
  - Implemented `query_db_emit_query_graph` sorting all executed derived `QueryKey` nodes lexicographically by `(QueryKind, SemanticKey)` and formatting terminal state (`Ready` / `Poisoned`), `verified_at`, `changed_at`, `hits`, `misses`, and canonical outgoing `caller -> callee` dependency edges.

## Files changed
- compiler/query/db/mod.ax
- tests/run/query_db/demand_driven_firewall.ax
- tests/run/query_db/demand_driven_firewall.stdout
- tests/run/query_db/query_db_engine.test
- tests/run/query_db/query_db_oracle.py
- tests/run/query_db/query_db_probe.ax.in
- tests/run/query_db/query_graph_determinism.ax
- tests/run/query_db/query_graph_determinism.stdout

## Tests
- Built Stage-2 self-hosted compiler inside `build-snap-T753`:
  - `build-snap-T753/build/axiomc2.exe` (`sha256: 3f27878d500d0b49326a9b4e80f706f294422827a5186cdf9363c071c51ba797`)
- Live compiler probe & oracle (`python build-snap-T753/tests/run/query_db/query_db_oracle.py build-snap-T753/build/axiomc2.exe build-snap-T753/build build-snap-T753/build/tmp_qdb build-snap-T753`):
  - `QUERY-DB-ENGINE-OK` (bundles `compiler/query/db/mod.ax` with `tests/run/query_db/query_db_probe.ax.in` and verifies `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` parity on demand-driven evaluation, header/body firewall, shallow verification backdating, allocation-order-independent `SemanticKey` cycle rotation, cascade suppression, and byte-for-byte deterministic `--emit=query-graph` output).
- Targeted `axtest.py` run (`python build-snap-T753/tools/axtest.py -j 1 --compiler build-snap-T753/build/axiomc2.exe --build build-snap-T753/build --root build-snap-T753 run/query_db run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`):
  - `WEAK-NATIVE 0`
  - `TOTAL 14 PASS 14 FAIL 0 SKIP 0 XFAIL 0`
- Architecture check (`python tools/archcheck.py`):
  - `archcheck: 193 files scanned, 0 violations`

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
