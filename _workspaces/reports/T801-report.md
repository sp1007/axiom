# T801 Report: E19.1 LSP JSON-RPC Transport, Incremental VFS, AXEDITOR Piece-Table Buffer & Partial-Program Recovery

## Summary

Implemented the foundational IDE/LSP protocol transport, `std.editor` (`AXEDITOR`) Unicode-aware piece-table text buffer, incremental Virtual File System (`VFS`) bridged to `CompilerDB`, generational semantic entity arena, and partial-program syntax/HIR recovery engine specified by `SPEC-100`, `SPEC-21`, and `SPEC-22` (`INV-LSP-001`, `REQ-TOOL-183`, `REQ-TOOL-184`, `REQ-TOOL-188`, `REQ-TOOL-191`, `REQ-TOOL-297`, `REQ-TOOL-298`, `REQ-TOOL-299`).

1. **`std/editor/mod.ax` (`module std.editor`) — `AXEDITOR` Adaptive Text Buffer & Unicode Coordinate Engine (`SPEC-100 §3`, `REQ-TOOL-299`)**:
   - Adaptive dual-representation storage: `CompactBuffer` (`< 4 KiB` default or configurable threshold) automatically promoting to a balanced AVL `PieceTree` (`>= 4 KiB`) backed by an immutable original buffer and append-only `add` buffer.
   - Maintained 3-tuple subtree aggregates (`subtree_bytes`, `subtree_lines`, `subtree_utf16`) across piece splits, insertions, deletions, and AVL rotations (`editor_verify_tree_invariants`) supporting $O(\log N)$ incremental edits on large files.
   - Exact UTF-8 byte offset $\leftrightarrow$ UTF-16/UTF-8 `LspPosition` / `LspRange` conversion (`0146 §22-23`, `AXS-LSP-012`, `AXS-LSP-021`), validated on Vietnamese multi-byte text (`"Xin chào thế giới"` = 22 UTF-8 bytes, 17 UTF-16 code units), astral surrogate pairs (`U+1F600`), and out-of-range column clamping.
   - UAX #29 grapheme cluster boundary navigation (`editor_next_grapheme_offset`, `editor_prev_grapheme_offset`) preserving CRLF pairs and combining mark sequences.
   - Atomic `EditTransaction` batch execution with full rollback on overlapping/invalid ranges, multi-cursor `SelectionSet` sorting/merging, piece-backed undo/redo history, and $O(1)$ immutable `DocumentSnapshot` creation.

2. **`compiler/lsp/protocol/mod.ax` (`module compiler.lsp.protocol`) — LSP 3.17 JSON-RPC 2.0 Transport, Lifecycle & Cancellation (`SPEC-100 §1.1, §1.5, §2.4`)**:
   - `Content-Length` HTTP-style framing parser and writer (`lsp_parse_frame`, `lsp_write_frame`) handling multi-header blocks (`Content-Type` + `Content-Length`), incomplete frames, and malformed header detection (`-32700 ParseError`).
   - Lifecycle state machine (`Uninitialized` $\to$ `Initializing` $\to$ `Running` $\to$ `ShuttingDown` $\to$ `Exited`) enforcing `-32002 ServerNotInitialized` prior to `initialize`, `-32600 InvalidRequest` after `shutdown`, and exit code `0` vs `1` on `exit`.
   - Cooperative `CancellationToken` table supporting explicit `$/cancelRequest` and automatic revision-superseding cancellation on `textDocument/didChange` (`-32800 RequestCancelled`).
   - Versioned fact envelope (`LspFactHeader`: `schema_version`, `revision`, `certainty`, `fallback_reason`).

3. **`compiler/lsp/vfs/mod.ax` (`module compiler.lsp.vfs`) — Incremental VFS, Generational Entity IDs & Partial-Program Recovery (`SPEC-100 §1.2–1.7, §2.1–2.3`)**:
   - Overlay lifecycle (`vfs_did_open`, `vfs_did_change_range`, `vfs_did_change_bytes`, `vfs_did_save`, `vfs_did_close`) synchronizing `std.editor.EditorDocument` with `compiler.query.db.CompilerDB` inputs while enforcing the zero-codegen query firewall (`codegen_invocations == 0`) and `InterfaceFingerprint` downstream backdating.
   - Distinct typed generational IDs (`GenerationalId`, `LspSymbolId`, `FunctionId`, `LspTypeId`, `LocalId`, `PlaceId`, `DeclarationId`, `ExprId`) anchored by span-independent `SemanticKey`s so edits outside a declaration preserve exact `(index, generation)` handles (`REQ-TOOL-184`, `REQ-TOOL-191`), while retired entities advance slot generation and return `LOOKUP_STALE` (`StaleEntityError`) without aliasing.
   - Partial-program syntax/HIR recovery nodes (`MissingToken`, `IncompleteExpr`, `IncompleteMemberAccess`, `IncompleteCallExpr`, `IncompleteType`, `SemanticTombstone`) preserving receiver `LspTypeId`, ownership (`OWNERSHIP_VIEW`, `OWNERSHIP_MUT_VIEW`), and capability (`CAP_READ_ONLY`, `CAP_READ_WRITE`) across trailing `.` edits, poisoning only affected bindings to suppress cascading secondary errors while still typechecking healthy sibling functions (`REQ-TOOL-183`, `REQ-TOOL-188`, `REQ-TOOL-297`, `REQ-TOOL-298`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T801`
- `python build-snap-T801/tools/axtest.py -j 1 --root build-snap-T801 --build-dir build-snap-T801/build --compiler build-snap-T801/build/axiomc2.exe run/lsp_vfs run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`
  - Result: `WEAK-NATIVE 0`, `TOTAL 17 PASS 17 FAIL 0 SKIP 0 XFAIL 0` (verified across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`).
- `python tools/archcheck.py`
  - Result: `archcheck: 196 files scanned, 0 violations`.

## Files changed

- compiler/lsp/protocol/mod.ax
- compiler/lsp/vfs/mod.ax
- std/editor/mod.ax
- tests/run/lsp_vfs/generational_id_and_partial_recovery.ax
- tests/run/lsp_vfs/generational_id_and_partial_recovery.stdout
- tests/run/lsp_vfs/jsonrpc_lifecycle_and_cancellation.ax
- tests/run/lsp_vfs/jsonrpc_lifecycle_and_cancellation.stdout
- tests/run/lsp_vfs/lsp_vfs_engine.test
- tests/run/lsp_vfs/lsp_vfs_oracle.py
- tests/run/lsp_vfs/lsp_vfs_probe.ax.in
- tests/run/lsp_vfs/utf8_utf16_vietnamese_and_axeditor_tree.ax
- tests/run/lsp_vfs/utf8_utf16_vietnamese_and_axeditor_tree.stdout

STATUS: COMPLETE round=0
