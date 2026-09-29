# BOOTSTRAP-734 — AXINPUT

**Namespace:** `AXINPUT`  
**Phase:** Axiom Civilization Runtime / Native Human Interaction Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXGRAPHICS`, `AXAUDIO`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

> `AXINPUT` là lớp native chuẩn hóa toàn bộ tín hiệu tương tác từ người dùng và thiết bị đầu vào thành một mô hình thống nhất, có timestamp, device identity, routing, mapping và replay. Nó không sở hữu UI semantics; `AXUI` ở tầng trên sẽ sử dụng `AXINPUT`.

---

# 734.0 — Mục tiêu

AXINPUT phải thống nhất:

```text
keyboard
mouse
touch
pen
gamepad
joystick
controller
wheel
pedal
remote
gesture
motion sensor
camera-derived input
microphone-derived control
haptic feedback
accessibility input
```

Kiến trúc:

```text
                 AXINPUT
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
    DEVICES       EVENTS       ACTIONS
       │            │            │
       └────────────┼────────────┘
                    ↓
                 ROUTING
                    ↓
             APPLICATION / UI
```

---

# 734.1 — Boundary

AXINPUT sở hữu:

```text
device discovery
device lifecycle
raw input
normalized input
input events
device capabilities
input routing
mapping
actions
gestures
haptics
input recording
input replay
input simulation
multi-user input
```

Không sở hữu:

```text
UI widgets            → AXUI
window management     → AXWINDOW
graphics rendering    → AXGRAPHICS
audio playback        → AXAUDIO
physical device asset → AXASSET
authentication        → AXSECURITY
human identity        → AXIDENTITY
```

---

# 734.2 — Input Device

```axiom
input_device {
    id
    class
    name
    capabilities
    state
}
```

---

# 734.3 — Device Classes

```text
keyboard
pointer
touch
pen
gamepad
joystick
wheel
pedal
controller
remote
sensor
camera
microphone
haptic
custom
```

---

# 734.4 — Device Identity

Phải phân biệt:

```text
logical device
physical device
OS device handle
AXASSET identity
user-assigned alias
```

Không được dùng OS handle làm persistent identity.

---

# 734.5 — Device Lifecycle

```text
DISCOVERED
CONNECTING
CONNECTED
READY
SUSPENDED
DISCONNECTED
REMOVED
```

---

# 734.6 — Device Discovery

```axiom
enumerate_input_devices()
get_input_device(id)
```

Discovery không được tự động cấp quyền sử dụng.

---

# 734.7 — Hot Plug

```axiom
input_device_event {
    type
    device
    timestamp
}
```

Events:

```text
CONNECTED
DISCONNECTED
CAPABILITY_CHANGED
BATTERY_CHANGED
```

---

# 734.8 — Input Event

Mọi input normalized về:

```axiom
input_event {
    timestamp
    device
    user
    kind
    payload
}
```

`timestamp` phải gắn với clock domain.

---

# 734.9 — Event Kind

```text
key
pointer
touch
pen
button
axis
hat
gesture
motion
sensor
text
haptic
system
```

---

# 734.10 — Input Clock

```axiom
input_clock {
    timestamp
    clock_domain
}
```

Input timing phải độc lập với frame rate của UI.

---

# 734.11 — Keyboard

```axiom
keyboard_event {
    key
    physical_key
    action
    modifiers
}
```

Actions:

```text
pressed
released
repeat
```

---

# 734.12 — Logical Key

```axiom
key_code
```

Ví dụ:

```text
A
ENTER
ESCAPE
TAB
F1
ARROW_UP
```

---

# 734.13 — Physical Key

```axiom
physical_key_code
```

Physical key giữ vị trí phím, không phụ thuộc keyboard layout.

---

# 734.14 — Keyboard Layout

AXINPUT phải phân biệt:

```text
physical key
logical key
text character
```

Ví dụ:

```text
physical key
   ↓
keyboard layout
   ↓
logical key / text
```

---

# 734.15 — Text Input

Text input không đồng nhất với key event.

```axiom
text_input_event {
    text
    composition
}
```

Điều này cần cho:

```text
IME
Vietnamese input
Chinese IME
Japanese IME
accent composition
```

---

# 734.16 — Composition

```axiom
text_composition {
    preedit
    selection
    candidate_state
    committed
}
```

---

# 734.17 — Modifier

```text
SHIFT
CTRL
ALT
META
ALTGR
CAPS_LOCK
NUM_LOCK
```

---

# 734.18 — Keyboard Repeat

```axiom
key_repeat {
    initial_delay
    interval
}
```

OS/backend có thể cung cấp native repeat.

---

# 734.19 — Pointer

```axiom
pointer_event {
    pointer_id
    position
    delta
    buttons
    modifiers
}
```

---

# 734.20 — Pointer Coordinates

Phải phân biệt:

```text
screen coordinates
window coordinates
client coordinates
viewport coordinates
world coordinates
```

AXINPUT chỉ sở hữu input-space coordinates.

---

# 734.21 — Pointer Button

```text
left
right
middle
back
forward
extra
```

---

# 734.22 — Pointer Motion

```axiom
pointer_motion {
    position
    delta
    velocity
}
```

Velocity có thể là derived value.

---

# 734.23 — High Resolution Pointer

Nếu hardware cung cấp:

```text
raw delta
high-resolution wheel
high-resolution motion
```

runtime không được ép xuống integer trước khi application yêu cầu.

---

# 734.24 — Mouse Wheel

```axiom
wheel_event {
    delta
    axis
    unit
}
```

Units:

```text
notch
line
pixel
device_unit
```

---

# 734.25 — Touch

```axiom
touch_event {
    touch_id
    position
    pressure
    contact_area
    phase
}
```

Phases:

```text
began
moved
stationary
ended
cancelled
```

---

# 734.26 — Multi-Touch

Mỗi finger/contact có:

```text
touch_id
```

Không dùng array index làm persistent touch identity.

---

# 734.27 — Touch Gesture Boundary

Raw touch:

→ AXINPUT.

Semantic UI gesture:

→ AXUI / higher-level interaction layer.

AXINPUT chỉ cung cấp primitive gesture recognition khi cần.

---

# 734.28 — Pen

```axiom
pen_event {
    pen_id
    position
    pressure
    tilt
    rotation
    buttons
    phase
}
```

---

# 734.29 — Pen Pressure

Pressure phải là normalized capability:

```text
0.0 → 1.0
```

nhưng runtime phải giữ metadata về native resolution nếu có.

---

# 734.30 — Pen Tilt

```axiom
pen_tilt {
    x
    y
}
```

---

# 734.31 — Pen Eraser

```axiom
pen_tool {
    tip
    eraser
    barrel
}
```

---

# 734.32 — Gamepad

```axiom
gamepad {
    buttons
    axes
    triggers
    hats
}
```

---

# 734.33 — Gamepad Button

```axiom
gamepad_button_event {
    button
    state
}
```

---

# 734.34 — Analog Axis

```axiom
analog_axis_event {
    axis
    value
}
```

Giá trị chuẩn:

```text
-1.0 → +1.0
```

hoặc range capability-specific.

---

# 734.35 — Trigger

Trigger có thể là:

```text
0.0 → 1.0
```

không nên ép thành digital button.

---

# 734.36 — Dead Zone

```axiom
dead_zone {
    inner
    outer
    curve
}
```

Dead-zone là mapping policy, không phải raw device state.

---

# 734.37 — Input Calibration

```axiom
input_calibration {
    offset
    scale
    dead_zone
    curve
}
```

---

# 734.38 — Joystick

```axiom
joystick {
    axes
    buttons
    hats
}
```

---

# 734.39 — Hat Switch

```axiom
hat_state {
    direction
}
```

---

# 734.40 — Wheel / Pedal

```axiom
wheel_device {
    steering
    throttle
    brake
    clutch
}
```

---

# 734.41 — Controller Mapping

AXINPUT cung cấp canonical control names:

```text
move
look
jump
confirm
cancel
menu
primary
secondary
```

Nhưng mapping cụ thể thuộc application profile.

---

# 734.42 — Input Profile

```axiom
input_profile {
    device_class
    mappings
}
```

---

# 734.43 — Mapping

```axiom
input_mapping {
    source
    transform
    destination
}
```

Ví dụ:

```text
Gamepad Left Stick
        ↓
      deadzone
        ↓
      curve
        ↓
     Move X/Y
```

---

# 734.44 — Input Transform

```axiom
input_transform {
    scale
    offset
    dead_zone
    curve
    inversion
}
```

---

# 734.45 — Action

Higher-level abstraction:

```axiom
input_action {
    id
    value
    state
    timestamp
}
```

---

# 734.46 — Action State

```text
started
performed
changed
cancelled
completed
```

---

# 734.47 — Action Value

Có thể là:

```text
bool
scalar
vector2
vector3
rotation
text
```

---

# 734.48 — Action Binding

```axiom
action_binding {
    action
    source
    conditions
}
```

Ví dụ:

```text
Space → Jump
Left Stick → Move
Mouse → Look
```

---

# 734.49 — Chord

```axiom
input_chord {
    keys
    simultaneous
}
```

Ví dụ:

```text
CTRL + S
```

---

# 734.50 — Sequence

```axiom
input_sequence {
    events
    timeout
}
```

Có thể dùng cho:

```text
shortcut
gesture
controller combo
```

---

# 734.51 — Context

Input mapping phụ thuộc context:

```axiom
input_context {
    id
    priority
    enabled
}
```

Ví dụ:

```text
Gameplay
Menu
TextEditing
Console
PhotoMode
```

---

# 734.52 — Context Stack

```text
Gameplay
   ↓
Inventory
   ↓
TextInput
```

Input được route từ context ưu tiên cao xuống thấp.

---

# 734.53 — Input Routing

```axiom
route_input(event)
```

Pipeline:

```text
device
 ↓
raw event
 ↓
normalize
 ↓
filter
 ↓
context
 ↓
mapping
 ↓
action
 ↓
application
```

---

# 734.54 — Event Propagation

Modes:

```text
consume
pass
transform
redirect
broadcast
```

---

# 734.55 — Capture

Một consumer có thể capture input:

```axiom
capture_input(
    device,
    consumer
)
```

Ví dụ:

```text
drag operation
text editing
game controller ownership
```

---

# 734.56 — Focus

Input focus phải phân biệt:

```text
keyboard focus
pointer focus
touch focus
controller focus
text focus
```

---

# 734.57 — Focus Owner

```axiom
input_focus {
    device_class
    owner
}
```

AXWINDOW/AXUI có thể quản lý UI focus.

---

# 734.58 — Multi-User Input

Input event có thể chứa:

```axiom
user_id?
```

Một thiết bị có thể:

```text
unassigned
assigned to user
shared
```

---

# 734.59 — User Assignment

```axiom
assign_device(
    device,
    user
)
```

Không được suy ra identity chỉ từ device.

---

# 734.60 — Accessibility Input

AXINPUT phải cho phép input từ:

```text
switch device
eye tracker
assistive controller
voice command
screen reader control
alternative pointer
```

Các semantic accessibility cao hơn thuộc AXUI.

---

# 734.61 — Input Virtualization

Một virtual device có thể phát:

```axiom
virtual_input_device {
    source
    capabilities
}
```

Ví dụ:

```text
AI controller
remote desktop
accessibility adapter
simulation
```

---

# 734.62 — Raw Input

```axiom
raw_input_event {
    device
    bytes
    timestamp
}
```

Raw data không được tự động coi là portable.

---

# 734.63 — Native Backend

Backend abstraction:

```text
Windows
Linux
macOS
Android
iOS
Web
Console
Embedded
```

Core API vẫn thống nhất.

---

# 734.64 — Backend Contract

```axiom
input_backend {
    enumerate
    open
    close
    poll
    subscribe
}
```

---

# 734.65 — Polling

```axiom
poll_input()
```

Có thể dùng trong:

```text
games
simulation
real-time systems
```

---

# 734.66 — Event Subscription

```axiom
subscribe_input(
    callback
)
```

Callback phải có concurrency semantics rõ ràng.

---

# 734.67 — Input Queue

```axiom
input_queue {
    capacity
    policy
}
```

Overflow policies:

```text
drop_oldest
drop_newest
coalesce
block
error
```

Real-time input không nên mặc định block.

---

# 734.68 — Event Coalescing

Pointer movement có thể coalesce:

```text
move1
move2
move3
```

thành:

```text
move(total_delta)
```

nhưng raw-event mode phải giữ được từng event khi application yêu cầu.

---

# 734.69 — Input Latency

```axiom
input_latency {
    hardware
    transport
    backend
    queue
    application
}
```

---

# 734.70 — Timestamp Preservation

Normalization không được loại bỏ timestamp gốc nếu backend cung cấp timestamp chính xác.

---

# 734.71 — Input Prediction

Runtime có thể expose predicted position:

```axiom
predicted_input {
    value
    prediction_horizon
    confidence
}
```

Prediction luôn là derived state.

---

# 734.72 — Motion Sensor

```axiom
motion_sensor {
    accelerometer
    gyroscope
    magnetometer
}
```

---

# 734.73 — Sensor Sample

```axiom
sensor_sample {
    sensor
    timestamp
    values
}
```

---

# 734.74 — Orientation

```axiom
orientation {
    quaternion
}
```

Không dùng Euler angle làm canonical internal representation.

---

# 734.75 — Sensor Fusion

```axiom
sensor_fusion {
    inputs
    output
    algorithm
}
```

Output phải đánh dấu là derived.

---

# 734.76 — Gesture

Primitive gesture:

```text
tap
double_tap
long_press
drag
swipe
pinch
rotate
```

Gesture recognizer:

```axiom
gesture_recognizer {
    input
    state
}
```

---

# 734.77 — Gesture State

```text
possible
began
changed
ended
failed
cancelled
```

---

# 734.78 — Gesture Conflict

Ví dụ:

```text
drag
vs
scroll
```

Resolver:

```axiom
gesture_arbitrator {
    recognizers
    priority
}
```

---

# 734.79 — Camera-Derived Input

AXINPUT có thể consume:

```text
hand tracking
pose tracking
face gesture
eye gaze
```

nhưng camera/image analysis:

→ AXMEDIA / AXAI.

AXINPUT chỉ nhận normalized result.

---

# 734.80 — Gaze

```axiom
gaze_input {
    origin
    direction
    confidence
}
```

---

# 734.81 — Haptic Device

```axiom
haptic_device {
    capabilities
}
```

---

# 734.82 — Haptic Command

```axiom
haptic_command {
    channel
    amplitude
    frequency
    duration
}
```

---

# 734.83 — Rumble

```axiom
rumble {
    low_frequency
    high_frequency
    duration
}
```

---

# 734.84 — Force Feedback

```axiom
force_feedback {
    force
    torque
    duration
}
```

Safety constraints phải nằm trong device/backend policy.

---

# 734.85 — Haptic Timeline

```axiom
haptic_timeline {
    events
}
```

---

# 734.86 — Input + AXAUDIO

Input:

```text
microphone
 ↓
AXAUDIO
 ↓
audio analysis
 ↓
AXINPUT action
```

AXINPUT không sở hữu PCM processing.

---

# 734.87 — Input + AXGRAPHICS

Graphics có thể cung cấp:

```text
viewport
camera transform
```

AXINPUT cung cấp:

```text
pointer
touch
pen
gesture
```

Không trộn coordinate ownership.

---

# 734.88 — Input + AXCOMPUTE

Heavy processing:

```text
sensor fusion
gesture recognition
prediction
AI input
```

có thể chạy trên AXCOMPUTE.

---

# 734.89 — Input Recording

```axiom
input_recording {
    events
    devices
    clock
    metadata
}
```

---

# 734.90 — Replay

```axiom
replay_input(recording)
```

Replay phải có mode:

```text
real-time
accelerated
step
deterministic
```

---

# 734.91 — Deterministic Input

Record phải giữ:

```text
event order
timestamps
device identity
mapping configuration
input context
```

nếu muốn deterministic replay.

---

# 734.92 — Simulation

```axiom
input_simulator {
    devices
    events
    timing
}
```

Dùng cho:

```text
testing
games
UI
robotics
training
```

---

# 734.93 — Input Fault Injection

Simulation có thể mô phỏng:

```text
device disconnect
dropped events
duplicate events
delayed events
jitter
stuck button
axis noise
```

---

# 734.94 — Security

Input có thể chứa:

```text
keystrokes
touch interaction
voice-derived commands
device identifiers
```

Security boundary:

→ `AXSECURITY`.

---

# 734.95 — Secure Input

Có thể yêu cầu:

```axiom
secure_input {
    trusted_source
    anti_injection
    restricted_observers
}
```

---

# 734.96 — Synthetic Input

Synthetic input phải có provenance:

```axiom
input_origin {
    hardware
    virtual
    replay
    simulation
    accessibility
    ai
}
```

Điều này tránh nhầm:

```text
real user input
```

với:

```text
programmatically generated input
```

---

# 734.97 — Trusted Input

Một số platform có trusted input path.

AXINPUT phải biểu diễn:

```axiom
input_assurance {
    level
    source
}
```

Không tự nâng assurance level.

---

# 734.98 — AI Input

AI có thể tạo:

```text
predicted gesture
suggested action
synthetic controller input
```

Nhưng:

```text
AI prediction ≠ physical user event
```

---

# 734.99 — AI Boundary

AI output phải giữ:

```text
origin = ai
confidence
model reference
timestamp
```

và không tự động vượt qua security policy.

---

# 734.100 — Input Provenance

```axiom
input_provenance {
    source
    transformations
    mappings
    consumers
}
```

---

# 734.101 — Input Audit

Security-sensitive input operations có thể tạo:

```axiom
input_audit_event {
    timestamp
    device
    operation
    principal
}
```

Không ghi raw keystrokes mặc định vào audit log.

---

# 734.102 — Privacy

Runtime phải hỗ trợ:

```text
data minimization
selective recording
redaction
retention policy
permission
```

---

# 734.103 — Input Redaction

Ví dụ:

```axiom
redact_input(
    recording,
    region
)
```

hoặc theo event class.

---

# 734.104 — Device Permissions

Permission model:

```text
none
discovery
read
exclusive
haptic_output
raw_access
```

---

# 734.105 — Exclusive Device Access

Một application có thể yêu cầu:

```axiom
exclusive_input(
    device
)
```

OS/security backend quyết định có cấp hay không.

---

# 734.106 — Input Sharing

Không phải device nào cũng exclusive.

```text
shared
exclusive
observer
```

---

# 734.107 — Input Ownership

Phân biệt:

```text
device ownership
device access
input focus
user assignment
```

Đây là bốn semantic khác nhau.

---

# 734.108 — Input Graph

Input mapping có thể biểu diễn như graph:

```text
Raw Device
    ↓
Normalization
    ↓
Calibration
    ↓
Filter
    ↓
Mapping
    ↓
Action
    ↓
Application
```

---

# 734.109 — Input Graph Compilation

Graph compiler có thể:

```text
constant-fold transforms
fuse mappings
remove unreachable nodes
specialize device layouts
```

---

# 734.110 — Zero Allocation Hot Path

Input event path nên hỗ trợ:

```text
preallocated event pools
ring buffers
stack values
small-value optimization
```

---

# 734.111 — Event Memory

Một event nhỏ nên có thể fit trong compact native structure.

Ví dụ conceptual:

```axiom
input_event {
    timestamp
    device_id
    kind
    payload
}
```

Payload lớn dùng external buffer/reference.

---

# 734.112 — Input Snapshot

```axiom
input_snapshot {
    timestamp
    keys
    buttons
    axes
    pointers
    touches
}
```

Rất hữu ích cho game loop:

```text
read snapshot
 ↓
simulate
 ↓
render
```

---

# 734.113 — Snapshot Consistency

Một snapshot phải có:

```text
single logical timestamp
```

hoặc explicit multi-clock representation.

---

# 734.114 — Frame Input

Application có thể yêu cầu:

```axiom
sample_input_at(frame_time)
```

Nhưng frame time không thay thế input timestamp.

---

# 734.115 — Input Interpolation

Analog input có thể interpolate giữa samples.

Phải đánh dấu:

```text
measured
interpolated
predicted
```

---

# 734.116 — Input Prediction Boundary

Prediction không được ghi đè raw input.

---

# 734.117 — Multi-Device Fusion

Ví dụ:

```text
keyboard
+
mouse
+
gamepad
+
motion sensor
```

có thể tạo một action graph.

---

# 734.118 — Device Capability Query

```axiom
get_capabilities(device)
```

Capabilities:

```text
buttons
axes
pressure
tilt
touch
motion
haptic
raw_access
```

---

# 734.119 — Device State

```axiom
device_state {
    connected
    enabled
    battery
    capabilities
}
```

Battery là optional observation.

---

# 734.120 — Battery

```axiom
battery_state {
    level
    charging
}
```

Không coi battery level luôn chính xác.

---

# 734.121 — Input Error Model

```text
DEVICE_NOT_FOUND
DEVICE_BUSY
ACCESS_DENIED
DEVICE_DISCONNECTED
UNSUPPORTED_CAPABILITY
INVALID_MAPPING
QUEUE_OVERFLOW
INVALID_EVENT
TIMESTAMP_ERROR
BACKEND_ERROR
PERMISSION_DENIED
```

---

# 734.122 — Recovery

Ví dụ:

```text
device disconnected
       ↓
event
       ↓
invalidate handle
       ↓
attempt rediscovery
       ↓
restore mapping
       ↓
resume if policy permits
```

---

# 734.123 — Input Session

```axiom
input_session {
    devices
    contexts
    mappings
    clock
}
```

---

# 734.124 — Session Lifecycle

```text
CREATED
ACTIVE
SUSPENDED
RESUMING
CLOSED
```

---

# 734.125 — Suspend/Resume

Thiết bị mobile:

```text
application
 ↓
suspend
 ↓
devices released
 ↓
resume
 ↓
rediscover
```

Không giữ stale handles.

---

# 734.126 — Input Backend Isolation

Platform-specific code phải nằm sau:

```axiom
input_backend
```

Core AXINPUT không phụ thuộc trực tiếp Win32/X11/Wayland/CoreFoundation/etc.

---

# 734.127 — Native API

```axiom
enumerate_input_devices()
get_input_device()

open_input_device()
close_input_device()

poll_input()
subscribe_input()

create_input_queue()
create_input_snapshot()

create_input_context()
push_input_context()
pop_input_context()

create_input_mapping()
bind_action()

capture_input()
release_input()

assign_device()
unassign_device()

create_gesture_recognizer()

create_sensor()
create_sensor_fusion()

create_haptic_device()
send_haptic()

record_input()
replay_input()

simulate_input()
inject_input_event()

create_input_snapshot()
sample_input_at()

get_device_capabilities()
get_device_state()

calibrate_input()
transform_input()

create_input_session()
```

---

# 734.128 — Formal Invariants

```text
INP-INV-01   Every normalized event has an explicit event kind.
INP-INV-02   Every event has a timestamp.
INP-INV-03   Timestamp clock domain is explicit.
INP-INV-04   Device identity is distinct from OS handle.
INP-INV-05   Device identity is distinct from AXASSET identity.
INP-INV-06   Device lifecycle transitions are explicit.
INP-INV-07   Disconnect invalidates active device handles.
INP-INV-08   Raw events remain distinguishable from normalized events.
INP-INV-09   Physical keys remain distinguishable from logical keys.
INP-INV-10   Text input remains distinct from key events.

INP-INV-11   Touch identities are stable for a contact lifetime.
INP-INV-12   Pointer coordinates have explicit coordinate space.
INP-INV-13   Analog values retain source capability semantics.
INP-INV-14   Calibration is distinct from raw device state.
INP-INV-15   Dead-zone processing is a mapping operation.
INP-INV-16   Synthetic input carries explicit origin metadata.
INP-INV-17   Replay input remains distinguishable from live input.
INP-INV-18   Prediction is distinguishable from measurement.
INP-INV-19   Interpolation is distinguishable from measurement.
INP-INV-20   Input mappings are versionable.

INP-INV-21   Input context precedence is explicit.
INP-INV-22   Input capture is explicit.
INP-INV-23   Focus is distinct from device ownership.
INP-INV-24   Device assignment is distinct from identity authentication.
INP-INV-25   Input routing cannot silently bypass security policy.
INP-INV-26   Raw input access requires explicit capability.
INP-INV-27   Haptic output is distinct from input acquisition.
INP-INV-28   Gesture recognition produces derived events.
INP-INV-29   Sensor fusion produces derived observations.
INP-INV-30   AI-generated input is marked as AI-originated.

INP-INV-31   Input queue overflow behavior is explicit.
INP-INV-32   Real-time input paths cannot require unbounded blocking.
INP-INV-33   Event coalescing is distinguishable from raw event delivery.
INP-INV-34   Input snapshots have explicit temporal semantics.
INP-INV-35   Replay does not mutate the original recording.
INP-INV-36   Simulation cannot mutate production device state.
INP-INV-37   Security authorization belongs to AXSECURITY.
INP-INV-38   UI semantics belong above AXINPUT.
INP-INV-39   Physical device semantics are separated from logical actions.
INP-INV-40   Input provenance is preserved across normalization, mapping, replay, and synthesis.
```

---

# 734.129 — Performance Architecture

Hot path:

```text
Hardware
   ↓
Native Backend
   ↓
Lock-Free Queue
   ↓
Normalization
   ↓
Mapping
   ↓
Action
   ↓
Application
```

Không:

```text
hardware
 ↓
heap allocation
 ↓
reflection
 ↓
generic object graph
 ↓
blocking
```

---

# 734.130 — Compile-Time Mapping

Axiom compiler có thể specialize:

```text
device type
mapping
action layout
transform chain
```

Ví dụ:

```text
Gamepad
 → LeftStick
 → DeadZone
 → Normalize
 → MoveAction
```

có thể compile thành native fast path.

---

# 734.131 — Input SIMD

Có thể vectorize:

```text
axis normalization
sensor processing
touch transformations
motion processing
gesture preprocessing
```

---

# 734.132 — Lock-Free Routing

High-frequency input:

```text
mouse
touch
motion sensor
```

có thể sử dụng:

```text
SPSC queue
MPSC queue
ring buffer
```

tùy topology.

---

# 734.133 — Zero-Copy

Input payload lớn:

```text
raw sensor batch
camera tracking data
gesture data
```

có thể truyền bằng shared immutable buffer.

---

# 734.134 — Deterministic Runtime

Deterministic mode phải cố định:

```text
event order
mapping version
context stack
calibration
clock mapping
random seed nếu có
```

---

# 734.135 — Input Digital Twin

```axiom
input_digital_twin {
    devices
    capabilities
    mappings
    users
    events
    timing
}
```

Cho phép mô phỏng toàn bộ input subsystem mà không cần hardware.

---

# 734.136 — Input Runtime 5.0

```text
                         AXINPUT 5.0
                              │
          ┌───────────────────┼──────────────────┐
          ↓                   ↓                  ↓
       DEVICES              EVENTS             ACTIONS
          │                   │                  │
 keyboard/mouse        raw/normalized       bindings
 touch/pen             timestamps            contexts
 gamepad/sensors        routing              gestures
          │                   │                  │
          └───────────────────┼──────────────────┘
                              ↓
                       INPUT GRAPH
                              ↓
                    APPLICATION / AXUI
                              │
             ┌────────────────┼───────────────┐
             ↓                ↓               ↓
          HAPTICS          REPLAY         SIMULATION
```

---

# 734.137 — Completion Criteria

`BOOTSTRAP-734` phải freeze:

1. Input device.
2. Device classes.
3. Device identity.
4. Device lifecycle.
5. Discovery.
6. Hot plug.
7. Input event.
8. Clock/timestamp.
9. Keyboard.
10. Physical key.
11. Logical key.
12. Text input.
13. IME composition.
14. Modifiers.
15. Key repeat.
16. Pointer.
17. Coordinate spaces.
18. Pointer buttons.
19. Pointer motion.
20. High-resolution input.
21. Wheel.
22. Touch.
23. Multi-touch.
24. Pen.
25. Pressure.
26. Tilt.
27. Eraser/tool state.
28. Gamepad.
29. Analog axes.
30. Trigger.
31. Dead zones.
32. Calibration.
33. Joystick.
34. Hat switch.
35. Wheel/pedal.
36. Controller mapping.
37. Input profiles.
38. Input transforms.
39. Actions.
40. Action states.
41. Action values.
42. Bindings.
43. Chords.
44. Sequences.
45. Context.
46. Context stack.
47. Routing.
48. Propagation.
49. Capture.
50. Focus.
51. Multi-user input.
52. User assignment.
53. Accessibility.
54. Virtual devices.
55. Raw input.
56. Native backend.
57. Polling.
58. Subscription.
59. Queue.
60. Coalescing.
61. Latency.
62. Timestamp preservation.
63. Prediction.
64. Motion sensors.
65. Orientation.
66. Sensor fusion.
67. Gestures.
68. Gesture arbitration.
69. Camera-derived input boundary.
70. Gaze.
71. Haptics.
72. Rumble.
73. Force feedback.
74. Haptic timeline.
75. AXAUDIO integration.
76. AXGRAPHICS integration.
77. AXCOMPUTE integration.
78. Security.
79. Secure input.
80. Synthetic input provenance.
81. AI boundary.
82. Input provenance.
83. Privacy.
84. Permissions.
85. Exclusive access.
86. Input ownership.
87. Input graph.
88. Graph compilation.
89. Zero-allocation hot path.
90. Input snapshots.
91. Snapshot consistency.
92. Frame sampling.
93. Interpolation.
94. Prediction boundary.
95. Multi-device fusion.
96. Capability queries.
97. Device state.
98. Battery state.
99. Error model.
100. Recovery.
101. Input session.
102. Suspend/resume.
103. Backend isolation.
104. Native API.
105. 40 formal invariants.
106. Performance architecture.
107. Compile-time specialization.
108. Lock-free routing.
109. Zero-copy.
110. Deterministic runtime.
111. Input digital twin.
112. Runtime 5.0 architecture.

---

# 734.138 — Definition of Done

```text
BOOTSTRAP-734
STATUS: COMPLETE / FROZEN

AXINPUT
 ├── Device Runtime
 ├── Raw Input
 ├── Normalized Input
 ├── Keyboard
 ├── Text / IME
 ├── Pointer
 ├── Touch
 ├── Pen
 ├── Gamepad
 ├── Joystick
 ├── Wheel / Pedal
 ├── Motion Sensors
 ├── Gesture Runtime
 ├── Input Mapping
 ├── Action System
 ├── Context / Focus
 ├── Multi-User Input
 ├── Accessibility Input
 ├── Virtual Input
 ├── Haptic Output
 ├── Low-Latency Runtime
 ├── Input Recording
 ├── Deterministic Replay
 ├── Simulation
 ├── Security Boundary
 ├── AI Input Boundary
 ├── AXAUDIO Integration
 ├── AXGRAPHICS Integration
 ├── AXCOMPUTE Integration
 ├── Device Recovery
 ├── Input Digital Twin
 └── Human Interaction Runtime 5.0
```

**BOOTSTRAP-734 / AXINPUT — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-735 — AXUI

**Native User Interface Runtime — windows, surfaces, widgets, layout, text, accessibility, focus, input integration, rendering integration, retained/immediate UI models, styling, themes, animation, data binding, forms, menus, dialogs, desktop/mobile UI, DPI/scaling, localization, accessibility tree, UI state, event routing, UI composition, GPU acceleration, native controls, declarative UI, UI compilation, UI testing, deterministic UI replay, UI automation và Axiom User Interface Runtime 5.0.**