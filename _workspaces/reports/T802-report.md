# T802 Report — E19.1 Semantic IDE Queries (`hover`, `definition`, `references`, `completion`, `rename`) & `AXCODEEDITOR` / VS Code Client

## Summary
Implemented the `CompilerDB`-backed semantic IDE query engine (`compiler/lsp/handlers/mod.ax`), the `axiomc lsp` CLI driver entrypoint (`compiler/driver/lsp_cmd/mod.ax`), the thin VS Code extension client (`tools/vscode-axiom/`), and the multi-tier verification suite (`tests/run/lsp_queries/`) per `spec/SPEC-100-lsp-server-ide-engine.md` (`REQ-TOOL-183`, `REQ-TOOL-185`, `REQ-TOOL-188`, `REQ-TOOL-189`, `REQ-TOOL-297`, `REQ-TOOL-298`, `REQ-TOOL-300`, `INV-LSP-002`).

### Key Deliverables
1. **Constraint-Aware Semantic IDE Queries (`compiler/lsp/handlers/mod.ax`)**:
   - `lsp_handle_publish_diagnostics`: Maps `CompilerDB` (`query_typeck_module`) and `VfsWorkspace` diagnostics to UTF-16 `LspRange` coordinates with stable `AX_*` diagnostic codes (`AX_PARSE_*`, `AX_NAME_*`, `AX_TYPE_*`, `AX_OWN_*`, `AX_MOVE_*`, `AX_BORROW_*`) and single-root cascade suppression (`AXS-LSP-005`).
   - `lsp_handle_hover`: Produces the 5-section Hover Markdown card (`AXS-LSP-041`: signature, resolved canonical type + ownership/capability badge, effect/async/unsafe summary, ABI layout size/align/offset, and doc comment) plus `CERTAINTY_EXACT` / `CERTAINTY_RECOVERED` provenance.
   - `lsp_handle_definition`, `lsp_handle_type_definition`, `lsp_handle_implementation`, `lsp_handle_references`, `lsp_handle_document_symbol`, `lsp_handle_workspace_symbol`: Cross-module and local symbol navigation anchored to `LspSymbolId` / `LspTypeId` (`AXS-LSP-042`).
   - `lsp_handle_completion`: Constraint-filtered completion engine (`AXS-LSP-040`) enforcing all 5 semantic filters (lexical scope, module visibility `pub`, active `@cfg`, move/liveness via `moved_locals`, and receiver mutability capability `mut_view<T>` vs `view<T>`) with 6-tier deterministic ranking and explicit trait qualification when multiple in-scope traits provide the same method name.
   - `lsp_handle_prepare_rename`, `lsp_handle_rename`, `lsp_apply_workspace_rename`: Hygienic semantic rename (`AXS-LSP-043`) rejecting built-ins/keywords, detecting target-scope `AX_NAME_DUPLICATE` collisions before edit emission, and applying multi-document transactions via `AXEDITOR`.
   - `lsp_handle_semantic_tokens_full`, `lsp_handle_semantic_tokens_delta`, `lsp_handle_inlay_hints`, `lsp_verify_presentation_span`: `AXCODEEDITOR` semantic intelligence layer (`AXS-LSP-050`, `AXS-LSP-051`, `REQ-TOOL-300`) encoding ownership/capability token modifiers (`ownedValue`, `readView`, `mutView`, `movedOut`, `unsafeContext`, `asyncContext`), non-mutating inlay hints (inferred types, parameter names, `mut_view`/`moved` badges, `.await` suspension states), and 6-tier highlight precedence.
2. **`axiomc lsp` CLI Driver (`compiler/driver/lsp_cmd/mod.ax`)**:
   - Parses `--stdio`, `--position-encoding=utf-16|utf-8`, `--inlay-types`, `--inlay-params`, `--inlay-ownership`, `--inlay-async`, `--version`, and `--help` (`AXS-LSP-070`).
   - Routes JSON-RPC 2.0 requests and notifications across `LspServerSession`, `VfsWorkspace`, and `LspSemanticEngine` while enforcing the `AXS-LSP-004` (`REQ-TOOL-185`) zero-codegen firewall (`codegen_invocations == 0`).
3. **Thin VS Code Extension (`tools/vscode-axiom/`)**:
   - Implemented `package.json`, `language-configuration.json`, `syntaxes/axiom.tmLanguage.json`, `extension.js`, and `README.md` (`AXS-LSP-060..062`, `INV-LSP-002`) delegating all semantic intelligence to `axiomc lsp --stdio` and rendering `AXCODEEDITOR` ownership/capability decorations and commands (`axiom.restartServer`, `axiom.showExpandedMacro`, `axiom.inspectOwnershipRegion`, `axiom.showQueryStats`).

## Files changed
- compiler/driver/lsp_cmd/mod.ax
- compiler/lsp/handlers/mod.ax
- tests/run/lsp_queries/completion_constraints_and_ambiguity.ax
- tests/run/lsp_queries/completion_constraints_and_ambiguity.stdout
- tests/run/lsp_queries/hover_and_navigation.ax
- tests/run/lsp_queries/hover_and_navigation.stdout
- tests/run/lsp_queries/hygienic_rename_and_axcodeeditor_inlays.ax
- tests/run/lsp_queries/hygienic_rename_and_axcodeeditor_inlays.stdout
- tests/run/lsp_queries/lsp_queries_engine.test
- tests/run/lsp_queries/lsp_queries_oracle.py
- tests/run/lsp_queries/lsp_queries_probe.ax.in
- tools/vscode-axiom/README.md
- tools/vscode-axiom/extension.js
- tools/vscode-axiom/language-configuration.json
- tools/vscode-axiom/package.json
- tools/vscode-axiom/syntaxes/axiom.tmLanguage.json

## Verification
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T802`
- `python build-snap-T802/tools/axtest.py -j 1 --root build-snap-T802 --build-dir build-snap-T802/build --compiler build-snap-T802/build/axiomc2.exe run/lsp_queries run/lsp_vfs run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 27 PASS 27 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T802`

STATUS: COMPLETE round=0
