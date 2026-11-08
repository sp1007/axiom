# T809 Report: E19.3 CompilerDB Semantic Refactorings & LSP `codeAction`

## Summary

Implemented E19.3 (`SPEC-102 §§1..3`: `AXS-REF-001..003`, `AXS-REF-010..014`, `AXS-REF-020..021`, `REQ-TOOL-183`, `REQ-TOOL-186`):

1. **`compiler/refactor/transforms/mod.ax`**:
   - Unified `CompilerDB` refactoring architecture (`AXS-REF-001`) and atomic `RefactorWorkspaceEdit` construction (`AXS-REF-003`) with non-overlapping byte-span verification (`e_i.span_end <= e_{i+1}.span_start`).
   - Mandatory post-transformation `CompilerDB` verification gate (`refactor_verify_and_commit_edit`, `AXS-REF-002`):
     - Rejects any transformation that synthesizes `unsafe` blocks or `@allow_unsafe` without explicit audited user authorization (`REFACTOR_UNSAFE_SYNTHESIS_FORBIDDEN`, `DIAG_UNSAFE_REQUIRED = 3201`).
     - Applies per-document atomic `EditTransaction` batches to `AXEDITOR` buffers in `VfsWorkspace`, re-evaluates `parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, and `mir_body` under the zero-codegen firewall (`ws.codegen_invocations == 0`), and transactionally rolls back all modified buffers via `editor_undo` if verification fails.
   - `refactor_extract_function` (`AXS-REF-010`):
     - Synthesizes helper parameter modes from `CompilerDB` ownership/capability facts (`PARAM_MODE_BY_COPY` for `Copy` values, `PARAM_MODE_READ_VIEW` `view<T>` for read-only `!Copy` values, `PARAM_MODE_MUT_VIEW` `mut_view<T>` for mutated values live after selection, and `PARAM_MODE_BY_MOVE` for `!Copy` values consumed in selection and dead after selection).
     - Synthesizes single and tuple return values for bindings live after the selection, propagates `async`/`.await` and `! ErrorType`/`?` effects, and rejects extractions that cause use-after-move (`DIAG_MOVE_USE_AFTER_MOVE = 3101`), escaping local capability views (`DIAG_CAP_OUTLIVES_OWNER = 3008`), conflicting borrows (`DIAG_BORROW_CONFLICT = 3001`), or unstructured control-flow jumps.
   - `refactor_extract_variable` & `refactor_inline_variable` (`AXS-REF-011`):
     - `extract_variable`: verifies evaluation-order preservation, rejects shadowing/duplicate names (`DIAG_NAME_DUPLICATE = 2002`), and permits multi-occurrence extraction iff the subexpression is pure, `Copy`, and unmutated between occurrences.
     - `inline_variable`: requires an immutable `let` binding with a definite initializer (rejecting `let mut`), enforces `k == 0`, `k == 1`, and `k >= 2` purity/`Copy`/`Drop` invariants, and wraps lower-precedence initializers in `(...)` (`init_precedence < use_context_precedence`).
   - `refactor_populate_match_arms` (`AXS-REF-012`):
     - Expands missing `enum` variants in declaration order (`Unit => todo()`, `Tuple(v0) => todo()`, `Struct { field } => todo()`), `bool` arms (`true`/`false`), and open scalar wildcards (`_ => todo()`) with `APPLICABILITY_HAS_PLACEHOLDERS`, and rejects already-exhaustive `match` expressions.
   - `refactor_organize_imports` (`AXS-REF-013`):
     - Prunes unused private `use` items (`reference_count == 0 && !is_pub_reexport && !is_cfg_gated`), preserves `pub use` re-exports and `@cfg`-gated imports, deduplicates by resolved `SymbolId`, preserves `as` aliases unmerged, and merges contiguous sibling imports into canonical dot-path brace groups (`use std.io.{Read, Write}`).
   - `refactor_change_signature`, `refactor_move_item` & `refactor_convert_capability_view` (`AXS-REF-014`):
     - Coordinated declaration and call-site signature updates, cross-module item moves with re-import synthesis and coherence/privacy gating, and capability-view conversions (`T -> view<T>`, `view<T> -> mut_view<T>`, `let -> let mut`).

2. **`compiler/refactor/code_actions/mod.ax` & `compiler/lsp/handlers/mod.ax`**:
   - Added E19.3 diagnostic codes (`DIAG_CAP_MUT_REQUIRED`, `DIAG_CAP_CONFLICT_READ`, `DIAG_CAP_OUTLIVES_OWNER`, `DIAG_MOVE_ASSIGN_IMMUTABLE`, `DIAG_PAT_NON_EXHAUSTIVE`, `DIAG_UNSAFE_REQUIRED`), `RefactorApplicability` & `CodeActionKind` constants, `LspCodeActionDataToken`, `LspCodeActionItem`, `LspCodeActionResult`, `LspCodeActionResolveResult`, `lsp_handle_code_action`, `lsp_handle_code_action_resolve`, `code_action_evaluate_context`, and `code_action_resolve_and_verify`.
   - Enforces deterministic ordering (`is_preferred` -> `CodeActionKind` tier -> lexicographical `action_id` & `SymbolId`), precondition-gated surfacing (never offering illegal refactorings), and snapshot-pinned `codeAction/resolve` (`LSP_ERR_CONTENT_MODIFIED = -32801` on revision mismatch).

3. **`tests/run/refactor_engine/`**:
   - Added standalone differential `.ax` + `.stdout` tests and the bundled `refactor_engine.test` + `refactor_engine_oracle.py` + `refactor_engine_probe.ax.in` suite verifying all transformations and LSP `codeAction` handlers across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` with `0 WEAK-NATIVE`.

## Verification

Executed in `build-snap-T809`:
```
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/refactor_engine run/lsp_queries
```
- `TOTAL 23 PASS 23 FAIL 0 SKIP 0 XFAIL 0`
- `WEAK-NATIVE 0`

## Files changed
- compiler/lsp/handlers/mod.ax
- compiler/refactor/transforms/mod.ax
- compiler/refactor/code_actions/mod.ax
- tests/run/refactor_engine/refactor_engine.test
- tests/run/refactor_engine/refactor_engine_oracle.py
- tests/run/refactor_engine/refactor_engine_probe.ax.in
- tests/run/refactor_engine/extract_function_ownership_and_views.ax
- tests/run/refactor_engine/extract_function_ownership_and_views.stdout
- tests/run/refactor_engine/extract_and_inline_variable_semantics.ax
- tests/run/refactor_engine/extract_and_inline_variable_semantics.stdout
- tests/run/refactor_engine/populate_match_and_organize_imports.ax
- tests/run/refactor_engine/populate_match_and_organize_imports.stdout
- tests/run/refactor_engine/code_actions_and_verification_gate.ax
- tests/run/refactor_engine/code_actions_and_verification_gate.stdout
