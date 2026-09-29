# BOOTSTRAP-198 — GUI, Application Framework, Event Loop & Native UI Architecture

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> **GUI là một capability/library layer của Axiom, không phải thành phần của Core và không phải một runtime bắt buộc.**

Axiom phải cho phép cả:

```text
tiny CLI
kernel
embedded
game
desktop application
mobile application
GPU application
WASM application
```

cùng dùng một ngôn ngữ mà không kéo GUI stack không cần thiết.

---

# 198.1. GUI không thuộc Language Core

Core chỉ cần các primitive cần thiết:

```text
struct
enum
trait
function
closure
async
ownership
capability
GPU
```

GUI nằm ở library/framework:

```text
std::ui
std::window
std::graphics
std::text
std::accessibility
```

---

# 198.2. GUI stack

Kiến trúc:

```text
Application
     │
     ▼
UI Framework
     │
     ├── Widget / Component
     ├── Layout
     ├── State
     ├── Event
     ├── Animation
     └── Accessibility
     │
     ▼
UI Runtime
     │
     ├── Event Loop
     ├── Window Manager
     ├── Input
     └── Rendering
     │
     ├──────────────┐
     ▼              ▼
GPU Renderer     Native Controls
     │              │
     ▼              ▼
Platform Backend
```

---

# 198.3. Không có một GUI framework duy nhất bắt buộc

Axiom cung cấp **GUI foundation**, không ép một programming model duy nhất.

Có thể xây:

```text
std::ui::native
std::ui::canvas
std::ui::immediate
std::ui::declarative
```

trên cùng infrastructure.

---

# 198.4. Chọn retained-mode làm nền tảng

Kiến trúc nền tảng:

> **Retained scene/UI tree là semantic model chính.**

Ví dụ:

```text
Window
 └── Root
      ├── Panel
      │    ├── Button
      │    └── Text
      └── Image
```

Lợi ích:

- accessibility
- event routing
- layout
- focus
- animation
- incremental rendering
- tooling/inspection
- AI hiểu UI structure

---

# 198.5. Immediate mode vẫn được hỗ trợ

Immediate mode có thể xây trên renderer:

```axiom
ui.button("Save")
ui.text("Hello")
```

nhưng nó không phải semantic foundation bắt buộc.

Có thể có:

```text
std::ui::immediate
```

cho tooling/editor/debug UI.

---

# 198.6. Declarative UI

Axiom nên hỗ trợ declarative style bằng chính language:

```axiom
Window {
    title: "Editor"

    Column {
        Text("Hello")
        Button("Build") {
            on_click: build_project
        }
    }
}
```

Đây **không cần một DSL/macro language riêng**.

Compiler có thể xử lý syntax sugar thành các struct/function/trait thông thường.

---

# 198.7. Không tạo một UI language thứ hai

Không thiết kế:

```text
AXUI
QML-like language
XML UI
special macro language
```

ở Core.

Thay vào đó:

```text
Axiom language
+
UI library
+
compiler-known optimization
```

---

# 198.8. Component model

UI element là struct:

```axiom
struct Button {
    text: String
    enabled: bool
}
```

Behavior là function/trait:

```axiom
fn render(self: view<Button>, ctx: mut_view<RenderContext>)
```

Đúng với triết lý:

> **struct + function, không cần class.**

---

# 198.9. Không có class inheritance cho widget

Không:

```text
Button extends Control
```

Thay vào đó:

```text
Widget
Renderable
Focusable
Clickable
Accessible
```

là các capability/trait.

Một type có thể implement nhiều behavior mà không có inheritance tree.

---

# 198.10. Widget identity

Không dùng địa chỉ memory làm identity.

Widget có:

```text
WidgetId
```

hoặc:

```text
NodeId
Generation
```

theo logical identity model đã khóa ở Memory Architecture.

---

# 198.11. Widget tree ownership

UI tree có ownership rõ ràng:

```text
Window
 └── Root owns children
```

Child không sở hữu parent.

Các API có thể sử dụng:

```text
view<Node>
mut_view<Node>
NodeId
```

thay vì raw pointers.

---

# 198.12. Stable identity không đồng nghĩa stable address

Một widget có:

```text
NodeId = 42
```

không có nghĩa:

```text
address == constant
```

UI framework có thể relocate internal storage.

Đây là điểm rất quan trọng để tránh GUI framework phụ thuộc pointer stability.

---

# 198.13. Event model

Event là value:

```axiom
enum Event {
    Pointer(PointerEvent),
    Key(KeyEvent),
    Text(TextInputEvent),
    Window(WindowEvent),
    Touch(TouchEvent),
    Gesture(GestureEvent),
}
```

Không cần inheritance/event object hierarchy.

---

# 198.14. Event routing

Event flow:

```text
Platform
   ↓
Window
   ↓
Hit Test
   ↓
Capture
   ↓
Target
   ↓
Bubble
   ↓
Application
```

GUI framework có thể hỗ trợ:

```text
capture
target
bubble
```

và event propagation control.

---

# 198.15. Event handlers

Không cần heap-allocated virtual objects bắt buộc.

Handler có thể là:

```axiom
fn on_click(event: view<ClickEvent>) {
    ...
}
```

Closure cũng được phép.

Compiler có thể inline/eliminate closure environment khi có thể.

---

# 198.16. Event loop

Event loop **không thuộc Core runtime**.

Nó là UI runtime component:

```text
UIEventLoop
```

Có thể tích hợp với:

```text
async executor
```

nhưng không đồng nhất hai thứ.

---

# 198.17. GUI thread affinity

Một số platform yêu cầu UI operations trên UI thread.

Axiom biểu diễn điều này như execution-domain contract:

```text
UIThread
```

Compiler/tooling có thể kiểm tra API yêu cầu UI execution domain.

---

# 198.18. Không biến UI thread thành special language thread

Không tạo:

```text
@ui_thread
```

thành một loại thread primitive của Core.

Thay vào đó là library/execution-domain contract.

---

# 198.19. Send/Share với UI

Ví dụ:

```text
Widget
```

có thể:

```text
Send = false
Share = false
```

nếu platform yêu cầu thread affinity.

Một model/data object bình thường vẫn có thể:

```text
Send = true
Share = true
```

Điều này cho phép:

```text
Worker thread
    ↓
compute
    ↓
Send result
    ↓
UI thread
```

---

# 198.20. Async + GUI

Không được thiết kế:

```text
GUI = async runtime
```

Thay vào đó:

```text
UI Event Loop
      ↕
Async Executor
```

Có thể cùng chạy trên một thread hoặc nhiều thread tùy runtime.

---

# 198.21. `await` trên UI thread

Nếu:

```axiom
async fn load() -> Data
```

được gọi từ UI:

```text
UI
 ↓
await
 ↓
suspend
 ↓
UI event loop continues
```

không được block UI thread.

Compiler không tự đảm bảo mọi API là nonblocking, nhưng API metadata phải thể hiện:

```text
blocking
async
may_suspend
```

---

# 198.22. Blocking API trên UI

Tooling có thể cảnh báo:

```text
UI thread
   ↓
File.read()
   ↓
blocking
```

Nếu contract yêu cầu nghiêm ngặt, profile/framework có thể biến thành compile error.

---

# 198.23. Rendering model

UI framework tách:

```text
UI Tree
   ↓
Render Tree
   ↓
Render Commands
   ↓
GPU
```

UI semantics không bị khóa vào GPU implementation.

---

# 198.24. Render tree

UI tree:

```text
Button
 ├── Background
 ├── Border
 └── Text
```

có thể được flatten thành render tree:

```text
DrawRoundedRect
DrawText
```

Compiler/runtime có thể cache và diff render tree.

---

# 198.25. GPU integration

GPU rendering sử dụng architecture GPU đã khóa:

```text
Device
DeviceBuffer
DeviceView
GpuEvent
Kernel
```

Không tạo một GPU memory model riêng cho GUI.

---

# 198.26. CPU fallback

GUI phải có backend không-GPU khi target yêu cầu.

```text
UI
 ↓
Renderer interface
 ├── GPU
 ├── software
 └── native platform
```

---

# 198.27. Renderer trait

Conceptually:

```axiom
trait Renderer {
    fn begin_frame(...)
    fn draw(...)
    fn end_frame(...)
}
```

Static dispatch mặc định.

Dynamic renderer:

```text
dyn Renderer
```

chỉ khi runtime plugin/backend thực sự cần.

---

# 198.28. Không bắt buộc vtable

Một application chỉ dùng:

```text
DirectRenderer
```

có thể được monomorphized/inlined hoàn toàn.

Không tự động tạo:

```text
Renderer vtable
```

---

# 198.29. Layout engine

Layout là library subsystem:

```text
Constraints
Measure
Arrange
Render
```

Một layout pass:

```text
parent constraints
       ↓
child measure
       ↓
child desired size
       ↓
parent arrange
```

---

# 198.30. Layout không dùng GC

UI tree không yêu cầu tracing GC.

Ownership + IDs + arena/storage strategies đủ để quản lý lifetime.

Framework có thể dùng arena/pool để giảm allocation.

---

# 198.31. Layout invalidation

Node thay đổi:

```text
Button.width
```

không nhất thiết layout lại toàn bộ tree.

Framework theo dõi:

```text
LayoutDirty
PaintDirty
TransformDirty
TextDirty
```

và recompute tối thiểu.

---

# 198.32. Reactive state

Reactive programming là library feature.

Ví dụ concept:

```text
Signal<T>
Computed<T>
Effect
```

nhưng chúng tuân theo ownership/capability bình thường.

Không tạo reactive magic vào language semantics.

---

# 198.33. State ownership

Ví dụ:

```axiom
struct CounterState {
    value: i32
}
```

UI có thể giữ:

```text
owned state
```

hoặc:

```text
view state
```

Không cần framework-specific lifetime annotations.

---

# 198.34. Data binding

Data binding có thể là generic library:

```text
Binding<T>
Observable<T>
Signal<T>
```

Compiler có thể specialize.

Không bắt buộc runtime reflection.

---

# 198.35. Animation

Animation là value/time function:

```text
Animation<T>
Timeline
Easing
Transition
```

Compiler/runtime chỉ cần scheduler/timer khi animation thực sự chạy.

---

# 198.36. Timer

Timer dependency:

```text
Animation
   ↓
Timer
```

không tự động kéo networking/async executor nếu implementation không cần.

---

# 198.37. Text rendering

Text pipeline:

```text
String / Str
    ↓
Unicode
    ↓
Script segmentation
    ↓
Text shaping
    ↓
Glyphs
    ↓
Font rasterization
    ↓
GPU
```

Các bước nặng nằm ở library.

---

# 198.38. Unicode không đồng nghĩa GUI

Một CLI chỉ dùng:

```text
String
```

không cần:

```text
font shaping
glyph rasterizer
```

GUI text renderer mới kéo chúng vào.

---

# 198.39. Font subsystem

Font loading:

```text
Font
FontFace
FontManager
GlyphRun
```

có thể là library/runtime components.

Không phải Core.

---

# 198.40. Accessibility

Accessibility phải nằm trong semantic UI tree.

Ví dụ:

```text
Button
role = button
name = "Save"
state = enabled
```

Không phụ thuộc vào pixel rendering.

Điều này cho phép platform accessibility backend:

```text
Windows
macOS
Linux
iOS
Android
```

---

# 198.41. Accessibility và custom rendering

Một custom GPU button vẫn phải có accessibility node nếu developer khai báo/được framework suy ra.

Do đó:

```text
Visual Tree
```

và:

```text
Accessibility Tree
```

có thể là hai representation khác nhau của cùng semantic UI.

---

# 198.42. DPI

Logical units:

```text
dp
logical_px
```

và physical pixels:

```text
px
```

là các semantic units khác nhau.

Không dùng `f32` tùy tiện để tránh nhầm.

Có thể có:

```text
Px
Dp
Point
```

như newtypes.

---

# 198.43. Coordinate spaces

GUI phải phân biệt:

```text
Screen
Window
Local
Content
Transform
```

Compiler/library type system có thể dùng newtypes để tránh nhầm coordinate spaces.

---

# 198.44. Input

Unified semantic input:

```text
Pointer
Mouse
Keyboard
Touch
Pen
Gamepad
IME
Accessibility
```

Platform backend chuyển thành Axiom events.

---

# 198.45. IME

Text input không được coi đơn giản là:

```text
KeyEvent
```

IME có:

```text
composition
preedit
candidate
commit
```

để hỗ trợ tiếng Việt, Trung, Nhật, Hàn và các hệ chữ khác.

Đây đặc biệt quan trọng đối với mục tiêu multilingual của Axiom.

---

# 198.46. Native controls vs custom controls

Axiom hỗ trợ cả hai.

### Native control

```text
Button
 ↓
Win32/AppKit/UIKit/etc.
```

Ưu điểm:

- accessibility native
- platform behavior
- native integration

### Custom control

```text
Button
 ↓
Axiom UI renderer
 ↓
GPU
```

Ưu điểm:

- visual consistency
- custom rendering
- game/editor style UI

Không chọn một bên làm duy nhất.

---

# 198.47. Native window

`Window` là abstraction:

```text
Window
```

với backend:

```text
Win32
Cocoa
UIKit
Wayland/X11
Android
WASM
```

Window handle là resource identity, không phải raw pointer.

---

# 198.48. Window lifetime

```text
Window
```

là owning resource.

Drop:

```text
Window
```

có thể release native handle nhưng không mặc định:

```text
terminate process
```

đúng theo resource semantics đã khóa.

---

# 198.49. Multiple windows

Framework phải hỗ trợ:

```text
Application
 ├── Window A
 ├── Window B
 └── Window C
```

Không giả định single-window architecture.

---

# 198.50. Headless mode

GUI library phải hỗ trợ:

```text
headless
```

cho:

- testing
- server rendering
- screenshot generation
- CI
- AI UI testing

Không cần platform window.

---

# 198.51. UI testing

Semantic UI tree cho phép test:

```axiom
assert(ui.find("SaveButton").enabled)
```

thay vì phụ thuộc pixel.

Pixel testing vẫn có thể tồn tại riêng.

---

# 198.52. AI-native UI

Vì UI tree có semantic metadata, AI/tooling có thể query:

```text
Window
 ├── Toolbar
 │    ├── Open
 │    └── Save
 └── Editor
```

AI không cần suy luận từ screenshot nếu semantic tree đã có.

CompilerDB/tooling có thể cung cấp:

```text
UI element
type
properties
events
bindings
layout
accessibility
source span
```

---

# 198.53. Hot reload

Hot reload không được mặc định.

Nếu muốn:

```text
UI code
 ↓
dynamic module
 ↓
stable UI ABI
```

thì phải tuân theo ABI architecture 193.

State migration explicit.

---

# 198.54. UI plugin

Plugin UI có:

```text
stable interface
version
ABI fingerprint
capability contract
```

Không cho plugin tự ý truy cập toàn bộ application state.

---

# 198.55. WASM/Web

Axiom UI abstraction có thể map:

```text
Window
 ↓
Browser surface
 ↓
Canvas/WebGPU
```

hoặc native DOM integration thông qua FFI/platform library.

Không biến DOM thành semantic primitive của Core.

---

# 198.56. Mobile

iOS/Android có lifecycle:

```text
created
active
background
suspended
terminated
```

UI framework phải biểu diễn lifecycle bằng events/state machine.

Không giả định desktop process model.

---

# 198.57. Application lifecycle

Conceptually:

```text
Application
 ↓
Init
 ↓
Running
 ↓
Suspending
 ↓
Suspended
 ↓
Resuming
 ↓
Running
 ↓
Closing
```

Nhưng lifecycle implementation phụ thuộc platform.

---

# 198.58. GUI runtime graph

Một desktop application có thể cần:

```text
Startup
 ├── Window
 ├── UI Event Loop
 ├── GPU
 ├── Font
 ├── Text Shaping
 └── Accessibility
```

Không dùng GUI:

```text
GUI components = absent
```

---

# 198.59. GUI và runtime composition

GUI không được biến thành:

```text
AxiomRuntime
```

Nó chỉ thêm:

```text
UIEventLoop
WindowSystem
Renderer
```

vào RuntimeGraph.

---

# 198.60. Binary size

Một command-line:

```text
fn main() {
    println("hello");
}
```

không được kéo:

```text
Window
GPU
Font
Accessibility
```

Một GUI app mới kéo chúng.

---

# 198.61. Compile-time UI optimization

Declarative UI:

```axiom
Button("Save")
```

có thể được compiler specialize thành:

```text
static UI structure
```

nếu bất biến.

Dynamic state vẫn runtime.

---

# 198.62. UI allocation optimization

Framework có thể dùng:

```text
arena
pool
slab
inline storage
```

cho UI nodes.

Compiler có thể eliminate allocation nếu lifetime/locality cho phép.

---

# 198.63. No GC requirement

UI không được yêu cầu garbage collector.

Cycle trong semantic graph phải được giải quyết bằng:

```text
ownership
IDs
weak handles
explicit graph storage
```

chứ không mặc định GC.

---

# 198.64. Weak references

UI parent-child graph thường có nhu cầu non-owning identity.

Dùng:

```text
WeakHandle<T>
NodeId
```

thay vì tạo raw reference cycles.

---

# 198.65. GUI effects

CompilerDB có thể phân biệt:

```text
UI
GPU
Input
Window
IO
Network
```

như effects/capabilities.

Một pure layout function:

```text
LayoutResult layout(...)
```

có thể được tối ưu mạnh.

---

# 198.66. Pure UI computation

Ví dụ:

```axiom
fn calculate_layout(
    constraints: Constraints,
    children: view<Child>
) -> LayoutResult
```

nếu không có external effects:

```text
pure
```

Compiler có thể:

- inline
- SIMD
- parallelize khi an toàn
- cache
- memoize trong framework

---

# 198.67. Rendering side effects

Renderer:

```text
draw(...)
```

có GPU/external effect.

Compiler không được tự ý loại bỏ/reorder nếu semantics observable.

---

# 198.68. Parallel UI

Layout/render preparation có thể chạy worker threads:

```text
Worker
 ↓
compute layout
 ↓
Send result
 ↓
UI thread
 ↓
commit
```

UI tree mutation vẫn theo thread-affinity contract.

---

# 198.69. UI transactions

Để tránh trạng thái UI nửa cập nhật:

```text
begin_update
mutate
commit
```

có thể được library abstraction.

Không cần transaction primitive trong Core.

---

# 198.70. Scene graph vs widget tree

Không ép game/3D UI sử dụng widget tree cho mọi thứ.

Có:

```text
UI Tree
Scene Graph
Render Graph
```

là các semantic structures khác nhau.

Có thể tích hợp nhưng không đồng nhất.

---

# 198.71. Render Graph

GPU-heavy application có:

```text
RenderGraph
 ├── ShadowPass
 ├── GeometryPass
 ├── LightingPass
 └── PostProcess
```

Đây là library/compiler-optimized layer trên GPU model.

---

# 198.72. UI + 3D

Axiom có thể composition:

```text
Window
 ├── UI
 └── 3D Surface
```

không cần hai runtime độc lập.

---

# 198.73. GUI FFI

Platform-specific native APIs đi qua:

```text
FFI Contract
```

đã định nghĩa ở 192.

Safe GUI layer bao bọc:

```text
unsafe OS calls
```

và trả về safe types.

---

# 198.74. GUI framework implementation

Final implementation có thể được viết hoàn toàn bằng Axiom:

```text
UI framework
Layout
Renderer
Event system
Accessibility
Text
```

chỉ giữ platform FFI boundary ở tầng thấp.

---

# 198.75. GUI compiler integration

Compiler không cần hiểu toàn bộ UI framework.

Compiler chỉ cần hiểu các semantic primitives:

```text
ownership
Send/Share
async
GPU
effects
comptime
generic
```

Framework tự xây semantics cấp cao bằng các primitive đó.

---

# 198.76. GUI-specific compiler optimizations

Có thể bổ sung compiler plugins/knowledge sau:

```text
UI tree constant folding
render command batching
layout specialization
dead widget elimination
GPU command fusion
event-handler devirtualization
```

nhưng **không được đưa thành requirement của Core v1**.

---

# 198.77. Invariants — `AGUI`

### `AGUI-20`
GUI shall not be part of the mandatory Axiom language runtime.

### `AGUI-21`
GUI shall not be required by Core or freestanding programs.

### `AGUI-22`
GUI APIs shall be implemented as library/framework abstractions.

### `AGUI-23`
Axiom shall provide a semantic UI tree model.

### `AGUI-24`
UI elements shall not require class inheritance.

### `AGUI-25`
Widget identity shall be independent of physical memory address.

### `AGUI-26`
UI ownership shall follow Axiom ownership semantics.

### `AGUI-27`
Non-owning UI access shall use Axiom capability/identity mechanisms.

### `AGUI-28`
GUI event delivery shall be represented by typed values.

### `AGUI-29`
Event routing shall support target/capture/bubble semantics.

### `AGUI-30`
GUI event loops shall remain separate from the language Core async model.

### `AGUI-31`
GUI thread affinity shall be represented as an execution-domain contract.

### `AGUI-32`
UI-bound values shall obey normal Send/Share verification.

### `AGUI-33`
GUI APIs shall not implicitly block an execution domain without an appropriate contract.

### `AGUI-34`
GUI rendering shall be separable from UI semantics.

### `AGUI-35`
GPU rendering shall use the established Axiom GPU model.

### `AGUI-36`
Axiom shall support GPU and software rendering backends.

### `AGUI-37`
Native platform controls and custom-rendered controls shall both be supported.

### `AGUI-38`
Accessibility semantics shall be independent of visual rendering.

### `AGUI-39`
Text input shall support IME/composition semantics.

### `AGUI-40`
Unicode/text shaping shall remain separate from Language Core.

### `AGUI-41`
Logical and physical coordinate spaces shall be distinguishable.

### `AGUI-42`
UI layout shall not require tracing garbage collection.

### `AGUI-43`
Reactive state shall remain a library abstraction.

### `AGUI-44`
Declarative UI shall use ordinary Axiom semantics rather than introducing a mandatory second language.

### `AGUI-45`
GUI applications shall support multiple windows.

### `AGUI-46`
Headless UI execution/testing shall be supported.

### `AGUI-47`
GUI runtime dependencies shall participate in RuntimeGraph.

### `AGUI-48`
Unused GUI subsystems shall not be linked into non-GUI programs.

### `AGUI-49`
GUI plugins/hot reload shall require explicit ABI and state contracts.

### `AGUI-50`
Platform-specific GUI APIs shall be isolated behind platform/FFI boundaries.

### `AGUI-51`
UI framework abstractions shall preserve Axiom ownership and capability verification.

### `AGUI-52`
GUI optimization shall never weaken language semantics.

### `AGUI-53`
Pure UI computations shall remain eligible for ordinary compiler optimization.

### `AGUI-54`
GUI architecture shall support desktop, mobile, embedded and WASM targets where platform capabilities permit.

### `AGUI-55`
AI and IDE tooling shall be able to inspect semantic UI structure without relying exclusively on rendered pixels.

### `AGUI-56`
Accessibility, UI identity, event routing and source mapping shall be represented in compiler/tooling metadata where available.

---

# Kiến trúc GUI cuối cùng

```text
                    Axiom Application
                           │
              ┌────────────┴────────────┐
              │                         │
          Application                UI State
              │                         │
              └────────────┬────────────┘
                           ▼
                       UI Tree
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Layout      Accessibility   Event System
             │                           │
             └─────────────┬─────────────┘
                           ▼
                       Render Tree
                           │
                     Render Graph
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
             GPU Backend        Software/Native
                 │                   │
                 └─────────┬─────────┘
                           ▼
                      Platform
```

Điểm quan trọng là **GUI không làm Axiom trở thành một ngôn ngữ UI**. Nó chỉ là một tầng framework rất mạnh nằm trên các primitive vốn đã có.

---

# BOOTSTRAP-199 — Graphics, Rendering, Game Engine & GPU Compute Architecture

**TRẠNG THÁI: NEXT**

Vì GUI đã xác định renderer và GPU boundary, bước tiếp theo nên đi sâu hơn vào **graphics stack tổng thể** của Axiom.

Mục tiêu không chỉ là GUI mà còn:

```text
2D
3D
Game
CAD
Visualization
Scientific computing
GPU compute
AI/tensor
Video processing
```

Kiến trúc dự kiến:

```text
Axiom GPU Model
       │
       ├── Compute
       ├── Graphics
       ├── Ray Tracing
       └── Copy/Transfer
              │
              ▼
        Graphics API
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
    Vulkan  Metal  DirectX
       │      │      │
       └──────┼──────┘
              ▼
        Axiom RenderGraph
              │
       ┌──────┼───────────┐
       ▼      ▼           ▼
      2D      3D       Compute
       │      │           │
       └──────┼───────────┘
              ▼
        GPU Command Model
```

Phần này cần đặc biệt khóa:

- GPU resource ownership.
- Buffer/Image/Texture/Sampler.
- descriptor/bindless model.
- command buffer.
- queue/fence/semaphore.
- render graph.
- synchronization và barrier inference.
- shader language có phải Axiom hay không.
- compute kernel và graphics shader có cùng type system không.
- CPU/GPU shared types.
- GPU memory allocator.
- zero-copy.
- VRAM/system RAM.
- multi-GPU.
- CPU fallback.
- Vulkan/Metal/D3D12/WebGPU.
- ray tracing.
- mesh/shader pipelines.
- tensor/AI compute.
- shader compilation và caching.
- pipeline state caching.
- GPU debugging.
- GPU code generation từ Axiom.
- làm sao để **một ngôn ngữ duy nhất có thể viết CPU code + GPU kernel + shader mà không biến Core thành một ngôn ngữ khổng lồ**.