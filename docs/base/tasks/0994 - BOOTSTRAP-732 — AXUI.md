# BOOTSTRAP-732 — AXUI

**Namespace:** `AXUI`  
**Phase:** Axiom Civilization Runtime / Native User Interface Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXGRAPHICS`, `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXMEDIA`, `AXSECURITY`, `AXIDENTITY`, `AXGEOSPATIAL`

> `AXUI` là UI substrate native của Axiom. Nó cung cấp window, input, layout, controls, text, accessibility, event routing, styling, animation, desktop/mobile UI và UI composition. `AXUI` không phải business application framework.

---

# 732.0 — Mục tiêu

AXUI phải cho phép xây:

```text
desktop applications
mobile applications
tablet applications
embedded UI
developer tools
IDE
CAD
scientific visualization
media editor
games/tools UI
administrative applications
```

với một core thống nhất:

```text
Input
  ↓
Event
  ↓
UI Tree
  ↓
State
  ↓
Layout
  ↓
Render Graph
  ↓
AXGRAPHICS
  ↓
Display
```

Không bắt buộc application phải dùng:

```text
reflection
garbage collection
virtual widget hierarchy
runtime serialization
```

trên hot path.

---

# 732.1 — UI Boundary

`AXUI` sở hữu:

```text
application shell
window
surface
view
widget
control
layout
event
input
focus
selection
text editing
styling
theme
animation
accessibility
clipboard
drag/drop
menu
dialog
notification
UI state
data binding
UI virtualization
UI rendering
```

Không sở hữu:

```text
GPU primitives          → AXGRAPHICS
persistent data         → AXSTORAGE / AXDATABASE
network transport       → AXNETWORK
identity authority      → AXIDENTITY
security authority      → AXSECURITY
media codecs            → AXMEDIA
business semantics      → application layer
```

---

# 732.2 — Application

```axiom
ui_application {
    id
    windows
    resources
    theme
    locale
}
```

Lifecycle:

```text
CREATED
INITIALIZING
RUNNING
SUSPENDING
SUSPENDED
RESUMING
CLOSING
CLOSED
```

---

# 732.3 — Application Shell

Shell quản lý:

```text
main window
application menu
global commands
notifications
lifecycle
input routing
clipboard
accessibility root
```

---

# 732.4 — Window

```axiom
ui_window {
    window_id
    title
    bounds
    state
    root_view
}
```

Window state:

```text
NORMAL
MINIMIZED
MAXIMIZED
FULLSCREEN
HIDDEN
```

---

# 732.5 — Window Surface

Window có rendering surface:

```axiom
ui_surface {
    graphics_surface
    scale_factor
    color_space
}
```

Liên kết:

```text
AXUI
 ↓
AXGRAPHICS display_surface
```

---

# 732.6 — Window Manager Boundary

AXUI không giả định một OS window manager cụ thể.

Backend có thể cung cấp:

```text
Windows
Linux
macOS
Android
iOS
embedded
headless
```

---

# 732.7 — UI Node

Core semantic unit:

```axiom
ui_node {
    id
    parent
    children
    layout
    style
    state
}
```

---

# 732.8 — Visual Tree

```text
Window
 └── Root
      ├── Header
      │    ├── Logo
      │    └── Menu
      └── Content
           ├── Sidebar
           └── Main
```

Visual tree phục vụ:

```text
layout
rendering
hit testing
accessibility
event propagation
```

---

# 732.9 — Logical Tree

Logical relationships có thể khác visual tree.

Ví dụ:

```text
ComboBox
 ├── logical control
 ├── popup
 └── popup items
```

Logical tree phục vụ semantic relationships.

---

# 732.10 — Widget

```axiom
widget<T> {
    state
    properties
    children
}
```

Widget không nhất thiết là class.

Phù hợp với triết lý Axiom:

```text
struct + functions
```

---

# 732.11 — Control

Control là widget có interaction semantics.

Ví dụ:

```text
button
checkbox
radio
slider
text_input
list
tree
table
tab
menu
```

---

# 732.12 — View

View là container/rendering surface có thể compose UI.

```axiom
view {
    children
    layout
}
```

---

# 732.13 — Declarative UI

Axiom hỗ trợ declarative syntax:

```axiom
ui MainWindow {
    Column {
        Text("Hello")
        Button("Run") {
            on_click = run_program
        }
    }
}
```

Compiler có thể transform thành native UI tree construction.

---

# 732.14 — Imperative UI

Vẫn hỗ trợ:

```axiom
let button = Button()
button.text = "Run"
window.content = button
```

Hai model dùng chung runtime.

---

# 732.15 — UI State

```axiom
ui_state<T> {
    value
}
```

State mutation phải đi qua explicit update semantics.

---

# 732.16 — Reactive State

```axiom
state count = 0

Button("Increment") {
    on_click = {
        count += 1
    }
}

Text(bind count)
```

Runtime chỉ invalidate phần UI phụ thuộc state.

---

# 732.17 — Dependency Tracking

Dependency graph:

```text
state A
 ├── Text1
 └── Panel3

state B
 └── Button2
```

Thay đổi A không cần rebuild toàn bộ UI.

---

# 732.18 — UI Invalidation

Node có thể dirty:

```text
LAYOUT_DIRTY
PAINT_DIRTY
STYLE_DIRTY
CHILDREN_DIRTY
ACCESSIBILITY_DIRTY
```

---

# 732.19 — Layout

Layout pipeline:

```text
measure
 ↓
arrange
 ↓
paint
```

---

# 732.20 — Measure

```axiom
measure(
    available_size
) -> desired_size
```

---

# 732.21 — Arrange

```axiom
arrange(
    final_rect
)
```

---

# 732.22 — Layout Constraints

```axiom
size_constraints {
    min
    preferred
    max
}
```

---

# 732.23 — Layout Models

Core:

```text
absolute
stack
row
column
grid
flex
overlay
anchor
```

---

# 732.24 — Flex Layout

```axiom
Row {
    width = fill
    gap = 8

    Button("A")
    Button("B")
}
```

Có:

```text
grow
shrink
basis
alignment
gap
```

---

# 732.25 — Grid

```axiom
Grid {
    columns = [1fr, 2fr]
    rows = [auto, 1fr]
}
```

---

# 732.26 — Overlay

Cho phép:

```text
content
+
popup
+
tooltip
+
overlay
```

---

# 732.27 — Coordinate Systems

UI có:

```text
screen coordinates
window coordinates
local coordinates
content coordinates
scroll coordinates
```

Transform phải explicit.

---

# 732.28 — DPI / Scaling

```axiom
ui_scale {
    logical_dpi
    physical_dpi
    scale_factor
}
```

UI layout ưu tiên logical units.

---

# 732.29 — High DPI

Runtime phải hỗ trợ:

```text
100%
125%
150%
200%
custom scaling
```

và không giả định pixel = logical unit.

---

# 732.30 — Hit Testing

```axiom
hit_test(point) -> ui_node?
```

Có thể xét:

```text
bounds
clip
transform
visibility
input_enabled
z_order
```

---

# 732.31 — Pointer

```axiom
pointer_event {
    pointer_id
    position
    buttons
    modifiers
    timestamp
}
```

---

# 732.32 — Mouse

```text
move
down
up
wheel
enter
leave
```

---

# 732.33 — Touch

```axiom
touch_event {
    id
    position
    pressure
    phase
}
```

Phases:

```text
BEGAN
MOVED
ENDED
CANCELLED
```

---

# 732.34 — Pen

```axiom
pen_event {
    position
    pressure
    tilt
    azimuth
    buttons
}
```

---

# 732.35 — Keyboard

```axiom
key_event {
    key
    scan_code
    modifiers
    repeat
    phase
}
```

Phân biệt:

```text
physical key
logical key
text input
```

---

# 732.36 — Text Input

IME composition phải là semantic riêng:

```text
composition_start
composition_update
composition_commit
composition_cancel
```

Điều này cần cho:

```text
Vietnamese
Chinese
Japanese
Korean
```

và các hệ chữ có IME.

---

# 732.37 — Input Method

```axiom
text_input_session {
    locale
    surrounding_text
    selection
    composition
}
```

---

# 732.38 — Gamepad

```axiom
gamepad_event {
    device
    buttons
    axes
}
```

---

# 732.39 — Input Device Abstraction

Input device:

```axiom
input_device {
    id
    type
    capabilities
}
```

Không hard-code mouse/keyboard là thiết bị duy nhất.

---

# 732.40 — Event

```axiom
ui_event {
    type
    target
    timestamp
}
```

---

# 732.41 — Event Routing

Event flow:

```text
input
 ↓
hit test
 ↓
target
 ↓
capture phase
 ↓
target phase
 ↓
bubble phase
```

---

# 732.42 — Capture

Parent hoặc node có thể capture pointer:

```axiom
capture_pointer(pointer_id)
```

Cần cho:

```text
drag
resize
slider
drawing
```

---

# 732.43 — Event Cancellation

```axiom
event.stop_propagation()
event.prevent_default()
```

---

# 732.44 — Focus

```axiom
focus_manager {
    focused_node
}
```

---

# 732.45 — Focus Scope

Dialog/menu/popup có thể tạo:

```text
focus scope
```

Focus không tự động thoát khỏi scope khi modal interaction đang hoạt động.

---

# 732.46 — Keyboard Navigation

Core navigation:

```text
Tab
Shift+Tab
Arrow keys
Enter
Escape
```

Navigation graph có thể explicit.

---

# 732.47 — Focus Order

```axiom
focus_order {
    node
    order
}
```

Không dựa hoàn toàn vào visual tree order.

---

# 732.48 — Selection

Core abstraction:

```axiom
selection<T> {
    selected
    anchor
    extent
}
```

Hỗ trợ:

```text
single
multiple
range
```

---

# 732.49 — Text Selection

```axiom
text_selection {
    anchor
    caret
}
```

---

# 732.50 — Clipboard

```axiom
clipboard {
    formats
}
```

Formats:

```text
text
html
image
files
custom
```

---

# 732.51 — Drag and Drop

```axiom
drag_session {
    source
    data
    allowed_operations
}
```

Operations:

```text
COPY
MOVE
LINK
```

---

# 732.52 — Context Menu

```axiom
context_menu {
    items
    commands
}
```

---

# 732.53 — Menu

```axiom
menu {
    items
}
```

Item types:

```text
command
checkbox
radio
separator
submenu
```

---

# 732.54 — Command

Command là abstraction dùng chung:

```axiom
ui_command {
    id
    execute
    can_execute
    shortcut
}
```

Cho phép:

```text
button
menu
toolbar
keyboard shortcut
```

cùng invoke một command.

---

# 732.55 — Command State

```text
enabled
disabled
checked
visible
```

---

# 732.56 — Shortcut

```axiom
shortcut {
    keys
    modifiers
    command
}
```

---

# 732.57 — Dialog

```axiom
dialog {
    content
    buttons
    modality
}
```

Modality:

```text
modeless
window_modal
application_modal
```

---

# 732.58 — Popup

Popup có:

```text
anchor
placement
dismiss policy
focus policy
```

---

# 732.59 — Tooltip

```axiom
tooltip {
    content
    delay
    duration
}
```

---

# 732.60 — Notification

```axiom
notification {
    title
    body
    severity
    actions
}
```

AXUI không quyết định business meaning của notification.

---

# 732.61 — Styling

Style:

```axiom
style {
    selector
    properties
}
```

Ví dụ:

```axiom
Button {
    background = theme.primary
    radius = 6
}
```

---

# 732.62 — Selector

Có thể select theo:

```text
type
id
class
state
ancestor
attribute
```

---

# 732.63 — Pseudo States

```text
:hover
:pressed
:focused
:disabled
:checked
:selected
:active
```

---

# 732.64 — Theme

```axiom
theme {
    colors
    typography
    spacing
    shapes
    controls
}
```

---

# 732.65 — Design Tokens

```axiom
theme.primary
theme.surface
theme.text
theme.border
theme.spacing.medium
theme.radius.medium
```

Tokens có thể được compile thành constants.

---

# 732.66 — Dynamic Theme

Có thể thay theme runtime:

```axiom
application.theme = dark_theme
```

Runtime chỉ invalidate affected nodes.

---

# 732.67 — Accessibility Tree

Accessibility tree khác visual tree khi cần.

```axiom
accessibility_node {
    role
    name
    description
    value
    state
    actions
}
```

---

# 732.68 — Accessibility Roles

Ví dụ:

```text
window
button
checkbox
textbox
slider
list
list_item
tree
tree_item
table
row
cell
image
heading
link
dialog
```

---

# 732.69 — Accessibility Actions

```text
activate
expand
collapse
select
set_value
increment
decrement
scroll
```

---

# 732.70 — Accessibility Properties

```text
label
description
state
value
range
position
```

---

# 732.71 — Screen Reader

AXUI cung cấp semantic tree cho platform accessibility API.

Không hard-code screen reader engine.

---

# 732.72 — Keyboard Accessibility

Mọi interactive control phải có khả năng expose keyboard semantics nếu platform hỗ trợ.

---

# 732.73 — Reduced Motion

Theme/accessibility preference:

```axiom
accessibility.reduced_motion
```

Animation system phải tôn trọng preference.

---

# 732.74 — High Contrast

```axiom
accessibility.high_contrast
```

Theme có thể chuyển sang high-contrast variant.

---

# 732.75 — Text Rendering

AXUI sử dụng:

→ `AXGRAPHICS`

cho:

```text
glyph rendering
text textures
vector glyph
GPU compositing
```

Nhưng text layout semantics thuộc AXUI/text subsystem.

---

# 732.76 — Text Layout

Hỗ trợ:

```text
Unicode
grapheme clusters
bidirectional text
RTL
line breaking
word wrapping
font fallback
shaping
```

---

# 732.77 — Unicode

UI strings mặc định:

```text
UTF-8
```

Internal text representation có thể tối ưu theo workload nhưng API semantics là Unicode.

---

# 732.78 — Font Fallback

```axiom
font_fallback {
    primary
    fallback_chain
}
```

Ví dụ:

```text
Latin
→ Vietnamese
→ CJK
→ Emoji
```

---

# 732.79 — Text Editing

Core operations:

```text
insert
delete
replace
select
copy
paste
undo
redo
```

---

# 732.80 — Undo/Redo

```axiom
undo_manager {
    history
    undo()
    redo()
}
```

Có thể group operations:

```text
begin_group()
end_group()
```

---

# 732.81 — Rich Text

```axiom
rich_text {
    spans
    attributes
}
```

Attributes:

```text
font
size
weight
style
color
underline
link
```

---

# 732.82 — Layout Virtualization

Large lists không tạo toàn bộ node.

```text
1000000 items
        ↓
viewport
        ↓
visible items only
```

---

# 732.83 — Virtual List

```axiom
virtual_list<T> {
    source
    item_builder
}
```

---

# 732.84 — Virtual Grid

```axiom
virtual_grid<T> {
    source
    columns
    item_builder
}
```

---

# 732.85 — Tree Virtualization

Tree lớn phải hỗ trợ lazy/virtual children.

---

# 732.86 — Data Binding

```axiom
bind(
    control.property,
    model.field
)
```

Binding phải explicit.

---

# 732.87 — Binding Direction

```text
one_way
two_way
one_time
command
```

---

# 732.88 — Validation

UI validation có thể báo:

```text
required
format
range
constraint
```

Nhưng:

```text
UI validation ≠ domain authority
```

---

# 732.89 — Form

```axiom
form {
    fields
    validation
    submit
}
```

---

# 732.90 — Async UI

UI thread không được block bởi:

```text
network
database
file IO
GPU wait
long compute
```

---

# 732.91 — UI Task

```axiom
ui_task<T> {
    start
    await
    resume_on_ui
}
```

---

# 732.92 — UI Thread Affinity

Một số UI objects có:

```text
UI-thread affinity
```

Nhưng immutable/render data có thể được prepare ngoài UI thread.

---

# 732.93 — Background Work

Pattern:

```text
UI
 ↓
AXCOMPUTE / worker
 ↓
result
 ↓
UI state update
```

---

# 732.94 — Render Integration

Pipeline:

```text
UI tree
 ↓
layout
 ↓
paint commands
 ↓
render graph
 ↓
AXGRAPHICS
```

---

# 732.95 — Retained Rendering

UI giữ:

```text
visual tree
layout state
paint state
```

và chỉ redraw vùng cần thiết.

---

# 732.96 — Immediate Rendering

Cho use cases:

```text
plot
canvas
game HUD
debugger
custom editor
```

API:

```axiom
canvas {
    draw_rect(...)
    draw_path(...)
    draw_text(...)
}
```

---

# 732.97 — Hybrid Rendering

Một application có thể kết hợp:

```text
retained widgets
+
immediate canvas
+
3D viewport
```

---

# 732.98 — Clipping

```axiom
clip {
    rect
    rounded_rect
    path
}
```

Clip được compile vào graphics render graph.

---

# 732.99 — Scrolling

```axiom
scroll_view {
    content
    offset
    viewport
}
```

Hỗ trợ:

```text
horizontal
vertical
both
```

---

# 732.100 — Scroll Virtualization

Scroll container phải có thể kết hợp:

```text
virtual list
virtual grid
lazy content
```

---

# 732.101 — UI Animation

```axiom
ui_animation<T> {
    from
    to
    duration
    easing
}
```

---

# 732.102 — Easing

```text
linear
ease_in
ease_out
ease_in_out
cubic
spring
steps
custom
```

---

# 732.103 — Animation Clock

Animation sử dụng:

```text
monotonic clock
```

không phụ thuộc wall clock.

---

# 732.104 — Transition

```axiom
transition {
    property
    duration
    easing
}
```

---

# 732.105 — Layout Animation

Có thể animate:

```text
position
size
opacity
transform
```

Nhưng layout recalculation phải được kiểm soát để tránh frame-time explosion.

---

# 732.106 — Compositing

UI layer:

```text
background
content
overlay
popup
tooltip
cursor
```

có thể được compositor xử lý độc lập.

---

# 732.107 — Opacity

```axiom
opacity: f32
```

Compositing phải sử dụng explicit alpha semantics.

---

# 732.108 — Transform

UI hỗ trợ:

```text
translate
scale
rotate
matrix
```

---

# 732.109 — 3D Viewport

AXUI có control:

```axiom
viewport3d {
    scene
    camera
    renderer
}
```

Semantics 3D thuộc AXGRAPHICS.

---

# 732.110 — Media View

AXMEDIA frame có thể hiển thị:

```axiom
media_view {
    source
    fit
    playback
}
```

---

# 732.111 — Image View

```axiom
image_view {
    source
    fit
    interpolation
}
```

---

# 732.112 — Canvas

```axiom
canvas_view {
    draw
    transform
    clipping
}
```

---

# 732.113 — Custom Control

Axiom phải cho phép:

```axiom
control MySlider {
    state
    layout
    paint
    input
    accessibility
}
```

Không yêu cầu inheritance.

---

# 732.114 — Struct-Based Controls

Phù hợp core Axiom:

```axiom
struct Button {
    text: string
    enabled: bool
}

fn Button.paint(self, ctx)
fn Button.handle(self, event)
```

UI composition thông qua data + functions.

---

# 732.115 — Control Override

Một control có thể override behavior bằng explicit composition:

```axiom
button {
    paint = custom_paint
    on_click = custom_action
}
```

Không cần virtual-class hierarchy bắt buộc.

---

# 732.116 — UI Resource

Resources:

```text
image
font
brush
style
theme
template
icon
cursor
```

Có thể shared immutable.

---

# 732.117 — Resource Lifetime

UI resources có:

```text
created
loaded
resident
unloaded
destroyed
```

Không được use-after-destroy.

---

# 732.118 — Resource Loading

```text
UI
 ↓
resource request
 ↓
AXSTORAGE
 ↓
decode
 ↓
GPU upload
 ↓
UI resource
```

Loading async.

---

# 732.119 — Icon

```axiom
icon {
    vector
    raster
}
```

Vector icon có thể rasterize theo DPI.

---

# 732.120 — Cursor

```axiom
cursor {
    shape
    hotspot
}
```

---

# 732.121 — Localization

```axiom
locale {
    language
    region
    calendar
    number_format
    date_format
}
```

---

# 732.122 — Localized String

UI không hard-code user-facing string:

```axiom
text = tr("settings.save")
```

---

# 732.123 — Pluralization

Localization engine phải hỗ trợ locale-specific plural rules.

---

# 732.124 — RTL

Layout có thể hỗ trợ:

```text
LTR
RTL
AUTO
```

Direction phải được tính trong layout semantics.

---

# 732.125 — BiDi

Text rendering pipeline phải bảo toàn Unicode bidirectional semantics.

---

# 732.126 — Calendar / Number Formatting

UI formatting sử dụng locale-aware services.

AXUI không trở thành global localization database.

---

# 732.127 — Mobile Lifecycle

Mobile có thể:

```text
foreground
background
suspended
terminated
restored
```

State cần persist khi platform yêu cầu.

---

# 732.128 — State Restoration

```axiom
ui_state_snapshot {
    route
    navigation
    control_state
    user_state
}
```

Storage:

→ AXSTORAGE.

---

# 732.129 — Navigation

```axiom
navigation {
    stack
    push
    pop
    replace
}
```

---

# 732.130 — Route

```axiom
route {
    path
    parameters
}
```

Navigation semantics không đồng nghĩa network URL.

---

# 732.131 — Responsive Layout

UI có thể thay đổi theo:

```text
window size
orientation
input capability
DPI
device class
```

---

# 732.132 — Adaptive UI

```axiom
adaptive {
    when width < 600
    when width >= 600
}
```

Compiler/runtime có thể optimize breakpoint conditions.

---

# 732.133 — Safe Areas

Mobile/display notch:

```axiom
safe_area {
    top
    right
    bottom
    left
}
```

---

# 732.134 — Multi-Window

Application có thể sở hữu nhiều windows:

```text
main
tool
floating
document
dialog
```

---

# 732.135 — Multi-Monitor

Window placement phải aware:

```text
display
scale
work_area
orientation
```

---

# 732.136 — UI Persistence

Có thể lưu:

```text
window size
position
splitter state
column widths
theme
recent items
```

Không mặc định lưu mọi UI state.

---

# 732.137 — Security Boundary

UI không tự quyết định authorization.

Ví dụ:

```text
button.visible = false
```

không phải security control.

Authorization:

→ AXSECURITY.

---

# 732.138 — Secure Input

Các control nhạy cảm có thể yêu cầu:

```text
secure_text
protected_input
platform_secure_keyboard
```

---

# 732.139 — Clipboard Security

Application có thể khai báo:

```text
clipboard sensitivity
expiration
restricted export
```

---

# 732.140 — Screen Capture Policy

Application/window có thể yêu cầu platform policy:

```text
capture_allowed
capture_restricted
```

AXUI chỉ expresses policy; OS/security backend enforces.

---

# 732.141 — Accessibility Security

Accessibility data có thể chứa:

```text
private text
financial information
credentials
```

Access phải qua platform security boundary.

---

# 732.142 — UI Automation

Automation API:

```axiom
find_by_id()
find_by_role()
find_by_text()
invoke()
set_value()
get_value()
```

---

# 732.143 — UI Testability

Control nên expose stable semantic ID:

```axiom
Button {
    automation_id = "save_button"
}
```

Không dùng screen coordinates làm identity.

---

# 732.144 — UI Snapshot

```axiom
ui_snapshot {
    tree
    state
    theme
    locale
    viewport
}
```

Dùng cho:

```text
testing
debugging
replay
visual regression
```

---

# 732.145 — Event Replay

Có thể ghi:

```text
input
focus
commands
state transitions
```

sau đó replay.

---

# 732.146 — Deterministic UI

Reference mode:

```axiom
ui_runtime {
    deterministic = true
}
```

Có thể cố định:

```text
clock
animation seed
layout order
input ordering
```

---

# 732.147 — UI Simulation

Simulation có thể test:

```text
window resize
input events
network latency
slow storage
GPU delay
display refresh
```

mà không tác động production.

---

# 732.148 — UI Digital Twin

```axiom
ui_digital_twin {
    windows
    controls
    events
    rendering
    performance
}
```

Phục vụ:

```text
testing
performance analysis
automation
```

---

# 732.149 — UI Performance Model

Các hot paths:

```text
input dispatch
layout
state invalidation
paint
render submission
text shaping
virtualization
```

---

# 732.150 — No Global UI Rebuild

Thay đổi một state phải invalidate tối thiểu subtree cần thiết.

---

# 732.151 — Layout Cache

Layout result có thể cache nếu:

```text
constraints unchanged
style unchanged
content unchanged
```

---

# 732.152 — Paint Cache

Paint commands có thể cache cho subtree bất biến.

---

# 732.153 — GPU Layer Cache

Một UI subtree có thể trở thành composited GPU layer nếu có lợi.

---

# 732.154 — Zero-Copy UI

Ví dụ:

```text
camera texture
 ↓
AXMEDIA
 ↓
AXUI media_view
 ↓
AXGRAPHICS
```

không copy pixel nếu backend cho phép.

---

# 732.155 — Zero-Copy Textures

Image resource có thể được share trực tiếp với AXGRAPHICS.

---

# 732.156 — Multi-Threaded Layout

Layout tree độc lập có thể measure song song.

UI mutations vẫn phải obey ownership/thread rules.

---

# 732.157 — Multi-Threaded Paint

Independent subtrees có thể generate paint commands song song.

---

# 732.158 — Render Submission

```text
UI threads
 ↓
paint command buffers
 ↓
render graph
 ↓
AXGRAPHICS
```

Không yêu cầu một global lock cho toàn bộ UI.

---

# 732.159 — Frame Budget

Runtime theo dõi:

```text
input latency
layout time
paint time
GPU time
present latency
```

---

# 732.160 — Backpressure

Nếu rendering chậm:

```text
UI state
 ↓
coalesce invalidations
 ↓
drop redundant intermediate frames
```

Không được drop semantic events tùy tiện.

---

# 732.161 — Event Coalescing

Có thể coalesce:

```text
pointer move
resize
scroll
```

nhưng không mặc định coalesce:

```text
click
command
text commit
state-changing action
```

---

# 732.162 — Async Rendering

UI state:

```text
frame N
```

có thể render trong khi CPU xây:

```text
frame N+1
```

với snapshot isolation.

---

# 732.163 — Frame Snapshot

```axiom
ui_render_snapshot {
    visual_tree_version
    layout_version
    style_version
    resources
}
```

Renderer đọc snapshot thay vì mutable live tree.

---

# 732.164 — UI Event Log

```axiom
ui_event_record {
    event
    timestamp
    target
    result
}
```

Có thể phục vụ debugging/replay.

---

# 732.165 — Telemetry

Metrics:

```text
frame_time
input_latency
layout_time
paint_time
render_time
memory_usage
widget_count
draw_count
texture_count
```

---

# 732.166 — Error Model

```text
INVALID_NODE
INVALID_PARENT
LAYOUT_ERROR
RESOURCE_ERROR
INPUT_ERROR
WINDOW_ERROR
RENDER_ERROR
ACCESSIBILITY_ERROR
PLATFORM_ERROR
```

---

# 732.167 — Platform Backend

```axiom
ui_backend {
    create_window()
    create_surface()
    process_events()
    set_cursor()
    clipboard()
    accessibility()
}
```

Backend không làm thay đổi AXUI semantic model.

---

# 732.168 — Headless UI

AXUI phải chạy được headless cho:

```text
testing
server rendering
automation
snapshot generation
```

---

# 732.169 — Server Rendering

Có thể:

```text
UI state
 ↓
headless layout
 ↓
AXGRAPHICS
 ↓
image
```

---

# 732.170 — Remote UI

Architecture cho phép:

```text
UI model
 ↓
AXNETWORK
 ↓
remote renderer
```

nhưng AXUI core không phụ thuộc network.

---

# 732.171 — UI Serialization

Có thể serialize:

```text
UI snapshot
state snapshot
theme
layout configuration
```

Không serialize live native handles trực tiếp.

---

# 732.172 — UI Database Integration

Database-backed UI:

```text
AXDATABASE
 ↓
typed query
 ↓
view model
 ↓
virtualized control
```

UI không được biến database query thành synchronous render hot path.

---

# 732.173 — UI Network Integration

```text
network
 ↓
async task
 ↓
state
 ↓
incremental UI update
```

---

# 732.174 — UI Compute Integration

```text
AXCOMPUTE
 ↓
background computation
 ↓
immutable result
 ↓
UI state
```

---

# 732.175 — UI Media Integration

Native:

```text
video
audio
camera
microphone
screen capture
```

thông qua AXMEDIA.

---

# 732.176 — UI Graphics Integration

AXUI không duplicate renderer.

```text
AXUI
  ↓
render graph
  ↓
AXGRAPHICS
```

---

# 732.177 — UI Security Integration

```text
UI action
 ↓
AXSECURITY authorization
 ↓
application command
```

UI state không được coi là authorization.

---

# 732.178 — UI Identity Integration

AXIDENTITY cung cấp:

```text
user identity
organization identity
account/profile
```

AXUI chỉ hiển thị identity information theo application policy.

---

# 732.179 — UI Geospatial Integration

Không xây GIS riêng.

Ví dụ:

```axiom
MapView {
    spatial_source
}
```

Rendering:

```text
AXGEOSPATIAL
 ↓
geometry
 ↓
AXGRAPHICS
 ↓
AXUI
```

---

# 732.180 — Native API Surface

Core:

```axiom
create_application()
create_window()
create_view()
create_widget()

measure()
arrange()
layout()

invalidate()
request_render()

dispatch_event()
capture_pointer()
release_pointer()

focus()
clear_focus()

set_theme()
set_locale()

create_style()
create_theme()

create_command()
register_shortcut()

open_dialog()
open_popup()

clipboard_get()
clipboard_set()

start_drag()
accept_drop()

create_animation()
start_animation()

create_navigation()
push_route()
pop_route()

create_accessibility_node()

create_virtual_list()
create_virtual_grid()

create_ui_snapshot()
restore_ui_snapshot()

replay_ui_events()

run_ui_task()

create_ui_digital_twin()
simulate_ui()
```

---

# 732.181 — Formal Invariants

```text
UI-INV-01   UI node identity is stable within its lifetime.
UI-INV-02   Visual tree parent-child relationships are explicit.
UI-INV-03   Logical tree relationships are distinct from visual hierarchy.
UI-INV-04   A node cannot have two parents simultaneously.
UI-INV-05   Destroyed nodes cannot receive events.
UI-INV-06   Layout uses explicit measure and arrange semantics.
UI-INV-07   Logical units are distinct from physical pixels.
UI-INV-08   DPI scaling is explicit.
UI-INV-09   Hit testing respects transforms and clipping.
UI-INV-10   Event routing order is deterministic.

UI-INV-11   Pointer capture is explicit.
UI-INV-12   Focus ownership is explicit.
UI-INV-13   Text input is distinct from physical key events.
UI-INV-14   IME composition cannot be treated as ordinary committed text.
UI-INV-15   Selection state is explicit.
UI-INV-16   Clipboard operations are explicit.
UI-INV-17   Drag/drop operations declare allowed semantics.
UI-INV-18   Commands are distinct from visual controls.
UI-INV-19   UI visibility is not authorization.
UI-INV-20   UI validation is not domain validation.

UI-INV-21   Accessibility semantics are distinct from visual appearance.
UI-INV-22   Accessibility state is derived from authoritative UI state.
UI-INV-23   Localization does not mutate semantic identifiers.
UI-INV-24   RTL direction is explicit.
UI-INV-25   Unicode text semantics are preserved.
UI-INV-26   Theme is distinct from widget state.
UI-INV-27   Style resolution is deterministic.
UI-INV-28   Animation uses a monotonic clock.
UI-INV-29   Reduced-motion preferences are respected.
UI-INV-30   Virtualized controls preserve logical item identity.

UI-INV-31   UI mutations cannot race with protected UI-thread state.
UI-INV-32   Background work cannot directly mutate UI-owned state without synchronization.
UI-INV-33   Render snapshots are immutable during rendering.
UI-INV-34   UI rendering does not mutate logical application state.
UI-INV-35   Dropped frames cannot silently drop semantic events.
UI-INV-36   Resource destruction cannot occur while rendering uses the resource.
UI-INV-37   GPU resource synchronization is delegated to AXGRAPHICS.
UI-INV-38   Persistent state is distinct from transient UI state.
UI-INV-39   Replay does not mutate the original event log.
UI-INV-40   Simulation cannot mutate production UI state.
```

---

# 732.182 — Performance Architecture

Đường đi tối ưu:

```text
Input
 ↓
typed event
 ↓
targeted state update
 ↓
incremental invalidation
 ↓
incremental layout
 ↓
cached paint
 ↓
render snapshot
 ↓
AXGRAPHICS render graph
```

Không:

```text
input
 ↓
rebuild entire application
 ↓
reflection
 ↓
serialize UI
 ↓
render everything
```

---

# 732.183 — Compile-Time UI

Declarative UI có thể compile thành native construction code.

Ví dụ:

```axiom
ui Main {
    Column {
        Text("Hello")
        Button("Save")
    }
}
```

Compiler có thể sinh trực tiếp:

```text
node creation
property initialization
event registration
layout metadata
style metadata
```

không cần parse UI DSL tại runtime.

---

# 732.184 — Static UI Optimization

Compiler có thể biết:

```text
static tree
fixed properties
constant styles
constant layout
```

và precompute.

---

# 732.185 — Dynamic UI

Dynamic content vẫn hỗ trợ:

```axiom
for item in items {
    Text(item.name)
}
```

Compiler giữ phần dynamic tối thiểu.

---

# 732.186 — UI Diffing

Nếu declarative state thay đổi:

```text
old tree
   ↓
structural diff
   ↓
new tree
```

Diffing phải dựa trên stable identity, không chỉ index.

---

# 732.187 — Stable Identity

```axiom
key = item.id
```

giúp list virtualization và diffing giữ state chính xác.

---

# 732.188 — UI Memory

Không yêu cầu GC.

UI runtime phải hoạt động với:

```text
explicit ownership
arena/pool allocation
reference-counted shared immutable resources khi cần
stack/local state
```

nhưng API core không ép application sử dụng một memory strategy duy nhất.

---

# 732.189 — Widget Lifetime

Widget ownership nên theo tree:

```text
parent owns child
```

với explicit escape mechanism khi cần.

Điều này phù hợp với memory model của Axiom mà không cần borrow checker.

---

# 732.190 — UI Object Model

Không yêu cầu:

```text
class inheritance
virtual method table
```

cho mọi control.

Preferred model:

```text
struct
+
functions
+
composition
+
explicit interface/behavior
```

---

# 732.191 — Native Handle Boundary

OS handles phải được encapsulate:

```axiom
native_window_handle
native_input_handle
native_accessibility_handle
```

Không để platform-specific handle trở thành UI semantic type.

---

# 732.192 — UI Backend Isolation

```text
AXUI semantic
      ↓
platform adapter
 ┌────┼────┬────┐
Win  Linux macOS Mobile
```

Một application không cần biết backend đang dùng.

---

# 732.193 — UI Testing Layers

Ba cấp:

```text
semantic test
layout test
render test
```

Semantic test không phụ thuộc pixel.

---

# 732.194 — Visual Regression

```axiom
assert_snapshot(
    ui_snapshot,
    expected
)
```

Có tolerance rõ ràng cho rendering differences.

---

# 732.195 — Accessibility Testing

Automation có thể kiểm:

```text
role
name
focus order
keyboard access
state
actions
```

---

# 732.196 — Performance Testing

Benchmark:

```text
10 widgets
1K widgets
100K virtual items
large text
large image
complex layout
GPU-heavy viewport
```

---

# 732.197 — UI Profiler

Profiler hiển thị:

```text
event
layout
paint
text
GPU
frame
memory
```

theo timeline.

---

# 732.198 — UI Trace

Trace:

```text
input
state mutation
layout
paint
GPU submission
present
```

cho phép tìm input-to-display latency.

---

# 732.199 — UI Event Ordering

Nếu nhiều event có cùng timestamp:

```text
sequence_number
```

quyết định deterministic order.

---

# 732.200 — Backpressure / Slow Frame

Khi frame vượt budget:

```text
preserve semantic state
coalesce visual invalidation
reduce animation work
reduce optional rendering
```

Không tự ý bỏ user command.

---

# 732.201 — Rendering Quality Levels

Application có thể chọn:

```text
quality
performance
balanced
```

nhưng đây là rendering policy, không phải semantic correctness.

---

# 732.202 — Adaptive Rendering

Runtime có thể giảm:

```text
animation frequency
shadow quality
blur quality
particle count
```

nếu application cho phép.

---

# 732.203 — UI Memory Budget

Runtime có thể track:

```text
widget memory
text cache
image cache
GPU resources
layout cache
paint cache
```

---

# 732.204 — Resource Eviction

Cache resource có thể evict:

```text
glyph atlas
image cache
paint cache
GPU layer
```

Logical UI state không bị mất.

---

# 732.205 — UI Offline

AXUI phải hoạt động khi network unavailable.

Network-backed controls phải thể hiện:

```text
loading
offline
error
retry
```

nhưng đây là application semantics.

---

# 732.206 — Error Presentation

AXUI cung cấp primitive:

```text
error state
validation message
notification
dialog
```

Không quyết định error policy của application.

---

# 732.207 — UI State Machine

Một control có thể có explicit states:

```axiom
control_state {
    idle
    hover
    pressed
    focused
    disabled
}
```

---

# 732.208 — State vs Style

Phân biệt:

```text
semantic state
visual state
interaction state
```

để tránh style trở thành business logic.

---

# 732.209 — UI Composition

Application có thể compose:

```text
Window
 ├── Navigation
 ├── Toolbar
 ├── Content
 │    ├── Form
 │    └── Viewport3D
 └── StatusBar
```

mà không cần framework-specific inheritance.

---

# 732.210 — Component Boundary

Higher-level components:

```text
property_editor
file_browser
data_grid
chart
map
media_player
code_editor
```

không thuộc AXUI core.

Chúng có thể xây trên AXUI.

---

# 732.211 — Core Controls

AXUI core nên có:

```text
Text
Image
Button
Toggle
Checkbox
Radio
Slider
TextInput
TextArea
ScrollView
List
Grid
Tree
Table
Tab
Menu
Toolbar
Dialog
Popup
Progress
Separator
Canvas
Viewport
```

---

# 732.212 — Core Container Controls

```text
Panel
Stack
Row
Column
Grid
Overlay
SplitView
ScrollView
```

---

# 732.213 — Data Controls

Data-aware primitive:

```text
List<T>
Grid<T>
Tree<T>
Table<T>
```

Data model không thuộc AXUI.

---

# 732.214 — UI Metadata

Compiler/runtime metadata có thể chứa:

```text
control type
properties
event signatures
accessibility role
layout capabilities
style properties
```

Metadata phục vụ tooling; không yêu cầu reflection hot path.

---

# 732.215 — AI Boundary

AI có thể hỗ trợ:

```text
layout suggestion
accessibility analysis
UI test generation
style generation
component generation
visual debugging
```

Nhưng AI output:

```text
proposal / derived artifact
```

không tự động trở thành authoritative UI behavior.

---

# 732.216 — AI UI Generation

Generated UI phải vẫn compile thành:

```text
typed AXUI structures
typed event handlers
typed resources
```

Không chạy arbitrary generated code chỉ vì AI đề xuất.

---

# 732.217 — AI Accessibility

AI có thể phát hiện:

```text
missing labels
low contrast
focus problems
layout issues
```

Nhưng findings phải được phân biệt:

```text
observation
recommendation
confirmed issue
```

---

# 732.218 — AI Visual Testing

AI có thể so sánh snapshots nhưng kết quả là:

```text
derived analysis
```

không thay thế deterministic test assertions.

---

# 732.219 — UI Security AI Boundary

AI không tự cấp:

```text
permission
authorization
credential
secret
```

---

# 732.220 — UI Digital Twin 5.0

Mục tiêu cuối:

```text
Application
 ↓
AXUI
 ├── state model
 ├── visual tree
 ├── input model
 ├── layout model
 ├── accessibility tree
 ├── render graph
 └── performance model
          ↓
     Digital Twin
```

Có thể:

```text
simulate
replay
profile
test
inspect
```

mà không sửa production state.

---

# 732.221 — Canonical UI Flow

```text
create application
    ↓
create window
    ↓
create root
    ↓
compose controls
    ↓
resolve styles
    ↓
measure
    ↓
arrange
    ↓
paint
    ↓
compile render graph
    ↓
AXGRAPHICS
    ↓
present
```

---

# 732.222 — Canonical Input Flow

```text
OS/device
    ↓
platform backend
    ↓
AXUI input event
    ↓
hit test / focus
    ↓
capture
    ↓
target
    ↓
bubble
    ↓
command/state mutation
    ↓
invalidation
    ↓
render
```

---

# 732.223 — Canonical Async Flow

```text
UI action
    ↓
command
    ↓
background task
    ↓
AXNETWORK / AXDATABASE / AXCOMPUTE
    ↓
result
    ↓
UI state update
    ↓
incremental invalidation
    ↓
render
```

---

# 732.224 — Canonical Accessibility Flow

```text
UI tree
 ↓
semantic projection
 ↓
accessibility tree
 ↓
platform accessibility backend
 ↓
assistive technology
```

Visual styling không được trở thành accessibility semantics mặc định.

---

# 732.225 — Completion Criteria

`BOOTSTRAP-732` hoàn thành khi specification đã xác định:

1. Application lifecycle.
2. Application shell.
3. Window.
4. Window surface.
5. Platform backend.
6. UI node.
7. Visual tree.
8. Logical tree.
9. Widget.
10. Control.
11. View.
12. Declarative UI.
13. Imperative UI.
14. UI state.
15. Reactive state.
16. Dependency tracking.
17. Invalidation.
18. Measure.
19. Arrange.
20. Layout constraints.
21. Layout primitives.
22. Flex.
23. Grid.
24. Overlay.
25. Coordinates.
26. DPI.
27. Hit testing.
28. Mouse.
29. Touch.
30. Pen.
31. Keyboard.
32. IME.
33. Gamepad.
34. Input abstraction.
35. Event model.
36. Event routing.
37. Pointer capture.
38. Event cancellation.
39. Focus.
40. Focus scope.
41. Keyboard navigation.
42. Selection.
43. Clipboard.
44. Drag/drop.
45. Context menu.
46. Menu.
47. Command.
48. Shortcut.
49. Dialog.
50. Popup.
51. Tooltip.
52. Notification.
53. Styling.
54. Selector.
55. Pseudo states.
56. Theme.
57. Design tokens.
58. Dynamic theme.
59. Accessibility tree.
60. Accessibility roles.
61. Accessibility actions.
62. Screen-reader integration.
63. Accessibility keyboard semantics.
64. Reduced motion.
65. High contrast.
66. Unicode text.
67. Text shaping/layout.
68. Font fallback.
69. Text editing.
70. Rich text.
71. Undo/redo.
72. Virtual lists.
73. Virtual grids.
74. Tree virtualization.
75. Data binding.
76. Validation.
77. Forms.
78. Async UI.
79. UI task model.
80. Thread affinity.
81. Background work.
82. AXGRAPHICS integration.
83. Retained rendering.
84. Immediate rendering.
85. Hybrid rendering.
86. Clipping.
87. Scrolling.
88. UI animation.
89. Transitions.
90. Compositing.
91. 3D viewport.
92. Media view.
93. Image view.
94. Canvas.
95. Custom controls.
96. Struct-based control model.
97. Resource model.
98. Resource loading.
99. Localization.
100. RTL.
101. Mobile lifecycle.
102. State restoration.
103. Navigation.
104. Responsive UI.
105. Safe areas.
106. Multi-window.
107. Multi-monitor.
108. UI persistence.
109. Security boundary.
110. Secure input.
111. Clipboard security.
112. Screen capture policy.
113. UI automation.
114. UI snapshot.
115. Event replay.
116. Deterministic UI.
117. UI simulation.
118. UI digital twin.
119. Performance model.
120. Compile-time UI.
121. UI diffing.
122. Memory/lifetime model.
123. Native handle boundary.
124. Headless mode.
125. Remote UI boundary.
126. Database integration.
127. Network integration.
128. Compute integration.
129. Media integration.
130. Security integration.
131. Identity integration.
132. Geospatial integration.
133. Core controls.
134. AI boundary.
135. AI accessibility.
136. AI visual testing.
137. UI security boundary.
138. UI Digital Twin 5.0.
139. 40 formal invariants.
140. Native API surface.
141. Performance architecture.
142. Testing architecture.
143. Profiling architecture.
144. Definition of Done.

---

# 732.226 — Definition of Done

```text
BOOTSTRAP-732
STATUS: COMPLETE / FROZEN

AXUI
 ├── Application Runtime
 ├── Window Runtime
 ├── UI Tree
 ├── Widget/Control Runtime
 ├── Layout Engine
 ├── Input System
 ├── Event System
 ├── Focus System
 ├── Selection
 ├── Clipboard
 ├── Drag & Drop
 ├── Command System
 ├── Menu/Dialog/Popup
 ├── Styling
 ├── Theme
 ├── Typography
 ├── Localization
 ├── Accessibility
 ├── Data Binding
 ├── Virtualization
 ├── Navigation
 ├── Animation
 ├── Retained Rendering
 ├── Immediate Rendering
 ├── GPU Composition
 ├── Media Integration
 ├── 3D Viewport
 ├── Mobile Runtime
 ├── Desktop Runtime
 ├── UI Automation
 ├── Deterministic Replay
 ├── UI Simulation
 ├── AI Boundary
 └── UI Digital Twin 5.0
```

**BOOTSTRAP-732 / AXUI — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-733 — AXAUDIO

**Native Audio Runtime — PCM/audio buffers, sample formats, channels, sample rates, clocks, capture/playback devices, mixer, routing, DSP, resampling, effects, spatial audio, 3D audio, voice/audio streaming, MIDI/control events, low-latency audio, real-time scheduling, audio graphs, synchronization with AXMEDIA/AXGRAPHICS, GPU/CPU DSP, audio recording, metering, analysis, codecs boundary, distributed audio, deterministic processing, audio simulation & Audio Runtime 5.0.**