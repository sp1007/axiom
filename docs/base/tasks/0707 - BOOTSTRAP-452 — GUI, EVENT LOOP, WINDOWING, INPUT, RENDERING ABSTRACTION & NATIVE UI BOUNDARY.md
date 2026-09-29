# BOOTSTRAP-452 — GUI, EVENT LOOP, WINDOWING, INPUT, RENDERING ABSTRACTION & NATIVE UI BOUNDARY

**Trạng thái: COMPLETED / LOCKED**

Axiom GUI được thiết kế như **library/ecosystem layer**, không phải language core và không phải mandatory runtime.

Mục tiêu:

```text
Axiom Core
    ↓
Core/Std
    ↓
Platform Abstraction
    ↓
Window + Event
    ↓
UI Toolkit / Scene Graph
    ↓
Renderer
    ↓
GPU / CPU / Native Platform
```

Một chương trình:

```text
fn main() -> i32 {
    42
}
```

không được kéo GUI runtime vào binary.

---

## 452.1 — GUI layering

GUI stack gồm:

```text
gui-core
gui-platform
gui-input
gui-layout
gui-text
gui-render
gui-widgets
gui-accessibility
gui-app
```

Các tầng phụ thuộc một chiều.

---

## 452.2 — No GUI in language core

Compiler chỉ cung cấp:

```text
struct
enum
trait
generic
comptime
SIMD
GPU/FFI primitives
```

không cung cấp `Window`, `Button`, `Canvas` như built-in types.

---

## 452.3 — Window abstraction

Conceptual:

```text
Window
WindowId
WindowConfig
WindowHandle
```

---

## 452.4 — Window ownership

Window là resource-owning object.

Drop phải giải phóng native window resource theo platform contract.

---

## 452.5 — Window configuration

Bao gồm:

```text
title
size
position
minimum_size
maximum_size
resizable
fullscreen
visibility
decorations
high_dpi
```

---

## 452.6 — Logical vs physical pixels

GUI API phải phân biệt:

```text
logical_size
physical_size
scale_factor
```

---

## 452.7 — HiDPI

Scale factor là runtime/platform property.

Không hard-code 1.0.

---

## 452.8 — Monitor

API có thể expose:

```text
Monitor
MonitorId
MonitorInfo
```

với:

```text
resolution
scale
refresh_rate
work_area
```

---

## 452.9 — Multi-monitor

Window có thể chuyển giữa monitors.

---

## 452.10 — Window lifecycle

Lifecycle:

```text
created
shown
hidden
minimized
maximized
focused
unfocused
closing
closed
```

---

# 452.11 — Event model

Event là typed enum thay vì string-based messages.

Ví dụ:

```text
enum WindowEvent {
    Resized(Size),
    Moved(Position),
    Focused,
    Unfocused,
    CloseRequested,
    Closed
}
```

---

## 452.12 — Input event

```text
KeyDown
KeyUp
TextInput
MouseMove
MouseButton
MouseWheel
Touch
Pen
Gamepad
```

---

## 452.13 — Physical key vs logical key

Phải phân biệt:

```text
PhysicalKey
LogicalKey
```

để hỗ trợ keyboard layout.

---

## 452.14 — Text input

`KeyDown` không được coi là text input.

Text composition phải hỗ trợ IME.

---

## 452.15 — IME

GUI input layer phải hỗ trợ:

```text
composition_start
composition_update
composition_end
```

---

## 452.16 — Unicode input

Text input là Unicode-aware.

---

## 452.17 — Clipboard

Clipboard là platform capability.

Hỗ trợ:

```text
text
binary/custom formats
```

khi platform cho phép.

---

## 452.18 — Drag and drop

Optional GUI capability:

```text
DragEnter
DragOver
Drop
DragLeave
```

---

## 452.19 — Pointer model

Pointer event chứa:

```text
position
device
buttons
modifiers
timestamp
```

---

## 452.20 — Pointer coordinates

Coordinates có thể được biểu diễn trong:

```text
screen
window
client
widget
scene
```

với explicit transformation.

---

# 452.21 — Event loop

Event loop là library/runtime component.

Không phải compiler primitive bắt buộc.

---

## 452.22 — Native event loop

Platform adapter có thể map trực tiếp:

```text
Windows → native message loop
Linux → selected backend
macOS → native event system
iOS → native event system
Android → native event system
Web → browser event loop
```

---

## 452.23 — One UI thread

UI toolkit mặc định có một UI/event thread.

---

## 452.24 — UI thread affinity

UI objects có thể có thread-affinity contract.

---

## 452.25 — Cross-thread UI mutation

Không được implicit.

Phải sử dụng:

```text
dispatch
post
invoke
channel
```

---

## 452.26 — Event dispatch

Event pipeline:

```text
platform event
→ normalized event
→ application event
→ hit testing
→ capture
→ target
→ bubbling
```

---

## 452.27 — Event propagation

Widget toolkit có thể hỗ trợ:

```text
capture
target
bubble
```

---

## 452.28 — Event cancellation

Event có thể có:

```text
handled
stop_propagation
prevent_default
```

---

## 452.29 — Event timestamps

Platform timestamps nên được chuyển thành monotonic `Instant`.

---

## 452.30 — Event queue

Queue implementation không được bắt buộc heap allocation cho từng event.

---

# 452.31 — Application lifecycle

Application states:

```text
launch
active
inactive
background
suspended
terminated
```

target-dependent.

---

## 452.32 — Mobile lifecycle

iOS/Android lifecycle phải được expose qua platform abstraction.

---

## 452.33 — Background execution

Không được giả định desktop-style unlimited background execution trên mobile.

---

## 452.34 — Web lifecycle

WASM/Web application chạy trong browser event model.

---

# 452.35 — UI object model

Axiom GUI không dùng class inheritance.

Ví dụ:

```text
struct Button {
    text: String
    enabled: bool
}
```

Methods:

```text
fn set_text(self: mut Button, text: String)
```

---

## 452.36 — Widget composition

Composition là primary reuse mechanism.

```text
Panel {
    children: Vec<Widget>
}
```

---

## 452.37 — Widget trait

Conceptual:

```text
trait Widget {
    fn measure(self: &WidgetContext, constraint: Size) -> Size
    fn layout(self: &mut WidgetContext, rect: Rect)
    fn render(self: &WidgetContext, canvas: &mut Canvas)
}
```

Exact borrow syntax sẽ tuân theo final reference/view syntax.

---

## 452.38 — No class hierarchy

Không có:

```text
Button : Control : Widget : Object
```

---

## 452.39 — Trait composition

Capabilities dùng trait:

```text
Focusable
Clickable
Scrollable
TextInput
Accessible
```

---

## 452.40 — Dynamic widget

Khi runtime heterogeneous collection cần thiết:

```text
dyn Widget
```

được dùng explicit.

---

# 452.41 — Layout engine

Layout tách khỏi rendering.

---

## 452.42 — Measure/arrange

Mô hình có thể dùng:

```text
measure()
arrange()
render()
```

---

## 452.43 — Constraints

Layout constraints có:

```text
min
preferred
max
```

---

## 452.44 — Layout units

GUI phải hỗ trợ:

```text
logical pixel
physical pixel
percentage
fraction
auto
```

nếu toolkit cần.

---

## 452.45 — Flex layout

Flex-like layout là library feature.

---

## 452.46 — Grid layout

Grid layout là library feature.

---

## 452.47 — Absolute layout

Canvas/absolute positioning được hỗ trợ.

---

## 452.48 — Custom layout

Developer có thể implement layout trait.

---

# 452.49 — Rendering architecture

Renderer abstraction:

```text
Canvas
Paint
Brush
Image
Font
Path
Transform
Clip
```

---

## 452.50 — Retained vs immediate rendering

Axiom GUI hỗ trợ cả:

```text
retained UI
immediate/custom rendering
```

---

## 452.51 — Scene graph

Retained UI có thể có scene/widget tree.

---

## 452.52 — Render tree

Layout tree không nhất thiết phải giống render tree.

---

## 452.53 — Dirty regions

Renderer có thể track dirty regions.

---

## 452.54 — Partial redraw

Không redraw toàn bộ window nếu platform/backend có thể tránh.

---

## 452.55 — Double buffering

Renderer hỗ trợ double/triple buffering khi backend yêu cầu.

---

## 452.56 — VSync

VSync là explicit renderer/present configuration.

---

## 452.57 — Frame pacing

Renderer có thể expose frame pacing.

---

## 452.58 — Refresh rate

Application có thể query target refresh rate.

---

## 452.59 — Animation clock

Animation dùng monotonic clock.

---

## 452.60 — Frame callback

Conceptual:

```text
on_frame(timestamp)
```

---

# 452.61 — GPU rendering

GPU backend là optional.

---

## 452.62 — CPU renderer

CPU fallback phải có thể tồn tại cho:

```text
headless
software rendering
testing
low-end environments
```

---

## 452.63 — GPU abstraction

Không khóa GUI vào một API cụ thể.

Conceptual:

```text
GraphicsDevice
Buffer
Texture
Sampler
Shader
Pipeline
CommandList
Surface
```

---

## 452.64 — Backend independence

Possible backends:

```text
Direct3D
Vulkan
Metal
OpenGL
WebGPU
software
```

---

## 452.65 — Rendering API vs GPU API

GUI rendering API không expose toàn bộ low-level GPU API.

Hai tầng phải tách biệt.

---

## 452.66 — Custom GPU access

Developer có thể xuống GPU abstraction thấp hơn khi cần.

---

## 452.67 — Shader model

Shader source/IR là ecosystem/backend concern.

---

## 452.68 — Shader compilation

Có thể dùng Axiom shader toolchain về sau.

Không yêu cầu compiler core hiện tại phải compile mọi shader language.

---

## 452.69 — GPU resources

GPU resources có explicit ownership.

---

## 452.70 — GPU synchronization

GPU synchronization không được nhầm với CPU mutex/atomic model.

---

# 452.71 — Text rendering

Text rendering là subsystem riêng.

---

## 452.72 — Font abstraction

```text
Font
FontFace
FontFamily
FontStyle
FontWeight
```

---

## 452.73 — Text shaping

Complex text shaping phải được hỗ trợ ở toolkit/backend.

---

## 452.74 — Bidirectional text

Unicode bidirectional layout được hỗ trợ.

---

## 452.75 — Script shaping

Không assume Latin-only.

---

## 452.76 — Glyph runs

Text layout có thể produce glyph runs.

---

## 452.77 — Text measurement

API phải trả:

```text
advance
bounds
baseline
line_height
```

---

## 452.78 — Font fallback

Font fallback phải configurable.

---

## 452.79 — Text selection

Text widgets hỗ trợ selection ranges.

---

## 452.80 — Cursor/IME

Text editor phải integrate:

```text
caret
selection
composition
```

---

# 452.81 — Accessibility

Accessibility là first-class GUI subsystem.

---

## 452.82 — Accessibility tree

UI toolkit có semantic accessibility tree độc lập render tree.

---

## 452.83 — Roles

Ví dụ:

```text
button
checkbox
textbox
list
tree
menu
dialog
```

---

## 452.84 — Accessible names

Widget phải có accessible label/name khi appropriate.

---

## 452.85 — Keyboard navigation

Focus traversal là explicit toolkit behavior.

---

## 452.86 — Screen reader

Platform adapters bridge accessibility APIs.

---

## 452.87 — High contrast

Toolkit có thể support system accessibility settings.

---

## 452.88 — Reduced motion

Animation system có thể respect system reduced-motion preference.

---

# 452.89 — Styling

Style system là library layer.

---

## 452.90 — No mandatory CSS

Web target có thể map style concepts sang CSS, nhưng native GUI không phụ thuộc CSS.

---

## 452.91 — Theme

Theme là data/configuration.

---

## 452.92 — Style inheritance

Style inheritance có thể tồn tại ở toolkit layer nhưng không phải language inheritance.

---

## 452.93 — Resource dictionaries

Theme resources có thể được keyed bằng typed identifiers.

---

## 452.94 — Hot reload

Optional development feature.

Không ảnh hưởng release semantics.

---

# 452.95 — Data binding

Data binding là optional GUI library feature.

---

## 452.96 — Reactive state

Có thể implement bằng:

```text
Signal
Observable
Store
Event
```

library types.

---

## 452.97 — No mandatory reactive runtime

Core GUI không yêu cầu reactive engine.

---

## 452.98 — State ownership

UI state ownership phải tuân Axiom ownership model.

---

## 452.99 — Async UI

Async task không tự động chạy UI mutation.

---

## 452.100 — UI dispatch

Explicit:

```text
ui.dispatch(fn)
```

hoặc tương đương.

---

# 452.101 — Native widgets

Toolkit có thể cung cấp native widget backend.

---

## 452.102 — Custom widgets

Toolkit cũng phải cho phép fully custom rendered widgets.

---

## 452.103 — Native/custom hybrid

Application có thể trộn hai loại.

---

## 452.104 — Widget abstraction

Application code không nên phụ thuộc native implementation khi dùng portable widget API.

---

## 452.105 — Platform-specific escape hatch

Native handle phải có explicit API.

---

## 452.106 — Native window handle

Có thể expose:

```text
HWND
NSWindow*
UIView*
android window/context
Web DOM handle
```

thông qua target-specific types.

---

## 452.107 — Unsafe native access

Native handle operations có thể yêu cầu unsafe.

---

# 452.108 — GUI and FFI

GUI platform backend sử dụng FFI 451.

---

## 452.109 — GUI runtime

GUI runtime chỉ link khi GUI package được sử dụng.

---

## 452.110 — No hidden GUI thread

GUI toolkit không được tự spawn background thread trừ khi explicitly documented capability.

---

## 452.111 — Renderer threads

Renderer có thể có worker threads nếu application/runtime profile cho phép.

---

## 452.112 — GPU worker

GPU driver threads thuộc platform/backend, không phải Axiom semantic guarantee.

---

# 452.113 — Headless mode

GUI framework phải hỗ trợ headless/test mode khi khả thi.

---

## 452.114 — Screenshot testing

Renderer có thể tạo deterministic screenshot fixtures.

---

## 452.115 — Golden rendering

Rendering tests có:

```text
scene
target
renderer
expected image
tolerance
```

---

## 452.116 — Pixel tolerance

Anti-aliasing/GPU differences phải có configurable tolerance.

---

## 452.117 — UI automation

Widget tree có semantic IDs để testing.

---

## 452.118 — Deterministic UI tests

Test environment có thể control:

```text
clock
input
window size
DPI
randomness
```

---

## 452.119 — Event replay

Event stream có thể được record/replay.

---

## 452.120 — GUI fuzzing

Input/event parser có thể fuzz.

---

# 452.121 — Web target

WASM GUI adapter có thể map:

```text
Window → browser canvas/viewport
Event → DOM events
Clipboard → browser API
GPU → WebGPU
```

---

## 452.122 — Browser sandbox

WASM GUI chịu browser capability/security model.

---

## 452.123 — Native file APIs

Web target không được giả định native filesystem access.

---

## 452.124 — Mobile UI

Mobile toolkit có thể map native controls hoặc custom renderer.

---

## 452.125 — Desktop UI

Desktop toolkit có thể sử dụng native controls hoặc custom renderer.

---

# 452.126 — GUI package structure

Đề xuất:

```text
axiom.gui.core
axiom.gui.window
axiom.gui.input
axiom.gui.layout
axiom.gui.text
axiom.gui.render
axiom.gui.widgets
axiom.gui.accessibility
axiom.gui.platform.windows
axiom.gui.platform.linux
axiom.gui.platform.macos
axiom.gui.platform.ios
axiom.gui.platform.android
axiom.gui.platform.web
```

---

## 452.127 — Dependency granularity

Application chỉ link package capabilities thực sự sử dụng.

---

## 452.128 — GUI binary size

Simple GUI application không nên kéo toàn bộ graphics stack nếu chỉ dùng native widgets.

---

## 452.129 — Renderer selection

Renderer selection có thể compile-time hoặc runtime tùy deployment requirement.

---

## 452.130 — Backend fallback

Nếu application yêu cầu portable rendering, fallback chain có thể là:

```text
GPU backend
→ alternate GPU backend
→ software
```

---

# 452.131 — GUI performance

GUI benchmark gồm:

```text
startup
window creation
event dispatch
layout
text layout
render
frame time
memory
allocation
```

---

## 452.132 — Frame budget

Toolkit có thể report frame budget violations.

---

## 452.133 — Frame timing

Report:

```text
CPU frame time
GPU frame time
present latency
```

khi backend hỗ trợ.

---

## 452.134 — Allocation-free rendering

Renderer có thể cung cấp APIs designed for `@no_alloc` frame rendering.

---

## 452.135 — Object pooling

Pooling là implementation/library optimization, không phải mandatory GUI behavior.

---

# 452.136 — GUI error model

GUI APIs dùng:

```text
Result
Option
panic
```

theo 425.

---

## 452.137 — Device loss

GPU device loss phải trở thành explicit recoverable/error state.

---

## 452.138 — Window creation failure

Window creation trả `Result` khi failure recoverable.

---

## 452.139 — Event loop failure

Fatal platform failure có thể panic/abort tùy runtime contract.

---

## 452.140 — Shutdown

Application shutdown phải cleanup GUI resources deterministically.

---

# 452.141 — GUI metadata

Widgets có semantic metadata:

```text
type
properties
events
layout
accessibility
thread_affinity
allocation
```

---

## 452.142 — AI GUI query

AI tooling có thể query:

```text
find widget
find event handler
find layout owner
find renderer
find platform backend
```

---

## 452.143 — UI source mapping

GUI runtime errors có thể map back đến:

```text
widget declaration
event handler
layout function
render function
```

---

## 452.144 — UI inspector

Development toolkit có thể inspect widget tree.

---

## 452.145 — Runtime UI inspector

Inspector là optional development capability, không link release mặc định.

---

# 452.146 — GUI resource system

Resources:

```text
image
font
icon
shader
style
localized text
```

được package/build system quản lý.

---

## 452.147 — Resource embedding

Small resources có thể embed vào binary.

---

## 452.148 — External resources

Large assets có thể remain external.

---

## 452.149 — Resource hashing

Build system tracks resource hashes for incremental builds.

---

## 452.150 — Hard invariants

1. GUI không thuộc language core.
2. GUI không thuộc mandatory runtime.
3. Window là resource có ownership.
4. Window lifecycle phải explicit.
5. Logical/physical pixels phải phân biệt.
6. DPI/scale factor phải được hỗ trợ.
7. Multi-monitor phải được hỗ trợ ở desktop-capable targets.
8. Event model phải typed.
9. Keyboard physical/logical identity phải phân biệt.
10. Text input phải tách khỏi raw key events.
11. IME phải được hỗ trợ.
12. Unicode input phải được hỗ trợ.
13. Clipboard là capability.
14. Drag-and-drop là optional capability.
15. Event loop là library/runtime component.
16. UI thread affinity phải explicit.
17. Cross-thread UI mutation không được implicit.
18. Event propagation phải deterministic.
19. Event timestamps nên dùng monotonic time.
20. Application lifecycle phải được model.
21. Mobile lifecycle phải được model riêng.
22. Web lifecycle phải tôn trọng browser model.
23. GUI object model không dùng class inheritance.
24. Widget composition là reuse mechanism chính.
25. Trait capability được dùng thay inheritance.
26. `dyn Trait` chỉ dùng khi dynamic dispatch thực sự cần.
27. Layout tách khỏi rendering.
28. Measure/arrange hoặc equivalent constraint model phải tồn tại.
29. Custom layout được hỗ trợ.
30. Retained UI và custom/immediate rendering có thể coexist.
31. Dirty-region/partial redraw phải khả dụng.
32. Double/triple buffering phải được backend hỗ trợ khi cần.
33. VSync phải explicit.
34. GPU rendering là optional.
35. CPU/software renderer phải có thể tồn tại.
36. GUI không bị khóa vào một GPU API.
37. Native GPU backends có thể coexist.
38. GPU resource ownership phải explicit.
39. CPU synchronization không được nhầm với GPU synchronization.
40. Text rendering là subsystem riêng.
41. Unicode shaping phải được hỗ trợ.
42. BiDi text phải được hỗ trợ.
43. Font fallback phải được hỗ trợ.
44. IME phải tích hợp với text editing.
45. Accessibility là first-class subsystem.
46. Accessibility tree tách khỏi render tree.
47. Keyboard navigation được hỗ trợ.
48. Native screen-reader APIs có thể được bridge.
49. Reduced-motion/high-contrast preferences có thể được expose.
50. Styling không thuộc language core.
51. CSS không phải dependency bắt buộc của native GUI.
52. Theme là library data/configuration.
53. Reactive/data binding là optional.
54. GUI state tuân ownership model.
55. Async không tự động mutate UI.
56. UI dispatch phải explicit.
57. Native widget và custom widget đều được hỗ trợ.
58. Native handles là explicit platform escape hatch.
59. Native handles không tự động trở thành portable objects.
60. GUI platform backend sử dụng FFI architecture 451.
61. GUI không được tự spawn hidden threads.
62. Headless mode phải được hỗ trợ khi backend cho phép.
63. Screenshot/golden rendering testing phải tồn tại.
64. Pixel comparison phải có tolerance.
65. UI automation phải có semantic identity.
66. Event replay phải khả dụng.
67. GUI fuzzing phải khả dụng.
68. WASM GUI phải tôn trọng browser sandbox.
69. Mobile GUI phải tôn trọng platform lifecycle.
70. GUI package phải modular.
71. Binary size phải scale theo capabilities sử dụng.
72. Renderer không được bắt buộc với native-widget-only application.
73. Resource embedding phải explicit.
74. Resource hashing phải tích hợp incremental build.
75. GUI performance phải benchmark được.
76. Frame timing phải inspect được khi backend hỗ trợ.
77. Allocation behavior của renderer có thể được đo.
78. GUI failures dùng Result/Option/panic/abort model 425.
79. GPU device loss phải có error model.
80. GUI resources phải cleanup deterministic.
81. GUI semantic metadata tích hợp metadata system 446.
82. AI có thể query widget/event/layout/render relationships.
83. UI inspector là development capability, không phải release requirement.
84. GUI runtime errors phải có source mapping khi debug info bật.
85. Native platform implementation không được làm thay đổi Axiom language semantics.
86. Platform-specific functionality phải nằm sau explicit platform boundary.
87. Portable GUI API không được giả định mọi platform có cùng capabilities.
88. Unsupported capability phải được biểu diễn explicit, không silently emulate khi semantics khác.
89. GUI toolkit không được biến thành mandatory dependency của console/freestanding applications.
90. **Axiom phải có khả năng xây một GUI framework native, composable, high-performance và cross-platform hoàn toàn ở library/platform layer mà không làm phình language core hoặc runtime bắt buộc.**

**BOOTSTRAP-452 hoàn tất.**

---

# BOOTSTRAP-453 — GPU, SIMD, VECTOR TYPES, COMPUTE, TENSOR FOUNDATION & CPU/GPU EXECUTION MODEL

Task tiếp theo khóa phần **CPU + SIMD + GPU compute**.

Đây là nền tảng quan trọng nếu Axiom về sau muốn hỗ trợ:

```text
graphics
image processing
signal processing
scientific computing
tensor
AI/ML
GPU compute
```

nhưng vẫn giữ nguyên nguyên tắc:

```text
Language Core
     ↓
CPU scalar
     ↓
SIMD
     ↓
GPU abstraction
     ↓
Tensor/ML libraries
```

**GPU không phải một “CPU thứ hai” được compiler tự động sử dụng.**

---

## 453.1 — Execution domains

Axiom phân biệt:

```text
CPU
SIMD
GPU
```

---

## 453.2 — Scalar CPU execution

Đây là default execution domain.

---

## 453.3 — SIMD execution

SIMD là vectorized CPU execution.

---

## 453.4 — GPU execution

GPU execution là explicit compute/render capability.

---

## 453.5 — No implicit GPU offload

Một function CPU bình thường không tự nhiên chạy GPU.

---

## 453.6 — GPU kernel

Conceptual:

```text
kernel fn add(...)
```

hoặc equivalent syntax sẽ được khóa ở GPU-language task riêng.

---

## 453.7 — Separate address spaces

GPU memory model phải phân biệt:

```text
host
device
shared
constant
local
```

khi backend hỗ trợ.

---

## 453.8 — CPU pointer ≠ GPU pointer

Không được coi device pointer là CPU-accessible pointer.

---

## 453.9 — GPU resource handles

GPU resources là explicit owned/borrowed handles.

---

## 453.10 — GPU context/device

Application chọn:

```text
GpuInstance
GpuAdapter
GpuDevice
Queue
```

theo abstraction layer.

---

## 453.11 — Queue

GPU submission đi qua explicit queue abstraction.

---

## 453.12 — Command buffer

GPU commands được record thành command buffer/list khi backend yêu cầu.

---

## 453.13 — Synchronization

GPU synchronization explicit.

---

## 453.14 — Fence

Fence được dùng để synchronize host/device hoặc queue work.

---

## 453.15 — Semaphore

Queue synchronization có thể sử dụng semaphore-like primitives.

---

## 453.16 — Event

GPU completion event có thể integrate với async runtime.

---

## 453.17 — Async GPU

GPU operation có thể return future/event nhưng không bắt buộc.

---

## 453.18 — Blocking GPU wait

Blocking wait phải explicit.

---

## 453.19 — Device loss

Device loss là recoverable error nếu backend/platform cho phép recovery.

---

## 453.20 — Resource lifetime

GPU resource drop phải respect pending GPU work.

---

# 453.21 — SIMD types

Core/library phải hỗ trợ portable vector concepts.

Ví dụ:

```text
vec<T, 4>
vec<T, 8>
```

---

## 453.22 — SIMD lane count

Lane count là type-level information khi static vector.

---

## 453.23 — SIMD scalar element

Element type phải là SIMD-compatible primitive.

---

## 453.24 — SIMD arithmetic

Support:

```text
add
sub
mul
div
min
max
```

khi target hỗ trợ.

---

## 453.25 — SIMD comparison

Comparison trả mask/vector mask.

---

## 453.26 — SIMD mask

Mask representation phải target-aware.

---

## 453.27 — SIMD select

`select(mask, a, b)` là fundamental operation.

---

## 453.28 — SIMD load/store

Aligned và unaligned operations phải phân biệt khi relevant.

---

## 453.29 — SIMD gather/scatter

Optional target capability.

---

## 453.30 — SIMD reduction

Support:

```text
sum
min
max
and
or
```

khi available.

---

## 453.31 — Auto-vectorization

Optimizer có thể vectorize scalar loops.

---

## 453.32 — Explicit SIMD

Developer có thể yêu cầu vectorization/SIMD explicitly.

---

## 453.33 — Vectorization safety

Compiler phải preserve overflow, NaN, aliasing và ordering semantics theo language rules.

---

## 453.34 — Floating-point vectorization

Fast-math transformations không được mặc định.

---

## 453.35 — Fast math

Có thể có explicit profile/attribute:

```text
@fast_math
```

với semantics được định nghĩa rõ.

---

## 453.36 — Deterministic math

Library có thể cung cấp deterministic math profile.

---

## 453.37 — CPU feature detection

Runtime có thể query:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

hoặc future extensions.

---

## 453.38 — CPU feature dispatch

Có thể compile multiple variants:

```text
generic
avx2
avx512
```

---

## 453.39 — Dispatch selection

Runtime CPU feature dispatch phải explicit.

---

## 453.40 — Compile-time CPU target

Compiler biết target feature set.

---

# 453.41 — GPU kernel model

GPU kernel là function chạy trên device.

---

## 453.42 — Kernel arguments

Kernel arguments phải có GPU-compatible representation.

---

## 453.43 — Kernel restrictions

GPU kernel không được tự động sử dụng:

```text
OS syscall
filesystem
arbitrary heap
GUI
CPU-only synchronization
```

---

## 453.44 — Device memory allocation

GPU allocation explicit.

---

## 453.45 — Host-device transfer

Copy:

```text
host → device
device → host
device → device
```

được model explicit.

---

## 453.46 — Transfer cost

Compiler/tooling không được che giấu transfer cost.

---

## 453.47 — Unified memory

Nếu platform hỗ trợ unified memory, nó vẫn phải có explicit memory semantics.

---

## 453.48 — Shared memory

GPU shared/workgroup memory được model riêng.

---

## 453.49 — Workgroup

Kernel launch có:

```text
grid
workgroup
local invocation
```

concepts.

---

## 453.50 — Thread IDs

Kernel có access đến execution IDs.

---

# 453.51 — GPU synchronization

Support conceptual:

```text
workgroup_barrier
memory_barrier
```

---

## 453.52 — Atomic GPU

GPU atomics có explicit atomic types/operations.

---

## 453.53 — GPU memory ordering

GPU memory order không mặc định giống CPU SeqCst model.

---

## 453.54 — Backend memory model

Compiler maps Axiom GPU synchronization semantics xuống backend-supported semantics.

---

## 453.55 — Data race

GPU data race phải được classified theo GPU execution model.

---

## 453.56 — Safe GPU subset

Có thể xây safe abstraction đảm bảo race-free access patterns.

---

## 453.57 — Unsafe GPU

Low-level kernel code có explicit unsafe escape hatch nếu abstraction không thể prove safety.

---

# 453.58 — Tensor foundation

Tensor không thuộc language core.

---

## 453.59 — Tensor type

Library-level:

```text
Tensor<T, const Rank: usize>
```

có thể tồn tại.

---

## 453.60 — Dynamic shape

Runtime dimensions có thể được represented separately.

---

## 453.61 — Static shape

Const generics có thể encode static dimensions.

---

## 453.62 — Tensor storage

Tensor storage abstraction:

```text
CPU
GPU
shared
mapped
```

---

## 453.63 — Layout

Tensor layout explicit:

```text
shape
stride
offset
dtype
device
```

---

## 453.64 — Contiguous tensor

Contiguous storage là optimization/representation property.

---

## 453.65 — Strided tensor

Strided views không cần copy.

---

## 453.66 — Tensor ownership

Tensor owns storage hoặc explicit borrowed view.

---

## 453.67 — Tensor view

View không own underlying storage.

---

## 453.68 — No implicit tensor copy

Shape/device conversion không tự copy nếu API không yêu cầu.

---

## 453.69 — Device mismatch

Operations trên tensors khác device phải có explicit transfer or error.

---

## 453.70 — Lazy execution

Tensor library có thể dùng lazy graph nhưng không phải language semantic.

---

# 453.71 — ML foundation

ML/AI APIs thuộc ecosystem.

Core chỉ cung cấp primitives cần thiết.

---

## 453.72 — Kernel specialization

Comptime có thể specialize:

```text
dtype
shape
tile size
vector width
```

---

## 453.73 — Kernel generation

Comptime/codegen có thể generate specialized kernels.

---

## 453.74 — Deterministic generation

Generated kernels phải deterministic.

---

## 453.75 — GPU compile pipeline

Conceptual:

```text
Axiom GPU source
→ GPU HIR
→ GPU IR
→ backend
→ shader/kernel artifact
```

---

## 453.76 — Separate GPU backend

GPU backend không được làm rối native CPU backend.

---

## 453.77 — CPU fallback

Algorithms có thể cung cấp CPU implementation.

---

## 453.78 — Kernel selection

Library chọn CPU/GPU implementation explicit hoặc policy-based.

---

## 453.79 — No hidden transfer

Library không được silently transfer large tensor between devices mà không có documented behavior.

---

## 453.80 — Async transfer

Host-device transfer có thể async.

---

# 453.81 — GPU memory safety

Device pointers không được dereference bằng CPU instruction.

---

## 453.82 — Resource state

Graphics APIs có resource states/layouts; abstraction phải preserve required transitions.

---

## 453.83 — Command validation

Debug backend có thể validate command/resource state.

---

## 453.84 — GPU debug metadata

Kernel source mapping được preserve trong debug build.

---

## 453.85 — Kernel crash diagnostics

GPU errors phải map về:

```text
kernel
source
dispatch
resource
```

khi backend cung cấp information.

---

## 453.86 — Shader reflection

Compile-time/generated metadata được ưu tiên hơn runtime reflection.

---

## 453.87 — GPU metadata

GPU artifact metadata có:

```text
kernel
bindings
resources
workgroup
target
features
```

---

## 453.88 — Binding validation

Host code có thể validate kernel resource bindings.

---

## 453.89 — Descriptor model

Graphics backend có thể expose descriptor/resource-binding abstraction.

---

## 453.90 — Pipeline cache

Compiled GPU pipelines có thể được cached.

---

# 453.91 — GPU compilation cache

Cache key gồm:

```text
source
compiler
GPU target
features
specialization
```

---

## 453.92 — Binary cache

GPU binaries có thể được cached nếu platform/backend cho phép.

---

## 453.93 — Cache invalidation

Driver/compiler version changes có thể invalidate GPU binary cache.

---

## 453.94 — Cross-GPU portability

GPU binary không được giả định portable giữa architectures.

---

## 453.95 — Portable GPU source

Source/kernel IR có thể được recompiled cho target GPU.

---

# 453.96 — CPU/GPU API separation

CPU API:

```text
fn compute()
```

GPU API:

```text
dispatch(kernel)
```

phải phân biệt semantic execution domain.

---

## 453.97 — Explicit synchronization

Cross-device synchronization phải explicit.

---

## 453.98 — Ownership transfer

Host/device ownership transfer phải representable.

---

## 453.99 — Lifetime

GPU resource lifetime phải cover tất cả queued uses.

---

## 453.100 — Drop safety

Dropping resource còn referenced by submitted work phải được prevented hoặc deferred theo explicit backend mechanism.

---

# 453.101 — SIMD optimizer integration

MIR/LIR phải có vector operations.

---

## 453.102 — Vector lowering

Vector IR có thể lower:

```text
portable SIMD
→ target SIMD
→ scalar fallback
```

---

## 453.103 — Scalar fallback

Nếu target không support vector width, compiler có thể legalize thành smaller vectors/scalar operations.

---

## 453.104 — Vector ABI

SIMD argument/return phải dùng ABI engine 421.

---

## 453.105 — Vector calling convention

Target ABI quyết định vector register passing.

---

## 453.106 — Vector alignment

Layout engine 422 quyết định alignment.

---

## 453.107 — Vector memory semantics

SIMD load/store phải obey same memory validity rules.

---

## 453.108 — Vector aliasing

Optimizer chỉ áp dụng noalias assumptions khi semantic contract cho phép.

---

## 453.109 — Vector bounds

Vectorized memory access vẫn phải preserve bounds semantics hoặc dùng explicit unsafe primitive.

---

## 453.110 — Vector diagnostics

Compiler có thể báo reason auto-vectorization failed.

---

# 453.111 — GPU/CPU concurrency

CPU thread có thể submit GPU work.

---

## 453.112 — GPU queue ownership

Queue handle ownership phải deterministic.

---

## 453.113 — Multi-queue

Backend có thể expose:

```text
graphics
compute
transfer
```

queues.

---

## 453.114 — Queue synchronization

Cross-queue dependencies phải explicit.

---

## 453.115 — Multi-GPU

Multiple devices được hỗ trợ ở ecosystem layer.

---

## 453.116 — Device selection

Selection criteria có thể gồm:

```text
type
memory
features
power
vendor
```

nhưng library quyết định policy.

---

## 453.117 — No compiler device selection

Compiler không tự chọn GPU runtime device.

---

# 453.118 — GPU profiling

Optional profiling:

```text
kernel duration
transfer duration
queue wait
memory usage
```

---

## 453.119 — CPU/GPU timeline

Profiler có thể correlate:

```text
CPU call
→ submit
→ GPU execution
→ completion
```

---

## 453.120 — AI performance query

AI metadata có thể trả lời:

```text
which kernel is slow?
where is host-device transfer?
which tensor causes allocation?
```

---

# 453.121 — Tensor performance

Tensor benchmark đo:

```text
FLOPS
memory bandwidth
kernel launch
transfer
allocation
```

---

## 453.122 — Benchmark correctness

GPU benchmark phải validate numerical correctness.

---

## 453.123 — Floating-point tolerance

GPU/CPU numerical comparison dùng explicit tolerance.

---

## 453.124 — Deterministic mode

Library có thể cung cấp deterministic execution mode.

---

## 453.125 — Fast mode

Fast math/relaxed numerical semantics phải explicit.

---

# 453.126 — GPU security

GPU kernels không được tự động có host privileges.

---

## 453.127 — GPU sandbox

Backend/platform security model vẫn áp dụng.

---

## 453.128 — Resource limits

Application có thể limit:

```text
GPU memory
dispatch size
execution time
```

khi platform hỗ trợ.

---

## 453.129 — Untrusted kernels

Untrusted GPU code phải chịu platform/driver isolation assumptions; Axiom language safety không tự đảm bảo GPU driver safety.

---

## 453.130 — Native driver boundary

GPU driver là external trust boundary giống FFI 451.

---

# 453.131 — GUI integration

GUI renderer có thể dùng GPU abstraction 453.

---

## 453.132 — Rendering vs compute

Graphics rendering và general compute dùng chung low-level device abstraction khi backend phù hợp, nhưng semantics riêng.

---

## 453.133 — Render graph

GUI/game/rendering libraries có thể build render graph phía trên GPU API.

---

## 453.134 — Compute graph

ML/tensor libraries có thể build compute graph.

---

## 453.135 — No mandatory render graph

Render graph không thuộc core.

---

# 453.136 — GPU artifact formats

Backend có thể generate platform-specific shader/kernel artifacts.

---

## 453.137 — GPU target identity

Artifact ghi:

```text
vendor
architecture
driver/API
feature level
```

khi relevant.

---

## 453.138 — Shader source provenance

GPU artifact phải retain source provenance trong debug/development build.

---

## 453.139 — GPU reproducibility

Build phải record compiler/backend versions.

---

## 453.140 — GPU cache reproducibility

Cache key phải deterministic.

---

# 453.141 — AI-friendly GPU metadata

AI có thể query:

```text
kernel inputs
outputs
memory spaces
synchronization
device
required features
```

---

## 453.142 — AI kernel diagnostics

Compiler diagnostics phải machine-readable.

---

## 453.143 — Kernel optimization remarks

Compiler có thể report:

```text
vectorized
unrolled
tiled
register pressure
occupancy limitation
```

khi backend có information.

---

## 453.144 — CPU optimization metadata

Tương tự SIMD:

```text
vector width
unrolling
register pressure
```

---

## 453.145 — No universal occupancy promise

GPU occupancy phụ thuộc backend/device/compiler.

---

# 453.146 — Future accelerator model

Architecture phải có thể mở rộng:

```text
NPU
TPU
DSP
FPGA
```

nhưng không đưa chúng vào core.

---

## 453.147 — Accelerator abstraction

Future accelerator backend có thể implement common execution/resource traits.

---

## 453.148 — Explicit execution domain

Mọi accelerator execution phải có explicit domain identity.

---

## 453.149 — No magic heterogeneous execution

Axiom không tự động chuyển arbitrary function giữa CPU/GPU/NPU.

---

## 453.150 — Hard invariants

1. CPU là default execution domain.
2. SIMD là explicit/optimizer-supported CPU execution domain.
3. GPU là explicit execution domain.
4. Không có implicit GPU offload.
5. CPU pointer và GPU pointer không được coi là cùng address space.
6. GPU resources có explicit ownership.
7. GPU device/queue model phải tồn tại.
8. GPU synchronization phải explicit.
9. GPU wait phải explicit nếu blocking.
10. Device loss phải có error model.
11. GPU resource lifetime phải cover queued work.
12. Drop không được tạo use-after-free trên GPU.
13. Host-device transfer phải explicit.
14. Transfer cost phải visible.
15. Unified memory không được làm mất memory semantics.
16. GPU shared/local/constant memory phải được model khi backend hỗ trợ.
17. Kernel là execution-domain-specific function.
18. Kernel không được tự sử dụng arbitrary host facilities.
19. Workgroup/grid semantics phải được model.
20. GPU barrier/atomic semantics phải explicit.
21. GPU memory ordering không được giả định giống CPU nếu không đúng backend.
22. GPU data race phải có defined classification.
23. Safe GPU abstractions có thể được xây.
24. Unsafe GPU operations có explicit boundary.
25. SIMD vector types phải tồn tại ở library/compiler level.
26. SIMD lane count có thể là type-level.
27. SIMD masks phải được model.
28. SIMD load/store semantics phải rõ.
29. Auto-vectorization phải preserve language semantics.
30. Fast-math không được mặc định.
31. Explicit SIMD phải được hỗ trợ.
32. CPU feature detection phải khả dụng.
33. Multi-version CPU dispatch có thể được hỗ trợ.
34. Vector ABI phải tích hợp ABI engine.
35. Vector layout phải tích hợp layout engine.
36. Vector aliasing phải obey semantic alias rules.
37. Bounds safety phải được preserve khi vectorizing.
38. Tensor không thuộc language core.
39. Tensor có thể dùng generics/const generics.
40. Tensor shape/stride/device phải biểu diễn được.
41. Tensor view không own storage.
42. Tensor không implicit copy.
43. Device mismatch phải explicit.
44. Tensor lazy execution là library choice.
45. ML framework không thuộc compiler core.
46. Comptime có thể specialize kernels.
47. Generated kernels phải deterministic.
48. CPU fallback có thể tồn tại.
49. Host-device async transfer có thể được hỗ trợ.
50. GPU backend tách khỏi CPU backend.
51. GPU binary cache phải target-specific.
52. Driver/compiler version có thể invalidate GPU cache.
53. GPU binary không được coi là universally portable.
54. GPU source/IR có thể recompile theo target.
55. GPU debug metadata phải có source provenance.
56. Kernel diagnostics phải machine-readable.
57. Host/device synchronization phải explicit.
58. Multi-queue synchronization phải explicit.
59. Multi-GPU selection là runtime/library policy.
60. Compiler không tự chọn GPU device.
61. GPU profiling có thể được hỗ trợ.
62. CPU/GPU timeline có thể được correlate.
63. GPU benchmarks phải validate correctness.
64. Floating-point tolerance phải explicit.
65. Deterministic numerical mode có thể được cung cấp.
66. Relaxed/fast numerical mode phải explicit.
67. GPU code không tự có host privileges.
68. GPU driver là external trust boundary.
69. GPU resource limits có thể được cấu hình.
70. GUI renderer có thể sử dụng GPU layer.
71. Graphics và compute có thể share low-level device abstraction.
72. Graphics semantics và compute semantics vẫn tách biệt.
73. Render graph không thuộc core.
74. Compute graph không thuộc core.
75. Future accelerators có thể plug vào execution architecture.
76. Accelerator execution domain phải explicit.
77. Không có magic heterogeneous execution.
78. GPU/SIMD metadata tích hợp semantic metadata 446.
79. Performance diagnostics tích hợp benchmark system 450.
80. GPU backend phải có thể được bỏ hoàn toàn khỏi freestanding/CPU-only builds.
81. **Axiom phải cung cấp nền tảng đủ mạnh để xây SIMD, graphics, GPU compute và tensor/AI libraries hiệu năng cao, nhưng không biến GPU/AI runtime thành thành phần bắt buộc của ngôn ngữ hoặc executable thông thường.**

**BOOTSTRAP-453 hoàn tất.**

---

# BOOTSTRAP-454 — NETWORKING, HTTP, TLS, SOCKETS, IPC, SERIALIZATION & DISTRIBUTED-SYSTEM FOUNDATION

Task tiếp theo sẽ khóa tầng **network/system communication**:

```text
socket
TCP
UDP
QUIC
DNS
HTTP
TLS
WebSocket
IPC
shared memory
serialization
RPC
```

và đặc biệt phải phân biệt:

```text
core networking primitives
standard library APIs
optional protocol libraries
third-party ecosystem
```

để một Axiom executable nhỏ có thể dùng socket trực tiếp mà không phải kéo theo một networking runtime khổng lồ.

