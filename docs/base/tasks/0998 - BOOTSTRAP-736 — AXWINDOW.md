# BOOTSTRAP-736 — AXWINDOW

**Namespace:** `AXWINDOW`  
**Phase:** Axiom Civilization Runtime / Native Window & Display Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXUI`, `AXGRAPHICS`, `AXINPUT`, `AXMEDIA`, `AXAUDIO`, `AXCOMPUTE`, `AXSTORAGE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

> `AXWINDOW` là lớp native quản lý **cửa sổ, màn hình, display topology, surface, DPI, fullscreen, z-order, focus và lifecycle của visual application**. `AXUI` quản lý nội dung giao diện; `AXWINDOW` quản lý nơi giao diện tồn tại và cách nó tương tác với window/display system.

---

# 736.0 — Mục tiêu

AXWINDOW phải cung cấp một abstraction thống nhất cho:

```text
Desktop
Laptop
Multi-monitor
Mobile display
Embedded display
Fullscreen application
Borderless application
Tool window
Popup
Dialog window
Offscreen surface
Headless surface
Remote display
Virtual display
```

Kiến trúc:

```text
                         AXWINDOW
                            │
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
       DISPLAYS           WINDOWS           SURFACES
          │                 │                 │
          ↓                 ↓                 ↓
      topology           lifecycle        rendering
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ↓
                         COMPOSITOR
                            │
                    AXGRAPHICS / OS
```

---

# 736.1 — Boundary

AXWINDOW sở hữu:

```text
window identity
window lifecycle
display enumeration
display topology
window positioning
window sizing
fullscreen
minimize/maximize
z-order
focus activation
window state
surface attachment
DPI/scaling
refresh/display mode
HDR/color-space metadata
cursor confinement
display synchronization
window capture
headless surfaces
window security boundary
```

Không sở hữu:

```text
UI widgets            → AXUI
raw input             → AXINPUT
GPU rendering         → AXGRAPHICS
audio                 → AXAUDIO
media decoding        → AXMEDIA
identity              → AXIDENTITY
security primitives   → AXSECURITY
physical display asset→ AXASSET
```

---

# 736.2 — Window Model

```axiom
window {
    id
    surface
    display
    bounds
    state
    style
    flags
    focus
}
```

---

# 736.3 — Window Identity

```axiom
window_id
```

Phải phân biệt:

```text
AX window ID
OS native handle
surface ID
process ID
application ID
```

OS handle không được làm persistent Axiom identity.

---

# 736.4 — Window Lifecycle

```text
CREATED
INITIALIZING
READY
VISIBLE
HIDDEN
MINIMIZED
SUSPENDED
RESUMING
CLOSING
CLOSED
```

Transition phải explicit.

---

# 736.5 — Window Creation

```axiom
create_window(
    descriptor
)
```

Descriptor:

```axiom
window_descriptor {
    title
    size
    position
    style
    display
    flags
}
```

---

# 736.6 — Window Styles

```text
normal
borderless
tool
dialog
popup
transparent
overlay
fullscreen
embedded
```

---

# 736.7 — Window Flags

```text
resizable
movable
closable
minimizable
maximizable
always_on_top
focusable
accepts_input
transparent
decorated
```

---

# 736.8 — Window Bounds

```axiom
window_bounds {
    position
    size
}
```

Phải phân biệt:

```text
outer bounds
client bounds
content bounds
frame bounds
```

---

# 736.9 — Coordinate Spaces

AXWINDOW định nghĩa:

```text
screen
display
window
client
surface
```

AXUI định nghĩa thêm logical UI coordinates.

---

# 736.10 — Window Position

```axiom
set_window_position(
    window,
    position
)
```

Backend có thể từ chối hoặc điều chỉnh position theo platform policy.

---

# 736.11 — Window Size

```axiom
set_window_size(
    window,
    size
)
```

Application có thể chỉ định:

```text
minimum
preferred
maximum
```

---

# 736.12 — Resize Constraints

```axiom
window_constraints {
    minimum_size
    maximum_size
    aspect_ratio
}
```

---

# 736.13 — Aspect Ratio

```axiom
aspect_ratio {
    numerator
    denominator
}
```

Không dùng floating-point làm canonical ratio.

---

# 736.14 — Resize Event

```axiom
window_resize_event {
    old_size
    new_size
    timestamp
}
```

Resize có thể xảy ra ngoài application request.

---

# 736.15 — Move Event

```axiom
window_move_event {
    old_position
    new_position
}
```

---

# 736.16 — Display

```axiom
display {
    id
    bounds
    work_area
    scale
    resolution
    refresh
    color
    capabilities
}
```

---

# 736.17 — Display Identity

Display identity phải phân biệt:

```text
physical display
logical display
OS display identifier
virtual display
remote display
```

---

# 736.18 — Display Topology

```axiom
display_topology {
    displays
    relationships
    primary
}
```

Ví dụ:

```text
┌───────────────┐
│   Display A   │
└───────────────┘
        │
        └──────┐
               ↓
       ┌───────────────┐
       │   Display B   │
       └───────────────┘
```

---

# 736.19 — Display Arrangement

Mỗi display có:

```text
origin
extent
rotation
scale
```

trong virtual desktop coordinate space.

---

# 736.20 — Primary Display

```axiom
get_primary_display()
```

Primary display là platform concept, không nhất thiết là display đầu tiên được enumerate.

---

# 736.21 — Work Area

```axiom
display_work_area(display)
```

Work area có thể loại trừ:

```text
taskbar
dock
system bars
reserved regions
```

---

# 736.22 — Display Scale

```axiom
display_scale {
    x
    y
}
```

Không giả định mọi display có cùng scale.

---

# 736.23 — DPI

AXWINDOW phải phân biệt:

```text
logical scale
DPI
pixel density
device pixel ratio
```

Không coi chúng là cùng một khái niệm.

---

# 736.24 — Per-Display Scaling

Một window có thể chuyển:

```text
Display A: 100%
        ↓
Display B: 200%
```

Runtime phải phát event scale change.

---

# 736.25 — Scale Event

```axiom
window_scale_event {
    old_scale
    new_scale
}
```

AXUI phải re-layout khi policy yêu cầu.

---

# 736.26 — Display Resolution

```axiom
display_resolution {
    width
    height
}
```

Resolution là physical/display mode property, không phải UI logical size.

---

# 736.27 — Refresh Rate

```axiom
refresh_rate {
    numerator
    denominator
}
```

Fractional refresh rates phải được biểu diễn chính xác.

---

# 736.28 — Variable Refresh Rate

```axiom
display_vrr {
    minimum
    maximum
}
```

AXWINDOW chỉ quản lý capability; frame scheduling thuộc AXGRAPHICS.

---

# 736.29 — Display Mode

```axiom
display_mode {
    resolution
    refresh_rate
    color_format
    hdr
}
```

---

# 736.30 — Mode Enumeration

```axiom
enumerate_display_modes(display)
```

Không được giả định mọi mode đều có thể chuyển runtime.

---

# 736.31 — Fullscreen

Modes:

```text
windowed
borderless_fullscreen
exclusive_fullscreen
```

---

# 736.32 — Fullscreen Transition

```axiom
set_fullscreen(
    window,
    mode
)
```

Platform backend quyết định availability của exclusive mode.

---

# 736.33 — Fullscreen Safety

Nếu fullscreen transition thất bại:

```text
previous window state
```

phải được khôi phục.

---

# 736.34 — Borderless Fullscreen

Borderless fullscreen là:

```text
normal window
+
display-sized bounds
+
decorations disabled
```

không nhất thiết thay đổi display mode.

---

# 736.35 — Window Decorations

```axiom
window_decorations {
    title_bar
    border
    system_buttons
}
```

---

# 736.36 — Custom Decorations

Application có thể tự render:

```text
title bar
buttons
resize areas
```

nhưng AXWINDOW vẫn sở hữu native hit/resize policy nếu platform yêu cầu.

---

# 736.37 — Minimize

```axiom
minimize_window(window)
```

---

# 736.38 — Maximize

```axiom
maximize_window(window)
```

---

# 736.39 — Restore

```axiom
restore_window(window)
```

Runtime phải lưu state trước khi maximize/fullscreen nếu platform cho phép.

---

# 736.40 — Visibility

```axiom
show_window(window)
hide_window(window)
```

Visibility không đồng nghĩa với focus.

---

# 736.41 — Focus

```axiom
focus_window(window)
```

Phải phân biệt:

```text
focused
active
visible
foreground
```

---

# 736.42 — Activation

```axiom
activate_window(window)
```

OS có thể từ chối activation để ngăn focus stealing.

---

# 736.43 — Focus Policy

AXWINDOW không được mặc định cưỡng ép application lên foreground.

---

# 736.44 — Z-Order

```axiom
window_z_order {
    layer
    position
}
```

Layers:

```text
normal
topmost
system
popup
overlay
```

Actual system restrictions vẫn thuộc platform.

---

# 736.45 — Always On Top

```axiom
set_always_on_top(
    window,
    true
)
```

Đây là requested state, không phải guaranteed state.

---

# 736.46 — Parent / Owner

Phân biệt:

```text
parent window
owner window
child window
modal owner
```

---

# 736.47 — Window Hierarchy

```text
Application
 ├── Main Window
 │    ├── Tool Window
 │    └── Popup
 └── Dialog
```

AXWINDOW quản lý hierarchy; AXUI quản lý content hierarchy.

---

# 736.48 — Modal Window

```axiom
window_modal {
    owner
    scope
}
```

Modal window giới hạn interaction theo policy.

---

# 736.49 — Popup Window

```axiom
popup_window {
    owner
    anchor
    placement
}
```

---

# 736.50 — Tool Window

Tool window:

```text
inspector
debugger
properties
terminal
```

có lifecycle độc lập nhưng thường gắn với owner.

---

# 736.51 — Embedded Window

Một surface có thể embedded vào:

```text
AXUI
AXGRAPHICS
another window
external host
```

---

# 736.52 — Window Surface

```axiom
window_surface {
    window
    graphics_surface
    size
    format
}
```

AXGRAPHICS sở hữu rendering semantics.

---

# 736.53 — Surface Attachment

```axiom
attach_surface(
    window,
    surface
)
```

Một surface không nhất thiết luôn gắn với một window.

---

# 736.54 — Surface Detachment

```axiom
detach_surface(window)
```

Window có thể tồn tại trước khi surface được attach.

---

# 736.55 — Offscreen Surface

```axiom
offscreen_surface {
    size
    format
}
```

Dùng cho:

```text
render-to-texture
thumbnail
remote rendering
testing
```

---

# 736.56 — Headless Window

```axiom
headless_window {
    surface
}
```

Không yêu cầu physical display.

---

# 736.57 — Remote Window

AXWINDOW có thể biểu diễn:

```axiom
remote_window {
    endpoint
    surface
}
```

Network transport:

→ AXNETWORK.

Remote desktop protocol semantics không thuộc core AXWINDOW.

---

# 736.58 — Virtual Display

```axiom
virtual_display {
    resolution
    scale
    refresh
}
```

Dùng cho:

```text
testing
streaming
remote desktop
simulation
```

---

# 736.59 — Display Capture

```axiom
capture_display(display)
capture_window(window)
capture_surface(surface)
```

Capture output là media/image data:

→ AXMEDIA / AXGRAPHICS.

---

# 736.60 — Capture Security

Display/window capture có thể chứa:

```text
password
private documents
personal data
```

AXWINDOW phải expose security metadata; AXSECURITY quyết định authorization.

---

# 736.61 — Protected Window

```axiom
window_security {
    capture_policy
    screenshot_policy
    overlay_policy
}
```

---

# 736.62 — Cursor

AXWINDOW quản lý cursor/display relationship:

```axiom
cursor {
    shape
    visibility
    position
}
```

Raw pointer:

→ AXINPUT.

---

# 736.63 — Cursor Visibility

```axiom
show_cursor()
hide_cursor()
```

---

# 736.64 — Cursor Confinement

```axiom
confine_cursor(
    window,
    region
)
```

Thường dùng cho:

```text
games
3D viewport
remote control
```

---

# 736.65 — Relative Pointer Mode

```axiom
set_relative_pointer_mode(window)
```

Pointer movement có thể được cung cấp dưới dạng delta thay vì absolute coordinates.

---

# 736.66 — Window Icon

```axiom
window_icon {
    image
    scale
}
```

AXMEDIA/AXASSET cung cấp underlying resource.

---

# 736.67 — Window Title

```axiom
set_window_title(
    window,
    text
)
```

Title là display metadata, không phải UI content.

---

# 736.68 — Window State Snapshot

```axiom
window_snapshot {
    bounds
    state
    display
    scale
    z_order
}
```

---

# 736.69 — Persistent Window State

Application có thể lưu:

```text
position
size
display
maximized
```

qua AXSTORAGE.

AXWINDOW không tự quyết định persistence policy.

---

# 736.70 — Multi-Window Session

```axiom
window_session {
    application
    windows
    displays
    focus
}
```

---

# 736.71 — Session Restore

```axiom
restore_window_session()
```

Nếu display cũ không còn:

```text
fallback placement
```

phải được áp dụng.

---

# 736.72 — Safe Placement

Window không nên restore vào vùng hoàn toàn inaccessible.

```axiom
ensure_visible(window)
```

---

# 736.73 — Virtual Desktop

Desktop OS có thể có:

```text
workspace
virtual_desktop
desktop_space
```

AXWINDOW biểu diễn capability nếu backend hỗ trợ.

---

# 736.74 — Workspace

```axiom
window_workspace {
    id
    name
}
```

Một window có thể được gắn vào workspace theo platform semantics.

---

# 736.75 — Window Groups

```axiom
window_group {
    windows
    policy
}
```

Ví dụ:

```text
IDE
 ├── Editor
 ├── Terminal
 └── Inspector
```

---

# 736.76 — Snap / Tiling

AXWINDOW có thể expose:

```text
snap_left
snap_right
snap_top
tile
cascade
```

Nhưng desktop compositor vẫn là authority.

---

# 736.77 — Window Placement Policy

```axiom
window_placement_policy {
    preferred_display
    preferred_region
    fallback
}
```

---

# 736.78 — Safe Area

Mobile/embedded:

```axiom
display_safe_area {
    top
    right
    bottom
    left
}
```

AXUI sử dụng để layout.

---

# 736.79 — System Insets

```axiom
display_insets {
    status_bar
    navigation_bar
    notch
    gesture_region
}
```

---

# 736.80 — Orientation

```axiom
display_orientation {
    rotation
    orientation
}
```

Window có thể nhận orientation change event.

---

# 736.81 — Display Rotation

```text
0°
90°
180°
270°
```

Rotation metadata phải độc lập với UI layout.

---

# 736.82 — Color Space

```axiom
display_color_space {
    primaries
    transfer
    white_point
}
```

---

# 736.83 — HDR

```axiom
display_hdr {
    supported
    format
    peak_luminance
}
```

AXWINDOW mô tả capability; AXGRAPHICS chịu trách nhiệm rendering.

---

# 736.84 — SDR/HDR Transition

Khi display mode thay đổi:

```text
display event
 ↓
color capability changed
 ↓
window notified
 ↓
AXGRAPHICS adapts
```

---

# 736.85 — Color Management

AXWINDOW cung cấp display metadata:

```text
display profile
color space
HDR capability
```

Không tự thực hiện pixel conversion.

---

# 736.86 — VSync Relationship

AXWINDOW expose:

```axiom
display_sync_info {
    refresh_rate
    sync_mode
}
```

Actual frame scheduling:

→ AXGRAPHICS.

---

# 736.87 — Presentation

```axiom
present_window(window)
```

AXWINDOW cung cấp surface/presentation target; graphics backend thực hiện command submission.

---

# 736.88 — Presentation Result

```axiom
presentation_result {
    timestamp
    presented
    mode
}
```

---

# 736.89 — Frame Pacing

AXWINDOW phải cho phép runtime biết:

```text
display refresh
presentation timing
```

nhưng không ép application vào một rendering strategy.

---

# 736.90 — Window Events

```text
created
shown
hidden
moved
resized
focused
unfocused
minimized
maximized
restored
fullscreen_changed
display_changed
scale_changed
closed
```

---

# 736.91 — Event Timestamp

Mỗi event phải có:

```axiom
window_event {
    timestamp
    clock_domain
}
```

---

# 736.92 — Event Queue

```axiom
window_event_queue {
    capacity
    policy
}
```

Overflow behavior phải explicit.

---

# 736.93 — Event Coalescing

Có thể coalesce:

```text
move
resize
scale
pointer-related window events
```

nhưng application có thể yêu cầu raw delivery nếu backend hỗ trợ.

---

# 736.94 — Window Threading

Window operations có thể yêu cầu:

```text
UI thread
platform thread
main thread
```

AXWINDOW phải biểu diễn thread-affinity contract của backend.

---

# 736.95 — Nonblocking API

Các operation không cần thiết phải block:

```axiom
request_resize()
request_close()
request_focus()
```

Backend event sau đó xác nhận kết quả.

---

# 736.96 — Close Request

```axiom
window_close_request {
    window
}
```

Application có thể:

```text
accept
cancel
defer
```

---

# 736.97 — Close Lifecycle

```text
close_requested
       ↓
application decision
       ↓
closing
       ↓
closed
```

---

# 736.98 — Forced Close

OS có thể force termination.

AXWINDOW không được giả định application luôn có cơ hội cleanup.

---

# 736.99 — Suspend

Mobile/embedded có thể:

```text
window
 ↓
suspend
 ↓
surface released
```

Application state phải thuộc application/runtime layer.

---

# 736.100 — Resume

```text
resume
 ↓
display re-evaluate
 ↓
surface recreate
 ↓
UI reattach
```

---

# 736.101 — Device Loss

GPU/display device có thể mất.

AXWINDOW phải phân biệt:

```text
window still exists
surface lost
graphics device lost
display changed
```

AXGRAPHICS xử lý GPU recovery.

---

# 736.102 — Window Recreation

Backend có thể cần recreate native surface:

```text
old surface
   ↓
detach
   ↓
new surface
   ↓
attach
```

Window identity vẫn có thể giữ nguyên.

---

# 736.103 — Native Handle

```axiom
native_window_handle(window)
```

Handle phải:

```text
borrowed
backend-specific
non-portable
lifetime-bound
```

---

# 736.104 — Native Handle Safety

Không được giả định:

```text
Windows HWND == Linux handle == Android surface
```

Axiom chỉ cung cấp opaque native handle.

---

# 736.105 — Platform Backend

```axiom
window_backend {
    create
    destroy
    show
    hide
    move
    resize
    focus
    fullscreen
    enumerate_displays
    create_surface
}
```

---

# 736.106 — Backend Implementations

Có thể có:

```text
Windows
Linux
macOS
Android
iOS
Embedded
Web
Headless
Remote
```

Core AXWINDOW không phụ thuộc một platform toolkit.

---

# 736.107 — Mobile Window Model

Mobile có thể chỉ có một application surface.

AXWINDOW vẫn giữ abstraction:

```text
application
surface
display
lifecycle
```

mà không ép mobile phải mô phỏng desktop windows.

---

# 736.108 — Embedded Model

Embedded có thể:

```text
one display
one surface
no compositor
no window manager
```

AXWINDOW phải cho phép configuration cực nhỏ.

---

# 736.109 — Server / Headless

```text
no display
no physical window
offscreen surface
```

vẫn có thể sử dụng:

```text
AXUI
AXGRAPHICS
```

cho testing/rendering.

---

# 736.110 — Remote Rendering

```text
AXUI
 ↓
AXWINDOW surface
 ↓
AXGRAPHICS
 ↓
encode
 ↓
AXMEDIA / AXNETWORK
```

AXWINDOW không sở hữu video transport.

---

# 736.111 — Window Streaming

Window capture có thể được stream qua AXNETWORK.

Metadata:

```text
window id
frame timestamp
display scale
color space
```

---

# 736.112 — Window Security

Window capability có thể bao gồm:

```text
create
modify
focus
capture
enumerate
inject_input
```

AXSECURITY kiểm soát authorization.

---

# 736.113 — Input Injection Boundary

AXWINDOW không tự động cho phép:

```text
synthetic keyboard
synthetic pointer
```

AXINPUT + AXSECURITY xử lý.

---

# 736.114 — Window Ownership

Phân biệt:

```text
application owns window
OS manages window
user controls window
```

---

# 736.115 — Cross-Process Window

Một process không được mặc định sửa window của process khác.

Nếu platform hỗ trợ:

```axiom
external_window_reference {
    handle
    capabilities
}
```

---

# 736.116 — Window Reference

External window references phải:

```text
opaque
capability-bound
revocable
non-forgeable
```

theo AXSECURITY.

---

# 736.117 — Display Permission

Một số platform có thể yêu cầu permission cho:

```text
screen capture
display enumeration
window enumeration
```

AXWINDOW phải phản ánh permission failure rõ ràng.

---

# 736.118 — Display Enumeration

```axiom
enumerate_displays()
get_display(id)
get_primary_display()
get_display_topology()
```

---

# 736.119 — Display Capabilities

```axiom
display_capabilities {
    hdr
    vrr
    touch
    pen
    color_management
    capture
}
```

---

# 736.120 — Display Input Relationship

Display có thể liên kết với:

```text
touch surface
pen digitizer
pointer
```

nhưng input ownership:

→ AXINPUT.

---

# 736.121 — Display Metadata

```axiom
display_metadata {
    manufacturer
    model
    serial_reference
    physical_size
}
```

Metadata có thể không available.

---

# 736.122 — Physical Display vs Logical Display

Một physical display có thể expose nhiều logical surfaces.

Không được coi:

```text
display_id == panel_identity
```

là invariant.

---

# 736.123 — Window State Machine

```text
             ┌──────────┐
             │ CREATED  │
             └────┬─────┘
                  ↓
             INITIALIZING
                  ↓
                READY
                  ↓
               VISIBLE
              ↙       ↘
        MINIMIZED    HIDDEN
              ↘       ↙
               VISIBLE
                  ↓
               CLOSING
                  ↓
                CLOSED
```

Fullscreen/maximized là orthogonal state hoặc mode, không nên tạo state explosion.

---

# 736.124 — Orthogonal Window State

Tách:

```text
visibility
activation
size mode
fullscreen mode
display assignment
surface state
```

thay vì một enum khổng lồ.

---

# 736.125 — Window Command

```axiom
window_command {
    type
    window
    parameters
}
```

Commands:

```text
move
resize
show
hide
minimize
maximize
restore
fullscreen
close
focus
```

---

# 736.126 — Requested vs Actual State

Cần phân biệt:

```text
requested state
actual platform state
```

Ví dụ application request:

```text
fullscreen
```

nhưng OS từ chối.

---

# 736.127 — State Observation

```axiom
get_window_state(window)
```

trả về actual state.

---

# 736.128 — Window Constraints

Platform có thể impose:

```text
minimum size
safe region
restricted placement
fullscreen policy
focus policy
```

AXWINDOW không bypass.

---

# 736.129 — Window Manager Integration

Desktop window manager có thể thay đổi:

```text
position
size
workspace
z-order
```

AXWINDOW phải coi đây là external state changes.

---

# 736.130 — Compositor Integration

```text
AXWINDOW
   ↓
compositor surface
   ↓
display
```

Compositor implementation platform-specific.

---

# 736.131 — Composition Metadata

```axiom
surface_composition {
    opacity
    transform
    clip
    z_order
}
```

Actual compositor behavior thuộc platform.

---

# 736.132 — Transparency

Window có thể request:

```text
opaque
alpha
per-pixel-alpha
color-key
```

Availability platform-dependent.

---

# 736.133 — Transparent Window Security

Transparent overlay có thể tạo clickjacking/security risks.

AXWINDOW phải expose security-relevant metadata; AXSECURITY policy quyết định.

---

# 736.134 — Overlay Window

```axiom
overlay_window {
    owner
    layer
    input_policy
}
```

Không mặc định được phép phủ lên secure/system UI.

---

# 736.135 — Display Topology Changes

Khi monitor:

```text
connected
disconnected
resolution changed
scale changed
rotation changed
```

AXWINDOW phát topology event.

---

# 736.136 — Window Migration

Nếu display biến mất:

```text
window
 ↓
display unavailable
 ↓
placement resolver
 ↓
new display
```

---

# 736.137 — Placement Resolver

```axiom
resolve_window_placement(
    window,
    topology
)
```

Policy:

```text
same display
nearest display
primary display
saved display
safe default
```

---

# 736.138 — Multi-Window Atomic Update

Application có thể yêu cầu:

```axiom
begin_window_transaction()
...
commit_window_transaction()
```

để tránh trạng thái trung gian khó quan sát.

---

# 736.139 — Window Transaction

Transaction chỉ áp dụng cho window management state, không phải database transaction.

---

# 736.140 — Window Snapshot / Restore

```axiom
capture_window_state()
restore_window_state()
```

Restore phải validate current topology trước.

---

# 736.141 — Display Simulation

```axiom
display_simulator {
    displays
    topology
    modes
    scale
}
```

Cho testing multi-monitor mà không cần physical hardware.

---

# 736.142 — Window Simulation

```axiom
window_simulator {
    windows
    events
    display_topology
}
```

---

# 736.143 — Deterministic Window Replay

Record:

```text
window events
display events
commands
timestamps
topology versions
```

để tái hiện bug.

---

# 736.144 — UI Integration

```text
AXWINDOW
   ↓
window surface
   ↓
AXUI root
   ↓
AXINPUT
```

Một window có thể chứa một hoặc nhiều UI surfaces tùy architecture.

---

# 736.145 — Graphics Integration

```text
AXWINDOW
   ↓
graphics surface
   ↓
AXGRAPHICS
   ↓
presentation
```

---

# 736.146 — Media Integration

Video playback:

```text
AXMEDIA
   ↓
media frame
   ↓
AXGRAPHICS surface
   ↓
AXWINDOW
```

---

# 736.147 — Audio Integration

Window/application lifecycle có thể phát signal:

```text
foreground
background
suspended
```

AXAUDIO dùng signal đó để áp dụng audio focus policy.

AXWINDOW không điều khiển mixer.

---

# 736.148 — Compute Integration

Heavy UI work:

```text
AXCOMPUTE
 ↓
result
 ↓
UI thread
```

Window operations không nên block vì compute task.

---

# 736.149 — Storage Integration

Window session có thể lưu:

```text
position
size
display
state
```

AXSTORAGE sở hữu persistence.

---

# 736.150 — Network Integration

Remote windows:

```text
AXNETWORK
```

chỉ là transport.

AXWINDOW vẫn sở hữu local window semantics.

---

# 736.151 — AI Window Management

AI có thể:

```text
suggest window arrangement
detect layout problems
generate responsive placement
analyze multi-monitor usage
```

Nhưng AI không tự động thay đổi secure/system window state.

---

# 736.152 — AI Boundary

AI result:

```axiom
window_ai_suggestion {
    suggestion
    confidence
    model
    provenance
}
```

Phải phân biệt:

```text
suggestion
vs
authorized window command
```

---

# 736.153 — Window Digital Twin

```axiom
window_digital_twin {
    displays
    topology
    windows
    surfaces
    focus
    states
}
```

Cho phép test desktop/mobile layouts trong simulation.

---

# 736.154 — Performance Architecture

Hot path:

```text
Display Event
      ↓
Window State
      ↓
Surface State
      ↓
AXGRAPHICS
```

Không yêu cầu:

```text
dynamic reflection
generic object graph
blocking IPC
global tree rebuild
```

---

# 736.155 — Native Fast Path

Window metadata nên dùng compact structures:

```axiom
window_fast_state {
    id
    display_id
    x
    y
    width
    height
    flags
}
```

Cold metadata tách riêng.

---

# 736.156 — Event Coalescing

Có thể coalesce:

```text
resize
move
scale
display topology
```

nhưng state cuối cùng phải chính xác.

---

# 736.157 — Zero-Copy Surface

Graphics surface nên được truyền:

```text
AXWINDOW
 ↔
AXGRAPHICS
```

bằng native handles/shared resources khi backend hỗ trợ.

Không serialize pixels giữa hai subsystem trong local process.

---

# 736.158 — Presentation Latency

AXWINDOW phải cung cấp timing information đủ để AXGRAPHICS tối ưu:

```text
submit time
presentation time
refresh interval
display timestamp
```

---

# 736.159 — Memory

Window runtime phải tránh allocation trên:

```text
resize event
move event
focus event
frame presentation
```

nếu backend có thể cung cấp fixed-size event structures.

---

# 736.160 — Compile-Time Platform Specialization

Axiom compiler có thể specialize:

```text
platform backend
window flags
surface format
display capabilities
```

khi target platform cố định.

---

# 736.161 — Native API

```axiom
create_window()
destroy_window()

show_window()
hide_window()

move_window()
resize_window()

minimize_window()
maximize_window()
restore_window()

set_fullscreen()
get_fullscreen()

focus_window()
activate_window()

set_window_title()
set_window_icon()

set_always_on_top()

attach_surface()
detach_surface()

create_surface()
destroy_surface()

enumerate_displays()
get_display()
get_primary_display()
get_display_topology()

enumerate_display_modes()

get_window_state()
get_window_bounds()

capture_window()
capture_display()
capture_surface()

show_cursor()
hide_cursor()
confine_cursor()
set_relative_pointer_mode()

create_window_session()
save_window_session()
restore_window_session()

begin_window_transaction()
commit_window_transaction()

simulate_window()
replay_window()

get_native_window_handle()
get_native_display_handle()

get_window_security()
```

---

# 736.162 — Canonical Flow: Application Start

```text
Application
    ↓
AXWINDOW.create_window()
    ↓
platform backend
    ↓
native window
    ↓
surface creation
    ↓
AXGRAPHICS attach
    ↓
AXUI attach root
    ↓
VISIBLE
```

---

# 736.163 — Canonical Flow: Multi-Monitor

```text
Display A
     │
     │ disconnect
     ↓
AXWINDOW topology event
     ↓
window placement resolver
     ↓
Display B
     ↓
scale update
     ↓
AXUI relayout
     ↓
AXGRAPHICS resize
```

---

# 736.164 — Canonical Flow: Fullscreen

```text
WINDOWED
   ↓
request fullscreen
   ↓
platform validation
   ↓
surface resize/reconfigure
   ↓
display mode if required
   ↓
AXGRAPHICS reconfigure
   ↓
FULLSCREEN
```

---

# 736.165 — Canonical Flow: Display Loss

```text
Display removed
      ↓
Window notified
      ↓
Surface unavailable
      ↓
Window state preserved
      ↓
Placement resolver
      ↓
New display
      ↓
New surface
      ↓
AXGRAPHICS recovery
      ↓
AXUI resumes
```

---

# 736.166 — Formal Invariants

```text
WIN-INV-01   Every Axiom window has a stable window identity.
WIN-INV-02   Window identity is distinct from native OS handle.
WIN-INV-03   Surface identity is distinct from window identity.
WIN-INV-04   Display identity is distinct from window identity.
WIN-INV-05   Window lifecycle transitions are explicit.
WIN-INV-06   Window visibility is distinct from focus.
WIN-INV-07   Focus is distinct from activation.
WIN-INV-08   Requested window state is distinct from actual platform state.
WIN-INV-09   Window bounds have an explicit coordinate space.
WIN-INV-10   Client bounds are distinct from outer bounds.

WIN-INV-11   Logical UI dimensions are distinct from physical pixels.
WIN-INV-12   Display scale is explicit.
WIN-INV-13   Per-display scale changes are observable.
WIN-INV-14   Display topology is versionable.
WIN-INV-15   Display removal is observable.
WIN-INV-16   Window migration after display removal is explicit.
WIN-INV-17   Display mode changes are capability-checked.
WIN-INV-18   Fullscreen state is distinct from ordinary window size.
WIN-INV-19   Borderless fullscreen is distinct from exclusive fullscreen.
WIN-INV-20   Refresh rate is represented without lossy floating-point canonicalization.

WIN-INV-21   Color-space metadata is distinct from pixel data.
WIN-INV-22   HDR capability is distinct from HDR rendering.
WIN-INV-23   VRR capability is distinct from frame scheduling.
WIN-INV-24   Presentation is distinct from rendering command generation.
WIN-INV-25   Window surfaces can be recreated without necessarily changing window identity.
WIN-INV-26   Native handles are opaque and backend-specific.
WIN-INV-27   Native handles have explicit lifetime semantics.
WIN-INV-28   Window manager changes are treated as external state changes.
WIN-INV-29   Platform policy can reject requested window operations.
WIN-INV-30   AXWINDOW cannot bypass platform security policy.

WIN-INV-31   UI content belongs to AXUI.
WIN-INV-32   Raw input belongs to AXINPUT.
WIN-INV-33   GPU rendering belongs to AXGRAPHICS.
WIN-INV-34   Audio lifecycle signals do not make AXWINDOW an audio subsystem.
WIN-INV-35   Display capture is distinct from display rendering.
WIN-INV-36   Cross-process window access requires explicit capability.
WIN-INV-37   Synthetic input injection is not implicit in window ownership.
WIN-INV-38   Headless surfaces cannot require a physical display.
WIN-INV-39   Window simulation cannot mutate production window state.
WIN-INV-40   Window replay preserves event ordering and timing semantics.
```

---

# 736.167 — Completion Criteria

`BOOTSTRAP-736` phải freeze:

1. Window identity.
2. Window lifecycle.
3. Window creation.
4. Window styles.
5. Window flags.
6. Bounds.
7. Coordinate spaces.
8. Positioning.
9. Sizing.
10. Resize constraints.
11. Aspect ratio.
12. Resize events.
13. Move events.
14. Display model.
15. Display identity.
16. Display topology.
17. Display arrangement.
18. Primary display.
19. Work area.
20. Display scale.
21. DPI semantics.
22. Per-display scaling.
23. Resolution.
24. Refresh rate.
25. VRR.
26. Display modes.
27. Fullscreen.
28. Borderless fullscreen.
29. Exclusive fullscreen.
30. Decorations.
31. Custom decorations.
32. Minimize/maximize/restore.
33. Visibility.
34. Focus.
35. Activation.
36. Z-order.
37. Always-on-top.
38. Parent/owner hierarchy.
39. Modal windows.
40. Popup windows.
41. Tool windows.
42. Embedded windows.
43. Window surfaces.
44. Surface attachment.
45. Offscreen surfaces.
46. Headless windows.
47. Remote windows.
48. Virtual displays.
49. Display capture.
50. Capture security.
51. Cursor management.
52. Cursor confinement.
53. Relative pointer mode.
54. Window icon/title.
55. Window snapshots.
56. Persistent state.
57. Session restore.
58. Safe placement.
59. Virtual desktops/workspaces.
60. Window groups.
61. Tiling/snap.
62. Placement policies.
63. Safe areas.
64. System insets.
65. Orientation.
66. Rotation.
67. Color space.
68. HDR.
69. Color management boundary.
70. VSync relationship.
71. Presentation.
72. Presentation timing.
73. Window events.
74. Event queue.
75. Event coalescing.
76. Thread affinity.
77. Nonblocking operations.
78. Close requests.
79. Forced close.
80. Suspend/resume.
81. Device loss.
82. Surface recreation.
83. Native handles.
84. Platform backend.
85. Desktop backend.
86. Mobile backend.
87. Embedded backend.
88. Headless backend.
89. Remote rendering boundary.
90. Window streaming boundary.
91. Window security.
92. Cross-process windows.
93. Permission model.
94. Display capabilities.
95. Physical vs logical display.
96. Window state machine.
97. Orthogonal state model.
98. Window commands.
99. Requested vs actual state.
100. Window constraints.
101. Window manager integration.
102. Compositor integration.
103. Transparency.
104. Overlay security.
105. Display topology changes.
106. Window migration.
107. Placement resolver.
108. Window transactions.
109. Snapshot/restore.
110. Display simulation.
111. Window simulation.
112. Deterministic replay.
113. UI integration.
114. Graphics integration.
115. Media integration.
116. Audio integration.
117. Compute integration.
118. Storage integration.
119. Network integration.
120. AI boundary.
121. Digital twin.
122. Performance architecture.
123. Native fast path.
124. Event coalescing.
125. Zero-copy surface.
126. Presentation latency.
127. Memory strategy.
128. Compile-time specialization.
129. Native API.
130. Canonical lifecycle flows.
131. 40 formal invariants.

---

# 736.168 — Definition of Done

```text
BOOTSTRAP-736
STATUS: COMPLETE / FROZEN

AXWINDOW
 ├── Window Runtime
 ├── Display Runtime
 ├── Display Topology
 ├── Surface Runtime
 ├── Multi-Monitor
 ├── DPI / Scaling
 ├── Fullscreen
 ├── Window State
 ├── Focus / Activation
 ├── Z-Order
 ├── Window Hierarchy
 ├── Modal / Popup / Tool Windows
 ├── Cursor Runtime
 ├── Display Modes
 ├── HDR / Color Metadata
 ├── Presentation Timing
 ├── Surface Recreation
 ├── Headless Runtime
 ├── Remote Surface Boundary
 ├── Capture Boundary
 ├── Security Boundary
 ├── Desktop Integration
 ├── Mobile Integration
 ├── Embedded Integration
 ├── AXUI Integration
 ├── AXGRAPHICS Integration
 ├── AXINPUT Integration
 ├── AXMEDIA Integration
 ├── AXAUDIO Integration
 ├── AXCOMPUTE Integration
 ├── AXSTORAGE Integration
 ├── AXNETWORK Integration
 ├── AXSECURITY Integration
 ├── AI Boundary
 ├── Window Simulation
 ├── Display Simulation
 ├── Window Digital Twin
 ├── Deterministic Replay
 ├── Native Fast Path
 └── Window Runtime 5.0
```

**BOOTSTRAP-736 / AXWINDOW — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-737 — AXDISPLAY

**Native Display & Visual Output Runtime — physical/virtual displays, display topology, EDID/identity metadata, resolution, refresh timing, color management, HDR, VRR, orientation, pixel formats, display calibration, ICC/profile integration, display capabilities, presentation timing, frame synchronization, display capture boundary, multi-display synchronization, remote/virtual displays, embedded panels, display power state, brightness, adaptive brightness, display configuration transactions, deterministic display simulation, visual output telemetry và Display Runtime 5.0.**