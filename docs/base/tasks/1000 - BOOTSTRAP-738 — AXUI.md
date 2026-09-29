# BOOTSTRAP-738 — AXUI

**Namespace:** `AXUI`  
**Phase:** Axiom Civilization Runtime / Native User Interface Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXWINDOW`, `AXDISPLAY`, `AXGRAPHICS`, `AXINPUT`, `AXMEDIA`, `AXAUDIO`, `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

> `AXUI` là tầng UI native của Axiom. Nó sở hữu **semantic UI, visual tree, controls, layout, styling, text, accessibility, interaction state và UI lifecycle**; không sở hữu window, display, GPU rendering backend hay raw input device.

---

# 738.0 — Mục tiêu

AXUI phải cung cấp một UI framework native đủ để xây:

```text
desktop applications
mobile applications
embedded UI
tools
editors
IDEs
databases/admin consoles
media editors
games/tools UI
scientific applications
enterprise applications
accessibility interfaces
```

Kiến trúc:

```text
                         AXUI
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
     SEMANTICS          LAYOUT           RENDERING
        │                 │                 │
        ↓                 ↓                 ↓
   controls/tree      geometry/flow      AXGRAPHICS
        │                 │                 │
        └────────────┬────┴─────────────────┘
                     ↓
                  INPUT
                     │
                  AXINPUT
                     │
                     ↓
                  WINDOW
                     │
                  AXWINDOW
```

Nguyên tắc:

```text
UI ≠ Window
UI ≠ Graphics
UI ≠ Input
UI ≠ Application State
```

---

# 738.1 — UI Root

Mỗi UI hierarchy có root:

```axiom
ui_root {
    id
    tree
    viewport
    environment
}
```

Root có thể gắn vào:

```text
window
offscreen surface
embedded display
virtual display
headless renderer
```

---

# 738.2 — Visual Tree

AXUI dùng retained visual tree làm canonical representation:

```text
ui_root
 ├── node
 │    ├── node
 │    └── node
 └── node
```

Mỗi node có stable identity.

---

# 738.3 — UI Node Identity

```axiom
ui_node_id
```

không được phụ thuộc vào:

```text
memory address
GPU handle
native window handle
DOM-like string selector
```

---

# 738.4 — UI Node

```axiom
ui_node {
    id
    parent
    children
    layout
    style
    state
    semantics
    render_state
}
```

---

# 738.5 — Node Lifecycle

```text
CREATED
   ↓
ATTACHED
   ↓
LAYOUT
   ↓
READY
   ↓
VISIBLE
   ↓
DETACHING
   ↓
DETACHED
   ↓
DESTROYED
```

Lifecycle phải explicit.

---

# 738.6 — Ownership

UI tree sở hữu node hierarchy.

Application state không bắt buộc phải nằm trong UI node.

Điều này tránh:

```text
UI lifetime == business-data lifetime
```

---

# 738.7 — Application State Boundary

```text
Application State
        │
        ↓
    View Model
        │
        ↓
       AXUI
```

AXUI không trở thành database/business runtime.

---

# 738.8 — Control

Control là UI node có semantics + behavior.

Ví dụ:

```text
button
checkbox
radio
slider
text_field
text_area
list
table
tree
menu
dialog
tab
scroll_view
image
canvas
progress
calendar
```

---

# 738.9 — Primitive vs Control

Primitive:

```text
node
rectangle
text
image
path
clip
transform
```

Control:

```text
button
list
textbox
menu
```

Không nên biến mọi visual primitive thành heavyweight object.

---

# 738.10 — Control State

```axiom
control_state {
    enabled
    visible
    focused
    hovered
    pressed
    selected
    checked
    expanded
    active
}
```

Chỉ những state phù hợp với control mới được sử dụng.

---

# 738.11 — Enabled vs Visible

Hai trạng thái độc lập:

```text
enabled = false
visible = true
```

là hợp lệ.

---

# 738.12 — Focus

Focus semantics:

```axiom
focus_manager {
    focused_node
    focus_scope
    traversal_policy
}
```

---

# 738.13 — Focus Scope

Một dialog hoặc panel có thể tạo focus scope.

```text
application
 ├── main focus scope
 └── modal dialog focus scope
```

---

# 738.14 — Keyboard Focus

AXUI nhận semantic input từ:

→ `AXINPUT`

AXINPUT không quyết định control nào nhận keyboard focus.

---

# 738.15 — Pointer Hover

```axiom
pointer_state {
    position
    buttons
    modifiers
    target
}
```

AXUI resolve target từ visual tree/hit testing.

---

# 738.16 — Hit Testing

```axiom
hit_test(root, point)
```

phải xét:

```text
visibility
clip
transform
input_enabled
z-order
modal scope
```

---

# 738.17 — Input Routing

Input flow:

```text
AXINPUT
   ↓
AXWINDOW
   ↓
AXUI
   ↓
capture/focus/hit-test
   ↓
control
```

---

# 738.18 — Event Phases

AXUI event propagation:

```text
capture
target
bubble
```

Ví dụ:

```text
Window
 └── Panel
      └── Button
```

Input có thể đi:

```text
Window → Panel → Button
Button → Panel → Window
```

---

# 738.19 — Event Consumption

Control có thể:

```axiom
event.consume()
```

nhưng event consumption không được tự động hủy raw device event.

---

# 738.20 — Pointer Capture

```axiom
capture_pointer(node)
release_pointer(node)
```

Dùng cho:

```text
drag
resize
slider
drawing
```

---

# 738.21 — Keyboard Capture

UI có thể request keyboard capture trong focus scope.

---

# 738.22 — Gesture Recognition

AXUI có thể expose:

```text
tap
double_tap
long_press
drag
swipe
pinch
rotate
```

Raw sensor/device semantics vẫn thuộc AXINPUT.

---

# 738.23 — UI Command

Control không nên trực tiếp chứa business logic.

```axiom
ui_command {
    id
    source
    parameters
}
```

Application xử lý command.

---

# 738.24 — Action System

```axiom
ui_action {
    id
    enabled
    visible
    execute
}
```

Một action có thể được bind vào:

```text
button
menu
toolbar
keyboard shortcut
touch gesture
```

---

# 738.25 — Command Binding

```axiom
bind(button, action)
bind(menu_item, action)
bind(shortcut, action)
```

---

# 738.26 — Keyboard Shortcut

```axiom
shortcut {
    key
    modifiers
    scope
    action
}
```

Scope:

```text
global
window
focus_scope
control
```

---

# 738.27 — Layout

AXUI phải có layout engine native.

Core primitives:

```text
absolute
stack
row
column
grid
overlay
flow
constraint
```

---

# 738.28 — Layout Node

```axiom
layout_node {
    preferred_size
    minimum_size
    maximum_size
    margin
    padding
    alignment
    constraints
}
```

---

# 738.29 — Measure / Arrange

Canonical layout pipeline:

```text
measure
   ↓
resolve constraints
   ↓
arrange
   ↓
final bounds
```

---

# 738.30 — Measure

```axiom
measure(node, available_size)
```

returns:

```text
desired_size
minimum_size
maximum_size
```

---

# 738.31 — Arrange

```axiom
arrange(node, final_rect)
```

produces final geometry.

---

# 738.32 — Layout Dependency

Layout must detect invalidation:

```text
content changed
font changed
style changed
parent size changed
display scale changed
```

---

# 738.33 — Layout Invalidation

```axiom
invalidate_layout(node)
```

Không được layout lại toàn bộ application nếu chỉ một subtree thay đổi.

---

# 738.34 — Incremental Layout

AXUI ưu tiên:

```text
dirty subtree
    ↓
dependency analysis
    ↓
partial layout
```

---

# 738.35 — Layout Cache

Layout result có thể cache nếu:

```text
constraints unchanged
style unchanged
content measurement unchanged
```

---

# 738.36 — Responsive Layout

UI có thể phản ứng với:

```text
window size
display scale
orientation
available space
input mode
```

---

# 738.37 — Safe Area

AXUI nhận safe-area/insets từ platform/window layer.

Không tự suy đoán notch/cutout geometry.

---

# 738.38 — Coordinate Systems

UI phải phân biệt:

```text
window coordinates
UI logical coordinates
device pixels
display coordinates
local node coordinates
```

---

# 738.39 — DPI Scaling

UI layout hoạt động trên logical units.

Rendering chuyển logical units → physical pixels.

---

# 738.40 — Pixel Snapping

```axiom
pixel_snap(node)
```

cho phép căn chỉnh geometry vào pixel boundary.

---

# 738.41 — Fractional Scaling

AXUI phải hỗ trợ:

```text
100%
125%
150%
175%
200%
```

và các scale không nguyên.

---

# 738.42 — Style

```axiom
ui_style {
    font
    color
    background
    border
    radius
    shadow
    opacity
    spacing
}
```

---

# 738.43 — Style Resolution

Style có thể đến từ:

```text
default
theme
parent
class
state
local override
```

---

# 738.44 — Style Cascade

Ưu tiên:

```text
default
  ↓
theme
  ↓
inherited
  ↓
selector/class
  ↓
state
  ↓
local
```

Không cần sao chép toàn bộ style vào từng node.

---

# 738.45 — Style Cache

Resolved style có thể cache theo:

```text
node type
theme version
state mask
style version
```

---

# 738.46 — Theme

```axiom
ui_theme {
    id
    version
    palette
    typography
    spacing
    control_styles
}
```

---

# 738.47 — Theme Switching

Theme có thể thay đổi runtime.

```text
light
dark
high_contrast
custom
```

---

# 738.48 — System Theme

AXUI có thể query system preference nhưng không ép application sử dụng.

---

# 738.49 — Color

UI color phải hỗ trợ:

```text
sRGB
linear
HDR-aware color
alpha
```

Color conversion:

→ `AXGRAPHICS`.

---

# 738.50 — Typography

AXUI phải hỗ trợ:

```text
font family
font weight
font style
font size
line height
letter spacing
word spacing
```

---

# 738.51 — Text Model

Text là Unicode/UTF-8 native.

```axiom
ui_text {
    content
    attributes
}
```

Không sử dụng byte index như character index.

---

# 738.52 — Text Segmentation

Text engine phải phân biệt:

```text
byte
code point
grapheme cluster
word
line
```

---

# 738.53 — Text Shaping

AXUI gọi native text shaping service.

Không được giả định:

```text
1 code point = 1 glyph
```

---

# 738.54 — Glyph

```axiom
glyph_run {
    glyphs
    positions
    font
}
```

---

# 738.55 — Font Resource

Font có thể đến từ:

```text
system
application
embedded asset
remote/resource package
```

---

# 738.56 — Font Fallback

Fallback chain:

```text
primary font
 ↓
language fallback
 ↓
script fallback
 ↓
system fallback
```

---

# 738.57 — Complex Scripts

UI phải hỗ trợ shaping cho:

```text
Vietnamese
Arabic
Indic
Thai
CJK
```

và các script Unicode khác.

---

# 738.58 — Text Direction

```text
LTR
RTL
auto
```

---

# 738.59 — Bidirectional Text

AXUI phải giữ logical text order riêng với visual glyph order.

---

# 738.60 — Text Selection

```axiom
text_selection {
    anchor
    focus
}
```

Selection index phải theo text model, không theo rendered glyph count.

---

# 738.61 — Clipboard

```axiom
clipboard {
    text
    rich_text
    image
    custom_formats
}
```

Clipboard transport/platform integration thuộc platform backend.

---

# 738.62 — Text Editing

Native text editor phải hỗ trợ:

```text
insert
delete
replace
selection
copy
paste
undo
redo
IME
composition
```

---

# 738.63 — IME

AXUI phải hỗ trợ composition:

```text
composition_start
composition_update
composition_commit
composition_cancel
```

Đặc biệt quan trọng cho tiếng Việt, CJK và các hệ chữ có IME.

---

# 738.64 — Undo/Redo

```axiom
ui_edit_history {
    undo()
    redo()
}
```

History phải có transaction grouping.

---

# 738.65 — Accessibility Tree

AXUI phải tạo semantic tree riêng:

```text
visual tree
      │
      └── accessibility tree
```

Không phải mọi visual node đều cần accessibility node.

---

# 738.66 — Accessibility Role

```text
button
checkbox
textbox
heading
list
list_item
table
row
cell
dialog
menu
slider
image
progress
```

---

# 738.67 — Accessibility Properties

```axiom
accessibility_node {
    role
    name
    description
    value
    state
    actions
    bounds
}
```

---

# 738.68 — Accessibility Actions

Ví dụ:

```text
activate
expand
collapse
increment
decrement
select
scroll
edit
```

---

# 738.69 — Accessibility State

```text
disabled
selected
checked
expanded
busy
invalid
required
readonly
```

---

# 738.70 — Accessibility Focus

Accessibility focus có thể khác keyboard focus.

---

# 738.71 — Screen Reader Boundary

AXUI cung cấp semantics.

Platform accessibility backend chịu trách nhiệm tích hợp:

```text
Windows UI Automation
macOS accessibility
Android accessibility
iOS accessibility
Linux accessibility
```

---

# 738.72 — Accessibility Announcement

```axiom
announce(
    text,
    priority
)
```

---

# 738.73 — Accessibility Contrast

Theme/accessibility engine có thể kiểm tra contrast.

AXUI không tự thay đổi design nếu application chưa yêu cầu.

---

# 738.74 — Reduced Motion

```axiom
ui_environment {
    reduced_motion
    high_contrast
    text_scale
}
```

---

# 738.75 — Text Scaling

UI phải hỗ trợ text scale độc lập với display DPI.

---

# 738.76 — Control Templates

Control semantics tách khỏi visual presentation.

Ví dụ:

```text
Button
 ├── semantics
 └── template
```

Cho phép theme thay đổi visual mà không thay đổi control behavior.

---

# 738.77 — Custom Control

Developer có thể định nghĩa:

```axiom
control MyControl {
    state ...
    actions ...
    template ...
}
```

---

# 738.78 — Custom Rendering

Custom control có thể cung cấp render callback/node.

Rendering:

→ AXGRAPHICS.

---

# 738.79 — Canvas

```axiom
ui_canvas {
    primitives
    transforms
    clips
}
```

Canvas là UI primitive, không thay thế AXGRAPHICS.

---

# 738.80 — Image

```axiom
ui_image {
    source
    fit
    alignment
    sampling
}
```

Image resource có thể đến từ `AXMEDIA`/`AXASSET`.

---

# 738.81 — Video

Video control:

```text
AXUI
 ↓
AXMEDIA
 ↓
AXGRAPHICS
```

AXUI chỉ quản lý presentation control.

---

# 738.82 — Audio Feedback

UI event có thể trigger audio action:

```text
click
notification
error
focus
```

Audio rendering:

→ `AXAUDIO`.

---

# 738.83 — Animation

```axiom
ui_animation {
    property
    start
    end
    duration
    easing
}
```

---

# 738.84 — Animation Timeline

Animation phải có timeline riêng:

```text
start
update
complete
cancel
```

---

# 738.85 — Easing

```text
linear
step
cubic
spring
custom
```

---

# 738.86 — Animation Clock

Có thể dùng:

```text
real-time
display-synchronized
simulation-time
manual-time
```

---

# 738.87 — Deterministic Animation

Test mode:

```axiom
ui_clock.manual()
ui_clock.advance(duration)
```

cho phép deterministic replay.

---

# 738.88 — UI State Machine

Control phức tạp có thể sử dụng:

```axiom
ui_state_machine {
    states
    transitions
    actions
}
```

---

# 738.89 — Data Binding

AXUI hỗ trợ typed binding:

```axiom
bind(
    ui.text,
    model.name
)
```

---

# 738.90 — Binding Direction

```text
one_way
two_way
one_time
command
```

---

# 738.91 — Binding Safety

Binding không được tạo implicit global dependency.

---

# 738.92 — Reactive Updates

Model change:

```text
model
 ↓
dependency graph
 ↓
dirty UI nodes
 ↓
layout/render
```

---

# 738.93 — Dependency Graph

AXUI phải tránh re-render toàn tree khi một value nhỏ thay đổi.

---

# 738.94 — UI Virtualization

Các control lớn:

```text
list
grid
table
tree
```

phải hỗ trợ virtualization.

Ví dụ:

```text
1,000,000 rows
        ↓
visible rows only
        ↓
small control set
```

---

# 738.95 — Virtualized List

```axiom
virtual_list {
    item_count
    item_builder
    item_measure
}
```

---

# 738.96 — Virtualized Table

```axiom
virtual_table {
    rows
    columns
    cell_builder
}
```

---

# 738.97 — Scrolling

```axiom
scroll_state {
    offset
    viewport
    content_size
}
```

---

# 738.98 — Scroll Physics

Có thể hỗ trợ:

```text
instant
smooth
momentum
spring
```

---

# 738.99 — Menu

```axiom
menu {
    items
    shortcuts
    submenus
}
```

---

# 738.100 — Dialog

```axiom
dialog {
    content
    modality
    buttons
    result
}
```

Dialog result phải typed:

```axiom
result := dialog.show()
```

---

# 738.101 — Modal Boundary

Modal dialog thuộc UI/window semantics.

Window modality implementation:

→ AXWINDOW.

---

# 738.102 — Notification

```axiom
ui_notification {
    title
    message
    severity
    actions
}
```

---

# 738.103 — Severity

```text
info
success
warning
error
```

Không đồng nghĩa với security severity.

---

# 738.104 — Form

```axiom
ui_form {
    fields
    validation
    submission
}
```

---

# 738.105 — Validation

Validation có thể là:

```text
syntax
format
range
required
application rule
```

AXUI chỉ hiển thị kết quả validation; domain authority thuộc application/domain runtime.

---

# 738.106 — Error Presentation

```axiom
field_error {
    field
    message
    severity
}
```

---

# 738.107 — Localization

AXUI phải hỗ trợ:

```text
locale
language
region
calendar
number format
date format
plural rules
```

---

# 738.108 — Localization Resource

```axiom
localized_string {
    key
    locale
    value
}
```

---

# 738.109 — Text Expansion

Layout không được giả định bản dịch có cùng chiều dài.

---

# 738.110 — RTL Layout

Layout engine phải hỗ trợ:

```text
LTR
RTL
inherit
```

---

# 738.111 — Locale-Aware Formatting

Formatting:

```text
number
currency
date
time
measurement
```

nên gọi appropriate runtime service thay vì tự hard-code.

---

# 738.112 — UI Resource

UI resource có thể là:

```text
style
font
image
icon
string
animation
template
```

---

# 738.113 — Resource Lifetime

Resource lifetime phải tách khỏi node lifetime.

```text
1000 buttons
       ↓
shared icon resource
```

---

# 738.114 — Icon

```axiom
ui_icon {
    source
    size
    tint
}
```

---

# 738.115 — Vector Icon

Có thể giữ vector representation để scale không mất chất lượng.

---

# 738.116 — Render Tree

Visual tree không nhất thiết bằng render tree.

```text
UI Tree
   ↓
style/layout
   ↓
render tree
   ↓
AXGRAPHICS
```

---

# 738.117 — Render Tree Optimization

Có thể:

```text
merge
flatten
cache
clip
batch
```

---

# 738.118 — Render Cache

Cache được phép nếu node không thay đổi.

Invalidation:

```text
content
style
transform
clip
resource
display scale
```

---

# 738.119 — Dirty Regions

AXUI phải hỗ trợ dirty-region rendering:

```text
changed node
 ↓
bounding region
 ↓
union
 ↓
partial redraw
```

---

# 738.120 — Full Redraw

Full redraw vẫn được phép khi:

```text
GPU backend requires
massive tree change
simple embedded target
```

---

# 738.121 — Compositor Boundary

AXUI tạo render content.

Compositor:

→ `AXWINDOW` / platform graphics stack.

---

# 738.122 — Surface

UI root có thể render vào:

```text
window surface
offscreen surface
texture
image
headless target
```

---

# 738.123 — GPU Integration

AXUI có thể tạo:

```text
draw commands
glyph resources
texture resources
clip operations
```

nhưng GPU execution:

→ `AXGRAPHICS`.

---

# 738.124 — CPU Fallback

Nếu GPU unavailable:

```text
AXUI
 ↓
CPU renderer
```

phải tồn tại cho:

```text
headless
testing
embedded
software rendering
```

---

# 738.125 — GPU/CPU Selection

Không phải lúc nào GPU cũng nhanh hơn.

Selection có thể dựa trên:

```text
tree size
dirty area
animation
device capability
transfer cost
latency
```

---

# 738.126 — UI Thread

AXUI có một logical UI execution context.

Không nhất thiết map 1:1 với OS thread.

---

# 738.127 — Thread Affinity

Operations liên quan đến:

```text
tree mutation
focus
layout
event routing
```

phải có defined execution context.

---

# 738.128 — Background Work

Không được block UI execution context bằng:

```text
filesystem
database
network
long compute
model inference
```

Các subsystem tương ứng:

→ `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXCOMPUTE`.

---

# 738.129 — Async UI Update

Background task:

```text
worker
 ↓
result
 ↓
UI dispatcher
 ↓
UI mutation
```

---

# 738.130 — UI Dispatcher

```axiom
ui_dispatch(fn)
```

---

# 738.131 — Frame Scheduler

UI frame pipeline:

```text
input
 ↓
state update
 ↓
layout
 ↓
animation
 ↓
render
 ↓
present
```

---

# 738.132 — Frame Budget

AXUI có thể expose:

```axiom
ui_frame_budget {
    target_duration
    deadline
}
```

---

# 738.133 — Frame Miss

Telemetry phải phân biệt:

```text
input delay
layout delay
render delay
present delay
```

---

# 738.134 — Interaction Latency

Có thể đo:

```text
input timestamp
 ↓
event dispatch
 ↓
state mutation
 ↓
render
 ↓
presentation
```

---

# 738.135 — Input Coalescing

Pointer move/touch move events có thể coalesce nếu semantics cho phép.

Không được coalesce semantic actions như:

```text
button activation
text insertion
key press
```

một cách mất mát.

---

# 738.136 — UI Automation

```axiom
ui_query(role, name)
ui_activate(node)
ui_set_value(node, value)
ui_select(node)
ui_focus(node)
```

---

# 738.137 — Stable Automation Identity

Mỗi interactive control nên có:

```axiom
automation_id
```

ổn định qua render/style changes.

---

# 738.138 — UI Testing

Test có thể:

```text
create UI
set deterministic clock
inject semantic input
assert state
capture render
```

---

# 738.139 — Snapshot Testing

```axiom
ui_snapshot(root)
```

có thể kiểm tra:

```text
tree
layout
semantics
render output
```

---

# 738.140 — Deterministic Input Replay

```text
record:
input
timestamp
focus
tree version

replay:
same event sequence
same clock
same state
```

---

# 738.141 — UI Simulation

```axiom
ui_simulation {
    clock
    input
    display
    environment
}
```

---

# 738.142 — Headless UI

Ứng dụng có thể tạo UI tree mà không cần physical display:

```text
AXUI
 ↓
headless renderer
 ↓
AXMEDIA/image
```

---

# 738.143 — Remote UI

Có thể serialize semantic UI representation để remote client render.

Tuy nhiên:

```text
UI state serialization
```

không được trở thành implicit RPC framework.

---

# 738.144 — Security Boundary

UI phải phân biệt:

```text
trusted application UI
untrusted content
system UI
security-sensitive UI
```

---

# 738.145 — Secure UI

Các control có thể yêu cầu:

```axiom
secure_input
secure_display
protected_text
```

Ví dụ password/credential input.

---

# 738.146 — Secure Input

Secure input phải ngăn các đường capture không được phép theo capability/platform policy.

---

# 738.147 — Identity Boundary

AXUI không sở hữu identity.

Có thể hiển thị:

```text
user name
avatar
account
credential status
```

nhưng authoritative identity:

→ `AXIDENTITY`.

---

# 738.148 — Permission UI

AXUI có thể render permission request.

Authorization:

→ `AXSECURITY`.

---

# 738.149 — AI UI Assistant

AI có thể cung cấp:

```text
suggestions
summaries
autocomplete
layout suggestions
accessibility suggestions
translation
content generation
```

---

# 738.150 — AI Boundary

AI output phải được coi là:

```axiom
ui_ai_suggestion
```

cho tới khi application/user chấp nhận.

AI không tự:

```text
execute arbitrary command
change security policy
grant permission
send transaction
```

---

# 738.151 — AI-Generated UI

AI có thể tạo:

```text
ui tree
style
layout
binding proposal
```

nhưng compilation/validation phải kiểm tra schema và capabilities trước khi activate.

---

# 738.152 — UI Schema

UI có thể được biểu diễn bằng typed declarative form:

```axiom
ui MainView {
    column {
        text "Axiom"
        button "Build"
        button "Run"
    }
}
```

Compiler có thể lower thành native retained UI tree.

---

# 738.153 — Imperative UI

Axiom cũng hỗ trợ:

```axiom
view := ui.create(...)
view.add(...)
view.set(...)
```

---

# 738.154 — Declarative + Imperative

Hai mô hình phải cùng target một runtime model.

Không tạo hai UI engines độc lập.

---

# 738.155 — UI Compiler

Compiler có thể precompute:

```text
static layout
static styles
static resource references
static accessibility metadata
```

---

# 738.156 — Compile-Time UI Optimization

Có thể loại bỏ:

```text
unused controls
unused themes
unused styles
unused assets
```

nếu semantics cho phép.

---

# 738.157 — Native Widget Backend

Một control có thể:

```text
Axiom-rendered
native-platform-backed
hybrid
```

Ví dụ text input cần IME/accessibility native integration.

---

# 738.158 — Native vs Custom Control

Không được để application phải biết platform-specific widget API để dùng UI cơ bản.

---

# 738.159 — Platform Adapter

```text
AXUI
 ↓
platform adapter
 ↓
Windows
Linux
macOS
Android
iOS
embedded
```

---

# 738.160 — UI Persistence

AXUI có thể lưu:

```text
window-independent UI state
expanded nodes
selected tabs
scroll position
user preferences
```

Storage:

→ `AXSTORAGE`.

---

# 738.161 — Session Restore

Session restore phải phân biệt:

```text
UI state
application state
window state
display state
```

---

# 738.162 — Undo Architecture

Undo có thể tồn tại ở nhiều tầng:

```text
text edit
control state
document operation
application transaction
```

AXUI chỉ sở hữu UI editing history.

---

# 738.163 — Document Integration

Editor UI:

```text
AXUI
 ↓
application document model
 ↓
AXSTORAGE / AXDATABASE
```

---

# 738.164 — Data Grid

Native data grid phải hỗ trợ:

```text
virtual rows
virtual columns
sorting
selection
editing
column resize
column reorder
frozen columns
```

Sorting/filter semantics có thể delegate cho database khi dataset lớn.

---

# 738.165 — Tree View

```axiom
tree_view {
    model
    expanded
    selected
}
```

Model không cần tồn tại toàn bộ dưới UI node.

---

# 738.166 — Selection Model

```axiom
selection_model {
    mode
    selected_items
    anchor
}
```

Modes:

```text
single
multiple
range
none
```

---

# 738.167 — Drag & Drop

```axiom
drag_session {
    source
    payload
    allowed_operations
    target
}
```

---

# 738.168 — Drag Payload

Payload có thể là:

```text
text
files
images
application objects
custom typed data
```

---

# 738.169 — Context Menu

Context menu target phải được xác định bởi hit-test/focus context.

---

# 738.170 — Tooltip

```axiom
tooltip {
    target
    content
    delay
}
```

---

# 738.171 — Cursor

Cursor visual semantics thuộc UI/window layer.

Actual device cursor:

→ `AXINPUT` / `AXWINDOW`.

---

# 738.172 — UI Audio

UI sound events:

```axiom
ui_sound_event {
    kind
    resource
}
```

Actual playback:

→ `AXAUDIO`.

---

# 738.173 — Media Controls

Media controls có thể bind vào:

→ `AXMEDIA`

nhưng control semantics vẫn thuộc AXUI.

---

# 738.174 — Error Recovery

Một control render failure không được làm crash toàn UI tree nếu có thể isolate.

---

# 738.175 — Resource Failure

Missing image/font/icon:

```text
fallback
diagnostic
placeholder
```

thay vì undefined behavior.

---

# 738.176 — Accessibility Failure

Nếu accessibility backend unavailable:

UI vẫn phải hoạt động, nhưng diagnostics phải phản ánh capability thiếu.

---

# 738.177 — Performance Hot Path

Hot path:

```text
input
 ↓
event routing
 ↓
state mutation
 ↓
layout invalidation
 ↓
render invalidation
 ↓
render
```

Không được có:

```text
reflection
generic serialization
network RPC
blocking I/O
```

---

# 738.178 — Memory Architecture

UI node phải có compact representation.

Ưu tiên:

```text
stable IDs
dense storage
index-based relationships
shared styles
shared resources
arena/pool allocation
```

thay vì mỗi node một heap allocation.

---

# 738.179 — Node Storage

Có thể sử dụng:

```axiom
ui_node_index
```

để tham chiếu node trong tree.

Native pointer chỉ là implementation detail.

---

# 738.180 — Style Storage

Styles nên intern/share:

```text
theme
style table
resolved style cache
```

---

# 738.181 — Render Batching

Các node tương thích có thể batch:

```text
text
rectangles
images
paths
```

để giảm GPU submission.

---

# 738.182 — Glyph Batching

Text renderer phải hỗ trợ glyph atlas/cache.

---

# 738.183 — Texture Cache

Image resources có thể được GPU-cache.

Cache eviction phải không làm thay đổi semantic UI state.

---

# 738.184 — Layout Complexity

Layout engine phải cung cấp complexity expectations.

Không cho phép một control đơn giản vô tình gây O(N²) toàn tree.

---

# 738.185 — Virtualization Performance

Large collections phải có đường đi:

```text
O(visible_items)
```

hoặc gần tương đương thay vì:

```text
O(total_items)
```

trong rendering hot path.

---

# 738.186 — Async Data

UI collection có thể nhận incremental data:

```text
loading
partial
complete
error
```

---

# 738.187 — Cancellation

Async UI-bound operation phải hỗ trợ cancellation.

---

# 738.188 — Backpressure

Streaming data vào UI phải có backpressure.

UI không được buộc render mọi update nếu producer nhanh hơn frame rate.

---

# 738.189 — Update Coalescing

Ví dụ:

```text
1000 model updates
        ↓
coalesce
        ↓
1 UI frame
```

nếu semantics cho phép.

---

# 738.190 — UI Telemetry

Có thể ghi:

```text
frame time
layout time
render time
input latency
node count
dirty nodes
draw calls
glyph count
texture memory
```

---

# 738.191 — UI Diagnostics

```axiom
ui_diagnostics {
    tree_stats
    layout_stats
    render_stats
    input_stats
    accessibility_stats
}
```

---

# 738.192 — Debug Inspector

Native inspector có thể expose:

```text
visual tree
layout bounds
styles
semantics
accessibility tree
render nodes
event routing
```

---

# 738.193 — Debug Overlay

```axiom
ui_debug_overlay {
    bounds
    hit_regions
    layout_constraints
    dirty_regions
    frame_stats
}
```

---

# 738.194 — Production Removal

Debug inspector/overlay phải có thể loại bỏ khỏi release binary.

---

# 738.195 — UI Recording

Recorder có thể lưu:

```text
input events
UI state transitions
focus
commands
layout versions
theme changes
```

---

# 738.196 — UI Replay

Replay phải dùng:

```text
deterministic clock
deterministic input
controlled environment
```

---

# 738.197 — Render Reproducibility

Rendering snapshot có thể không bit-identical trên mọi GPU.

AXUI phải phân biệt:

```text
semantic equality
layout equality
pixel equality
```

---

# 738.198 — Semantic Snapshot

```axiom
ui_semantic_snapshot(root)
```

kiểm tra:

```text
roles
names
states
values
hierarchy
```

---

# 738.199 — Layout Snapshot

```axiom
ui_layout_snapshot(root)
```

kiểm tra:

```text
bounds
transforms
visibility
clip
```

---

# 738.200 — Native API

```axiom
ui_create_root()
ui_destroy_root()

ui_create_node()
ui_destroy_node()

ui_attach()
ui_detach()
ui_reparent()

ui_set_style()
ui_get_style()

ui_measure()
ui_arrange()
ui_invalidate_layout()

ui_hit_test()

ui_focus()
ui_capture_pointer()
ui_release_pointer()

ui_dispatch_event()

ui_bind()
ui_unbind()

ui_create_theme()
ui_set_theme()

ui_create_animation()
ui_start_animation()
ui_stop_animation()

ui_create_dialog()
ui_show_dialog()

ui_create_menu()

ui_set_accessibility()
ui_get_accessibility_tree()

ui_set_clipboard()
ui_get_clipboard()

ui_snapshot()
ui_semantic_snapshot()
ui_layout_snapshot()

ui_record()
ui_replay()

ui_get_diagnostics()
ui_debug_overlay()

ui_render()
```

---

# 738.201 — Canonical Flow: Button Click

```text
AXINPUT
   ↓
pointer event
   ↓
AXWINDOW
   ↓
AXUI
   ↓
hit-test
   ↓
button
   ↓
capture/target/bubble
   ↓
action
   ↓
application
   ↓
state change
   ↓
UI invalidation
   ↓
layout/render
   ↓
AXGRAPHICS
```

---

# 738.202 — Canonical Flow: Text Input

```text
keyboard/IME
      ↓
AXINPUT
      ↓
AXUI focus
      ↓
text control
      ↓
composition
      ↓
text model
      ↓
selection/edit history
      ↓
layout
      ↓
glyph shaping
      ↓
render
```

---

# 738.203 — Canonical Flow: Responsive Layout

```text
display/window change
       ↓
AXWINDOW / AXDISPLAY
       ↓
UI viewport update
       ↓
layout invalidation
       ↓
measure
       ↓
arrange
       ↓
render
```

---

# 738.204 — Canonical Flow: Accessibility

```text
UI tree
   ↓
semantic projection
   ↓
accessibility tree
   ↓
platform adapter
   ↓
screen reader / assistive technology
```

---

# 738.205 — Canonical Flow: Virtualized List

```text
dataset
   ↓
item count
   ↓
viewport
   ↓
visible range
   ↓
virtual controls
   ↓
layout
   ↓
render
```

---

# 738.206 — Canonical Flow: Declarative UI

```text
Axiom source
     ↓
UI compiler
     ↓
typed UI representation
     ↓
static optimization
     ↓
AXUI runtime
     ↓
layout/style/render
```

---

# 738.207 — Canonical Flow: UI → GPU

```text
UI tree
   ↓
style
   ↓
layout
   ↓
render tree
   ↓
batching
   ↓
AXGRAPHICS
   ↓
GPU
   ↓
AXWINDOW surface
   ↓
AXDISPLAY
```

---

# 738.208 — Formal Invariants

```text
UI-INV-01   Every UI node has a stable runtime identity.
UI-INV-02   UI identity is distinct from memory address.
UI-INV-03   Visual tree hierarchy is explicit.
UI-INV-04   Node ownership is explicit.
UI-INV-05   UI lifecycle states are explicit.
UI-INV-06   Application state is distinct from UI state.
UI-INV-07   Visual tree is distinct from render tree.
UI-INV-08   Accessibility tree is distinct from visual tree.
UI-INV-09   Control semantics are distinct from visual templates.
UI-INV-10   Raw device input is distinct from UI semantic events.

UI-INV-11   Focus is explicit.
UI-INV-12   Focus scope is explicit.
UI-INV-13   Pointer capture is explicit.
UI-INV-14   Event propagation order is deterministic.
UI-INV-15   Event consumption is explicit.
UI-INV-16   Hit testing respects visibility and clipping.
UI-INV-17   UI coordinate spaces are explicit.
UI-INV-18   Logical units are distinct from physical pixels.
UI-INV-19   Display scale is not silently treated as DPI.
UI-INV-20   Layout invalidation is explicit.

UI-INV-21   Measure and arrange are distinct phases.
UI-INV-22   Layout may be incremental.
UI-INV-23   Layout results may be cached only while dependencies remain valid.
UI-INV-24   Style resolution is versioned.
UI-INV-25   Shared styles do not require per-node duplication.
UI-INV-26   Theme identity is explicit.
UI-INV-27   Theme changes invalidate dependent style state.
UI-INV-28   Text uses Unicode-aware semantics.
UI-INV-29   Byte offsets are distinct from text character semantics.
UI-INV-30   Visual glyph order is distinct from logical text order.

UI-INV-31   Accessibility semantics are explicit.
UI-INV-32   Accessibility focus may differ from keyboard focus.
UI-INV-33   UI automation identities are stable.
UI-INV-34   Virtualized collections need not instantiate every logical item.
UI-INV-35   UI updates may be coalesced without losing required semantic events.
UI-INV-36   Background work cannot silently mutate UI state outside the UI execution context.
UI-INV-37   AI-generated UI is untrusted until validated and authorized.
UI-INV-38   Secure UI operations are capability-controlled.
UI-INV-39   UI simulation cannot mutate production application state.
UI-INV-40   UI replay preserves deterministic semantic event ordering.
```

---

# 738.209 — Performance Architecture

AXUI phải ưu tiên:

```text
dense node storage
shared styles
shared resources
incremental layout
incremental rendering
virtualized collections
dirty regions
render batching
glyph caching
texture caching
zero-copy resources
GPU acceleration
CPU fallback
compile-time specialization
```

Đường nóng:

```text
INPUT
  ↓
STATE
  ↓
LAYOUT INVALIDATION
  ↓
RENDER INVALIDATION
  ↓
BATCH
  ↓
GPU
```

Không được phụ thuộc vào:

```text
reflection
JSON
dynamic serialization
RPC
heap allocation per event
blocking I/O
```

---

# 738.210 — Axiom UI Syntax Target

Một declarative syntax mục tiêu:

```axiom
ui MainWindow {
    column {
        text "Axiom"

        row {
            button "Build" on_click build
            button "Run"  on_click run
        }

        table results {
            virtualized true
            columns [
                "Name",
                "Status",
                "Duration"
            ]
        }
    }
}
```

Compiler có thể lower thành native UI structures thay vì runtime parse text.

---

# 738.211 — Definition of Done

```text
BOOTSTRAP-738
STATUS: COMPLETE / FROZEN

AXUI
 ├── UI Root
 ├── Visual Tree
 ├── Node Identity
 ├── Node Lifecycle
 ├── Controls
 ├── Control State
 ├── Focus
 ├── Focus Scope
 ├── Hit Testing
 ├── Event Routing
 ├── Pointer Capture
 ├── Keyboard Handling
 ├── Gesture Semantics
 ├── Actions
 ├── Commands
 ├── Shortcuts
 ├── Layout
 ├── Measure / Arrange
 ├── Incremental Layout
 ├── Responsive Layout
 ├── Coordinate Spaces
 ├── Styling
 ├── Themes
 ├── Typography
 ├── Unicode Text
 ├── Text Shaping
 ├── IME
 ├── Text Editing
 ├── Clipboard
 ├── Accessibility
 ├── Localization
 ├── Animation
 ├── Data Binding
 ├── Reactive Updates
 ├── Virtualization
 ├── Scrolling
 ├── Menus
 ├── Dialogs
 ├── Forms
 ├── Tables
 ├── Trees
 ├── Drag & Drop
 ├── Media Controls
 ├── Native Widgets
 ├── Custom Controls
 ├── Render Tree
 ├── Dirty Regions
 ├── GPU Rendering
 ├── CPU Fallback
 ├── UI Thread Model
 ├── Async Updates
 ├── UI Automation
 ├── UI Testing
 ├── Deterministic Replay
 ├── Headless UI
 ├── Secure UI
 ├── AI UI Boundary
 ├── UI Compiler
 ├── Performance Runtime
 ├── Diagnostics
 ├── 40 Formal Invariants
 └── User Interface Runtime 5.0
```

**BOOTSTRAP-738 / AXUI — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-739 — AXCOMPOSITOR

**Native Composition & Presentation Runtime — visual surface composition, scene composition, layer tree, clipping, transforms, opacity, blending, z-order, damage tracking, occlusion, window composition, display composition, hardware overlays, GPU composition, CPU fallback, frame scheduling, presentation synchronization, multi-surface composition, HDR composition, color-space propagation, protected surfaces, remote composition, capture boundaries, deterministic composition, compositor transactions, composition telemetry và Composition Runtime 5.0.**