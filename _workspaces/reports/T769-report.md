# T769 Report — E18.5: IR Pass Pre/Postcondition Declarations, Effect/Dataflow Proof Certificates & Fail-Closed Gate

## Summary

Implemented the proof-carrying IR pass contract, three-valued static certainty lattice, proof certificate DAG with canonical 128-bit fingerprint caching and transitive invalidation, multi-category effect summaries, bounded symbolic domain proofs, and transactional fail-closed pass execution gate in `compiler/verify/pass_contracts/mod.ax` per `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`AXS-PCT-001..015`, `AXS-PCT-050..053`, `INV-PCT-001`).

1. **Pass Contract Descriptors & Canonical Registry (`AXS-PCT-001..002`)**:
   - Defined `IrLevel` (`Hir`, `Thir`, `Mir`, `OptIr`, `Lir`, `MachIr`), `AnalysisKind` (19 analysis kinds from `Cfg` and `DominatorTree` through `EffectSummary`, `ValueRange`, `KnownBits`, `Nullability`, `CallGraphScc`, and `CostProfile` with topological dependency/invalidation closure `pct_analysis_expand_required` and `pct_analysis_expand_invalidated`), `SemanticProperty` (15 semantic properties and `SEM_PROP_MANDATORY_INTRA_LEVEL`), `ValidationStrategy`, `PassFailurePolicy`, and `PassContract`.
   - Implemented `pct_canonical_contract` covering all 20 canonical pipeline passes across `MIR`, `OptIR`, `ABI`, `LIR`, and `Target/x64`, plus `pct_validate_contract_declaration` rejecting malformed contracts (overlapping `preserved_analyses & invalidated_analyses`, missing postconditions, or missing mandatory intra-level semantic properties).

2. **Three-Valued Static Certainty Lattice & Semantic Firewall (`AXS-PCT-004`, `AXS-PCT-010`)**:
   - Implemented `Certainty` (`Proven`, `Possible`, `Unknown`), `certainty_and`, `certainty_join_paths`, `certainty_degrade_on_boundary` (degrading to `Unknown`/`Possible` on budget exhaustion, FFI/indirect boundaries, volatile/atomic accesses, or FP `NaN`/`-0.0` hazards), `certainty_allows_transform`, and `pct_semantic_firewall_gate` (ensuring `ProfitabilityFact` from `CostProfile` can veto unprofitable transforms but can never override `Possible` or `Unknown` semantic obligations).

3. **Proof Certificates, Canonical `Fingerprint128` Caching & Transitive Invalidation (`AXS-PCT-011`, `AXS-PCT-015`)**:
   - Implemented `PropositionKind` (16 proposition kinds), `FactOrigin` (`SemanticVerifier`, `DataflowEngine`, `EffectEngine`, `SymbolicEngine`, `TrustedBoundary`), `Fingerprint128`, `ProofProvenance`, `ProofCertificate`, `AuditTrailEntry`, and `ProofStore`.
   - `pct_compute_proof_digest` canonicalizes symmetric propositions (`NoAlias`, `MustAlias`) so commuted queries hit the same 128-bit digest cache entry.
   - `proof_store_invalidate_cert`, `proof_store_invalidate_by_analyses`, and `proof_store_notify_ir_mutation` automatically propagate invalidation transitively across `parent_proof_mask` edges in the proof DAG.
   - `FactOrigin.TrustedBoundary` requires explicit policy opt-in (`allow_trusted_boundaries == true`) and a non-zero `trusted_attr_id`, logging an `AuditTrailEntry`; unaudited boundary facts fail closed to `CERTAINTY_UNKNOWN`.

4. **Shared Monotone Dataflow Solver, Multi-Category `PctEffectSummary` & Bounded `SymbolicValueDomain` (`AXS-PCT-012..014`)**:
   - Implemented `pct_solve_monotone_fixpoint` with forward/backward traversal and fail-closed `CERTAINTY_UNKNOWN` degradation on iteration budget exhaustion.
   - Implemented `PctEffectSummary` over `Memory`, `Resource`, `Control`, `Concurrency`, and `External` lattices (`Unknown` never downgrades to `Pure`), `pct_effect_summary_with_implicit_drop`, `pct_effect_callback_within_bound`, `pct_effect_can_dce_or_hoist` (with debug/profile trace non-interference), `pct_effect_can_memoize_comptime`, and `pct_effect_propagate_scc`.
   - Implemented `SymbolicValueDomain` (`Constant`, `Range [lo, hi]`, `Nullability`, `Bitmask`, `Congruence`) and bounded solvers `sym_prove_non_zero`, `sym_prove_shift_in_range`, `sym_prove_in_bounds` (with UTF-8 byte vs Unicode scalar domain mismatch protection), `sym_prove_no_unsigned_add_overflow`, and `sym_domain_refine_range` (with contradiction detection).

5. **Transactional Pass Execution Engine & `--verify-pass-contracts` Gate (`AXS-PCT-003..005`, `AXS-PCT-050..052`)**:
   - Implemented `PassContractEngine`, `MirBodyCheckpoint`, `pct_engine_checkpoint_mir`, `pct_engine_rollback_mir`, `pct_engine_finish_pass`, `pct_emit_contract_trap_diagnostic` (reporting `AX_ICE_INTERNAL` / `AX_ICE_MIR_VERIFY` with `data.stage = "pass_contract"`, `data.pass_id`, `data.detail`), and `pct_format_witness_summary`.

## Files changed

- compiler/verify/pass_contracts/mod.ax
- tests/run/pass_contracts/pass_contracts_engine.test
- tests/run/pass_contracts/pass_contracts_fail_closed_and_effects.ax
- tests/run/pass_contracts/pass_contracts_oracle.py
- tests/run/pass_contracts/pass_contracts_probe.ax.in

## Verification

- Built `axiomc2.exe` in isolated snapshot `build-snap-T769`:
  `python build-snap-T769/tools/build_axiomc.py --root build-snap-T769 --out build-snap-T769/build` -> `BUILD-AXIOMC OK`
- Ran `axtest.py -j 1` on `run/pass_contracts` and targeted canaries:
  `python build-snap-T769/tools/axtest.py --compiler build-snap-T769/build/axiomc2.exe --build-dir build-snap-T769/build -j 1 run/pass_contracts run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 11 PASS 11 FAIL 0 SKIP 0 XFAIL 0`
- Ran architecture layer check:
  `python tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`
- Verified task file ownership & report changes:
  `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T769` -> exits 0 (`0 REFUSED`)

STATUS: COMPLETE round=0
