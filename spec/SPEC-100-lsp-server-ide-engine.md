# SPEC-100 — Language Server (`axiomc lsp`), IDE Semantic Engine, `AXEDITOR` / `AXCODEEDITOR` & Thin VS Code Client

- **Status**: draft (T800, 2026-11-08)
- **Owner**: `axiom-architect`
- **Consolidates**: `0101` (`specs/0101`, §1–§13, §18–§22, §27–§29, §38–§43, §48 `AIDE-01..25`), `0146` (`specs/0146`, Part XXVII §3, §20–§24, §31–§37, §40), `0374` (`tasks/0374`, BOOTSTRAP-115 §1–§3, §10–§13), `0448` (`tasks/0448`, BOOTSTRAP-189 §1–§8, §25, §31, §34, §36 `ATOOL-20..26, 33..34, 38..40`), `0450` (`tasks/0450`, BOOTSTRAP-191 §1–§28, §30–§36 `ADIAG-20..36`), `0479` (`tasks/0479`, BOOTSTRAP-220 §1–§15, §65 `ACDB-20..26, 28, 32`), `0664` (`tasks/0664`, BOOTSTRAP-405 §1–§17, §46–§50 `AIDE-01..30`), `0693` (`tasks/0693`, BOOTSTRAP-434 §434.1–§434.4), `0695` (`tasks/0695`, BOOTSTRAP-434 §434.1–§434.5), `0696` (`tasks/0696`, BOOTSTRAP-434 §434.1–§434.6), `1053` (`tasks/1053`, BOOTSTRAP-788 `AXEDITOR` §1–§23, §121–§132 `EDITOR-INV-01..40`), `1054` (`tasks/1054`, BOOTSTRAP-789 `AXCODEEDITOR` §1–§25, §130–§138 `CODE-INV-01..40`)
- **Covers**: `REQ-TOOL-183`, `REQ-TOOL-184`, `REQ-TOOL-185`, `REQ-TOOL-188`, `REQ-TOOL-189`, `REQ-TOOL-191`, `REQ-TOOL-297`, `REQ-TOOL-298`, `REQ-TOOL-299`, `REQ-TOOL-300`
- **Related**: `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md`, `spec/SPEC-03-core-semantics.md`, `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`, `spec/SPEC-12-drop.md`, `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-100 định nghĩa kiến trúc máy chủ ngôn ngữ chuẩn (`axiomc lsp`), bộ máy ngữ nghĩa IDE dựa trên `CompilerDB`, hệ thống đệm văn bản Unicode thích ứng cho tệp lớn (`AXEDITOR`), tầng trình bày mã nguồn nhận biết trình biên dịch (`AXCODEEDITOR`), và phần mở rộng VS Code mỏng (`tools/vscode-axiom`) cho giai đoạn E19.1:
1. **`CompilerDB` là nguồn sự thật ngữ nghĩa duy nhất (`REQ-TOOL-183`, `REQ-TOOL-297`, `REQ-TOOL-298`)**: CLI, máy chủ LSP, trình định dạng, công cụ tái cấu trúc, `AXCODEEDITOR` và giao diện AI dùng chung `CompilerDB` (`SPEC-21`/`SPEC-22`). Cấm mọi bộ phân tích cú pháp, bộ kiểm tra kiểu hoặc mô hình ngữ nghĩa riêng biệt trong IDE/plugin.
2. **Định danh thực thể có kiểu kèm thế hệ (`GenerationalId`, `REQ-TOOL-191`), ổn định qua truy vấn tăng dần (`REQ-TOOL-184`), và tường lửa truy vấn không sinh mã (`REQ-TOOL-185`)**: Các thực thể ngữ nghĩa (`LocalId`, `FunctionId`, `TypeId`, `PlaceId`, `SymbolId`) mang cặp `(index, generation)` phát hiện tham chiếu cũ (stale ID) và ánh xạ hai chiều với `SemanticKey`. Các truy vấn IDE chỉ đánh giá đến tầng AST/HIR/Typeck/Ownership/MIR verification theo nhu cầu mà không bao giờ chạy tối ưu hóa hạ tầng, chọn lệnh LIR hay sinh mã máy.
3. **Phục hồi chương trình dở dang (`REQ-TOOL-188`) & truy vấn IDE tôn trọng ràng buộc (`REQ-TOOL-189`)**: Trên mã nguồn đang gõ dở, trình phân tích tạo các nút phục hồi không mất dữ liệu (`MissingToken`, `IncompleteExpr`, `IncompleteMemberAccess`, `IncompleteType`, `SemanticTombstone`). Gợi ý mã (`completion`), `hover`, `definition`, `references` và `rename` tuân thủ nghiêm ngặt phạm vi từ vựng, quyền truy cập (`pub`/module), trạng thái sở hữu (loại trừ biến đã `move`), năng lực bộ nhớ (`view<T>` so với `mut_view<T>`), và không bao giờ đoán mò ứng viên khi trait/phương thức nhập nhằng.
4. **Đệm văn bản `AXEDITOR` (`REQ-TOOL-299`), trình bày mã `AXCODEEDITOR` (`REQ-TOOL-300`), và phần mở rộng VS Code mỏng (`0101 §38–§41`)**: `AXEDITOR` (`std/editor`, `compiler/lsp/vfs`) cung cấp bộ đệm piece-table/rope thích ứng $O(\log N)$ cho tệp lớn, ánh xạ chính xác byte UTF-8 ↔ dòng/ký tự UTF-16 và cụm grapheme Unicode, cùng giao dịch sửa đổi nguyên tử gắn `RevisionId`. `AXCODEEDITOR` hiển thị tô sáng ngữ nghĩa và gợi ý nội dòng (inlay hints) cho quyền sở hữu/`move`/`view`/`mut_view`/`await`, còn phần mở rộng VS Code chỉ đóng vai trò trình khách LSP mỏng.

---

## 1. Unified Semantic Authority (`CompilerDB`), Generational Entity IDs & No-Codegen Query Firewall

### `AXS-LSP-001` — `CompilerDB` as Single Semantic Authority (`REQ-TOOL-183`, `REQ-TOOL-297`, `REQ-TOOL-298`)

1. **Unified semantic kernel**: The self-hosted compiler database `CompilerDB` (`SPEC-21`, `SPEC-22`) is the sole semantic authority for the command-line compiler (`axiomc check`/`build`), the Language Server (`axiomc lsp`), the code formatter (`axiomc fmt`), the refactoring engine, `AXCODEEDITOR`, and AI developer interfaces (`0101 §1, §5, §48 AIDE-01..03, AIDE-30`, `tasks/0374 §1`, `tasks/0448 §1, §36 ATOOL-20..21`, `tasks/0664 §1, §49`, `tasks/0693 §434.1`, `tasks/0695 §434.1`, `tasks/0696 §434.1`).
2. **Ban on shadow parsers and typecheckers**: External editors, LSP handlers, and IDE plugins SHALL NOT implement a separate Axiom parser, name resolver, type inference pass, trait solver, or ownership/capability checker (`0101 §5 AIDE-02`, `tasks/0448 §1 ATOOL-21`). Every IDE answer is projected directly from memoized `CompilerDB` query tables.
3. **Cold vs warm equivalence**: Long-running in-memory `CompilerDB` sessions inside `axiomc lsp` (`L1` session cache, `SPEC-22 AXS-INC-020`) are strictly a latency optimization (`0101 §42–§43 AIDE-18..19`, `tasks/0664 §3`). For any workspace snapshot at revision `R_curr`, querying `CompilerDB` in an incremental LSP session MUST yield the exact same resolved symbols, types, ownership states, and `AXD-060`-sorted diagnostics as a cold `axiomc check` invocation on the same workspace contents.

### `AXS-LSP-002` — Typed Generational Entity IDs & Stale-Reference Detection (`REQ-TOOL-191`)

1. **Domain-separated generational handles**: Semantic entities managed by `CompilerDB` and exposed to IDE/LSP queries are identified by strongly typed 64-bit generational handles (`SymbolId`, `FunctionId`, `TypeId`, `LocalId`, `PlaceId`, `DeclarationId`, `ExprId`, `RegionId`; `tasks/0479 §3–§4, §65 ACDB-21..22`, `INV-KERN-001`). Raw integer index reuse across deleted or rebuilt entities is forbidden:
   - `slot_index: u32` — 1-based slot index within the domain table (`0` is the sentinel `NONE`).
   - `generation: u32` — non-zero generation counter incremented whenever a slot is retired or reallocated across revisions.
2. **Deterministic stale-ID detection (`ACDB-22`)**: Every table lookup `table.get(id)` validates `id.generation == slot.generation`. Lookup of a handle whose generation no longer matches returns `StaleEntityError` (`Option.None` / `QueryResult.Stale`) rather than silently aliasing a newly allocated declaration, local, or place (`tasks/0479 §4`).
3. **Three distinct identity layers (`0101 §10 AIDE-05, AIDE-15`)**:
   - **Source identity (`SourceSpan`)**: `(SourceFileId, start_byte: u32, end_byte: u32)` locating surface text within a specific revision (`SPEC-01`).
   - **Semantic identity (`SymbolId` / `SemanticKey`)**: Package- and module-qualified structural identity `(PackageId, ModulePath, Namespace, CanonicalName, Disambiguator)` (`SPEC-21 AXS-QRY-003`).
   - **ABI symbol identity (`LinkSymbol`)**: Mangled or `@export` binary symbol name in COFF/ELF/Mach-O/WASM object files (`SPEC-24`, `SPEC-27`). IDE navigation and refactoring operate strictly on `SymbolId` / `SemanticKey`, never on raw source strings or linker symbols.

```axiom
module compiler.lsp.id

pub struct GenerationalId {
    pub slot_index: u32,
    pub generation: u32
}

pub struct SymbolId { pub raw: GenerationalId }
pub struct FunctionId { pub raw: GenerationalId }
pub struct TypeId { pub raw: GenerationalId }
pub struct LocalId { pub raw: GenerationalId }
pub struct PlaceId { pub raw: GenerationalId }

pub enum EntityLookup<T> {
    Found(T),
    NotFound,
    Stale(u32, u32) // (expected_generation, actual_generation)
}
```

### `AXS-LSP-003` — Stable Semantic Identity Across Incremental Edits & Targeted Invalidation (`REQ-TOOL-184`)

1. **Span-independent identity anchoring (`tasks/0448 §4–§5 ATOOL-22`, `tasks/0664 §6 AIDE-03..04`)**: `CompilerDB` interns each declaration's `SymbolId` and `FunctionId` by its `SemanticKey` `(ModuleId, ItemKind, Name, Disambiguator)`. Editing whitespace, comments, or statements inside a function body shifts byte offsets (`SourceSpan`) but preserves the enclosing item's `SymbolId`, `FunctionId`, and `generation`.
2. **Local and place stability within a body**: Within `resolve_module` and `typeck_body`, `LocalId` and `PlaceId` are keyed by `(FunctionId, ScopeDepth, BindingName, LexicalOrdinal)` and retain stable handles across edits outside their lexical block.
3. **Minimal dependency invalidation (`ATOOL-23`, `SPEC-21 AXS-QRY-032..033`, `SPEC-22 AXS-INC-011..013`)**:
   - Updating a single open buffer in `axiomc lsp` increments `RevisionId` (`R_curr -> R_next`) and marks only dependents of the modified `SourceFileId` as `MaybeDirty(R_next)`.
   - Body-only edits inside a function `f` re-evaluate `parse_module`, `typeck_body(f)`, and `ownership_check(f)` on demand while `item_signature(f)` and `InterfaceFingerprint(module)` backdate to `Green(R_next)`. Zero downstream modules are re-typechecked (`SPEC-22 AXS-INC-012`).

### `AXS-LSP-004` — Zero-Codegen Semantic Query Firewall & Versioned Structured Facts (`REQ-TOOL-185`)

1. **No codegen on IDE queries (`ATOOL-24`, `tasks/0374 §3`, `tasks/0448 §3`)**: Evaluating any LSP or IDE query (`publishDiagnostics`, `hover`, `completion`, `definition`, `typeDefinition`, `implementation`, `references`, `prepareRename`, `rename`, `documentSymbol`, `workspace/symbol`, `semanticTokens`, `inlayHint`, `signatureHelp`) SHALL invoke only frontend and semantic verification queries (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `const_eval`, `mir_body`, `layout_of`). It SHALL NEVER invoke `OptIR` optimization passes (`SPEC-70..75`), LIR lowering, ABI lowering, register allocation (`SPEC-77`), machine encoding, object emission, or linking.
2. **Separation of semantic, optimization, and target facts (`0101 §28–§29 AIDE-16..17`, `tasks/0448 §36 ATOOL-36`)**: Structured responses distinguish language-level semantic facts (`TypeId`, `Copy`, `Drop`, `Send`, `Share`, ownership state, `view`/`mut_view` capability provenance, `layout_of`) from profile-dependent optimization facts (`inlined`, `vectorized`, `stack_promoted`) and backend target facts (`register`, `section`).
3. **Versioned machine-readable fact schema (`ATOOL-26, ATOOL-34`, `0101 §27`)**: Every structured semantic explanation or IDE fact payload carries an explicit `schema_version: u32` (`1`), `revision: u64`, and `certainty: SemanticCertainty` (`Proven`, `Inferred`, `Partial`, `Unknown`, `Error`) so IDE clients and AI agents never parse human terminal prose (`0146 §38–§39`).

---

## 2. LSP 3.17 JSON-RPC 2.0 Transport, Incremental VFS & UTF-8 / UTF-16 Coordinate Mapping

### `AXS-LSP-010` — `axiomc lsp` Server Lifecycle, JSON-RPC 2.0 Framing & Request Cancellation (`REQ-TOOL-297`)

1. **CLI entrypoint (`0101 §2, §40`, `tasks/0695 §434.2`)**: `axiomc lsp` (and driver alias `axiom lsp`) starts the canonical Language Server speaking **LSP 3.17** over **JSON-RPC 2.0** (`stdio` by default, with framing `Content-Length: <byte_len>\r\n\r\n<utf8_json_payload>`). Diagnostic and protocol stdout/stderr streams are strictly isolated: JSON-RPC frames are the only bytes written to `stdout` (`INV-LAYER-006`).
2. **Lifecycle state machine**:
   - Before `initialize`: any request other than `initialize` or `exit` returns JSON-RPC error `-32002` (`ServerNotInitialized`).
   - `initialize`: negotiates UTF-16/UTF-8 position encoding (`positionEncoding`: `"utf-16"` default per LSP 3.17, `"utf-8"` when negotiated via `general.positionEncodings`), workspace root URIs, and server capabilities (`textDocumentSync = Incremental`, `hoverProvider`, `completionProvider` with trigger `"."`, `definitionProvider`, `typeDefinitionProvider`, `implementationProvider`, `referencesProvider`, `documentSymbolProvider`, `workspaceSymbolProvider`, `renameProvider` with `prepareProvider = true`, `semanticTokensProvider` with `full`/`delta`, `inlayHintProvider`, `signatureHelpProvider`).
   - `shutdown`: transitions the server to `ShuttingDown`, flushes pending read-only queries, and responds `null`; subsequent requests (except `exit`) return `-32600` (`InvalidRequest`).
   - `exit`: exits with code `0` if preceded by `shutdown`, or `1` otherwise.
3. **Deterministic cancellation (`$/cancelRequest`, `tasks/0664 §49 AIDE-07`)**: Every in-flight read request (`id`) is bound to a `CancellationToken` checked at query boundaries in `CompilerDB`. When `$/cancelRequest` arrives for `id`, or when a newer `textDocument/didChange` supersedes the snapshot required by an uncommitted overlay query, the server aborts the stale evaluation without mutating `CompilerDB` memo tables and replies with JSON-RPC error `-32800` (`RequestCancelled`).

### `AXS-LSP-011` — Incremental Virtual File System (`VFS`) & `CompilerDB` Revision Synchronization

1. **Overlay ownership (`compiler/lsp/vfs`)**: The LSP Virtual File System (`VFS`) maintains an authoritative in-memory overlay map `Uri -> OpenDocument` for all files opened via `textDocument/didOpen`. While a document is open in the VFS, `CompilerDB`'s `source_file_input` reads exclusively from the VFS `AXEDITOR` buffer for that `SourceFileId`, ignoring unsaved or concurrent on-disk versions until `textDocument/didClose` (`tasks/0664 §4`).
2. **Monotonic document versions & revision binding (`AIDE-05..06`, `tasks/1053 EDITOR-INV-11..15`)**:
   - Each `didOpen` / `didChange` carries client `version: i32` and advances `CompilerDB` to a new immutable `DatabaseSnapshot(SnapshotId, RevisionId)`.
   - Every response or notification (`publishDiagnostics`, `semanticTokens`, `inlayHint`, `completion`) is computed against a single pinned `DatabaseSnapshot` and tagged with its `RevisionId` and document `version`. Results from an older `RevisionId` SHALL NEVER overwrite state for a newer revision (`tasks/1054 §127 CODE-INV-08..09`).

### `AXS-LSP-012` — UTF-8 Byte Span ↔ UTF-16 LSP Position & Display Column Conversion

1. **Three distinct coordinate systems (`0146 §21–§23`, `tasks/1053 §5–§8`)**:
   - **Canonical storage coordinate**: `ByteOffset (u32 / u64)` in valid UTF-8 (`SPEC-01 §1`, `INV-KERN-005`). All `CompilerDB` spans (`Span { file: SourceFileId, start: u32, end: u32 }`) use UTF-8 byte offsets.
   - **Unicode scalar / grapheme coordinate**: 0-based Unicode code point index and UAX #29 extended grapheme cluster boundaries used by `AXEDITOR` cursor movement (`EDITOR-INV-21..22`) and human CLI diagnostics (`AXD-062`).
   - **LSP wire coordinate (`LspPosition { line: u32, character: u32 }`)**: 0-based line and 0-based `character` offset in the negotiated `PositionEncodingKind` (`UTF-16` code units by default, where scalar values `U+0000..U+FFFF` count as `1` UTF-16 code unit and supplementary planes `U+10000..U+10FFFF` count as `2` UTF-16 surrogate code units; or `UTF-8` byte units when negotiated).
2. **Exact bidirectional conversion**: `compiler/lsp/vfs` and `std/editor` provide total, $O(\log L)$ line-indexed conversions `byte_offset_to_lsp_pos(buf, byte_offset, encoding) -> LspPosition` and `lsp_pos_to_byte_offset(buf, pos, encoding) -> ByteOffset`:
   - `CRLF` (`\r\n`) and `LF` (`\n`) both advance `line` by `1` (`INV-KERN-005`).
   - Multi-byte UTF-8 sequences (such as Vietnamese `"Xin chào thế giới"`, where `'à'`, `'ế'`, `'ớ'` are 2- or 3-byte UTF-8 sequences but `1` UTF-16 code unit each, and astral symbols `U+1F600` which are 4 UTF-8 bytes and 2 UTF-16 code units) MUST round-trip without splitting a UTF-8 scalar or clamping mid-codepoint (`EDITOR-INV-06, 21`).
   - An out-of-range `character` on a line clamps deterministically to the line's terminal byte offset (before `\r` or `\n`).

---

## 3. `AXEDITOR` Adaptive Piece-Table / Rope Text Buffer & Transaction Model

### `AXS-LSP-020` — `AXEDITOR` Architecture Boundary & Adaptive `TextBuffer` Representation (`REQ-TOOL-299`)

1. **Pure text-editing engine (`tasks/1053 §1–§4, §121 EDITOR-INV-01..03, 27, 30`)**: `AXEDITOR` (`std.editor` and `compiler/lsp/vfs`) is a headless-capable, GUI-independent text buffer and editing engine (`AXEDITOR_ABI_1`). It owns UTF-8 document storage, incremental range edits, line/UTF-16 indexing, cursors, multi-selections, undo/redo history, and immutable snapshots, and never calls GPU/windowing APIs or embeds compiler typechecking logic.
2. **Adaptive storage representation (`tasks/1053 §3, §10–§17, §128–§130`)**: `AXEDITOR` does not force a single data structure onto every file size:
   - **Small documents (`< 4 KiB` default threshold)**: `CompactBuffer` (contiguous UTF-8 byte buffer) for maximum cache locality and zero tree metadata overhead.
   - **Medium / large documents (`>= 4 KiB` or incremental edit stream)**: `PieceTable` / balanced `PieceTree` (or chunked rope) composed of an immutable `OriginalBuffer`, an append-only `AddBuffer`, and a balanced B-tree / red-black tree of `PieceDescriptor { source: BufferKind, start: u64, byte_len: u32 }` nodes (`tasks/1053 §14–§15`).
3. **Seamless representation promotion (`tasks/1053 §17`)**: Promoting a document from `CompactBuffer` to `PieceTree` preserves `DocumentId`, `RevisionId`, `SelectionSet`, undo history, and all byte offsets identically.

```axiom
module std.editor

pub struct TextPosition {
    pub byte_offset: u64
}

pub struct TextRange {
    pub start: TextPosition,
    pub end: TextPosition
}

pub enum BufferSource {
    Original,
    Added
}

pub struct PieceNode {
    pub source: BufferSource,
    pub offset: u64,
    pub byte_len: u32,
    pub line_breaks: u32,
    pub utf16_units: u32,
    pub subtree_bytes: u64,
    pub subtree_lines: u64,
    pub subtree_utf16: u64
}
```

### `AXS-LSP-021` — Piece-Tree Node Aggregates & $O(\log N)$ Large-File Incremental Edits (`REQ-TOOL-299`)

1. **Subtree summary invariants (`tasks/1053 §8, §14`)**: Every interior and leaf node in the `AXEDITOR` `PieceTree` maintains three exact subtree aggregates:
   - `subtree_bytes: u64` — total UTF-8 byte length;
   - `subtree_lines: u64` — total `\n` line break count;
   - `subtree_utf16: u64` — total UTF-16 code unit length.
2. **$O(\log N)$ edit and lookup complexity (`tasks/1053 §13–§15, §128`)**:
   - Inserting, deleting, or replacing a text range of length $k$ in a document of $N$ pieces splits at most 2 leaf pieces, appends $k$ UTF-8 bytes to `AddBuffer`, and rebalances the tree in $O(\log N)$ time without copying the unaffected $O(\text{file\_size})$ bytes.
   - Resolving `line -> byte_offset`, `byte_offset -> (line, utf16_col)`, or `(line, utf16_col) -> byte_offset` descends the subtree aggregates in $O(\log N)$ time without scanning the file from offset `0`.
3. **UTF-8 and grapheme boundary integrity (`EDITOR-INV-01..03, 06, 21..22, 25`)**:
   - Every `TextRange` satisfies `start.byte_offset <= end.byte_offset <= byte_len()` and both endpoints MUST lie on valid UTF-8 scalar boundaries.
   - User-level cursor motion (`move_left`, `move_right`, `delete_backward`, `delete_forward`) steps across UAX #29 extended grapheme cluster boundaries so multi-codepoint sequences (e.g. base vowel + combining tone mark or ZWJ emoji sequences) are never split into corrupt half-clusters.
   - `NewlineMode` (`Lf`, `CrLf`, `Preserve`) is tracked per document (`tasks/1053 §9`); internal normalization or preservation is deterministic and round-trip exact.

### `AXS-LSP-022` — Atomic `EditTransaction`, Multi-Cursor Normalization, Bounded Undo/Redo & Snapshots (`REQ-TOOL-299`)

1. **Transactional mutation (`tasks/1053 §22–§23, EDITOR-INV-04..05, 11..15, 33`)**: Every buffer modification (single edit, multi-cursor edit, LSP `didChange` batch, formatter edit, or refactoring `WorkspaceEdit`) executes inside an atomic `EditTransaction`:
   - Multi-range edits within one transaction are validated for non-overlapping sorted ranges (`e_i.end <= e_{i+1}.start`) and applied deterministically from highest byte offset to lowest (or via cumulative delta mapping) so earlier edits never shift later target spans in the same batch.
   - If any range in the batch is invalid (out of bounds, `start > end`, or mid-UTF-8 codepoint), the entire transaction rolls back cleanly with zero partial mutation (`EDITOR-INV-05`).
   - Committing a non-empty transaction increments `RevisionId` by `1` and emits a deterministic `ChangeSet { from_rev, to_rev, edits }` used for `AXEDITOR.map_range()` and `CompilerDB` incremental invalidation.
2. **Multi-cursor and selection canonicalization (`tasks/1053 §18–§21, EDITOR-INV-06..10`)**: `SelectionSet` stores one or more `Selection { anchor: TextPosition, active: TextPosition, affinity: CursorAffinity }` entries, sorts them by range start, and merges overlapping or adjacent selections after every transaction while remapping surviving carets deterministically across insertions and deletions.
3. **Piece-backed undo/redo & immutable snapshots (`tasks/1053 EDITOR-INV-15..20`)**:
   - `UndoManager` records inverse `TextEdit` slices referencing `OriginalBuffer`/`AddBuffer` pieces rather than cloning the whole document (`EDITOR-INV-16`), bounded by configurable step/byte limits (`EDITOR-INV-19`).
   - `document.snapshot()` returns an $O(1)$ immutable structural view (`DocumentSnapshot { doc_id, revision, piece_root, content_hash }`) safe for concurrent `CompilerDB` query evaluation without locking the UI caret (`EDITOR-INV-15, 31..32`).

---

## 4. Partial-Program Syntax / Semantic Recovery & Non-Cascading Diagnostics

### `AXS-LSP-030` — Complete vs Partial Semantic Mode & Production Verification Barrier (`REQ-TOOL-188`)

1. **Two explicit semantic modes (`tasks/0450 §1–§2, §20, §32–§36 ADIAG-20..24, ADIAG-35`)**:
   - **Complete Semantic Mode (`axiomc build`, `axiomc run`, release/link)**: Requires `0` syntax errors, `0` unresolved names, `0` `ErrorType` / `Unknown` / `Incomplete` nodes, and `SemanticCertainty.Proven` on all ownership, capability, and `Verified MIR` invariants (`INV-PIPE-002`).
   - **Partial Semantic Mode (`axiomc lsp`, `axiomc check`, IDE/AI queries)**: Operates on incomplete, mid-keystroke source files (`REQ-TOOL-188`, `ATOOL-40`). Syntax and semantic tables MAY contain recovery placeholders (`ErrorType`, `DefId.ERROR`, `OwnershipState.Unknown`, `CapabilityState.Incomplete`) so unaffected declarations, expressions, and modules remain fully queryable.
2. **Hard production barrier (`ADIAG-21, 24, 35`)**: Partial semantic facts NEVER constitute a safety proof and SHALL NEVER authorize machine code generation, optimizer transformations (`SPEC-25`), or executable linking. `ErrorType` is strictly a poison/recovery sentinel (`ErrorType != Any`, `ADIAG-22`) and never unifies silently as a valid production type without a root diagnostic already recorded.

### `AXS-LSP-031` — Lossless Syntax & HIR Recovery Nodes (`REQ-TOOL-188`)

When parsing or lowering an incomplete source file in `CompilerDB` (`tasks/0450 §3–§5, §23–§27 ADIAG-25..26`):
1. **Zero silent source mutation (`ADIAG-25..26`)**: The parser NEVER fabricates or deletes bytes in the underlying `SourceFileId` buffer. Synchronizing insertions (such as virtual closing delimiters `)`, `]`, `}` or missing `;`) are represented solely as zero-width `MissingToken` nodes in the lossless CST/AST.
2. **Canonical recovery node taxonomy**:
   - `MissingToken(expected_kind, zero_width_span)`: Synthesized when a required token (e.g. `)`, `}`, `:`, `=`, identifier after `.`) is absent before a synchronization token (`fn`, `struct`, `enum`, `trait`, `impl`, `let`, `return`, `}`, `;`).
   - `IncompleteMemberAccess { base: ExprId, dot_span: Span, partial_ident: Option<SymbolId> }`: Synthesized for trailing `expr.` or `expr.par` at statement/block boundaries (`0101 §6–§7`, `tasks/0450 §12, §15`). Lowered into HIR so `typeck_body` still computes `type_of(base)` and `ownership_state(base)` for completion and hover!
   - `IncompleteCallExpr { callee: ExprId, partial_args: Slice<ExprId>, open_paren_span: Span }`: Synthesized for unclosed `foo(a, ` so `signatureHelp` and expected-argument-type completion (`tasks/0450 §11, §19`) resolve `item_signature(callee)`.
   - `IncompleteType(span)` / `IncompletePattern(span)`: Lowered to `TypeId.ERROR` (`certainty = Incomplete`) on unfinished bindings `let x: = 1`, struct fields `age: `, generic bounds `fn f<T: >(x: T)`, or match arms `Some(v) =>` (`tasks/0450 §23–§26`) while keeping sibling fields, parameters, and enclosing item `SymbolId`s registered in `module_def_map`.
   - `SemanticTombstone(SymbolId, prev_revision)` (`tasks/0450 §27`): Retained for one revision transition when a declaration is deleted or renamed so references report a single root unresolved-symbol diagnostic instead of collapsing the module graph.

### `AXS-LSP-032` — Snapshot-Bound `publishDiagnostics`, Root-Cause Provenance & Cascading Error Suppression (`REQ-TOOL-188`, `REQ-TOOL-298`)

1. **Causal suppression (`tasks/0450 §6–§10, §30–§31 ADIAG-27..29`, `SPEC-21 AXS-QRY-031`, `AXD-044`)**:
   - Every syntax recovery node (`MissingToken`, `IncompleteExpr`, `IncompleteType`) emits at most **one** root `AX_PARSE_*` diagnostic at its primary span and marks its resulting HIR/type carrier as poisoned (`is_error() == true`).
   - Downstream name resolution, type inference, trait solving, exhaustiveness checking (e.g. on a `match` with an `IncompletePattern` or missing arm body, `tasks/0450 §24`), and ownership/capability verification MUST NOT emit secondary derived diagnostics on poisoned inputs.
   - Independent functions, structs, and statements in the same file whose dependency subgraphs do not touch the poisoned node MUST still be checked in full and report all of their genuine diagnostics (`SPEC-21 AXS-QRY-031`).
2. **Deterministic `textDocument/publishDiagnostics` streaming**: On `didOpen` and `didChange`, `axiomc lsp` evaluates the open module's diagnostic query in `CompilerDB` (`SPEC-21 AXS-QRY-030`), converts `AXD-060`-sorted diagnostics to LSP `Diagnostic` objects (mapping `primary` byte spans to UTF-16 `range`, `code` to `"AX_<AREA>_<NAME>"`, `severity` to `1=Error, 2=Warning, 3=Information, 4=Hint`, and `labels`/`notes` to `relatedInformation`), and publishes them tagged with the document `version`.

---

## 5. Constraint-Aware IDE Semantic Queries (Completion, Hover, Navigation & Rename)

### `AXS-LSP-040` — Constraint-Filtered Semantic Code Completion (`textDocument/completion`; `REQ-TOOL-189`)

When `textDocument/completion` is invoked at cursor position `pos` (including on a partial program with `IncompleteMemberAccess` `receiver.` or `IncompleteCallExpr` `callee(`; `0101 §6–§8 AIDE-08`, `tasks/0448 §7, §25`, `tasks/0450 §11–§19, §36 ADIAG-30..32`, `tasks/0664 §11–§12`):
1. **Semantic resolution, never text/regex scraping**: Completion candidates are queried directly from `CompilerDB` (`resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `ownership_state_at`). Active `@cfg(...)` predicates for the workspace target/profile (`tasks/0448 §25`, `SPEC-88`) prune inactive declarations before candidate collection.
2. **Mandatory four-constraint filter (`REQ-TOOL-189`, `ADIAG-31`)**:
   - **Visibility & lexical scope (`tasks/0450 §16`)**: Candidates outside the cursor's lexical scope or module visibility boundary (e.g. non-`pub` fields, private helper functions, or private struct items from another module) are strictly excluded.
   - **Ownership liveness (`tasks/0664 §12`)**: At cursor program point `pos`, any local binding `LocalId` whose ownership state is `Moved(move_span)` or `Uninitialized` is **excluded** from value/receiver completion candidates (or surfaced only in a dedicated disabled/explanatory diagnostic note `"unavailable: value moved at line L"` — never as a valid callable/insertable completion item).
   - **Capability & mutability legality (`view<T>` vs `mut_view<T>`)**: On member completion `receiver.`, `CompilerDB` determines the capability available on `receiver`:
     - If `receiver` is a read-only `view<T>` or an immutable binding `let x: T`, methods requiring `mut_view<Self>` (exclusive write capability) are excluded from primary callable completions.
     - If `receiver` is `let mut x: T`, `mut_view<T>`, or an owned temporary permitting mutable access, both `view<Self>` and `mut_view<Self>` methods are included.
     - If `receiver` has already been moved, methods taking `Self` by value or `view<Self>`/`mut_view<Self>` are rejected.
   - **Expected type & canonical method-resolution precedence (`0101 §6–§8`, `tasks/0450 §18–§19`)**: Candidates are ranked by deterministic semantic tier: (1) inherent fields and inherent `impl T` methods matching expected type `T_expected`, (2) in-scope `trait` methods implemented by `T`, (3) local/module bindings in scope.
3. **Zero arbitrary heuristic disambiguation (`REQ-TOOL-189`, `0101 §8`, `tasks/0450 §18 ADIAG-32`)**: If two in-scope traits `TraitA` and `TraitB` both provide a method `m` for receiver `T` (`AX_TRAIT_AMBIGUOUS_METHOD`), the completion engine SHALL NOT guess or arbitrarily hide one candidate; it MUST return both candidates explicitly qualified with their defining trait (`TraitA.m`, `TraitB.m`) and mark the bare call as ambiguous.

### `AXS-LSP-041` — Semantic Hover: Type, Ownership State, Capability Provenance, Trait Origin & Layout (`textDocument/hover`)

`textDocument/hover` at `pos` queries `CompilerDB` for the innermost semantic node (`ExprId`, `LocalId`, `PlaceId`, `SymbolId`, `TypeId`) covering `pos` (`0146 §33–§36`, `tasks/0448 §8`, `tasks/0664 §13, §15–§17 AIDE-14..18`):
1. **Canonical signature & resolved type**: Renders the canonical Axiom signature (`=` and `.` syntax) and concrete inferred/instantiated type without exposing internal compiler arena numbers (`TypeId(1847)` is never shown in user hover; `0146 §14`).
2. **Ownership & capability state (`0146 §34–§35`, `tasks/0664 §13, §15–§16`)**:
   - For locals and places: reports `ownership: owned | moved (at line L) | copy`, mutability (`let` vs `let mut`), and `Copy`/`Drop`/`Send`/`Share` auto-trait facts.
   - For capabilities (`view<T>`, `mut_view<T>`): reports `capability: read (view<T>) | exclusive write (mut_view<T>)` and the root owner place (`origin: buffer`).
3. **Trait resolution & dispatch mode (`0146 §36`)**: Hovering a method call `x.display()` reports the resolved declaration (`TraitName.method` or inherent `Type.method`), the satisfying `impl` block, and `dispatch: static | dynamic (dyn Trait)`.
4. **Type layout summary (`0146 §33`, `tasks/0448 §2`)**: Hovering a nominal type (`struct`, `enum`, `union`) reports module path, visibility, representation (`@repr(Axiom)` / `@repr(C)` / `@repr(packed)`), and target-resolved `size` and `align` from `layout_of(TypeId)` when layout is known.

### `AXS-LSP-042` — Semantic Navigation: Go-to-Definition, Type Definition, Trait Implementation, References & Symbols

1. **`textDocument/definition` & `textDocument/typeDefinition` (`0101 §9–§10 AIDE-05, AIDE-09`, `tasks/0664 §7`)**: Resolves the `SymbolId` at `pos` (including field accesses, inherent methods, trait methods, `use` imports, and module paths) and returns the exact declaration `Location` (`uri` + UTF-16 `range`). `typeDefinition` jumps to the nominal declaration of `type_of(expr)`.
2. **`textDocument/implementation` (`tasks/0664 §8`)**: When invoked on a `trait` declaration or trait method signature, queries `CompilerDB`'s `TraitDB` / `ImplDB` and returns all `impl Trait for Type` declarations (and concrete method definitions) in deterministic `SemanticKey` order.
3. **`textDocument/references` (`0101 §11 AIDE-07, AIDE-10`, `tasks/0664 §9`)**: Queries the reverse semantic reference graph for `SymbolId` across all loaded workspace modules. Matches are determined strictly by `SymbolId` identity — never by substring/regex search — so identically named variables in other scopes, comments, and string literals are never returned.
4. **`textDocument/documentSymbol` & `workspace/symbol` (`tasks/0448 §6`)**: Emits hierarchical document outlines (`Module`, `Struct`, `Enum`, `Trait`, `Impl`, `Function`, `Const`, `Static`, `Field`, `TypeParam`) from `parse_module` / `module_def_map`, including partially recovered declarations (`AXS-LSP-031`).

### `AXS-LSP-043` — Hygienic Cross-Module & Scoped Semantic Rename (`textDocument/prepareRename`, `textDocument/rename`)

1. **`prepareRename` validation (`0101 §12–§13 AIDE-06, AIDE-11`, `tasks/0664 §10`)**: Verifies that `pos` points to a renameable user workspace symbol (`LocalId`, `FunctionId`, `StructId`, `EnumId`, `TraitId`, `FieldId`, `GenericParamId`, `ModuleId`) and rejects renaming keywords, literals, built-in primitive types (`i32`, `bool`, `view`), or external read-only sysroot/stdlib symbols.
2. **Hygienic `WorkspaceEdit` generation (`0101 §12–§13`)**:
   - Validates that the new identifier is a legal Axiom ASCII identifier (`SPEC-01`) and is not a reserved keyword.
   - Checks for name collisions / shadowing conflicts in every target scope; if renaming `x` to `y` would collide with an existing declaration `y` in the same scope or silently capture an outer/inner binding, `rename` returns a structured JSON-RPC conflict error (`AX_NAME_DUPLICATE` / rename conflict) without emitting a broken edit.
   - Rewrites only tokens bound to the target `SymbolId` (including declaration site, call sites, struct field initializers/projections, `use` imports, and scoped generic type parameters `T -> Item` in `fn max<T>(a: T, b: T) -> T`), leaving string literals `"Vec"`, comments, and unrelated symbols of the same spelling untouched (`0101 §12–§13`).

---

## 6. `AXCODEEDITOR` Semantic Presentation Layer & Thin VS Code Extension

### `AXS-LSP-050` — `AXCODEEDITOR` Presentation Boundary, Highlight Precedence & Semantic Tokens (`REQ-TOOL-300`)

1. **Strict presentation boundary (`tasks/1054 §1–§6, §130 CODE-INV-01..15`)**: `AXCODEEDITOR` (`AXCODEEDITOR_ABI_1`) is the code-specific presentation and interaction layer situated between `AXEDITOR` (text storage) and `CompilerDB` / `axiomc lsp` (semantic truth). `AXCODEEDITOR` owns gutter line numbers, syntax/semantic token presentation, folding regions, diagnostic squiggle anchoring, completion/signature-help popups, and inlay hint overlays, and NEVER duplicates text storage (`CODE-INV-01, 06`) or compiler typechecking (`CODE-INV-02`).
2. **Deterministic highlight layer precedence (`tasks/1054 §8–§11`)**: `AXCODEEDITOR` composites visual spans in strict non-destructive precedence order:
   ```text
   base text -> lexical syntax span -> CompilerDB semantic span -> diagnostic decoration -> selection -> active caret / current line
   ```
   Every presentation span is stamped with `(DocumentId, RevisionId)`. If the underlying `AXEDITOR` buffer advances to `R_{k+1}`, stale presentation spans from `R_k` are range-mapped via `AXEDITOR.map_range()` or discarded — never applied blindly to mutated offsets (`CODE-INV-08..09, 26..27`).
3. **Compiler-driven semantic tokens (`textDocument/semanticTokens/full` & `delta`; `0101 §18`, `tasks/1054 §9`)**: `CompilerDB` classifies tokens into canonical semantic types and modifiers:
   - **Token types**: `namespace` (`module`), `type`, `struct`, `enum`, `interface` (`trait`), `typeParameter`, `parameter`, `variable`, `property` (`field`), `enumMember` (`variant`), `function`, `method`, `keyword`, `comment`, `string`, `number`, `operator`, `decorator` (`@attribute`).
   - **Axiom semantic modifiers**: `declaration`, `definition`, `readonly` (`let`), `modification` (`let mut` / `mut_view`), `static`, `async`, `unsafe`, `ownedValue`, `readView` (`view<T>`), `mutView` (`mut_view<T>`), `movedValue` (`0101 §18`).

### `AXS-LSP-051` — `AXCODEEDITOR` Ownership, Capability, Move & Async Suspension Inlay Visualization (`REQ-TOOL-300`)

1. **Non-mutating virtual overlays (`tasks/1054 §21–§24, §130 CODE-INV-17..18, 21..25`)**: Folding placeholders (`⋯`) and inline hints (`textDocument/inlayHint`) are strictly presentation overlays; they never alter `AXEDITOR` byte offsets, document revisions, or saved file bytes (`CODE-INV-17, 25`). Accepting a completion item or code action always commits through an atomic `AXEDITOR` `EditTransaction` after verifying `RevisionId` (`CODE-INV-21..22`).
2. **Compiler-proven inlay hints (`0101 §19–§22 AIDE-11..13`, `tasks/0664 §14–§16`)**: `axiomc lsp` and `AXCODEEDITOR` expose four categories of toggleable semantic inlay annotations derived from `CompilerDB`:
   - **Inferred type hints**: `: <Type>` on `let name = expr` bindings and closure parameters (`tasks/0664 §14`).
   - **Parameter name hints**: `<param>:` on non-trivial positional call arguments.
   - **Ownership & capability flow hints (`0101 §19–§21`, `tasks/0664 §15–§16`)**:
     - `/* move */` at call arguments or assignments that transfer ownership of a `!Copy` value;
     - `/* view(owner) */` / `/* mut_view(owner) */` showing capability provenance and disjoint field projections (`x.a` vs `x.b` `DISJOINT`, or overlapping region conflicts);
   - **Async state-machine suspension hints (`0101 §22`)**: At `.await` points inside `async fn`, displays the suspension state ordinal and the live locals captured across that `.await` frame (`SPEC-33`).

### `AXS-LSP-052` — Thin VS Code Extension Architecture (`tools/vscode-axiom`; `0101 §38–§41`)

1. **Thin-client rule (`0101 §38–§40, §48 AIDE-02, AIDE-25`, `T802`)**: The official VS Code extension in `tools/vscode-axiom` is a thin UI and transport adapter:
   - `package.json`: registers language ID `"axiom"`, file extensions `[".ax"]`, activation events (`onLanguage:axiom`, `workspaceContains:**/axiom.toml`), configuration properties (`axiom.lsp.path`, `axiom.inlayHints.ownership`, `axiom.inlayHints.types`, `axiom.inlayHints.capabilities`), and semantic token legends matching `AXS-LSP-050`.
   - `language-configuration.json` & `syntaxes/axiom.tmLanguage.json`: provide fast bracket matching, comment toggling (`//`, `/* */`), indentation rules, and lexical fallback highlighting before the LSP handshake completes.
   - `src/extension.ts` (or `.js` client entrypoint): spawns `axiomc lsp` over `stdio`, forwards workspace configuration and LSP requests/notifications verbatim, and renders diagnostics, completions, hovers, semantic tokens, and ownership inlay hints.
2. **Zero semantic logic in the extension (`0101 §39 AIDE-25`)**: `tools/vscode-axiom` SHALL NOT contain any Axiom AST parser, type inference logic, symbol table, or heuristic autocomplete provider. All semantic computation resides in `axiomc lsp` via `CompilerDB`.

---

## 7. Diagnostics, Canonical Examples & Verification Matrix

### `AXS-LSP-060` — LSP & Editor Diagnostic Policy

1. **Shared `AX_<AREA>_<NAME>` diagnostic registry (`0101 §48 AIDE-10`, `spec/diagnostics.md` `AXD-001..020`, `AXD-040`)**: `axiomc lsp` never invents a separate IDE-only error code namespace. Every error or warning published over `textDocument/publishDiagnostics` uses the canonical registered `AX_<AREA>_<NAME>` codes from `spec/diagnostics.md` (`AX_LEX_*`, `AX_PARSE_*`, `AX_NAME_*`, `AX_TYPE_*`, `AX_TRAIT_*`, `AX_MOVE_*`, `AX_INIT_*`, `AX_CAP_*`, `AX_DROP_*`, `AX_UNSAFE_*`, `AX_CONST_*`, `AX_CTM_*`, `AX_CONC_*`, `AX_ASYNC_*`, …).
2. **Tooling `info` and `hint` severities (`spec/diagnostics.md` §5 `AXD-040`)**: While batch `check`/`build` emit `error` and `warning`, `axiomc lsp` MAY attach `info` and `hint` diagnostics (LSP severities `3` and `4`) for non-error editor affordances such as unused-binding dimming or move-site provenance notes, without affecting `axiomc check`/`build` exit codes.
3. **Protocol-level errors**: Malformed JSON-RPC frames, requests before `initialize`, cancelled requests (`$/cancelRequest`), and illegal `rename` targets are reported as standard JSON-RPC 2.0 error responses (`-32700` `ParseError`, `-32600` `InvalidRequest`, `-32602` `InvalidParams`, `-32002` `ServerNotInitialized`, `-32800` `RequestCancelled`) rather than compiler `AX_ICE_*` crashes (`INV-DIAG-007`).

### `AXS-LSP-061` — Positive Canonical Examples

```axiom
// === File: src/buffer.ax ===
module buffer

pub struct PacketBuffer {
    pub len: usize,
    capacity: usize // private field: visible only inside `module buffer`
}

impl PacketBuffer {
    pub fn new(cap: usize) -> PacketBuffer {
        PacketBuffer { len: 0, capacity: cap }
    }

    // Read-only capability receiver (`view<PacketBuffer>`)
    pub fn remaining(self: view<PacketBuffer>) -> usize {
        self.capacity - self.len
    }

    // Exclusive write capability receiver (`mut_view<PacketBuffer>`)
    pub fn reset(self: mut_view<PacketBuffer>) {
        self.len = 0
    }
}

pub fn consume_buffer(buf: PacketBuffer) -> usize {
    buf.len
}
```

```axiom
// === File: src/app.ax (Interactive LSP Session) ===
module app

use buffer.PacketBuffer
use buffer.consume_buffer

pub fn process() -> usize {
    // 1. Unicode UTF-8 <-> UTF-16 span accuracy (`AXS-LSP-012`):
    // Multi-byte Vietnamese text in UTF-8 shifts byte offsets by +5 bytes relative to UTF-16 code units;
    // `byte_offset_to_lsp_pos` maps every subsequent token on the line to its exact UTF-16 column.
    let greeting = "Xin chào thế giới"

    let mut pkt = PacketBuffer.new(64)
    let ro = view(pkt)

    // 2. Capability-filtered completion (`AXS-LSP-040`, `REQ-TOOL-189`):
    // At `ro.` (where `ro: view<PacketBuffer>` in `module app`):
    // - `len` (pub field) -> INCLUDED
    // - `remaining` (`self: view<PacketBuffer>`) -> INCLUDED
    // - `reset` (`self: mut_view<PacketBuffer>`) -> EXCLUDED (requires `mut_view`, only `view` available)
    // - `capacity` (private field of `buffer.PacketBuffer`) -> EXCLUDED (visibility boundary)
    let rem = ro.remaining()

    // At `pkt.` (where `pkt` is `let mut pkt: PacketBuffer`):
    // Both `remaining` and `reset` are INCLUDED; `AXCODEEDITOR` inlay hint shows `/* mut_view(pkt) */`.
    pkt.reset()

    // `consume_buffer(pkt)` transfers ownership; `AXCODEEDITOR` inlay hint shows `/* move pkt */`.
    let used = consume_buffer(pkt)
    rem + used
}
```

### `AXS-LSP-062` — Negative / Partial-Program Canonical Examples

```axiom
// === Scenario 1: Partial-program member completion & moved-value exclusion (`REQ-TOOL-188`, `REQ-TOOL-189`) ===
// In `src/app.ax`, suppose the developer is mid-edit after moving `pkt`:
//
//   let used = consume_buffer(pkt)
//   pkt.
//
// 1. Parser synthesizes `IncompleteMemberAccess { base: pkt, dot_span, partial_ident: None }`
//    and emits a single root syntax diagnostic `AX_PARSE_EXPECTED_TOKEN` without crashing (`AXS-LSP-031`).
// 2. `typeck_body` and `ownership_check` run on the partial HIR (`AXS-LSP-004`, zero codegen).
// 3. `textDocument/completion` at `pkt.` observes `ownership_state(pkt) == Moved` (moved into `consume_buffer`)
//    and EXCLUDES callable instance methods on `pkt`, returning the structured unavailability note
//    ("`pkt` moved at `consume_buffer(pkt)`") instead of offering invalid post-move completions (`AXS-LSP-040`).
// 4. `textDocument/hover` on `pkt` reports `type: buffer.PacketBuffer`, `ownership: moved` (`AXS-LSP-041`).

// === Scenario 2: Ambiguous trait methods are never picked by heuristic (`REQ-TOOL-189`, `0101 §8`) ===
module traits_demo

pub trait ReaderA {
    fn read_word(self: view<Self>) -> u32
}

pub trait ReaderB {
    fn read_word(self: view<Self>) -> u32
}

pub struct Stream {
    pub state: u32
}

impl ReaderA for Stream {
    fn read_word(self: view<Stream>) -> u32 { self.state }
}

impl ReaderB for Stream {
    fn read_word(self: view<Stream>) -> u32 { self.state + 1 }
}

// When both `ReaderA` and `ReaderB` are in scope and the user types `s.read_`:
// - Completion MUST NOT arbitrarily pick `ReaderA.read_word` over `ReaderB.read_word`.
// - It surfaces both disambiguated candidates (`ReaderA.read_word`, `ReaderB.read_word`),
//   and an unqualified `s.read_word()` reports `AX_TRAIT_AMBIGUOUS_METHOD` (`AXS-LSP-040`).
```

### `AXS-LSP-063` — E19.1 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T801` | LSP 3.17 JSON-RPC 2.0 transport (`compiler/lsp/protocol`), incremental VFS (`compiler/lsp/vfs`), `AXEDITOR` adaptive piece-table/rope buffer (`std/editor`) with UTF-8 ↔ UTF-16 mapping, generational IDs (`LocalId`, `FunctionId`, `TypeId`, `PlaceId`, `SymbolId`), and partial-program AST/HIR recovery | `tests/run/lsp_vfs` | `INV-LSP-001` |
| `T802` | `CompilerDB`-backed semantic IDE handlers (`publishDiagnostics`, `hover`, `definition`, `typeDefinition`, `implementation`, `references`, constraint-filtered `completion`, hygienic `rename`, `AXCODEEDITOR` `semanticTokens` & ownership/capability/async `inlayHint`) with zero codegen, `axiomc lsp` CLI (`compiler/driver/lsp_cmd`), and thin VS Code client (`tools/vscode-axiom`) | `tests/run/lsp_queries` | `INV-LSP-002` |
| `T803` | End-to-end E19.1 conformance suite: multi-module incremental LSP sessions, partial-program visibility/ownership/`view`/`mut_view`/trait-ambiguity completion, `AXEDITOR` large-file Unicode edits, `AXCODEEDITOR` highlighting/inlay hints, VS Code extension handshake, and `--interp` vs native equivalence (`0 WEAK-NATIVE`) | `tests/conformance/p19/e19_1_lsp_server` | `INV-LSP-003` |

---

## Sources

- `docs/base/specs/0101 - Axiom — IDE, LSP, Refactoring & AI-native Tooling v0.1.md` (§1–§13, §18–§22, §27–§29, §38–§43, §48 `AIDE-01..25`)
- `docs/base/specs/0146 - Part XXVII — Diagnostics · Error Model · IDELSP · AI-Agent Interface.md` (§3, §20–§24, §31–§37, §40)
- `docs/base/tasks/0374 - BOOTSTRAP-115 — Compiler Tooling, Diagnostics & DeveloperAI Interface.md` (§1–§3, §10–§13)
- `docs/base/tasks/0448 - BOOTSTRAP-189 — Developer Experience, IDE, Tooling & AI-Native Compiler Interface.md` (§1–§8, §25, §31, §34, §36 `ATOOL-20..40`)
- `docs/base/tasks/0450 - BOOTSTRAP-191 — Diagnostics, Error Recovery, IDE Recovery & Partial-Program Semantics.md` (§1–§28, §30–§36 `ADIAG-20..36`)
- `docs/base/tasks/0479 - BOOTSTRAP-220 — AXIOM COMPILER INTERNAL API & DATA MODEL.md` (§1–§15, §65 `ACDB-20..36`)
- `docs/base/tasks/0664 - BOOTSTRAP-405 — Language Server, IDE Semantic Engine & AI-Native Developer Interface.md` (§1–§17, §46–§50 `AIDE-01..30`)
- `docs/base/tasks/0693 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE.md` (§434.1–§434.4)
- `docs/base/tasks/0695 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE.md` (§434.1–§434.5)
- `docs/base/tasks/0696 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE.md` (§434.1–§434.6)
- `docs/base/tasks/1053 - BOOTSTRAP-788 — AXEDITOR.md` (§1–§23, §121–§132 `EDITOR-INV-01..40`)
- `docs/base/tasks/1054 - BOOTSTRAP-789 — AXCODEEDITOR.md` (§1–§25, §130–§138 `CODE-INV-01..40`)
- `spec/SPEC-21-query-engine-semantic-db.md`
- `spec/SPEC-22-incremental-compilation.md`
