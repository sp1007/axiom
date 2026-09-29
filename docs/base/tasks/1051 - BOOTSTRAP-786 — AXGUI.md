# BOOTSTRAP-786 — AXGUI

**Native Axiom GUI Framework, Retained/Immediate Hybrid UI Model, Widget Tree, Layout Engine, Input Routing, Focus Management, Accessibility Tree, Styling, Themes, Text/UI Integration, GPU Rendering, Window Integration, Native Controls, Event Loop & High-Performance Desktop UI Runtime 5.0**

**Status:** FROZEN  
**Namespace:** `AXGUI`  
**ABI:** `AXGUI_ABI_1`  
**Depends on:** `AXAPPLICATION`, `AXWINDOW`, `AXDISPLAY`, `AXCOMPOSITOR`, `AXINPUT`, `AXGRAPHICS`, `AXTEXT`/text-layout facilities, `AXMEMORY`, `AXRUNTIME`, `AXIDE`, `AXEDITOR`

---

# 1. Mục tiêu

`AXGUI` là **GUI framework native của Axiom**.

Nó nằm trên:

```text
AXDISPLAY
    ↓
AXCOMPOSITOR
    ↓
AXWINDOW
    ↓
AXGUI
    ↓
Application UI
```

Mục tiêu là có một framework đủ mạnh để xây:

- Axiom IDE
- file manager
- settings
- terminal
- database tools
- media applications
- engineering applications
- desktop applications
- lightweight editors
- native productivity software

mà không cần:

- WPF
- Qt
- GTK
- Electron
- Java UI
- browser engine

trong final Axiom stack.

---

# 2. Architectural Principle

AXGUI chọn **retained-mode UI làm semantic model**, kết hợp **immediate-style rendering/update APIs** cho các trường hợp đặc biệt.

```text
Application
     │
     ▼
Widget Tree
     │
     ├── state
     ├── layout
     ├── event handlers
     ├── accessibility
     └── semantics
     │
     ▼
Render Tree
     │
     ▼
AXGRAPHICS / AXCOMPOSITOR
```

Không chọn immediate-mode thuần túy vì:

- accessibility khó
- focus/navigation khó
- retained state khó
- large UI tree kém thuận tiện
- editor/IDE cần persistent widget state

Không chọn retained rendering quá nặng theo kiểu browser DOM.

---

# 3. Boundary

AXGUI sở hữu:

- widget model
- UI tree
- layout
- styling
- theme
- event routing
- focus
- keyboard navigation
- gestures
- UI state
- accessibility tree
- rendering abstraction
- controls
- menus
- dialogs
- popup
- tooltip
- scrolling
- animation scheduling
- UI resource lifecycle

AXGUI không sở hữu:

- OS window primitive → `AXWINDOW`
- GPU device authority → `AXGRAPHICS`
- compositor → `AXCOMPOSITOR`
- physical input device → `AXINPUT`
- application lifecycle → `AXAPPLICATION`
- text editing semantics → `AXEDITOR`
- IDE semantics → `AXIDE`
- filesystem → `AXSTORAGE`
- networking → `AXNETWORK`

---

# 4. Overall Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        Application                           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                           AXGUI                              │
│                                                              │
│  Widget Tree                                                 │
│  ├── State                                                   │
│  ├── Layout                                                  │
│  ├── Events                                                  │
│  ├── Focus                                                   │
│  ├── Accessibility                                           │
│  └── Styling                                                 │
│                                                              │
│  Render Tree                                                 │
│  ├── Geometry                                                │
│  ├── Clips                                                   │
│  ├── Transforms                                              │
│  ├── Text/Glyphs                                             │
│  └── Draw commands                                           │
└───────────────┬──────────────────────┬───────────────────────┘
                │                      │
                ▼                      ▼
           AXWINDOW                 AXINPUT
                │
                ▼
          AXCOMPOSITOR
                │
                ▼
           AXDISPLAY
```

---

# 5. GUI Application Model

Một application có:

```text
GuiApplication {
    id
    windows[]
    resources
    theme
    locale
    accessibility
    scheduler
}
```

Mỗi window có một root:

```text
Window
  ↓
GuiRoot
  ↓
Widget Tree
```

---

# 6. Widget

Canonical model:

```text
Widget {
    id
    parent
    children[]
    bounds
    layout
    style
    state
    flags
    accessibility
}
```

Widget ID:

```text
WidgetId = u64
```

không dùng raw pointer làm public identity.

---

# 7. Widget Tree

Ví dụ:

```text
Window
└── Root
    ├── MenuBar
    ├── SplitView
    │   ├── FileExplorer
    │   └── Editor
    └── StatusBar
```

Tree là semantic UI hierarchy.

---

# 8. Widget Lifecycle

```text
create
  ↓
attach
  ↓
initialize
  ↓
measure
  ↓
layout
  ↓
render
  ↓
events*
  ↓
detach
  ↓
destroy
```

Không được render widget trước khi initialization hoàn tất.

---

# 9. Widget State

State tách khỏi geometry:

```text
WidgetState {
    enabled
    visible
    focused
    hovered
    pressed
    checked
    selected
    expanded
    disabled_reason?
}
```

Application-specific state không bị framework sở hữu.

---

# 10. Widget Classes

Axiom không cần language-level class.

GUI controls được mô hình hóa bằng:

```text
struct + traits + functions
```

Ví dụ:

```text
Button {
    label
    on_click
}
```

với các behavior traits:

```text
Focusable
Clickable
Accessible
Stylable
```

Đi đúng định hướng struct-oriented của Axiom.

---

# 11. Widget Behavior

Behavior được compose:

```text
Widget
 ├── Focusable
 ├── Hoverable
 ├── Clickable
 ├── Scrollable
 ├── Draggable
 └── Accessible
```

Không cần inheritance hierarchy sâu.

---

# 12. Layout Engine

Layout là một subsystem riêng:

```text
Widget Tree
     ↓
Measure
     ↓
Arrange
     ↓
Geometry Tree
```

Hai phase:

```text
measure()
arrange()
```

---

# 13. Measure

Widget yêu cầu:

```text
SizeConstraint {
    min
    preferred
    max
}
```

Kết quả:

```text
MeasuredSize {
    width
    height
}
```

---

# 14. Arrange

Parent quyết định:

```text
Rect {
    x
    y
    width
    height
}
```

Child không tự thay đổi parent geometry.

---

# 15. Layout Models

Baseline controls:

```text
STACK
ROW
COLUMN
GRID
OVERLAY
ABSOLUTE
SCROLL
DOCK
SPLIT
```

---

# 16. Stack Layout

```text
Column
├── Header
├── Content
└── Footer
```

hỗ trợ:

```text
spacing
padding
alignment
distribution
```

---

# 17. Grid Layout

```text
Grid
 ├── rows[]
 └── columns[]
```

Row/column sizing:

```text
FIXED
AUTO
FLEX
```

---

# 18. Flex Layout

AXGUI có flex-like layout nhưng không cần clone CSS.

```text
FlexDirection
FlexGrow
FlexShrink
Basis
Alignment
Gap
```

API phải native Axiom, không web-compatible by design.

---

# 19. Constraints

Layout engine hỗ trợ:

```text
minimum
maximum
preferred
aspect_ratio
alignment
```

Không đưa một constraint solver nặng vào mọi widget.

Complex constraints là optional subsystem.

---

# 20. DPI / Scaling

Geometry logical units:

```text
LogicalPx
```

mapping:

```text
LogicalPx
   ↓
DPI scale
   ↓
DevicePx
```

Không lưu UI layout cố định bằng physical pixels.

---

# 21. Multi-Monitor

Mỗi window có:

```text
DisplayId
DpiScale
WorkArea
```

AXGUI phản ứng với DPI/display change.

---

# 22. Rendering Model

Widget không trực tiếp vẽ framebuffer.

```text
Widget Tree
    ↓
Render Tree
    ↓
Draw Commands
    ↓
AXGRAPHICS
    ↓
AXCOMPOSITOR
```

---

# 23. Render Node

```text
RenderNode {
    widget_id
    bounds
    transform
    clip
    opacity
    commands[]
}
```

---

# 24. Draw Commands

Canonical primitives:

```text
DrawRect
DrawRoundedRect
DrawPath
DrawImage
DrawText
DrawGlyphRun
DrawBorder
PushClip
PopClip
PushTransform
PopTransform
```

---

# 25. GPU Acceleration

AXGUI ưu tiên GPU nhưng không bắt buộc.

```text
GPU renderer
     │
     └── AXGRAPHICS

Software renderer
     │
     └── AXDISPLAY fallback
```

Application semantics không phụ thuộc renderer.

---

# 26. Render Batching

Các command tương thích được batch:

```text
DrawRect
DrawRect
DrawRect
```

→ một batch.

Texture/image resources cũng được grouped khi có thể.

---

# 27. Dirty Regions

Không render toàn window sau mỗi thay đổi.

```text
Widget changed
     ↓
dirty bounds
     ↓
dirty region union
     ↓
partial render
```

---

# 28. Render Invalidation

Widget có thể yêu cầu:

```text
invalidate_layout()
invalidate_paint()
invalidate_measure()
```

Phân biệt:

```text
layout invalidation
paint invalidation
```

để tránh layout lại toàn tree.

---

# 29. Layout Invalidation

Ví dụ thay đổi:

```text
button label
```

có thể yêu cầu:

```text
measure
arrange
paint
```

nhưng thay đổi:

```text
button color
```

chỉ cần:

```text
paint
```

---

# 30. Event Model

```text
Input Device
     ↓
AXINPUT
     ↓
AXGUI Event
     ↓
Hit Test
     ↓
Capture
     ↓
Target
     ↓
Bubble
```

---

# 31. Event

```text
GuiEvent {
    type
    timestamp
    target
    modifiers
    position?
    device
}
```

Event types:

```text
POINTER
KEY
TEXT
FOCUS
WINDOW
SCROLL
GESTURE
DRAG
DROP
IME
ACCESSIBILITY
```

---

# 32. Event Propagation

Ba phase:

```text
CAPTURE
TARGET
BUBBLE
```

Ví dụ:

```text
Window
  ↓ capture
Panel
  ↓ capture
Button
  ↑ bubble
Panel
  ↑ bubble
Window
```

---

# 33. Event Cancellation

Handler có thể:

```text
consume
stop_propagation
prevent_default
```

Nhưng event system không được làm mất input events ngoài policy.

---

# 34. Hit Testing

```text
pointer(x,y)
     ↓
topmost visible widget
     ↓
hit target
```

Hit test phải tôn trọng:

- clipping
- transforms
- visibility
- enabled state
- z-order
- popup layers

---

# 35. Pointer Capture

Drag operation:

```text
pointer_down
     ↓
capture(widget)
     ↓
pointer_move*
     ↓
pointer_up
     ↓
release
```

Widget tiếp tục nhận pointer event dù pointer rời bounds.

---

# 36. Keyboard Focus

Một window có:

```text
FocusManager
```

chỉ một logical keyboard focus tại một thời điểm.

```text
Window
 └── FocusedWidget
```

---

# 37. Focus Navigation

Keyboard navigation:

```text
Tab
Shift+Tab
Arrow
Enter
Escape
```

Focus order có thể:

```text
explicit
tree order
spatial
```

---

# 38. Focus Scope

Dialogs, menus, popups có focus scope riêng.

```text
Main Window
     │
     └── Dialog Scope
          ├── input
          ├── button
          └── cancel
```

Focus không được thoát scope khi modal.

---

# 39. Keyboard Event

```text
KeyEvent {
    key
    physical_key
    modifiers
    repeat
    pressed
}
```

Phân biệt:

```text
logical key
physical key
```

để hỗ trợ keyboard layout.

---

# 40. Text Input

Text nhập qua:

```text
TextInputEvent
```

không suy ra trực tiếp từ KeyEvent.

Điều này bắt buộc để hỗ trợ:

- Unicode
- IME
- dead keys
- compose
- Vietnamese input
- CJK input

---

# 41. IME Composition

```text
composition_start
      ↓
composition_update*
      ↓
composition_commit
```

Widget nhận composition state riêng.

---

# 42. Pointer Model

```text
PointerEvent {
    pointer_id
    device
    position
    buttons
    pressure?
    tilt?
    modifiers
}
```

Hỗ trợ:

- mouse
- touch
- pen
- trackpad

nếu platform cung cấp.

---

# 43. Gesture Engine

Baseline:

```text
tap
double_tap
long_press
drag
pan
scroll
pinch
```

Gesture recognizer không được block raw input.

---

# 44. Scroll Model

```text
ScrollView {
    content_size
    viewport_size
    offset
    velocity
}
```

Scrolling phải hỗ trợ:

- wheel
- touch
- keyboard
- scrollbar
- programmatic scrolling

---

# 45. Virtualized Controls

Các control lớn:

```text
ListView
TreeView
TableView
GridView
```

không tạo widget cho mọi item.

```text
1,000,000 items
       ↓
~50 visible item widgets
```

---

# 46. Virtualization

```text
Data Model
    ↓
Viewport
    ↓
Visible Range
    ↓
Widget Pool
    ↓
Render
```

Đây là architecture quan trọng cho IDE/file explorer.

---

# 47. Native Controls

Baseline:

```text
Button
CheckBox
RadioButton
Toggle
TextBox
PasswordBox
Label
Image
List
Tree
Table
ComboBox
Slider
ProgressBar
ScrollBar
TabView
Menu
MenuItem
Toolbar
Dialog
Tooltip
Splitter
StatusBar
```

---

# 48. TextBox

TextBox sử dụng `AXEDITOR` làm editing engine.

```text
TextBox
   ↓
AXEDITOR document
```

Nhờ đó:

- UTF-8
- undo
- selection
- IME
- multi-cursor capability

có thể dùng chung.

---

# 49. Rich Text

Baseline AXGUI hỗ trợ text runs:

```text
TextRun {
    text
    font
    size
    weight
    style
    decoration
}
```

Không xây một browser HTML engine.

---

# 50. Rich Text Boundary

Không mặc định hỗ trợ:

```text
HTML
CSS
JavaScript
DOM
```

Một rich text application có thể xây abstraction riêng trên AXGUI.

---

# 51. Font

```text
FontDescriptor {
    family
    size
    weight
    style
    stretch
}
```

Font fallback:

```text
primary
 ↓
fallback[]
 ↓
platform fallback
```

---

# 52. Text Layout

Text layout engine phải xử lý:

- shaping
- ligatures
- combining marks
- bidi
- fallback
- glyph metrics
- line breaking

AXGUI chỉ tiêu thụ text-layout API.

---

# 53. Theme

```text
Theme {
    colors
    typography
    spacing
    radii
    shadows
    control_metrics
    animations
}
```

Theme token:

```text
ColorToken
MetricToken
FontToken
DurationToken
```

---

# 54. Styling

Widget style:

```text
Style {
    background
    foreground
    border
    radius
    padding
    margin
    font
    opacity
}
```

State selectors:

```text
normal
hover
pressed
focused
disabled
selected
checked
```

---

# 55. Không Clone CSS

Axiom GUI không cần:

```text
selector engine
DOM
CSS cascade
browser layout
```

Styling phải:

- typed
- deterministic
- native
- nhanh

---

# 56. Theme Inheritance

Theme có thể kế thừa:

```text
Application
   ↓
Window
   ↓
Container
   ↓
Widget
```

nhưng resolved style phải cache được.

---

# 57. Animation

Animation model:

```text
Animation {
    property
    from
    to
    duration
    easing
}
```

Animation chỉ là presentation.

Không được ảnh hưởng semantic state.

---

# 58. Animation Scheduler

Animation sử dụng:

```text
AXTIME
```

và frame scheduling của compositor.

Không tạo timer/thread riêng cho mỗi animation.

---

# 59. Modal Dialog

```text
Dialog {
    owner
    modal
    content
    result
}
```

Modal dialog:

- tạo focus scope
- capture interaction
- có lifecycle rõ ràng

---

# 60. Popup

Popup layer tách khỏi normal widget clipping:

```text
Window
 ├── normal tree
 └── popup layer
       ├── tooltip
       ├── menu
       └── dropdown
```

---

# 61. Z-Order

AXGUI có layer:

```text
BACKGROUND
CONTENT
OVERLAY
POPUP
MODAL
SYSTEM_OVERLAY
```

OS-level overlays vẫn thuộc AXWINDOW/platform.

---

# 62. Accessibility

Accessibility không phải plugin phụ.

AXGUI xây semantic tree:

```text
Widget Tree
     ↓
Accessibility Tree
```

---

# 63. Accessibility Node

```text
AccessibleNode {
    id
    role
    name
    description
    value
    state
    actions[]
    bounds
    children[]
}
```

Roles:

```text
WINDOW
BUTTON
TEXT_FIELD
CHECKBOX
LIST
LIST_ITEM
TREE
TREE_ITEM
TABLE
TAB
MENU
MENU_ITEM
DIALOG
IMAGE
TEXT
```

---

# 64. Accessibility Actions

```text
invoke
focus
expand
collapse
select
set_value
scroll
```

Screen reader không cần biết implementation của widget.

---

# 65. Accessibility Events

```text
focus_changed
value_changed
selection_changed
structure_changed
state_changed
```

Chỉ phát event khi semantic state thực sự thay đổi.

---

# 66. Native Platform Accessibility

```text
AXGUI Accessibility Tree
          ↓
Platform Adapter
     ├── Windows
     ├── macOS/iOS
     ├── Android
     └── other
```

AXGUI không hard-code một accessibility API duy nhất.

---

# 67. Window Integration

AXGUI attach:

```text
GuiRoot
   ↓
AXWINDOW
```

AXWINDOW sở hữu:

- native window handle
- OS window state
- window size
- native lifecycle

AXGUI sở hữu:

- content UI

---

# 68. Window Events

AXWINDOW → AXGUI:

```text
resize
dpi_changed
display_changed
activation
deactivation
close_request
```

---

# 69. Application Event Loop

AXGUI không tạo event loop thứ hai.

```text
AXAPPLICATION
      ↓
event loop
      ↓
AXWINDOW
      ↓
AXINPUT
      ↓
AXGUI
```

---

# 70. Frame Lifecycle

Canonical frame:

```text
input
 ↓
events
 ↓
state updates
 ↓
layout
 ↓
animation
 ↓
render tree
 ↓
draw commands
 ↓
compositor
```

Không cho phép arbitrary reentrant rendering giữa các bước.

---

# 71. Frame Scheduling

UI có thể request:

```text
request_frame()
```

Nếu không có visual changes:

```text
no frame
```

tránh render loop vô ích.

---

# 72. State Update

Nhiều state changes trong cùng event batch có thể batch:

```text
event 1
event 2
event 3
    ↓
state commit
    ↓
single layout/render
```

---

# 73. Reactive Binding

AXGUI có typed binding:

```text
Binding<T> {
    get
    set?
    subscribe
}
```

Không bắt buộc một reactive framework nặng.

---

# 74. Observable State

```text
State<T>
```

có:

```text
read
write
subscribe
```

Widget có thể subscribe.

Thay đổi phải coalesce trước render.

---

# 75. Avoiding Global Reactivity

Không cho phép mọi state change trigger:

```text
whole application rebuild
```

Invalidation phải scoped:

```text
state
 ↓
affected widget
 ↓
affected layout subtree
 ↓
affected render region
```

---

# 76. UI Commands

```text
GuiCommand {
    id
    can_execute
    execute
}
```

Menu, toolbar, shortcut và context menu dùng chung command.

Ví dụ:

```text
file.save
edit.undo
edit.redo
view.toggle_sidebar
```

---

# 77. Keyboard Shortcuts

```text
Shortcut {
    key
    modifiers
    command
    scope
}
```

Scope:

```text
APPLICATION
WINDOW
PANEL
EDITOR
TEXT_INPUT
```

---

# 78. Shortcut Resolution

```text
most specific scope
       ↓
parent scope
       ↓
window
       ↓
application
```

Nếu conflict:

```text
specific scope wins
```

và resolution phải deterministic.

---

# 79. Menus

Menu item có thể bind command:

```text
MenuItem {
    command
    label
    shortcut
    icon
    checked
    enabled
}
```

State tự reflect command state.

---

# 80. Toolbars

Toolbar sử dụng cùng command system.

Không duplicate command implementation.

---

# 81. Context Menu

Context menu nhận:

```text
Context {
    widget
    selection
    coordinates
}
```

và sinh actions.

---

# 82. Resource Management

GUI resources:

```text
Image
Font
Texture
Brush
Path
Icon
Cursor
```

được cache theo identity.

---

# 83. Resource Cache

```text
ResourceCache {
    images
    textures
    fonts
    glyphs
    icons
}
```

LRU/size bounded.

---

# 84. GPU Resource Lifetime

CPU object:

```text
Image
```

không đồng nghĩa GPU resource.

```text
Image
 ↓
GPU texture cache
```

GPU resource được tạo/lifecycle bởi AXGRAPHICS.

---

# 85. Icon System

Native icon:

```text
Icon {
    source
    variants
    symbolic?
}
```

Hỗ trợ:

- vector
- raster
- symbolic
- DPI variants

---

# 86. High-DPI Rendering

Một icon 16 logical px trên scale 2:

```text
16 logical px
      ↓
32 device px
```

không được stretch bitmap 16px nếu có vector source.

---

# 87. Localization

AXGUI text không hard-code.

```text
LocalizedString {
    key
    arguments[]
}
```

AXAPPLICATION/configuration cung cấp locale.

---

# 88. Right-to-Left UI

Layout hỗ trợ:

```text
LTR
RTL
AUTO
```

Direction ảnh hưởng:

- horizontal layout
- text alignment
- navigation
- scrollbar placement

---

# 89. GUI State Serialization

GUI state có thể serialize:

```text
GuiState {
    widget_states
    selected_items
    expanded_nodes
    splitter_positions
    scroll_positions
}
```

Không serialize raw pointers.

---

# 90. Hot Reload Boundary

Development mode có thể hỗ trợ:

```text
reload theme
reload resources
reload UI configuration
```

Nhưng code hot reload không phải AXGUI core requirement.

---

# 91. Testing

AXTEST phải test:

### Layout

```text
measure
arrange
constraints
DPI
RTL
```

### Input

```text
hit test
focus
capture
keyboard
IME
gesture
```

### Rendering

```text
render tree
dirty region
clipping
z-order
DPI
```

### Accessibility

```text
tree
roles
actions
events
```

---

# 92. Headless GUI Testing

AXGUI phải chạy với:

```text
headless renderer
```

để test:

```text
Widget Tree
Layout Tree
Accessibility Tree
RenderModel
```

không cần display.

---

# 93. Golden Rendering Tests

Có thể render:

```text
Widget Tree
 ↓
software renderer
 ↓
canonical image
```

và compare.

Platform-specific raster differences phải được canonicalize hoặc dùng structural RenderModel tests.

---

# 94. Fuzzing

Fuzz:

```text
layout trees
style trees
input events
focus transitions
widget destruction
popup nesting
IME sequences
DPI changes
window resize
accessibility actions
```

Không được crash.

---

# 95. Lifecycle Fuzzing

Đặc biệt:

```text
create widget
attach
focus
remove
destroy
event arrives
```

phải không tạo use-after-free.

Widget IDs và generation IDs giúp phát hiện stale handles.

---

# 96. Resource Exhaustion

Giới hạn:

```text
max widgets
max depth
max render commands
max texture memory
max layout iterations
max animation count
max accessibility nodes
```

---

# 97. Layout Loop Protection

Một layout không được:

```text
measure
 → state mutation
 → measure
 → state mutation
 → ...
```

vô hạn.

Mỗi frame có layout iteration budget.

Nếu vượt:

```text
GUI_LAYOUT_CYCLE
```

và giữ state an toàn.

---

# 98. Threading

Baseline:

```text
UI state mutation:
    UI thread

snapshot/read-only data:
    concurrent

asset decoding:
    background

text shaping:
    background-capable

render preparation:
    parallelizable

GPU submission:
    graphics context thread
```

Không cho arbitrary widget mutation từ background thread.

---

# 99. Cross-Thread UI Mutation

Background code phải gửi:

```text
UiTask
```

vào UI scheduler.

Không:

```text
background → widget.field = ...
```

---

# 100. UI Task

```text
UiTask {
    id
    priority
    callback
    cancellation
}
```

Scheduler tích hợp `AXAPPLICATION`.

---

# 101. Performance Goals

Mục tiêu baseline:

```text
input dispatch             < 1 ms target
simple state update        < 1 ms
small layout               < 2 ms
visible render preparation < 4 ms
```

Để giữ 60 FPS:

```text
frame budget ≈ 16.67 ms
```

AXGUI phải tránh dùng toàn bộ budget nếu UI đơn giản.

---

# 102. Large UI Tree

Một UI có hàng chục nghìn logical widgets không được khiến mỗi frame:

```text
visit every widget
layout every widget
render every widget
```

Phải có:

```text
subtree invalidation
layout caching
visibility culling
render caching
virtualization
```

---

# 103. Render Cache

Widget subtree có thể cache khi:

```text
state unchanged
geometry unchanged
resources unchanged
```

Cache có thể là:

```text
RenderNode
GPU texture
draw command list
```

tùy renderer.

---

# 104. Cache Invalidation

Key:

```text
widget_state_hash
geometry_hash
style_hash
resource_hash
renderer_version
```

Không cache dựa chỉ trên WidgetId.

---

# 105. No Hidden Runtime

AXGUI không được âm thầm tạo:

- thread cho từng widget
- heap allocation cho từng event
- reference counting cycle
- GC object graph
- background timer cho từng animation

Các resource phải pooled/batched khi có thể.

---

# 106. Memory Strategy

Ưu tiên:

```text
arena
pool
small-vector
interned strings
struct-of-arrays cho large control collections
object pooling cho transient events
```

Widget nhỏ có thể inline storage.

---

# 107. Event Allocation

Input event trên hot path không nên heap allocate.

Baseline:

```text
stack/value event
```

hoặc pool.

---

# 108. Widget Allocation

Widget lifetime dài có thể heap allocate.

Nhưng:

```text
children[]
```

phải dùng compact storage.

Không dùng linked list cho widget children mặc định.

---

# 109. Accessibility Performance

Accessibility tree có thể được cached.

Chỉ update affected subtree:

```text
Widget changed
 ↓
AccessibleNode changed
 ↓
notify platform
```

---

# 110. Security

AXGUI phải coi:

- image files
- font files
- clipboard
- drag/drop
- remote UI data
- accessibility requests
- plugins

là potentially untrusted.

---

# 111. Malformed Resources

Image/font decoder vượt giới hạn:

```text
GUI_RESOURCE_INVALID
GUI_RESOURCE_LIMIT
```

không crash application.

---

# 112. Drag & Drop Security

Dropped file path chỉ là data.

Không tự động:

```text
execute
open process
run script
```

---

# 113. Plugin Boundary

Plugin UI:

```text
AXGUI Extension
      ↓
Widget capability
```

Extension không mặc định có:

```text
filesystem
network
process
credentials
```

---

# 114. Native GUI Plugin ABI

```text
AXGUI_EXTENSION_ABI_1
```

Plugin khai báo:

```text
name
version
abi
capabilities
dependencies
```

---

# 115. Native API — Lifecycle

```text
gui_create()
gui_destroy()

gui_window_attach()
gui_window_detach()

gui_frame_begin()
gui_frame_end()
```

---

# 116. Widget API

```text
gui_widget_create()
gui_widget_destroy()

gui_widget_attach()
gui_widget_detach()

gui_widget_add_child()
gui_widget_remove_child()

gui_widget_set_visible()
gui_widget_set_enabled()
gui_widget_set_style()
```

---

# 117. Layout API

```text
gui_measure()
gui_arrange()

gui_layout_invalidate()
gui_layout_recompute()

gui_get_bounds()
gui_get_content_bounds()
```

---

# 118. Event API

```text
gui_event_dispatch()
gui_event_capture()
gui_event_release()

gui_focus_set()
gui_focus_get()
gui_focus_next()
gui_focus_previous()
```

---

# 119. Rendering API

```text
gui_render()
gui_render_model()

gui_invalidate()
gui_invalidate_rect()

gui_hit_test()
```

---

# 120. Theme API

```text
gui_theme_load()
gui_theme_set()
gui_theme_get()

gui_style_resolve()
gui_style_invalidate()
```

---

# 121. Accessibility API

```text
gui_accessibility_tree()
gui_accessibility_node()
gui_accessibility_action()
gui_accessibility_notify()
```

---

# 122. Resource API

```text
gui_image_load()
gui_image_release()

gui_font_load()
gui_font_release()

gui_icon_load()
gui_icon_release()
```

---

# 123. Command API

```text
gui_command_register()
gui_command_unregister()

gui_command_execute()
gui_command_can_execute()

gui_shortcut_register()
gui_shortcut_unregister()
```

---

# 124. Dialog API

```text
gui_dialog_create()
gui_dialog_show()
gui_dialog_close()
gui_dialog_result()
```

---

# 125. Scroll API

```text
gui_scroll_set()
gui_scroll_by()
gui_scroll_to()
gui_scroll_get()
```

---

# 126. Virtualization API

```text
gui_virtual_list_create()
gui_virtual_list_set_model()
gui_virtual_list_set_viewport()
gui_virtual_list_visible_range()
```

---

# 127. Error Model

```text id="m8j2xq"
GUI_INVALID_WIDGET
GUI_INVALID_PARENT
GUI_INVALID_STATE
GUI_LAYOUT_FAILED
GUI_LAYOUT_CYCLE
GUI_EVENT_REJECTED
GUI_FOCUS_FAILED
GUI_RENDER_FAILED
GUI_RESOURCE_INVALID
GUI_RESOURCE_LIMIT
GUI_THEME_INVALID
GUI_ACCESSIBILITY_FAILED
GUI_WINDOW_INVALID
GUI_THREAD_VIOLATION
GUI_RESOURCE_NOT_FOUND
GUI_EXTENSION_DENIED
GUI_PERMISSION_DENIED
GUI_UNSUPPORTED_FEATURE
```

---

# 128. ABI Ownership

`AXGUI_ABI_1` phải định nghĩa:

- WidgetHandle ownership
- WidgetId lifetime
- event lifetime
- render-model lifetime
- resource ownership
- callback ABI
- thread affinity
- allocator boundary
- error handling

Public API không expose internal tree implementation.

---

# 129. Handle Generation

Để tránh stale handles:

```text
WidgetHandle {
    index
    generation
}
```

Widget destroy:

```text
generation++
```

Handle cũ sẽ fail validation.

---

# 130. Callback Safety

Không gọi user callback khi đang giữ internal tree mutation lock.

```text
mutate
 ↓
release internal lock
 ↓
callback
```

Nếu callback yêu cầu mutation mới:

```text
queue
 ↓
next safe mutation point
```

---

# 131. Determinism

Với cùng:

```text
widget tree
style
input sequence
window geometry
DPI
theme
```

AXGUI phải tạo cùng:

```text
layout
focus transitions
render model
accessibility structure
```

trừ renderer-specific floating-point differences được xác định rõ.

---

# 132. GUI State Machine

Frame:

```text
IDLE
 ↓
INPUT
 ↓
UPDATE
 ↓
LAYOUT
 ↓
RENDER_PREPARE
 ↓
RENDER
 ↓
PRESENT
 ↓
IDLE
```

Không được bỏ qua validation khi state transition.

---

# 133. Exception/Failure Isolation

Một widget handler lỗi không được corrupt toàn bộ UI tree.

Có thể:

```text
handler failure
 ↓
error boundary
 ↓
disable/fail widget operation
 ↓
report diagnostic
```

Cơ chế panic/error semantics cụ thể dùng AXRUNTIME.

---

# 134. AXIDE Integration

AXIDE xây UI bằng AXGUI:

```text
AXIDE CORE
    ↓
AXIDE SHELL
    ↓
AXGUI
    ├── AXEDITOR
    ├── TreeView
    ├── Terminal
    ├── Problems
    ├── Debug
    └── Documentation
```

AXGUI không biết IDE semantics.

---

# 135. AXEDITOR Integration

```text
AXGUI TextBox/CodeEditor
          ↓
       AXEDITOR
          ↓
       AXIDE
```

Editor rendering model được embed vào GUI render tree.

---

# 136. AXWINDOW Integration

```text
AXGUI
  ↓
GuiRoot
  ↓
AXWINDOW
```

Một `GuiRoot` tương ứng với content root của một native window.

---

# 137. AXCOMPOSITOR Integration

AXGUI tạo render commands.

AXCOMPOSITOR chịu:

- surface composition
- window composition
- presentation timing

AXGUI không tự compose windows.

---

# 138. AXGRAPHICS Integration

AXGUI sử dụng:

```text
buffers
textures
fonts/glyph resources
pipelines
draw commands
```

từ AXGRAPHICS.

---

# 139. Mobile Boundary

iOS/Android có platform lifecycle đặc biệt.

AXGUI không giả định desktop window.

```text
AXAPPLICATION
 ↓
platform lifecycle
 ↓
AXGUI surface
```

Controls vẫn dùng cùng semantic model.

---

# 140. WASM Boundary

WASM hosted GUI có thể:

```text
AXGUI
 ↓
host surface adapter
```

AXGUI không yêu cầu native OS window.

---

# 141. Testing Matrix

Phải test:

```text
Windows x86_64
Windows AArch64

Linux x86_64
Linux AArch64

macOS x86_64
macOS AArch64

iOS
Android

WASM hosted
headless
software renderer
GPU renderer
```

---

# 142. Conformance Categories

```text
GUI-CONFORMANCE
LAYOUT-CONFORMANCE
INPUT-CONFORMANCE
FOCUS-CONFORMANCE
TEXT-CONFORMANCE
ACCESSIBILITY-CONFORMANCE
RENDER-CONFORMANCE
DPI-CONFORMANCE
RESOURCE-CONFORMANCE
SECURITY-CONFORMANCE
PERFORMANCE-CONFORMANCE
```

---

# 143. 40 Invariants

### GUI-INV-01
AXGUI không sở hữu native window lifecycle.

### GUI-INV-02
AXGUI không sở hữu compiler semantics.

### GUI-INV-03
Widget identity dùng stable WidgetId/handle.

### GUI-INV-04
Stale widget handle phải bị phát hiện.

### GUI-INV-05
Widget tree không được chứa dangling child.

### GUI-INV-06
Widget lifecycle phải deterministic.

### GUI-INV-07
Measure và arrange là hai phase riêng.

### GUI-INV-08
Child không tự ý mutate parent geometry.

### GUI-INV-09
Logical coordinates là canonical GUI coordinates.

### GUI-INV-10
DPI scaling không làm thay đổi logical layout semantics.

### GUI-INV-11
UI không được layout toàn bộ tree nếu không cần.

### GUI-INV-12
Invisible subtrees không được render.

### GUI-INV-13
Dirty region phải giới hạn rendering khi có thể.

### GUI-INV-14
Render tree không được mutate widget semantic state.

### GUI-INV-15
Widget không trực tiếp sở hữu compositor.

### GUI-INV-16
Widget không trực tiếp điều khiển physical input device.

### GUI-INV-17
Input propagation phải deterministic.

### GUI-INV-18
Pointer capture phải được release khi owner bị destroy.

### GUI-INV-19
Mỗi window chỉ có một logical keyboard focus.

### GUI-INV-20
Modal focus scope không được để focus thoát ngoài scope.

### GUI-INV-21
Text input phải hỗ trợ IME boundary.

### GUI-INV-22
Text input không được suy ra đơn giản từ physical key events.

### GUI-INV-23
Accessibility tree phải phản ánh semantic widget state.

### GUI-INV-24
Accessibility không phải optional requirement đối với core controls.

### GUI-INV-25
Virtualized controls không tạo widget cho toàn bộ dataset.

### GUI-INV-26
Style resolution phải deterministic.

### GUI-INV-27
Theme không được mutate source/application semantic state.

### GUI-INV-28
Animation không được thay đổi semantic state ngoài explicit application logic.

### GUI-INV-29
Background thread không được trực tiếp mutate widget state.

### GUI-INV-30
UI callbacks không chạy dưới internal mutation lock.

### GUI-INV-31
Một handler failure không được corrupt widget tree.

### GUI-INV-32
Resource decoding phải resource-bounded.

### GUI-INV-33
Clipboard/drag-drop data không được tự động execute.

### GUI-INV-34
Extension capabilities phải explicit.

### GUI-INV-35
GUI không yêu cầu third-party UI framework.

### GUI-INV-36
Headless mode phải tồn tại để testing/automation.

### GUI-INV-37
Layout cycles phải được phát hiện và giới hạn.

### GUI-INV-38
Render resources phải có ownership/lifetime rõ ràng.

### GUI-INV-39
`AXGUI_ABI_1` phải versioned và stable.

### GUI-INV-40
AXGUI phải có khả năng self-host bằng Axiom.

---

# 144. Definition of Done

`BOOTSTRAP-786` hoàn thành khi có:

- [x] native widget tree
- [x] retained UI semantic model
- [x] immediate-style render API
- [x] layout engine
- [x] measure/arrange
- [x] row/column/grid/flex/overlay
- [x] DPI scaling
- [x] multi-display support
- [x] render tree
- [x] draw command abstraction
- [x] GPU/software rendering boundary
- [x] dirty-region rendering
- [x] render caching
- [x] event propagation
- [x] capture/target/bubble
- [x] hit testing
- [x] pointer capture
- [x] keyboard focus
- [x] focus scopes
- [x] keyboard navigation
- [x] Unicode text input
- [x] IME
- [x] pointer/touch/pen abstraction
- [x] gestures
- [x] scrolling
- [x] virtualization
- [x] native controls
- [x] AXEDITOR TextBox integration
- [x] rich text primitives
- [x] font/text layout boundary
- [x] theme
- [x] styling
- [x] localization
- [x] RTL
- [x] animation
- [x] dialogs
- [x] popup layer
- [x] menus
- [x] toolbar
- [x] command system
- [x] shortcuts
- [x] accessibility tree
- [x] platform accessibility boundary
- [x] session/UI state
- [x] headless mode
- [x] testing renderer
- [x] fuzzing
- [x] resource limits
- [x] plugin capability boundary
- [x] threading model
- [x] deterministic frame model
- [x] `AXGUI_ABI_1`
- [x] 40 invariants
- [x] AXTEST conformance suite
- [x] native bootstrap path
- [x] self-hosting target

**AXGUI 5.0 được đóng băng.**

---

# 145. Vị trí mới của stack

Axiom hiện có một tầng UI hoàn chỉnh:

```text
                    APPLICATION
                         │
                    AXAPPLICATION
                         │
              ┌──────────▼──────────┐
              │        AXGUI        │
              │                     │
              │ Widget / Layout     │
              │ Input / Focus       │
              │ Theme / Style       │
              │ Accessibility       │
              │ Rendering           │
              └───────┬─────┬───────┘
                      │     │
                 AXEDITOR   │
                      │     │
                   AXIDE    │
                            │
                     AXWINDOW
                            │
                     AXCOMPOSITOR
                            │
                       AXDISPLAY
```

Điểm quan trọng là Axiom giờ **không cần biến IDE thành một ứng dụng đặc biệt**. `AXIDE` có thể được xây như một application native thông thường sử dụng `AXGUI + AXEDITOR`.

---

# BOOTSTRAP-787 — AXWIDGETS

**Native Axiom Standard Widget Library, Desktop Controls, Forms, Navigation, Lists, Trees, Tables, Tabs, Menus, Dialogs, Toolbars, Status Bars, Data Binding, Virtualized Collections, Command Surfaces, Native Interaction Patterns & Accessible Control Runtime 5.0**

Bước tiếp theo sẽ xây **bộ controls thực sự** trên `AXGUI`:

```text
AXGUI
  │
  ▼
AXWIDGETS
  ├── Button
  ├── TextBox
  ├── CheckBox
  ├── ComboBox
  ├── ListView
  ├── TreeView
  ├── TableView
  ├── TabView
  ├── Menu
  ├── Dialog
  ├── Toolbar
  ├── StatusBar
  ├── Form
  └── Navigation
       │
       ▼
    AXIDE / Applications
```

`AXGUI` cung cấp **framework**; `AXWIDGETS` sẽ cung cấp **control library chuẩn** để tránh mỗi ứng dụng phải tự xây lại các control cơ bản.