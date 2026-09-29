# BOOTSTRAP-785 — AXEDITOR

**Native Axiom Code Editor Engine, Text Buffer, Piece/Rope Storage, Cursor & Selection Model, Unicode Text Layout, Syntax/Semantic Rendering, Multi-Cursor Editing, Undo/Redo Transaction Engine, Search/Replace, Folding, Minimap, Viewport Virtualization & High-Performance Editor Runtime 5.0**

**Status:** FROZEN  
**Namespace:** `AXEDITOR`  
**ABI:** `AXEDITOR_ABI_1`  
**Depends on:** `AXIDE`, `AXCOMPILER`, `AXDOC`, `AXWINDOW`, `AXDISPLAY`, `AXCOMPOSITOR`, `AXINPUT`, `AXAPPLICATION`, `AXMEMORY`, `AXRUNTIME`

---

# 1. Mục tiêu

`AXEDITOR` là **text editing engine** của Axiom.

Nếu `AXIDE` trả lời:

> "Code này có nghĩa gì?"

thì `AXEDITOR` trả lời:

> "Người dùng đang nhìn và chỉnh sửa đoạn text nào?"

Hai subsystem phải được tách biệt.

```text
                         AXIDE
                           │
              semantic/document services
                           │
                           ▼
                     AXEDITOR
                           │
       ┌───────────────────┼──────────────────┐
       │                   │                  │
 Text Buffer          View Model        Edit Engine
       │                   │                  │
       ├── UTF-8           ├── viewport       ├── insert
       ├── lines           ├── layout         ├── delete
       ├── cursors         ├── folding        ├── replace
       ├── selections     ├── highlighting   └── undo
       └── search          └── rendering
                           │
                           ▼
                 AXWINDOW / AXDISPLAY
```

---

# 2. Boundary

AXEDITOR sở hữu:

- text storage
- text mutation
- cursor
- selection
- multi-cursor
- line model
- viewport
- undo/redo
- search/replace
- folding state
- editor-local decorations
- syntax/semantic token presentation
- text layout model
- editor rendering model
- input-to-edit translation
- editor transactions

AXEDITOR không sở hữu:

- compiler semantics
- SymbolId
- diagnostics authority
- project graph
- build graph
- test execution
- debugger engine
- package resolution
- documentation semantics
- AI model
- window management
- compositor
- OS input device

---

# 3. Kiến trúc

```text
┌──────────────────────────────────────────────────────────┐
│                      AXEDITOR                            │
│                                                          │
│  ┌──────────────┐       ┌────────────────────────────┐  │
│  │ Text Storage │──────►│ Document Projection        │  │
│  └──────────────┘       └──────────────┬─────────────┘  │
│                                        │                │
│  ┌──────────────┐       ┌──────────────▼─────────────┐  │
│  │ Edit Engine  │──────►│ Editor State               │  │
│  └──────────────┘       │ cursor/selection/folding   │  │
│                         └──────────────┬─────────────┘  │
│                                        │                │
│                         ┌──────────────▼─────────────┐  │
│                         │ Layout / Viewport          │  │
│                         └──────────────┬─────────────┘  │
│                                        │                │
│                         ┌──────────────▼─────────────┐  │
│                         │ Render Model               │  │
│                         └────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
                  AXDISPLAY / AXCOMPOSITOR
```

---

# 4. Text Storage Architecture

AXEDITOR không hard-code một cấu trúc lưu trữ duy nhất.

Interface chuẩn:

```text
TextStore {
    length()
    byte_at()
    slice()
    insert()
    delete()
    replace()
    line_count()
    line_start()
    line_end()
}
```

Backend có thể là:

```text
CONTIGUOUS
PIECE_TABLE
ROPE
B_TREE_TEXT
PAGED_TEXT
MAPPED_TEXT
```

---

# 5. Default Storage

Axiom chọn **Piece Table + balanced index** làm baseline editor storage.

Lý do:

- insert/delete không cần move toàn bộ file
- undo dễ biểu diễn
- file lớn tốt
- original buffer immutable
- appended buffer immutable
- có thể chia sẻ segment
- phù hợp incremental parsing

Mô hình:

```text id="t4m9a2"
Original Buffer
       │
       ├───────────┐
       │           │
       ▼           ▼
Piece Table ───► Add Buffer
       │
       ▼
Logical Document
```

---

# 6. Piece

```text
Piece {
    source
    offset
    length
}
```

`source`:

```text
ORIGINAL
ADD_BUFFER
MAPPED
```

Logical text:

```text
Piece[]
```

Không cần copy text khi split piece.

---

# 7. Piece Index

Không dùng linked list tuyến tính cho file lớn.

Baseline:

```text
PieceTree
```

với:

```text
subtree_byte_count
subtree_line_count
```

Nhờ vậy:

```text
offset → line
line → offset
```

có thể thực hiện logarithmic.

---

# 8. Line Index

Editor cần truy cập dòng cực nhanh.

```text
LineIndex {
    line_count
    checkpoints[]
}
```

Line metadata:

```text
LineInfo {
    start_offset
    byte_length
    newline_kind
}
```

AXEDITOR phải hỗ trợ:

```text
LF
CRLF
CR
```

nhưng Axiom source canonical representation nên ưu tiên `LF`.

---

# 9. Offset Model

Internal canonical position:

```text
ByteOffset = u64
```

Không sử dụng UTF-16 code unit làm canonical offset.

UI adapters có thể convert:

```text
UTF-8 byte offset
       ↕
Unicode scalar index
       ↕
UTF-16 index
       ↕
line/column
```

---

# 10. Position

```text
TextPosition {
    line
    column
}
```

Nhưng `column` phải có encoding metadata khi giao tiếp protocol.

Native AXIDE protocol ưu tiên:

```text
byte_offset
```

Editor UI có thể dùng:

```text
visual_column
```

---

# 11. Unicode

AXEDITOR phải xử lý:

- UTF-8
- Unicode scalar values
- combining marks
- grapheme clusters
- bidirectional text
- tabs
- wide characters

Không được coi:

```text
1 byte == 1 character
```

---

# 12. Grapheme Cluster

Cursor không nên mặc định nhảy giữa các byte của một grapheme.

```text
text:
e + combining accent

logical cursor:
|é|
```

Movement:

```text
cursor_left()
cursor_right()
```

phải sử dụng grapheme boundaries cho UI editing.

Raw byte operations vẫn tồn tại ở low-level API.

---

# 13. Newline Model

Editor giữ newline information.

```text
NewlineKind {
    LF
    CRLF
    CR
}
```

Document policy:

```text
PRESERVE
NORMALIZE_LF
NORMALIZE_CRLF
```

Default Axiom source:

```text
LF
```

Nhưng mở file không được âm thầm thay đổi file nếu chưa save.

---

# 14. Cursor Model

```text
Cursor {
    id
    position
    affinity
    virtual_column?
}
```

`affinity` xử lý vị trí ở boundary:

```text
UPSTREAM
DOWNSTREAM
```

---

# 15. Selection

```text
Selection {
    anchor
    active
}
```

Normalized range:

```text
Range {
    start
    end
}
```

Selection có thể:

```text
EMPTY
LINEAR
RECTANGULAR
```

---

# 16. Multi-Cursor

AXEDITOR native support:

```text
EditorState {
    cursors[]
    primary_cursor
}
```

Ví dụ:

```text
foo
foo
foo
```

có thể có:

```text
|foo
|foo
|foo
```

Một command áp dụng transaction tới tất cả cursor.

---

# 17. Cursor Ordering

Cursors phải được canonicalize:

```text
sort by position
merge overlapping selections
```

Không cho phép hai cursor tạo edit ambiguity.

---

# 18. Edit Transaction

Mọi mutation đi qua:

```text
EditTransaction
```

```text
EditTransaction {
    id
    document_version
    edits[]
    selection_before
    selection_after
    origin
}
```

Origin:

```text
TYPING
PASTE
DELETE
FORMAT
REFACTOR
AI_PATCH
UNDO
REDO
AUTOMATION
```

---

# 19. Atomic Editing

Một transaction:

```text
edit A
edit B
edit C
```

hoặc commit toàn bộ hoặc không commit.

```text
BEGIN
 ↓
validate
 ↓
apply
 ↓
update indices
 ↓
commit
```

Không để document rơi vào state trung gian observable.

---

# 20. Edit Conflict

Mỗi transaction có:

```text
base_version
```

Nếu:

```text
base_version != current_version
```

→ transaction bị reject hoặc rebase.

Không được silent overwrite.

---

# 21. Edit Rebase

Một edit có thể được transform qua edit khác:

```text
E1
 ↓
E2
 ↓
transform(E2, E1)
 ↓
E2'
```

Dùng cho:

- collaborative future support
- background refactoring
- AI patch
- formatter result
- stale IDE operation

---

# 22. AI Patch Integration

AXEDITOR chỉ nhận:

```text
WorkspaceEdit
```

từ AXIDE.

Flow:

```text
AI
 ↓
AXIDE
 ↓
WorkspaceEdit
 ↓
AXEDITOR
 ↓
preview
 ↓
explicit apply
```

AXEDITOR không biết AI là model nào.

---

# 23. Undo/Redo

Undo phải transaction-based.

```text
UndoManager {
    undo_stack[]
    redo_stack[]
}
```

Mỗi transaction lưu semantic inverse:

```text
EditTransaction
      ↓
InverseTransaction
```

---

# 24. Typing Coalescing

Các keystroke liên tiếp có thể merge:

```text
h
e
l
l
o
```

thành:

```text
"hello"
```

trong một undo unit nếu:

- cùng cursor
- thời gian gần nhau
- không có semantic boundary
- không có explicit command giữa chúng

---

# 25. Undo Boundary

Các operation như:

```text
format
rename
refactor
paste
run code action
```

mặc định tạo transaction boundary riêng.

---

# 26. Redo

Sau:

```text
undo()
```

redo stack được giữ.

Một edit mới:

```text
undo
 ↓
new edit
```

xóa redo branch.

---

# 27. Persistent Undo

Optional:

```text
persistent_undo = true
```

Undo history có thể tồn tại qua session.

Nhưng phải bound:

```text
max_bytes
max_transactions
max_age
```

---

# 28. Search Engine

AXEDITOR có search engine local.

```text
search(
    query,
    range,
    options
)
```

Options:

```text
literal
case_sensitive
whole_word
regex
unicode
multiline
```

---

# 29. Search Result

```text
SearchMatch {
    range
    captures[]
}
```

Search phải trả lazy iterator cho file lớn.

---

# 30. Regex

Regex engine phải:

- deterministic
- bounded
- cancellable
- không catastrophic backtracking không kiểm soát

Pattern quá lớn hoặc execution vượt budget:

```text
SEARCH_RESOURCE_LIMIT
```

---

# 31. Replace

```text
replace(
    query,
    replacement
)
```

phải tạo **một transaction** nếu user chọn "Replace All".

Trước khi apply:

```text
find
 ↓
preview matches
 ↓
construct edits
 ↓
validate
 ↓
atomic apply
```

---

# 32. Selection Search

Editor hỗ trợ:

```text
search_selection()
```

và:

```text
select_next_match()
select_all_matches()
```

rất phù hợp multi-cursor.

---

# 33. Folding

Fold model:

```text
FoldRegion {
    id
    start_line
    end_line
    kind
    collapsed
}
```

Kind:

```text
BLOCK
FUNCTION
TYPE
IMPORT
COMMENT
DOC
CUSTOM
```

---

# 34. Semantic Folding

AXIDE có thể cung cấp fold regions từ compiler.

```text
AXCOMPILER
 ↓
Syntax/semantic ranges
 ↓
AXIDE
 ↓
AXEDITOR
```

AXEDITOR chỉ lưu presentation state.

---

# 35. Viewport

Không render toàn file.

```text
Viewport {
    top
    bottom
    horizontal_offset
    vertical_offset
}
```

Chỉ layout/render visible region + margin.

---

# 36. Viewport Virtualization

```text
20,000 lines
       │
       ▼
visible lines = ~80
       │
       ▼
layout ~80 + cache margin
```

Đây là bắt buộc cho file lớn.

---

# 37. Layout Cache

```text
LineLayout {
    line
    width
    height
    glyph_runs[]
    visual_columns[]
}
```

Cache key:

```text
line_hash
font
font_size
tab_width
wrap_width
render_flags
```

---

# 38. Long Lines

Một dòng dài hàng MB không được làm editor treo.

AXEDITOR phải hỗ trợ:

```text
lazy line layout
chunked glyph layout
horizontal virtualization
```

và có giới hạn tài nguyên.

---

# 39. Word Wrap

Modes:

```text
OFF
VIEWPORT
FIXED_COLUMN
```

Wrapping không thay đổi source offsets.

---

# 40. Tabs

```text
TabPolicy {
    width
    insert_spaces
    display_width
}
```

Tab character vẫn là byte `0x09`.

---

# 41. Indentation

AXEDITOR chỉ presentation/editing.

Thông tin language-aware indentation đến từ AXIDE/AXCOMPILER.

Ví dụ:

```text
{
    |
}
```

editor có thể hỏi:

```text
ide_indent_at(position)
```

---

# 42. Syntax Highlighting

Pipeline:

```text
AXEDITOR
   │
   ├── lexical fallback
   │
   └── AXIDE semantic tokens
```

Syntax tokens phải có:

```text
TokenSpan {
    range
    token_kind
    modifiers
}
```

---

# 43. Semantic Highlighting

AXIDE cung cấp:

```text
SymbolId
TokenKind
TokenModifiers
```

AXEDITOR biến chúng thành visual spans.

Ví dụ:

```text
FUNCTION
TYPE
FIELD
VARIABLE
PARAMETER
CONSTANT
MODULE
TRAIT
ENUM
```

---

# 44. Token Delta

Không gửi lại toàn bộ token list nếu chỉ một vùng thay đổi.

```text
SemanticTokenDelta {
    old_version
    edits[]
}
```

Editor render cache cập nhật incremental.

---

# 45. Decorations

```text
Decoration {
    id
    range
    layer
    style
    priority
}
```

Layers:

```text
DIAGNOSTIC
SELECTION
SEARCH
GIT
DEBUG
SEMANTIC
INLINE_HINT
AI_PROPOSAL
USER
```

---

# 46. Decoration Priority

Canonical ordering:

```text
selection
diagnostic
debug
search
semantic
other
```

nhưng theme/UI có thể quyết định final rendering.

Decoration không được thay đổi source.

---

# 47. Diagnostics Rendering

Diagnostic có:

```text
underline
gutter marker
overview marker
hover
```

AXEDITOR chỉ render.

Severity semantics thuộc AXIDE.

---

# 48. Inline Suggestions

AI/editor suggestion có thể hiển thị:

```text
ghost text
```

Nhưng:

```text
visible ≠ committed
```

Chỉ khi explicit accept mới trở thành edit transaction.

---

# 49. Diff View

AXEDITOR hỗ trợ:

```text
single-pane diff
side-by-side diff
inline diff
```

Diff engine có thể nằm trong AXEDITOR.

---

# 50. Diff Model

```text
DiffHunk {
    old_range
    new_range
    changes[]
}
```

Change:

```text
EQUAL
INSERT
DELETE
REPLACE
```

---

# 51. AI Diff

AI patch phải được trình bày:

```text
original
   │
   ▼
proposed
```

và user có thể:

```text
accept all
reject all
accept hunk
reject hunk
```

---

# 52. Editor Commands

Command model:

```text
EditorCommand {
    id
    execute
    can_execute
}
```

Core commands:

```text
cursor_left
cursor_right
cursor_up
cursor_down

word_left
word_right
line_start
line_end

select_left
select_right
select_line

insert_text
delete_backward
delete_forward

copy
cut
paste

undo
redo

indent
outdent

toggle_comment
fold
unfold

find
replace
```

---

# 53. Command Context

```text
CommandContext {
    document
    selections
    mode
    read_only
    editable
    target
}
```

Command không được bypass transaction engine.

---

# 54. Read-Only Documents

Document có:

```text
READ_ONLY
EDITABLE
GENERATED
LOCKED
```

Generated/dependency source mặc định read-only.

---

# 55. Embedded Documents

AXEDITOR có thể host:

```text
markdown
JSON
XML
shader
SQL
resource
generated text
```

Language-specific semantic service vẫn do AXIDE cung cấp.

---

# 56. Large File Mode

Nếu file vượt threshold:

```text
LARGE_FILE_MODE
```

AXEDITOR có thể disable:

- full semantic indexing
- minimap
- expensive regex
- persistent undo
- complex wrapping

nhưng vẫn phải cho phép editing cơ bản.

---

# 57. Minimap

Minimap là presentation projection:

```text
document
 ↓
compressed syntax map
 ↓
viewport overview
```

Không cần layout toàn bộ glyphs.

Có thể dùng:

```text
syntax tokens
line density
diagnostic markers
fold markers
```

---

# 58. Overview Ruler

Một thanh bên cạnh scrollbar:

```text
diagnostics
search matches
breakpoints
changes
```

được tạo từ decoration ranges.

---

# 59. Gutter

Gutter hỗ trợ:

```text
line numbers
relative line numbers
breakpoints
fold markers
diagnostic icons
diff markers
```

---

# 60. Line Number Model

Line number rendering không được lưu duplicate cho mỗi line.

Tính:

```text
first_visible_line + index
```

và format dynamically.

---

# 61. Cursor Rendering

Cursor styles:

```text
LINE
BLOCK
UNDERLINE
```

Blink timer thuộc UI layer.

AXEDITOR chỉ cung cấp cursor geometry/state.

---

# 62. Selection Rendering

Selection ranges phải được map:

```text
logical range
 ↓
visual line segments
```

vì một selection có thể vượt nhiều visual lines do wrapping.

---

# 63. Bidirectional Text

Editor phải phân biệt:

```text
logical order
visual order
```

Cursor movement trong bidi text phải dùng text layout engine.

Không dùng byte offset đơn giản để tính visual X.

---

# 64. IME

AXEDITOR không tự implement keyboard driver.

AXINPUT cung cấp:

```text
composition_start
composition_update
composition_commit
composition_cancel
```

Composition text không commit vào undo history cho tới khi committed.

---

# 65. Clipboard

Clipboard payload:

```text
PlainText
RichText?
StructuredEditorData?
```

AXEDITOR ưu tiên PlainText.

Structured clipboard có thể giữ:

- indentation metadata
- source language
- internal editor markers

nhưng khi paste vào editor khác phải degrade an toàn.

---

# 66. Paste Pipeline

```text
clipboard
 ↓
decode UTF-8
 ↓
normalize newline
 ↓
indent adjustment
 ↓
multi-cursor expansion
 ↓
EditTransaction
 ↓
commit
```

---

# 67. Drag & Drop

Text selection drag:

```text
drag
 ↓
compute source range
 ↓
target position
 ↓
move/copy decision
 ↓
atomic transaction
```

---

# 68. Read/Write File Boundary

AXEDITOR không tự quyết định filesystem policy.

```text
AXIDE
 ↓
document source
 ↓
AXEDITOR buffer
```

Save:

```text
AXEDITOR
 ↓
serialized text
 ↓
AXIDE
 ↓
filesystem
```

---

# 69. Autosave

AXEDITOR không tự ghi source vào original file.

Autosave destination phải là:

```text
recovery journal
temporary checkpoint
```

và chịu session policy của AXIDE.

---

# 70. Collaborative Future Boundary

AXEDITOR hiện tại không yêu cầu collaboration.

Nhưng edit model phải có:

```text
operation identity
base version
transformation capability
```

để sau này có thể thêm:

```text
AXCOLLAB
```

mà không phá editor core.

---

# 71. Text Snapshot

```text
TextSnapshot {
    document_id
    version
    length
    root
}
```

Snapshot immutable.

Có thể dùng cho:

- compiler
- search
- formatter
- AI
- diff
- background tasks

---

# 72. Snapshot Lifetime

Reader giữ:

```text
snapshot_handle
```

Khi hết reference:

```text
snapshot memory
```

có thể reclaim.

Không dùng raw dangling pointers.

---

# 73. Incremental Line Update

Sau edit:

```text
old lines
    ↓
affected line interval
    ↓
recompute newline boundaries
    ↓
reuse unaffected line index
```

Không scan toàn file nếu không cần.

---

# 74. Incremental Layout

Edit line 100:

```text
line 100
```

chỉ invalidates:

```text
line 100
wrapped visual lines
nearby viewport
```

không invalidates toàn file.

---

# 75. Incremental Highlighting

Edit:

```text
"foo("
```

syntax state propagation bắt đầu từ affected token.

Nếu lexer state unchanged sau một đoạn:

```text
stop propagation
```

Đây là cách tránh highlight toàn file.

---

# 76. Editor State

```text
EditorState {
    document_id
    snapshot_version
    cursors[]
    selections[]
    viewport
    folds[]
    decorations[]
    mode
    preferences
}
```

State này không thuộc compiler semantic snapshot.

---

# 77. Multiple Views

Một document có thể mở ở nhiều editor view:

```text
Document
 ├── View A
 ├── View B
 └── View C
```

Text storage dùng chung.

Mỗi view có:

- cursor
- selection
- viewport
- folding
- scroll
- local decorations

---

# 78. Split Editor

```text
Workspace
 ├── ViewGroup A
 │     ├── Editor 1
 │     └── Editor 2
 │
 └── ViewGroup B
       └── Editor 3
```

AXEDITOR không quản lý panel/window layout; chỉ cung cấp editor view.

---

# 79. Read/Write Concurrency

Background readers có thể giữ snapshot.

UI writer tạo transaction.

```text
UI thread
   │
   ▼
transaction
   │
   ▼
new snapshot
   │
   ├── compiler
   ├── search
   └── AI
```

Không lock editor trong toàn bộ compiler operation.

---

# 80. Performance Goals

Baseline mục tiêu:

```text
single keystroke → buffer mutation       < 1 ms target
cursor movement                            < 1 ms
selection                                  < 1 ms
undo/redo                                  < 2 ms
visible layout                             < 10 ms target
search first result                        < 20 ms target
completion rendering                       < 5 ms target
```

Với file lớn, operations có thể chuyển sang incremental/background execution.

---

# 81. Memory Targets

Mục tiêu:

```text
small file:
    overhead minimal

large file:
    no full-file duplication per edit

undo:
    structural sharing

layout:
    viewport bounded

syntax:
    incremental/shared
```

AXEDITOR không được tạo:

```text
original text
+
full edited copy
+
full undo copy
+
full highlight copy
+
full layout copy
```

cho mỗi version.

---

# 82. Resource Budgets

Editor config:

```text
EditorResourceLimits {
    max_document_bytes
    max_piece_count
    max_undo_bytes
    max_search_time
    max_regex_steps
    max_layout_bytes
    max_decoration_count
    max_snapshot_count
}
```

---

# 83. Error Model

```text
EDITOR_INVALID_DOCUMENT
EDITOR_INVALID_RANGE
EDITOR_INVALID_UTF8
EDITOR_VERSION_CONFLICT
EDITOR_READ_ONLY
EDITOR_TRANSACTION_FAILED
EDITOR_SEARCH_LIMIT
EDITOR_REGEX_LIMIT
EDITOR_RESOURCE_LIMIT
EDITOR_SNAPSHOT_EXPIRED
EDITOR_CLIPBOARD_ERROR
EDITOR_LAYOUT_FAILED
```

---

# 84. Native API

Lifecycle:

```text
editor_create()
editor_destroy()

editor_open()
editor_close()
editor_attach_document()
editor_detach_document()
```

Text:

```text
editor_text_length()
editor_text_slice()
editor_text_snapshot()

editor_insert()
editor_delete()
editor_replace()
editor_apply_transaction()
```

Cursor:

```text
editor_cursor_add()
editor_cursor_remove()
editor_cursor_move()
editor_selection_set()
editor_selection_clear()
```

Undo:

```text
editor_undo()
editor_redo()
editor_undo_clear()
```

Search:

```text
editor_search()
editor_search_next()
editor_search_previous()
editor_replace()
editor_replace_all()
```

Viewport:

```text
editor_set_viewport()
editor_get_viewport()
editor_layout_visible()
```

Rendering:

```text
editor_get_layout()
editor_get_tokens()
editor_get_decorations()
editor_get_gutter()
```

Folding:

```text
editor_fold()
editor_unfold()
editor_toggle_fold()
editor_folding_ranges()
```

---

# 85. Transaction API

```text
editor_transaction_begin()
editor_transaction_add_edit()
editor_transaction_set_selection()
editor_transaction_commit()
editor_transaction_abort()
```

Commit trả:

```text
EditResult {
    old_version
    new_version
    applied_edits[]
    inverse
}
```

---

# 86. Snapshot API

```text
editor_snapshot_create()
editor_snapshot_retain()
editor_snapshot_release()

editor_snapshot_slice()
editor_snapshot_hash()
editor_snapshot_line_count()
```

---

# 87. Search API

```text
editor_search_begin()
editor_search_next()
editor_search_cancel()
editor_search_end()
```

Search handle cancellable.

---

# 88. Rendering API

Editor không vẽ trực tiếp vào framebuffer.

Nó tạo:

```text
EditorRenderModel
```

```text
EditorRenderModel {
    viewport
    lines[]
    glyph_runs[]
    selections[]
    cursors[]
    decorations[]
    gutter[]
}
```

Sau đó UI renderer sử dụng AXDISPLAY/AXCOMPOSITOR.

---

# 89. Renderer Separation

```text
AXEDITOR
    │
    ▼
RenderModel
    │
    ▼
AXDISPLAY renderer
    │
    ▼
AXCOMPOSITOR
```

Điều này cho phép:

- GPU renderer
- software renderer
- remote renderer
- accessibility renderer
- test renderer

---

# 90. Theme Model

AXEDITOR không hard-code colors.

```text
EditorTheme {
    token_styles
    selection_style
    diagnostic_styles
    gutter_style
    cursor_style
}
```

Theme thuộc UI configuration.

---

# 91. Accessibility Projection

AXEDITOR cung cấp semantic text ranges:

```text
AccessibilityTextModel {
    text
    ranges[]
    cursor
    selections[]
}
```

AXWINDOW/AXINPUT quyết định screen-reader backend.

---

# 92. Testing

AXTEST phải kiểm tra:

### Storage

```text
insert/delete/replace
piece splitting
large file
unicode
newline
```

### Cursor

```text
grapheme
bidi
multicursor
selection
```

### Transactions

```text
atomicity
version conflict
rollback
rebase
```

### Undo

```text
coalescing
undo
redo
branching
persistent recovery
```

### Rendering

```text
viewport
wrapping
folding
semantic tokens
decorations
```

---

# 93. Differential Testing

So sánh PieceTree với reference model:

```text
naive_string
      VS
AXEDITOR
```

Sau random edit sequence:

```text
text_equal
line_index_equal
range_mapping_equal
```

phải đúng.

---

# 94. Fuzzing

Fuzz:

```text
random UTF-8
random edits
random cursor movement
random selections
random undo/redo
random folding
random search
random regex
random transaction ordering
```

Một chuỗi hàng triệu operations không được corrupt text state.

---

# 95. Deterministic Replay

Mỗi editor operation có:

```text
operation_id
document_version
input
result
```

Một crash có thể replay:

```text
operation log
 ↓
AXEDITOR
 ↓
same final state
```

---

# 96. Security

AXEDITOR phải coi:

- file content
- clipboard
- drag/drop
- generated source
- AI patch
- remote document

là untrusted input.

Không được execute source code.

Không được parse regex vô hạn.

Không được allocate vô hạn từ file độc hại.

---

# 97. Clipboard Security

Clipboard không được phép inject:

```text
commands
shell instructions
editor commands
```

Clipboard chỉ là data.

---

# 98. File Security

AXEDITOR không tự follow arbitrary symlink để save.

Save authority thuộc AXIDE/filesystem policy.

Editor chỉ cung cấp:

```text
serialized document
```

---

# 99. AI Security

AI proposal:

```text
proposal
 ↓
diff
 ↓
user approval
 ↓
transaction
```

AXEDITOR không có API kiểu:

```text
ai_write_file(path)
```

---

# 100. Plugin Boundary

Editor extension có thể đăng ký:

```text
syntax provider
decoration provider
command
formatter adapter
language service
```

nhưng phải chạy qua capability system.

Không được truy cập nội bộ:

```text
raw allocator
arbitrary process
secret state
```

---

# 101. ABI

```text
AXEDITOR_ABI_1
```

Ổn định:

- opaque handles
- text offsets
- range structures
- transaction structures
- error codes
- ownership
- callbacks
- threading rules

Không expose PieceTree internals.

---

# 102. Threading Contract

Default:

```text
Editor mutation:
    serialized

Snapshot read:
    concurrent

Layout:
    parallelizable

Search:
    parallelizable

Rendering:
    parallelizable
```

UI mutation không được race.

---

# 103. Callback Rules

Callbacks không được gọi trong internal lock.

Pattern:

```text
mutate
 ↓
release internal lock/state guard
 ↓
notify callback
```

tránh deadlock/reentrancy.

---

# 104. Editor Events

```text
DocumentChanged
SelectionChanged
ViewportChanged
FoldChanged
DecorationChanged
DiagnosticVisualChanged
SearchChanged
UndoStateChanged
```

Event chứa version.

---

# 105. Event Ordering

Trong cùng document:

```text
DocumentChanged(v10)
DocumentChanged(v11)
DocumentChanged(v12)
```

Không được phát:

```text
v12
v10
v11
```

cho cùng logical stream.

---

# 106. Reentrancy

Callback không được làm editor state inconsistent.

Một callback có thể request edit mới nhưng edit đó phải vào transaction queue/next mutation boundary.

---

# 107. Headless Editor

AXEDITOR phải chạy không GUI:

```text
axiom editor --format
axiom editor --search
axiom editor --replace
axiom editor --diff
```

RenderModel có thể được test bằng golden snapshots.

---

# 108. Integration với AXIDE

```text
AXIDE
  │
  ├── semantic snapshot
  │
  ▼
AXEDITOR
  │
  ├── text snapshot
  ├── visual state
  └── edit transactions
  │
  ▼
AXIDE
  │
  └── document change
```

Không có circular semantic ownership.

---

# 109. Integration với AXCOMPILER

Compiler nhận:

```text
TextSnapshot
```

Compiler không đọc trực tiếp editor PieceTree.

```text
AXEDITOR
 ↓
immutable TextSnapshot
 ↓
AXCOMPILER
```

---

# 110. Integration với AI

```text
AXIDE
 ↓
AIContextPack
 ↓
AI
 ↓
WorkspaceEdit
 ↓
AXIDE
 ↓
AXEDITOR
 ↓
transaction
```

---

# 111. Integration với Debugger

Breakpoint visual:

```text
Debugger
 ↓
AXIDE
 ↓
Decoration
 ↓
AXEDITOR
```

Editor không sở hữu breakpoint semantics.

---

# 112. Integration với AXDOC

Documentation hover:

```text
AXDOC
 ↓
AXIDE
 ↓
editor hover UI
```

AXEDITOR chỉ hiển thị.

---

# 113. Multi-Document Atomicity

Rename/refactor có thể sửa nhiều documents.

AXEDITOR từng document commit atomic.

AXIDE chịu trách nhiệm transaction cấp workspace:

```text
WorkspaceEdit
    ↓
validate all
    ↓
prepare all
    ↓
commit all
```

AXEDITOR không tự làm workspace transaction.

---

# 114. Save Serialization

Serialize:

```text
TextSnapshot
 ↓
newline policy
 ↓
UTF-8 bytes
 ↓
AXIDE filesystem service
```

Không serialize qua repeated string concatenation.

---

# 115. Hashing

Document hash:

```text
DocumentHash = hash(canonical byte content)
```

Dùng cho:

- cache
- build
- semantic snapshot
- recovery
- conflict detection

---

# 116. Editor Fingerprint

```text
EditorFingerprint {
    text_hash
    newline_policy
    encoding
    editor_version
}
```

Không được dùng editor fingerprint thay compiler semantic fingerprint.

---

# 117. Large Workspace

AXEDITOR phải đảm bảo một document mở không bắt AXIDE:

```text
load every workspace file
```

Editor chỉ materialize active documents.

---

# 118. Editor Startup

```text
AXIDE session
 ↓
open document
 ↓
load text
 ↓
create TextStore
 ↓
create editor state
 ↓
restore cursor
 ↓
restore viewport
 ↓
render visible region
```

Không cần layout toàn file trước khi first paint.

---

# 119. Fast First Paint

Mục tiêu:

```text
open file
 ↓
first visible text
```

phải xảy ra trước:

- full semantic analysis
- full indexing
- full AXDOC
- workspace background indexing

---

# 120. Responsiveness Rule

Không operation nào sau đây được block UI indefinitely:

```text
parse
compile
search workspace
index
build
test
AI context generation
regex
debugger attach
```

Tất cả phải cancellable/asynchronous nếu có thể lâu.

---

# 121. Editor Command Latency

Interactive command phải ưu tiên:

```text
P0
```

Background:

```text
P3-P5
```

Scheduler dùng cùng triết lý với AXIDE.

---

# 122. 40 Invariants

### EDITOR-INV-01
AXEDITOR không sở hữu compiler semantics.

### EDITOR-INV-02
Text buffer là authoritative source của editor document.

### EDITOR-INV-03
Document version tăng đơn điệu.

### EDITOR-INV-04
Transaction có base version.

### EDITOR-INV-05
Stale transaction không được silent overwrite.

### EDITOR-INV-06
Committed transaction atomic.

### EDITOR-INV-07
Snapshot immutable.

### EDITOR-INV-08
Snapshot có stable version.

### EDITOR-INV-09
Canonical offset là UTF-8 byte offset.

### EDITOR-INV-10
UI cursor phải tôn trọng grapheme boundaries.

### EDITOR-INV-11
Logical offset không phụ thuộc visual layout.

### EDITOR-INV-12
Piece storage không được yêu cầu full-file copy cho mỗi edit.

### EDITOR-INV-13
Line index phải được cập nhật incremental.

### EDITOR-INV-14
Undo phải transaction-based.

### EDITOR-INV-15
Undo/redo không được phá document consistency.

### EDITOR-INV-16
Redo branch bị invalid khi có edit mới sau undo.

### EDITOR-INV-17
Multi-cursor edits phải atomic.

### EDITOR-INV-18
Overlapping cursor edits phải canonicalize.

### EDITOR-INV-19
Search phải cancellable.

### EDITOR-INV-20
Regex phải resource-bounded.

### EDITOR-INV-21
Replace All phải atomic.

### EDITOR-INV-22
Folding không thay đổi source.

### EDITOR-INV-23
Decorations không thay đổi source.

### EDITOR-INV-24
Semantic highlighting không phải semantic authority.

### EDITOR-INV-25
RenderModel không được mutate document.

### EDITOR-INV-26
Viewport rendering phải virtualized.

### EDITOR-INV-27
Long-line layout phải bounded.

### EDITOR-INV-28
AI proposal không phải committed source.

### EDITOR-INV-29
AI edit phải đi qua explicit transaction.

### EDITOR-INV-30
Read-only document không được mutate.

### EDITOR-INV-31
External filesystem state không được silent overwrite buffer.

### EDITOR-INV-32
Snapshot readers có thể chạy concurrent với writer.

### EDITOR-INV-33
Callbacks không được chạy dưới internal mutation lock.

### EDITOR-INV-34
Event version ordering phải deterministic.

### EDITOR-INV-35
Editor không execute clipboard content.

### EDITOR-INV-36
Editor không execute source content.

### EDITOR-INV-37
Headless mode phải dùng cùng editing core.

### EDITOR-INV-38
Rendering backend không được trở thành text-storage authority.

### EDITOR-INV-39
`AXEDITOR_ABI_1` phải versioned và stable.

### EDITOR-INV-40
AXEDITOR phải có khả năng self-host bằng Axiom.

---

# 123. Definition of Done

`BOOTSTRAP-785` hoàn thành khi có:

- [x] TextStore abstraction
- [x] PieceTree baseline
- [x] UTF-8
- [x] Unicode scalar handling
- [x] grapheme-aware cursor
- [x] newline model
- [x] line index
- [x] cursor
- [x] selection
- [x] multi-cursor
- [x] atomic edit transactions
- [x] version conflict detection
- [x] edit rebase foundation
- [x] undo/redo
- [x] typing coalescing
- [x] persistent undo boundary
- [x] search
- [x] bounded regex
- [x] replace
- [x] diff
- [x] folding
- [x] syntax highlighting
- [x] semantic highlighting
- [x] decorations
- [x] viewport virtualization
- [x] wrapping
- [x] long-line protection
- [x] minimap model
- [x] overview ruler
- [x] gutter
- [x] IME boundary
- [x] clipboard boundary
- [x] accessibility projection
- [x] RenderModel
- [x] headless operation
- [x] AXIDE integration
- [x] AXCOMPILER snapshot integration
- [x] AXDOC/AXTEST/AXBUILD integration boundary
- [x] AI patch boundary
- [x] deterministic replay
- [x] fuzzing
- [x] differential testing
- [x] resource limits
- [x] threading contract
- [x] callback/reentrancy rules
- [x] crash/recovery compatibility
- [x] `AXEDITOR_ABI_1`
- [x] 40 invariants
- [x] AXTEST conformance suite
- [x] native self-hosting path

**AXEDITOR 5.0 được đóng băng.**

---

# BOOTSTRAP-786 — AXGUI

**Native Axiom GUI Framework, Retained/Immediate Hybrid UI Model, Widget Tree, Layout Engine, Input Routing, Focus Management, Accessibility Tree, Styling, Themes, Text/UI Integration, GPU Rendering, Window Integration, Native Controls, Event Loop & High-Performance Desktop UI Runtime 5.0**

Kiến trúc tiếp theo sẽ xây lớp GUI tổng quát mà `AXIDE` và `AXEDITOR` sử dụng:

```text
                 AXAPPLICATION
                       │
                    AXGUI
             ┌─────────┼─────────┐
             ▼         ▼         ▼
         Widget     Layout     Input
           Tree       Engine    Router
             │         │         │
             └─────────┼─────────┘
                       ▼
                  Render Tree
                       │
                       ▼
                 AXCOMPOSITOR
                       │
                       ▼
                   AXDISPLAY
```

`AXWINDOW` đã cung cấp window primitive; `AXGUI` sẽ cung cấp **UI framework thực sự** trên primitive đó.