# BOOTSTRAP-788 — AXEDITOR

**Native Axiom Text Editor Engine, Gap/Rope Text Buffer, UTF-8/Unicode Editing, Cursor & Selection, IME, Composition, Undo/Redo, Multi-Cursor, Search/Replace, Syntax-Aware Editing, Incremental Text Analysis, Large-File Editing, Virtualized Text Rendering & Editor ABI 5.0**

**Status:** FROZEN  
**Namespace:** `AXEDITOR`  
**ABI:** `AXEDITOR_ABI_1`  
**Depends on:** `AXSTANDARD`, `AXGUI`, `AXTASK`, `AXASYNC`, `AXINPUT`, `AXDOC`, `AXCOMPILER`, `AXTEST`

---

# 1. Mục tiêu

`AXEDITOR` là **text-editing engine**, không phải GUI widget.

Nó phải phục vụ:

- `TextBox`
- `SearchBox`
- `CodeEditor`
- AXIDE
- editor của ứng dụng
- document viewer/editor
- large-file editor
- structured/code-aware editing

Kiến trúc:

```text
AXWIDGETS
   │
   ├── TextBox
   ├── SearchBox
   └── CodeEditor
          │
          ▼
       AXEDITOR
          │
    ┌─────┼───────────────┐
    ▼     ▼               ▼
TextBuffer Cursor       Selection
    │       │               │
    ├───────┼───────────────┤
    ▼       ▼               ▼
Undo/Redo  IME          Clipboard
    │
    ▼
Incremental Analysis
    │
 ┌──┴───────────┐
 ▼              ▼
AXCOMPILER     AXDOC
```

---

# 2. Boundary

## AXEDITOR sở hữu

- document model
- text buffer
- insertion/deletion
- cursor
- selection
- multi-cursor
- navigation
- Unicode-aware editing
- line/column mapping
- IME composition
- undo/redo
- search/replace
- clipboard editing semantics
- editor commands
- incremental text change tracking
- syntax-aware editing hooks
- large-file strategy
- viewport model
- text-layout integration contract
- editor state serialization

## Không sở hữu

| Chức năng | Owner |
|---|---|
| TextBox visual control | AXWIDGETS |
| Widget tree | AXGUI |
| Font shaping | AXGUI/text subsystem |
| Window | AXWINDOW |
| Physical keyboard | AXINPUT |
| Compiler semantics | AXCOMPILER |
| Syntax definition authority | AXCOMPILER/AXDOC |
| File system | AXSTORAGE |
| Application session | AXAPPLICATION |
| IDE workspace | AXIDE |
| Rendering GPU | AXGRAPHICS |
| Clipboard platform backend | AXGUI/platform |

---

# 3. Thiết kế nền tảng

AXEDITOR **không dùng một data structure duy nhất cho mọi kích thước file**.

Thay vào đó:

```text
Document
   │
   ├── Small
   │      └── contiguous / compact buffer
   │
   ├── Medium
   │      └── gap-buffer / piece representation
   │
   └── Large
          └── rope/piece-tree/chunked storage
```

Mục tiêu là:

- editing nhanh
- memory locality tốt
- không copy toàn bộ file
- không biến mọi document nhỏ thành cấu trúc phức tạp
- large file vẫn có thể mở nhanh

---

# 4. Canonical Document

```text
Document {
    id: DocumentId
    revision: RevisionId
    encoding: TextEncoding
    newline: NewlineMode
    buffer: TextBuffer
    selections: SelectionSet
    undo: UndoManager
    analysis: AnalysisState
    viewport: ViewportState
    metadata: DocumentMetadata
}
```

---

# 5. Encoding

Axiom mặc định:

```text
UTF-8
```

AXEDITOR phải phân biệt:

```text
Bytes
UTF-8 code units
Unicode scalar values
grapheme clusters
display columns
```

Không được đồng nhất chúng.

---

# 6. Index model

Một vị trí editor:

```text
TextPosition {
    byte_offset: u64
}
```

là canonical storage position.

Các coordinate khác được derive:

```text
byte offset
    ↓
UTF-8 scalar
    ↓
grapheme
    ↓
line
    ↓
visual column
```

Không dùng `column` làm storage identity.

---

# 7. TextRange

```text
TextRange {
    start: TextPosition
    end: TextPosition
}
```

Invariant:

```text
start <= end
```

Range không được chứa pointer trực tiếp vào buffer nếu buffer có thể mutate.

---

# 8. Line model

Document duy trì line index.

```text
LineIndex {
    line_count
    checkpoints[]
}
```

Không bắt buộc lưu object cho từng line.

Với file cực lớn, line index có thể phân cấp:

```text
Document
 └ LineIndex
      ├ block
      ├ block
      └ block
```

---

# 9. Newline model

Hỗ trợ:

```text
LF
CRLF
CR
```

Canonical internal editing representation có thể là LF.

Khi lưu:

```text
LF → selected newline format
```

Nếu document cần preserve mixed newlines:

```text
PRESERVE
```

phải được hỗ trợ.

---

# 10. TextBuffer abstraction

```text
trait TextBuffer {
    fn byte_len() -> u64
    fn read(range: TextRange, dst: &mut [u8]) -> Result<usize>
    fn insert(pos: TextPosition, bytes: &[u8]) -> Result<TextEdit>
    fn delete(range: TextRange) -> Result<TextEdit>
    fn replace(range: TextRange, bytes: &[u8]) -> Result<TextEdit>
    fn line_count() -> u64
}
```

---

# 11. Small document optimization

Với document nhỏ:

```text
TextBuffer
   ↓
CompactBuffer
```

Có thể sử dụng contiguous storage.

Lợi ích:

- cache locality
- ít pointer
- ít metadata
- nhanh khi typing
- serialization đơn giản

Không được ép mọi document vào rope.

---

# 12. Gap Buffer

Gap buffer là implementation tùy chọn:

```text id="r2i4y9"
[content][ GAP ][content]
```

Cursor di chuyển gần gap:

```text
insert
   ↓
write into gap
```

Phù hợp document nhỏ/medium và editing tập trung.

---

# 13. Chunked Buffer

Document lớn sử dụng chunks:

```text
Document
 ├ Chunk
 ├ Chunk
 ├ Chunk
 └ Chunk
```

Mỗi chunk có kích thước bounded.

Mục tiêu:

```text
insert/delete
≈ O(log N) hoặc O(number_of_affected_chunks)
```

thay vì copy toàn bộ document.

---

# 14. Rope/Piece Tree

Implementation large-file có thể dùng balanced tree:

```text
             Root
           /      \
       Node        Node
      /   \       /   \
   Chunk Chunk  Chunk Chunk
```

Mỗi node lưu aggregate:

```text
byte_count
newline_count
```

Do đó:

```text
offset → line
line → offset
```

không cần scan toàn file.

---

# 15. Piece representation

Một implementation có thể giữ:

```text
OriginalBuffer
AddBuffer
```

và piece list:

```text
Piece {
    source
    offset
    length
}
```

Insertion chỉ append vào AddBuffer rồi thay đổi piece metadata.

Điều này đặc biệt hữu ích cho undo và large documents.

---

# 16. Editor không ép implementation

`TextBuffer` là abstraction.

AXEDITOR có thể chọn:

```text
CompactBuffer
GapBuffer
ChunkBuffer
PieceTree
Rope
MappedBuffer
```

theo document profile.

---

# 17. Automatic representation selection

Có thể:

```text
small
 ↓
CompactBuffer

medium
 ↓
GapBuffer / PieceTree

large
 ↓
Chunked/PieceTree
```

Việc chuyển representation phải giữ nguyên:

- DocumentId
- RevisionId
- selections
- undo history
- semantic IDs

nếu conversion được thực hiện.

---

# 18. Cursor

```text
Cursor {
    position: TextPosition
    affinity: CursorAffinity
}
```

```text
CursorAffinity =
    Before
    After
```

Affinity cần thiết tại:

- wrapped lines
- bidi text
- line boundaries
- visual caret placement

---

# 19. Selection

```text
Selection {
    anchor: TextPosition
    active: TextPosition
}
```

Range:

```text
min(anchor, active)
max(anchor, active)
```

Direction được giữ lại để hỗ trợ shift-selection.

---

# 20. Multi-cursor

```text
SelectionSet {
    selections[]
    primary
}
```

Ví dụ:

```text
foo
foo
foo
```

có thể có 3 cursors.

Insertion áp dụng cho từng range nhưng phải xử lý offset từ cuối về đầu hoặc thông qua edit transaction.

---

# 21. Selection normalization

Các selection overlapping phải được canonicalize.

Ví dụ:

```text
[10,20]
[15,30]
```

có thể merge thành:

```text
[10,30]
```

trừ khi operation explicitly yêu cầu giữ chúng riêng.

---

# 22. Edit Transaction

Mọi mutation quan trọng đi qua:

```text
EditTransaction
```

```text
EditTransaction {
    document
    edits[]
    origin
    undo_group
}
```

Pipeline:

```text
begin
 ↓
validate
 ↓
apply edits
 ↓
update line index
 ↓
update selections
 ↓
record undo
 ↓
emit change
 ↓
increment revision
 ↓
commit
```

Nếu failure trước commit:

```text
rollback
```

---

# 23. TextEdit

```text
TextEdit {
    range
    inserted: Bytes
}
```

Có thể biểu diễn:

```text
Insert
Delete
Replace
```

như một primitive `Replace(range, bytes)`.

---

# 24. Edit batching

Typing:

```text
H
e
l
l
o
```

không nhất thiết tạo 5 undo steps.

AXEDITOR có grouping policy:

```text
UndoGroup {
    edits[]
    timestamp
    origin
}
```

Ví dụ một chuỗi typing liên tục có thể là một undo group.

---

# 25. Undo architecture

Undo phải là **operation-based**, không snapshot toàn bộ document cho mỗi keystroke.

```text
UndoStack
 ├ Transaction
 ├ Transaction
 └ Transaction
```

Mỗi transaction có inverse edit.

---

# 26. Redo

```text
undo
 ↓
RedoStack
```

Một edit mới sau undo:

```text
undo
 ↓
new edit
 ↓
redo stack cleared
```

trừ khi collaborative/branch history mode được sử dụng.

---

# 27. Large-file undo

Undo history có giới hạn:

```text
max_bytes
max_transactions
max_memory
```

Khi vượt:

```text
oldest undo entries evicted
```

Không được làm editor crash.

---

# 28. Cursor update after edit

Ví dụ:

```text
before:
cursor = 100

insert 20 bytes at 50
```

cursor trở thành:

```text
120
```

Nếu insertion nằm sau cursor:

```text
100
```

Nếu edit bao quanh cursor:

```text
cursor → defined boundary
```

Tất cả phải deterministic.

---

# 29. Anchor tracking

Selection/cursor có thể dùng anchor objects:

```text
PositionAnchor {
    id
    bias
}
```

Edit engine cập nhật anchors.

Điều này hữu ích cho:

- diagnostics
- code actions
- search highlights
- editor markers

---

# 30. Marker

```text
Marker {
    id
    range
    affinity
}
```

Marker có thể đại diện:

- diagnostic
- breakpoint
- search result
- code lens
- semantic highlight

AXEDITOR chỉ giữ vị trí; semantic meaning thuộc subsystem khác.

---

# 31. Revision

Mỗi committed edit tăng:

```text
RevisionId
```

```text
RevisionId = u64
```

Revision dùng cho:

- async analysis
- stale-result rejection
- undo
- AXIDE synchronization
- diagnostics

---

# 32. ChangeSet

```text
ChangeSet {
    document
    from_revision
    to_revision
    edits[]
}
```

Consumer có thể biết chính xác document thay đổi thế nào.

---

# 33. Incremental analysis

```text
Document
   ↓
ChangeSet
   ↓
AXCOMPILER
   ↓
incremental parse
   ↓
semantic update
```

AXEDITOR không tự quyết định compiler semantics.

Nó chỉ cung cấp precise edits.

---

# 34. Syntax-aware editing

AXEDITOR hỗ trợ hook:

```text
SyntaxProvider {
    classify(range)
    indentation(position)
    matching_delimiter(position)
}
```

Nhưng syntax authority có thể đến từ AXCOMPILER.

---

# 35. Bracket matching

Editor cần hỗ trợ:

```text
()
[]
{}
```

và language-defined delimiters.

API:

```text
editor_matching_delimiter(position)
```

---

# 36. Auto indentation

```text
IndentationProvider
```

có thể dựa trên:

```text
current syntax context
previous line
language rules
```

Không hard-code C-style indentation.

---

# 37. Code-aware hooks

AXEDITOR cung cấp:

```text
EditorSemanticProvider
```

với:

```text
completion
signature
diagnostic
folding
formatting
rename
code action
```

nhưng implementation semantics thuộc AXIDE/AXCOMPILER.

---

# 38. IME

IME là first-class.

Pipeline:

```text
AXINPUT
 ↓
IME backend
 ↓
AXEDITOR
 ↓
CompositionState
 ↓
TextBox / CodeEditor
```

---

# 39. CompositionState

```text
CompositionState {
    range
    text
    selection
    attributes[]
}
```

Composition text chưa nhất thiết là committed document text.

Do đó:

```text
typing Vietnamese/Japanese/Chinese
```

không được phá undo hoặc semantic analysis sai cách.

---

# 40. IME commit

```text
composition_start
 ↓
composition_update
 ↓
composition_update
 ↓
composition_commit
 ↓
EditTransaction
```

Chỉ committed text mới trở thành document revision chính.

---

# 41. IME cancellation

```text
composition_cancel
```

phải khôi phục trạng thái trước composition mà không tạo document edit giả.

---

# 42. Unicode grapheme

Các thao tác:

```text
Backspace
Delete
Left
Right
```

phải có Unicode-aware mode.

Không được xóa nửa grapheme cluster trong default user-facing editing behavior.

Storage vẫn UTF-8 byte-based.

---

# 43. Word navigation

AXEDITOR định nghĩa:

```text
move_word_left()
move_word_right()
delete_word_left()
delete_word_right()
```

Word boundary policy configurable theo locale/language.

---

# 44. Line navigation

```text
move_line_start()
move_line_end()
move_document_start()
move_document_end()

move_up()
move_down()
```

`move_up/down` phải giữ preferred visual column khi có thể.

---

# 45. Visual column

Logical byte offset không nhất thiết bằng visual column.

Ví dụ:

```text
tab
wide Unicode glyph
combining mark
emoji
```

Editor phải dùng text layout service để xác định visual position.

---

# 46. Tabs

Document có thể cấu hình:

```text
TabPolicy {
    width
    insert_spaces
    preserve_tabs
}
```

Indentation policy không được hard-code toàn hệ thống.

---

# 47. Search

API:

```text
SearchQuery {
    pattern
    mode
    case_sensitive
    whole_word
    regex
    direction
}
```

Modes:

```text
Literal
Regex
WholeWord
```

---

# 48. Search execution

Search engine phải hỗ trợ:

```text
forward
backward
selection
document
incremental
```

Large-file search không được yêu cầu copy toàn document vào một string mới.

---

# 49. Regex

Regex là optional capability.

Nếu regex engine không khả dụng:

```text
UnsupportedFeature
```

Không làm crash editor.

Regex phải có:

- execution limit
- memory limit
- cancellation

để tránh pattern pathological làm treo UI.

---

# 50. Replace

```text
ReplaceOptions {
    query
    replacement
    scope
    preview
}
```

`ReplaceAll` phải là một logical edit transaction hoặc nhóm transaction có thể undo thống nhất.

---

# 51. Incremental search

SearchBox:

```text
input
 ↓
search
 ↓
highlight
 ↓
current match
```

Async search phải dùng revision/generation.

---

# 52. Clipboard

AXEDITOR định nghĩa semantic operations:

```text
copy()
cut()
paste()
select_all()
```

Clipboard backend thuộc platform layer.

Copy có thể tạo:

```text
text/plain
text/html?
application/x-axiom-fragment?
```

nhưng rich formats là optional.

---

# 53. Clipboard safety

Paste data phải được coi là untrusted input.

Không execute:

- commands
- macros
- scripts

chỉ vì nội dung clipboard chứa chúng.

---

# 54. Drag selection

Editor phải hỗ trợ:

- character selection
- word selection
- line selection
- rectangular selection

Rectangular selection:

```text
SelectionMode =
    Linear
    Columnar
```

---

# 55. Columnar editing

Ví dụ:

```text
abc
def
ghi
```

có thể chọn cùng visual column.

Implementation không được giả định byte offsets thẳng hàng.

---

# 56. Multi-selection editing

Một command có thể áp dụng:

```text
N selections
```

theo một transaction:

```text
begin
apply all
normalize
record one undo group
commit
```

---

# 57. Viewport

```text
ViewportState {
    top_line
    bottom_line
    horizontal_offset
    vertical_offset
    width
    height
}
```

Editor chỉ render phần cần thiết.

---

# 58. Virtualized text rendering

File:

```text
5,000,000 lines
```

không tạo:

```text
5,000,000 TextBox
```

Thay vào đó:

```text
Document
 ↓
Viewport
 ↓
Visible lines
 ↓
Text layout
 ↓
Draw commands
```

---

# 59. Long-line strategy

Một dòng dài hàng MB không được gây allocation proportional to entire line mỗi frame.

Có thể:

```text
line chunking
visual segment cache
incremental shaping
horizontal virtualization
```

---

# 60. Text layout cache

Cache key:

```text
LayoutCacheKey {
    document_revision
    line_range
    font
    size
    width
    direction
    shaping_options
}
```

Cache phải invalidated chính xác sau edit/theme/font changes.

---

# 61. Rendering architecture

```text
AXEDITOR
   ↓
visible text
   ↓
TextLayout
   ↓
GlyphRuns
   ↓
AXGUI DrawCommands
   ↓
AXGRAPHICS
```

AXEDITOR không gọi GPU trực tiếp.

---

# 62. Syntax highlighting

Syntax spans:

```text
HighlightSpan {
    range
    token_kind
    style_id
}
```

Highlighting có thể incremental.

Không scan lại toàn bộ file sau mỗi keystroke nếu parser có khả năng giới hạn vùng affected.

---

# 63. Semantic highlighting

Semantic spans:

```text
SemanticSpan {
    range
    symbol_id
    semantic_kind
}
```

Nguồn:

```text
AXCOMPILER / AXIDE
```

AXEDITOR chỉ hiển thị.

---

# 64. Diagnostics

```text
EditorDiagnostic {
    id
    range
    severity
    message
    code
}
```

Range nên được neo vào document revision.

Stale diagnostic:

```text
diagnostic.revision != document.revision
```

phải bị reject hoặc remap.

---

# 65. Folding

```text
FoldRegion {
    id
    range
    collapsed
}
```

Fold có thể đến từ:

- syntax
- semantic structure
- manual editor state

Folding không xóa text.

---

# 66. Large file mode

Khi file vượt threshold:

```text
EditorMode =
    Normal
    LargeFile
    ReadOnlyLargeFile
```

Large-file mode có thể disable hoặc giới hạn:

- full semantic analysis
- unlimited undo
- expensive syntax features
- full minimap
- expensive regex

nhưng phải báo rõ state.

---

# 67. Memory mapping

AXEDITOR có thể dùng memory mapping cho read-heavy documents.

Nhưng mapped storage không đồng nghĩa document mutable trực tiếp.

```text
MappedFile
    ↓
TextBuffer view
```

Mutation phải đi qua editor buffer contract.

---

# 68. Lazy loading

Large document có thể:

```text
open metadata
 ↓
map/index
 ↓
load visible region
```

không cần decode toàn file trước khi editor xuất hiện.

---

# 69. Save

Save pipeline:

```text
Document
 ↓
snapshot revision R
 ↓
serialize
 ↓
newline encoding
 ↓
atomic write
 ↓
fsync policy
 ↓
commit saved_revision
```

Nếu document thay đổi trong lúc save:

```text
saved_revision < current_revision
```

và file không được đánh dấu clean sai.

---

# 70. Atomic save

Default safe save:

```text
temp
 ↓
write
 ↓
flush
 ↓
replace
```

Platform-specific implementation thuộc AXSTORAGE nhưng AXEDITOR định nghĩa required semantics.

---

# 71. Save conflict

Nếu external file thay đổi:

```text
disk_revision != loaded_revision
```

AXEDITOR phải báo:

```text
ExternalModification
```

không silently overwrite theo mặc định.

---

# 72. Autosave

Autosave là optional consumer feature.

AXEDITOR có thể expose snapshot API:

```text
editor_snapshot()
```

AXIDE/AXAPPLICATION quyết định:

- khi nào autosave
- nơi lưu
- retention

---

# 73. Session persistence

Editor state có thể serialize:

```text
EditorSession {
    document_id
    revision
    cursor[]
    selections[]
    scroll
    folds
    search_state
}
```

Không serialize plaintext password content vào session nếu control là password editor.

---

# 74. Crash recovery

AXEDITOR cung cấp journal/snapshot hooks.

```text
edit
 ↓
journal
 ↓
crash
 ↓
recover
```

Journal format phải có:

```text
document identity
base revision
transaction
checksum
```

AXAPPLICATION/AXIDE sở hữu session policy.

---

# 75. Concurrency

Một document có **single mutation owner**.

```text
UI/editor thread
    ↓
Document mutation
```

Background:

```text
parse
search
syntax analysis
formatting
```

được phép đọc immutable snapshot.

---

# 76. Immutable snapshots

```text
DocumentSnapshot {
    document_id
    revision
    text_view
}
```

Background task dùng snapshot:

```text
snapshot R100
```

Khi result quay về:

```text
current revision = R103
```

phải kiểm tra compatibility/change mapping.

---

# 77. Change mapping

AXEDITOR có thể cung cấp:

```text
map_position(old_revision, new_revision)
map_range(old_revision, new_revision)
```

để AXIDE remap:

- diagnostics
- completion ranges
- code actions
- semantic spans

---

# 78. Async completion

Completion request:

```text
request {
    document
    revision
    position
}
```

Result:

```text
if compatible(current_revision, request_revision):
    apply
else:
    discard/remap
```

Không để stale completion thay đổi text.

---

# 79. Formatting

AXEDITOR chỉ thực thi edit result.

```text
Formatter
   ↓
TextEdits
   ↓
AXEDITOR
   ↓
transaction
```

Formatter không trực tiếp mutate buffer.

---

# 80. Rename

Tương tự:

```text
AXIDE
 ↓
rename analysis
 ↓
TextEdit[]
 ↓
AXEDITOR transaction
```

Cho phép một rename được undo như một operation.

---

# 81. Code actions

Code action trả:

```text
WorkspaceEdit
```

AXEDITOR áp dụng phần thuộc document của nó.

---

# 82. Editor commands

Chuẩn:

```text
cursor_left
cursor_right
cursor_up
cursor_down
line_start
line_end

page_up
page_down

select_left
select_right
select_line

delete
backspace
delete_word
delete_line

copy
cut
paste

undo
redo

indent
unindent

find
replace
```

---

# 83. Command integration

Các command này expose cho AXWIDGETS:

```text
TextBox
CodeEditor
Menu
Toolbar
Shortcut
```

Do đó:

```text
Ctrl+Z
Ctrl+Y
Ctrl+C
Ctrl+V
Ctrl+A
```

được xử lý thống nhất.

---

# 84. Keymap

```text
KeyBinding {
    key
    modifiers
    command
    context
}
```

Context:

```text
Editor
Selection
Completion
IME
Search
ReadOnly
```

Keymap không được hard-code vào control.

---

# 85. Read-only

Document có:

```text
DocumentMode =
    Editable
    ReadOnly
```

Read-only phải được enforce tại edit transaction layer.

Không chỉ disable UI button.

---

# 86. Protected ranges

Một editor có thể có:

```text
ProtectedRange {
    range
    policy
}
```

Ví dụ:

- generated region
- template marker
- embedded metadata

Edit transaction phải kiểm tra protected ranges.

---

# 87. Embedded documents

AXEDITOR có thể hỗ trợ vùng embedded:

```text
Document
 ├ plain text
 ├ embedded language
 └ embedded language
```

Nhưng parser authority thuộc AXCOMPILER/AXIDE.

---

# 88. Binary data

AXEDITOR mặc định là text editor.

Nếu file không hợp lệ UTF-8:

```text
BinaryDetected
```

policy:

```text
OpenAsBytes
OpenWithReplacement
OpenReadOnly
Reject
```

Không âm thầm phá binary file.

---

# 89. Encoding detection

Có thể detect:

```text
UTF-8
UTF-8 BOM
UTF-16
UTF-32
```

nhưng canonical editor representation vẫn UTF-8.

Encoding conversion phải explicit khi save.

---

# 90. Search indexing

Search trên document lớn có thể sử dụng:

```text
chunk scanning
parallel scan
incremental index
```

nhưng UI phải cancellable.

---

# 91. Search cancellation

```text
SearchTask
   ↓
CancellationToken
```

Nếu document đóng:

```text
cancel
```

Nếu query mới:

```text
cancel old
start new
```

---

# 92. Undo during async operation

Background result không được tự ý inject edit nếu user đã thay đổi document.

Mọi async edit phải:

```text
base_revision
change compatibility
explicit apply
```

---

# 93. Plugin boundary

Custom editor extensions có thể implement:

```text
SyntaxProvider
Formatter
CompletionProvider
CodeActionProvider
EditorCommand
```

Nhưng extension không được có implicit access tới:

- raw process memory
- filesystem
- network
- arbitrary executable code

Capability system của Axiom kiểm soát quyền.

---

# 94. AI integration

AXEDITOR cung cấp semantic context:

```text
EditorContext {
    document_id
    revision
    selection[]
    visible_range
    surrounding_text
    language
}
```

AI subsystem có thể yêu cầu context.

AI **không được trực tiếp mutate buffer**.

Thay vào đó:

```text
AI
 ↓
proposed TextEdit[]
 ↓
preview
 ↓
user/application approval
 ↓
AXEDITOR transaction
```

---

# 95. AI provenance

Mọi AI-generated edit nên có:

```text
EditOrigin =
    User
    Formatter
    Refactor
    AI
    Plugin
    System
```

Nếu origin = AI:

```text
metadata.provenance = AI
```

để AXIDE/AXTEST/audit có thể truy nguyên.

---

# 96. Determinism

Cùng:

```text
document
revision
command
key sequence
configuration
```

phải tạo cùng:

```text
text result
cursor result
selection result
undo structure
```

trong deterministic mode.

---

# 97. Performance targets

Mục tiêu:

| Operation | Target |
|---|---:|
| simple insertion | < 1 ms typical |
| cursor movement | < 0.5 ms typical |
| selection update | < 0.5 ms |
| small document edit | < 1 ms |
| visible-line layout preparation | < 4 ms |
| incremental change notification | < 1 ms |
| search cancellation | immediate/bounded |
| UI-thread allocation per keystroke | ideally 0 |

Đây là target engineering, không phải guarantee trên mọi hardware.

---

# 98. Large-file targets

AXEDITOR phải hướng tới:

```text
100 MB
1 GB
multi-GB
```

với graceful degradation.

Đặc biệt:

```text
open
scroll
search
navigate
small edit
```

không được yêu cầu copy toàn file.

---

# 99. Memory behavior

Mục tiêu:

```text
small document → compact
large document → bounded metadata
visible rendering → viewport-sized
undo → bounded by configured budget
search → streaming/chunked
```

Không tạo:

```text
String copy của toàn file
```

cho mỗi search/analysis.

---

# 100. ABI API

Core:

```text
editor_create()
editor_destroy()

document_open()
document_close()
document_snapshot()

document_byte_len()
document_line_count()
document_read()

document_insert()
document_delete()
document_replace()

editor_apply_transaction()
editor_begin_transaction()
editor_commit_transaction()
editor_rollback_transaction()
```

Cursor:

```text
editor_cursor_add()
editor_cursor_remove()
editor_cursor_move()
editor_cursor_position()

editor_selection_get()
editor_selection_set()
editor_selection_clear()
```

---

# 101. Navigation APIs

```text
editor_move_left()
editor_move_right()
editor_move_up()
editor_move_down()

editor_move_word_left()
editor_move_word_right()

editor_move_line_start()
editor_move_line_end()

editor_move_document_start()
editor_move_document_end()

editor_page_up()
editor_page_down()
```

---

# 102. Edit APIs

```text
editor_insert()
editor_backspace()
editor_delete()
editor_delete_word()
editor_delete_line()

editor_indent()
editor_unindent()

editor_copy()
editor_cut()
editor_paste()
```

---

# 103. Undo APIs

```text
editor_undo()
editor_redo()

editor_begin_undo_group()
editor_end_undo_group()

editor_can_undo()
editor_can_redo()
```

---

# 104. Search APIs

```text
editor_search()
editor_search_next()
editor_search_previous()

editor_replace()
editor_replace_all()

editor_cancel_search()
```

---

# 105. Analysis APIs

```text
editor_set_syntax_provider()
editor_set_semantic_provider()

editor_set_diagnostics()
editor_set_highlights()
editor_set_fold_regions()

editor_map_position()
editor_map_range()
```

---

# 106. View APIs

```text
editor_set_viewport()
editor_get_viewport()

editor_scroll_to()
editor_scroll_line()

editor_visible_range()
editor_visual_position()
```

---

# 107. IME APIs

```text
editor_composition_start()
editor_composition_update()
editor_composition_commit()
editor_composition_cancel()

editor_composition_state()
```

---

# 108. Snapshot APIs

```text
editor_snapshot()
snapshot_revision()
snapshot_read()
snapshot_range()
snapshot_line()
```

Snapshots phải có immutable semantics.

---

# 109. Persistence APIs

```text
editor_save()
editor_save_snapshot()

editor_is_dirty()
editor_saved_revision()

editor_create_recovery_journal()
editor_recover()
```

---

# 110. Configuration APIs

```text
editor_set_tab_policy()
editor_set_newline_policy()
editor_set_encoding()
editor_set_read_only()

editor_set_undo_limit()
editor_set_large_file_policy()
editor_set_keymap()
```

---

# 111. Error model

```text
EditorError =
    InvalidDocument
    InvalidRange
    InvalidPosition
    InvalidRevision
    InvalidEdit
    ReadOnly
    ProtectedRange
    EncodingError
    BufferError
    UndoLimit
    SearchError
    RegexLimit
    Cancelled
    ResourceLimit
    StaleRequest
    Conflict
    RecoveryError
```

Sử dụng:

```text
Result<T, EditorError>
```

---

# 112. ABI object identity

```text
DocumentId = u64
RevisionId = u64
CursorId = u64
SelectionId = u64
MarkerId = u64
```

Không expose internal buffer pointer như public ABI.

---

# 113. ABI stability

`AXEDITOR_ABI_1` phải cố định:

- handle size
- enum representation
- error ABI
- callback ABI
- snapshot ABI
- edit ABI
- revision semantics
- encoding semantics

Thay đổi breaking tạo ABI version mới.

---

# 114. Testing architecture

AXTEST phải kiểm tra:

```text
buffer
cursor
selection
unicode
IME
undo
redo
search
replace
virtualization
large files
async
snapshots
save/recovery
diagnostics
syntax
semantic mapping
```

---

# 115. Property testing

Ví dụ property:

```text
insert(text)
then undo
```

phải trả document về trạng thái tương đương trước insertion.

Tương tự:

```text
edit
undo
redo
```

phải tương đương edit ban đầu.

---

# 116. Unicode tests

Corpus phải bao gồm:

- ASCII
- Vietnamese
- combining marks
- emoji
- CJK
- RTL
- mixed scripts
- tabs
- CRLF
- LF
- malformed UTF-8

---

# 117. Large-file tests

AXTEST phải tạo synthetic documents:

```text
10 MB
100 MB
1 GB+
```

và kiểm tra:

- open
- line lookup
- cursor movement
- insertion
- deletion
- search
- scrolling
- save
- memory growth

---

# 118. Fuzzing

Fuzz command sequences:

```text
insert
delete
undo
redo
move
select
replace
search
IME
scroll
```

Random sequence không được:

- corrupt buffer
- violate UTF-8 invariant
- create invalid range
- crash
- deadlock

---

# 119. Crash recovery tests

```text
edit
 ↓
journal
 ↓
simulated crash
 ↓
recover
```

Recovered document phải khớp revision đã committed theo journal contract.

---

# 120. Concurrency tests

Test:

```text
editor mutation
+
background analysis
+
async search
+
diagnostic update
```

với nhiều ordering.

Stale result phải luôn bị reject/remap đúng.

---

# 121. 40 invariants

### Buffer

`EDITOR-INV-01` — document storage canonical là UTF-8 khi ở normal text mode.

`EDITOR-INV-02` — byte offset không được âm hoặc vượt document length.

`EDITOR-INV-03` — mọi TextRange phải có `start <= end`.

`EDITOR-INV-04` — buffer mutation chỉ xảy ra qua edit transaction.

`EDITOR-INV-05` — failed transaction không được để lại partial mutation.

### Cursor / Selection

`EDITOR-INV-06` — cursor luôn nằm trên boundary hợp lệ.

`EDITOR-INV-07` — selection range luôn hợp lệ.

`EDITOR-INV-08` — multi-selection phải được canonicalize.

`EDITOR-INV-09` — selection identity không phụ thuộc widget identity.

`EDITOR-INV-10` — cursor/selection phải được remap sau edit deterministic.

### Revision

`EDITOR-INV-11` — mỗi committed mutation tạo revision mới.

`EDITOR-INV-12` — revision không được giảm.

`EDITOR-INV-13` — ChangeSet phải xác định from/to revision.

`EDITOR-INV-14` — stale async result không được tự động mutate document.

`EDITOR-INV-15` — snapshot phải immutable.

### Undo

`EDITOR-INV-16` — undo không được copy toàn bộ document mỗi operation.

`EDITOR-INV-17` — undo transaction phải atomic.

`EDITOR-INV-18` — edit mới sau undo phải invalidate redo theo policy.

`EDITOR-INV-19` — undo memory phải bounded theo configuration.

`EDITOR-INV-20` — undo/redo phải giữ cursor/selection semantics nhất quán.

### Unicode / IME

`EDITOR-INV-21` — storage không được giả định byte = character.

`EDITOR-INV-22` — user-facing deletion không được mặc định phá grapheme cluster.

`EDITOR-INV-23` — IME composition chưa commit không được coi là ordinary committed edit.

`EDITOR-INV-24` — composition cancel phải khôi phục state hợp lệ.

`EDITOR-INV-25` — malformed UTF-8 phải được xử lý theo explicit policy.

### Rendering

`EDITOR-INV-26` — editor chỉ yêu cầu layout/render cho vùng cần thiết.

`EDITOR-INV-27` — rendering không được mutate document.

`EDITOR-INV-28` — layout cache phải gắn với revision/configuration.

`EDITOR-INV-29` — large document không được instantiate visual object cho mọi line.

`EDITOR-INV-30` — editor không được gọi GPU trực tiếp.

### Async / Integration

`EDITOR-INV-31` — background task không mutate document trực tiếp.

`EDITOR-INV-32` — async result phải kiểm tra revision/generation.

`EDITOR-INV-33` — formatter/refactor trả edit phải đi qua transaction.

`EDITOR-INV-34` — diagnostics phải có revision/range semantics.

### Safety / ABI

`EDITOR-INV-35` — read-only document phải được enforce ở mutation layer.

`EDITOR-INV-36` — protected range không được bị bypass bởi UI.

`EDITOR-INV-37` — untrusted clipboard content không được tự động execute.

`EDITOR-INV-38` — regex/search phải có resource/cancellation boundary.

`EDITOR-INV-39` — `AXEDITOR_ABI_1` phải deterministic và versioned.

`EDITOR-INV-40` — toàn bộ core editor phải có AXTEST conformance coverage.

---

# 122. Performance architecture tổng thể

```text
                  AXEDITOR
                     │
          ┌──────────┼───────────┐
          ▼          ▼           ▼
      TextBuffer   Cursor     Selection
          │
      ┌───┴────┐
      ▼        ▼
   Revision   Undo
      │
      ▼
 ChangeSet
      │
 ┌────┼──────────────┐
 ▼    ▼              ▼
AXIDE AXCOMPILER   Search
      │
      ▼
 Analysis
      │
      ▼
 Visible Range
      │
      ▼
 Text Layout
      │
      ▼
 AXGUI
```

Điểm quan trọng là **text storage, semantic analysis và rendering không được khóa chặt vào nhau**.

---

# 123. Tích hợp với AXWIDGETS

`TextBox`:

```text
AXWIDGETS.TextBox
        ↓
     AXEDITOR
        ↓
    TextBuffer
```

`SearchBox`:

```text
AXWIDGETS.SearchBox
        ↓
     AXEDITOR
```

`CodeEditor`:

```text
AXWIDGETS.CodeEditor
        ↓
     AXEDITOR
        ↓
 ┌──────┼───────────┐
 ▼      ▼           ▼
AXGUI AXCOMPILER  AXIDE
```

Do đó TextBox không cần tự implement:

- cursor
- selection
- undo
- IME
- Unicode
- search

---

# 124. Tích hợp với AXIDE

```text
AXIDE
 │
 ├── Workspace
 ├── Language Service
 ├── Diagnostics
 ├── Completion
 ├── Refactoring
 │
 ▼
AXEDITOR
 │
 ├── Text
 ├── Cursor
 ├── Selection
 ├── Undo
 ├── Viewport
 └── ChangeSet
```

AXIDE trở thành semantic orchestration layer, còn AXEDITOR là editing engine.

---

# 125. Tích hợp với AXCOMPILER

Compiler nhận:

```text
DocumentSnapshot
ChangeSet
RevisionId
```

Compiler trả:

```text
Diagnostics
SemanticTokens
Completion
Folding
FormattingEdits
```

AXEDITOR chỉ áp dụng các kết quả hợp lệ.

---

# 126. Tích hợp với AXDOC

AXDOC có thể sử dụng:

```text
AXEDITOR
    ↓
source ranges
    ↓
documentation anchors
```

Nhưng AXDOC không được phụ thuộc vào internal buffer implementation.

---

# 127. Native implementation strategy

AXEDITOR nên được implement bằng chính các primitive Axiom:

```text
struct
trait
enum
generic
slice
Result
Option
```

Không cần:

```text
C++ std::string
Qt text engine
Scintilla
Electron
browser DOM
```

Stage0 có thể dùng host implementation trong bootstrap.

Final Axiom toolchain phải self-host AXEDITOR.

---

# 128. Why not just use a simple string?

Một editor không thể dùng:

```text
String {
    entire_file
}
```

rồi mỗi insertion:

```text
allocate new String
copy entire file
```

vì:

```text
1 GB file
1 byte insertion
→ potentially 1 GB copy
```

AXEDITOR bắt buộc có data structures thích hợp cho mutation.

---

# 129. Why not always use Rope?

Rope có overhead:

- node metadata
- pointers
- balancing
- cache locality kém hơn contiguous buffer

Vì vậy Axiom dùng **adaptive text storage**:

```text
small → contiguous
medium → gap/piece
large → chunked/tree
```

Đây phù hợp hơn mục tiêu hiệu năng của Axiom.

---

# 130. Core design decision

Đây là quyết định kiến trúc quan trọng của AXEDITOR 5.0:

> **Không có một text-buffer implementation bắt buộc cho mọi document.**

AXEDITOR định nghĩa abstraction + semantics.

Implementation được chọn theo:

```text
document size
edit locality
read/write ratio
memory pressure
large-file mode
```

Điều này cho phép Axiom đạt được cả:

- tốc độ của contiguous buffer
- khả năng large-file của rope/piece tree
- memory efficiency của chunked storage

mà không biến mọi editor thành cấu trúc nặng.

---

# 131. Definition of Done

`AXEDITOR 5.0` hoàn thành khi:

1. Document model frozen.
2. UTF-8 semantics frozen.
3. Byte/Unicode/grapheme coordinate model frozen.
4. TextBuffer ABI frozen.
5. Small-buffer implementation hoạt động.
6. Gap/chunk/piece implementation hoạt động.
7. Large-file mode hoạt động.
8. Cursor hoạt động.
9. Selection hoạt động.
10. Multi-cursor hoạt động.
11. Column selection hoạt động.
12. Edit transaction hoạt động.
13. Undo/redo hoạt động.
14. Revision/ChangeSet hoạt động.
15. Position/range mapping hoạt động.
16. IME hoạt động.
17. Unicode navigation hoạt động.
18. Search hoạt động.
19. Replace hoạt động.
20. Regex resource limits hoạt động.
21. Clipboard semantics hoạt động.
22. Virtualized text rendering hoạt động.
23. Long-line handling hoạt động.
24. Syntax highlighting integration hoạt động.
25. Semantic highlighting integration hoạt động.
26. Diagnostic integration hoạt động.
27. Folding hoạt động.
28. Async analysis cancellation hoạt động.
29. Immutable snapshots hoạt động.
30. Save/conflict semantics hoạt động.
31. Recovery/journal contract hoạt động.
32. Headless mode hoạt động.
33. AXWIDGETS TextBox integration hoạt động.
34. AXIDE integration hoạt động.
35. AXCOMPILER integration hoạt động.
36. Large-file tests pass.
37. Unicode/IME fuzzing pass.
38. Concurrency/stale-result tests pass.
39. `AXEDITOR_ABI_1` được freeze.
40. Specification ↔ API ↔ implementation ↔ AXTEST traceability hoàn chỉnh.

---

# 132. Trạng thái

```text
BOOTSTRAP-788
AXEDITOR 5.0
     │
     ├── Adaptive TextBuffer
     ├── UTF-8 / Unicode
     ├── Cursor / Selection
     ├── Multi-Cursor
     ├── IME
     ├── Undo / Redo
     ├── Search / Replace
     ├── Incremental Analysis
     ├── Large Files
     ├── Virtualized Rendering
     ├── Snapshots / Revision
     ├── Recovery
     └── AI / IDE integration
             │
             ▼
       AXWIDGETS / AXIDE
```

**AXEDITOR 5.0 — FROZEN.**

---

# BOOTSTRAP-789 — AXCODEEDITOR

**Native Axiom Code Editor Control, Syntax Highlighting, Semantic Highlighting, Code Folding, Minimap, Gutter, Diagnostics, Completion UI, Signature Help, Code Lens, Inline Hints, Breakpoints, Search/Replace UI, Multiple Carets, Selection Rendering, Editor Decorations & IDE-Grade Editing Surface 5.0**

Kiến trúc tiếp theo:

```text
AXWIDGETS
    │
    ▼
AXCODEEDITOR
    │
    ▼
AXEDITOR
    │
 ┌──┼───────────────┐
 ▼  ▼               ▼
AXCOMPILER        AXIDE
 │                  │
 ├ syntax           ├ completion
 ├ semantics        ├ diagnostics
 ├ symbols          ├ refactoring
 └ source map       └ debugger
```

**Phân tách quan trọng:** `AXEDITOR` là engine xử lý text; `AXCODEEDITOR` sẽ là **control chuyên dụng cho lập trình**, chịu trách nhiệm gutter, syntax/semantic presentation, completion UI, folding, decorations và debugger/editor integration nhưng vẫn không biến thành AXIDE.