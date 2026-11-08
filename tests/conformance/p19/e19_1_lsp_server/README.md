# E19.1 Conformance Suite — LSP Server, `CompilerDB` Semantic IDE Engine, `AXEDITOR` / `AXCODEEDITOR`, and Thin VS Code Extension (`SPEC-100`)

This directory contains the Phase 19 (`E19.1` / `T803`) end-to-end conformance suite for `SPEC-100-lsp-server-ide-engine.md`:
- `e19_1_lsp_server_oracle.test` & `e19_1_lsp_server_oracle.py` — Master conformance oracle validating:
  1. Thin VS Code client extension (`tools/vscode-axiom/package.json`, `language-configuration.json`, `syntaxes/axiom.tmLanguage.json`, `extension.js`, `README.md`),
  2. Live bundled execution of `std/editor/mod.ax`, `compiler/query/db/mod.ax`, `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`, `compiler/lsp/handlers/mod.ax`, and `compiler/driver/lsp_cmd/mod.ax` with `e19_1_lsp_server_probe.ax.in` across `--interp` and native `-O0` compilation (compiled at most once per `<120s` resource budget),
  3. Differential verification (`--interp` vs native `-O1 --verify-each`) of all 4 standalone `.ax` conformance fixtures.
- `end_to_end_lsp_session_and_zero_codegen.ax` — End-to-end LSP 3.17 JSON-RPC session lifecycle (`initialize` -> `initialized` -> `didOpen` -> `didChange` -> `hover` -> `definition` -> `typeDefinition` -> `implementation` -> `references` -> `documentSymbol` -> `workspace/symbol` -> `$/cancelRequest` -> `shutdown` -> `exit`) and the zero-backend-codegen firewall.
- `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` — `AXEDITOR` hybrid `CompactBuffer` -> balanced `PieceTree` promotion across 600 incremental edits, subtree summary invariants (`subtree_bytes`, `subtree_lines`, `subtree_utf16`), and UTF-8 <-> UTF-16 span round-tripping on Vietnamese text (`"Xin chào thế giới"`).
- `partial_recovery_and_generational_id_stability.ax` — Span-independent generational entity ID stability across comment/body edits, stale-ID rejection (`LOOKUP_STALE` / `SemanticTombstone`), and partial-program recovery (`IncompleteMemberAccess`, `IncompleteExpr`, `IncompleteType`, `MissingToken`) with non-cascading poison suppression and hard production codegen barrier.
- `completion_constraints_rename_and_axcodeeditor.ax` — Constraint-filtered completion (visibility, move liveness, receiver capability `view<T>` vs `mut_view<T>`, trait ambiguity qualification), conflict-checked hygienic rename (`AX_NAME_DUPLICATE`), and `AXCODEEDITOR` semantic token modifiers & non-mutating inlay hints.

---

## `SPEC-100` Rule & Invariant Mapping (`AXS-LSP-*` & `INV-LSP-001..003`)

| Rule / Invariant / Req | Normative Requirement (`SPEC-100`) | Conformance Test Coverage |
|---|---|---|
| `AXS-LSP-001` | Single Semantic Authority (`CompilerDB`, `IncrementalEngine`, `DiagnosticEmitter`; zero shadow parser/typechecker) | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `AXS-LSP-002` | Span-Independent Generational Semantic Identity (`FunctionId`, `LocalId`, `PlaceId`, `LspTypeId`, `LspSymbolId` keyed by `SemanticKey`) | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-003` | Versioned Semantic Fact Envelope (`LspFactHeader`: `schema_version`, `revision`, `certainty`, `fallback_reason`) | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-004` | Zero-Codegen Interactive Firewall (`ws.codegen_invocations == 0` and `drv.codegen_invocations == 0` across all IDE queries) | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `AXS-LSP-010` | JSON-RPC 2.0 `Content-Length` Framing, Lifecycle (`-32002 ServerNotInitialized`, `initialize`, `initialized`, `shutdown`, `-32600 InvalidRequest`, `exit`), and Cancellation (`-32800 RequestCancelled`) | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `AXS-LSP-011` | VFS Overlay Ownership (`didOpen`, `didChange`, `didSave`, `didClose`) and `InterfaceFingerprint` Backdating | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-012` | Position Encoding Negotiation (`utf-16` Mandatory Baseline, `utf-8` Negotiated Extension) & Vietnamese `"Xin chào thế giới"` Round-Trip | `e19_1_lsp_server_probe.ax.in`, `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` |
| `AXS-LSP-020` | `AXEDITOR` Hybrid Buffer Representation (`CompactBuffer` <= threshold, balanced `PieceTree` with `(subtree_bytes, subtree_lines, subtree_utf16)` above threshold) | `e19_1_lsp_server_probe.ax.in`, `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` |
| `AXS-LSP-021` | `EditorDocument` Core Types (`ByteOffset`, `LineCol`, `LspPosition`, `TextRange`, `LspRange`, `Selection`, `SelectionSet`, `TextEdit`, `EditTransaction`, `DocumentSnapshot`) | `e19_1_lsp_server_probe.ax.in`, `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` |
| `AXS-LSP-022` | `AXEDITOR` Editing Semantics (UAX #29 Grapheme Cluster Motion, Multi-Cursor Normalization, Atomic `EditTransaction` Rollback, Linear Undo/Redo) | `e19_1_lsp_server_probe.ax.in`, `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` |
| `AXS-LSP-030` | Partial-Program Lexer & Parser Recovery (`MissingToken`, `IncompleteMemberAccess`, `IncompleteExpr`, `IncompleteType`, `IncompleteCall`, `SemanticTombstone`) | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-031` | Partial-Program Type, Capability & Borrow Recovery (`ErrorType` Non-Cascading Poison Suppression, Receiver Type/Capability Preservation) | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-032` | Hard Production Codegen Barrier (`vfs_can_codegen == false` whenever recovery nodes or error diagnostics exist) | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-040` | Constraint-Filtered Completion (Visibility, Move Liveness, Capability `view<T>` vs `mut_view<T>`, Trait Ambiguity Qualification, 4-Tier Ranking) | `e19_1_lsp_server_probe.ax.in`, `completion_constraints_rename_and_axcodeeditor.ax` |
| `AXS-LSP-041` | 5-Section Semantic `textDocument/hover` (Canonical Signature, Ownership/Move State, Capability Provenance, Target Layout `size`/`align`/`@repr`, Doc Comment) | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `AXS-LSP-042` | Semantic Navigation (`definition`, `typeDefinition`, `implementation`, `references`, `documentSymbol`, `workspace/symbol`) | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `AXS-LSP-043` | Hygienic `prepareRename` & Conflict-Checked Cross-Module `rename` (`AX_NAME_DUPLICATE` Rejection, Built-In/Keyword Rejection, Atomic Workspace Edits) | `e19_1_lsp_server_probe.ax.in`, `completion_constraints_rename_and_axcodeeditor.ax` |
| `AXS-LSP-050` | `AXCODEEDITOR` Highlight Layer Precedence, Revision-Bound Presentation Spans, and Semantic Token Modifiers (`ownedValue`, `readView`, `mutView`, `movedValue`) | `e19_1_lsp_server_probe.ax.in`, `completion_constraints_rename_and_axcodeeditor.ax` |
| `AXS-LSP-051` | `AXCODEEDITOR` Non-Mutating Inlay Hints (Inferred Types, Parameter Names, Ownership/Capability Flow, Async Suspension State) | `e19_1_lsp_server_probe.ax.in`, `completion_constraints_rename_and_axcodeeditor.ax` |
| `AXS-LSP-052` | Thin VS Code Extension (`tools/vscode-axiom/` Spawning `axiomc lsp --stdio` with Zero Duplicate Parser/Typechecker in JS/TS) | `e19_1_lsp_server_oracle.py` |
| `AXS-LSP-060` | Diagnostic Parity & Zero-Cascade Guarantee (`publishDiagnostics` Mirrors `DiagnosticEmitter` Codes/Spans/Hints) | `e19_1_lsp_server_probe.ax.in`, `partial_recovery_and_generational_id_stability.ax` |
| `AXS-LSP-061` | Interactive Latency & Memory Determinism (Incremental Keystroke & Query Execution Without Full-Workspace Re-Typecheck) | `e19_1_lsp_server_probe.ax.in`, `axeditor_piece_tree_and_vietnamese_utf16_spans.ax` |
| `AXS-LSP-062` | CLI Driver Entrypoint (`axiomc lsp --stdio`, `--position-encoding`, `--inlay-*`) & Event-Loop Dispatch | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `AXS-LSP-063` | End-to-End Conformance & Differential Parity (`--interp` vs Native Compilation) | `e19_1_lsp_server_oracle.py`, all `.ax` fixtures in this directory |
| `INV-LSP-001` | Single-Brain Semantic Parity & Zero-Codegen Query Firewall | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax`, `partial_recovery_and_generational_id_stability.ax` |
| `INV-LSP-002` | Constraint-Filtered Completion & Conflict-Checked Semantic Rename | `e19_1_lsp_server_probe.ax.in`, `completion_constraints_rename_and_axcodeeditor.ax` |
| `INV-LSP-003` | Cancellation Safety & Revision-Tagged Response Consistency | `e19_1_lsp_server_probe.ax.in`, `end_to_end_lsp_session_and_zero_codegen.ax` |
| `REQ-TOOL-183..185`, `REQ-TOOL-188..189`, `REQ-TOOL-191`, `REQ-TOOL-297..300` | Phase 19 `E19.1` Requirements (`CompilerDB` LSP Server, Incremental VFS, Zero Codegen, Partial Recovery, Constraint-Filtered Completion, Generational IDs, `AXEDITOR`, `AXCODEEDITOR`) | `e19_1_lsp_server_oracle.py`, `e19_1_lsp_server_probe.ax.in`, all `.ax` fixtures |
