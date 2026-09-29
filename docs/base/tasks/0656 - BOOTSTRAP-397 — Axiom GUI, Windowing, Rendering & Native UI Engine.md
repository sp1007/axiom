# BOOTSTRAP-397 — Axiom GUI, Windowing, Rendering & Native UI Engine

Sau **396 — OS/System Interface**, bước tiếp theo hợp lý là xây tầng **GUI + Graphics + Rendering**.

Đây là một domain quan trọng vì mục tiêu Axiom không chỉ là systems language mà còn phải có khả năng xây **ứng dụng desktop native, công cụ kỹ thuật, IDE, editor, visualization, game/tooling** mà không bị phụ thuộc vào một object runtime nặng.

Nguyên tắc:

> **UI là data + state + event + rendering, không phải class hierarchy + widget object hierarchy bắt buộc.**

---

# 1. GUI không thuộc Core

Core chỉ biết:

```text
Value
Ownership
Capability
Concurrency
I/O
Execution
```

GUI nằm trên:

```text
OS
Windowing
Input
Graphics
Rendering
Text
Accessibility
```

---

# 2. Kiến trúc tổng thể

```text
Axiom Application
        │
        ├── UI State
        ├── Event
        ├── Layout
        ├── Widget
        └── Rendering
                │
        ┌───────┼────────┐
        │       │        │
      CPU     GPU      OS Window
        │       │        │
        └───────┼────────┘
                │
          Native Platform
```

---

# 3. Window

Window là OS resource:

```text
Window
WindowHandle
```

có ownership và capability.

Không phải một class kế thừa `Widget`.

---

# 4. Window Lifecycle

Semantic state:

```text
Created
Shown
Hidden
Minimized
Maximized
Focused
Closing
Closed
```

OS backend có thể có nhiều trạng thái vật lý hơn.

---

# 5. Window Ownership

Window handle:

```text
Move
Drop
close()
```

Không mặc định `Copy`.

Duplicate/native handle duplication phải explicit.

---

# 6. Window Configuration

```text
WindowConfig {
    title
    size
    position
    resizable
    fullscreen
    decorations
    vsync
    transparency
}
```

Physical representation implementation-defined.

---

# 7. Window Events

Events:

```text
WindowCreated
WindowResized
WindowMoved
WindowFocused
WindowUnfocused
WindowCloseRequested
WindowClosed
WindowMinimized
WindowMaximized
```

---

# 8. Event Loop

Event loop là execution abstraction:

```text
poll_events()
wait_events()
dispatch_events()
```

Không phải bắt buộc global singleton.

---

# 9. Event Loop + Async

GUI event loop có thể tích hợp với Future/executor:

```text
OS Event
    ↓
Event Source
    ↓
Future
    ↓
await
```

nhưng GUI không được tự động phụ thuộc vào async runtime.

---

# 10. Input

Input events:

```text
Keyboard
Mouse
Touch
Pen
Gamepad
TextInput
IME
```

---

# 11. Keyboard

Không nên chỉ biểu diễn key bằng ASCII.

Phân biệt:

```text
PhysicalKey
LogicalKey
Modifier
TextInput
```

Ví dụ cùng phím vật lý có thể tạo ký tự khác nhau tùy keyboard layout.

---

# 12. Text Input

Text input phải đi qua Unicode-aware pipeline.

Không dùng:

```text
key == character
```

một cách đơn giản.

IME cần:

```text
composition
candidate
commit
```

---

# 13. Mouse

Semantic event:

```text
position
buttons
wheel
pressure
device
```

tọa độ phải có coordinate-space contract.

---

# 14. Coordinate Systems

Tái sử dụng 379:

```text
Screen
Window
Client
Viewport
World
Local
```

Không được âm thầm trộn coordinate systems.

---

# 15. Touch

Touch cần logical identity:

```text
TouchId
```

không phải memory address.

---

# 16. DPI

GUI phải phân biệt:

```text
LogicalPixels
PhysicalPixels
DPI
ScaleFactor
```

Một UI layout không nên phụ thuộc trực tiếp physical pixel nếu không yêu cầu.

---

# 17. High-DPI

Window có thể:

```text
logical size = 800×600
physical framebuffer = 1600×1200
```

Rendering layer phải biết conversion.

---

# 18. Surface

Window rendering target:

```text
Surface
```

có:

```text
format
size
color space
present mode
storage/device
```

---

# 19. Swapchain

GPU backend có thể dùng:

```text
Swapchain
Framebuffer
Image
ImageView
```

nhưng không bắt buộc Core GPU abstraction phải biết API cụ thể.

---

# 20. Graphics Backend

Axiom nên có backend abstraction:

```text
Vulkan
Direct3D
Metal
OpenGL
WebGPU
Software
```

Backend không phải language runtime.

---

# 21. Rendering API

Không nên thiết kế GUI API phụ thuộc trực tiếp một graphics API.

Semantic operations:

```text
draw
clear
copy
blend
transform
clip
```

sau đó lower xuống backend.

---

# 22. Render Context

```text
RenderContext
```

chứa capability cần thiết để render.

Không dùng global graphics state nếu không cần.

---

# 23. Immediate vs Retained UI

Axiom nên hỗ trợ cả hai semantic models.

### Immediate

```text
ui {
    button(...)
    text(...)
    image(...)
}
```

mỗi frame mô tả UI.

### Retained

```text
WidgetTree
```

state tồn tại giữa frames.

---

# 24. Không ép class hierarchy

Retained UI vẫn có thể dùng:

```text
struct Widget
struct Button
struct TextBox
```

và traits:

```text
trait Renderable
trait Layoutable
trait Interactive
```

Không cần:

```text
class Button : Widget
```

---

# 25. Widget

Widget nên là logical abstraction:

```text
WidgetId
WidgetState
WidgetLayout
WidgetStyle
```

Identity tách khỏi physical memory.

---

# 26. Widget Tree

```text
Window
 └── Root
      ├── Panel
      │    ├── Button
      │    └── Text
      └── Image
```

Tree topology có thể lưu bằng arena/index/generation handle.

Không yêu cầu object pointers.

---

# 27. WidgetId

```text
WidgetId {
    index
    generation
}
```

tái sử dụng Handle/Growth semantics từ 389.

---

# 28. Widget Mutation

Structural mutation:

```text
add_child
remove_child
reparent
```

có thể invalidate một số views.

Compiler/runtime phải có invalidation contract.

---

# 29. UI State

UI state nên là data:

```text
struct AppState {
    counter: i32
    selected: Option<ItemId>
}
```

Không bắt buộc hidden object state.

---

# 30. Event → State → Render

Một mô hình tự nhiên:

```text
Event
  ↓
Update(State)
  ↓
Layout
  ↓
Render
```

Compiler có thể optimize các bước khi semantics cho phép.

---

# 31. Unidirectional Data Flow

Có thể hỗ trợ pattern:

```text
State
 ↓
View
 ↓
Event
 ↓
Action
 ↓
State
```

nhưng đây là library architecture, không phải Core rule.

---

# 32. Reactive State

Reactive abstraction:

```text
Signal<T>
Computed<T>
Effect
```

có thể xây trên dependency graph.

Không cần GC.

---

# 33. Dependency Graph

Ví dụ:

```text
name
 ↓
display_name
 ↓
label
```

Compiler/library có thể theo dõi dependency.

---

# 34. Change Detection

Có thể sử dụng:

```text
dirty flag
version
dependency graph
structural equality
```

thay vì scan toàn bộ UI.

---

# 35. Retained Rendering

Render tree:

```text
UI Tree
 ↓
Render Tree
 ↓
Draw Commands
 ↓
GPU
```

UI tree và render tree không nhất thiết cùng representation.

---

# 36. Render Command Buffer

```text
DrawCommand {
    pipeline
    vertices
    indices
    texture
    transform
    clip
}
```

có thể compile thành contiguous buffers.

---

# 37. Batching

Renderer có thể tự động:

```text
draw A
draw B
draw C
```

→

```text
batch
```

nếu state transitions cho phép.

---

# 38. State Sorting

Có thể reorder draw calls nếu:

- không thay đổi blending;
- depth semantics;
- transparency;
- ordering;
- side effects.

---

# 39. GPU Integration

Render operations lower xuống GPU kernels/graphics API.

Graphics pipeline không đồng nhất với compute kernel.

---

# 40. Graphics Pipeline

Có thể biểu diễn:

```text
Vertex
Primitive Assembly
Rasterization
Fragment
Depth/Stencil
Blend
Present
```

---

# 41. Shader

Shader là code chạy trên GPU.

Axiom có thể hỗ trợ:

```text
@vertex
@fragment
@compute
```

---

# 42. Shader Compilation

Shader source:

```text
Axiom
 ↓
Shader IR
 ↓
SPIR-V / DXIL / MSL / backend
```

Không nhất thiết compile shader thành CPU machine code.

---

# 43. Shader Type Safety

Shader parameters phải được kiểm tra:

```text
type
layout
binding
address space
alignment
stage
```

---

# 44. Resource Binding

GPU resource:

```text
Texture
Sampler
Buffer
UniformBuffer
StorageBuffer
```

có explicit capability.

---

# 45. Bindings

Binding layout:

```text
set
binding
type
visibility
```

phải được compiler/backend kiểm tra.

---

# 46. Uniform Data

Uniform struct có thể dùng:

```text
@repr(gpu)
struct Camera {
    view: Mat4
    projection: Mat4
}
```

để compiler biết GPU ABI layout.

---

# 47. CPU/GPU Layout

Data Layout Engine 389 có thể chuyên biệt hóa:

```text
CPU layout
GPU layout
```

nhưng chỉ được tự động thay đổi khi boundary contract cho phép.

---

# 48. Texture

Texture semantic type:

```text
Texture<T, Shape, Format>
```

với:

```text
width
height
depth
mips
layers
format
```

---

# 49. Texture View

```text
TextureView
```

cho phép:

```text
mip
layer
region
format view
```

theo capability contract.

---

# 50. Sampler

Sampler là configuration:

```text
filter
address_mode
anisotropy
compare
```

có thể là immutable value hoặc GPU resource tùy backend.

---

# 51. Render Target

Render target:

```text
ColorTarget
DepthTarget
StencilTarget
```

có explicit format/load/store semantics.

---

# 52. Render Pass

Render pass mô tả:

```text
attachments
load
store
dependencies
transitions
```

Compiler/backend có thể tối ưu memory barriers.

---

# 53. GPU Synchronization

Tái sử dụng 367:

```text
GpuEvent
GpuBarrier
GpuFence
```

không dùng CPU mutex để mô hình hóa GPU dependency.

---

# 54. Frame Graph

Một abstraction rất quan trọng:

```text
Pass A
 ↓
Texture X
 ↓
Pass B
 ↓
Texture Y
 ↓
Pass C
```

Compiler có thể xây dependency graph.

---

# 55. Resource Lifetime

Frame graph biết:

```text
first use
last use
```

→ có thể reuse GPU memory.

Điều này kết hợp trực tiếp với 389.

---

# 56. Transient Resource Aliasing

Hai texture:

```text
A lifetime: frame 0–2
B lifetime: frame 3–5
```

có thể dùng cùng physical allocation nếu không overlap.

Compiler có thể chứng minh:

```text
DISJOINT_LIFETIME
```

---

# 57. Render Graph Optimization

Có thể:

```text
remove unused pass
merge compatible passes
alias resources
batch barriers
fuse compatible operations
```

---

# 58. CPU Rendering

Không bắt buộc GPU.

Có:

```text
SoftwareRenderer
```

sử dụng:

```text
SIMD
parallel
tile rendering
```

---

# 59. Vector Graphics

Semantic primitives:

```text
Path
Line
Bezier
Fill
Stroke
Clip
Transform
```

có thể dùng Geometry engine 379.

---

# 60. Rasterization

Vector graphics có thể lower:

```text
Path
 ↓
Tessellation
 ↓
Triangles
 ↓
GPU/CPU renderer
```

---

# 61. Text Rendering

Text rendering cần:

```text
Unicode
Font
Glyph
Shaping
Rasterization
```

---

# 62. Text ≠ Glyph

String:

```text
"abc"
```

không trực tiếp tương ứng 3 glyph.

Shaping engine quyết định glyph sequence.

---

# 63. Text Shaping

Pipeline:

```text
Unicode Text
 ↓
Script detection
 ↓
Shaping
 ↓
Glyph IDs
 ↓
Positioning
 ↓
Rasterization
```

---

# 64. Font

Font resource:

```text
Font
FontFace
FontInstance
GlyphAtlas
```

có resource lifetime.

---

# 65. Font Layout

Font metrics có thể bao gồm:

```text
ascent
descent
line_gap
advance
kerning
```

---

# 66. Glyph Atlas

Renderer có thể cache glyphs vào texture atlas.

Đây là optimization, không phải semantic requirement.

---

# 67. Accessibility

GUI phải có semantic accessibility tree:

```text
role
name
value
state
actions
children
```

Không được suy ra hoàn toàn từ pixels.

---

# 68. Accessibility Backend

Có thể map tới:

```text
Windows UI Automation
macOS Accessibility
Linux AT-SPI
Web accessibility
```

---

# 69. Accessibility Identity

Accessibility node có logical identity, không phải memory address.

---

# 70. Clipboard

Clipboard là OS resource/data exchange:

```text
Text
Image
Files
CustomFormat
```

security/capability contract từ 394.

---

# 71. Drag & Drop

Drag payload phải có ownership:

```text
DragSource
DragPayload
DropTarget
```

Không dùng dangling pointer tới widget.

---

# 72. Clipboard Security

Sensitive `Secret<T>` không được tự động copy ra clipboard.

Nếu muốn:

```text
explicit export
```

---

# 73. File Dialog

File dialog trả capability/resource thay vì chỉ path string khi security semantics yêu cầu.

---

# 74. Native Controls

Axiom có thể wrap native controls:

```text
NativeButton
NativeTextBox
NativeMenu
```

qua FFI/system backend.

---

# 75. Custom Controls

Renderer có thể tự vẽ hoàn toàn.

Do đó Axiom không phụ thuộc native widget system.

---

# 76. Styling

Style có thể là data:

```text
Style {
    font
    color
    background
    border
    padding
    margin
}
```

không cần inheritance hierarchy.

---

# 77. CSS-like Model

Một library có thể cung cấp selector:

```text
Button.primary
Panel > Button
```

nhưng compiler không cần có CSS engine trong Core.

---

# 78. Layout

Layout algorithms:

```text
Absolute
Stack
Flex
Grid
Constraint
Flow
```

---

# 79. Layout as Pure Computation

Nếu layout không có external effect:

```text
Input geometry
 + style
 + state
 → LayoutResult
```

có thể được compiler tối ưu mạnh.

---

# 80. Layout Parallelism

Các subtree độc lập có thể layout song song nếu không có dependency.

---

# 81. Layout + SIMD

Large UI trees có thể dùng batch operations.

Không phải mọi widget đều cần object dispatch.

---

# 82. Layout Cache

Cache layout khi:

```text
inputs unchanged
```

có thể tránh recomputation.

---

# 83. Animation

Animation là function:

```text
value = f(time)
```

có thể sử dụng:

```text
Curve
Keyframe
Spring
Tween
Easing
```

---

# 84. Animation + Comptime

Static animation data có thể compile vào binary.

Không cần runtime parser.

---

# 85. Frame Timing

Phải phân biệt:

```text
WallClock
MonotonicClock
PresentationTime
FrameTime
GPUTime
```

---

# 86. VSync

VSync/presentation là rendering synchronization, không phải CPU synchronization primitive.

---

# 87. Frame Pacing

Renderer nên expose:

```text
frame start
simulation
layout
render
submit
present
```

để tránh implicit blocking.

---

# 88. Input Latency

Compiler/runtime có thể tối ưu pipeline:

```text
input
 ↓
state
 ↓
render
 ↓
present
```

nhưng không được thay đổi event ordering.

---

# 89. Multi-Window

Một application có thể có:

```text
Window A
Window B
Window C
```

không cần global UI singleton.

---

# 90. Multi-Display

Display:

```text
DisplayId
Monitor
DisplayMode
Dpi
Scale
```

là system resources.

---

# 91. Fullscreen

Phân biệt:

```text
BorderlessFullscreen
ExclusiveFullscreen
MaximizedWindow
```

không gộp thành một boolean.

---

# 92. Offscreen Rendering

Có thể render:

```text
Window
Texture
Image
Video
```

cùng semantic rendering graph.

---

# 93. GUI + Video

Render graph có thể nhận:

```text
VideoFrame
```

từ I/O/decoder → GPU texture → UI.

Zero-copy nếu storage domain/format phù hợp.

---

# 94. GUI + ML

ML output:

```text
Tensor
```

có thể render trực tiếp nếu layout/storage compatible:

```text
Tensor
 ↓
ImageView
 ↓
Texture
```

tránh copy.

---

# 95. GUI + Scientific Visualization

Tensor/mesh/graph data từ các domain trước có thể đi:

```text
Simulation
 ↓
Tensor/Mesh
 ↓
RenderGraph
 ↓
GPU
```

---

# 96. GUI + Database

Database query có thể produce:

```text
ColumnView
```

sau đó render table/chart mà không cần materialize object-per-row.

---

# 97. Immediate UI + Compiler

Static UI code:

```text
ui {
    text(...)
    button(...)
}
```

có thể compiler specialize thành draw commands.

---

# 98. Dynamic UI

Nếu widget structure runtime-generated:

```text
WidgetTree
```

thì runtime representation vẫn cần thiết.

Nhưng nó là library runtime, không phải language runtime bắt buộc.

---

# 99. CompilerDB

Bổ sung:

```text id="a6u9c8"
GuiDB
WindowDB
WindowTypeDB
WindowHandleDB
WindowConfigDB
WindowStateDB
WindowEventDB
WindowLifecycleDB
WindowSurfaceDB

DisplayDB
DisplayIdDB
DisplayModeDB
DpiDB
ScaleFactorDB

InputDB
KeyboardDB
PhysicalKeyDB
LogicalKeyDB
ModifierDB
TextInputDB
ImeDB
MouseDB
TouchDB
PenDB
GamepadDB
InputDeviceDB

EventLoopDB
GuiEventDB
GuiDispatchDB
GuiAsyncDB

WidgetDB
WidgetTypeDB
WidgetIdDB
WidgetTreeDB
WidgetStateDB
WidgetLayoutDB
WidgetStyleDB
WidgetEventDB
WidgetMutationDB
WidgetInvalidationDB

UiStateDB
ReactiveStateDB
SignalDB
ComputedDB
EffectDB
DependencyGraphDB
ChangeDetectionDB

LayoutDB
LayoutConstraintDB
FlexLayoutDB
GridLayoutDB
StackLayoutDB
FlowLayoutDB
ConstraintLayoutDB
LayoutCacheDB
LayoutParallelDB

RenderDB
RenderContextDB
RenderSurfaceDB
RenderPassDB
RenderCommandDB
RenderCommandBufferDB
RenderBatchDB
RenderStateDB
RenderSortDB
RenderTargetDB

GraphicsDB
GraphicsBackendDB
GraphicsDeviceDB
GraphicsQueueDB
GraphicsFenceDB
GraphicsSemaphoreDB
GraphicsResourceDB

SwapchainDB
FramebufferDB
GraphicsImageDB
GraphicsImageViewDB
GraphicsBufferDB
GraphicsSamplerDB
GraphicsPipelineDB
GraphicsShaderDB
GraphicsBindingDB

ShaderDB
ShaderStageDB
ShaderTypeDB
ShaderLayoutDB
ShaderBindingDB
ShaderCompilationDB
ShaderIrDB

TextureDB
TextureTypeDB
TextureFormatDB
TextureViewDB
TextureMipDB
TextureLayerDB
TextureAtlasDB

FrameGraphDB
FramePassDB
FrameResourceDB
FrameDependencyDB
FrameLifetimeDB
FrameAliasingDB
FrameBarrierDB
FrameFusionDB

VectorGraphicsDB
PathDB
BezierDB
FillDB
StrokeDB
TessellationDB
RasterizationDB

TextRenderingDB
FontDB
FontFaceDB
FontInstanceDB
GlyphDB
GlyphRunDB
TextShapingDB
GlyphAtlasDB

AccessibilityDB
AccessibilityNodeDB
AccessibilityTreeDB
AccessibilityRoleDB
AccessibilityStateDB
AccessibilityActionDB

ClipboardDB
DragDropDB
FileDialogDB
NativeControlDB

AnimationDB
KeyframeDB
CurveDB
TweenDB
SpringDB
FrameTimingDB
PresentationDB

SoftwareRendererDB
CpuRendererDB
GpuRendererDB

GuiImageDB
GuiVideoDB
GuiTensorDB
GuiMeshDB
GuiDatabaseDB

GuiSecurityDB
GuiCapabilityDB
GuiSecretDB

GuiOptimizationDB
GuiCostModelDB
GuiVerificationDB
```

---

# 100. MIR

```text id="8x0r2y"
WINDOW_CREATE
WINDOW_SHOW
WINDOW_HIDE
WINDOW_CLOSE
WINDOW_RESIZE
WINDOW_MOVE
WINDOW_FOCUS
WINDOW_PRESENT

DISPLAY_QUERY
DISPLAY_MODE_QUERY
DPI_QUERY

EVENT_POLL
EVENT_WAIT
EVENT_DISPATCH

INPUT_KEY
INPUT_TEXT
INPUT_MOUSE
INPUT_TOUCH
INPUT_PEN
INPUT_GAMEPAD

UI_STATE_READ
UI_STATE_WRITE
UI_SIGNAL_READ
UI_SIGNAL_WRITE
UI_COMPUTED
UI_EFFECT

WIDGET_CREATE
WIDGET_DESTROY
WIDGET_ATTACH
WIDGET_DETACH
WIDGET_REPARENT
WIDGET_EVENT
WIDGET_INVALIDATE

LAYOUT_BEGIN
LAYOUT_MEASURE
LAYOUT_ARRANGE
LAYOUT_SOLVE
LAYOUT_END

RENDER_BEGIN
RENDER_END
RENDER_CLEAR
RENDER_DRAW
RENDER_BATCH
RENDER_SORT
RENDER_CLIP
RENDER_TRANSFORM

FRAME_BEGIN
FRAME_PASS
FRAME_RESOURCE
FRAME_DEPENDENCY
FRAME_BARRIER
FRAME_ALIAS
FRAME_END

GPU_SURFACE_CREATE
GPU_SWAPCHAIN_CREATE
GPU_FRAMEBUFFER_CREATE
GPU_TEXTURE_CREATE
GPU_BUFFER_CREATE
GPU_SAMPLER_CREATE
GPU_PIPELINE_CREATE
GPU_SHADER_CREATE
GPU_BIND

SHADER_COMPILE
SHADER_LINK

TEXT_SHAPE
GLYPH_LAYOUT
GLYPH_RASTERIZE

ACCESSIBILITY_CREATE
ACCESSIBILITY_UPDATE

CLIPBOARD_READ
CLIPBOARD_WRITE

DRAG_BEGIN
DRAG_DROP

ANIMATION_EVALUATE
PRESENT
```

---

# 101. Proof System

```text id="v4d6e1"
WindowOwnershipProof
WindowLifetimeProof
WindowCapabilityProof
WindowEventOrderingProof

InputOrderingProof
InputCoordinateProof
InputLifetimeProof

WidgetOwnershipProof
WidgetTreeProof
WidgetIdentityProof
WidgetMutationProof
WidgetInvalidationProof

UiStateProof
ReactiveDependencyProof
ChangeDetectionProof

LayoutConstraintProof
LayoutBoundsProof
LayoutDependencyProof
LayoutCacheProof
LayoutParallelProof

RenderOrderingProof
RenderStateProof
RenderBatchProof
RenderSortProof
RenderFusionProof

GraphicsResourceProof
GraphicsBindingProof
GraphicsLayoutProof
GraphicsSynchronizationProof

ShaderTypeProof
ShaderBindingProof
ShaderAbiProof
ShaderSafetyProof

TextureBoundsProof
TextureLayoutProof
TextureViewProof

FrameGraphProof
FrameDependencyProof
FrameLifetimeProof
FrameAliasingProof
FrameBarrierProof

VectorGeometryProof
TessellationProof

TextEncodingProof
TextShapingProof
GlyphLayoutProof

AccessibilityProof
ClipboardCapabilityProof
DragDropOwnershipProof

AnimationTimingProof
PresentationProof

GuiTensorProof
GuiVideoProof
GuiMeshProof
GuiDatabaseProof

GuiSecurityProof
GuiOptimizationProof
GuiVerificationProof
```

---

# 102. Invariants

### `AGUI-01`
Window là resource có ownership rõ ràng.

### `AGUI-02`
Window handle không mặc định `Copy`.

### `AGUI-03`
Window lifecycle phải được xác định trước khi sử dụng.

### `AGUI-04`
Event ordering observable không được thay đổi bởi optimizer.

### `AGUI-05`
GUI event loop không mặc định yêu cầu async runtime.

### `AGUI-06`
Blocking GUI operation phải được compiler nhận diện.

### `AGUI-07`
Physical key và logical text input phải được phân biệt.

### `AGUI-08`
Coordinate spaces không được implicit-compatible nếu semantic khác nhau.

### `AGUI-09`
Logical pixels và physical pixels phải được phân biệt.

### `AGUI-10`
Widget identity không phụ thuộc physical memory address.

### `AGUI-11`
Widget mutation phải tuân thủ capability invalidation.

### `AGUI-12`
Widget view không được sống qua mutation có thể invalidate nó.

### `AGUI-13`
UI state không được ngầm tạo shared mutable global state.

### `AGUI-14`
Reactive dependency graph không được tạo dependency cycle không được xử lý.

### `AGUI-15`
Layout phải preserve declared geometric constraints.

### `AGUI-16`
Layout cache chỉ được reuse khi toàn bộ semantic dependencies còn hợp lệ.

### `AGUI-17`
Render command reordering chỉ hợp lệ khi observable rendering semantics không đổi.

### `AGUI-18`
Blending/depth/transparency ordering phải được preserve khi observable.

### `AGUI-19`
GPU resource lifetime phải bao phủ mọi asynchronous GPU use.

### `AGUI-20`
GPU binding layout phải khớp shader contract.

### `AGUI-21`
Shader memory access phải tuân thủ GPU address-space và bounds semantics.

### `AGUI-22`
Frame-resource aliasing chỉ được phép khi lifetimes proven disjoint.

### `AGUI-23`
Render graph fusion phải preserve synchronization dependencies.

### `AGUI-24`
Texture view phải preserve bounds, format và storage-domain contract.

### `AGUI-25`
Text input phải preserve Unicode semantics.

### `AGUI-26`
Glyph layout không được đồng nhất trực tiếp với Unicode code points.

### `AGUI-27`
Accessibility semantics không được bị mất khi custom rendering.

### `AGUI-28`
Secret data không được tự động xuất ra clipboard, logs hoặc accessibility tree.

### `AGUI-29`
GUI optimization có thể thay đổi physical representation nhưng không được thay đổi observable UI semantics.

### `AGUI-30`
Chương trình không sử dụng GUI/graphics subsystem không được kéo theo GUI runtime bắt buộc.

---

## Điểm kiến trúc quan trọng của 397

Sau bước này Axiom bắt đầu có một đường đi rất mạnh từ **data → compute → visualization**:

```text
Database
    ↓
Tensor / Graph / Simulation
    ↓
Data Layout
    ↓
CPU SIMD / GPU
    ↓
Render Graph
    ↓
Native Window
```

Và quan trọng hơn, GUI **không bắt Axiom phải quay lại mô hình OOP cổ điển**:

```text
❌ Window
   └── Widget
       └── Button
           └── TextButton
               └── ...
```

thay vào đó:

```text
Window
  │
  ├── State
  ├── WidgetId
  ├── WidgetData
  ├── Layout
  ├── Event
  └── RenderData
```

kết hợp với:

```text
struct + function + trait + generic
```

và compiler có thể biến abstraction đó thành **flat data + direct calls + SIMD/GPU/native calls** khi có thể.

Đây chính là nơi triết lý **“compiler phức tạp hơn programmer”** của Axiom phát huy rất mạnh.