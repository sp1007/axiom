# BOOTSTRAP-787 — AXWIDGETS

**Native Axiom Standard Widget Library, Desktop Controls, Forms, Navigation, Lists, Trees, Tables, Tabs, Menus, Dialogs, Toolbars, Status Bars, Data Binding, Virtualized Collections, Command Surfaces, Native Interaction Patterns & Accessible Control Runtime 5.0**

**Status:** FROZEN  
**Namespace:** `AXWIDGETS`  
**ABI:** `AXWIDGETS_ABI_1`  
**Depends on:** `AXGUI`, `AXEDITOR`, `AXSTANDARD`, `AXASYNC`, `AXTASK`, `AXTEST`, `AXDOC`

---

# 1. Mục tiêu

`AXGUI` cung cấp **GUI framework**.

`AXWIDGETS` cung cấp **bộ control chuẩn** được xây dựng trên AXGUI.

```text
AXAPPLICATION
      │
      ▼
    AXGUI
      │
      ▼
  AXWIDGETS
      │
 ┌────┼─────────────────────────────┐
 │    │       │       │             │
Input Lists   Data   Navigation   Commands
 │    │       │       │             │
 ▼    ▼       ▼       ▼             ▼
Text  Table  Binding  Tabs        Command
Form  Tree   Models   Menus       Toolbar
```

AXWIDGETS **không được trở thành một GUI framework thứ hai**.

---

# 2. Boundary

## AXWIDGETS sở hữu

- standard controls
- control state
- control behavior
- selection models
- collection models
- data binding
- validation UI
- command surfaces
- navigation controls
- virtualized presentation
- accessibility mapping của controls
- keyboard interaction chuẩn
- standard interaction patterns
- control templates
- control-specific rendering composition

## AXWIDGETS không sở hữu

| Thành phần | Owner |
|---|---|
| Window | AXWINDOW |
| Physical input | AXINPUT |
| Widget tree | AXGUI |
| Layout engine | AXGUI |
| Render backend | AXGRAPHICS |
| Compositor | AXCOMPOSITOR |
| Text editing engine | AXEDITOR |
| Application lifecycle | AXAPPLICATION |
| Task scheduler | AXTASK |
| Async primitives | AXASYNC |
| File/network/database | các subsystem tương ứng |
| Compiler semantics | AXCOMPILER |

---

# 3. Nguyên tắc thiết kế

AXWIDGETS phải tuân thủ:

```text
Struct > class hierarchy
Composition > inheritance
Typed model > untyped callback
Value state > hidden object state
Static dispatch > dynamic dispatch
Virtualization > instantiate-all
Explicit allocation > hidden allocation
Explicit async > hidden background work
Semantic accessibility > visual-only controls
```

Không có:

- GC bắt buộc
- reference counting ngầm
- widget thread riêng
- hidden event thread
- browser DOM
- CSS engine
- JavaScript runtime
- dependency vào native GUI toolkit khác

---

# 4. Control architecture

Mỗi control gồm 4 lớp logic:

```text
             Control
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
     State     Model    Command
       │        │        │
       └────────┼────────┘
                ▼
             AXGUI
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Layout    Events   Render
                │
                ▼
          Accessibility
```

Control không trực tiếp quản lý window hoặc GPU.

---

# 5. Base Control Contract

AXWIDGETS định nghĩa protocol chung:

```text
trait Control {
    fn widget(&self) -> WidgetRef

    fn state(&self) -> ControlState
    fn set_state(&mut self, state: ControlState)

    fn enabled(&self) -> bool
    fn set_enabled(&mut self, value: bool)

    fn visible(&self) -> bool
    fn set_visible(&mut self, value: bool)

    fn focusable(&self) -> bool
    fn request_focus(&mut self)

    fn invalidate(&mut self)
    fn measure(&mut self, constraints: SizeConstraints) -> Size
    fn arrange(&mut self, bounds: Rect)

    fn activate(&mut self)
}
```

Không yêu cầu inheritance.

Một struct có thể implement nhiều control protocol.

---

# 6. Control State

```text
ControlState {
    enabled: bool
    visible: bool
    focused: bool
    hovered: bool
    pressed: bool
    checked: bool
    selected: bool
    expanded: bool
    read_only: bool
    busy: bool
    invalid: bool
}
```

State không được lưu trùng một cách không cần thiết.

Các state có thể được biểu diễn bằng bitset:

```text
ControlStateBits : u32
```

Ví dụ:

```text
ENABLED
FOCUSED
HOVERED
PRESSED
CHECKED
SELECTED
EXPANDED
READ_ONLY
BUSY
INVALID
DISABLED
```

---

# 7. Button

```text
Button {
    label: Str
    icon: IconRef?
    command: CommandRef?
    on_click: Callback?
}
```

Behavior:

```text
pointer_down
    ↓
pressed
    ↓
pointer_up
    ↓
activate
    ↓
Command.execute()
```

Keyboard:

```text
Enter
Space
```

Button phải tự động hỗ trợ accessibility role:

```text
Button
```

Không cho phép callback chạy ngoài UI transaction nếu callback thay đổi UI.

---

# 8. Command

Command là abstraction chung cho:

- Button
- MenuItem
- ToolbarItem
- Shortcut
- ContextMenu
- navigation action

```text
Command {
    id: CommandId
    label: Str
    description: Str
    icon: IconRef?
    shortcut: Shortcut?
    enabled: bool
    checked: bool
    execute: CommandHandler
}
```

API:

```text
command_create()
command_execute()
command_set_enabled()
command_set_checked()
command_bind_shortcut()
command_query()
```

Một command có thể xuất hiện ở nhiều control.

```text
Ctrl+S
  │
  └── Command.Save
       ├── MenuItem
       ├── ToolbarButton
       └── Button
```

---

# 9. Label

```text
Label {
    text: Str
    typography: TypographyRef
    wrapping: TextWrapMode
    alignment: TextAlignment
}
```

Label không sở hữu text shaping engine.

AXGUI/AXEDITOR/text subsystem cung cấp text layout.

---

# 10. Image và Icon

```text
ImageView {
    source: ImageSource
    fit: ImageFit
    alignment: Alignment
}

Icon {
    source: IconSource
    size: Size
}
```

Nguồn:

```text
Raster
Vector
Glyph
GPU texture
Resource ID
```

Không load tài nguyên đồng bộ trên UI thread nếu việc decode có thể tốn thời gian đáng kể.

---

# 11. TextBox

TextBox **không tự implement text editor**.

```text
TextBox
    ↓
AXEDITOR
    ↓
text buffer
selection
cursor
IME
undo/redo
composition
```

```text
TextBox {
    editor: EditorHandle
    placeholder: Str
    read_only: bool
    password_mode: bool
    validation: ValidationState
}
```

AXEDITOR chịu trách nhiệm:

- cursor
- selection
- insertion
- deletion
- IME
- composition
- undo/redo
- text buffer
- Unicode handling

AXWIDGETS chịu trách nhiệm:

- border
- visual state
- placeholder presentation
- focus state
- command integration
- accessibility mapping

---

# 12. PasswordBox

```text
PasswordBox {
    editor: EditorHandle
    reveal: bool
}
```

Đặc biệt:

- không ghi plaintext vào log
- không đưa plaintext vào diagnostics
- accessibility exposure phải theo policy
- clipboard behavior configurable
- memory lifetime tối thiểu cần thiết

---

# 13. CheckBox

```text
CheckBox {
    label: Str
    value: CheckState
}
```

```text
CheckState =
    Unchecked
    Checked
    Indeterminate
```

Hỗ trợ:

- mouse
- keyboard
- accessibility
- command binding

---

# 14. RadioButton

RadioButton không tự tạo group bằng hierarchy ngầm.

```text
RadioGroupId
```

```text
RadioButton {
    group: RadioGroupId
    selected: bool
    value: Any
}
```

`SelectionModel` quản lý selection thực tế.

---

# 15. Toggle

```text
Toggle {
    value: bool
}
```

Có thể render:

- switch
- compact toggle
- icon toggle

Visual presentation không thay đổi semantic behavior.

---

# 16. Slider

```text
Slider<T> {
    value: T
    minimum: T
    maximum: T
    step: T?
}
```

Yêu cầu:

- checked range
- keyboard increment/decrement
- page increment
- accessibility value
- optional continuous update

---

# 17. ProgressBar

```text
ProgressBar {
    value: f64
    minimum: f64
    maximum: f64
    mode: ProgressMode
}
```

```text
ProgressMode =
    Determinate
    Indeterminate
```

Indeterminate không được tạo timer/thread riêng cho mỗi control.

Animation dùng AXGUI animation scheduler.

---

# 18. Spinner

Spinner chỉ là trạng thái visual:

```text
Spinner {
    active: bool
    progress: f32
}
```

Không được tự tạo OS thread.

---

# 19. CollectionModel

Đây là abstraction quan trọng cho List/Tree/Table/ComboBox.

```text
trait CollectionModel<T> {
    fn count() -> usize
    fn item(index: usize) -> T
}
```

Optional:

```text
fn item_key(index) -> Key
fn item_changed(key)
fn items_inserted(range)
fn items_removed(range)
fn items_reset()
```

Không yêu cầu toàn bộ dataset nằm trong widget.

---

# 20. SelectionModel

```text
SelectionModel {
    mode: SelectionMode
    selected: SelectionSet
    anchor: Index?
    current: Index?
}
```

```text
SelectionMode =
    None
    Single
    Multiple
    Extended
}
```

API:

```text
selection_select()
selection_deselect()
selection_toggle()
selection_clear()
selection_select_range()
selection_current()
selection_anchor()
selection_is_selected()
```

Selection model tách khỏi visual control.

Điều này cho phép:

```text
ListView
TableView
TreeView
```

cùng sử dụng một mô hình selection.

---

# 21. ListView

```text
ListView<T> {
    model: CollectionModel<T>
    selection: SelectionModel
    item_template: ItemTemplate<T>
    virtualization: VirtualizationMode
}
```

Pipeline:

```text
model
  ↓
visible range
  ↓
item realization
  ↓
control reuse
  ↓
layout
  ↓
render
```

Không tạo widget cho hàng triệu item.

---

# 22. Virtualization

Virtualization là **bắt buộc** đối với collection controls lớn.

Ví dụ:

```text
10,000,000 rows
       ↓
visible rows ≈ 40
       ↓
realized widgets ≈ 40–100
```

Widget pool:

```text
create
  ↓
bind(item)
  ↓
render
  ↓
unbind
  ↓
reuse
```

Không được giữ reference lâu dài tới item visual đã recycle.

---

# 23. TreeView

```text
TreeModel {
    root_count()
    root(index)
    child_count(node)
    child(node, index)
    is_expandable(node)
}
```

TreeView duy trì:

```text
expanded_set
selection_model
current_node
```

Không flatten toàn bộ tree nếu dataset rất lớn.

Có thể sử dụng lazy expansion:

```text
collapsed
    ↓
expand
    ↓
load children
    ↓
insert visible nodes
```

---

# 24. TableView / DataGrid

Table phải tách:

```text
TableModel
ColumnModel
SelectionModel
SortModel
FilterModel
```

```text
Table
 ├ columns
 ├ header
 ├ rows
 ├ selection
 ├ sorting
 ├ filtering
 └ virtualization
```

Cell API:

```text
CellContext {
    row
    column
    value
    selected
    focused
}
```

Không tạo một object riêng cho mỗi cell nếu không cần.

---

# 25. ColumnModel

```text
Column {
    id
    title
    width
    min_width
    max_width
    alignment
    sortable
    resizable
    visible
}
```

Cho phép:

- resize
- reorder
- hide/show
- sort
- custom cell renderer

---

# 26. Sorting

Sorting nên nằm ở model layer:

```text
SourceModel
    ↓
FilterModel
    ↓
SortModel
    ↓
PaginationModel
    ↓
View
```

Không sort trực tiếp trong render path.

---

# 27. Filtering

```text
Filter<T> {
    predicate
}
```

Filtering có thể:

- synchronous
- asynchronous
- incremental

UI không bị block bởi dataset lớn.

---

# 28. Paging

```text
PagedModel<T> {
    total_count: usize?
    page_size: usize
    load_page(page)
}
```

Hỗ trợ:

```text
local dataset
remote dataset
database-backed model
```

Nhưng AXWIDGETS không sở hữu network/database.

---

# 29. ComboBox

```text
ComboBox<T> {
    model
    selection
    editable
    search
}
```

Pipeline:

```text
ComboBox
 ├ TextBox
 ├ Popup
 ├ ListView
 └ SelectionModel
```

Không cần control implementation độc lập hoàn toàn.

---

# 30. TabView

```text
Tab {
    id
    title
    icon
    content
    closable
}
```

```text
TabView {
    tabs[]
    selected
    overflow_policy
}
```

Hỗ trợ:

- keyboard navigation
- close
- reorder
- overflow
- lazy content creation

Lazy content:

```text
Tab selected
   ↓
instantiate content
```

---

# 31. Panels

Các primitive chuẩn:

```text
Panel
GroupBox
Card
Frame
StackPanel
```

Phần layout thực tế thuộc AXGUI.

AXWIDGETS chỉ cung cấp semantic/container controls.

---

# 32. SplitView / Splitter

```text
SplitView {
    orientation
    first
    second
    ratio
    min_first
    min_second
}
```

Splitter phải:

- keyboard accessible
- DPI aware
- bounded
- deterministic

---

# 33. ScrollView

```text
ScrollView {
    content
    horizontal
    vertical
    viewport
    offset
}
```

Không bắt buộc tạo ScrollBar nếu platform/theme không cần.

Scrolling phải hỗ trợ:

- wheel
- touch
- keyboard
- scrollbar
- programmatic scroll

---

# 34. Menu

```text
Menu {
    items[]
}
```

```text
MenuItem {
    command
    submenu?
    separator
    shortcut
}
```

Menu được xây dựng từ `Command`.

```text
Command
   ↓
MenuItem
```

Do đó command state tự động đồng bộ.

---

# 35. ContextMenu

Context menu có:

```text
target
commands
position
```

Không được tự động thực thi hành động khi mở.

Context:

```text
Widget
Selection
Application
```

có thể cung cấp command set tương ứng.

---

# 36. Toolbar

```text
Toolbar {
    items[]
}
```

Item:

```text
ToolbarButton
ToolbarToggle
ToolbarSeparator
ToolbarSpacer
ToolbarOverflow
```

Toolbar có thể chuyển item ít dùng vào overflow menu.

---

# 37. StatusBar

```text
StatusBar {
    segments[]
}
```

Ví dụ:

```text
Ready | Line 10, Col 20 | UTF-8 | x86_64 | 100%
```

StatusBar không tự lấy global application state.

Application/IDE cung cấp model.

---

# 38. Dialog

```text
Dialog {
    title
    content
    buttons
    modal
}
```

Dialog lifecycle:

```text
create
 ↓
open
 ↓
activate
 ↓
result
 ↓
close
 ↓
destroy
```

Modal dialog phải khóa interaction đúng scope, không khóa toàn bộ process nếu không cần.

---

# 39. MessageBox

MessageBox chỉ là convenience control:

```text
message_box(
    title,
    message,
    buttons,
    icon
)
```

Không phải primitive của AXGUI.

---

# 40. Form

```text
Form {
    fields[]
}
```

```text
FormField<T> {
    label
    editor
    value
    validation
    description
}
```

Form hỗ trợ:

- label association
- validation
- required state
- error/help text
- keyboard navigation
- submit/cancel

---

# 41. ValidationState

```text
ValidationState =
    Valid
    Invalid
    Warning
    Pending
    Unknown
```

```text
ValidationMessage {
    severity
    message
    code
}
```

Validation không được chỉ biểu diễn bằng màu.

Accessibility phải expose semantic state.

---

# 42. Navigation

Controls:

```text
NavigationView
Sidebar
NavigationItem
Breadcrumbs
BreadcrumbItem
```

Model:

```text
NavigationModel {
    items[]
    selected
    history?
}
```

Navigation không sở hữu application routing engine.

---

# 43. SearchBox

```text
SearchBox {
    editor
    query
    debounce
    command
}
```

Search phải hỗ trợ:

- keyboard
- clear
- submit
- IME
- incremental query

Debounce timer dùng scheduler chung.

---

# 44. FilterBar

```text
FilterBar {
    filters[]
}
```

Có thể biểu diễn:

```text
Status = Active
Type = Source
Author = ...
```

Filter state phải serializable nếu application cần session persistence.

---

# 45. DataBinding

```text
DataBinding<T> {
    source
    target
    direction
    converter?
    validation?
}
```

```text
BindingDirection =
    OneWay
    TwoWay
    OneTime
```

Không có binding magic dựa trên reflection bắt buộc.

Ưu tiên:

```text
typed binding
```

thay vì:

```text
string property lookup
```

---

# 46. Binding updates

Pipeline:

```text
Model
 ↓
Binding
 ↓
Control State
 ↓
invalidate
 ↓
layout/render
```

Ngược lại:

```text
User input
 ↓
Control
 ↓
Binding
 ↓
Model
```

Binding cycle phải được phát hiện.

```text
A → B → A
```

không được tạo infinite update loop.

---

# 47. Async Data

Async model:

```text
CollectionModel
      ↓
AsyncModel<T>
      ↓
load()
      ↓
Task<Result<T>>
```

Task phải cancellable:

```text
CancellationToken
```

Pipeline:

```text
UI
 ↓
request
 ↓
background task
 ↓
result
 ↓
UI queue
 ↓
validate generation
 ↓
apply
```

Generation check:

```text
request_generation = 42

result arrives:
if generation != current_generation:
    discard
```

Ngăn stale result ghi đè state mới.

---

# 48. Thread Safety

Quy tắc:

```text
UI thread
    ├ control mutation
    ├ widget tree mutation
    └ visual state

worker
    ├ computation
    ├ data loading
    ├ parsing
    └ decoding
```

Worker không được:

```text
control.set_text(...)
widget.add_child(...)
```

trực tiếp.

Thay vào đó:

```text
ui_post(UiTask)
```

---

# 49. Keyboard navigation

AXWIDGETS định nghĩa navigation semantics chung:

```text
Tab
Shift+Tab
Arrow
Home
End
PageUp
PageDown
Enter
Space
Escape
```

Mỗi control khai báo:

```text
KeyboardPolicy
```

Không để từng control tự tạo shortcut conflict tùy ý.

---

# 50. Focus

Focus hierarchy:

```text
Window
 ↓
FocusScope
 ↓
Control
 ↓
Text/editor caret
```

Dialog tạo focus scope riêng.

Tab order có thể explicit:

```text
tab_index
```

Nếu không khai báo, AXGUI có thể dùng document order.

---

# 51. Accessibility

Mỗi standard control phải có semantic role.

Ví dụ:

```text
Button      → Button
CheckBox    → CheckBox
TextBox     → TextField
Slider      → Slider
ListView    → List
TreeView    → Tree
TableView   → Grid
TabView     → TabList
Dialog      → Dialog
```

Accessibility tree:

```text
Control
   ↓
AccessibleNode
   ↓
AXGUI accessibility layer
   ↓
Platform adapter
```

Không cho phép control chỉ “trông giống” accessible control nhưng thiếu semantics.

---

# 52. Accessibility actions

Ví dụ Button:

```text
Invoke
```

Slider:

```text
Increase
Decrease
SetValue
```

Tree:

```text
Expand
Collapse
Select
```

Table:

```text
Select
Focus
Navigate
```

---

# 53. Styling

AXWIDGETS không tạo CSS.

Style state:

```text
Normal
Hovered
Pressed
Focused
Disabled
Selected
Checked
Invalid
Busy
```

Theme:

```text
Theme
 ├ Typography
 ├ Spacing
 ├ Metrics
 ├ Colors
 ├ Borders
 ├ Radii
 ├ Shadows
 └ Animation
```

Theme token được tham chiếu bằng ID/value.

---

# 54. Control templates

Customisation dùng composition:

```text
Button
 ├ icon
 ├ content
 └ visual template
```

Không cần:

```text
class MyButton : Button
```

Thay vào đó:

```text
ButtonTemplate {
    build(control_state)
}
```

Template không được thay đổi semantic contract.

---

# 55. Custom drawing

Control có escape hatch:

```text
CustomControl {
    measure
    arrange
    render
    handle_event
    accessibility
}
```

Rendering:

```text
draw_context
```

cho phép trực tiếp tạo AXGUI draw commands.

Nhưng custom drawing không được bypass:

- accessibility
- focus
- input routing
- security
- lifetime

---

# 56. Localization

Control text phải hỗ trợ:

```text
Locale
TranslationId
FormattedText
```

Không hard-code UI strings trong widget implementation.

RTL:

```text
LTR
RTL
Auto
```

Layout direction được truyền từ AXGUI.

---

# 57. High DPI

AXWIDGETS sử dụng **logical pixels**.

```text
logical size
      ↓
AXGUI DPI scale
      ↓
device pixels
```

Control không tự nhân DPI nhiều lần.

---

# 58. Animation

Control animation phải sử dụng AXGUI animation scheduler.

Ví dụ:

```text
hover transition
pressed transition
expand/collapse
progress
selection
```

Không tạo timer/thread riêng.

Reduced-motion preference phải được hỗ trợ.

---

# 59. Lifecycle

Chuẩn:

```text
create
 ↓
attach
 ↓
initialize
 ↓
bind
 ↓
measure
 ↓
arrange
 ↓
render
 ↓
interactive
 ↓
unbind
 ↓
detach
 ↓
destroy
```

Control không được sử dụng child/model sau `detach`.

---

# 60. Memory architecture

Mục tiêu:

```text
No GC
No hidden RC
No hidden finalizer
No per-widget thread
```

Sử dụng:

- inline values
- small-vector
- arena cho control trees khi phù hợp
- pool cho virtualized items
- interned IDs/strings
- explicit ownership

Ví dụ ListView 1 triệu item **không** đồng nghĩa 1 triệu Widget allocation.

---

# 61. Large Dataset Architecture

Mục tiêu:

```text
10M records
      ↓
CollectionModel
      ↓
Virtualization
      ↓
~visible controls
```

Memory phụ thuộc chủ yếu vào:

```text
visible range
+
model/cache
```

không phụ thuộc tuyến tính vào số visual controls.

---

# 62. Selection + virtualization

Selection phải tồn tại độc lập với realized widgets.

Sai:

```text
selected = widget.selected
```

Đúng:

```text
SelectionModel
      ↓
item identity
      ↓
realized widget visual state
```

Nếu item bị recycle, selection vẫn tồn tại.

---

# 63. Item identity

Collection item nên có:

```text
Key
```

thay vì chỉ index.

```text
ItemKey = u64 | UUID | application-defined
```

Index có thể thay đổi sau sorting/filtering.

---

# 64. Stable identity

Virtualized controls phải phân biệt:

```text
item identity
```

với:

```text
widget identity
```

```text
Item #ABC
     ↓
Widget #17
     ↓
recycled
     ↓
Widget #17 → Item #XYZ
```

Không được giữ semantic identity cũ.

---

# 65. Sorting + selection

Khi sort:

```text
before:
A B C D

selected:
C

sort:
D C B A
```

Selection vẫn phải trỏ tới `C`, không phải index cũ.

Đây là invariant quan trọng của collection controls.

---

# 66. Filtering + selection

Nếu item bị filter khỏi view:

```text
visible = false
```

không nhất thiết:

```text
selected = false
```

Selection policy phải configurable:

```text
PreserveHiddenSelection
ClearHiddenSelection
```

---

# 67. Paging + selection

Selection model phải hỗ trợ selection của item chưa được load nếu model có stable identity.

```text
selected_keys
```

không bắt buộc item phải đang hiện diện.

---

# 68. Async cancellation

Mọi asynchronous control request phải có cancellation.

Ví dụ:

```text
search("axi")
search("axiom")
```

Request `"axi"` phải có khả năng bị hủy/discard khi `"axiom"` trở thành request mới.

---

# 69. Command surfaces

Một command có thể bind:

```text
Button
Menu
Toolbar
ContextMenu
Shortcut
NavigationItem
```

Ví dụ:

```text
Command.Save
 ├ Ctrl+S
 ├ File → Save
 └ Toolbar Save
```

State:

```text
enabled
checked
label
```

được đồng bộ từ command model.

---

# 70. Context-sensitive commands

Command có thể phụ thuộc context:

```text
ApplicationContext
DocumentContext
SelectionContext
WidgetContext
```

Context resolution:

```text
local
 ↓
parent
 ↓
document
 ↓
application
```

Không dùng global mutable singleton bắt buộc.

---

# 71. Dialog result

Dialog trả:

```text
DialogResult<T>
```

Ví dụ:

```text
Ok(T)
Cancel
Closed
```

Không cần exception để biểu diễn cancel.

---

# 72. Form submission

```text
form_validate()
     ↓
all fields valid?
   /       \
 no         yes
 ↓           ↓
errors     submit
```

Async validation:

```text
Pending
 ↓
Valid / Invalid
```

Submit không được xảy ra khi validation policy yêu cầu chờ.

---

# 73. Native interaction patterns

AXWIDGETS chuẩn hóa:

- double-click
- drag selection
- keyboard selection
- range selection
- context menu
- type-to-search
- incremental search
- expand/collapse
- reorder
- resize
- drag/drop hooks
- clipboard commands

Nhưng physical input vẫn thuộc AXINPUT.

---

# 74. Drag & Drop

AXWIDGETS định nghĩa semantic protocol:

```text
DragSource
DropTarget
DragPayload
DropEffect
```

Không tự truy cập filesystem/network.

Payload được kiểm tra type/capability.

---

# 75. Clipboard

Controls sử dụng command abstraction:

```text
Cut
Copy
Paste
SelectAll
Undo
Redo
```

Text editing thực tế thuộc AXEDITOR.

---

# 76. Headless Mode

AXWIDGETS phải chạy được không có:

- GPU
- native window
- display server

Ví dụ:

```text
AXGUI_HEADLESS
      ↓
AXWIDGETS
      ↓
semantic tree
```

Cho phép AXTEST kiểm tra:

- state
- events
- focus
- selection
- layout
- accessibility
- commands

mà không cần desktop.

---

# 77. Deterministic behavior

Test mode:

```text
fixed clock
fixed animation time
fixed input sequence
fixed model
fixed random seed
```

Không để hover/animation timing gây test nondeterminism.

---

# 78. Rendering tests

Có hai tầng:

### Semantic test

```text
widget state
layout
accessibility
```

### Render test

```text
DrawCommand stream
```

Có thể snapshot canonical draw commands thay vì phụ thuộc pixel GPU.

Pixel golden test chỉ là tầng bổ sung.

---

# 79. Performance targets

Mục tiêu desktop:

| Operation | Target |
|---|---:|
| simple state change | < 1 ms |
| simple control event | < 1 ms |
| small form layout | < 2 ms |
| render preparation | < 4 ms |
| 60 FPS frame | ≤ 16.67 ms |

Collection:

```text
10M model items
```

không được yêu cầu instantiate 10M controls.

Virtualized scrolling phải có chi phí gần:

```text O(visible_items)
```

thay vì:

```text O(total_items)
```

trong render path.

---

# 80. Memory targets

Không có hard-coded universal byte budget vì control phụ thuộc template/theme.

Nhưng:

```text
hidden allocations = 0
per-frame allocations = 0
```

là mục tiêu cho hot path.

Virtualized item pools được reuse.

---

# 81. Error model

AXWIDGETS sử dụng `Result<T,E>`.

Ví dụ:

```text
WidgetError =
    InvalidState
    InvalidModel
    InvalidSelection
    InvalidBinding
    LayoutFailure
    TemplateFailure
    AccessibilityFailure
    AsyncCancelled
    ResourceLimit
```

Không dùng exception bắt buộc.

---

# 82. API chính

```text
widget_create()
widget_destroy()

button_create()
button_set_command()
button_click()

label_create()
label_set_text()

textbox_create()
textbox_editor()

checkbox_create()
checkbox_set_state()

radiobutton_create()
toggle_create()

slider_create()
slider_set_value()

progress_create()
spinner_create()

list_create()
list_set_model()
list_set_selection()

tree_create()
tree_set_model()

table_create()
table_set_model()
table_add_column()
table_remove_column()

combobox_create()

tabview_create()
tab_add()
tab_remove()
tab_select()

panel_create()
groupbox_create()
card_create()

splitview_create()

scrollview_create()

menu_create()
menu_add_item()
menu_add_separator()

toolbar_create()
toolbar_add_command()

statusbar_create()

dialog_create()
dialog_open()
dialog_close()
dialog_result()

form_create()
form_add_field()
form_validate()
form_submit()

navigation_create()
navigation_select()

searchbox_create()
filterbar_create()
```

---

# 83. Model APIs

```text
collection_model_create()
collection_model_count()
collection_model_item()
collection_model_key()

selection_create()
selection_select()
selection_deselect()
selection_toggle()
selection_clear()
selection_select_range()

sort_model_create()
filter_model_create()
paging_model_create()

binding_create()
binding_update()
binding_disconnect()

virtualizer_create()
virtualizer_visible_range()
virtualizer_realize()
virtualizer_recycle()
```

---

# 84. Command APIs

```text
command_create()
command_destroy()
command_execute()

command_set_enabled()
command_set_checked()
command_set_label()

command_bind_shortcut()
command_unbind_shortcut()

command_context_push()
command_context_pop()
command_resolve()
```

---

# 85. Accessibility APIs

```text
control_accessible_node()
control_accessible_role()
control_accessible_name()
control_accessible_value()
control_accessible_state()
control_accessible_actions()

control_accessible_invoke()
control_accessible_set_value()
```

---

# 86. Template APIs

```text
template_create()
template_destroy()

control_set_template()
control_get_template()

template_build()
template_measure()
template_arrange()
template_render()
```

Template lifecycle phải deterministic.

---

# 87. Async APIs

```text
control_load_async()
control_cancel_async()

control_async_generation()
control_apply_async_result()

collection_load_async()
collection_cancel()
```

Mọi async result phải xác thực:

```text
control lifetime
generation
cancellation
```

trước khi apply.

---

# 88. ABI

```text
AXWIDGETS_ABI_1
```

ABI phải ổn định đối với:

- Control handles
- Widget IDs
- Selection model ABI
- Collection model ABI
- Command ABI
- Binding ABI
- Template ABI
- Accessibility ABI
- error representation

Struct ABI versioning phải explicit.

---

# 89. ABI handle safety

Handle:

```text
WidgetHandle {
    index
    generation
}
```

Object reuse:

```text
destroy Widget #10 generation 3
create Widget #10 generation 4
```

Handle generation cũ phải fail validation.

---

# 90. Extension boundary

Third-party/custom controls có thể implement:

```text
Control
CollectionModel
SelectionModel
CommandProvider
AccessibleProvider
Template
```

Nhưng không được yêu cầu:

- browser runtime
- GC
- external GUI toolkit
- hidden thread

Plugin/capability security thuộc AXSECURITY/AXCAPABILITY.

---

# 91. Security

Untrusted model/data phải được coi là dữ liệu.

Không tự động:

- execute command
- load arbitrary executable
- execute script
- invoke network
- mở file ngoài policy
- parse unlimited input

Text/image/table data phải có resource limits.

---

# 92. Resource limits

Có thể giới hạn:

```text
max realized widgets
max popup depth
max menu depth
max text length
max selection size
max image decode size
max async requests
max template recursion
max tree expansion work
```

Khi vượt giới hạn:

```text
ResourceLimit
```

thay vì crash.

---

# 93. Reentrancy

Control callback có thể gây mutation.

Do đó event dispatcher cần transaction semantics:

```text
dispatch event
 ↓
callback
 ↓
state changes queued/applied
 ↓
invalidate
 ↓
next dispatch phase
```

Không cho phép một callback phá hủy context đang được dispatcher sử dụng mà không có lifetime protection.

---

# 94. Lifetime safety

Mọi callback chứa control reference phải kiểm tra generation/lifetime.

Không giữ raw pointer lâu dài nếu control có thể bị destroy.

```text
WeakControlHandle
```

là lựa chọn cho callback lâu sống.

---

# 95. Layout boundary

AXWIDGETS không tự implement layout algorithm mới.

Ví dụ:

```text
Form
```

có thể yêu cầu:

```text
GridLayout
```

của AXGUI.

```text
ListView
```

sử dụng layout primitives của AXGUI.

---

# 96. Text boundary

```text
AXWIDGETS
     ↓
AXEDITOR
     ↓
text buffer
IME
selection
undo
```

Không được duplicate text-editing implementation trong TextBox, ComboBox hay SearchBox.

---

# 97. Application integration

```text
AXAPPLICATION
      ↓
AXGUI
      ↓
AXWIDGETS
      ↓
Application UI
```

AXAPPLICATION cung cấp lifecycle.

AXWIDGETS chỉ quản lý controls.

---

# 98. IDE integration

AXIDE có thể dùng:

```text
AXWIDGETS
 ├ TreeView
 ├ TableView
 ├ TabView
 ├ TextBox
 ├ SearchBox
 ├ Toolbar
 ├ Menu
 ├ Dialog
 └ StatusBar
```

Nhưng AXWIDGETS không chứa logic IDE.

---

# 99. AXTEST integration

Mỗi control phải có:

```text
semantic snapshot
```

Ví dụ:

```text
Button {
    enabled: true
    focused: false
    label: "Save"
}
```

Test có thể dispatch:

```text
click
keypress
focus
select
expand
scroll
```

và kiểm tra state mà không cần desktop thật.

---

# 100. Fuzzing

Fuzz targets:

```text
event sequences
selection ranges
tree expansion
table mutations
binding graphs
async completion ordering
keyboard sequences
focus transitions
layout constraints
template trees
accessibility trees
```

Đặc biệt:

```text
destroy during callback
model reset during selection
async completion after destroy
```

phải được fuzz.

---

# 101. Conformance

AXTEST phải có suite:

```text
WIDGET_BUTTON
WIDGET_TEXTBOX
WIDGET_SELECTION
WIDGET_LIST
WIDGET_TREE
WIDGET_TABLE
WIDGET_MENU
WIDGET_DIALOG
WIDGET_FORM
WIDGET_NAVIGATION
WIDGET_ACCESSIBILITY
WIDGET_VIRTUALIZATION
WIDGET_BINDING
WIDGET_ASYNC
```

Mỗi control phải pass:

```text
semantic
lifecycle
keyboard
accessibility
thread-safety
determinism
resource-limit
```

---

# 102. 40 invariants

### Control

`WIDGET-INV-01` — mọi standard control phải có stable WidgetId.

`WIDGET-INV-02` — stale handle phải bị phát hiện.

`WIDGET-INV-03` — lifecycle phải deterministic.

`WIDGET-INV-04` — control không sở hữu native window.

`WIDGET-INV-05` — control không tạo thread riêng.

### State

`WIDGET-INV-06` — state mutation phải qua UI ownership rule.

`WIDGET-INV-07` — disabled control không được activate.

`WIDGET-INV-08` — focus state phải nhất quán với AXGUI.

`WIDGET-INV-09` — visual state không được thay thế semantic state.

`WIDGET-INV-10` — state transition phải deterministic.

### Models

`WIDGET-INV-11` — CollectionModel không phụ thuộc widget lifetime.

`WIDGET-INV-12` — SelectionModel không phụ thuộc realized widget.

`WIDGET-INV-13` — item identity không đồng nhất với visual widget identity.

`WIDGET-INV-14` — sorting không được phá selection identity.

`WIDGET-INV-15` — filtering không được làm hỏng model identity.

### Virtualization

`WIDGET-INV-16` — virtualized control không instantiate toàn bộ dataset.

`WIDGET-INV-17` — recycled widget phải được rebind hoàn toàn.

`WIDGET-INV-18` — stale binding phải bị vô hiệu hóa.

`WIDGET-INV-19` — visible-range calculation phải bounded.

`WIDGET-INV-20` — virtualization không được làm mất accessibility semantics.

### Input

`WIDGET-INV-21` — keyboard navigation phải deterministic.

`WIDGET-INV-22` — focus traversal phải không tạo cycle ngoài focus-scope semantics.

`WIDGET-INV-23` — command activation phải qua command contract.

`WIDGET-INV-24` — callback không được bypass lifetime validation.

`WIDGET-INV-25` — TextBox phải sử dụng AXEDITOR.

### Data binding

`WIDGET-INV-26` — binding graph không được infinite-loop.

`WIDGET-INV-27` — stale async result không được mutate current state.

`WIDGET-INV-28` — cancellation phải được quan sát.

`WIDGET-INV-29` — background task không mutate UI trực tiếp.

`WIDGET-INV-30` — binding type mismatch phải báo lỗi deterministic.

### Accessibility

`WIDGET-INV-31` — standard control phải expose semantic role.

`WIDGET-INV-32` — visual-only state không được là accessibility-only state.

`WIDGET-INV-33` — keyboard-accessible action phải có semantic action tương ứng.

`WIDGET-INV-34` — validation errors phải accessible.

### Performance/security

`WIDGET-INV-35` — hot render path không được tạo allocation không cần thiết.

`WIDGET-INV-36` — resource limits phải được enforce.

`WIDGET-INV-37` — untrusted data không tự động execute behavior.

`WIDGET-INV-38` — headless mode phải không yêu cầu display/GPU.

### ABI/testing

`WIDGET-INV-39` — `AXWIDGETS_ABI_1` phải deterministic và versioned.

`WIDGET-INV-40` — mọi standard widget phải có AXTEST conformance coverage.

---

# 103. Canonical event flow

Ví dụ Button:

```text
AXINPUT
   ↓
AXGUI event routing
   ↓
Button
   ↓
ControlState.PRESSED
   ↓
pointer release
   ↓
Command
   ↓
Application
   ↓
state mutation
   ↓
AXGUI invalidation
   ↓
RenderTree
```

---

# 104. Canonical List flow

```text
CollectionModel
       ↓
Virtualizer
       ↓
VisibleRange
       ↓
ItemTemplate
       ↓
WidgetPool
       ↓
SelectionModel
       ↓
AXGUI
       ↓
Render
```

---

# 105. Canonical async flow

```text
User
 ↓
SearchBox
 ↓
request generation 12
 ↓
AXTASK
 ↓
worker
 ↓
Result
 ↓
UI queue
 ↓
generation == 12 ?
 ├─ no → discard
 └─ yes
      ↓
apply model
      ↓
invalidate
```

---

# 106. Canonical accessibility flow

```text
Control
   ↓
Control semantic state
   ↓
AccessibleNode
   ↓
AXGUI accessibility tree
   ↓
platform adapter
   ↓
OS accessibility API
```

---

# 107. Why AXWIDGETS must remain separate from AXGUI

Nếu gộp hai tầng:

```text
AXGUI = framework + 40 controls + data models + forms + tables...
```

framework sẽ phình lớn và khó thay đổi.

Thiết kế đúng:

```text
AXGUI
  = primitive GUI engine

AXWIDGETS
  = reusable standard control library
```

Do đó Axiom có thể:

- xây IDE
- xây file manager
- xây database GUI
- xây editor
- xây business application

mà không sửa core GUI engine.

---

# 108. Zero-cost usage

Application có thể chọn profile:

```text
AXWIDGETS_MINIMAL
AXWIDGETS_STANDARD
AXWIDGETS_EXTENDED
```

Ví dụ console utility không link:

```text
AXWIDGETS
AXGUI
AXWINDOW
```

Desktop app mới link chúng.

Dead stripping loại bỏ control không sử dụng.

---

# 109. Binary size

Không yêu cầu toàn bộ widget library nằm trong executable.

```text
Application
 ↓
used controls only
 ↓
generic specialization
 ↓
dead stripping
 ↓
AXLINKER
```

Mục tiêu là không trả chi phí runtime cho control không sử dụng.

---

# 110. Generic implementation

Ví dụ:

```text
ListView<T>
TableView<T>
ComboBox<T>
```

được monomorphize khi phù hợp.

Không biến mọi item thành:

```text
Any
Object
Box<T>
```

chỉ để có genericity.

---

# 111. No inheritance tree

Không thiết kế:

```text
Widget
 └ Control
    └ ButtonBase
       └ Button
          └ SpecialButton
```

Thay vào đó:

```text
Button
 ├ Control
 ├ CommandSurface
 ├ Focusable
 ├ Accessible
 └ Activatable
```

Các capability là trait/protocol.

---

# 112. Standard control composition

Ví dụ ComboBox:

```text
ComboBox
 ├ TextBox
 ├ Popup
 ├ ListView
 ├ SelectionModel
 └ Command
```

TabView:

```text
TabView
 ├ TabStrip
 │   └ TabButton*
 └ ContentPresenter
```

Dialog:

```text
Dialog
 ├ Title
 ├ Content
 └ CommandBar
```

Điều này giảm implementation duplication.

---

# 113. AI-readable metadata

Mỗi control cung cấp metadata tương thích AXDOC:

```text
WidgetMetadata {
    type
    purpose
    properties[]
    events[]
    commands[]
    models[]
    accessibility_role
    lifecycle
    thread_safety
    allocation
    async_behavior
}
```

AI/IDE có thể biết:

```text
"TableView có virtualization"
"TextBox sử dụng AXEDITOR"
"SelectionModel độc lập widget"
```

mà không cần suy đoán.

---

# 114. Documentation linkage

Mỗi API có:

```text
AXDOC SymbolId
AXTEST test IDs
AXGUI dependency
AXABI version
```

Tạo traceability:

```text
AXDOC
  ↕
AXWIDGETS API
  ↕
AXTEST
  ↕
implementation
```

---

# 115. Performance validation

AXTEST phải đo:

- widget creation
- event dispatch
- layout
- rendering preparation
- virtualization
- selection
- model reset
- sorting
- filtering
- async completion
- accessibility traversal
- memory allocations

Không chỉ đo average.

Phải lưu:

```text
p50
p95
p99
max
allocation count
```

---

# 116. Failure containment

Nếu custom model lỗi:

```text
ModelError
```

không được làm hỏng toàn bộ GUI process nếu subsystem có thể cô lập lỗi.

Nếu template invalid:

```text
TemplateFailure
```

control phải chuyển sang safe fallback/render diagnostic.

---

# 117. ABI compatibility

Một `AXWIDGETS_ABI_1` consumer phải kiểm tra:

```text
AXGUI ABI
AXEDITOR ABI
AXSTANDARD ABI
AXTASK ABI
```

trước khi load module.

Không silently accept ABI mismatch.

---

# 118. Build integration

AXBUILD phải có khả năng:

```text
import axwidgets
```

và chỉ link module/control được sử dụng.

Ví dụ:

```text
app
 ├ AXGUI
 ├ AXWIDGETS.Button
 ├ AXWIDGETS.TextBox
 └ AXWIDGETS.ListView
```

không nhất thiết link:

```text
Table
Tree
Menu
Dialog
...
```

nếu dead-stripping không đủ granular.

---

# 119. Platform neutrality

AXWIDGETS không hard-code:

```text
Win32
Cocoa
UIKit
Android Views
GTK
Qt
```

Platform integration:

```text
AXWIDGETS
    ↓
AXGUI
    ↓
AXWINDOW / AXDISPLAY / AXCOMPOSITOR
    ↓
platform
```

---

# 120. Definition of Done

`AXWIDGETS 5.0` được xem là hoàn thành khi:

1. Standard control taxonomy được frozen.
2. Control lifecycle được định nghĩa.
3. Base Control contract được implement.
4. Command model hoạt động.
5. SelectionModel hoạt động độc lập.
6. CollectionModel hoạt động.
7. ListView virtualization hoạt động.
8. TreeView virtualization hoạt động.
9. TableView virtualization hoạt động.
10. ComboBox hoạt động.
11. TabView hoạt động.
12. Menu/ContextMenu hoạt động.
13. Toolbar hoạt động.
14. Dialog/Form hoạt động.
15. Validation model hoạt động.
16. Navigation controls hoạt động.
17. Search/filter model hoạt động.
18. DataBinding hoạt động.
19. Async cancellation hoạt động.
20. TextBox tích hợp AXEDITOR.
21. Accessibility tree đầy đủ.
22. Keyboard navigation đầy đủ.
23. RTL/localization hoạt động.
24. DPI scaling đúng.
25. Animation dùng scheduler chung.
26. Headless mode hoạt động.
27. Semantic testing hoạt động.
28. Virtualization test với dataset lớn pass.
29. Fuzz lifecycle/reentrancy pass.
30. Memory allocation hot-path được kiểm soát.
31. ABI test pass.
32. AXDOC metadata đầy đủ.
33. AXTEST conformance pass.
34. Không phụ thuộc browser/native GUI toolkit.
35. Không có hidden GC/RC/thread.
36. Static linking hoạt động.
37. Dead stripping hoạt động.
38. Cross-platform ABI validation pass.
39. `AXWIDGETS_ABI_1` được freeze.
40. Specification ↔ API ↔ implementation ↔ test traceability hoàn chỉnh.

---

# 121. Trạng thái cuối

```text
BOOTSTRAP-787
AXWIDGETS 5.0
        │
        ├── Standard Controls
        ├── Selection
        ├── Collections
        ├── Virtualization
        ├── Commands
        ├── Binding
        ├── Forms
        ├── Navigation
        ├── Accessibility
        ├── Async
        ├── Headless Testing
        └── Native ABI
             │
             ▼
        AXIDE / APPLICATIONS
```

**AXWIDGETS 5.0 — FROZEN.**

---

# BOOTSTRAP-788 — AXEDITOR

**Native Axiom Text Editor Engine, Gap/Rope Text Buffer, UTF-8/Unicode Editing, Cursor & Selection, IME, Composition, Undo/Redo, Multi-Cursor, Search/Replace, Syntax-Aware Editing, Incremental Text Analysis, Large-File Editing, Virtualized Text Rendering & Editor ABI 5.0**

Kiến trúc kế tiếp:

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
    ┌─────┼──────────────┐
    ▼     ▼              ▼
 TextBuffer Cursor      IME
    │     │              │
    ├─────┼──────────────┤
    ▼     ▼              ▼
Undo   Selection     Composition
    │
    ▼
Incremental Analysis
    │
    ▼
AXCOMPILER / AXDOC / AXIDE
```

**Mục tiêu chính của BOOTSTRAP-788:** xây dựng editor engine đủ mạnh cho IDE Axiom nhưng vẫn giữ được nguyên tắc **native, zero-copy khi có thể, không GC, không hidden allocation, xử lý file rất lớn và Unicode/IME đúng ngay từ nền tảng**.