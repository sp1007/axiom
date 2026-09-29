# BOOTSTRAP-789 — AXCODEEDITOR

**Native Axiom Code Editor Control, Syntax Highlighting, Semantic Highlighting, Code Folding, Minimap, Gutter, Diagnostics, Completion UI, Signature Help, Code Lens, Inline Hints, Breakpoints, Search/Replace UI, Multiple Carets, Selection Rendering, Editor Decorations & IDE-Grade Editing Surface 5.0**

**Status:** FROZEN  
**Namespace:** `AXCODEEDITOR`  
**ABI:** `AXCODEEDITOR_ABI_1`  
**Depends on:** `AXEDITOR`, `AXWIDGETS`, `AXGUI`, `AXIDE`, `AXCOMPILER`, `AXDOC`, `AXTEST`, `AXDEBUGGER` *(integration boundary)*

---

# 1. Mục tiêu

`AXCODEEDITOR` là **presentation/control layer dành riêng cho source code**, nằm giữa editor engine và IDE.

```text id="a9x0q1"
AXIDE
 │
 ├── Compiler / Language Service
 ├── Diagnostics
 ├── Completion
 ├── Refactoring
 ├── Debugger
 │
 ▼
AXCODEEDITOR
 │
 ├── Gutter
 ├── Syntax highlighting
 ├── Semantic highlighting
 ├── Folding
 ├── Completion UI
 ├── Diagnostics UI
 ├── Inline hints
 ├── Code lens
 ├── Breakpoints
 └── Minimap
 │
 ▼
AXEDITOR
 │
 ▼
TextBuffer
```

AXCODEEDITOR **không trở thành IDE**.

---

# 2. Boundary

## AXCODEEDITOR sở hữu

- code-editor control
- source-code presentation
- gutter
- line numbers
- folding presentation
- syntax/semantic highlighting presentation
- diagnostic decorations
- completion popup
- signature-help popup
- parameter hints
- code lens presentation
- breakpoint markers
- current-line highlighting
- whitespace visualization
- indentation guides
- minimap
- editor-specific overlays
- code navigation visual affordances
- editor command integration
- debugger visual integration

## Không sở hữu

| Chức năng | Owner |
|---|---|
| Text storage | AXEDITOR |
| Cursor/editing | AXEDITOR |
| IME | AXEDITOR |
| Undo/redo | AXEDITOR |
| Compiler semantics | AXCOMPILER |
| Workspace | AXIDE |
| Debug engine | AXDEBUGGER |
| Window | AXWINDOW |
| GPU | AXGRAPHICS |
| Widget framework | AXGUI |
| Standard controls | AXWIDGETS |
| Documentation | AXDOC |

---

# 3. Nguyên tắc kiến trúc

```text id="7a0xqf"
AXEDITOR = editing truth
AXCOMPILER = language truth
AXIDE = development orchestration
AXCODEEDITOR = code presentation
```

Không được duplicate semantic authority.

Ví dụ:

```text
AXCOMPILER
    ↓
"token này là function"

AXCODEEDITOR
    ↓
render function-token style
```

AXCODEEDITOR không tự quyết định symbol semantics nếu compiler đã cung cấp semantic information.

---

# 4. CodeEditor structure

```text id="x8v1h7"
CodeEditor
 ├── EditorCore
 │     └── AXEDITOR
 │
 ├── Gutter
 │     ├── line numbers
 │     ├── diagnostics
 │     ├── breakpoints
 │     └── folding
 │
 ├── TextPresentation
 │     ├── syntax
 │     ├── semantic
 │     ├── selections
 │     └── current line
 │
 ├── OverlayLayer
 │     ├── completion
 │     ├── signature help
 │     ├── code lens
 │     └── inline hints
 │
 └── Minimap
```

---

# 5. Base model

```text id="v5c0nq"
CodeEditor {
    editor: EditorHandle
    language: LanguageId
    presentation: CodePresentation
    gutter: GutterState
    overlays: OverlayState
    minimap: MinimapState
    debug: DebugPresentation
}
```

---

# 6. Code presentation

```text id="k2r3w9"
CodePresentation {
    syntax_spans[]
    semantic_spans[]
    decorations[]
    folds[]
    whitespace
    indentation
    current_line
    selections
}
```

Tất cả presentation state phải gắn với:

```text id="7e3q1b"
DocumentId
RevisionId
```

để tránh stale rendering.

---

# 7. Language identity

```text id="m0p4yk"
LanguageId
```

Ví dụ:

```text
axiom
c
cpp
rust
python
javascript
```

AXCODEEDITOR không hard-code chỉ Axiom.

Axiom language service cung cấp semantic behavior.

---

# 8. Syntax highlighting

Syntax spans:

```text id="6h8n3p"
SyntaxSpan {
    range
    token_kind
    style_id
}
```

Token kinds có thể gồm:

```text
Keyword
Identifier
Type
Function
Variable
Literal
Number
String
Comment
Operator
Punctuation
Attribute
Directive
Error
```

Language service quyết định token classification.

---

# 9. Semantic highlighting

```text id="m8w4z1"
SemanticSpan {
    range
    symbol_id?
    semantic_kind
    modifiers
}
```

Ví dụ:

```text
Function
Type
Field
Parameter
Local
Constant
Module
Trait
EnumVariant
Macro
```

Semantic highlighting có thể override syntax style.

---

# 10. Highlight precedence

Canonical precedence:

```text id="f6c1j8"
base text
   ↓
syntax
   ↓
semantic
   ↓
diagnostic
   ↓
selection
   ↓
cursor/current-line
```

Nhưng mỗi layer chỉ được override properties được phép.

Ví dụ diagnostic underline không được xóa semantic foreground color nếu theme policy không yêu cầu.

---

# 11. Style IDs

Không lưu toàn bộ style trên mỗi token.

```text id="b3p8y0"
StyleId = u32
```

Style table:

```text id="e5j2q7"
CodeTheme
 ├ keyword
 ├ type
 ├ function
 ├ string
 ├ comment
 ├ number
 ├ operator
 └ ...
```

Giảm memory.

---

# 12. Incremental syntax

Sau edit:

```text id="h9x3a4"
ChangeSet
    ↓
affected syntax region
    ↓
incremental analysis
    ↓
replace spans
```

Không re-highlight toàn file nếu language engine hỗ trợ incremental parsing.

---

# 13. Semantic update

```text id="v7k4m2"
AXCOMPILER
     ↓
semantic snapshot
     ↓
AXCODEEDITOR
     ↓
presentation update
```

Semantic snapshot phải immutable.

---

# 14. Gutter

Gutter là vùng bên trái editor:

```text id="j2n8p5"
┌───────┬──────────────────────────────┐
│  12   │ fn main() {                  │
│  13   │     let x = 10;              │
│  14 ● │     println(x);              │
│  15   │ }                            │
└───────┴──────────────────────────────┘
```

Gutter không phải separate window.

Nó là một presentation region của CodeEditor.

---

# 15. Line numbers

```text id="a6w1z8"
LineNumberMode =
    None
    Absolute
    Relative
    Hybrid
```

Default:

```text
Absolute
```

Relative mode có thể dùng cho keyboard navigation.

---

# 16. Gutter width

Gutter width được tính từ:

```text id="z9p3s7"
visible_line_number_digits
+
marker_columns
+
padding
```

Không resize mỗi frame nếu line-count digit count không thay đổi.

---

# 17. Diagnostics

```text id="p1q6x4"
CodeDiagnostic {
    id
    revision
    range
    severity
    message
    code
    source
}
```

Severity:

```text
Error
Warning
Info
Hint
```

Presentation:

```text id="r3k8v2"
underline
gutter marker
hover message
overview marker
```

---

# 18. Diagnostic anchoring

Diagnostics phải được liên kết với:

```text id="n5c1j0"
RevisionId
TextRange
```

Nếu document thay đổi:

```text id="b7q9m3"
AXEDITOR.map_range()
```

có thể remap.

Nếu không thể chứng minh compatibility:

```text id="s2f6k8"
discard
```

Không hiển thị diagnostic sai vị trí.

---

# 19. Diagnostic hover

Khi cursor/hover trên diagnostic:

```text id="q6y8m2"
CodeDiagnostic
     ↓
AXWIDGETS Tooltip/Popup
```

AXCODEEDITOR cung cấp data; AXWIDGETS render popup.

---

# 20. Error squiggles

Diagnostic decoration:

```text id="u1p7d4"
DiagnosticDecoration {
    range
    severity
    underline_style
}
```

Các style:

```text
Wave
Straight
Dotted
None
```

Theme quyết định appearance.

---

# 21. Folding

```text id="v2n9c5"
FoldRegion {
    id
    range
    placeholder
    kind
    collapsed
}
```

Kinds:

```text
Block
Function
Type
Import
Comment
Region
Custom
```

---

# 22. Fold model

Folding state phải tách khỏi compiler result.

```text id="j8q1w6"
FoldStructure
    ↓
FoldState
```

Compiler có thể thay đổi structure mà không mất hoàn toàn user folding state.

---

# 23. Fold placeholder

Ví dụ:

```text id="d3m7k1"
fn very_long_function(...) {
    ⋯
}
```

Placeholder không phải text trong document.

---

# 24. Fold correctness

Fold không được:

- xóa text
- thay đổi document revision
- thay đổi semantic ranges
- ảnh hưởng save
- ảnh hưởng compiler

Nó chỉ thay đổi presentation.

---

# 25. Indentation guides

```text id="n7c4x2"
IndentGuide {
    visual_column
    depth
}
```

Có thể render:

```text
│
│   │
│   │   │
```

Không phải text.

---

# 26. Whitespace visualization

Modes:

```text id="e4z9q2"
None
Indentation
All
TrailingOnly
```

Whitespace glyphs chỉ là presentation.

---

# 27. Current line

```text id="h8v3p0"
CurrentLineHighlight {
    line
    enabled
}
```

Không thay đổi selection hoặc document.

---

# 28. Cursor presentation

AXEDITOR sở hữu cursor semantics.

AXCODEEDITOR sở hữu:

- cursor visual
- blink
- multi-cursor painting
- overwrite-mode indicator

Blink scheduler dùng AXGUI, không tạo timer riêng.

---

# 29. Multiple carets

Ví dụ:

```text id="x4q8s1"
foo
foo
foo
 ^
 ^
 ^
```

AXEDITOR lưu selections.

AXCODEEDITOR render chúng.

Không tạo cursor model thứ hai.

---

# 30. Selection rendering

Selection layers:

```text id="k1n6d8"
primary selection
secondary selections
matching selections
search selections
```

Priority phải deterministic.

---

# 31. Matching selection

Khi chọn:

```text id="v3m7a9"
foo
```

các occurrence có thể highlight.

Đây là presentation/search integration, không mutate selection model.

---

# 32. Completion

Completion request:

```text id="g8q4r2"
CompletionRequest {
    document
    revision
    position
    trigger
    context
}
```

Result:

```text id="z2n7k5"
CompletionList {
    items[]
    incomplete
}
```

---

# 33. Completion item

```text id="c5w1p8"
CompletionItem {
    label
    detail
    documentation
    kind
    sort_key
    filter_text
    insert_text
    edit
    symbol_id?
}
```

---

# 34. Completion popup

UI:

```text id="s9j3x6"
CodeEditor
    │
    └── CompletionPopup
          ├ filter
          ├ item list
          └ documentation
```

Popup là AXWIDGETS composition.

AXCODEEDITOR điều phối.

---

# 35. Completion acceptance

Accept:

```text id="y7k2m4"
CompletionItem
     ↓
TextEdit
     ↓
AXEDITOR transaction
```

Không sửa text trực tiếp.

---

# 36. Completion cancellation

Khi:

```text id="q8f1v3"
document changes
cursor moves
popup closes
new request starts
```

request cũ phải bị cancel hoặc stale-result reject.

---

# 37. Completion ranking

AXCODEEDITOR có thể hiển thị thứ tự compiler/language service cung cấp.

Không tự áp đặt semantic ranking nếu language service đã cung cấp ranking.

Presentation có thể filter theo query.

---

# 38. Signature Help

```text id="m3q7x1"
SignatureHelp {
    signatures[]
    active_signature
    active_parameter
}
```

UI:

```text id="c6v9p2"
foo(arg1: Type, arg2: Type)
        ^^^^^
```

---

# 39. Parameter hints

Inline parameter hint:

```text id="w4k8s0"
foo(
    value: x,
    count: 10
)
```

Đây là presentation-only overlay.

Không thêm text vào document.

---

# 40. Code Lens

```text id="e9q2m6"
CodeLens {
    range
    title
    command?
}
```

Ví dụ:

```text
3 references
fn foo() { ... }
```

CodeLens command phải đi qua `Command`.

---

# 41. Inline hints

```text id="p5r1x8"
InlineHint {
    position
    text
    kind
}
```

Kinds:

```text
TypeHint
ParameterHint
ValueHint
AIHint
Custom
```

AI hints phải có provenance.

---

# 42. Hover information

```text id="u8m4q1"
HoverInfo {
    range
    content
    actions[]
}
```

Content có thể đến từ:

- AXCOMPILER
- AXDOC
- AXIDE
- debugger

AXCODEEDITOR chỉ presentation.

---

# 43. Go-to-definition

CodeEditor không tự tìm definition.

```text id="j1s7c5"
user activation
      ↓
AXIDE
      ↓
SymbolId / SourceLocation
      ↓
AXEDITOR navigation
```

---

# 44. Source navigation

Source location:

```text id="x6p2n9"
SourceLocation {
    document
    range
}
```

AXCODEEDITOR gọi:

```text id="h7q3v1"
editor_scroll_to()
editor_set_selection()
```

---

# 45. Breakpoints

```text id="b8m2k6"
BreakpointMarker {
    id
    document
    line
    column?
    verified
    enabled
}
```

AXDEBUGGER sở hữu breakpoint semantics.

AXCODEEDITOR chỉ hiển thị và phát event.

---

# 46. Execution line

Debugger có thể cung cấp:

```text id="f4q9w3"
ExecutionLocation {
    document
    position
}
```

CodeEditor render:

```text
current execution line
```

Không tự chạy debugger.

---

# 47. Debug decorations

```text id="n2v7c4"
DebugDecoration {
    kind
    range
    state
}
```

Có thể biểu diễn:

- current instruction
- breakpoint
- breakpoint disabled
- breakpoint condition
- stopped state

---

# 48. Minimap

Minimap là overview representation:

```text id="p7x1m9"
┌──────┐
│░░░░░ │
│░▒░░░ │
│░░██░ │ ← viewport
│░░░░░ │
└──────┘
```

Không render toàn bộ text với full-size glyph layout.

---

# 49. Minimap rendering

Minimap sử dụng compact representation:

```text id="k3q8v5"
line
 ↓
token/style summary
 ↓
small geometry
```

Mục tiêu:

```text id="d1m6x9"
O(number_of_lines)
```

với bounded memory/cache.

Không giữ full-resolution layout cho toàn file.

---

# 50. Minimap viewport

Viewport indicator:

```text id="r8v2c6"
Minimap
   │
   └── ViewportRect
```

Click/drag viewport:

```text id="t5n9q1"
minimap position
 ↓
document line
 ↓
editor_scroll_to()
```

---

# 51. Overview ruler

Ngoài minimap có thể có:

```text id="y4m7p2"
OverviewRuler
```

hiển thị:

- errors
- warnings
- search matches
- breakpoints
- TODO markers

---

# 52. TODO markers

TODO/FIXME presentation nên đến từ:

```text id="q1x6n8"
Language/IDE analysis
```

không tự scan toàn bộ file mỗi frame.

---

# 53. Search UI

CodeEditor tích hợp AXWIDGETS:

```text id="m8q3v1"
FindBar
 ├ SearchBox
 ├ previous
 ├ next
 ├ replace
 └ options
```

Search engine thực tế:

```text id="j7k2p5"
AXEDITOR
```

---

# 54. Search highlights

Search result:

```text id="e3n8w4"
SearchMatch {
    range
    active
}
```

Presentation không sửa SelectionModel.

---

# 55. Code navigation bar

Có thể có:

```text id="c5m9q2"
breadcrumb
```

Ví dụ:

```text
module > type > function
```

Nguồn symbol hierarchy:

```text id="z1v7k3"
AXCOMPILER / AXIDE
```

---

# 56. Breadcrumb interaction

Click:

```text id="n4p8x6"
symbol
 ↓
navigation command
 ↓
AXEDITOR
```

Không mutate document.

---

# 57. Sticky headers

Khi scroll:

```text id="u6q2m8"
struct Foo {
    ...
```

header semantic có thể được giữ ở top.

Nguồn:

```text id="w3k9p1"
syntax/semantic structure
```

Sticky header là presentation layer.

---

# 58. Code editor layout

```text id="a8r3m7"
┌───────────────────────────────────────────────┐
│ Breadcrumb / toolbar                          │
├──────┬────────────────────────────────────────┤
│gutter│ text viewport                          │
│      │                                        │
│ 120  │ fn main() {                            │
│ 121  │     let x = foo();                     │
│ 122● │     println(x);                        │
│ 123  │ }                                      │
├──────┴────────────────────────────────────────┤
│ status / diagnostics                          │
└───────────────────────────────────────────────┘
```

AXCODEEDITOR không sở hữu toàn bộ IDE chrome.

---

# 59. Split editor

Split view thuộc AXWIDGETS/AXGUI.

Mỗi pane có:

```text id="g5v8n2"
CodeEditor
```

có thể cùng trỏ tới một Document:

```text id="m2q6x9"
Document
 ├ EditorView A
 └ EditorView B
```

---

# 60. Multiple views

Một document có thể có nhiều editor view.

```text id="p9c4k7"
Document #42
    ├ View #1
    ├ View #2
    └ View #3
```

Text state dùng chung.

Viewport/cursor/folding có thể riêng theo view.

---

# 61. Shared vs view-local state

### Document-wide

```text
text
revision
encoding
language
```

### View-local

```text
cursor
selection
scroll
fold state
zoom
minimap state
```

### Workspace/editor policy

```text
theme
keymap
formatting policy
```

---

# 62. Zoom

```text id="s6m1x8"
CodeEditorZoom {
    scale
}
```

Zoom chỉ thay đổi presentation.

Không thay đổi document.

---

# 63. Font

Code editor ưu tiên:

```text id="e8q3n5"
monospace font
```

nhưng architecture không bắt buộc một font cụ thể.

Font selection thuộc AXGUI/text system.

---

# 64. Tab visualization

Whitespace/tab rendering phải dùng text layout metrics.

Không giả định:

```text
tab = 4 ASCII spaces
```

về mặt visual.

---

# 65. Soft wrap

```text id="x2v7m4"
WrapMode =
    Off
    Viewport
    Column
```

Soft wrap không thay đổi document lines.

---

# 66. Wrapped line mapping

AXCODEEDITOR phải phân biệt:

```text id="f9p3k6"
logical line
visual line
```

Gutter line number chỉ hiển thị logical line.

---

# 67. Horizontal scrolling

Khi wrap off:

```text id="r5m8q2"
horizontal viewport
```

phải được virtualized.

Long line không được tạo toàn bộ glyph layout nếu chỉ một đoạn đang visible.

---

# 68. Code folding + virtualization

Folding làm thay đổi visible line mapping:

```text id="n7q1c5"
Document lines
     ↓
Fold state
     ↓
Visible logical lines
     ↓
Visual lines
```

Không thay đổi underlying text.

---

# 69. Decorations

General decoration:

```text id="k8p2m6"
Decoration {
    id
    range
    layer
    style
    priority
    tooltip?
    command?
}
```

Layers:

```text
Background
Text
Underline
Gutter
Inline
Overlay
```

---

# 70. Decoration lifetime

Decoration có:

```text id="v3x9n1"
source
revision
generation
```

Khi provider disconnect:

```text id="a7q4m2"
remove provider decorations
```

Không để stale decorations tồn tại.

---

# 71. Decoration providers

```text id="m6p1z8"
DecorationProvider {
    update(snapshot)
}
```

Providers có thể là:

- compiler
- debugger
- search
- test runner
- AI
- plugin

---

# 72. AI presentation

AI-generated:

- inline suggestion
- diagnostic explanation
- code action preview
- generated edit preview

không được tự động commit.

Flow:

```text id="y2q8k4"
AI
 ↓
proposal
 ↓
CodeEditor preview
 ↓
user/application approval
 ↓
AXEDITOR transaction
```

---

# 73. AI ghost text

Ghost text:

```text id="u5m9p2"
let result = foo(
                 └── suggested...)
```

là overlay.

Không nằm trong Document.

Nếu accepted:

```text id="k1x7c3"
TextEdit → AXEDITOR
```

---

# 74. AI provenance

```text id="p8q3m6"
DecorationOrigin =
    Compiler
    IDE
    Debugger
    Search
    AI
    User
    Plugin
```

AI decoration phải có explicit origin.

---

# 75. Accessibility

CodeEditor phải expose:

```text id="w4n9k2"
role = CodeEditor
```

Accessibility phải có:

- current line
- selection
- editable state
- diagnostics
- cursor location
- folded regions
- breakpoint state khi phù hợp

Không chỉ expose một canvas.

---

# 76. Screen reader

Screen-reader representation cần semantic text ranges.

AXCODEEDITOR không nên expose mỗi glyph như một UI object.

Có thể sử dụng virtualized accessibility representation.

---

# 77. Keyboard commands

CodeEditor tích hợp AXEDITOR commands:

```text id="h2m7q5"
navigation
selection
editing
undo/redo
search
folding
completion
formatting
navigation
```

Code-specific commands:

```text
toggle_comment
fold
unfold
fold_all
unfold_all
go_to_definition
go_to_symbol
trigger_completion
trigger_signature_help
toggle_breakpoint
```

Semantic commands đi qua AXIDE.

---

# 78. Context-sensitive keymap

```text id="q6p1m8"
CodeEditorContext
    ├ Editor
    ├ CompletionPopup
    ├ SignatureHelp
    ├ Debug
    └ Search
```

Ví dụ `Enter` trong completion popup khác `Enter` trong ordinary editing.

---

# 79. Mouse behavior

CodeEditor hỗ trợ:

- click
- double click
- triple click
- drag selection
- gutter click
- diagnostic hover
- symbol hover
- minimap navigation
- breakpoint click
- fold click

Physical pointer events vẫn đến từ AXGUI/AXINPUT.

---

# 80. Gutter interaction

Click line number:

```text id="j9x3v7"
select line
```

Click breakpoint region:

```text id="m5q8p2"
AXDEBUGGER.toggle_breakpoint()
```

Click fold marker:

```text id="c1n6k4"
toggle fold
```

---

# 81. Drag/drop source code

Dragging selected source text:

```text id="z7p2m9"
AXEDITOR selection
 ↓
AXGUI DragSource
```

Drop:

```text id="x4k8q1"
DropPayload
 ↓
AXEDITOR transaction
```

---

# 82. Read-only semantic mode

CodeEditor can display:

```text id="e2m7c5"
Generated
ReadOnly
Preview
Diff
```

without changing AXEDITOR's core semantics.

---

# 83. Diff mode

Optional `CodeDiffView`:

```text id="n8q4x1"
Original        Modified
────────        ────────
 foo            foo
 bar            baz
```

Có thể dùng hai AXEDITOR views:

```text id="p3m7k9"
Document A
Document B
```

và diff engine bên AXIDE/AXSTANDARD.

AXCODEEDITOR chỉ render diff decorations.

---

# 84. Diagnostics batching

Compiler có thể trả hàng nghìn diagnostics.

AXCODEEDITOR phải batch:

```text id="h6q1w4"
10000 diagnostics
       ↓
index by visible range
       ↓
render visible
```

Không instantiate 10000 UI widgets.

---

# 85. Completion scalability

Completion list có thể hàng nghìn item.

UI phải virtualize:

```text id="q2m8v5"
CompletionList
 ↓
visible items
 ↓
virtualized ListView
```

Không tạo widget cho mọi result.

---

# 86. Code lens scalability

CodeLens phải được virtualized theo visible lines.

Không giữ UI control cho toàn bộ source file.

---

# 87. Minimap scalability

Minimap có thể dùng precomputed line summaries:

```text id="v8p3k1"
LineSummary {
    style_runs
    density
}
```

Cache invalidation theo changed ranges.

---

# 88. Incremental invalidation

Một edit:

```text id="g5m9q2"
line 100
```

chỉ invalidates các cache bị ảnh hưởng:

```text
line index
syntax region
semantic region
layout region
minimap region
diagnostics region
```

Không `invalidate_all()` trừ khi cấu hình/representation thay đổi toàn cục.

---

# 89. Frame pipeline

```text id="x7q2m8"
AXEDITOR
   ↓
visible text
   ↓
semantic decorations
   ↓
CodeEditor layout
   ↓
gutter layout
   ↓
overlay layout
   ↓
draw commands
   ↓
AXGUI
   ↓
AXGRAPHICS
```

Mỗi frame phải tránh full-document work.

---

# 90. Memory architecture

Không có:

```text id="s4p9k2"
Widget per line
Widget per token
Widget per diagnostic
Widget per glyph
```

Thay vào đó:

```text id="m8x3q1"
ranges
style IDs
compact metadata
virtualized presentation
```

---

# 91. Render cache

Cache keys có thể bao gồm:

```text id="z2k7p5"
revision
line_range
font
zoom
theme
wrap_mode
DPI
semantic_generation
```

Không cache vô hạn.

LRU/budgeted cache.

---

# 92. Async architecture

```text id="p6m1x9"
CodeEditor
   │
   ├ syntax request
   ├ semantic request
   ├ completion request
   ├ signature request
   └ diagnostics request
          ↓
        AXTASK
          ↓
       AXCOMPILER
          ↓
       result
          ↓
revision/generation check
          ↓
       UI queue
```

---

# 93. Cancellation

Khi document thay đổi:

```text id="h4q8m2"
cancel obsolete requests
```

Nhưng cancellation không thay thế stale-result validation.

Cả hai đều cần.

---

# 94. Generation model

Mỗi provider có:

```text id="w7p3n5"
ProviderGeneration
```

Ví dụ:

```text
syntax = 17
semantic = 21
completion = 9
diagnostic = 44
```

Một result chỉ được apply nếu generation hợp lệ.

---

# 95. Plugin provider isolation

Provider lỗi không được làm CodeEditor crash.

```text id="c9m2x7"
Provider failure
 ↓
ProviderError
 ↓
disable/update provider
 ↓
editor remains usable
```

---

# 96. Security

Source code được xem là dữ liệu không tin cậy.

AXCODEEDITOR không tự động:

- execute source
- execute macros
- load plugins
- fetch remote documentation
- invoke compiler commands

Compiler/IDE actions phải đi qua explicit subsystem contracts.

---

# 97. Resource limits

Giới hạn:

```text id="n3q8v1"
max decoration count
max diagnostics
max completion items
max code lenses
max inline hints
max minimap cache
max popup size
max provider work
```

---

# 98. Extension API

```text id="m7x2q9"
codeeditor_add_decoration_provider()
codeeditor_add_completion_provider()
codeeditor_add_hover_provider()
codeeditor_add_lens_provider()
codeeditor_add_inline_hint_provider()
codeeditor_add_gutter_provider()
```

Providers không được mutate document trực tiếp.

---

# 99. Core APIs

```text id="q5n8k3"
codeeditor_create()
codeeditor_destroy()

codeeditor_document()
codeeditor_view()

codeeditor_set_language()
codeeditor_set_theme()

codeeditor_set_syntax_spans()
codeeditor_set_semantic_spans()

codeeditor_set_diagnostics()
codeeditor_set_fold_regions()

codeeditor_set_decorations()

codeeditor_show_completion()
codeeditor_hide_completion()

codeeditor_show_signature_help()
codeeditor_hide_signature_help()

codeeditor_set_code_lens()
codeeditor_set_inline_hints()

codeeditor_set_breakpoints()
codeeditor_set_execution_location()

codeeditor_set_minimap()
codeeditor_set_overview_ruler()
```

---

# 100. Navigation APIs

```text id="v4m9p1"
codeeditor_go_to_position()
codeeditor_go_to_range()
codeeditor_reveal_range()

codeeditor_center_line()
codeeditor_reveal_symbol()
```

---

# 101. Folding APIs

```text id="x8q2m6"
codeeditor_fold()
codeeditor_unfold()

codeeditor_fold_all()
codeeditor_unfold_all()

codeeditor_toggle_fold()

codeeditor_is_folded()
codeeditor_fold_state()
```

---

# 102. Completion APIs

```text id="k3p7n9"
codeeditor_trigger_completion()
codeeditor_update_completion()
codeeditor_accept_completion()
codeeditor_cancel_completion()

codeeditor_next_completion()
codeeditor_previous_completion()
```

---

# 103. Diagnostic APIs

```text id="b6m1x8"
codeeditor_set_diagnostics()
codeeditor_clear_diagnostics()

codeeditor_diagnostic_at()
codeeditor_reveal_diagnostic()
```

---

# 104. Gutter APIs

```text id="p9q4k2"
codeeditor_gutter_set_mode()
codeeditor_gutter_add_marker()
codeeditor_gutter_remove_marker()
codeeditor_gutter_click()
```

---

# 105. Minimap APIs

```text id="m2x7c5"
codeeditor_minimap_enable()
codeeditor_minimap_disable()
codeeditor_minimap_set_width()
codeeditor_minimap_scroll_to()
```

---

# 106. Debug APIs

```text id="j8p3n6"
codeeditor_set_breakpoint_marker()
codeeditor_clear_breakpoint_marker()

codeeditor_set_execution_location()
codeeditor_clear_execution_location()

codeeditor_set_debug_decoration()
```

AXCODEEDITOR không expose debugger execution APIs.

---

# 107. Provider APIs

```text id="r5m9q1"
codeeditor_provider_register()
codeeditor_provider_unregister()

codeeditor_provider_refresh()
codeeditor_provider_cancel()
```

---

# 108. Accessibility APIs

```text id="v3q8k2"
codeeditor_accessible_document()
codeeditor_accessible_line()
codeeditor_accessible_selection()
codeeditor_accessible_diagnostic()
```

---

# 109. State serialization

View state:

```text id="c7m2p9"
CodeEditorViewState {
    cursor[]
    selections[]
    scroll
    folds
    zoom
    minimap
    wrap_mode
}
```

Có thể được lưu bởi AXIDE/AXAPPLICATION.

---

# 110. No duplicated text state

AXCODEEDITOR tuyệt đối không giữ:

```text id="q8n3m5"
String entire_document
```

để render.

Nó đọc từ AXEDITOR snapshot/range.

---

# 111. No duplicated cursor state

Cursor truth:

```text id="x4p7k2"
AXEDITOR
```

AXCODEEDITOR chỉ cache presentation coordinates nếu cần.

---

# 112. No duplicated compiler state

Semantic truth:

```text id="m6q1v8"
AXCOMPILER / AXIDE
```

CodeEditor chỉ giữ immutable presentation snapshot.

---

# 113. Headless mode

AXCODEEDITOR phải hỗ trợ:

```text id="z9p3k6"
AXGUI_HEADLESS
```

để test:

- diagnostics
- folding
- completion state
- selection presentation
- gutter markers
- accessibility
- command routing

---

# 114. Semantic snapshot testing

Ví dụ:

```text id="h2m8q4"
CodeEditorSnapshot {
    visible_lines
    diagnostics
    folds
    decorations
    completion_state
    accessibility
}
```

Không cần GPU.

---

# 115. Render testing

Có thể snapshot:

```text id="r7q3m1"
DrawCommand stream
```

thay vì phụ thuộc pixel-perfect rendering.

Pixel tests chỉ là additional test layer.

---

# 116. Performance targets

| Operation | Target |
|---|---:|
| simple cursor presentation | < 0.5 ms |
| visible syntax update | < 2 ms |
| gutter layout | < 1 ms |
| visible diagnostic update | < 1 ms |
| completion popup update | < 2 ms |
| visible-line render preparation | < 4 ms |
| 60 FPS frame | ≤ 16.67 ms |

Target trên workload bình thường, không phải absolute hardware guarantee.

---

# 117. Large source target

Phải hướng tới:

```text id="e1m7x4"
100 MB
1 GB+
multi-million lines
```

với graceful degradation.

CodeEditor không được:

```text
instantiate all lines
parse all decorations into widgets
layout entire file every frame
```

---

# 118. Large-file degradation

Nếu document cực lớn:

```text id="k8q2p5"
syntax = limited/incremental
semantic = viewport/background
minimap = compact
code lens = visible-range only
diagnostics = indexed
```

UI vẫn phải responsive.

---

# 119. ABI

```text id="x3m9q7"
AXCODEEDITOR_ABI_1
```

ABI phải ổn định cho:

- CodeEditorHandle
- provider interfaces
- decoration representation
- diagnostic representation
- completion representation
- fold representation
- breakpoint presentation
- snapshot format
- callbacks
- error ABI

---

# 120. Error model

```text id="p4n8m2"
CodeEditorError =
    InvalidDocument
    InvalidRevision
    InvalidRange
    ProviderFailure
    StaleResult
    CompletionUnavailable
    LayoutFailure
    RenderFailure
    DecorationLimit
    DiagnosticLimit
    ResourceLimit
    Cancelled
    AccessibilityFailure
```

Dùng:

```text id="c7x1q9"
Result<T, CodeEditorError>
```

---

# 121. ABI handle

```text id="m2q8v5"
CodeEditorHandle {
    index
    generation
}
```

Không expose internal pointers.

---

# 122. Deterministic behavior

Cùng:

```text id="v9p3k6"
DocumentSnapshot
Revision
Theme
EditorConfig
ProviderResult
```

phải tạo cùng:

```text
layout
fold state
decorations
gutter
completion state
```

trong deterministic test mode.

---

# 123. Threading model

```text id="z5m1q8"
UI thread
 ├ CodeEditor state
 ├ viewport
 ├ presentation mutation
 └ popup state

worker
 ├ compiler
 ├ syntax analysis
 ├ semantic analysis
 ├ search
 └ completion
```

Worker chỉ trả immutable results.

---

# 124. Reentrancy

Provider callback không được phá hủy CodeEditor đang dispatch callback mà không qua lifetime-safe mechanism.

Callbacks phải sử dụng:

```text id="j6q2m9"
generation-safe handle
```

---

# 125. AXTEST conformance

Tests:

```text id="x8m4p1"
CODEEDITOR_SYNTAX
CODEEDITOR_SEMANTIC
CODEEDITOR_GUTTER
CODEEDITOR_FOLDING
CODEEDITOR_DIAGNOSTIC
CODEEDITOR_COMPLETION
CODEEDITOR_SIGNATURE
CODEEDITOR_LENS
CODEEDITOR_INLINE_HINT
CODEEDITOR_BREAKPOINT
CODEEDITOR_MINIMAP
CODEEDITOR_SEARCH
CODEEDITOR_MULTI_CURSOR
CODEEDITOR_ACCESSIBILITY
CODEEDITOR_ASYNC
CODEEDITOR_LARGE_FILE
CODEEDITOR_HEADLESS
```

---

# 126. Fuzzing

Fuzz:

```text id="q7n2m5"
document edits
fold transitions
provider result ordering
completion sequences
diagnostic updates
decoration ranges
cursor movement
multi-cursor
viewport changes
minimap input
debugger state changes
```

Mục tiêu:

```text
no crash
no stale-state corruption
no invalid range
no deadlock
no unbounded allocation
```

---

# 127. Async race tests

Test:

```text id="f3m8q1"
R100 request
R101 edit
R102 edit
R100 result arrives
R101 result arrives
R102 result arrives
```

Chỉ result hợp lệ được apply.

---

# 128. Accessibility tests

AXTEST kiểm tra:

- role
- name
- current line
- selection
- editable state
- diagnostic state
- fold state
- keyboard navigation
- breakpoint semantics

---

# 129. Performance tests

Đo:

```text id="n4q9m2"
p50
p95
p99
max
allocations
memory
```

cho:

- typing
- scrolling
- syntax update
- semantic update
- diagnostics
- completion
- folding
- minimap
- large files

---

# 130. 40 invariants

### Boundary

`CODE-INV-01` — AXCODEEDITOR không sở hữu text storage.

`CODE-INV-02` — AXCODEEDITOR không sở hữu compiler semantics.

`CODE-INV-03` — AXCODEEDITOR không sở hữu debugger execution.

`CODE-INV-04` — AXCODEEDITOR không sở hữu native window.

`CODE-INV-05` — AXCODEEDITOR không tạo thread riêng cho control.

### Document

`CODE-INV-06` — AXEDITOR là source of truth cho text.

`CODE-INV-07` — AXEDITOR là source of truth cho cursor.

`CODE-INV-08` — document revision phải gắn với semantic presentation.

`CODE-INV-09` — stale result không được mutate current presentation.

`CODE-INV-10` — CodeEditor không copy toàn bộ document để render.

### Syntax/Semantic

`CODE-INV-11` — syntax spans phải có valid ranges.

`CODE-INV-12` — semantic spans phải có valid ranges.

`CODE-INV-13` — semantic snapshot phải immutable.

`CODE-INV-14` — semantic presentation không được thay đổi source.

`CODE-INV-15` — incremental update phải invalidation đúng vùng affected.

### UI

`CODE-INV-16` — gutter line numbers phải tương ứng logical lines.

`CODE-INV-17` — folding không được thay đổi document.

`CODE-INV-18` — fold placeholder không phải document text.

`CODE-INV-19` — soft wrap không được thay đổi logical line numbering.

`CODE-INV-20` — minimap không được yêu cầu full-resolution text layout.

### Completion/overlay

`CODE-INV-21` — completion acceptance phải đi qua AXEDITOR edit transaction.

`CODE-INV-22` — completion stale result phải bị reject.

`CODE-INV-23` — signature help không được mutate document.

`CODE-INV-24` — code lens command phải qua Command contract.

`CODE-INV-25` — inline hint không được trở thành document text nếu chưa được accept.

### Diagnostics/debug

`CODE-INV-26` — diagnostic phải có revision/range semantics.

`CODE-INV-27` — stale diagnostics không được hiển thị như current truth.

`CODE-INV-28` — breakpoint marker không phải debugger state authority.

`CODE-INV-29` — execution marker không được thay đổi editor document.

`CODE-INV-30` — debug provider không được bypass capability/security boundary.

### Performance/security

`CODE-INV-31` — line-scale UI phải được virtualized.

`CODE-INV-32` — completion/lens/diagnostic presentation phải được bounded.

`CODE-INV-33` — hot rendering path không được tạo hidden allocation không cần thiết.

`CODE-INV-34` — untrusted provider result phải được validate.

### Integration/ABI

`CODE-INV-35` — background provider không mutate UI trực tiếp.

`CODE-INV-36` — provider cancellation phải được hỗ trợ.

`CODE-INV-37` — accessibility semantics không được phụ thuộc GPU rendering.

`CODE-INV-38` — headless mode không được yêu cầu physical display.

`CODE-INV-39` — `AXCODEEDITOR_ABI_1` phải deterministic và versioned.

`CODE-INV-40` — mọi standard CodeEditor capability phải có AXTEST conformance.

---

# 131. Canonical editing flow

```text id="q8m3p7"
User types
    ↓
AXINPUT
    ↓
AXGUI
    ↓
AXCODEEDITOR
    ↓
AXEDITOR
    ↓
EditTransaction
    ↓
Revision++
    ↓
ChangeSet
    ├── AXCOMPILER
    ├── AXIDE
    └── search/providers
             ↓
       presentation result
             ↓
       AXCODEEDITOR
             ↓
          AXGUI
```

---

# 132. Canonical completion flow

```text id="m5q9x2"
Cursor
  ↓
CodeEditor
  ↓
AXIDE
  ↓
AXCOMPILER
  ↓
CompletionResult
  ↓
revision validation
  ↓
CompletionPopup
  ↓
User accepts
  ↓
TextEdit
  ↓
AXEDITOR
```

---

# 133. Canonical diagnostic flow

```text id="j7p2m8"
AXCOMPILER
     ↓
Diagnostics
     ↓
AXIDE
     ↓
AXCODEEDITOR
     ↓
DiagnosticIndex
     ↓
visible decorations
     ↓
Gutter / underline / hover
```

---

# 134. Canonical debugger flow

```text id="x4n8q1"
AXDEBUGGER
    ↓
ExecutionLocation / Breakpoints
    ↓
AXIDE
    ↓
AXCODEEDITOR
    ↓
Gutter + current-line decoration
```

CodeEditor không biết cách điều khiển process.

---

# 135. Canonical AI flow

```text id="r6m1p9"
AXIDE / AI
     ↓
proposal
     ↓
AXCODEEDITOR preview
     ↓
user/application approval
     ↓
TextEdit[]
     ↓
AXEDITOR
```

Điều này giữ nguyên nguyên tắc:

> **AI có thể đề xuất, nhưng editor engine là nơi duy nhất commit text mutation.**

---

# 136. Architecture summary

```text id="k3x7m2"
                    AXIDE
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
   AXCOMPILER     AXDEBUGGER       AXDOC
        │             │              │
        └─────────────┼──────────────┘
                      ▼
                AXCODEEDITOR
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    Gutter       Presentation     Overlays
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                   AXEDITOR
                      │
                  TextBuffer
                      │
                   AXGUI
                      │
                AXGRAPHICS
```

---

# 137. Definition of Done

`AXCODEEDITOR 5.0` hoàn thành khi:

1. CodeEditor control contract frozen.
2. AXEDITOR integration hoàn chỉnh.
3. Gutter hoạt động.
4. Line numbers hoạt động.
5. Syntax highlighting hoạt động.
6. Incremental syntax presentation hoạt động.
7. Semantic highlighting hoạt động.
8. Diagnostics hoạt động.
9. Diagnostic decorations hoạt động.
10. Folding hoạt động.
11. Indentation guides hoạt động.
12. Whitespace visualization hoạt động.
13. Current-line presentation hoạt động.
14. Multi-cursor rendering hoạt động.
15. Search/replace UI hoạt động.
16. Completion request/display/accept hoạt động.
17. Completion virtualization hoạt động.
18. Signature help hoạt động.
19. Parameter hints hoạt động.
20. CodeLens hoạt động.
21. Inline hints hoạt động.
22. Hover presentation hoạt động.
23. Breadcrumb integration hoạt động.
24. Breakpoint presentation hoạt động.
25. Execution-location presentation hoạt động.
26. Minimap hoạt động.
27. Overview ruler hoạt động.
28. Soft-wrap hoạt động.
29. Long-line virtualization hoạt động.
30. Async cancellation + stale-result rejection hoạt động.
31. AI proposal preview hoạt động.
32. Accessibility semantics đầy đủ.
33. Headless testing hoạt động.
34. Large-file mode hoạt động.
35. Memory/performance budgets được kiểm chứng.
36. Provider isolation hoạt động.
37. AXTEST conformance pass.
38. Fuzzing pass.
39. `AXCODEEDITOR_ABI_1` được freeze.
40. Specification ↔ API ↔ implementation ↔ AXTEST traceability hoàn chỉnh.

---

# 138. Trạng thái cuối

```text id="v9m4q2"
BOOTSTRAP-789
AXCODEEDITOR 5.0
       │
       ├── Gutter
       ├── Syntax
       ├── Semantic Highlighting
       ├── Diagnostics
       ├── Folding
       ├── Completion
       ├── Signature Help
       ├── Code Lens
       ├── Inline Hints
       ├── Breakpoints
       ├── Minimap
       ├── Search UI
       ├── Accessibility
       ├── Large-file Virtualization
       └── AI / Debug / IDE Integration
                    │
                    ▼
             AXIDE / AXEDITOR
```

**AXCODEEDITOR 5.0 — FROZEN.**

---

# BOOTSTRAP-790 — AXDEBUGGER

**Native Axiom Debugger Engine, Process/Thread Inspection, Breakpoints, Watchpoints, Stack Unwinding, Register State, Memory Inspection, Source Mapping, Variable Inspection, Expression Evaluation, Exception/Panic/Trap Handling, Debug Sessions, Remote Debugging & Debug ABI 5.0**

Kiến trúc tiếp theo:

```text id="q7x2m9"
AXIDE
  │
  ▼
AXDEBUGGER
  │
  ├── DebugSession
  ├── Process
  ├── Threads
  ├── Breakpoints
  ├── Watchpoints
  ├── Stack
  ├── Registers
  ├── Memory
  ├── Variables
  ├── Expressions
  ├── SourceMapping
  └── Crash/Panic/Trap
       │
       ├── AXPROCESS
       ├── AXLOADER
       ├── AXRUNTIME
       ├── AXCOMPILER debug info
       └── AXCODEEDITOR
```

**Điểm kiến trúc quan trọng của BOOTSTRAP-790:** debugger phải là một subsystem native độc lập với IDE; `AXCODEEDITOR` chỉ hiển thị breakpoint/current-instruction/variable decorations, còn AXDEBUGGER mới sở hữu **debug session, process control, thread suspension, register/memory inspection, stack unwinding và expression evaluation**.