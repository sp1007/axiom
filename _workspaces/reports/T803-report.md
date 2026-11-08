# T803 — E19.1 LSP Server, AXEDITOR/AXCODEEDITOR & VS Code Extension Conformance Suite

## Summary

Authored the Phase 19 (`E19.1` / `T803`) end-to-end conformance test suite in `tests/conformance/p19/e19_1_lsp_server/` covering `SPEC-100-lsp-server-ide-engine.md` (`AXS-LSP-001..004`, `010..012`, `020..022`, `030..032`, `040..043`, `050..052`, `060..063`), `INV-LSP-001..003`, and `REQ-TOOL-183..185`, `REQ-TOOL-188..189`, `REQ-TOOL-191`, `REQ-TOOL-297..300`:

1. **Master Conformance Oracle & Live Compiler Probe (`e19_1_lsp_server_oracle.test`, `e19_1_lsp_server_oracle.py`, `e19_1_lsp_server_probe.ax.in`)**:
   - Validates the thin VS Code client extension in `tools/vscode-axiom/` (`package.json`, `language-configuration.json`, `syntaxes/axiom.tmLanguage.json`, `extension.js`, `README.md`) per `AXS-LSP-052`.
   - Bundles the live `std/editor/mod.ax`, `compiler/query/db/mod.ax`, `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`, `compiler/lsp/handlers/mod.ax`, and `compiler/driver/lsp_cmd/mod.ax` modules with `e19_1_lsp_server_probe.ax.in`, executing in `--interp` and compiling once at `-O0` (`--stack-reserve=67108864 -O0`) to verify byte-for-byte identical output across:
     - End-to-end LSP 3.17 JSON-RPC session lifecycle (`-32002 ServerNotInitialized`, `initialize`, `initialized`, `didOpen`, `didChange`, `publishDiagnostics`, `hover`, `definition`, `typeDefinition`, `implementation`, `references`, `documentSymbol`, `workspace/symbol`, `completion`, `prepareRename`, `rename`, `semanticTokens/full`, `inlayHint`, `$/cancelRequest` & revision-superseding `-32800 RequestCancelled`, `shutdown`, `-32600 InvalidRequest`, `exit`, and `zero_codegen=true`).
     - `AXEDITOR` `CompactBuffer` -> balanced `PieceTree` promotion across 600 incremental edits, subtree summary invariants, UTF-8 <-> UTF-16 span round-tripping on Vietnamese text (`"Xin chào thế giới"` — 22 UTF-8 bytes, 17 UTF-16 code units) and astral emoji, UAX #29 grapheme cluster motion, atomic `EditTransaction` commit/rollback, multi-cursor normalization, and linear undo/redo.
     - Span-independent generational entity ID stability across comment/body edits, `InterfaceFingerprint` backdating, stale-ID rejection (`LOOKUP_STALE` / `SemanticTombstone`), and partial-program recovery (`IncompleteMemberAccess`, `IncompleteExpr`, `IncompleteType`, `MissingToken`) with non-cascading poison suppression and hard production codegen barrier (`can_codegen=false`).
     - Constraint-filtered completions (`view<T>` vs `mut_view<T>` vs moved receiver, private visibility exclusion, trait ambiguity qualification), conflict-checked hygienic rename (`AX_NAME_DUPLICATE = 6001`, built-in/keyword rejection), and `AXCODEEDITOR` semantic token modifiers & non-mutating inlay hints.
2. **Standalone Differential Conformance Fixtures (`--interp` vs native `-O0`/`-O1 --verify-each`)**:
   - `end_to_end_lsp_session_and_zero_codegen.ax` + `.stdout`
   - `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` + `.stdout`
   - `partial_recovery_and_generational_id_stability.ax` + `.stdout`
   - `completion_constraints_rename_and_axcodeeditor.ax` + `.stdout`
3. **Traceability Mapping (`README.md`)**:
   - Maps every `AXS-LSP-*` rule and `INV-LSP-001..003` invariant in `SPEC-100` to the conformance tests.

## Files changed

- tests/conformance/p19/e19_1_lsp_server/README.md
- tests/conformance/p19/e19_1_lsp_server/axeditor_piece_tree_and_vietnamese_utf16_spans.ax
- tests/conformance/p19/e19_1_lsp_server/axeditor_piece_tree_and_vietnamese_utf16_spans.stdout
- tests/conformance/p19/e19_1_lsp_server/completion_constraints_rename_and_axcodeeditor.ax
- tests/conformance/p19/e19_1_lsp_server/completion_constraints_rename_and_axcodeeditor.stdout
- tests/conformance/p19/e19_1_lsp_server/e19_1_lsp_server_oracle.py
- tests/conformance/p19/e19_1_lsp_server/e19_1_lsp_server_oracle.test
- tests/conformance/p19/e19_1_lsp_server/e19_1_lsp_server_probe.ax.in
- tests/conformance/p19/e19_1_lsp_server/end_to_end_lsp_session_and_zero_codegen.ax
- tests/conformance/p19/e19_1_lsp_server/end_to_end_lsp_session_and_zero_codegen.stdout
- tests/conformance/p19/e19_1_lsp_server/partial_recovery_and_generational_id_stability.ax
- tests/conformance/p19/e19_1_lsp_server/partial_recovery_and_generational_id_stability.stdout

## Verification

- `python build-snap-T803/tools/axtest.py -j 1 --root build-snap-T803 --build-dir build-snap-T803/build --compiler build-snap-T803/build/axiomc2.exe conformance/p19/e19_1_lsp_server run/lsp_queries run/lsp_vfs run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 40 PASS 40 FAIL 0 SKIP 0 XFAIL 0`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK`
- `python tools/archcheck.py` -> `196 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T803` -> `OK 12 file(s) ready to stage for T803`

STATUS: COMPLETE round=0
