# T813 Execution Report: E19.4 Diagnostics UX 2.0 — Causal Provenance Spans, Cascading Suppression, Fix-It Applicator & `axiomc explain`

## Summary

Implemented Diagnostics UX 2.0 (`SPEC-103` §§1..3, §7; `AXS-DIAG-001..022`, `AXS-DIAG-050`; `REQ-TOOL-185`, `REQ-TOOL-186`, `REQ-TOOL-298`; `INV-DIAG-009`):

1. **Multi-Span Causal Provenance Chains & Deterministic 128-Bit `DiagnosticFingerprint` (`compiler/diag/ux2/mod.ax`)**:
   - Implemented `CausalRole` (`Origin`, `Transfer`, `BorrowShared`, `BorrowMut`, `AliasOverlap`, `ContainerMutation`, `SuspensionPoint`, `ScopeExit`, `ObligationOrigin`, `Violation`), `CausalStep`, and `CausalProvenanceChain`.
   - Implemented `ux2_verify_causal_completeness` enforcing mandatory causal provenance spans (`Origin -> Transfer -> Violation` for `AX_MOVE_USE_AFTER_MOVE` / `AX_CTM_STATIC_MOVE_FORBIDDEN`; `Origin -> BorrowShared/BorrowMut -> ContainerMutation/ScopeExit/AliasOverlap -> Violation` plus `region_expr` and `owner_symbol` for `CAP` conflict/escape/relocation diagnostics; `ObligationOrigin -> Violation` plus structural `derivation_path` for `CONC`/`TRAIT`/`DERIVE`/`DYN` obligation failures; `SuspensionPoint -> Violation` for `ASYNC`/`GEN` suspension across `.await`/`yield`).
   - Implemented domain-separated 128-bit `DiagnosticFingerprint` (`DIAG_FP_DOMAIN_V1 = 0x4158494F4D444650u64`, `ux2_compute_fingerprint`) anchored to the enclosing `SemanticKey` and item-relative byte offset so line shifts above an item preserve the exact fingerprint.
   - Implemented UTF-8 extended grapheme display column calculation (`ux2_utf8_display_cols`), internal compiler ID leak prevention (`ux2_check_no_internal_id_leak`), multi-span terminal renderer (`ux2_render_terminal`), and JSON Schema v1 renderer (`ux2_render_json_v1`).

2. **Root-Cause `PoisonTaint` & Cascading Diagnostic Suppression (`compiler/diag/ux2/mod.ax`)**:
   - Implemented `PoisonTaint` (`TAINT_PARSE_RECOVERY`, `TAINT_TYPE_NAME`, `TAINT_OWNERSHIP_CAP`, `TAINT_CONST_TRAIT`), `Ux2DiagTracker`, `ux2_emit_root_error_and_taint`, `ux2_try_emit_dependent_diag`, `ux2_try_emit_ownership_violation`, and `ux2_reinitialize_local`.
   - Suppresses secondary type/name/borrow/move cascades on poisoned symbols while preserving genuine errors on unpoisoned sibling bindings and clearing ownership taint upon local re-initialization (`x = new_val`).

3. **Four-Tier Fix-It Applicability & Transactional `axiomc fix` Engine (`compiler/diag/ux2/mod.ax`, `compiler/driver/explain_cmd/mod.ax`)**:
   - Implemented `Ux2Applicability` (`MachineApplicable`, `HasPlaceholders`, `MaybeIncorrect`, `Unspecified`), `Ux2TextEdit`, `Ux2Fix`, and `ux2_validate_fix_safety` (enforcing UTF-8 boundaries, canonical Axiom syntax hygiene, and rejecting `MachineApplicable` fixes that introduce `unsafe`, `@allow_unsafe`, or `bitcast`).
   - Implemented transactional `ux2_apply_fixes_transactional` with overlap conflict deferral, mandatory `CompilerDB` (`query_parse_module`, `query_module_def_map`, `query_resolve_module`, `query_typeck_body`, `query_mir_body`) re-verification under the zero-codegen firewall (`REQ-TOOL-185`, `REQ-TOOL-186`), monotonic error-count decrease check, and automatic rollback when a fix introduces new errors.

4. **Offline `axiomc explain <AX_CODE>` Encyclopedia & CLI Driver (`compiler/diag/explain/mod.ax`, `compiler/driver/explain_cmd/mod.ax`)**:
   - Implemented 37 compiled-in `ExplainEntry` records covering all 18 core areas (`LEX`, `PARSE`, `NAME`, `TYPE`, `TRAIT`, `PAT`, `MOVE`, `INIT`, `CAP`, `DROP`, `UNSAFE`, `CONST`, `VERIFY`, `FFI`, `LINK`, `IO`, `DRIVER`, `ICE`) and all 12 self-hosted domain prefixes (`CONC`, `ASYNC`, `SIMD`, `TARGET`, `SEC`, `PANIC`, `CTM`, `REFLECT`, `DERIVE`, `GEN`, `DYN`, `QUERY`), with corpus shorthand alias normalization (`E_USE_AFTER_MOVE` -> `AX_MOVE_USE_AFTER_MOVE`, etc.), bidirectional `SPEC-*`/`AXS-*` and `INV-*` citations, and `explain_cmd_execute` (exit `0` on valid code/`--list`, exit `2` with `AX_DRIVER_USAGE`/`AX_DRIVER_UNKNOWN_OPTION` on unknown code or invalid flag).

## Verification

Executed `axtest.py` against `build-snap-T813`:
```
python tools/axtest.py --compiler build-snap-T813/build/axiomc2.exe --root build-snap-T813 --build-dir build-snap-T813/build -j 1 --exclude-requires axiom0-internal run/diag_ux2
```
Result:
- `WEAK-NATIVE 0`
- `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`
- Verified `diag_ux2_probe_bundle.ax` and all 3 standalone fixtures across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` with byte-identical outputs.

## Files changed
- compiler/diag/ux2/mod.ax
- compiler/diag/explain/mod.ax
- compiler/driver/explain_cmd/mod.ax
- tests/run/diag_ux2/causal_provenance_and_fingerprints.ax
- tests/run/diag_ux2/causal_provenance_and_fingerprints.stdout
- tests/run/diag_ux2/poison_taint_cascade_suppression.ax
- tests/run/diag_ux2/poison_taint_cascade_suppression.stdout
- tests/run/diag_ux2/transactional_fix_and_explain_registry.ax
- tests/run/diag_ux2/transactional_fix_and_explain_registry.stdout
- tests/run/diag_ux2/diag_ux2_probe.ax.in
- tests/run/diag_ux2/diag_ux2_oracle.py
- tests/run/diag_ux2/diag_ux2.test
- _workspaces/reports/T813-report.md
