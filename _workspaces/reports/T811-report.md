# T811 Report — E19.3 Semantic Refactoring Engine, Code Actions & `AXDIFF` / `AXMERGE` / `AXPATCH` / `AXHISTORY` / `AXVCS` Conformance Suite

STATUS: COMPLETE

## Summary

Implemented the Phase 19 (`E19.3` / `T811`) end-to-end conformance suite in `tests/conformance/p19/e19_3_refactoring_vcs/` certifying `spec/SPEC-102-refactoring-engine-semantic-vcs.md` (`AXS-REF-001..063`, `INV-REF-001..003`, `REQ-TOOL-183`, `REQ-TOOL-186`, `REQ-TOOL-301..305`):

1. **Master Conformance Oracle & Live Compiler Bundle Probe (`e19_3_refactoring_vcs_oracle.test`, `e19_3_refactoring_vcs_oracle.py`, `e19_3_refactoring_vcs_probe.ax.in`)**:
   - Assembles the live `std/editor/mod.ax`, `std/vcs/mod.ax`, `compiler/query/db/mod.ax`, `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`, `compiler/lsp/handlers/mod.ax`, `compiler/refactor/transforms/mod.ax`, `compiler/refactor/code_actions/mod.ax`, `compiler/refactor/vcs/diff.ax`, `compiler/refactor/vcs/merge.ax`, `compiler/refactor/vcs/patch.ax`, `compiler/refactor/vcs/mod.ax`, and `compiler/driver/refactor_cmd/mod.ax` modules with `e19_3_refactoring_vcs_probe.ax.in`.
   - Executes the bundle under `--interp` and compiles + runs it at most once at `-O0` (`--stack-reserve=67108864`), verifying byte-for-byte identical output and `ws.codegen_invocations == 0` across all refactoring, code-action, and semantic VCS queries.
   - Runs differential verification (`--interp` vs `-O1 --verify-each`) across all 4 standalone `.ax` conformance fixtures.
2. **Before-vs-After Semantics Preservation (`refactoring_semantics_preservation_before_after.ax`)**:
   - Executes real Axiom code before and after `extract_function` (`Copy` by value, `!Copy` read-only by `view<T>`, `!Copy` mutated by `mut_view<T>`, `!Copy` moved & dead after selection), `extract_variable`, precedence-preserving `inline_variable` (`let sum = a + b` inlined into `sum * factor - sum` -> `(a + b) * factor - (a + b)`), `populate_match_arms` (exhaustive enum/bool/scalar matching), `change_signature`, and `convert_capability_view`, certifying identical runtime values in both `--interp` and native modes.
3. **`CompilerDB` Verification Gate, `unsafe` Firewall & LSP `codeAction` / `codeAction/resolve` (`compiler_db_verification_gate_and_code_actions.ax`)**:
   - Verifies ownership and capability precondition gating (`AX_MOVE_USE_AFTER_MOVE = 3101`, `AX_CAP_OUTLIVES_OWNER = 3008`, `AX_NAME_DUPLICATE = 2002`, `AX_BORROW_CONFLICT = 3001`, mutable `let mut` inline rejection, already-exhaustive match rejection), `unsafe` block synthesis prohibition (`AX_UNSAFE_REQUIRED = 3201`) with transactional `AXEDITOR` rollback, deterministic 4-tier `textDocument/codeAction` ranking (`quickfix` preferred -> `refactor.extract` -> `refactor.inline` -> `source.organizeImports`), and snapshot-pinned `codeAction/resolve` (`-32801 ContentModified` on stale revisions).
4. **`AXDIFF` & `AXMERGE` Three-Way Semantic VCS (`axdiff_and_axmerge_three_way_semantic_vcs.ax`)**:
   - Verifies formatting-only CST/AST diffs (`formatting_only == true`, `semantic_change_count == 0`), 9-state status lattice (`Incomparable` never collapsing to `Identical`), intra-module `Moved` (`Exact` evidence), cross-name `Renamed` (`Strong` evidence, never `Exact`), receiver `CapabilityChanged` (`view -> mut_view`, `Breaking`), `@repr(C)` struct `LayoutChanged` (`AbiImpact.Breaking`), three-way `AXMERGE` import union (`BASE={0,1}`, `LEFT=-0+2`, `RIGHT=+3` -> `{1,2,3}`), idempotent convergence, simultaneous rename + body modification auto-merge, structural `RenameIdentityConflict` / `SignatureConflict` with canonical `<<<<<<<`/`|||||||`/`=======`/`>>>>>>>` markers, and post-merge `CompilerDB` `SemanticConflict` downgrade (`AX_MOVE_USE_AFTER_MOVE = 3101`).
5. **`AXPATCH`, `AXHISTORY` & `AXVCS` Determinism (`axpatch_axhistory_and_axvcs_determinism.ax`)**:
   - Verifies span-independent `AXPATCH` AST relocation (`AppliedRelocated`), exact inversion (`axpatch_reverse`), transactional rollback on `CompilerDB` failure, algebraic composition (`axpatch_compose` collapsing chained renames), and semantic rebase (`axpatch_rebase`); `AXHISTORY` 4-hop symbol lineage (`Created -> Renamed -> Moved -> ExtractedFrom`), property-level blame skipping formatting-only commits, and non-resurrected recreation stop (`HISTORY-INV-14`); and `AXVCS` timestamp-independent revision hashes, permutation-invariant `Tree`/`Semantic` snapshots, BLAKE3 corruption detection, atomic CAS ref updates, fast-forward push checks, Git adapter mapping, and CLI exit codes (`0`, `1`, `2`).

## Files changed

- tests/conformance/p19/e19_3_refactoring_vcs/README.md
- tests/conformance/p19/e19_3_refactoring_vcs/axdiff_and_axmerge_three_way_semantic_vcs.ax
- tests/conformance/p19/e19_3_refactoring_vcs/axdiff_and_axmerge_three_way_semantic_vcs.stdout
- tests/conformance/p19/e19_3_refactoring_vcs/axpatch_axhistory_and_axvcs_determinism.ax
- tests/conformance/p19/e19_3_refactoring_vcs/axpatch_axhistory_and_axvcs_determinism.stdout
- tests/conformance/p19/e19_3_refactoring_vcs/compiler_db_verification_gate_and_code_actions.ax
- tests/conformance/p19/e19_3_refactoring_vcs/compiler_db_verification_gate_and_code_actions.stdout
- tests/conformance/p19/e19_3_refactoring_vcs/e19_3_refactoring_vcs_oracle.py
- tests/conformance/p19/e19_3_refactoring_vcs/e19_3_refactoring_vcs_oracle.test
- tests/conformance/p19/e19_3_refactoring_vcs/e19_3_refactoring_vcs_probe.ax.in
- tests/conformance/p19/e19_3_refactoring_vcs/refactoring_semantics_preservation_before_after.ax
- tests/conformance/p19/e19_3_refactoring_vcs/refactoring_semantics_preservation_before_after.stdout
- _workspaces/reports/T811-report.md

## Verification

- Command: `python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p19/e19_3_refactoring_vcs`
- Result: `WEAK-NATIVE 0`, `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`
