# BOOTSTRAP-735 — AXUI

**Namespace:** `AXUI`  
**Phase:** Axiom Civilization Runtime / Native User Interface Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXINPUT`, `AXGRAPHICS`, `AXMEDIA`, `AXAUDIO`, `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

> `AXUI` là native UI runtime của Axiom. Nó biến primitives của `AXGRAPHICS` + interaction primitives của `AXINPUT` thành một hệ thống giao diện hoàn chỉnh cho desktop, mobile, embedded, game/tool UI và ứng dụng native.

---

# 735.0 — Mục tiêu

AXUI phải hỗ trợ đồng thời:

```text
Desktop UI
Mobile UI
Embedded UI
Tool UI
Game UI
Data UI
Forms
Dialogs
Menus
Editors
Dashboards
Visualization UI
Accessibility
Internationalization
Declarative UI
Imperative UI
```

Kiến trúc:

```text
                    AXUI
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
     INPUT        UI MODEL      RENDERING
       │             │             │
   AXINPUT        UI TREE      AXGRAPHICS
       │             │             │
       └─────────────┼─────────────┘
                     ↓
                UI APPLICATION
```

---

# 735.1 — Boundary

AXUI sở hữu:

```text
window
surface
UI tree
widget
layout
style
theme
focus
UI event routing
text editing
forms
menus
dialogs
accessibility tree
UI state
data binding
animation
UI automation
UI testing
```

Không sở hữu:

```text
GPU driver          → AXGRAPHICS
raw input           → AXINPUT
audio               → AXAUDIO
media decoding      → AXMEDIA
database semantics  → AXDATABASE
network transport   → AXNETWORK
security primitives → AXSECURITY
human identity      → AXIDENTITY
```

---

# 735.2 — Core UI Model

AXUI dùng mô hình:

```text
Application
    ↓
Window
    ↓
Surface
    ↓
UI Tree
    ↓
Element
    ↓
Layout
    ↓
Render
```

---

# 735.3 — Window

```axiom
ui_window {
    id
    surface
    state
    bounds
    title
    root
}
```

Window là platform-level container.

---

# 735.4 — Window State

```text
NORMAL
MINIMIZED
MAXIMIZED
FULLSCREEN
HIDDEN
CLOSED
SUSPENDED
```

---

# 735.5 — Window Lifecycle

```text
CREATED
INITIALIZING
READY
VISIBLE
HIDDEN
SUSPENDED
CLOSING
CLOSED
```

Lifecycle transition phải explicit.

---

# 735.6 — Surface

```axiom
ui_surface {
    id
    size
    scale
    format
}
```

Surface có thể tồn tại mà không phải window.

Ví dụ:

```text
offscreen UI
embedded UI
texture UI
remote UI
```

---

# 735.7 — UI Element

```axiom
ui_element {
    id
    parent
    children
    layout
    style
    state
}
```

Element là primitive semantic của UI tree.

---

# 735.8 — Widget

Widget là reusable UI component:

```axiom
ui_widget {
    element
    behavior
    properties
}
```

Ví dụ:

```text
Button
Text
Input
Checkbox
Slider
List
Table
Tree
Menu
Toolbar
```

---

# 735.9 — UI Tree

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

Tree là logical structure, không nhất thiết tương ứng 1:1 với render primitives.

---

# 735.10 — Logical vs Visual Tree

Phải phân biệt:

```text
logical UI tree
visual/render tree
accessibility tree
```

Một widget có thể tạo nhiều render nodes.

---

# 735.11 — UI Identity

Mỗi element có stable identity:

```axiom
ui_id
```

Không sử dụng memory address làm UI identity.

---

# 735.12 — UI State

```axiom
ui_state {
    enabled
    visible
    focused
    hovered
    pressed
    selected
    expanded
    checked
}
```

State là runtime state, không nhất thiết là application model.

---

# 735.13 — Properties

```axiom
ui_property {
    name
    type
    value
}
```

Core phải hỗ trợ typed properties.

Không yêu cầu reflection trong hot path.

---

# 735.14 — Declarative UI

Axiom có thể mô tả:

```axiom
ui window {
    column {
        text("Hello")
        button("Save")
        button("Cancel")
    }
}
```

Declarative syntax được compiler lowering xuống native UI tree.

---

# 735.15 — Imperative UI

Đồng thời hỗ trợ:

```axiom
window.add(button)
button.on_click(save)
```

Hai mô hình phải sử dụng cùng runtime semantics.

---

# 735.16 — UI Compilation

Declarative UI có thể compile thành:

```text
UI AST
 ↓
UI IR
 ↓
layout plan
 ↓
render plan
 ↓
native executable data
```

---

# 735.17 — Static UI

UI không thay đổi cấu trúc runtime có thể được compile gần như hoàn toàn.

```text
compile-time
    ↓
static tree
    ↓
precomputed layout metadata
```

---

# 735.18 — Dynamic UI

UI dynamic vẫn hỗ trợ:

```text
insert
remove
replace
reorder
```

nhưng phải update incremental.

---

# 735.19 — Layout

Layout engine phải hỗ trợ:

```text
absolute
stack
row
column
grid
flex
overlay
anchor
constraint
flow
```

---

# 735.20 — Layout Constraints

Primitive:

```axiom
ui_constraint {
    variable
    relation
    value
}
```

Relations:

```text
equal
less_equal
greater_equal
```

---

# 735.21 — Size Model

```text
fixed
minimum
maximum
preferred
content
fill
fraction
```

---

# 735.22 — Measure / Arrange

Layout pipeline:

```text
measure
   ↓
constraints
   ↓
arrange
   ↓
final bounds
```

---

# 735.23 — Layout Invalidation

Khi property thay đổi:

```text
property change
 ↓
invalidate layout
 ↓
recompute affected subtree
```

Không layout lại toàn bộ UI nếu không cần.

---

# 735.24 — Render Invalidation

Tương tự:

```text
state change
 ↓
invalidate visual region
 ↓
rerender affected region
```

---

# 735.25 — DPI / Scaling

AXUI phải hỗ trợ:

```text
logical units
physical pixels
display scale
device pixel ratio
```

Không hard-code 96 DPI.

---

# 735.26 — Multi-Display

```axiom
ui_display {
    id
    bounds
    scale
    refresh_rate
    color_space
}
```

Window có thể di chuyển giữa displays.

---

# 735.27 — Orientation

Mobile:

```text
portrait
landscape
reverse_portrait
reverse_landscape
```

UI layout phải thích nghi mà không phụ thuộc orientation cố định.

---

# 735.28 — Responsive Layout

UI có thể thay đổi theo:

```text
width
height
scale
orientation
input capabilities
```

---

# 735.29 — Text

AXUI text system phải hỗ trợ:

```text
UTF-8
Unicode
grapheme clusters
bidirectional text
complex scripts
IME
text selection
cursor
```

---

# 735.30 — Text Layout

```axiom
text_layout {
    text
    font
    size
    width
    direction
    language
}
```

---

# 735.31 — Font

```axiom
ui_font {
    family
    weight
    style
    size
}
```

Font rasterization thuộc graphics integration.

---

# 735.32 — Text Editing

```axiom
text_editor {
    text
    selection
    cursor
    composition
}
```

AXINPUT cung cấp IME events; AXUI sở hữu editing semantics.

---

# 735.33 — Selection

Selection phải hỗ trợ:

```text
caret
range
multiple ranges
word
line
paragraph
```

---

# 735.34 — Clipboard

```axiom
clipboard {
    formats
    data
}
```

Formats:

```text
text
rich_text
image
application_data
```

Clipboard backend là platform integration.

---

# 735.35 — Drag & Drop

```axiom
drag_operation {
    source
    payload
    allowed_actions
}
```

Actions:

```text
copy
move
link
```

---

# 735.36 — Input Integration

Pipeline:

```text
AXINPUT
   ↓
raw/normalized event
   ↓
UI hit testing
   ↓
focus/capture
   ↓
UI event
   ↓
widget
```

---

# 735.37 — UI Event

```axiom
ui_event {
    type
    target
    source
    timestamp
    payload
}
```

---

# 735.38 — Event Phases

```text
capture
target
bubble
```

---

# 735.39 — Event Propagation

```text
Window
 ↓
Panel
 ↓
Button
 ↑
Panel
 ↑
Window
```

Application có thể:

```text
consume
pass
transform
redirect
```

---

# 735.40 — Hit Testing

```axiom
hit_test(
    surface,
    position
)
```

Phải hỗ trợ:

```text
visible bounds
clip region
transformed elements
input transparency
z-order
```

---

# 735.41 — Pointer Capture

Widget có thể giữ pointer:

```axiom
capture_pointer(pointer_id)
```

Cần thiết cho:

```text
drag
resize
drawing
slider
```

---

# 735.42 — Focus

```axiom
ui_focus {
    keyboard
    text
    pointer
    controller
}
```

---

# 735.43 — Focus Navigation

Có thể điều hướng:

```text
Tab
Shift+Tab
Arrow
Gamepad
Accessibility switch
```

---

# 735.44 — Focus Scope

```axiom
focus_scope {
    root
    policy
}
```

Ví dụ:

```text
dialog
menu
modal
form
```

---

# 735.45 — Modal UI

```axiom
ui_modal {
    owner
    content
    modality
}
```

Modal phải giới hạn input routing theo scope.

---

# 735.46 — Button

```axiom
ui_button {
    text
    icon
    command
}
```

States:

```text
normal
hover
pressed
disabled
focused
```

---

# 735.47 — Text

```axiom
ui_text {
    content
    style
    alignment
    wrapping
}
```

---

# 735.48 — Text Input

```axiom
ui_text_input {
    value
    placeholder
    selection
    validation
}
```

---

# 735.49 — Checkbox

```axiom
ui_checkbox {
    checked
    indeterminate
}
```

---

# 735.50 — Radio

```axiom
ui_radio {
    group
    selected
}
```

---

# 735.51 — Slider

```axiom
ui_slider {
    value
    minimum
    maximum
    step
}
```

---

# 735.52 — Progress

```axiom
ui_progress {
    value
    maximum
    indeterminate
}
```

---

# 735.53 — List

```axiom
ui_list {
    items
    selection
    virtualization
}
```

---

# 735.54 — Virtualized List

List lớn:

```text
1,000,000 items
```

không tạo 1,000,000 visual nodes.

Chỉ render visible range.

---

# 735.55 — Table

```axiom
ui_table {
    columns
    rows
    selection
    sorting
}
```

---

# 735.56 — Tree

```axiom
ui_tree {
    root
    expanded
    selection
}
```

---

# 735.57 — Menu

```axiom
ui_menu {
    items
    shortcuts
}
```

---

# 735.58 — Menu Item

```axiom
ui_menu_item {
    label
    command
    shortcut
    enabled
    checked
}
```

---

# 735.59 — Toolbar

```axiom
ui_toolbar {
    items
}
```

---

# 735.60 — Dialog

```axiom
ui_dialog {
    title
    content
    buttons
    modality
}
```

---

# 735.61 — Notification

```axiom
ui_notification {
    title
    message
    severity
    actions
}
```

---

# 735.62 — Form

```axiom
ui_form {
    fields
    validation
    submit
}
```

---

# 735.63 — Validation

```axiom
validation_result {
    valid
    errors
    warnings
}
```

UI validation không phải authoritative business validation.

---

# 735.64 — Data Binding

```axiom
ui_binding {
    source
    property
    direction
}
```

Modes:

```text
one_way
two_way
one_time
command
```

---

# 735.65 — Reactive State

UI có thể subscribe state changes:

```axiom
observe(state)
```

Compiler/runtime phải ưu tiên dependency graph typed thay vì reflection.

---

# 735.66 — State Graph

```text
Application State
       ↓
Derived State
       ↓
UI Binding
       ↓
UI State
       ↓
Render
```

UI-derived state không được tự động trở thành application truth.

---

# 735.67 — Command

```axiom
ui_command {
    id
    execute
    can_execute
}
```

Button, menu, shortcut có thể cùng gọi một command.

---

# 735.68 — Undo / Redo

```axiom
ui_history {
    undo()
    redo()
}
```

UI history phải phân biệt với domain transaction.

---

# 735.69 — Styling

```axiom
ui_style {
    font
    margin
    padding
    border
    background
    foreground
    opacity
}
```

---

# 735.70 — Theme

```axiom
ui_theme {
    colors
    typography
    spacing
    controls
    animations
}
```

Theme không nên hard-code vào widget implementation.

---

# 735.71 — Design Tokens

```axiom
ui_token {
    name
    type
    value
}
```

Ví dụ:

```text
spacing.small
spacing.large
radius.default
font.heading
```

---

# 735.72 — Style Resolution

```text
default
 ↓
theme
 ↓
component
 ↓
state
 ↓
instance
```

Priority phải deterministic.

---

# 735.73 — Animation

```axiom
ui_animation {
    target
    property
    duration
    easing
}
```

---

# 735.74 — Transition

```axiom
ui_transition {
    from_state
    to_state
    animation
}
```

---

# 735.75 — UI Timeline

```axiom
ui_timeline {
    tracks
    duration
}
```

Có thể sync với:

```text
AXMEDIA
AXAUDIO
AXGRAPHICS
```

---

# 735.76 — Accessibility Tree

AXUI phải cung cấp tree riêng:

```axiom
accessibility_node {
    role
    name
    value
    state
    actions
    children
}
```

---

# 735.77 — Accessibility Roles

```text
button
text
heading
textbox
checkbox
radio
slider
list
list_item
table
tree
dialog
menu
image
link
```

---

# 735.78 — Accessibility Actions

```text
activate
focus
select
expand
collapse
increment
decrement
scroll
edit
```

---

# 735.79 — Accessibility State

```text
enabled
disabled
selected
expanded
checked
focused
busy
invalid
```

---

# 735.80 — Screen Reader

AXUI expose semantic accessibility tree cho platform screen-reader backend.

Không để screen reader phải phân tích pixels.

---

# 735.81 — High Contrast

Theme có thể hỗ trợ:

```text
high_contrast
reduced_motion
large_text
large_controls
```

---

# 735.82 — Reduced Motion

Animation engine phải cho phép:

```text
normal
reduced
disabled
```

---

# 735.83 — Localization

```axiom
ui_locale {
    language
    region
    calendar
    numbering
}
```

---

# 735.84 — Localized Text

Không hard-code user-facing strings vào widget implementation.

```axiom
localized("save")
```

---

# 735.85 — RTL

UI phải hỗ trợ:

```text
LTR
RTL
mixed
```

Layout direction không được suy ra đơn giản từ từng character.

---

# 735.86 — Resource System

UI resources:

```text
fonts
icons
images
strings
themes
templates
sounds
animations
```

AXSTORAGE/AXMEDIA quản lý resource data; AXUI quản lý semantic usage.

---

# 735.87 — UI Asset

```axiom
ui_asset {
    id
    type
    resource
}
```

---

# 735.88 — Render Integration

AXUI tạo render plan:

```text
UI Tree
 ↓
Layout
 ↓
Visual Tree
 ↓
Render Commands
 ↓
AXGRAPHICS
```

---

# 735.89 — Render Batching

Các elements tương thích có thể batch:

```text
text
rectangles
icons
images
```

giảm GPU state changes.

---

# 735.90 — Dirty Regions

AXUI theo dõi:

```text
layout dirty
visual dirty
text dirty
accessibility dirty
```

độc lập.

---

# 735.91 — Clipping

Mỗi visual node có thể có:

```text
clip rect
clip path
scissor
mask
```

---

# 735.92 — Transform

```axiom
ui_transform {
    translation
    scale
    rotation
}
```

Canonical transform có thể sử dụng matrix/quaternion primitives của AXGRAPHICS.

---

# 735.93 — Compositing

```text
opacity
blend
mask
layer
```

---

# 735.94 — UI Layer

```axiom
ui_layer {
    z_index
    opacity
    transform
}
```

---

# 735.95 — Offscreen Surface

Một subtree có thể render vào offscreen surface:

```text
UI subtree
 ↓
offscreen texture
 ↓
composite
```

---

# 735.96 — GPU Acceleration

AXUI phải sử dụng GPU khi có lợi cho:

```text
large UI
text rendering
transforms
effects
animation
compositing
```

---

# 735.97 — CPU Fallback

Mọi core UI primitive phải có khả năng chạy trên CPU backend tối thiểu.

---

# 735.98 — Native Controls

Platform-native controls có thể được adapter:

```axiom
native_control {
    platform
    type
}
```

Nhưng không được làm core AXUI phụ thuộc vào native widget toolkit.

---

# 735.99 — Custom Controls

Developer có thể tạo:

```axiom
component MyControl {
    state
    layout
    render
    input
}
```

---

# 735.100 — Component Model

Component gồm:

```text
properties
state
children
layout
events
commands
render
accessibility
```

---

# 735.101 — Component Composition

Ưu tiên composition:

```text
Button
 = Surface
 + Text
 + Interaction
 + Accessibility
```

thay vì inheritance hierarchy sâu.

---

# 735.102 — Templates

```axiom
ui_template {
    structure
    style
    behavior
}
```

Template có thể instantiate nhiều lần.

---

# 735.103 — Virtual DOM Không Bắt Buộc

AXUI không yêu cầu virtual DOM.

Runtime có thể dùng:

```text
retained tree
incremental diff
direct mutation
compiled UI
```

theo workload.

---

# 735.104 — Retained Mode

Tree tồn tại giữa các frames.

Ưu điểm:

```text
layout caching
event routing
accessibility
incremental updates
```

---

# 735.105 — Immediate Mode

Cho tool/debug UI:

```axiom
ui.begin()
ui.button("Build")
ui.end()
```

Immediate mode có thể lower vào retained rendering internals nếu cần.

---

# 735.106 — Hybrid UI

AXUI cho phép:

```text
retained application shell
+
immediate editor panels
+
custom GPU rendering
```

Đây là mô hình quan trọng cho Axiom IDE/tooling.

---

# 735.107 — Embedded Render Surface

```axiom
ui_render_surface {
    graphics_surface
}
```

Cho phép nhúng:

```text
3D viewport
video player
chart
game renderer
```

---

# 735.108 — AXMEDIA Integration

Video/image:

```text
AXMEDIA
 ↓
media surface
 ↓
AXUI
```

AXUI không decode media.

---

# 735.109 — AXAUDIO Integration

UI có thể trigger:

```text
click sound
notification sound
preview
```

Nhưng audio rendering thuộc AXAUDIO.

---

# 735.110 — AXINPUT Integration

Các primitive:

```text
keyboard
pointer
touch
pen
gamepad
gesture
```

được chuyển thành UI events.

---

# 735.111 — UI Automation

```axiom
ui_automation_node {
    id
    role
    name
    actions
}
```

Cho phép test:

```text
find("Save")
click()
```

Không cần phụ thuộc coordinates.

---

# 735.112 — UI Testing

Test categories:

```text
layout
interaction
state
accessibility
render
localization
input
```

---

# 735.113 — Deterministic UI Test

Test environment có thể freeze:

```text
clock
input
network
randomness
animation
```

---

# 735.114 — UI Replay

```axiom
ui_replay {
    input_recording
    state_snapshots
    timing
}
```

Dùng để tái hiện bug.

---

# 735.115 — Screenshot Testing

Có thể render UI offscreen:

```axiom
render_ui_snapshot(
    component
)
```

và so sánh output theo policy.

---

# 735.116 — Accessibility Testing

Automated validation:

```text
missing label
invalid role
focus trap
contrast metadata
keyboard unreachable control
```

---

# 735.117 — UI State Machine

Một component có thể khai báo:

```axiom
ui_state_machine {
    states
    transitions
}
```

---

# 735.118 — State Transition

```axiom
ui_transition {
    from
    event
    to
}
```

---

# 735.119 — Async UI

UI operations có thể await:

```axiom
async fn load_data()
```

Nhưng UI thread không được block.

---

# 735.120 — UI Scheduler

```axiom
ui_scheduler {
    post()
    dispatch()
    defer()
}
```

Các mutation UI có thể yêu cầu UI-thread affinity tùy backend.

---

# 735.121 — Background Work

Pipeline:

```text
UI
 ↓
AXCOMPUTE task
 ↓
result
 ↓
UI scheduler
 ↓
state update
```

---

# 735.122 — Thread Affinity

UI objects có thể có:

```text
owner_thread
```

Runtime phải kiểm tra hoặc enforce policy.

---

# 735.123 — UI Data Streaming

Các bảng/list lớn có thể nhận stream:

```axiom
ui_data_source {
    fetch
    subscribe
}
```

Không yêu cầu load toàn bộ dataset vào UI memory.

---

# 735.124 — Database Integration

AXDATABASE cung cấp query:

```text
query
 ↓
typed result stream
 ↓
UI data source
```

Không cho UI trực tiếp trở thành database layer.

---

# 735.125 — Network Integration

Remote data:

```text
AXNETWORK
 ↓
application state
 ↓
AXUI
```

Không để widget tự ý tạo network connections mặc định.

---

# 735.126 — Security

Sensitive UI:

```text
password
secure input
authentication prompt
private data
```

phải có security metadata.

---

# 735.127 — Secure Text Input

```axiom
secure_text_input {
    value_policy
    clipboard_policy
    accessibility_policy
}
```

AXSECURITY quyết định các policy liên quan.

---

# 735.128 — Permission UI

UI có thể hiển thị permission request nhưng không tự cấp permission.

---

# 735.129 — Identity Integration

AXIDENTITY có thể cung cấp:

```text
display name
avatar
organization
account state
```

nhưng AXUI không trở thành identity authority.

---

# 735.130 — UI Session

```axiom
ui_session {
    windows
    focus
    theme
    locale
    accessibility
}
```

---

# 735.131 — UI Application Lifecycle

```text
CREATED
STARTING
RUNNING
SUSPENDING
SUSPENDED
RESUMING
CLOSING
CLOSED
```

---

# 735.132 — Multi-Window

Một application có thể có:

```text
main window
secondary window
dialog
floating tool
popup
```

---

# 735.133 — Popup

```axiom
ui_popup {
    anchor
    content
    placement
}
```

Placement có thể tự động điều chỉnh theo viewport.

---

# 735.134 — Tooltip

```axiom
ui_tooltip {
    target
    content
    delay
}
```

---

# 735.135 — Context Menu

```axiom
ui_context_menu {
    target
    items
}
```

---

# 735.136 — Desktop Integration

AXUI abstraction cho:

```text
window decorations
taskbar/dock
system menu
clipboard
notifications
drag/drop
file dialogs
```

Platform backend chịu trách nhiệm native integration.

---

# 735.137 — Mobile Integration

Hỗ trợ:

```text
safe areas
navigation
system bars
virtual keyboard
rotation
touch
gestures
application lifecycle
```

---

# 735.138 — Embedded

AXUI có thể chạy trên:

```text
no-window systems
fixed display
touch panel
industrial terminal
automotive display
```

---

# 735.139 — Headless UI

Có thể tạo UI tree không cần display:

```text
testing
server rendering
accessibility inspection
automation
```

---

# 735.140 — UI Serialization

UI structure có thể serialize khi cần:

```axiom
serialize_ui_tree()
```

Nhưng serialized representation không phải source of truth của application state.

---

# 735.141 — UI Snapshot

```axiom
ui_snapshot {
    tree
    state
    layout
    theme
}
```

Dùng cho debugging/replay.

---

# 735.142 — Undoable UI State

Runtime phân biệt:

```text
ephemeral UI state
application state
domain state
```

Không snapshot tất cả dữ liệu một cách mù quáng.

---

# 735.143 — UI Error Boundary

```axiom
ui_error_boundary {
    fallback
    logging
    recovery
}
```

Một widget lỗi không nhất thiết làm crash toàn bộ UI process nếu isolation policy cho phép.

---

# 735.144 — Plugin Components

Axiom tools có thể load UI components dynamically:

```axiom
ui_component_module {
    metadata
    interface
    capabilities
}
```

Security policy của AXSECURITY kiểm soát module.

---

# 735.145 — UI Resource Hot Reload

Development mode:

```text
style
layout
template
asset
```

có thể reload.

Production không phụ thuộc hot reload.

---

# 735.146 — UI Profiling

Runtime phải expose:

```text
layout time
style resolution
event dispatch
render preparation
GPU submission
text shaping
allocation
```

---

# 735.147 — Performance Counters

```axiom
ui_metrics {
    frame_time
    layout_time
    render_time
    event_time
    allocations
    nodes
}
```

---

# 735.148 — Memory Architecture

UI phải hỗ trợ:

```text
arena
pool
slab
small object storage
persistent component storage
```

Không bắt buộc heap allocation cho mỗi UI element/event.

---

# 735.149 — Node Storage

Hot data và cold data tách:

```text
HOT:
bounds
state
parent
flags

COLD:
metadata
debug info
accessibility extras
```

---

# 735.150 — Incremental Update

State change:

```text
state
 ↓
dependency graph
 ↓
affected nodes
 ↓
layout/render invalidation
```

Không rebuild toàn UI.

---

# 735.151 — Compile-Time Specialization

Compiler có thể specialize:

```text
static widget tree
layout constants
style constants
event routes
property types
accessibility metadata
```

---

# 735.152 — Zero Reflection Hot Path

Event dispatch, layout và rendering không được phụ thuộc bắt buộc vào:

```text
runtime reflection
dynamic string lookup
boxed values
```

---

# 735.153 — UI IR

Đề xuất:

```text
UI-AST
 ↓
UI-IR
 ├── NODE_CREATE
 ├── NODE_UPDATE
 ├── LAYOUT
 ├── STYLE
 ├── EVENT_BIND
 ├── ACCESSIBILITY
 └── RENDER
```

---

# 735.154 — UI Compiler

Compiler stages:

```text
parse
 ↓
semantic analysis
 ↓
component resolution
 ↓
binding analysis
 ↓
layout analysis
 ↓
UI IR
 ↓
specialization
 ↓
native code/data
```

---

# 735.155 — UI Runtime Graph

```text
State Graph
    ↓
Binding Graph
    ↓
UI Tree
    ↓
Layout Graph
    ↓
Visual Tree
    ↓
Render Graph
```

Accessibility graph được xây song song.

---

# 735.156 — AI UI Assistance

AI có thể:

```text
generate UI
suggest layout
generate bindings
generate accessibility metadata
generate tests
analyze UI performance
```

Nhưng AI-generated UI không tự động có quyền truy cập dữ liệu nhạy cảm.

---

# 735.157 — AI Boundary

AI output phải được coi là:

```text
generated
derived
reviewable
versioned
```

AI không tự động:

```text
grant permission
send sensitive data
execute privileged command
```

---

# 735.158 — UI Digital Twin

```axiom
ui_digital_twin {
    windows
    elements
    state
    input
    layout
    rendering
}
```

Cho phép mô phỏng interaction mà không cần physical display.

---

# 735.159 — UI Simulation

Có thể chạy:

```text
input
 ↓
UI routing
 ↓
state transitions
 ↓
layout
 ↓
render
```

trong headless environment.

---

# 735.160 — Formal Invariants

```text
UI-INV-01   Every UI element has stable identity.
UI-INV-02   UI identity is not a memory address.
UI-INV-03   Logical tree and visual tree are distinct concepts.
UI-INV-04   Accessibility tree is semantically independent.
UI-INV-05   Window lifecycle transitions are explicit.
UI-INV-06   Surface lifecycle is distinct from window lifecycle.
UI-INV-07   Layout operates on explicit constraints.
UI-INV-08   Layout invalidation is explicit.
UI-INV-09   Visual invalidation is distinct from layout invalidation.
UI-INV-10   Coordinate spaces are explicit.

UI-INV-11   Logical units are distinct from physical pixels.
UI-INV-12   Display scale is explicit.
UI-INV-13   UI supports multiple display contexts.
UI-INV-14   Text input is distinct from key input.
UI-INV-15   IME composition state is preserved.
UI-INV-16   Text layout supports Unicode semantics.
UI-INV-17   RTL direction is explicit.
UI-INV-18   Localization is distinct from rendering.
UI-INV-19   Clipboard data has explicit format.
UI-INV-20   Drag/drop payload has explicit action semantics.

UI-INV-21   Input routing follows explicit propagation phases.
UI-INV-22   Pointer capture is explicit.
UI-INV-23   Focus is distinct from pointer capture.
UI-INV-24   Modal scopes constrain event routing.
UI-INV-25   UI validation is distinct from domain validation.
UI-INV-26   UI state is distinct from application truth.
UI-INV-27   UI bindings are typed.
UI-INV-28   Binding updates are deterministic.
UI-INV-29   Commands are distinct from visual controls.
UI-INV-30   Undo history is distinct from domain transactions.

UI-INV-31   Accessibility semantics cannot depend solely on pixels.
UI-INV-32   Accessibility actions map to explicit UI capabilities.
UI-INV-33   Reduced-motion policy is respected by animation.
UI-INV-34   Sensitive input can be marked secure.
UI-INV-35   UI cannot bypass AXSECURITY authorization.
UI-INV-36   Native platform controls cannot redefine AXUI core semantics.
UI-INV-37   Immediate and retained UI modes share core event semantics.
UI-INV-38   Virtualized controls cannot require materialization of all items.
UI-INV-39   AI-generated UI is explicitly attributable.
UI-INV-40   UI replay and simulation cannot silently mutate production state.
```

---

# 735.161 — Performance Architecture

Mục tiêu hot path:

```text
Input
 ↓
Hit Test
 ↓
Event Dispatch
 ↓
State Update
 ↓
Incremental Layout
 ↓
Render Plan
 ↓
GPU
```

Không:

```text
event
 ↓
reflection
 ↓
string lookup
 ↓
boxed object
 ↓
global tree rebuild
```

---

# 735.162 — Frame Budget

AXUI phải cho phép:

```text
input budget
layout budget
render preparation budget
GPU budget
```

được đo độc lập.

---

# 735.163 — Parallel Layout

Large UI tree có thể partition:

```text
Root
 ├── Panel A → worker
 ├── Panel B → worker
 └── Panel C → worker
```

sau đó merge deterministic.

---

# 735.164 — GPU UI

GPU path ưu tiên:

```text
batched geometry
texture atlases
glyph atlases
instancing
cached render primitives
```

---

# 735.165 — Text Performance

Text system cần:

```text
glyph cache
shaping cache
layout cache
font cache
```

---

# 735.166 — Virtualization

Bắt buộc cho các component có potential large datasets:

```text
List
Grid
Table
Tree
```

---

# 735.167 — Memory Efficiency

Một UI node nhỏ phải có thể biểu diễn bằng compact native structure.

Không yêu cầu:

```text
object header
virtual table
hash map
reflection metadata
```

cho mọi node.

---

# 735.168 — Render Cache

Có thể cache:

```text
static subtree
text layout
vector geometry
image composition
shadow
```

Cache invalidation phải deterministic.

---

# 735.169 — Compile-Time UI

UI tĩnh:

```text
declarative source
 ↓
compile
 ↓
prebuilt UI graph
```

giảm startup cost và allocations.

---

# 735.170 — Native Platform Strategy

```text
                 AXUI
                   │
          ┌────────┼────────┐
          ↓        ↓        ↓
       Native    Custom    Headless
       Backend   Renderer   Backend
```

Application không cần biết backend cụ thể.

---

# 735.171 — Native API

```axiom
create_ui_application()
create_ui_window()
create_ui_surface()

create_element()
create_widget()
destroy_element()

append_child()
remove_child()
replace_child()

measure()
arrange()
invalidate_layout()
invalidate_visual()

hit_test()

set_focus()
capture_pointer()
release_pointer()

create_style()
create_theme()

create_text_layout()
create_text_input()

create_binding()
create_command()

create_list()
create_table()
create_tree()

create_menu()
create_dialog()
create_popup()

create_accessibility_node()

render_ui()
render_ui_snapshot()

record_ui()
replay_ui()

simulate_ui()

create_ui_session()
create_ui_digital_twin()

profile_ui()
```

---

# 735.172 — Canonical UI Flow

Ví dụ Button:

```text
AXINPUT
   ↓
pointer_down
   ↓
hit_test
   ↓
Button
   ↓
pressed state
   ↓
pointer_up
   ↓
activate
   ↓
Command
   ↓
Application
```

---

# 735.173 — Declarative Example

```axiom
window "Axiom IDE" {
    row {
        button("Build") -> build_project
        button("Run")   -> run_project
    }

    column {
        editor(source_code)
        terminal(output)
    }
}
```

Compiler có thể biến thành UI IR tĩnh + dynamic bindings.

---

# 735.174 — Definition of Done

`BOOTSTRAP-735` hoàn thành khi Axiom đã freeze:

```text
✓ Window
✓ Surface
✓ UI Tree
✓ Visual Tree
✓ Accessibility Tree
✓ Widget model
✓ Component model
✓ Declarative UI
✓ Imperative UI
✓ Hybrid UI
✓ Layout
✓ Constraints
✓ Responsive layout
✓ DPI/scaling
✓ Multi-display
✓ Text
✓ Unicode
✓ IME
✓ Text editing
✓ Clipboard
✓ Drag/drop
✓ Input routing
✓ Focus
✓ Capture
✓ Modal
✓ Standard controls
✓ Lists
✓ Tables
✓ Trees
✓ Menus
✓ Dialogs
✓ Forms
✓ Data binding
✓ Commands
✓ Undo/redo
✓ Styling
✓ Themes
✓ Design tokens
✓ Animation
✓ Accessibility
✓ Localization
✓ RTL
✓ Rendering
✓ GPU acceleration
✓ CPU fallback
✓ Native controls
✓ Custom controls
✓ Virtualization
✓ UI automation
✓ UI testing
✓ Deterministic replay
✓ Headless UI
✓ AXINPUT integration
✓ AXGRAPHICS integration
✓ AXMEDIA integration
✓ AXAUDIO integration
✓ AXCOMPUTE integration
✓ AXDATABASE integration
✓ AXNETWORK integration
✓ AXSECURITY integration
✓ AXIDENTITY integration
✓ AI boundary
✓ UI simulation
✓ UI digital twin
✓ UI compiler
✓ UI IR
✓ Performance architecture
✓ 40 formal invariants
✓ Native API
```

**BOOTSTRAP-735 / AXUI — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-736 — AXWINDOW

**Native Window & Display Management Runtime — windows, monitors, displays, surfaces, DPI, scaling, fullscreen, multi-monitor, virtual desktops, workspaces, decorations, positioning, resize, maximize/minimize, z-order, focus, compositor integration, display modes, HDR/color spaces, refresh synchronization, cursor integration, clipboard/drag-drop boundary, desktop/mobile window lifecycle, embedded surfaces, remote windows, headless surfaces, window security, display capture, screen topology, deterministic window simulation và Window Runtime 5.0.**