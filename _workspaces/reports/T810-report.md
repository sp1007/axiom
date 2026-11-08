# T810 Report — E19.3 Semantic AST Diff/Merge/Patch & Lineage History Engine (`AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, `AXVCS`)

STATUS: COMPLETE

## Summary

Implemented the `CompilerDB`-driven semantic version-control and change-management suite (`AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, `AXVCS`) and CLI subcommands (`axiomc refactor`, `axiomc diff`, `axiomc merge`, `axiomc patch`, `axiomc history`) per `spec/SPEC-102-refactoring-engine-semantic-vcs.md` §§4–7 (`AXS-REF-030`..`AXS-REF-063`, `REQ-TOOL-301`..`REQ-TOOL-305`):

1. **`AXDIFF` (`compiler/refactor/vcs/diff.ax`, `SPEC-102 §4 AXS-REF-030..032`, `REQ-TOOL-301`)**:
   - Multi-layer difference separation (`Byte`, `Trivia`/`CST`, `Ast`, `Semantic`, `Api`, `Abi`) and nine-state `DiffStatus` lattice (`Identical`, `Changed`, `Added`, `Removed`, `Moved`, `Renamed`, `Unknown`, `Unavailable`, `Incomparable`) that never collapses `Unknown`, `Unavailable`, or `Incomparable` into `Identical` (`DIFF-INV-06..07`).
   - Five-level `DiffEvidenceLevel` lattice (`Exact`, `Strong`, `Inferred`, `Heuristic`, `Unknown`) ensuring inferred/structural renames and moves are reported as `Strong` or `Inferred`, never `Exact` (`DIFF-INV-10`).
   - Four-pass structural CST/AST and `SemanticKey` matching classifying `FormattingOnly`, `TriviaOnly`, intra-module declaration reorderings (`Moved`, `DIFF-INV-12`), cross-name `Renamed` / `RenamedAndModified`, cross-module `Moved` / `MovedAndModified`, capability (`view<T>`/`mut_view<T>`), effect, visibility, `unsafe` surface, and `@repr` ABI layout changes (`LayoutChanged`, `AbiImpact.Breaking`), with deterministic `.axdiff` sorting and content-addressed `diff_hash`.
2. **`AXMERGE` (`compiler/refactor/vcs/merge.ax`, `SPEC-102 §5 AXS-REF-040..042`, `REQ-TOOL-302`)**:
   - Normative 3-way (`BASE`, `LEFT`, `RIGHT`) semantic merge with idempotent convergence (`MERGE-INV-02`), disjoint preservation (`MERGE-INV-03`), and zero silent guessing under `MERGE_POLICY_STRICT` (`MERGE-INV-04..05, 40`).
   - Six-level identity matching priority (`SymbolId`/`SemanticKey` -> `MemberId` -> `Rename/Move` -> `AST Path` -> `Token Stream` -> `Text Fallback`), formatting/doc-comment immunity, `use` import set algebra, `Rename + Body` auto-merge with call-site rewrites, `Move + Body` auto-merge, and composite struct/enum/trait member merges.
   - Explicit 11-kind `MergeConflictKind` taxonomy (`DuplicateSymbolAdd`, `ModifyDeleteConflict`, `RenameIdentityConflict`, `MoveDestinationConflict`, `SignatureConflict`, `StructFieldConflict`, `EnumDiscriminantConflict`, `TraitImplCoherenceConflict`, `StatementBodyConflict`, `ImportAliasCollision`, `SemanticVerificationConflict`), deterministic `ConflictId`, canonical 3-way conflict markers (`<<<<<<< LEFT`, `||||||| BASE`, `=======`, `>>>>>>> RIGHT`), and post-merge `CompilerDB` verification gate (`MERGE-INV-31, 38`).
3. **`AXPATCH` (`compiler/refactor/vcs/patch.ax`, `SPEC-102 §6 AXS-REF-050..052`, `REQ-TOOL-303`)**:
   - Content-addressed `PatchId`, five-tier target relocation priority (`SymbolId` -> `QualifiedPath+Sig` -> `AstSubtreeHash` -> `ContextAnchor` -> `ExactByteSpan`) rejecting missing (`TargetNotFound`) or ambiguous (`TargetAmbiguous`) targets, mandatory `Precondition` & `Postcondition` checks, DAG cycle detection, `--dry-run` preview, atomic copy-on-write transactional execution with `CompilerDB` rollback, exact patch inversion (`axpatch_reverse`), sequential composition (`axpatch_compose`), and 3-way semantic rebasing (`axpatch_rebase`).
4. **`AXHISTORY` & `AXVCS` (`std/vcs/mod.ax`, `compiler/driver/refactor_cmd/mod.ax`, `SPEC-102 §7 AXS-REF-060..063`, `REQ-TOOL-304`, `REQ-TOOL-305`)**:
   - Timestamp- and host-independent content-addressed `RevisionId` (`HISTORY-INV-02`), DAG cycle rejection (`HISTORY-INV-38`), symbol-centric lineage graph (`Created`, `Modified`, `Renamed`, `Moved`, `ExtractedFrom`, `InlinedInto`, `SplitInto`, `MergedFrom`, `Removed`) with non-resurrected recreation isolation (`HISTORY-INV-13..14`), and property-level `vcs_blame_symbol_property` skipping formatting-only commits (`HISTORY-INV-15..17`).
   - Content-addressed `VcsObjectStore` (`BLOB`, `TREE`, `SEMANTIC`, `PATCH`, `REVISION`) with read-time integrity verification (`VCS_INTEGRITY_ERROR`), permutation-invariant UTF-8 byte-sorted `Tree` and `SemanticKey`-sorted `Semantic` snapshots, atomic Compare-And-Swap (`CAS`) ref updates, isolated `fetch` (`refs/remotes/*`), fast-forward `push`, `GitAdapter` mapping, and CLI driver entrypoints (`compiler.driver.refactor_cmd`).

## Verification

- `python tools/axtest.py --compiler build-snap-T810/build/axiomc2.exe --root build-snap-T810 --build-dir build-snap-T810/build -j 1 --exclude-requires axiom0-internal run/semantic_vcs` -> `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

## Files changed

- compiler/refactor/vcs/diff.ax
- compiler/refactor/vcs/merge.ax
- compiler/refactor/vcs/patch.ax
- compiler/refactor/vcs/mod.ax
- std/vcs/mod.ax
- compiler/driver/refactor_cmd/mod.ax
- tests/run/semantic_vcs/axdiff_tree_vs_text_and_semantic_diff.ax
- tests/run/semantic_vcs/axdiff_tree_vs_text_and_semantic_diff.stdout
- tests/run/semantic_vcs/axmerge_ast_auto_merge_and_semantic_conflicts.ax
- tests/run/semantic_vcs/axmerge_ast_auto_merge_and_semantic_conflicts.stdout
- tests/run/semantic_vcs/axpatch_atomic_transactions_and_rebase.ax
- tests/run/semantic_vcs/axpatch_atomic_transactions_and_rebase.stdout
- tests/run/semantic_vcs/axhistory_lineage_and_axvcs_determinism.ax
- tests/run/semantic_vcs/axhistory_lineage_and_axvcs_determinism.stdout
- tests/run/semantic_vcs/semantic_vcs.test
- tests/run/semantic_vcs/semantic_vcs_oracle.py
- tests/run/semantic_vcs/semantic_vcs_probe.ax.in
