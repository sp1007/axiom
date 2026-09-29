# BOOTSTRAP-465 — INPUT SYSTEM, KEYBOARD, MOUSE, TOUCH, PEN, GAMEPAD, IME & UNIFIED EVENT MODEL

**Trạng thái: COMPLETED / LOCKED**

465 xây dựng input foundation dùng chung cho **GUI, editor, game, media, accessibility và interactive applications**.

Nguyên tắc trung tâm:

```text
Physical Input
      ↓
Platform Adapter
      ↓
Input Event
      ↓
Input State
      ↓
Routing / Focus / Capture
      ↓
Application / GUI / Game
```

Và phải phân biệt tuyệt đối:

```text
Physical Key
    ≠ Logical Key
    ≠ Text Input
    ≠ IME Composition
    ≠ Shortcut / Command
```

---

## 465.1 — Input architecture

Input được chia:

```text
input-core
input-platform
input-keyboard
input-pointer
input-touch
input-pen
input-gamepad
input-ime
input-text
input-gesture
input-focus
input-routing
input-mapping
input-record
input-accessibility
```

Không module nào được tự động kéo toàn bộ input stack vào executable.

---

## 465.2 — Input event

Canonical event:

```text
InputEvent {
    timestamp
    device_id
    window_id
    kind
    payload
}
```

---

## 465.3 — Event timestamp

Timestamp phải sử dụng monotonic clock khi dùng để ordering/latency.

Wall-clock chỉ dành cho logging/presentation.

---

## 465.4 — Event sequence

Mỗi input stream có thể có sequence number để phát hiện:

```text
missing
duplicate
reordered
```

events.

---

## 465.5 — Device identity

Device có:

```text
DeviceId
DeviceClass
Capabilities
```

---

## 465.6 — Device class

Canonical classes:

```text
Keyboard
Mouse
Touch
Pen
Gamepad
Controller
TextInput
```

---

## 465.7 — Device capabilities

Ví dụ:

```text
pressure
tilt
rotation
buttons
axes
haptics
touch_count
```

---

# 465.8 — Physical keyboard

Physical keyboard event biểu diễn phím vật lý.

Ví dụ concept:

```text
PhysicalKey::KeyA
PhysicalKey::Enter
PhysicalKey::F1
```

Không đại diện trực tiếp cho Unicode character.

---

## 465.9 — Key state

Các trạng thái:

```text
Down
Up
Repeat
```

---

## 465.10 — Key repeat

Repeat rate/delay thuộc platform configuration.

Application không được giả định một repeat rate cụ thể.

---

## 465.11 — Logical key

Logical key biểu diễn ý nghĩa của phím:

```text
LogicalKey::A
LogicalKey::Enter
LogicalKey::Escape
LogicalKey::ArrowLeft
```

---

## 465.12 — Physical vs logical

Một physical key có thể tạo logical key khác nhau tùy keyboard layout.

---

## 465.13 — Keyboard layout

Keyboard layout là platform/user configuration.

Không hard-code US QWERTY vào input core.

---

## 465.14 — Modifier

Modifiers:

```text
Shift
Ctrl
Alt
Meta
CapsLock
NumLock
ScrollLock
```

có trạng thái độc lập.

---

## 465.15 — Modifier location

Một số platform phân biệt:

```text
LeftShift
RightShift
```

Input layer phải giữ được thông tin này khi platform cung cấp.

---

## 465.16 — Modifier state

Event có thể chứa snapshot modifier state.

---

## 465.17 — Shortcut

Shortcut là higher-level command mapping:

```text
Ctrl + S → Save
Ctrl + Z → Undo
```

không phải keyboard primitive.

---

## 465.18 — Shortcut precedence

Routing xác định precedence giữa:

```text
text input
widget shortcut
local command
window command
global command
```

---

## 465.19 — Shortcut vs text

Một keyboard event không được tự động biến thành text event.

---

# 465.20 — Text input

Text input được cung cấp bởi:

```text
TextInputEvent {
    text
    range/replacement
}
```

và sử dụng 464.

---

## 465.21 — Unicode text

Text input là UTF-8 hợp lệ sau khi platform adapter hoàn tất decoding.

---

## 465.22 — IME

IME là một subsystem riêng.

---

## 465.23 — Composition

IME có trạng thái:

```text
composition text
selection
replacement range
candidate state
```

---

## 465.24 — Composition update

Ứng dụng nhận intermediate composition mà chưa coi đó là committed text.

---

## 465.25 — Commit

IME commit tạo text input chính thức.

---

## 465.26 — Vietnamese input

Input system phải hỗ trợ composition methods của Vietnamese IME mà không giả định text được tạo bằng từng keyboard key.

---

## 465.27 — CJK IME

Chinese/Japanese/Korean composition phải được hỗ trợ thông qua platform IME.

---

## 465.28 — Dead keys

Dead-key sequences được xử lý ở logical/text-input layer phù hợp.

---

## 465.29 — Compose sequences

Compose/dead-key mechanisms không được implement bằng hard-coded Unicode mapping trong application.

---

## 465.30 — Text replacement

IME có thể yêu cầu thay thế một text range.

---

# 465.31 — Mouse

Mouse event:

```text
MouseMove
MouseButtonDown
MouseButtonUp
MouseWheel
MouseHWheel
```

---

## 465.32 — Pointer coordinates

Pointer coordinates có:

```text
window-local
screen/global
content-local
```

và phải xác định coordinate space.

---

## 465.33 — Device pixels vs logical units

Input coordinates phải có scale semantics rõ ràng để tương thích HiDPI.

---

## 465.34 — Mouse buttons

Không giới hạn chỉ left/right/middle ở core.

Có thể biểu diễn extended buttons.

---

## 465.35 — Wheel

Wheel có thể cung cấp:

```text
delta
unit
axis
```

---

## 465.36 — Pixel scrolling

Touchpad có thể cung cấp continuous pixel deltas.

Không ép mọi wheel event thành integer clicks.

---

# 465.37 — Unified pointer

Mouse, touch và pen được quy về:

```text
PointerId
PointerType
Position
Delta
Buttons
Pressure
Tilt
Rotation
Timestamp
```

---

## 465.38 — Pointer type

```text
Mouse
Touch
Pen
Eraser
Unknown
```

---

## 465.39 — Pointer lifecycle

```text
Enter
Move
Down
Up
Cancel
Leave
```

---

## 465.40 — Pointer capture

Window/widget có thể capture pointer.

---

## 465.41 — Capture lifetime

Capture phải được release khi:

```text
pointer up
device cancellation
window destruction
explicit release
```

theo platform semantics.

---

## 465.42 — Multiple pointers

Touch và pen phải hỗ trợ nhiều `PointerId`.

---

# 465.43 — Touch

Touch event có:

```text
id
position
pressure
contact geometry
phase
```

---

## 465.44 — Touch phase

```text
Begin
Move
End
Cancel
```

---

## 465.45 — Touch pressure

Pressure là optional capability.

Không giả định mọi touchscreen hỗ trợ pressure.

---

## 465.46 — Contact geometry

Có thể cung cấp:

```text
radius_x
radius_y
rotation
```

---

## 465.47 — Touch cancellation

OS có thể cancel gesture/touch stream.

Application phải xử lý `Cancel`.

---

## 465.48 — Gesture recognition

Gesture recognition là layer phía trên raw touch.

---

## 465.49 — Gesture

Có thể cung cấp:

```text
Tap
DoubleTap
LongPress
Pan
Pinch
Rotate
Swipe
```

---

## 465.50 — Gesture ambiguity

Raw touch event vẫn phải tồn tại ngay cả khi gesture recognizer hoạt động.

---

# 465.51 — Pen/stylus

Pen hỗ trợ:

```text
pressure
tilt_x
tilt_y
rotation
barrel_buttons
eraser
```

khi hardware/platform cung cấp.

---

## 465.52 — Pen proximity

Một số platform cung cấp proximity events.

Không giả định mọi platform có.

---

## 465.53 — Pen eraser

Eraser có thể được biểu diễn như pointer type hoặc tool state.

---

## 465.54 — Stylus sampling

High-frequency pen events phải giữ timestamp chính xác.

---

## 465.55 — Coalesced events

Platform có thể gom nhiều pointer samples.

Input API có thể expose raw/coalesced samples.

---

## 465.56 — Predicted events

Predicted touch/pen events phải được đánh dấu là prediction.

Không được coi là committed input.

---

# 465.57 — Gamepad

Gamepad API:

```text
GamepadId
Button
Axis
Hat
Trigger
```

---

## 465.58 — Gamepad button

Button state:

```text
pressed
released
value
```

---

## 465.59 — Analog button

Một số buttons có analog value `0..1`.

---

## 465.60 — Analog axis

Axis sử dụng floating-point normalized hoặc raw range theo capability metadata.

---

## 465.61 — Dead zone

Dead-zone không được tự động áp dụng ở raw input layer.

---

## 465.62 — Input mapping

Game/application layer có thể cấu hình:

```text
physical input
      ↓
action
```

---

## 465.63 — Action

Ví dụ:

```text
MoveForward
Jump
Fire
OpenMenu
```

---

## 465.64 — Action state

```text
Pressed
Released
Held
Value
```

---

## 465.65 — Rebinding

User có thể thay đổi mapping mà không thay đổi application semantics.

---

## 465.66 — Multiple bindings

Một action có thể có nhiều bindings.

---

## 465.67 — Chord

Mapping hỗ trợ combination:

```text
Ctrl + S
```

---

## 465.68 — Sequence

Advanced mappings có thể biểu diễn key sequences.

---

# 465.69 — Focus

Input routing phải có focus model.

```text
Application
 → Window
   → View
     → Widget
```

---

## 465.70 — Keyboard focus

Chỉ một target keyboard focus active trong một focus scope.

---

## 465.71 — Focus scope

GUI có thể có nested focus scopes.

---

## 465.72 — Focus transitions

Events:

```text
FocusIn
FocusOut
```

---

## 465.73 — Pointer focus

Pointer hover không đồng nghĩa keyboard focus.

---

## 465.74 — Activation

Window activation khác keyboard focus.

---

# 465.75 — Input routing

Routing pipeline:

```text
OS event
 ↓
platform normalization
 ↓
window
 ↓
capture
 ↓
focus/target
 ↓
preview
 ↓
target
 ↓
bubble
 ↓
application
```

---

## 465.76 — Preview events

GUI có thể intercept event trước target.

---

## 465.77 — Bubble events

Event có thể propagate từ target lên parent hierarchy.

---

## 465.78 — Stop propagation

Handler có thể đánh dấu event handled.

---

## 465.79 — Capture precedence

Captured pointer event đi tới capture target thay vì hit-test target.

---

## 465.80 — Hit testing

Hit testing thuộc GUI/rendering layer, input chỉ tiêu thụ kết quả.

---

# 465.81 — Event queue

Input queue phải có bounded/unbounded policy rõ ràng.

---

## 465.82 — Overflow

Nếu queue bounded:

```textdrop/coalesce/block/fail
```

policy phải explicit.

---

## 465.83 — Move coalescing

High-frequency move events có thể coalesce.

Không coalesce:

```text button transitions
text commits
IME commits
```

một cách tùy tiện.

---

## 465.84 — Event ordering

Trong cùng input stream, ordering phải deterministic.

---

## 465.85 — Cross-device ordering

Events từ các devices khác nhau dựa trên timestamp/sequence/platform ordering contract.

---

## 465.86 — Thread affinity

GUI event processing thường thuộc UI thread.

Input core không ép toàn bộ applications phải single-threaded.

---

## 465.87 — Background input

Raw device acquisition có thể chạy thread riêng.

---

## 465.88 — Transfer

Event crossing thread boundaries phải có ownership semantics rõ ràng.

---

# 465.89 — Raw input

Raw input API expose platform-specific information khi application cần low-level control.

---

## 465.90 — Raw input isolation

Raw input không được phá vỡ safety của safe APIs.

---

## 465.91 — Device-specific APIs

Gaming/professional applications có thể query vendor/device-specific capabilities.

---

## 465.92 — HID

HID-level support thuộc platform/ecosystem layer.

---

## 465.93 — Accessibility

Input layer phải cho phép accessibility systems inject/transform input theo platform rules.

---

## 465.94 — Synthetic input

Synthetic input phải được phân biệt với physical input.

---

## 465.95 — Trust

Application không được mặc định coi synthetic input là physically generated.

---

# 465.96 — Haptics

Haptic output là separate capability:

```text
rumble
vibration
force feedback
```

---

## 465.97 — Haptic ownership

Device haptic resource tuân thủ 423.

---

## 465.98 — Haptic scheduling

Timed effects có timestamp/duration explicit.

---

## 465.99 — Haptic safety

Platform may clamp hardware output according to device policy.

---

## 465.100 — Input/output distinction

Input events và haptic commands không dùng chung semantics.

---

# 465.101 — IME integration

Platform adapters:

```text
Windows IME
macOS input services
Linux IME frameworks
Android IME
iOS text input
WASM/browser composition
```

là platform implementations.

---

## 465.102 — Composition UI

GUI layer có thể hiển thị:

```text composition string
selection
candidate window
caret
```

---

## 465.103 — Candidate window

IME candidate UI không thuộc text core 464.

---

## 465.104 — Text editor integration

Text editor sử dụng:

```text 464 TextBuffer
+
465 TextInput/IME
```

---

## 465.105 — Keyboard shortcut during IME

Application phải tránh xử lý composition keystrokes như ordinary shortcuts khi IME đang active, trừ những commands được platform cho phép.

---

# 465.106 — Accessibility input

Support:

```text keyboard navigation
screen reader commands
switch devices
alternative pointers
```

---

## 465.107 — Semantic actions

GUI nên expose semantic actions:

```text Activate
Cancel
Navigate
Increment
Decrement
```

thay vì bắt accessibility layer giả lập physical keys.

---

# 465.108 — Event recording

Input recorder có thể lưu:

```text timestamp
device
event
payload
```

---

## 465.109 — Deterministic replay

Replay mode injects synthetic events theo recorded timeline.

---

## 465.110 — Replay isolation

Replay không được đọc live input nếu deterministic mode đang bật, trừ explicit merge mode.

---

## 465.111 — Input test

GUI tests có thể inject:

```text key
text
pointer
touch
gamepad
IME
```

events.

---

## 465.112 — IME test

IME composition phải test riêng với committed text.

---

# 465.113 — Input latency

Instrumentation:

```text hardware timestamp
OS receive
application receive
handler start
handler complete
render submit
```

nếu platform hỗ trợ.

---

## 465.114 — Latency metadata

Không được giả định hardware timestamp luôn tồn tại.

---

## 465.115 — High-frequency input

Gaming/stylus applications có thể request raw/high-frequency event stream.

---

## 465.116 — Sampling rate

Không ép input layer xuống frame rate.

---

## 465.117 — Frame synchronization

Renderer có thể sample latest input state mỗi frame.

---

## 465.118 — Event vs state

Phải phân biệt:

```text event = something happened
state = current condition
```

---

## 465.119 — Input snapshot

API:

```text InputSnapshot
```

cho phép game/render thread đọc consistent state.

---

## 465.120 — Snapshot consistency

Snapshot là immutable view tại một logical tick.

---

# 465.121 — State queries

Ví dụ:

```text keyboard.is_down(Key::W)
mouse.position()
gamepad.axis(...)
```

---

## 465.122 — Edge queries

```text pressed_this_frame
released_this_frame
```

là derived state.

---

## 465.123 — Tick boundary

Game engine có thể reset edge states theo simulation tick.

---

## 465.124 — Variable-rate rendering

Input state không phụ thuộc render FPS.

---

## 465.125 — Fixed timestep

465 có thể cung cấp timestamped events cho fixed simulation loop.

---

# 465.126 — Coordinate transformations

Input coordinates có thể transform:

```text screen
→ window
→ viewport
→ content
→ world
```

nhưng world transformation thuộc 460/game engine.

---

## 465.127 — DPI scaling

DPI scale explicit.

---

## 465.128 — Multi-monitor

Screen coordinates phải hỗ trợ displays có scale khác nhau.

---

## 465.129 — Orientation

Mobile input phải xử lý orientation changes.

---

## 465.130 — Safe areas

Safe-area geometry thuộc window/UI layer nhưng input hit regions phải có thể dùng nó.

---

# 465.131 — Mobile gestures

Platform gestures có thể được expose riêng.

---

## 465.132 — Virtual keyboard

Virtual keyboard state:

```text shown
hidden
requested
dismissed
```

---

## 465.133 — Keyboard inset

Mobile platform có thể cung cấp keyboard-induced viewport/inset changes.

---

## 465.134 — Text focus

Text input request phải gắn với focused text target.

---

## 465.135 — Secure text input

Password/security-sensitive widgets có thể request platform secure input mode.

---

# 465.136 — Browser/WASM

Browser input maps:

```text DOM KeyboardEvent
PointerEvent
WheelEvent
TouchEvent
CompositionEvent
Gamepad API
```

vào Axiom model.

---

## 465.137 — Browser text

Browser composition events phải giữ composition/commit distinction.

---

## 465.138 — Browser security

Browser sandbox controls device access.

---

# 465.139 — Freestanding

Freestanding Axiom không có input runtime mặc định.

Application/platform adapter có thể cung cấp input events.

---

## 465.140 — Kernel/input drivers

Kernel-level implementation có thể implement lower-level device drivers outside standard input library.

---

# 465.141 — Performance

Input hot path phải tránh:

```text allocation
virtual dispatch
string construction
```

khi không cần.

---

## 465.142 — Event storage

Fixed-capacity event buffers được hỗ trợ cho realtime/game loops.

---

## 465.143 — Zero allocation

Raw event processing có thể `@no_alloc`.

---

## 465.144 — Coalescing

Pointer movement coalescing phải giảm overhead mà không phá button/text event semantics.

---

## 465.145 — Lock-free queues

SPSC/MPSC queues có thể dùng 424 atomics.

---

## 465.146 — Cache locality

Input state nên dùng compact arrays/bitsets cho keyboard/gamepad state.

---

# 465.147 — Security

Input là external/untrusted data.

---

## 465.148 — Malformed event

Platform adapter phải validate event payload.

---

## 465.149 — Device spoofing

Device identity không được coi là cryptographic identity.

---

## 465.150 — Synthetic event

Synthetic input phải có provenance metadata khi platform có thể cung cấp.

---

## 465.151 — Injection

Applications cần quyền OS/platform để inject global input.

---

## 465.152 — No hidden privileges

Axiom input library không tự yêu cầu elevated/global input privileges.

---

# 465.153 — AI metadata

446 có thể expose:

```text device
event
timestamp
target
routing path
handled_by
capture owner
focus owner
IME state
mapping
```

---

## 465.154 — Explain routing

AI/debugger có thể trả lời:

```text event
→ capture
→ target
→ handler
→ handled
```

---

## 465.155 — Explain shortcut

Có thể inspect:

```text physical key
→ logical key
→ modifiers
→ shortcut
→ command
```

---

## 465.156 — Explain text input

Có thể inspect:

```text keyboard/IME
→ composition
→ commit
→ TextBuffer mutation
```

---

# 465.157 — Testing

Bắt buộc test:

```text keyboard
logical mapping
modifiers
repeat
text
IME
mouse
touch
pen
gamepad
focus
capture
routing
gesture
DPI
multi-monitor
record/replay
```

---

## 465.158 — Unicode/IME tests

464 + 465 phải có test tích hợp cho:

```text Vietnamese
Chinese
Japanese
Korean
Arabic
Hebrew
emoji
```

---

## 465.159 — Replay tests

Recorded input phải tái tạo event sequence chính xác trong deterministic mode.

---

## 465.160 — Fuzzing

Fuzz:

```text event decoder
IME composition
mapping parser
gesture recognizer
device descriptors
```

---

## 465.161 — Stress tests

Test:

```text millions of pointer events
many touch points
rapid key transitions
device connect/disconnect
```

---

## 465.162 — Hotplug

Device connect/disconnect không được crash application.

---

## 465.163 — Device removal

Outstanding device handles phải chuyển sang defined failure state.

---

## 465.164 — Gamepad disconnect

Input state phải reset theo deterministic policy.

---

## 465.165 — Window destruction

Events targeting destroyed windows phải bị discard/cancel theo contract.

---

# 465.166 — Implementation order

### Phase 1

```text
input-core
keyboard
mouse
focus
basic routing
```

### Phase 2

```text
text input
IME
464 integration
```

### Phase 3

```text
touch
pen
unified pointer
gesture
```

### Phase 4

```text
gamepad
input mapping
actions
```

### Phase 5

```text
record/replay
diagnostics
accessibility
```

### Phase 6

```text
platform adapters
Windows
Linux
macOS
iOS
Android
WASM
```

---

# 465.167 — Integration

```text
452 GUI
   ↑
465 Input
   ↑
Platform
```

Text:

```text
465 IME/TextInput
        ↓
464 Text
        ↓
452 Text Widget
```

Game:

```text
465 Input
   ↓
Game/Input Mapping
   ↓
460 Graphics
   ↓
459 GPU
```

---

# 465.168 — Hard invariants

1. Physical key ≠ logical key.
2. Keyboard input ≠ text input.
3. IME composition ≠ committed text.
4. Shortcut ≠ text insertion.
5. UTF-8 committed text uses 464.
6. Keyboard layout is configurable.
7. Unicode input does not depend on keycode assumptions.
8. Key repeat is platform/configuration dependent.
9. Modifier state is explicit.
10. Left/right modifiers can be distinguished when available.
11. Mouse/touch/pen share a unified pointer abstraction.
12. Pointer IDs are stable during a pointer sequence.
13. Touch supports multiple simultaneous pointers.
14. Pointer cancellation is supported.
15. Pointer capture is explicit.
16. Capture is released under defined lifecycle conditions.
17. Pointer coordinates identify their coordinate space.
18. Logical units and physical pixels are distinct.
19. DPI scaling is explicit.
20. Multi-monitor scale differences are supported.
21. Pen pressure is optional.
22. Pen tilt is optional.
23. Pen rotation is optional.
24. Raw pointer samples may exceed render FPS.
25. Coalesced events are distinguishable where necessary.
26. Predicted events are never treated as committed input.
27. Gamepad analog values are preserved.
28. Dead zones are not silently applied at raw layer.
29. Input mapping is higher-level than device events.
30. Actions are distinct from physical devices.
31. User rebinding does not change application action semantics.
32. Multiple bindings per action are supported.
33. Chords can be represented.
34. Input state is distinct from input events.
35. Snapshots provide consistent state views.
36. Edge states are derived explicitly.
37. Fixed simulation can consume timestamped input.
38. Input is not tied to render FPS.
39. Focus is explicit.
40. Keyboard focus is distinct from pointer hover.
41. Window activation is distinct from keyboard focus.
42. Event routing is explicit.
43. Preview routing is supported.
44. Bubble routing is supported.
45. Event handling can stop propagation.
46. Capture takes precedence over normal pointer hit testing.
47. Hit testing belongs to GUI/rendering layer.
48. Input queues have explicit overflow semantics.
49. Button transitions must not be silently coalesced.
50. Text commits must not be silently dropped.
51. IME intermediate composition is preserved.
52. CJK IME is supported.
53. Vietnamese IME is supported.
54. Dead keys are supported.
55. Composition replacement ranges are supported.
56. Text editing integrates with 464 TextBuffer.
57. Accessibility can operate through semantic actions.
58. Synthetic input is distinguishable where possible.
59. Device identity is not treated as cryptographic identity.
60. Input does not grant hidden OS privileges.
61. Raw input remains explicitly low-level.
62. Global input injection requires platform authorization.
63. Haptic output is separate from input semantics.
64. Device hotplug is supported.
65. Device removal cannot crash safe applications.
66. Gamepad disconnect has defined state behavior.
67. Destroyed-window events have defined cancellation behavior.
68. Event timestamps use monotonic time for ordering/latency.
69. Wall-clock is not used for event ordering.
70. Cross-thread event ownership is explicit.
71. GUI thread affinity is platform-defined.
72. Input acquisition may run independently from UI processing.
73. SPSC/MPSC queues may integrate with 424.
74. Realtime input paths can be allocation-free.
75. Input state should be cache-efficient.
76. Browser input is adapted to the same semantic model.
77. WASM/browser permissions remain external.
78. Mobile virtual keyboard is explicit.
79. Secure text input can request platform protection.
80. Keyboard-induced viewport changes are represented explicitly.
81. Accessibility input is not required to emulate physical keys.
82. Input recording stores sufficient event provenance.
83. Deterministic replay is supported.
84. Replay can disable live input explicitly.
85. Event decoders are fuzz-tested.
86. IME paths are fuzz-tested.
87. Gesture recognition is fuzz-tested.
88. Device descriptors are validated.
89. Large event bursts are stress-tested.
90. AI can inspect input routing.
91. AI can inspect focus/capture.
92. AI can inspect keyboard→logical-key→shortcut conversion.
93. AI can inspect IME composition.
94. AI can inspect action mappings.
95. Input diagnostics are machine-readable.
96. Input modules are independently linkable.
97. Input does not require GUI.
98. Input does not require GPU.
99. Input does not require a mandatory runtime.
100. Input uses explicit ownership.
101. Input does not require GC.
102. Input does not require a borrow checker.
103. Input can operate in headless environments.
104. Platform-specific features remain adapters.
105. Core semantics remain platform-neutral.
106. Input events are not implicitly converted into strings.
107. Unicode text is handled by 464.
108. GUI commands are distinct from low-level input.
109. Game actions are distinct from raw devices.
110. No hidden input polling thread is introduced.
111. No hidden allocation is required by the core event model.
112. No hidden global mutable state is required.
113. Deterministic event ordering is defined within supported guarantees.
114. Input latency can be instrumented.
115. High-frequency input can bypass frame-rate throttling.
116. Axiom can implement the core input layer without LLVM/GCC/Clang.
117. **Axiom input must provide a low-level, high-performance and deterministic foundation from physical devices through Unicode/IME and semantic actions, without conflating hardware events, text entry, commands, or application state.**

**BOOTSTRAP-465 hoàn tất.**

---

# BOOTSTRAP-466 — ACCESSIBILITY, SEMANTIC UI, SCREEN READER, NAVIGATION, AUTOMATION & ASSISTIVE TECHNOLOGY CONTRACT

Tiếp theo là lớp accessibility, đặt **trên 452 GUI + 464 Text + 465 Input**, nhưng vẫn phải độc lập với một GUI toolkit cụ thể:

```text
              Axiom UI
                 │
        ┌────────┴────────┐
        ↓                 ↓
   Visual Tree       Semantic Tree
        │                 │
        ↓                 ↓
   Rendering        Accessibility
                          │
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
     Screen Reader    Keyboard Nav     Automation
          ↓               ↓               ↓
       OS AT APIs / Platform Accessibility
```

466 sẽ khóa các vấn đề:

- semantic tree độc lập visual tree;
- accessible role/name/value/state;
- labels và descriptions;
- focus vs accessibility focus;
- keyboard navigation;
- tab order;
- spatial navigation;
- screen reader;
- live regions;
- announcements;
- accessibility actions;
- UI automation;
- semantic hit testing;
- high-contrast/reduced-motion preferences;
- font/text scaling;
- platform accessibility bridges;
- Windows UI Automation;
- macOS/iOS accessibility;
- Android accessibility;
- Linux accessibility;
- browser/WASM accessibility;
- custom-rendered UI vẫn phải accessible;
- game/custom graphics accessibility;
- accessibility tree caching;
- dynamic UI updates;
- virtualized lists;
- disabled/hidden/offscreen semantics;
- localization qua 464;
- input integration qua 465;
- accessibility metadata cho AI tooling;
- security/privacy của accessibility APIs;
- không biến accessibility thành dependency bắt buộc của mọi executable.

**Nguyên tắc cốt lõi của 466:**

```text
Visual representation
        ≠
Interaction representation
        ≠
Accessibility representation
```

Một UI có thể được render hoàn toàn bằng GPU/custom graphics nhưng vẫn phải có một **semantic accessibility tree** mà screen reader, keyboard navigation, automation và assistive technology có thể sử dụng.