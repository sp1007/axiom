# BOOTSTRAP-737 — AXDISPLAY

**Namespace:** `AXDISPLAY`  
**Phase:** Axiom Civilization Runtime / Native Visual Output Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXWINDOW`, `AXGRAPHICS`, `AXMEDIA`, `AXINPUT`, `AXCOMPUTE`, `AXSTORAGE`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

> `AXDISPLAY` tách phần **physical/logical visual output** khỏi `AXWINDOW`. `AXWINDOW` quản lý cửa sổ và surface ownership; `AXDISPLAY` quản lý display hardware/logical outputs, timing, modes, color, HDR, VRR, topology, calibration và output configuration.

---

# 737.0 — Mục tiêu

AXDISPLAY phải cung cấp một abstraction thống nhất cho:

```text
Physical Display
Logical Display
Virtual Display
Embedded Panel
Remote Display
Display Controller
Display Output
Display Mode
Resolution
Refresh Rate
VRR
HDR
Color Space
Color Profile
Brightness
Orientation
Rotation
Display Timing
Presentation
Display Synchronization
Display Configuration
Display Capture Boundary
Display Simulation
```

Kiến trúc:

```text
                         AXDISPLAY
                            │
        ┌───────────────────┼────────────────────┐
        ↓                   ↓                    ↓
     OUTPUTS             TOPOLOGY              TIMING
        │                   │                    │
        ↓                   ↓                    ↓
      panels            relationships        refresh/vsync
        │                   │                    │
        └───────────────────┼────────────────────┘
                            ↓
                       COLOR / HDR
                            │
                            ↓
                       PRESENTATION
                            │
                 ┌──────────┴──────────┐
                 ↓                     ↓
            AXGRAPHICS             AXWINDOW
```

---

# 737.1 — Boundary

AXDISPLAY sở hữu:

```text
display identity
display enumeration
display topology
physical/logical output
display modes
resolution
refresh
VRR
HDR capability
color space
color profiles
brightness
orientation
rotation
display power state
display timing
vblank/vsync information
presentation timing
display synchronization
display configuration
display calibration metadata
virtual displays
remote displays
embedded panels
display simulation
```

Không sở hữu:

```text
window lifecycle       → AXWINDOW
widgets/UI             → AXUI
GPU rendering          → AXGRAPHICS
raw input              → AXINPUT
media encoding         → AXMEDIA
physical asset identity→ AXASSET
security policy        → AXSECURITY
network transport      → AXNETWORK
```

---

# 737.2 — Display Identity

```axiom
display_id
```

phải ổn định trong phạm vi mà platform có thể đảm bảo.

Không dùng native handle làm canonical identity.

---

# 737.3 — Physical Display

```axiom
physical_display {
    id
    manufacturer
    model
    serial_reference
    physical_size
    capabilities
}
```

Physical display đại diện cho panel/output vật lý.

---

# 737.4 — Logical Display

```axiom
logical_display {
    id
    physical_reference
    bounds
    scale
    orientation
    mode
}
```

Một physical output có thể được expose dưới nhiều logical configurations.

---

# 737.5 — Virtual Display

```axiom
virtual_display {
    id
    resolution
    refresh
    scale
    color
}
```

Dùng cho:

```text
remote desktop
streaming
testing
headless rendering
XR
virtual machines
```

---

# 737.6 — Remote Display

```axiom
remote_display {
    id
    endpoint
    capabilities
}
```

AXDISPLAY chỉ quản lý display semantics.

Transport:

→ `AXNETWORK`

Encoding:

→ `AXMEDIA`

---

# 737.7 — Embedded Display

Embedded target có thể có:

```text
one controller
one panel
fixed resolution
fixed refresh
no desktop compositor
```

AXDISPLAY phải support configuration cực nhỏ.

---

# 737.8 — Display Controller

```axiom
display_controller {
    id
    outputs
    capabilities
}
```

Một controller có thể điều khiển nhiều outputs.

---

# 737.9 — Display Output

```axiom
display_output {
    id
    controller
    display
    connector
    state
}
```

Phân biệt:

```text
controller
output
physical panel
logical display
```

---

# 737.10 — Connector

Metadata:

```text
HDMI
DisplayPort
USB-C
eDP
DSI
embedded
virtual
remote
```

Connector type chỉ là metadata, không phải rendering API.

---

# 737.11 — Connection State

```text
disconnected
connected
initializing
active
suspended
failed
```

---

# 737.12 — Hot Plug

Khi display được:

```text
connected
disconnected
reconnected
```

AXDISPLAY phát event.

---

# 737.13 — Display Topology

```axiom
display_topology {
    version
    displays
    outputs
    relationships
}
```

Topology phải versioned.

---

# 737.14 — Display Arrangement

Mỗi logical display có:

```text
origin
extent
rotation
scale
```

trong global display coordinate space.

---

# 737.15 — Primary Display

```axiom
get_primary_display()
```

Primary display là platform state, không phải canonical physical identity.

---

# 737.16 — Display Bounds

```axiom
display_bounds(display)
```

Phải xác định coordinate space rõ ràng.

---

# 737.17 — Work Area Boundary

Work area thuộc desktop/window environment:

→ `AXWINDOW`

AXDISPLAY chỉ cung cấp display geometry.

---

# 737.18 — Physical Size

```axiom
physical_display_size {
    width
    height
    unit
}
```

Nếu platform không cung cấp chính xác:

```text
unknown
```

thay vì suy đoán.

---

# 737.19 — Pixel Density

```axiom
pixel_density {
    horizontal
    vertical
}
```

Không đồng nhất:

```text
pixel density
DPI
logical scaling
```

---

# 737.20 — Display Scale

```axiom
display_scale {
    x
    y
}
```

Scale có thể thay đổi runtime.

---

# 737.21 — DPI

```axiom
display_dpi {
    x
    y
}
```

DPI có thể là:

```text
physical measurement
OS logical DPI
reported DPI
```

Phải ghi rõ loại.

---

# 737.22 — Resolution

```axiom
display_resolution {
    width
    height
}
```

Integer pixel dimensions.

---

# 737.23 — Native Resolution

```axiom
native_resolution(display)
```

Native resolution là panel capability, không nhất thiết là active mode.

---

# 737.24 — Active Resolution

```axiom
active_resolution(display)
```

Có thể khác native resolution.

---

# 737.25 — Display Mode

```axiom
display_mode {
    resolution
    refresh_rate
    pixel_format
    color_space
    hdr
}
```

---

# 737.26 — Mode Identity

Mỗi mode phải có stable backend reference:

```axiom
display_mode_id
```

nếu platform cung cấp.

---

# 737.27 — Mode Enumeration

```axiom
enumerate_display_modes(display)
```

---

# 737.28 — Mode Validation

```axiom
validate_display_mode(
    display,
    mode
)
```

Không được giả định mode enumerated vẫn available sau topology change.

---

# 737.29 — Display Configuration Transaction

```axiom
begin_display_configuration()

set_mode(...)
set_orientation(...)
set_position(...)
set_primary(...)

commit_display_configuration()
```

Nếu một phần thất bại:

```text
rollback
```

nếu platform hỗ trợ atomic configuration.

---

# 737.30 — Configuration Result

```axiom
display_configuration_result {
    applied
    partial
    rejected
    rolled_back
}
```

---

# 737.31 — Refresh Rate

```axiom
refresh_rate {
    numerator
    denominator
}
```

Không dùng float làm canonical representation.

Ví dụ:

```text
60000 / 1001
```

được giữ chính xác.

---

# 737.32 — Refresh Range

```axiom
refresh_range {
    minimum
    maximum
}
```

---

# 737.33 — VRR

```axiom
variable_refresh_rate {
    supported
    minimum
    maximum
}
```

AXDISPLAY mô tả capability.

AXGRAPHICS quyết định frame scheduling.

---

# 737.34 — VRR Policy

```text
disabled
automatic
forced
application_controlled
```

Availability platform-dependent.

---

# 737.35 — VSync

```axiom
display_sync {
    mode
    interval
}
```

Modes có thể:

```text
immediate
vsync
adaptive
mailbox
platform_default
```

Actual support thuộc backend.

---

# 737.36 — VBlank

```axiom
display_vblank_event {
    display
    sequence
    timestamp
}
```

Timestamp phải thuộc clock domain xác định.

---

# 737.37 — Display Clock

```axiom
display_clock {
    clock_id
    frequency
    synchronization
}
```

Display clock có thể khác:

```text
CPU clock
audio clock
media clock
GPU clock
```

---

# 737.38 — Presentation Timestamp

```axiom
presentation_timestamp {
    display
    frame
    predicted_time
    actual_time
}
```

---

# 737.39 — Presentation Feedback

```axiom
presentation_feedback {
    frame_id
    submitted_at
    displayed_at
    refresh_sequence
}
```

Dùng cho:

```text
frame pacing
latency measurement
adaptive rendering
```

---

# 737.40 — Frame Latency

```axiom
display_latency {
    input_time
    render_start
    render_end
    submit_time
    display_time
}
```

Không phải mọi backend đều cung cấp toàn bộ timestamps.

---

# 737.41 — Display Synchronization

AXDISPLAY cung cấp synchronization primitives giữa:

```text
GPU
display
window
media clock
audio clock
```

nhưng không sở hữu GPU command scheduling.

---

# 737.42 — Audio/Video Sync

AXDISPLAY có thể cung cấp display timing cho:

```text
AXMEDIA
AXAUDIO
```

để thực hiện A/V synchronization.

---

# 737.43 — Color Space

```axiom
display_color_space {
    primaries
    transfer
    white_point
    range
}
```

---

# 737.44 — Color Primaries

Có thể biểu diễn:

```text
sRGB
Display-P3
BT.2020
custom
```

nhưng enum phải extensible.

---

# 737.45 — Transfer Function

```text
gamma
sRGB
PQ
HLG
custom
```

---

# 737.46 — HDR Capability

```axiom
hdr_capability {
    supported
    formats
    peak_luminance
    minimum_luminance
    metadata_modes
}
```

---

# 737.47 — HDR Formats

```text
HDR10
HDR10+
Dolby Vision
HLG
vendor-specific
```

AXDISPLAY không hard-code implementation dependency vào một format.

---

# 737.48 — HDR Metadata

```axiom
hdr_metadata {
    mastering
    content
    dynamic
}
```

Metadata chỉ được truyền khi backend hỗ trợ.

---

# 737.49 — SDR/HDR Transition

```text
SDR
 ↓
display capability update
 ↓
HDR configuration
 ↓
AXGRAPHICS color pipeline
 ↓
HDR presentation
```

---

# 737.50 — Color Profile

```axiom
color_profile {
    id
    profile_data_reference
    source
    version
}
```

Profile data có thể được lưu trong `AXSTORAGE`.

---

# 737.51 — ICC Integration

AXDISPLAY có thể expose:

```axiom
get_display_color_profile(display)
```

ICC processing không bắt buộc nằm trong AXDISPLAY.

Color-management engine có thể thuộc AXGRAPHICS.

---

# 737.52 — Calibration

```axiom
display_calibration {
    white_point
    gamma
    luminance
    profile
    timestamp
}
```

Calibration phải có provenance.

---

# 737.53 — Calibration Authority

AXDISPLAY không tự tuyên bố display đã được calibration nếu chỉ có dữ liệu suy đoán.

Phải phân biệt:

```text
factory calibration
user calibration
application calibration
estimated calibration
```

---

# 737.54 — Brightness

```axiom
get_brightness(display)
set_brightness(display, value)
```

Brightness value phải có semantic rõ ràng.

Không mặc định coi:

```text
0..1
```

là physical luminance.

---

# 737.55 — Hardware Brightness

```axiom
brightness_capability {
    supported
    minimum
    maximum
    current
}
```

---

# 737.56 — Adaptive Brightness

```axiom
adaptive_brightness {
    supported
    enabled
}
```

Sensor source:

→ platform/input/sensor subsystem.

---

# 737.57 — Display Power

```text
on
standby
sleep
off
unknown
```

---

# 737.58 — Power State

```axiom
display_power_state {
    state
    reason
}
```

Reason có thể:

```text
user
system
power_policy
application
thermal
unknown
```

---

# 737.59 — Power Policy Boundary

Application không được mặc định cưỡng ép physical display power.

AXSECURITY/platform policy có thể từ chối.

---

# 737.60 — Orientation

```axiom
display_orientation {
    rotation
    orientation
}
```

---

# 737.61 — Rotation

Canonical rotations:

```text
0
90
180
270
```

---

# 737.62 — Orientation Event

```axiom
display_orientation_event {
    display
    old_orientation
    new_orientation
}
```

---

# 737.63 — Physical vs Logical Rotation

Phân biệt:

```text
panel physical orientation
logical desktop rotation
content rotation
```

---

# 737.64 — Display Transform

```axiom
display_transform {
    scale
    rotation
    translation
}
```

Transform được dùng để ánh xạ coordinate spaces.

---

# 737.65 — Display Coordinate Space

```text
physical pixel space
logical display space
global desktop space
window space
UI space
```

Mỗi conversion phải explicit.

---

# 737.66 — Coordinate Conversion

```axiom
display_to_global(...)
global_to_display(...)
display_to_physical(...)
physical_to_display(...)
```

---

# 737.67 — Multi-Display Synchronization

Các display có thể có:

```text
independent clocks
shared timing
genlocked timing
```

AXDISPLAY phải biểu diễn synchronization relationship.

---

# 737.68 — Display Sync Group

```axiom
display_sync_group {
    id
    displays
    synchronization
}
```

---

# 737.69 — Synchronized Presentation

```axiom
synchronized_present(
    sync_group,
    frames
)
```

Actual guarantee phụ thuộc hardware/backend.

---

# 737.70 — Genlock

```axiom
genlock_capability {
    supported
    source
    status
}
```

---

# 737.71 — Frame Lock

```axiom
frame_lock_capability
```

cho multi-display visualization.

---

# 737.72 — Display Mosaic

Một logical rendering surface có thể trải trên:

```text
Display A
Display B
Display C
```

AXDISPLAY mô tả topology; AXGRAPHICS render surface.

---

# 737.73 — Tiled Display

```axiom
display_tile {
    display
    region
    tile_position
}
```

Một physical display wall có thể gồm nhiều panels.

---

# 737.74 — Display Wall

```axiom
display_wall {
    tiles
    topology
    synchronization
}
```

---

# 737.75 — Embedded Timing

Embedded display có thể expose:

```text
pixel clock
line timing
frame timing
sync polarity
```

AXDISPLAY cho phép backend chuyên dụng cung cấp metadata này.

---

# 737.76 — Scanout

```axiom
scanout_config {
    format
    stride
    timing
}
```

Low-level scanout chỉ là optional backend capability.

---

# 737.77 — Direct Scanout

```axiom
direct_scanout_capability
```

Cho phép compositor bypass trong trường hợp phù hợp.

AXDISPLAY không ép sử dụng direct scanout.

---

# 737.78 — Display Buffer

```axiom
display_buffer {
    resource
    format
    stride
}
```

Resource ownership thuộc graphics/backend.

---

# 737.79 — Zero-Copy Presentation

Mục tiêu:

```text
AXGRAPHICS resource
        ↓
display scanout
```

không copy pixel nếu hardware hỗ trợ.

---

# 737.80 — Display Capture Boundary

```axiom
capture_display(display)
```

Output:

```text
AXMEDIA frame
```

hoặc graphics image resource.

---

# 737.81 — Capture Timing

Capture phải giữ:

```text
display timestamp
frame sequence
color metadata
resolution
```

---

# 737.82 — Protected Content

Display có thể chứa protected content.

AXDISPLAY phải biểu diễn:

```axiom
content_protection_state {
    protected
    restricted_capture
}
```

---

# 737.83 — Content Protection

Có thể liên quan:

```text
HDCP
secure display path
DRM-protected surface
```

AXDISPLAY chỉ cung cấp capability/state abstraction.

---

# 737.84 — Secure Presentation

```axiom
secure_presentation_policy
```

AXSECURITY quyết định authorization.

---

# 737.85 — Display Enumeration API

```axiom
enumerate_displays()
enumerate_outputs()
enumerate_controllers()
enumerate_modes(display)
get_display_capabilities(display)
```

---

# 737.86 — Display Observation

```axiom
observe_display(display)
```

có thể stream:

```text
connection
mode
brightness
orientation
HDR
VRR
power
timing
```

events.

---

# 737.87 — Display Events

```text
connected
disconnected
mode_changed
resolution_changed
refresh_changed
scale_changed
orientation_changed
color_changed
hdr_changed
brightness_changed
power_changed
topology_changed
timing_changed
```

---

# 737.88 — Event Coalescing

Các event trạng thái có thể coalesce:

```text
mode
resolution
scale
color
HDR
brightness
```

nhưng final state phải chính xác.

---

# 737.89 — Event Ordering

AXDISPLAY phải duy trì ordering trong cùng một display event stream.

Cross-display ordering chỉ guaranteed khi backend cung cấp common clock.

---

# 737.90 — Display Event Timestamp

```axiom
display_event {
    timestamp
    clock_domain
    sequence
}
```

---

# 737.91 — Display Configuration Request

```axiom
display_request {
    display
    changes
}
```

Changes có thể:

```text
mode
position
orientation
scale
brightness
power
HDR
```

---

# 737.92 — Permission Boundary

Một số operations có thể yêu cầu:

```text
display configuration permission
brightness permission
capture permission
virtual display permission
```

---

# 737.93 — Security Capability

```axiom
display_capability {
    display
    operation
}
```

Ví dụ:

```text
observe
configure
capture
control_power
control_brightness
```

---

# 737.94 — Cross-Process Display Control

Một process không được mặc định thay đổi display state của hệ thống.

---

# 737.95 — Display Configuration Authority

AXDISPLAY phân biệt:

```text
requested configuration
authorized configuration
platform configuration
actual configuration
```

---

# 737.96 — Configuration Conflict

Nếu OS/user thay đổi display trong lúc application đang transaction:

```text
transaction conflict
```

phải được báo rõ.

---

# 737.97 — Configuration Rollback

Nếu backend hỗ trợ:

```axiom
rollback_display_configuration()
```

phải khôi phục configuration snapshot đã capture.

---

# 737.98 — Configuration Snapshot

```axiom
display_configuration_snapshot {
    topology_version
    display_states
    modes
    positions
}
```

---

# 737.99 — Simulation

```axiom
display_simulation {
    topology
    displays
    modes
    timing
    events
}
```

---

# 737.100 — Deterministic Simulation

Simulation có thể tạo:

```text
monitor disconnect
resolution switch
HDR switch
VRR changes
rotation
refresh changes
```

với deterministic timestamps.

---

# 737.101 — Display Replay

Record:

```text
topology events
mode events
timing events
configuration requests
configuration results
```

để tái hiện display bugs.

---

# 737.102 — Display Digital Twin

```axiom
display_digital_twin {
    physical_model
    logical_model
    topology
    timing
    color
    power
    configuration
}
```

---

# 737.103 — Telemetry

AXDISPLAY có thể thu:

```text
refresh stability
frame timing
presentation misses
hotplug events
mode switches
brightness changes
HDR transitions
VRR state
```

---

# 737.104 — Diagnostics

```axiom
display_diagnostics {
    timing
    connection
    mode
    color
    power
    errors
}
```

---

# 737.105 — Error Model

Các lỗi phải phân biệt:

```text
unsupported
permission_denied
invalid_mode
display_disconnected
configuration_conflict
hardware_failure
timeout
temporary_unavailable
backend_error
```

---

# 737.106 — Retry Policy

AXDISPLAY không tự động retry mọi operation.

Retry policy phải phụ thuộc loại lỗi.

---

# 737.107 — Display Recovery

Nếu display disconnect:

```text
disconnect
 ↓
invalidate active output
 ↓
notify subscribers
 ↓
re-enumerate
 ↓
reconnect
 ↓
revalidate mode
```

---

# 737.108 — Recovery Identity

Reconnect có thể:

```text
same physical display
new logical display
new output
```

Không được suy đoán identity chỉ từ vị trí.

---

# 737.109 — Display Fingerprint

Có thể tạo:

```axiom
display_fingerprint
```

từ:

```text
manufacturer
model
serial
EDID-like metadata
```

nhưng fingerprint chỉ là correlation aid, không thay thế authoritative identity.

---

# 737.110 — EDID Metadata

```axiom
display_descriptor {
    raw_descriptor
    parsed_capabilities
}
```

Raw descriptor phải được giữ nguyên nếu available.

---

# 737.111 — Capability Discovery

Capability discovery phải phân biệt:

```text
supported
advertised
currently_available
currently_enabled
```

---

# 737.112 — Display Capability Cache

Capabilities có thể cache nhưng phải invalidated khi:

```text
hotplug
mode change
driver change
power state change
```

---

# 737.113 — Display Driver Boundary

AXDISPLAY không chứa driver implementation.

Backend adapter chuyển:

```text
AXDISPLAY API
       ↓
platform driver
```

---

# 737.114 — OS Backend

Có thể có:

```text
Windows backend
Linux backend
macOS backend
Android backend
iOS backend
embedded backend
headless backend
```

---

# 737.115 — Minimal Embedded Backend

Embedded build có thể loại bỏ:

```text
desktop topology
window manager
HDR
VRR
color profiles
virtual displays
```

nếu target không hỗ trợ.

Compiler/linker phải loại dead features khỏi binary.

---

# 737.116 — Headless Backend

Headless backend vẫn phải hỗ trợ:

```text
virtual display
timing simulation
surface presentation
capture
```

nếu được cấu hình.

---

# 737.117 — Remote Backend

Remote backend:

```text
AXDISPLAY
   ↓
virtual display
   ↓
AXMEDIA encode
   ↓
AXNETWORK
```

---

# 737.118 — XR Boundary

XR display/output có thể expose:

```text
eye
view
refresh
projection
display timing
```

AXDISPLAY chỉ sở hữu output/display semantics.

XR spatial semantics thuộc graphics/XR layer.

---

# 737.119 — Multi-Plane Output

Display hardware có thể hỗ trợ nhiều planes:

```axiom
display_plane {
    id
    format
    transform
    alpha
    z
}
```

AXDISPLAY expose capability; AXGRAPHICS quyết định usage.

---

# 737.120 — Overlay Plane

Overlay planes có thể dùng cho:

```text
video
cursor
UI
protected content
```

---

# 737.121 — Cursor Plane

Nếu hardware hỗ trợ hardware cursor:

```axiom
cursor_plane_capability
```

AXINPUT/AXWINDOW vẫn sở hữu cursor semantics.

---

# 737.122 — Color Pipeline

Display color pipeline:

```text
application color
      ↓
AXGRAPHICS
      ↓
composition
      ↓
display color transform
      ↓
panel
```

AXDISPLAY mô tả output-side state.

---

# 737.123 — Gamma / Transfer

```axiom
display_transfer_function
```

Không được silently apply arbitrary gamma correction.

---

# 737.124 — Luminance

```axiom
luminance_range {
    minimum
    typical
    peak
}
```

Units phải explicit.

---

# 737.125 — Color Accuracy

Color metadata phải có:

```text
source
confidence
timestamp
```

nếu không phải hardware-authoritative.

---

# 737.126 — Display Health

```axiom
display_health {
    status
    temperature
    error_count
    signal_quality
}
```

Chỉ cung cấp khi backend/hardware có dữ liệu.

---

# 737.127 — Thermal State

Display có thể report:

```text
normal
warm
hot
throttled
critical
unknown
```

Không được suy luận nếu không có sensor/backend evidence.

---

# 737.128 — Power-Aware Display

AXDISPLAY có thể expose:

```text
power consumption estimate
power state
refresh reduction
brightness reduction
```

Energy accounting:

→ `AXENERGY`.

---

# 737.129 — Energy Boundary

AXDISPLAY không trở thành energy ledger.

Nếu cần authoritative energy accounting:

→ `AXENERGY`.

---

# 737.130 — Compute Boundary

Display scheduling may request:

```text
GPU workload
composition workload
conversion workload
```

nhưng actual scheduling:

→ `AXCOMPUTE`.

---

# 737.131 — Graphics Boundary

AXDISPLAY không định nghĩa:

```text
shader
mesh
texture
render pass
```

Các khái niệm đó thuộc `AXGRAPHICS`.

---

# 737.132 — Media Boundary

AXDISPLAY không sở hữu:

```text
codec
container
decoder
encoder
timeline
```

→ `AXMEDIA`.

---

# 737.133 — Window Boundary

```text
AXWINDOW:
"cửa sổ nào?"

AXDISPLAY:
"xuất hình ảnh ở đâu và với timing/capability nào?"
```

---

# 737.134 — Input Boundary

```text
AXINPUT:
"người dùng nhập gì?"

AXDISPLAY:
"display ở đâu?"
```

---

# 737.135 — AI Display Optimization

AI có thể đề xuất:

```text
mode selection
refresh policy
brightness policy
display placement
color configuration
energy optimization
```

Nhưng AI result:

```axiom
display_ai_suggestion
```

không tự trở thành configuration command.

---

# 737.136 — AI Safety Boundary

AI không được tự động:

```text
disable security output
capture protected display
change system-critical display state
```

nếu không có explicit capability.

---

# 737.137 — Native API

```axiom
enumerate_displays()
enumerate_outputs()
enumerate_controllers()

get_display()
get_display_capabilities()
get_display_topology()

get_primary_display()

enumerate_display_modes()
get_active_mode()
validate_display_mode()

begin_display_configuration()
commit_display_configuration()
rollback_display_configuration()

get_display_scale()
get_display_dpi()
get_display_resolution()
get_native_resolution()

get_refresh_rate()
get_vrr_capability()
get_sync_info()

get_color_space()
get_color_profile()
get_hdr_capability()

get_brightness()
set_brightness()

get_power_state()
set_power_state()

get_orientation()
set_orientation()

display_to_global()
global_to_display()

capture_display()

observe_display()

create_virtual_display()
destroy_virtual_display()

create_display_simulation()
replay_display_events()

get_display_diagnostics()
get_display_health()

get_native_display_handle()
```

---

# 737.138 — Canonical Flow: Display Discovery

```text
AXDISPLAY
   ↓
enumerate controllers
   ↓
enumerate outputs
   ↓
detect displays
   ↓
read capabilities
   ↓
build topology
   ↓
publish topology version
```

---

# 737.139 — Canonical Flow: Hot Plug

```text
physical connection
        ↓
driver/backend
        ↓
AXDISPLAY
        ↓
topology update
        ↓
capability discovery
        ↓
display event
        ↓
AXWINDOW
        ↓
AXGRAPHICS
```

---

# 737.140 — Canonical Flow: Mode Change

```text
request
   ↓
validate
   ↓
authorize
   ↓
begin transaction
   ↓
apply
   ↓
verify actual state
   ↓
commit
   ↓
publish event
```

---

# 737.141 — Canonical Flow: Frame Presentation

```text
AXGRAPHICS
    ↓
render
    ↓
surface/resource
    ↓
AXWINDOW
    ↓
AXDISPLAY
    ↓
display timing
    ↓
scanout
    ↓
physical output
```

---

# 737.142 — Canonical Flow: HDR

```text
display discovery
      ↓
HDR capability
      ↓
application request
      ↓
AXGRAPHICS color pipeline
      ↓
HDR frame
      ↓
AXDISPLAY output metadata
      ↓
HDR presentation
```

---

# 737.143 — Canonical Flow: Display Loss

```text
disconnect
    ↓
output invalidated
    ↓
display event
    ↓
AXWINDOW notified
    ↓
surface reconfiguration
    ↓
new topology
    ↓
recovery
```

---

# 737.144 — Performance Architecture

Hot path:

```text
GPU frame
   ↓
presentation
   ↓
display timing
   ↓
scanout
```

Không được đưa vào hot path:

```text
reflection
generic serialization
dynamic metadata lookup
heap allocation
blocking filesystem
network RPC
```

---

# 737.145 — Native Fast Path

Display timing structure:

```axiom
display_fast_state {
    id
    width
    height
    refresh_num
    refresh_den
    flags
    sequence
}
```

Cold metadata tách khỏi hot state.

---

# 737.146 — Zero-Copy

Ưu tiên:

```text
GPU resource
   ↓
display plane
```

thay vì:

```text
GPU
 ↓ copy
CPU
 ↓ copy
display
```

khi hardware hỗ trợ.

---

# 737.147 — Frame Timing

Timing calculations phải ưu tiên:

```text
integer ticks
fixed-point
rational time
```

thay vì floating-point accumulated time.

---

# 737.148 — Deterministic Timing

Simulation phải cho phép:

```text
fixed refresh
deterministic vblank
deterministic presentation
```

để test graphics pipeline.

---

# 737.149 — Compile-Time Specialization

Target-specific build có thể specialize:

```text
HDR
VRR
embedded timing
direct scanout
display planes
```

Unused capabilities phải được loại khỏi final binary nếu có thể.

---

# 737.150 — Memory

AXDISPLAY runtime phải tránh allocation trong:

```text
vblank event
presentation feedback
hotplug notification
frame timing
```

---

# 737.151 — Formal Invariants

```text
DSP-INV-01   Every display has an explicit display identity.
DSP-INV-02   Physical and logical display identities are distinct.
DSP-INV-03   Display output identity is distinct from panel identity.
DSP-INV-04   Display controller identity is distinct from output identity.
DSP-INV-05   Display topology is versioned.
DSP-INV-06   Display connection state is observable.
DSP-INV-07   Display disconnection is observable.
DSP-INV-08   Display resolution is represented in integer pixels.
DSP-INV-09   Native resolution is distinct from active resolution.
DSP-INV-10   Display mode is explicit.

DSP-INV-11   Refresh rate uses lossless rational representation.
DSP-INV-12   VRR capability is distinct from active VRR state.
DSP-INV-13   VSync capability is distinct from frame scheduling policy.
DSP-INV-14   Display timing has an explicit clock domain.
DSP-INV-15   Presentation timestamps identify their timing domain.
DSP-INV-16   Cross-display synchronization is explicit.
DSP-INV-17   Display scale is distinct from physical pixel density.
DSP-INV-18   DPI type is explicit.
DSP-INV-19   Display coordinate space is explicit.
DSP-INV-20   Coordinate transformations are explicit.

DSP-INV-21   Color space is distinct from pixel format.
DSP-INV-22   HDR capability is distinct from HDR activation.
DSP-INV-23   HDR metadata is distinct from HDR pixel data.
DSP-INV-24   Color profile provenance is preserved.
DSP-INV-25   Calibration provenance is preserved.
DSP-INV-26   Brightness semantics are explicit.
DSP-INV-27   Display power state is observable.
DSP-INV-28   Display power control is permission-aware.
DSP-INV-29   Orientation is distinct from content rotation.
DSP-INV-30   Physical and logical rotation are distinct.

DSP-INV-31   Display configuration is transactional where backend permits.
DSP-INV-32   Requested configuration is distinct from actual configuration.
DSP-INV-33   Configuration conflicts are explicit.
DSP-INV-34   Backend limitations cannot be silently ignored.
DSP-INV-35   Display capture is security-aware.
DSP-INV-36   Protected display content cannot be captured without authorization.
DSP-INV-37   Native display handles are opaque.
DSP-INV-38   Virtual displays are distinct from physical displays.
DSP-INV-39   Display simulation cannot mutate production state.
DSP-INV-40   Display replay preserves deterministic event ordering.
```

---

# 737.152 — Completion Criteria

`BOOTSTRAP-737` phải freeze:

1. Display identity.
2. Physical displays.
3. Logical displays.
4. Virtual displays.
5. Remote displays.
6. Embedded displays.
7. Display controllers.
8. Display outputs.
9. Connector metadata.
10. Connection lifecycle.
11. Hot-plug.
12. Topology.
13. Display arrangement.
14. Primary display.
15. Physical size.
16. Pixel density.
17. DPI.
18. Scale.
19. Resolution.
20. Native resolution.
21. Active resolution.
22. Display modes.
23. Mode enumeration.
24. Mode validation.
25. Configuration transactions.
26. Refresh rate.
27. VRR.
28. VSync.
29. VBlank.
30. Display clocks.
31. Presentation timestamps.
32. Presentation feedback.
33. Frame latency.
34. Display synchronization.
35. Audio/video timing boundary.
36. Color space.
37. Primaries.
38. Transfer functions.
39. HDR.
40. HDR metadata.
41. Color profiles.
42. ICC boundary.
43. Calibration.
44. Brightness.
45. Adaptive brightness.
46. Power state.
47. Power policy.
48. Orientation.
49. Rotation.
50. Coordinate transforms.
51. Multi-display synchronization.
52. Sync groups.
53. Genlock.
54. Frame lock.
55. Display mosaics.
56. Display walls.
57. Embedded timing.
58. Scanout.
59. Direct scanout.
60. Display buffers.
61. Zero-copy presentation.
62. Capture boundary.
63. Capture timing.
64. Protected content.
65. Security capabilities.
66. Display observation.
67. Event ordering.
68. Event coalescing.
69. Configuration conflict handling.
70. Configuration rollback.
71. EDID-like metadata.
72. Capability discovery.
73. Capability cache.
74. Driver boundary.
75. Desktop backend.
76. Mobile backend.
77. Embedded backend.
78. Headless backend.
79. Remote backend.
80. XR output boundary.
81. Display planes.
82. Overlay planes.
83. Cursor plane.
84. Color pipeline boundary.
85. Luminance metadata.
86. Display health.
87. Thermal metadata.
88. Energy boundary.
89. AI boundary.
90. Digital twin.
91. Simulation.
92. Deterministic replay.
93. Diagnostics.
94. Error model.
95. Recovery.
96. Native API.
97. Canonical flows.
98. Performance architecture.
99. Zero-copy path.
100. Compile-time specialization.
101. Memory strategy.
102. 40 formal invariants.

---

# 737.153 — Definition of Done

```text
BOOTSTRAP-737
STATUS: COMPLETE / FROZEN

AXDISPLAY
 ├── Display Identity
 ├── Physical Display
 ├── Logical Display
 ├── Virtual Display
 ├── Remote Display
 ├── Embedded Display
 ├── Controller / Output
 ├── Display Topology
 ├── Hot Plug
 ├── Display Modes
 ├── Resolution
 ├── Refresh / VRR
 ├── VSync / VBlank
 ├── Presentation Timing
 ├── Multi-Display Synchronization
 ├── Color Management
 ├── HDR
 ├── Calibration
 ├── Brightness
 ├── Power State
 ├── Orientation
 ├── Scanout
 ├── Display Planes
 ├── Protected Content
 ├── Capture Boundary
 ├── Configuration Transactions
 ├── Display Simulation
 ├── Display Digital Twin
 ├── Deterministic Replay
 ├── Security Boundary
 ├── AXWINDOW Integration
 ├── AXGRAPHICS Integration
 ├── AXMEDIA Integration
 ├── AXCOMPUTE Integration
 ├── AXINPUT Integration
 ├── AXSTORAGE Integration
 ├── AXSECURITY Integration
 ├── AI Boundary
 ├── Native Fast Path
 └── Display Runtime 5.0
```

**BOOTSTRAP-737 / AXDISPLAY — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-738 — AXUI

**Native User Interface Runtime — visual tree, controls, layout, styling, text, accessibility, themes, animation, interaction states, forms, menus, dialogs, data binding, virtualization, retained/immediate rendering, UI composition, responsive layout, localization, input integration, window integration, GPU rendering, UI state management, UI testing, deterministic interaction replay, UI automation, accessibility semantics, UI performance và User Interface Runtime 5.0.**