Tiếp tục với kiến trúc kế tiếp, xây trực tiếp trên BOOTSTRAP-614 và hoàn thiện lớp đồ họa native của Axiom.

:::writing{variant="document" id="58321" title="BOOTSTRAP-615 — Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0"}

# BOOTSTRAP-615
## Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0

**Status:** Architecture Specification — Complete  
**Layer:** Native Runtime / Graphics  
**Depends on:** BOOTSTRAP-603, 606, 607, 608, 611, 612, 613, 614  
**Provides foundations for:** GUI, game engine, visualization, scientific rendering, CAD, video composition, ML visualization, 3D engine, editor/runtime UI

---

# 1. Purpose

BOOTSTRAP-615 defines Axiom's native graphics-facing runtime.

Its responsibility is to transform the hardware/device abstractions from BOOTSTRAP-614 into a coherent graphics system supporting:

- native windows;
- display surfaces;
- offscreen rendering;
- swapchains;
- render targets;
- textures;
- buffers;
- samplers;
- shaders;
- pipelines;
- command recording;
- render passes;
- compute passes;
- resource transitions;
- synchronization;
- presentation;
- frame pacing;
- color management;
- HDR;
- multi-window rendering;
- headless rendering;
- software rendering;
- GPU loss/recovery;
- render graphs;
- GPU profiling.

The architecture must support both:

```text
simple application
    ↓
Window
    ↓
GraphicsContext
    ↓
draw(...)
```

and:

```text
high-performance engine
    ↓
RenderGraph
    ↓
CommandEncoder
    ↓
Pipeline
    ↓
GPU CommandBuffer
    ↓
GpuQueue
    ↓
GPU
```

without forcing the simple application to understand the full GPU model.

---

# 2. Design Goals

The graphics runtime SHALL provide:

1. Native performance.
2. Explicit GPU resource lifetime.
3. Predictable synchronization.
4. Minimal hidden allocations.
5. Minimal hidden GPU stalls.
6. Deterministic command recording.
7. Cross-platform abstraction without lowest-common-denominator design.
8. Access to backend-specific capabilities when explicitly requested.
9. Headless rendering.
10. CPU/software fallback.
11. GPU device-loss recovery.
12. HDR and color-management support.
13. Multi-monitor and DPI awareness.
14. Async GPU execution.
15. Efficient transient resources.
16. Render-graph optimization.
17. Shader compilation and caching.
18. Package integration.
19. Resource quota integration.
20. Security/capability integration.

---

# 3. Non-Goals

615 does not define:

- a complete GUI widget toolkit;
- retained-mode UI controls;
- layout engines;
- text shaping;
- font rasterization;
- animation frameworks;
- game-engine ECS;
- scene graphs;
- physics;
- image editing;
- video editing;
- 3D asset authoring.

Those belong to higher layers.

615 provides the rendering substrate those systems use.

---

# 4. Layering

The architecture is:

```text
Axiom Application
       │
       ▼
GUI / Engine / Visualization
       │
       ▼
Rendering API
       │
       ├── Simple Graphics API
       └── Explicit Graphics API
              │
              ▼
         Render Graph
              │
              ▼
       Command Recording
              │
              ▼
      Graphics Backend Adapter
              │
       ┌──────┼─────────┐
       ▼      ▼         ▼
    Vulkan  D3D12     Metal
       │      │         │
       └──────┼─────────┘
              ▼
       BOOTSTRAP-614
       Device Runtime
              │
              ▼
          OS / GPU
```

615 MUST NOT duplicate device discovery, device identity, GPU memory ownership or device security already defined by 614.

---

# 5. Core Graphics Context

The top-level object is:

```text
GraphicsContext
```

Conceptually:

```text
GraphicsContext
├── Device
├── DisplayManager
├── SurfaceManager
├── ShaderCompiler
├── PipelineCache
├── ResourceFactory
├── FrameScheduler
└── Diagnostics
```

The context owns configuration and backend state but does not imply global singleton behavior.

Multiple independent graphics contexts MAY exist.

---

# 6. Graphics Adapter

A graphics adapter represents one graphics-capable device.

```text
GraphicsAdapter
```

contains:

```text
AdapterId
Name
Vendor
Architecture
ApiVersion
DriverVersion
Capabilities
MemoryInfo
QueueCapabilities
FormatCapabilities
FeatureSet
```

The underlying physical device originates from 614.

---

# 7. Graphics Device

```text
GraphicsDevice
```

represents the logical graphics device.

It owns:

- graphics queues;
- compute queues;
- transfer queues;
- resource allocators;
- descriptor allocators;
- pipeline caches;
- shader modules;
- command pools;
- synchronization primitives.

A graphics device is invalidated when the underlying 614 device is lost.

---

# 8. Device State

```text
GraphicsDeviceState =
    Created
    Ready
    Lost
    Recovering
    Recreated
    Destroyed
```

Normal flow:

```text
Created
   ↓
Ready
   ↓
Lost
   ↓
Recovering
   ↓
Recreated
   ↓
Ready
```

The runtime MUST NOT silently continue using resources belonging to a lost generation.

---

# 9. Device Generation

Every logical graphics device has:

```text
DeviceGeneration
```

A resource contains:

```text
DeviceId
Generation
ResourceId
```

A resource from generation N MUST NOT be submitted to generation N+1.

This prevents stale GPU handles after device reset.

---

# 10. Window Model

615 defines the native window abstraction.

```text
Window
WindowId
WindowHandle
```

A window contains:

```text
Position
Size
ClientSize
DpiScale
Visibility
FocusState
FullscreenState
Decorations
Resizable
MinSize
MaxSize
Monitor
Surface
```

---

# 11. Window States

```text
WindowState =
    Created
    Hidden
    Visible
    Minimized
    Maximized
    Fullscreen
    Closing
    Closed
```

Transitions are event-driven.

---

# 12. Window Events

```text
WindowEvent =
    Created
    Shown
    Hidden
    Moved
    Resized
    DpiChanged
    FocusGained
    FocusLost
    Minimized
    Restored
    Maximized
    FullscreenChanged
    CloseRequested
    Closed
    DisplayChanged
    SurfaceInvalidated
```

Events integrate with BOOTSTRAP-607.

The graphics layer MUST NOT create a second independent event loop.

---

# 13. Native Window Backends

Supported mappings include:

### Windows

```text
Win32 HWND
```

### macOS

```text
NSWindow / CAMetalLayer
```

### Linux

```text
Wayland
X11
```

### Android

```text
Activity / Surface
```

### iOS

```text
UIWindow / UIView / CAMetalLayer
```

### WASM/Web

```text
HTMLCanvasElement
WebGPU surface
```

### Embedded

```text
Framebuffer / DisplayController
```

Backend availability is capability-dependent.

---

# 14. Window Thread Affinity

Some native platforms require UI operations on a specific thread.

615 therefore defines:

```text
WindowAffinity
```

A window MAY be:

```text
ThreadAffine
ThreadAgile
PlatformDefined
```

The runtime MUST reject operations violating platform affinity.

No implicit thread migration is allowed.

---

# 15. Display Manager

```text
DisplayManager
```

provides:

```text
enumerate_displays()
primary_display()
display(id)
```

A display contains:

```text
DisplayId
Name
PhysicalSize
LogicalSize
Dpi
Scale
RefreshRate
Modes
HdrCapabilities
ColorSpaces
```

---

# 16. Display Mode

```text
DisplayMode
```

contains:

```text
Width
Height
RefreshNumerator
RefreshDenominator
PixelFormat
ColorSpace
HdrMode
```

Refresh rates MUST be represented as rational values rather than floating-point numbers.

Example:

```text
60000 / 1001
```

---

# 17. DPI

615 uses logical pixels and physical pixels explicitly.

```text
LogicalSize
PhysicalSize
DpiScale
```

Conversions:

```text
physical = logical × dpi_scale
logical  = physical / dpi_scale
```

The runtime MUST NOT silently round intermediate geometry.

---

# 18. Fullscreen

Supported modes:

```text
Windowed
BorderlessFullscreen
ExclusiveFullscreen
```

Exclusive fullscreen is optional and backend-dependent.

Applications MUST be able to detect whether requested fullscreen mode was actually granted.

---

# 19. Graphics Surface

A `Surface` connects a native window/display target to the graphics device.

```text
Surface
```

contains:

```text
SurfaceId
WindowId?
Capabilities
Formats
PresentModes
Extent
ColorSpaces
```

A surface MAY be:

```text
WindowSurface
HeadlessSurface
OffscreenSurface
ExternalSurface
```

---

# 20. Headless Surface

Headless rendering is first-class.

Example:

```text
surface = Graphics.create_headless_surface(
    width: 1920,
    height: 1080,
    format: RGBA8
)
```

No OS window is required.

This enables:

- server rendering;
- automated tests;
- screenshots;
- video generation;
- CI;
- cloud rendering;
- ML visualization.

---

# 21. Swapchain

A `Swapchain` manages presentation images.

```text
Swapchain
```

contains:

```text
Surface
ImageCount
Format
Extent
ColorSpace
PresentMode
Usage
Generation
```

---

# 22. Swapchain Lifecycle

Typical frame:

```text
acquire()
   ↓
BackBuffer
   ↓
render
   ↓
transition → Present
   ↓
submit
   ↓
present()
```

Acquired images MUST NOT be simultaneously acquired twice.

---

# 23. Present Modes

615 defines:

```text
Fifo
Mailbox
Immediate
FifoRelaxed
```

Backend support is queried dynamically.

The application can request a mode but MUST inspect the actual selected mode.

---

# 24. Frames In Flight

A graphics context supports:

```text
MaxFramesInFlight
```

Typical:

```text
1
2
3
```

The runtime MUST NOT assume three frames universally.

---

# 25. Present Token

```text
PresentToken
```

represents one presentation operation.

It contains:

```text
FrameId
SwapchainGeneration
ImageIndex
PresentSequence
```

This allows diagnostics to associate:

```text
CPU frame
GPU submission
GPU completion
display presentation
```

---

# 26. Frame Scheduler

```text
FrameScheduler
```

coordinates:

```text
Acquire
CPU simulation
Command recording
GPU submission
Present
Frame completion
```

It integrates with 607 rather than creating its own thread pool.

---

# 27. Frame Pacing

The scheduler supports:

```text
VSync
AdaptiveVSync
Uncapped
FixedRate
DisplayDriven
```

Frame pacing MUST avoid busy-waiting.

Sleep/wait operations use 607 timers and OS-native synchronization.

---

# 28. Render Resources

Core resource types:

```text
Buffer
Texture
TextureView
Sampler
RenderBuffer
DepthStencilBuffer
ShaderModule
Pipeline
DescriptorSet
QueryPool
```

All are explicit handles.

---

# 29. Buffer

```text
Buffer
```

has:

```text
Size
Usage
MemoryType
Flags
DeviceGeneration
```

Usage flags:

```text
Vertex
Index
Uniform
Storage
Indirect
CopySource
CopyDestination
Readback
Upload
```

---

# 30. Texture

```text
Texture
```

contains:

```text
Width
Height
Depth
MipLevels
ArrayLayers
Format
Samples
Usage
Dimension
```

Dimensions:

```text
1D
2D
3D
Cube
CubeArray
2DArray
```

---

# 31. Texture Usage

```text
Sampled
Storage
RenderTarget
DepthStencil
CopySource
CopyDestination
InputAttachment
Present
```

Usage MUST be declared when required by the backend.

---

# 32. Texture Formats

Core format families:

```text
RGBA8
BGRA8
RGBA16F
RGBA32F

R8
RG8
R16
RG16
R32
RG32

Depth16
Depth24
Depth32F

Depth24Stencil8
Depth32Stencil8
```

Optional compressed families:

```text
BC
ETC
ASTC
PVRTC
```

Applications query capabilities rather than assuming support.

---

# 33. Color Encoding

Each texture view explicitly identifies:

```text
Linear
sRGB
HDR
Integer
Normalized
Float
```

A resource MUST NOT silently reinterpret sRGB as linear.

---

# 34. Multisampling

Supported sample counts are device capabilities.

Typical:

```text
1
2
4
8
16
```

The runtime exposes:

```text
SampleCount
```

rather than assuming fixed support.

---

# 35. Render Target

A render target is:

```text
ColorAttachment*
DepthAttachment?
StencilAttachment?
```

It can represent:

- swapchain image;
- texture;
- multisample target;
- offscreen framebuffer.

---

# 36. Render Pass

```text
RenderPass
```

declares:

```text
ColorAttachments
DepthAttachment
StencilAttachment
ClearValues
LoadOperations
StoreOperations
```

Load operations:

```text
Load
Clear
DontCare
```

Store operations:

```text
Store
DontCare
```

This metadata enables tile-based GPU optimization.

---

# 37. Compute Pass

```text
ComputePass
```

contains:

```text
Pipeline
Bindings
Dispatch
DispatchIndirect
```

Compute and graphics passes MAY execute on separate queues when hardware supports it.

---

# 38. Copy Pass

```text
CopyPass
```

supports:

```text
Buffer → Buffer
Buffer → Texture
Texture → Buffer
Texture → Texture
```

Copy operations are explicit.

---

# 39. Command Encoder

```text
CommandEncoder
```

records commands.

Example:

```text
encoder.begin_render_pass(target)
encoder.bind_pipeline(pipeline)
encoder.bind_vertex_buffer(vertices)
encoder.bind_index_buffer(indices)
encoder.draw_indexed(...)
encoder.end_render_pass()

commands = encoder.finish()
```

---

# 40. Command Buffer

A finished:

```text
CommandBuffer
```

is immutable.

It can be submitted multiple times only when the recorded resource semantics permit it.

Mutable command buffers are not required.

---

# 41. Command State

The encoder tracks:

```text
CurrentPipeline
BoundResources
Viewport
Scissor
BlendState
DepthState
StencilState
VertexBuffers
IndexBuffer
PushConstants
```

Redundant backend state changes SHOULD be removed.

---

# 42. Resource Barriers

Resource transitions are explicit in the low-level model.

States:

```text
Undefined
CopySource
CopyDestination
Vertex
Index
Uniform
Storage
ShaderRead
ShaderWrite
RenderTarget
DepthRead
DepthWrite
Indirect
Present
```

The runtime validates illegal transitions.

---

# 43. Automatic Barrier Mode

Higher-level APIs MAY request:

```text
AutomaticBarriers
```

The render graph calculates transitions.

Low-level APIs MAY use:

```text
ExplicitBarriers
```

for maximum control.

---

# 44. Graphics Pipeline

```text
GraphicsPipeline
```

contains:

```text
VertexShader
FragmentShader
VertexLayout
PrimitiveTopology
RasterState
DepthState
StencilState
BlendState
RenderFormats
SampleCount
PipelineLayout
```

Optional stages:

```text
Geometry
TessellationControl
TessellationEvaluation
Mesh
Task
```

only when supported.

---

# 45. Compute Pipeline

```text
ComputePipeline
```

contains:

```text
ComputeShader
PipelineLayout
WorkgroupLimits
```

---

# 46. Shader Stages

Core:

```text
Vertex
Fragment
Compute
```

Optional:

```text
Geometry
Tessellation
Mesh
Task
RayGeneration
AnyHit
ClosestHit
Miss
Intersection
Callable
```

Optional stages MUST NOT contaminate the core API.

---

# 47. Shader Model

Axiom defines a portable shader representation:

```text
AXSL-IR
```

Axiom Shader Language:

```text
AXSL
```

MAY compile into AXSL-IR.

Backend adapters can then produce:

```text
SPIR-V
DXIL
MSL
WGSL
Native backend representation
```

---

# 48. Shader Compilation

Pipeline:

```text
AXSL
 ↓
Parser
 ↓
Typed Shader AST
 ↓
AXSL-IR
 ↓
Validation
 ↓
Optimization
 ↓
Backend Translation
 ↓
Native Shader
```

The shader compiler is separate from the general application compiler but shares Axiom's compiler infrastructure.

---

# 49. Shader Safety

Shader code MUST be validated before execution.

Validation includes:

- type correctness;
- resource binding correctness;
- stage interface correctness;
- instruction/resource limits;
- backend restrictions;
- workgroup limits;
- recursion restrictions where unsupported;
- memory access legality.

A shader MUST NOT become an unrestricted native CPU program.

---

# 50. Shader Reflection

Compiler output contains:

```text
ShaderReflection
```

with:

```text
Inputs
Outputs
Bindings
PushConstants
Resources
Stages
WorkgroupSize
RequiredFeatures
```

Reflection metadata is generated at compile time.

Runtime reflection is not mandatory.

---

# 51. Pipeline Layout

```text
PipelineLayout
```

describes:

```text
DescriptorSets
PushConstants
ResourceBindings
```

A pipeline MUST declare the layout it expects.

---

# 52. Descriptor Binding

615 supports:

```text
DescriptorSet
```

or equivalent backend abstraction:

```text
BindGroup
```

Bindings include:

```text
UniformBuffer
StorageBuffer
SampledTexture
StorageTexture
Sampler
CombinedTextureSampler
AccelerationStructure
```

---

# 53. Bindless Resources

Bindless/resource-array access is an optional capability.

When supported:

```text
ResourceArray<T>
```

allows shader indexing.

Applications query:

```text
Feature.Bindless
```

before use.

---

# 54. Push Constants

Small frequently changing values use:

```text
PushConstants
```

rather than allocating a new buffer.

Maximum size is backend-dependent.

---

# 55. Samplers

```text
Sampler
```

contains:

```text
MinFilter
MagFilter
MipFilter
AddressU
AddressV
AddressW
MipBias
MinLod
MaxLod
CompareMode
Anisotropy
```

---

# 56. Resource Views

A texture MAY expose multiple views:

```text
TextureView
```

Example:

```text
RGBA16F texture
    ├── mip 0
    ├── mip 1
    └── array layer 3
```

Views do not own the underlying allocation.

---

# 57. GPU Memory

GPU memory uses the 614 memory abstraction.

Classes include:

```text
DeviceLocal
HostVisible
HostCoherent
HostCached
Unified
Protected
```

Actual availability is backend-defined.

---

# 58. Mapping

```text
buffer.map()
```

is permitted only when the allocation supports mapping.

The runtime MUST NOT transparently migrate device-local memory to CPU-visible memory merely because the application calls `map()`.

---

# 59. Upload Path

Typical upload:

```text
CPU memory
   ↓
UploadBuffer
   ↓
CopyCommand
   ↓
DeviceLocalBuffer
```

615 provides reusable upload pools.

---

# 60. Readback Path

Typical readback:

```text
GPU resource
   ↓
CopyCommand
   ↓
ReadbackBuffer
   ↓
CPU
```

Readback SHOULD be asynchronous.

---

# 61. Transient Resources

Render graphs MAY allocate:

```text
TransientTexture
TransientBuffer
```

whose lifetime exists only inside a graph execution window.

Aliasing is allowed when lifetimes do not overlap.

---

# 62. Transient Memory Allocator

The allocator can use:

```text
Buddy
Slab
LinearArena
BestFit
BackendHeap
```

depending on resource type/backend.

No language-level garbage collector is involved.

---

# 63. Descriptor Allocator

Descriptor allocations are pooled.

Pools may be:

```text
FrameLocal
PassLocal
Persistent
Bindless
```

Frame-local descriptors can be reset after GPU completion.

---

# 64. Synchronization

GPU synchronization primitives:

```text
GpuFence
GpuSemaphore
GpuTimeline
GpuEvent
```

---

# 65. Timeline Synchronization

A timeline value:

```text
uint64
```

represents monotonically increasing GPU progress.

Example:

```text
submit(signal = 42)

wait(42)
```

Timeline synchronization SHOULD be preferred where backend support exists.

---

# 66. CPU/GPU Synchronization

The CPU MUST NOT call a global:

```text
GPU.wait_idle()
```

during normal frame operation.

Such waits are reserved for:

- shutdown;
- device recovery;
- explicit debugging;
- resource destruction fallback.

---

# 67. Queue Types

Core queues:

```text
Graphics
Compute
Transfer
```

Optional:

```text
VideoDecode
VideoEncode
Sparse
RayTracing
```

These can be supplied by BOOTSTRAP-616 or specialized extensions.

---

# 68. Queue Submission

```text
GpuQueue.submit(
    commands,
    waits,
    signals
)
```

Submission is asynchronous.

The call MUST NOT imply GPU completion.

---

# 69. Queue Ownership

Resources may have queue ownership requirements.

The render graph or explicit synchronization layer handles:

```text
Graphics → Compute
Compute → Graphics
Transfer → Graphics
```

ownership transitions.

---

# 70. Render Graph

The high-level explicit renderer is based on:

```text
RenderGraph
```

A graph contains:

```text
Resources
Passes
Dependencies
QueueAssignments
Barriers
Lifetimes
```

---

# 71. Render Graph Example

```text
ShadowPass
    ↓
DepthPrepass
    ↓
GBuffer
    ↓
Lighting
    ↓
Transparent
    ↓
PostProcess
    ↓
UI
    ↓
Present
```

---

# 72. Graph Compilation

The graph compiler performs:

1. dependency analysis;
2. cycle detection;
3. resource lifetime analysis;
4. transient aliasing;
5. queue assignment;
6. barrier generation;
7. synchronization generation;
8. pass ordering;
9. command recording plan.

---

# 73. Graph Cycles

A render graph containing an unresolved cycle MUST fail compilation.

Example:

```text
A → B → C → A
```

is invalid unless represented through an explicit multi-frame/history resource.

---

# 74. History Resources

Temporal rendering uses:

```text
HistoryResource
```

which explicitly crosses frame boundaries.

Examples:

```text
TAA history
motion history
temporal accumulation
```

This avoids falsely treating frame-to-frame dependencies as same-frame cycles.

---

# 75. Async Compute

A graph MAY schedule:

```text
Graphics
Compute
Transfer
```

concurrently.

The scheduler MUST only introduce synchronization where dependencies require it.

---

# 76. Pass Parallelism

Independent passes MAY be recorded concurrently by 607 workers.

Example:

```text
ShadowA ─┐
ShadowB ─┼→ Lighting
ShadowC ─┘
```

Each pass can have its own command encoder.

---

# 77. Command Recording Parallelism

The runtime supports:

```text
PrimaryCommandBuffer
SecondaryCommandBuffer
```

or equivalent backend abstraction.

Multiple workers can record independent command regions.

---

# 78. Software Renderer

615 defines:

```text
SoftwareGraphicsBackend
```

for:

- tests;
- CI;
- headless systems;
- unsupported hardware;
- deterministic screenshots.

It is not required to match GPU performance.

---

# 79. Deterministic Software Rendering

The test renderer SHOULD support:

```text
DeterministicRasterMode
```

with controlled:

- floating-point behavior;
- random seeds;
- texture sampling;
- timing;
- resource ordering.

This is useful for compiler/runtime regression tests.

---

# 80. Screenshot Capture

615 supports asynchronous:

```text
capture(surface)
capture(texture)
capture(frame)
```

The capture path uses:

```text
GPU → ReadbackBuffer → ImageEncoder
```

Image encoding itself belongs to the media/image layer.

---

# 81. Color Management

A display has a declared:

```text
ColorSpace
```

Examples:

```text
sRGB
DisplayP3
Rec709
Rec2020
scRGB
HDR10
```

The runtime MUST preserve color-space metadata through presentation.

---

# 82. Transfer Functions

Supported transfer functions can include:

```text
Linear
sRGB
PQ
HLG
```

Availability depends on backend/display.

---

# 83. HDR

HDR support exposes:

```text
HdrCapabilities
MaxLuminance
MinLuminance
ColorPrimaries
TransferFunction
MetadataSupport
```

Applications MUST NOT assume HDR output merely because a texture uses floating-point format.

---

# 84. ICC/EDID Boundary

Display calibration information such as:

```text
EDID
ICC
Display metadata
```

is exposed through the display backend.

Color-management engines above 615 can consume it.

615 does not implement a full professional color-management suite.

---

# 85. Window Composition

The OS compositor remains authoritative for ordinary desktop windows.

Axiom does not assume exclusive control of the physical display.

This allows:

```text
windowed
borderless
multi-window
mixed-DPI
HDR desktop
```

operation.

---

# 86. Protected Content

Protected surfaces/resources MAY be exposed:

```text
ProtectedMemory
ProtectedSurface
```

when the platform supports them.

CPU readback MUST be rejected when prohibited.

---

# 87. Multi-Window Rendering

One graphics device can service multiple:

```text
Window
Surface
Swapchain
```

objects.

Each surface has independent:

```text
Extent
Format
PresentMode
Frame pacing
```

---

# 88. Surface Recreation

A surface can become invalid after:

- resize;
- display change;
- fullscreen transition;
- device loss;
- OS compositor change.

The application receives:

```text
SurfaceInvalidated
```

and recreates the swapchain.

---

# 89. Swapchain Recreation

Swapchain generation increments:

```text
Generation += 1
```

Old backbuffers become invalid.

Command buffers referencing old backbuffers MUST NOT be submitted.

---

# 90. Device Lost

When GPU loss occurs:

```text
GPU work
   ↓
DeviceLost
   ↓
stop submissions
   ↓
diagnostics
   ↓
recreate device
   ↓
recreate reconstructible resources
   ↓
resume
```

---

# 91. Resource Reconstruction

Persistent graphics resources can declare:

```text
Reconstructible
NonReconstructible
External
```

Reconstructible resources may be recreated from package/content data.

Example:

```text
texture content hash
shader package ID
pipeline description
```

BOOTSTRAP-613 provides the content-addressed source.

---

# 92. External Resources

Resources originating from:

- native APIs;
- camera;
- video decoder;
- OS surfaces;
- imported GPU handles

are:

```text
ExternalResource
```

and require an explicit reconstruction strategy.

---

# 93. Resource Lifetime

Resources use deterministic lifetime:

```text
create
use
release
destroy
```

No tracing GC is involved.

Destruction MAY be deferred until GPU completion.

---

# 94. Deferred Destruction

Example:

```text
resource.destroy_after(fence)
```

The runtime retains the resource until:

```text
GPU completed fence
```

Then actual destruction occurs.

---

# 95. Resource Leak Detection

Debug mode records:

```text
ResourceId
CreationStack
Owner
CreationFrame
LastUseFrame
```

Leaks are reported through BOOTSTRAP-602.

Production builds MAY strip creation stacks.

---

# 96. GPU Queries

Core query types:

```text
Timestamp
Occlusion
PipelineStatistics
```

Availability is backend-dependent.

---

# 97. GPU Profiling

A GPU profiler can measure:

```text
GPU frame time
pass time
queue utilization
pipeline stalls
barrier cost
memory bandwidth
VRAM usage
```

Timing data is associated with frame IDs.

---

# 98. CPU/GPU Timeline

Diagnostics can display:

```text
CPU:
Frame 100 ────────────────┐
                          │
GPU:
        Shadow ─ Lighting ─ PostFX
                          │
Display:
                             Present
```

This is integrated with BOOTSTRAP-602 tracing.

---

# 99. Graphics Diagnostics

Events include:

```text
GraphicsDeviceCreated
GraphicsDeviceLost
SwapchainCreated
SwapchainRecreated
ShaderCompiled
PipelineCreated
PipelineCacheHit
PipelineCacheMiss
FrameSubmitted
FramePresented
GpuFault
ResourceAllocationFailure
```

---

# 100. Pipeline Cache

Pipeline keys are deterministic.

A key includes:

```text
ShaderHashes
PipelineLayoutHash
RenderFormats
DepthFormat
SampleCount
RasterState
BlendState
DeviceFeatureSet
DriverIdentity
BackendVersion
```

---

# 101. Pipeline Cache Storage

Pipeline cache may use BOOTSTRAP-613.

Example:

```text
.axcache/
    shaders/
    pipelines/
    layouts/
```

Cache artifacts MUST include:

```text
CompilerVersion
BackendVersion
DriverVersion
DeviceIdentity
```

to prevent unsafe incompatible reuse.

---

# 102. Shader Cache

Shader cache keys include:

```text
SourceHash
CompilerVersion
TargetBackend
FeatureSet
OptimizationLevel
```

Identical inputs produce reusable artifacts when deterministic compilation is enabled.

---

# 103. Package Integration

Graphics assets can be stored in AXPK:

```text
assets/
    shaders/
    textures/
    meshes/
    materials/
    pipelines/
    rendergraphs/
```

Package variants can be target-specific:

```text
shader.vulkan
shader.metal
shader.dx12
shader.webgpu
```

---

# 104. Graphics Manifest

A package can contain:

```text
graphics.axgfx
```

describing:

```text
Shaders
Pipelines
Textures
RequiredFeatures
Formats
TargetBackends
```

This metadata is AI-readable.

---

# 105. Resource Fingerprints

Every compiled graphics asset MAY expose:

```text
ContentHash
SchemaHash
CompilerHash
BackendHash
```

This allows incremental compilation and deterministic cache reuse.

---

# 106. Capability Negotiation

Graphics feature availability is queried:

```text
device.supports(Feature.RayTracing)
device.supports(Feature.MeshShaders)
device.supports(Feature.HdrOutput)
```

No backend feature is silently emulated unless explicitly declared.

---

# 107. Optional Backend Extensions

Applications may access backend-specific functionality:

```text
VulkanExtension
D3D12Extension
MetalExtension
WebGpuExtension
```

The extension boundary MUST be explicit.

Core code remains portable.

---

# 108. Native Handle Interop

615 allows controlled extraction:

```text
NativeWindowHandle
NativeSurfaceHandle
NativeDeviceHandle
NativeTextureHandle
NativeBufferHandle
```

Access requires the appropriate capability.

Raw handles MUST NOT bypass Axiom lifetime tracking.

---

# 109. FFI Graphics Interop

External native graphics libraries can import/export resources through:

```text
ExternalBuffer
ExternalTexture
ExternalFence
ExternalSemaphore
```

Ownership mode must be explicit:

```text
Borrowed
Owned
Transferred
```

---

# 110. Security

Graphics capabilities are integrated with 603.

Possible capabilities:

```text
graphics.use
graphics.create_surface
graphics.present
graphics.capture
graphics.protected
graphics.shader_execute
graphics.native_handle
```

A sandboxed application may have:

```text
graphics.headless
```

without permission to create desktop windows.

---

# 111. Shader Security Boundary

Shader execution does not automatically grant:

```text
filesystem
network
process
native-code
```

capabilities.

GPU shaders are isolated by the GPU execution model and backend validation.

---

# 112. Resource Quotas

BOOTSTRAP-606 tracks:

```text
GpuMemory
Buffers
Textures
Descriptors
Pipelines
CommandBuffers
FramesInFlight
ReadbackBytes
UploadBytes
```

Applications exceeding quotas receive typed resource errors.

---

# 113. Scheduler Integration

Graphics submission is integrated with 607.

The graphics runtime MUST NOT create an uncontrolled OS thread per window/device.

Possible worker model:

```text
Application Task
      ↓
Frame Task
      ↓
Command Recording Tasks
      ↓
Submission Task
```

---

# 114. Blocking Rules

GPU waits MUST NOT block general executor workers unnecessarily.

Instead:

```text
await fence
```

suspends the task.

---

# 115. Async GPU API

Example:

```text
await queue.wait(fence)
```

or:

```text
await texture.readback()
```

must lower to efficient async state machines.

No hidden blocking thread is required.

---

# 116. Synchronization Integration

Graphics synchronization uses BOOTSTRAP-608 primitives where appropriate.

CPU-side:

```text
Event
Semaphore
Atomic
Mutex
```

GPU-side:

```text
Fence
Timeline
Semaphore
```

The abstraction MUST prevent accidental confusion between CPU and GPU synchronization objects.

---

# 117. Memory Ordering

CPU writes to upload buffers must become visible to the GPU according to explicit backend synchronization rules.

Likewise:

```text
GPU → CPU
```

readback requires completion and appropriate visibility.

The runtime MUST NOT rely on undefined host/device cache behavior.

---

# 118. Resource State Validation

Debug mode validates:

```text
BufferUsage
TextureUsage
QueueOwnership
ResourceState
DescriptorType
PipelineCompatibility
DeviceGeneration
```

Invalid use produces deterministic diagnostics.

---

# 119. Simple Rendering API

For applications that do not need explicit GPU control:

```text
canvas.draw_rect(...)
canvas.draw_image(...)
canvas.draw_text(...)
```

may be provided by higher-level rendering libraries.

Those APIs eventually compile down to 615.

615 itself remains explicit and low-level.

---

# 120. Immediate Rendering Boundary

An optional convenience renderer may implement:

```text
begin_frame()
draw()
end_frame()
```

Internally it builds command buffers.

This does not make the underlying graphics model implicit.

---

# 121. GUI Integration Boundary

A future GUI toolkit can use:

```text
Window
Surface
Texture
RenderPass
CommandEncoder
```

for rendering.

GUI layout, widgets and input routing remain above 615.

---

# 122. Text Rendering Boundary

Text rendering is not part of 615.

A text engine can produce:

```text
GlyphAtlas
VertexBuffer
Texture
```

and submit them through the graphics runtime.

---

# 123. Image Rendering Boundary

Image/image-processing systems can use:

```text
Texture
ComputePipeline
RenderPass
Readback
```

without requiring a separate graphics abstraction.

---

# 124. Multi-GPU

A machine MAY expose multiple graphics adapters.

Applications can select:

```text
Integrated
Discrete
HighPerformance
LowPower
ExplicitAdapter(id)
```

Selection policy is explicit.

---

# 125. Cross-Adapter Resources

Cross-GPU resource sharing is optional.

When unsupported:

```text
copy through CPU
```

or:

```text
explicit peer-transfer
```

must be used.

No hidden cross-device copies are performed.

---

# 126. GPU Affinity

A resource is bound to:

```text
GraphicsDeviceId
DeviceGeneration
```

unless explicitly marked shared.

---

# 127. Memory Budget

Graphics memory uses the 606 governor.

Example:

```text
GpuBudget
├── persistent
├── transient
├── upload
├── readback
└── cache
```

Pressure events can trigger cache eviction.

---

# 128. Graphics Cache Eviction

Evictable:

```text
PipelineCache
ShaderCache
Transient allocations
Decoded texture cache
```

Non-evictable:

```text
actively referenced resource
persistent application resource
protected resource
```

---

# 129. Out-of-Memory Behavior

GPU OOM MUST NOT trigger arbitrary resource deletion.

Instead:

```text
GpuOutOfMemory
```

is returned.

Higher layers may choose:

```text
reduce quality
evict cache
reduce resolution
retry
terminate
```

---

# 130. Frame Failure

A frame may fail because of:

```text
SurfaceLost
DeviceLost
OutOfMemory
InvalidResource
PresentFailure
Timeout
CapabilityDenied
```

The error includes enough context for diagnostics.

---

# 131. Present Failure

Present errors are categorized:

```text
Retry
RecreateSwapchain
DeviceLost
Fatal
```

The application does not need backend-specific error parsing.

---

# 132. Display Hotplug

Display changes generate:

```text
DisplayAdded
DisplayRemoved
DisplayChanged
```

Affected windows receive:

```text
DisplayChanged
```

Applications may recreate swapchains or adapt DPI.

---

# 133. Monitor Selection

A window can query:

```text
window.monitor()
```

and:

```text
window.set_monitor(...)
```

where supported.

---

# 134. VSync and Latency

Frame scheduler exposes:

```text
target_frame_rate
max_frame_latency
present_mode
```

Applications can choose latency versus throughput explicitly.

---

# 135. Low-Latency Mode

When backend supports it:

```text
LowLatency
```

can reduce:

- frames in flight;
- driver queue depth;
- CPU/GPU latency.

It MUST NOT silently violate resource or synchronization guarantees.

---

# 136. Tearing

Tearing is permitted only when:

```text
PresentMode.Immediate
```

or equivalent backend support is explicitly selected.

---

# 137. Render Resolution

Logical window size and render resolution are independent.

Example:

```text
Window: 3840×2160
Render: 1920×1080
```

This enables:

- dynamic resolution;
- supersampling;
- performance scaling.

---

# 138. Viewport

A render pass supports:

```text
Viewport
Scissor
```

with floating-point viewport coordinates where backend permits.

---

# 139. Dynamic State

Optional dynamic pipeline state:

```text
Viewport
Scissor
BlendConstant
StencilReference
DepthBias
LineWidth
```

is capability-dependent.

---

# 140. Primitive Topology

Core:

```text
PointList
LineList
LineStrip
TriangleList
TriangleStrip
```

Optional:

```text
TriangleFan
PatchList
```

---

# 141. Indirect Rendering

Supports:

```text
draw_indirect
draw_indexed_indirect
dispatch_indirect
```

The command arguments can be produced by compute shaders.

This enables GPU-driven rendering.

---

# 142. GPU-Driven Rendering

Possible architecture:

```text
Compute
   ↓
Visibility
   ↓
IndirectBuffer
   ↓
GraphicsQueue
   ↓
DrawIndirect
```

No CPU round-trip is required.

---

# 143. Instancing

Core rendering supports:

```text
draw_instanced
draw_indexed_instanced
```

Instance data can be supplied through vertex buffers or shader storage resources.

---

# 144. Resource Arrays

Large scenes can use:

```text
TextureArray
BufferArray
BindlessArray
```

according to device capabilities.

---

# 145. Ray Tracing Boundary

Ray tracing is optional.

Core abstractions:

```text
AccelerationStructure
RayTracingPipeline
```

are enabled only when supported.

A future ray-tracing module may extend these definitions.

---

# 146. Mesh Shading Boundary

Mesh/task shaders are optional.

If unsupported, applications may use traditional vertex/fragment pipelines.

No automatic emulation is required.

---

# 147. Compute as First-Class Graphics Capability

Compute is not subordinate to rendering.

Axiom applications can use:

```text
GraphicsDevice
```

for:

- image processing;
- numerical computation;
- simulation;
- ML kernels;
- particle systems.

More general GPU compute/accelerator facilities may be extended by later runtime modules.

---

# 148. Command Validation

Debug builds validate command recording.

Examples:

```text
draw_without_pipeline
invalid_vertex_buffer
invalid_descriptor
wrong_device
wrong_generation
invalid_render_target
missing_barrier
```

---

# 149. Debug Labels

Resources and passes support:

```text
set_debug_name("ShadowMap")
push_debug_group("Lighting")
pop_debug_group()
```

These labels integrate with native graphics debuggers when possible.

---

# 150. GPU Markers

Optional:

```text
GpuMarker
GpuDebugGroup
GpuTimestamp
```

provide profiling information.

---

# 151. Validation Layers

615 supports:

```text
Disabled
Basic
Full
BackendValidation
```

Backend validation is development-only and MUST NOT be required for production execution.

---

# 152. Error Model

Graphics errors are typed:

```text
GraphicsError =
    InvalidArgument
    UnsupportedFeature
    InvalidState
    ResourceStateConflict
    OutOfMemory
    DeviceLost
    SurfaceLost
    PresentFailed
    ShaderCompileFailed
    PipelineCompileFailed
    CapabilityDenied
    Timeout
    BackendFailure
```

---

# 153. No String-Based Errors

Machine handling uses typed error codes.

Human-readable messages are diagnostic metadata.

---

# 154. Compiler Integration

The compiler understands graphics-specific metadata:

```text
@gpu_shader
@gpu_resource
@gpu_pipeline
@gpu_format
@gpu_feature
```

This permits compile-time validation.

---

# 155. Example Shader Declaration

Conceptually:

```text
@gpu_shader(stage = vertex)
fn vertex_main(input: VertexInput) -> VertexOutput {
    ...
}
```

The compiler emits shader metadata.

---

# 156. Compile-Time Resource Validation

The compiler can detect:

```text
shader expects binding 3
pipeline provides binding 2
```

before runtime.

---

# 157. Dead Stripping

If an application never uses:

```text
HDR
ray tracing
Vulkan
Metal
software renderer
```

their corresponding runtime code SHOULD be removable.

---

# 158. Backend Selection

Possible compile/runtime configuration:

```text
backend = Auto
backend = Vulkan
backend = D3D12
backend = Metal
backend = WebGPU
backend = Software
```

`Auto` selects according to platform policy.

---

# 159. Backend Priority

Axiom MUST NOT hard-code a universal backend priority.

Platform profiles define defaults.

Example:

```text
Windows → D3D12/Vulkan
Linux → Vulkan
macOS → Metal
iOS → Metal
Web → WebGPU
```

The exact runtime selection remains configurable.

---

# 160. Vulkan Boundary

Vulkan backend maps:

```text
GraphicsDevice
GpuQueue
Buffer
Texture
Pipeline
DescriptorSet
CommandBuffer
Fence
Semaphore
Surface
Swapchain
```

to native Vulkan objects.

---

# 161. D3D12 Boundary

D3D12 backend maps:

```text
ID3D12Device
CommandQueue
CommandAllocator
GraphicsCommandList
Resource
DescriptorHeap
Fence
SwapChain
```

into Axiom abstractions.

---

# 162. Metal Boundary

Metal backend maps:

```text
MTLDevice
MTLCommandQueue
MTLCommandBuffer
MTLTexture
MTLBuffer
MTLRenderPipelineState
MTLComputePipelineState
CAMetalLayer
```

into Axiom abstractions.

---

# 163. WebGPU Boundary

WebGPU backend maps:

```text
GPUAdapter
GPUDevice
GPUQueue
GPUBuffer
GPUTexture
GPURenderPipeline
GPUComputePipeline
GPUCanvasContext
```

into the same high-level model.

---

# 164. Embedded Boundary

Embedded platforms may expose:

```text
Framebuffer
DisplayController
DMA2D
GPU
```

with only the supported subset.

---

# 165. Backend Capability Matrix

Each backend exposes:

```text
FeatureSet
```

rather than a collection of compile-time assumptions.

---

# 166. Graphics API Version

The public Axiom graphics API has:

```text
GraphicsApiVersion
```

separate from:

```text
BackendApiVersion
DriverVersion
ShaderModelVersion
```

This allows stable Axiom APIs while backend implementations evolve.

---

# 167. ABI Stability

Opaque graphics handles SHOULD use stable ABI layouts.

Internal backend structures remain private.

FFI receives:

```text
opaque handle
```

rather than backend struct layouts.

---

# 168. Thread Safety

Objects explicitly declare:

```text
ThreadSafe
ThreadAffine
ExternallySynchronized
```

Command encoders are generally thread-confined.

Immutable resources are generally safe for concurrent read access.

---

# 169. Command Encoder Ownership

One encoder MUST NOT be mutated concurrently by multiple threads.

Parallel recording uses multiple encoders.

---

# 170. Render Graph Ownership

A render graph can be constructed by one owner and compiled into an immutable:

```text
CompiledRenderGraph
```

which can then be executed concurrently where backend rules allow.

---

# 171. Frame Context

A frame has:

```text
FrameContext
```

containing:

```text
FrameId
TransientAllocator
DescriptorPool
CommandPools
UploadAllocator
ReadbackAllocator
FrameFence
```

Frame context is recycled only after GPU completion.

---

# 172. Frame-local Allocation

Simple temporary graphics data can use:

```text
frame.alloc<T>()
```

which is reclaimed automatically at frame completion.

This is an arena, not garbage collection.

---

# 173. Persistent Allocation

Long-lived objects use explicit ownership:

```text
Texture
Buffer
Pipeline
Sampler
```

No hidden frame ownership.

---

# 174. Resource Naming

Every debug build resource MAY have:

```text
ResourceName
```

Names are UTF-8.

---

# 175. Graphics State Snapshot

The runtime can export a diagnostic snapshot:

```text
GraphicsSnapshot
```

containing:

```text
Device
Memory
Resources
Queues
Swapchains
Frames
Pipelines
Shaders
FeatureSet
```

Sensitive data is excluded.

---

# 176. Crash Diagnostics

On GPU/device failure, BOOTSTRAP-602 receives:

```text
DeviceIdentity
DriverVersion
DeviceGeneration
LastSubmittedFrame
LastCompletedFrame
ActivePass
ResourceSummary
MemoryBudget
```

Where supported, backend-specific GPU crash diagnostics are attached.

---

# 177. Security and Diagnostics Boundary

Shader source, resource names or debug labels MUST NOT accidentally expose secrets.

Applications can mark:

```text
@sensitive
```

for diagnostics redaction.

---

# 178. Configuration Integration

BOOTSTRAP-601 may configure:

```text
graphics.backend
graphics.validation
graphics.vsync
graphics.frames_in_flight
graphics.shader_cache
graphics.pipeline_cache
graphics.gpu_memory_budget
graphics.debug_markers
```

Configuration changes affecting device creation require explicit graphics-context recreation.

---

# 179. State Integration

BOOTSTRAP-600 can checkpoint:

```text
graphics configuration
render graph description
resource content hashes
pipeline identities
```

but NOT:

```text
live GPU command queues
live swapchain handles
live native windows
GPU synchronization state
```

Those are reconstructed.

---

# 180. Package Recovery

After restart:

```text
AXPK
 ↓
shader cache
 ↓
resource reconstruction
 ↓
pipeline creation
 ↓
window/surface creation
 ↓
render graph
```

This makes graphics restartable without serializing raw GPU state.

---

# 181. Supervisor Integration

BOOTSTRAP-605 can supervise rendering services.

Examples:

```text
RendererService
HeadlessRendererService
VisualizationService
```

A renderer crash does not necessarily imply application-wide state loss.

---

# 182. IPC Integration

Graphics resources can be transferred through explicit external-resource handles where OS/backend supports it.

Examples:

```text
SharedTexture
SharedBuffer
SharedFence
```

Transfer requires 603 capabilities.

---

# 183. Cross-Process Rendering

Possible model:

```text
Application
   │
   │ IPC
   ▼
Renderer Process
   │
   ▼
GPU
```

The renderer process receives only delegated graphics capabilities.

---

# 184. Remote Rendering Boundary

Network transport is intentionally outside 615.

A remote renderer can use:

```text
609 Networking
604 IPC
612 Serialization
613 Package
615 Graphics
```

without changing the graphics API.

---

# 185. Testing Architecture

Required backends:

```text
NullGraphicsBackend
SoftwareGraphicsBackend
FakeGpuBackend
```

at minimum for automated tests.

---

# 186. Null Graphics Backend

The null backend validates:

- resource creation;
- pipeline compatibility;
- command recording;
- graph dependencies;
- synchronization;
- lifecycle.

It performs no actual rendering.

---

# 187. Fake GPU

The fake GPU can simulate:

```text
device lost
out of memory
slow queue
stalled fence
surface invalidation
unsupported feature
```

for deterministic failure testing.

---

# 188. Golden Image Testing

Rendering tests can compare:

```text
ExpectedImage
ActualImage
```

with configurable tolerances.

The tolerance model must distinguish:

```text
exact
integer tolerance
floating-point tolerance
perceptual tolerance
```

---

# 189. Shader Tests

Every shader compiler backend should have:

- parser tests;
- type tests;
- reflection tests;
- validation tests;
- cross-backend tests;
- optimization tests;
- deterministic output tests.

---

# 190. Render Graph Tests

Required:

```text
dependency ordering
cycle detection
barrier generation
resource aliasing
queue synchronization
history resources
parallel recording
```

---

# 191. Device-Loss Tests

Simulate:

```text
loss during submission
loss during frame
loss during pipeline creation
loss during readback
loss during presentation
```

Expected behavior must be deterministic.

---

# 192. Window Tests

Test:

```text
resize
DPI change
monitor migration
fullscreen
minimize
restore
close
surface invalidation
display hotplug
```

---

# 193. Performance Tests

Measure:

```text
command recording time
submission latency
CPU frame overhead
GPU frame time
descriptor allocation
pipeline cache hit rate
shader compilation
resource creation
render graph compilation
```

---

# 194. Performance Targets

Typical target values for a production backend:

```text
Command recording:
low microsecond-scale overhead per simple command group

Task scheduling:
near-native 607 overhead

Resource lookup:
O(1) handle lookup

Pipeline cache lookup:
O(1) average

Render graph compilation:
O(P + R + E)
```

where:

```text
P = passes
R = resources
E = dependency edges
```

---

# 195. No Global Graphics Lock

The graphics runtime MUST NOT require one global mutex around:

```text
resource creation
command recording
render graph construction
frame submission
```

Backend-specific serialization may exist only where required.

---

# 196. Lock-Free/Low-Lock Hot Paths

Hot paths should use:

```text
atomic counters
thread-local pools
per-frame allocators
per-worker command pools
```

instead of global locks.

---

# 197. Deterministic Command Recording

For identical:

```text
input
device feature set
shader versions
resource versions
```

the logical command stream SHOULD be deterministic.

Backend-native binary command buffers are not required to be byte-identical.

---

# 198. Resource IDs

Graphics resources use generational IDs:

```text
ResourceId = {
    index,
    generation,
    device_generation
}
```

Stale handles are rejected.

---

# 199. No Raw GPU Pointers

The public Axiom API MUST NOT expose GPU pointers.

GPU addresses may exist internally or through an explicitly unsafe backend extension.

---

# 200. Unsafe Graphics Extensions

An `unsafe` extension can expose:

```text
native GPU address
native descriptor handle
backend command buffer
```

but must require explicit unsafe code.

Unsafe access does not automatically grant security capabilities.

---

# 201. AI-Friendly Metadata

Graphics APIs produce machine-readable metadata:

```text
graphics.schema
shader.schema
pipeline.schema
rendergraph.schema
```

The metadata describes:

```text
resource dependencies
pipeline inputs
shader bindings
feature requirements
formats
```

This is designed for Axiom tooling and AI agents.

---

# 202. Graphics Inspection CLI

Future compiler tooling supports:

```text
axiom gfx inspect app.ax
axiom gfx inspect-shader shader.axsl
axiom gfx inspect-pipeline pipeline.axpipe
axiom gfx inspect-graph graph.axrg
axiom gfx cache stats
```

---

# 203. Render Graph File

A serialized render graph can use:

```text
.axrg
```

containing:

```text
resources
passes
dependencies
formats
features
queue preferences
```

---

# 204. Pipeline File

Compiled pipeline descriptions can use:

```text
.axpipe
```

including:

```text
shader hashes
layout
render formats
state
feature requirements
```

---

# 205. Shader File

Source:

```text
.axsl
```

Compiled artifacts can contain:

```text
AXSL-IR
reflection
backend binaries
debug information
source hash
compiler hash
```

---

# 206. Resource Versioning

Every serialized graphics asset has:

```text
FormatVersion
SchemaVersion
CompilerVersion
```

Unknown mandatory fields cause explicit incompatibility rather than silent corruption.

---

# 207. Compatibility

A newer runtime may load an older graphics asset if the compatibility rules permit it.

An older runtime MUST reject unsupported future formats safely.

---

# 208. Deterministic Package Builds

Graphics packages normalize:

```text
resource ordering
metadata ordering
timestamps
floating-point serialization
shader metadata
```

where reproducibility is requested.

---

# 209. Build Pipeline

Typical:

```text
Source
 ↓
Axiom Compiler
 ↓
AXSL compiler
 ↓
Graphics Asset Compiler
 ↓
RenderGraph compiler
 ↓
AXPK
 ↓
Application binary
```

---

# 210. Native Application Build

Final executable can contain:

```text
Axiom runtime
graphics backend
shaders
pipelines
resources
```

Only required components should be linked.

---

# 211. Static Linking

For native static builds:

```text
Application
 + Graphics Core
 + Selected Backend
 + Selected Features
```

unused backends are dead-stripped.

---

# 212. Dynamic Backend Loading

Axiom MAY optionally load a backend dynamically:

```text
graphics-vulkan
graphics-d3d12
graphics-metal
```

This is a deployment choice, not a core requirement.

---

# 213. Backend Discovery

Dynamic loading must pass 603 trust/security policy.

Untrusted graphics backend code MUST NOT be loaded automatically.

---

# 214. Driver Boundary

Axiom does not replace the operating system's GPU driver.

The supported stack is:

```text
Axiom
 ↓
Graphics Backend
 ↓
OS API
 ↓
GPU Driver
 ↓
GPU
```

---

# 215. No Mandatory Third-Party Runtime

The Axiom graphics abstraction itself must not depend on:

```text
SDL
GLFW
Qt
Electron
```

or similar frameworks.

Platform adapters are native.

---

# 216. OpenGL Boundary

OpenGL may be supported as an optional compatibility backend.

It MUST NOT define the architecture.

The core design remains modern explicit graphics.

---

# 217. Web Rendering

On WASM:

```text
Axiom Graphics
 ↓
WebGPU
 ↓
Browser
 ↓
GPU
```

If WebGPU is unavailable, software rendering may be used where practical.

---

# 218. Mobile Rendering

Android/iOS rendering must account for:

```text
app suspension
surface recreation
backgrounding
foregrounding
thermal pressure
memory pressure
device loss
```

The graphics runtime integrates with 605/606.

---

# 219. Thermal Pressure

When 614 reports thermal pressure, the renderer can expose:

```text
ThermalLevel
```

Higher layers can reduce:

```text
resolution
frame rate
quality
GPU workload
```

615 itself does not silently change visual quality.

---

# 220. Power Profiles

Graphics applications can request:

```text
LowPower
Balanced
HighPerformance
```

subject to platform/security policy.

The OS remains authoritative.

---

# 221. Protected Windows

Some platforms support protected content windows.

Axiom exposes:

```text
WindowProtection
```

only when the backend supports it.

---

# 222. Screen Capture

Screen capture is explicitly capability-controlled.

Capabilities:

```text
graphics.capture_window
graphics.capture_display
graphics.capture_surface
```

No application receives unrestricted desktop capture by default.

---

# 223. Cursor Integration

615 may provide the basic native cursor surface:

```text
Window.set_cursor(...)
```

but advanced input remains under 614/input layers.

---

# 224. Clipboard Rendering

Clipboard image transfer is outside the core graphics runtime.

Graphics can convert to/from image buffers for higher-level clipboard services.

---

# 225. Accessibility Boundary

Accessibility APIs are not implemented by 615.

GUI systems above it provide semantic UI trees.

---

# 226. Remote Desktop

Graphics presentation must tolerate OS-level remote display/compositor behavior.

Applications may query reduced feature availability.

---

# 227. Virtual GPU

VM environments may expose:

```text
VirtualGpu
```

as ordinary 614 devices.

615 does not special-case them except for capability reporting.

---

# 228. Containerized Rendering

Headless rendering can operate in containers where the host provides the graphics device.

Security capabilities determine device access.

---

# 229. Server Rendering

A server can run:

```text
GraphicsContext
HeadlessSurface
SoftwareBackend
```

without a desktop environment.

---

# 230. Offscreen Composition

An application can compose:

```text
Texture A
Texture B
Texture C
 ↓
RenderTarget
```

without presentation.

This is fundamental for:

- video;
- thumbnails;
- image generation;
- UI snapshots;
- testing.

---

# 231. Multiple Render Targets

MRT is supported:

```text
Color0
Color1
Color2
Color3
...
```

subject to hardware limits.

---

# 232. Depth/Stencil

Depth and stencil are independent logical concepts even when stored together.

The API supports:

```text
DepthRead
DepthWrite
StencilRead
StencilWrite
```

---

# 233. Blending

Blend state:

```text
SourceFactor
DestinationFactor
SourceAlphaFactor
DestinationAlphaFactor
BlendOperation
WriteMask
```

is pipeline state or dynamic state depending on backend.

---

# 234. Raster State

Includes:

```text
CullMode
FrontFace
FillMode
DepthBias
DepthClamp
ConservativeRasterization
```

where supported.

---

# 235. Depth State

Includes:

```text
DepthTest
DepthWrite
CompareOperation
```

---

# 236. Stencil State

Includes:

```text
StencilTest
ReadMask
WriteMask
FrontOperation
BackOperation
```

---

# 237. Blend Attachments

Each color target can have independent blend state.

---

# 238. Vertex Layout

A vertex buffer layout contains:

```text
Binding
Stride
InputRate
```

attributes:

```text
Location
Format
Offset
```

---

# 239. Index Formats

Core:

```text
UInt16
UInt32
```

Optional:

```text
UInt8
```

if supported.

---

# 240. Push Descriptor / Fast Binding

Backends supporting low-overhead descriptor updates may use:

```text
FastBind
```

without exposing backend-specific implementation details.

---

# 241. Resource Binding Validation

At pipeline creation:

```text
shader bindings
        ↕
pipeline layout
        ↕
descriptor sets
```

must be compatible.

---

# 242. Dynamic Uniform Data

Frame-local uniform data should use:

```text
RingBuffer
UploadArena
```

rather than individual heap allocations.

---

# 243. Constant Buffer Alignment

Backend-required alignment is queried:

```text
min_uniform_alignment
```

The allocator automatically respects it.

---

# 244. Large Buffer Streaming

Streaming systems can use:

```text
PersistentMappedBuffer
RingBuffer
StagingBuffer
```

where supported.

---

# 245. Texture Streaming

Large texture systems may use:

```text
partial mip upload
async upload
sparse residency
```

where backend capabilities allow.

---

# 246. Virtual Texturing Boundary

Virtual texturing can build above:

```text
Texture
TextureView
CopyPass
ComputePass
```

No dedicated virtual-texture abstraction is mandatory in 615.

---

# 247. Resource Residency

When the backend supports residency control, resources may have:

```text
Resident
NonResident
Pending
```

State.

---

# 248. Residency Budget

Residency is integrated with 606 GPU memory budgets.

---

# 249. Command Reuse

Immutable command buffers MAY be reused if:

```text
resource lifetimes
swapchain generation
device generation
```

remain valid.

---

# 250. Secondary Command Reuse

Static scene command regions can be reused across frames.

Dynamic resources remain separately bound.

---

# 251. Pipeline Warmup

Applications may precompile pipelines:

```text
pipeline_cache.prewarm(...)
```

to avoid runtime frame stalls.

---

# 252. Runtime Pipeline Creation

If a pipeline is missing:

```text
PipelinePending
```

MAY be returned.

Higher-level renderers decide whether to:

```text
wait
fallback
skip
compile asynchronously
```

---

# 253. Shader Hot Reload

Development mode can support:

```text
shader.watch()
```

through 611 file watching.

The runtime safely replaces pipelines after GPU completion.

---

# 254. Hot Reload Safety

Old pipeline resources remain alive until no submitted command references them.

---

# 255. Material Boundary

A future material system can contain:

```text
Shader
Textures
Samplers
Parameters
```

and compile to 615 descriptors/pipelines.

---

# 256. Scene Boundary

A future scene renderer builds:

```text
Scene
 ↓
Visibility
 ↓
RenderGraph
 ↓
615
```

---

# 257. GUI Boundary

A future GUI renderer builds:

```text
WidgetTree
 ↓
Layout
 ↓
DrawCommands
 ↓
615
```

---

# 258. Compute/ML Boundary

A future tensor/GPU runtime can reuse:

```text
Buffer
ComputePipeline
DescriptorSet
CommandBuffer
GpuQueue
```

instead of creating a second GPU runtime.

---

# 259. Interop with BOOTSTRAP-614

614 owns:

```text
Device discovery
Device identity
Physical resources
GPU memory
DMA
Device reset
Peripheral access
```

615 owns:

```text
Graphics semantics
Presentation
Rendering
Shaders
Pipelines
Command recording
Render graph
```

This boundary MUST remain explicit.

---

# 260. Interop with BOOTSTRAP-610

610 supplies:

```text
Hash
Signature
Secure random
Key storage
Trust
```

615 uses these for:

```text
shader/package verification
pipeline artifact integrity
trusted graphics packages
```

---

# 261. Interop with BOOTSTRAP-612

612 supplies:

```text
AXBIN
schema
serialization
persistent metadata
```

615 uses it for:

```text
graphics metadata
render graph serialization
pipeline descriptions
shader reflection
```

---

# 262. Interop with BOOTSTRAP-613

613 supplies:

```text
AXPK
compression
content addressing
cache
resource packaging
```

615 uses it for:

```text
shader packages
texture packages
pipeline cache
render assets
```

---

# 263. Interop with BOOTSTRAP-611

611 supplies:

```text
file IO
memory mapping
file watching
durability
```

615 uses it for:

```text
shader hot reload
cache persistence
asset loading
capture output
```

---

# 264. Interop with BOOTSTRAP-606

606 accounts:

```text
GPU memory
resource count
queue usage
upload/readback bandwidth
```

615 provides the resource accounting hooks.

---

# 265. Interop with BOOTSTRAP-607

607 provides:

```text
worker execution
async tasks
timers
cancellation
thread affinity
```

615 builds frame and command execution on top.

---

# 266. Interop with BOOTSTRAP-608

608 provides:

```text
atomic operations
CPU synchronization
wait/notify
lock-free queues
```

615 uses these for CPU/GPU coordination.

---

# 267. Interop with BOOTSTRAP-605

605 manages:

```text
renderer service lifecycle
restart
health
watchdog
```

615 exposes renderer health state.

---

# 268. Health Model

Graphics health:

```text
Healthy
Degraded
DeviceLost
Recovering
Unavailable
```

---

# 269. Renderer Recovery

Recovery should preserve:

```text
application state
asset identity
render graph description
pipeline descriptions
```

while recreating:

```text
GPU resources
swapchains
command pools
queues
```

---

# 270. Recovery Event

Applications receive:

```text
GraphicsRecoveryEvent
```

such as:

```text
DeviceLost
RecoveryStarted
ResourcesRecreated
RecoveryCompleted
RecoveryFailed
```

---

# 271. Recovery Failure

If recovery fails:

```text
GraphicsUnavailable
```

is returned.

The application can switch to:

```text
SoftwareBackend
```

if configured.

---

# 272. Backend Fallback

Fallback policy is explicit:

```text
GPU → alternate GPU → software
```

No silent backend switching during an active frame unless the application explicitly enables recovery policy.

---

# 273. Render Graph Cache

Compiled graphs can be cached using:

```text
GraphHash
DeviceFeatureSet
BackendVersion
```

---

# 274. Graph Hash

The hash includes:

```text
passes
resource declarations
dependencies
formats
features
queue requirements
```

but excludes runtime handles.

---

# 275. Graph Reuse

A compiled graph can be reused when:

```text
GraphHash unchanged
Device generation compatible
Feature set compatible
```

---

# 276. Runtime Specialization

A graph may specialize for:

```text
resolution
MSAA
HDR
quality level
feature set
```

Each specialization gets its own key.

---

# 277. Quality Scaling

615 exposes capabilities but does not choose image-quality policies.

Higher renderers can select:

```text
Low
Medium
High
Ultra
```

using explicit application policy.

---

# 278. Resource Aliasing Safety

Two transient resources can alias only when their GPU lifetimes do not overlap.

The graph compiler must prove this before aliasing.

---

# 279. Barrier Minimization

The graph compiler should merge compatible transitions where safe.

It MUST NOT remove barriers solely for performance if doing so violates memory visibility.

---

# 280. Submission Batching

Independent command buffers MAY be batched into one queue submission.

Batching must preserve:

```text
dependency order
waits
signals
```

---

# 281. Queue Family Selection

The runtime selects queues based on:

```text
required capability
load
resource ownership
latency
```

The selection is deterministic under a deterministic scheduling profile.

---

# 282. Async Transfer

Texture/buffer uploads can run on transfer queues when available.

This allows:

```text
render queue
+
transfer queue
```

concurrency.

---

# 283. Upload Scheduling

Large uploads are chunked according to:

```text
upload budget
frame budget
resource priority
```

so one upload cannot monopolize the GPU.

---

# 284. Readback Scheduling

Readback can be throttled using 606 budgets.

---

# 285. GPU Timeout

Backend timeout events become:

```text
GpuTimeout
```

and are reported to 602.

The runtime MUST distinguish timeout from ordinary frame latency.

---

# 286. Long GPU Work

Applications performing long compute jobs should use:

```text
ComputeQueue
```

rather than blocking graphics presentation.

---

# 287. Presentation Isolation

Presentation operations are isolated from general compute workloads when the platform provides independent queues.

---

# 288. Multi-Queue Diagnostics

Diagnostics records:

```text
QueueId
SubmissionId
FenceValue
FrameId
```

for each submission.

---

# 289. Submission IDs

Each queue submission receives:

```text
SubmissionId
```

monotonically increasing within the device generation.

---

# 290. Command IDs

Debug command groups may receive:

```text
CommandId
```

for diagnostics.

---

# 291. Frame IDs

Frames use:

```text
FrameId
```

monotonically increasing within an application session.

---

# 292. Present IDs

Present operations use:

```text
PresentId
```

for latency tracking.

---

# 293. Latency Metrics

The runtime can expose:

```text
CPUStart
CPUSubmit
GPUStart
GPUFinish
PresentQueued
PresentComplete
```

when supported.

---

# 294. Frame Capture

A debug capture can include:

```text
FrameId
CommandBuffers
Resources
Shaders
Pipelines
RenderGraph
DeviceInfo
```

Sensitive resources are redacted where required.

---

# 295. Capture Replay

A capture can be replayed on the same backend when compatible.

Cross-backend replay is not guaranteed.

---

# 296. Reproducibility

A deterministic graphics test profile freezes:

```text
resource ordering
graph ordering
shader compiler mode
random seed
software renderer
timing source
```

---

# 297. Testing Matrix

Minimum backend test matrix:

```text
Null
Software
One native GPU backend
```

CI can add all available native backends.

---

# 298. Fuzzing

Fuzz:

```text
shader parser
shader IR
pipeline descriptions
render graph
serialized graphics metadata
resource descriptors
command streams
```

---

# 299. Security Fuzzing

Particular focus:

```text
shader resource indexing
descriptor validation
package shader loading
native handle import
external memory
cross-process resource transfer
```

---

# 300. Fault Injection

Inject:

```text
OOM
device loss
surface loss
shader failure
pipeline failure
queue timeout
driver error
display removal
window destruction
```

---

# 301. Acceptance Criteria — Windowing

1. Native window creation works.
2. Window destruction is deterministic.
3. Resize events are delivered.
4. DPI changes are delivered.
5. Multi-monitor movement works.
6. Fullscreen state is explicit.
7. Surface invalidation is detectable.
8. Headless surfaces work.
9. Thread affinity is enforced.
10. Window lifecycle integrates with 607.

---

# 302. Acceptance Criteria — Display

11. Displays enumerate.
12. Modes enumerate.
13. Rational refresh rates are preserved.
14. DPI is reported.
15. HDR capabilities are queryable.
16. Color spaces are queryable.
17. Display hotplug is handled.
18. Monitor assignment is queryable.
19. Present modes are queryable.
20. Tearing policy is explicit.

---

# 303. Acceptance Criteria — Resources

21. Buffers work.
22. Textures work.
23. Views work.
24. Samplers work.
25. Render targets work.
26. Depth/stencil works.
27. MSAA works when supported.
28. Resource usage is validated.
29. Device generation is checked.
30. Stale handles are rejected.

---

# 304. Acceptance Criteria — Commands

31. Command encoders work.
32. Command buffers are immutable.
33. Render passes work.
34. Compute passes work.
35. Copy passes work.
36. Indirect commands work.
37. Resource barriers work.
38. Parallel recording works.
39. Submission is asynchronous.
40. Queue synchronization works.

---

# 305. Acceptance Criteria — Shaders

41. AXSL parses.
42. AXSL type checking works.
43. AXSL-IR is generated.
44. Reflection metadata is generated.
45. Resource bindings are validated.
46. Shader limits are enforced.
47. Backend compilation works.
48. Shader cache works.
49. Deterministic shader builds work.
50. Shader errors are typed.

---

# 306. Acceptance Criteria — Pipelines

51. Graphics pipelines compile.
52. Compute pipelines compile.
53. Pipeline layout is validated.
54. Pipeline cache works.
55. Pipeline keys are deterministic.
56. Pipeline warmup works.
57. Async pipeline compilation works.
58. Hot reload is safe.
59. Invalid pipelines are rejected.
60. Backend feature requirements are enforced.

---

# 307. Acceptance Criteria — Render Graph

61. Resources can be declared.
62. Passes can be declared.
63. Dependencies are computed.
64. Cycles are detected.
65. Barriers are generated.
66. Transient aliasing is safe.
67. Queue assignment works.
68. Async compute works.
69. History resources work.
70. Graph caching works.

---

# 308. Acceptance Criteria — Presentation

71. Swapchains work.
72. Acquire works.
73. Present works.
74. Present modes are honored where supported.
75. Swapchain recreation works.
76. Frame IDs are tracked.
77. Present IDs are tracked.
78. Frame pacing works.
79. Max frames in flight is enforced.
80. Present errors are typed.

---

# 309. Acceptance Criteria — Recovery

81. Device loss is detected.
82. New submissions stop after loss.
83. Diagnostics capture device state.
84. Recoverable resources are identified.
85. Device recreation works where platform permits.
86. Resources can be reconstructed.
87. Swapchains can be recreated.
88. Failed recovery is reported.
89. Software fallback can be selected.
90. Stale resources cannot cross generations.

---

# 310. Acceptance Criteria — Memory

91. GPU budgets are enforced.
92. Upload pools work.
93. Readback pools work.
94. Transient allocations work.
95. Descriptor pools work.
96. Resource aliasing works.
97. OOM is typed.
98. Evictable caches can be reclaimed.
99. Deferred destruction works.
100. Resource leaks are diagnosable.

---

# 311. Acceptance Criteria — Diagnostics

101. GPU timings are exposed.
102. CPU/GPU correlation works.
103. Queue submissions are traceable.
104. Pipeline cache statistics exist.
105. Memory statistics exist.
106. Device loss diagnostics exist.
107. Resource names are visible in debug mode.
108. GPU markers work where supported.
109. Capture metadata is generated.
110. Sensitive metadata can be redacted.

---

# 312. Acceptance Criteria — Security

111. Graphics capabilities are enforced.
112. Screen capture is permission-controlled.
113. Native handles require explicit capability.
114. Protected resources cannot be read back illegally.
115. Shader validation prevents invalid access.
116. Untrusted backend loading is blocked.
117. Cross-process resource transfer is authorized.
118. Security failures are typed.
119. Diagnostics do not leak secrets.
120. `unsafe` does not bypass capability policy.

---

# 313. Acceptance Criteria — Integration

121. 607 executor integration works.
122. 608 synchronization integration works.
123. 606 resource accounting works.
124. 603 capability checks work.
125. 602 diagnostics work.
126. 605 supervision works.
127. 611 file/cache integration works.
128. 612 serialization integration works.
129. 613 package integration works.
130. 614 device integration works.

---

# 314. Acceptance Criteria — Toolchain

131. Graphics metadata is compiler-readable.
132. AXSL artifacts are deterministic.
133. Pipeline metadata is inspectable.
134. Render graphs are inspectable.
135. Graphics caches are versioned.
136. Backend artifacts identify their device/compiler requirements.
137. Dead stripping removes unused graphics components.
138. Static linking works.
139. FFI interop works.
140. ABI remains opaque and stable.

---

# 315. Acceptance Criteria — Cross Platform

141. Windows backend can create windows.
142. Linux backend can create surfaces.
143. macOS backend can use Metal.
144. iOS backend can render to native surfaces.
145. Android backend can render to native surfaces.
146. WASM backend can render through WebGPU where available.
147. Embedded framebuffer backend is possible.
148. Software rendering works without GPU.
149. Headless rendering works.
150. Backend feature differences are exposed explicitly.

---

# 316. Core Invariants

### Invariant 1 — Device ownership

Every GPU resource belongs to exactly one device generation unless explicitly external/shared.

### Invariant 2 — No stale resource use

A resource from a previous device generation cannot be submitted.

### Invariant 3 — Explicit synchronization

GPU visibility and ordering cannot depend on accidental host behavior.

### Invariant 4 — No hidden global GPU stalls

Normal rendering cannot implicitly wait for the entire GPU.

### Invariant 5 — Deterministic lifetime

Every resource has an explicit ownership/lifetime model.

### Invariant 6 — Capability boundary

Window creation, presentation, capture and native-handle access are capability-controlled.

### Invariant 7 — Backend independence

The Axiom API is not defined by any one graphics backend.

### Invariant 8 — Feature explicitness

Unsupported features are reported rather than silently approximated.

### Invariant 9 — Recoverability

Reconstructible graphics resources can be recreated after device loss.

### Invariant 10 — No language GC dependency

Graphics resource reclamation does not depend on garbage collection.

---

# 317. Struct-Only API Shape

Consistent with Axiom's struct-oriented design:

```text
struct GraphicsContext { ... }

fn GraphicsContext.create(config: GraphicsConfig)
    -> Result<GraphicsContext>

fn GraphicsContext.create_window(
    self,
    config: WindowConfig
) -> Result<Window>

fn GraphicsContext.create_texture(
    self,
    desc: TextureDesc
) -> Result<Texture>

fn GraphicsDevice.create_pipeline(
    self,
    desc: GraphicsPipelineDesc
) -> Result<GraphicsPipeline>

fn CommandEncoder.begin_render_pass(
    self,
    desc: RenderPassDesc
) -> RenderPass

fn RenderPass.draw(
    self,
    vertices: DrawRange
)

fn GpuQueue.submit(
    self,
    commands: CommandBuffer,
    waits: WaitSet,
    signals: SignalSet
) -> Result<SubmissionId>
```

No class hierarchy is required.

---

# 318. Example — Minimal Application

Conceptually:

```text
fn main() {
    gfx = Graphics.create_default()

    window = gfx.create_window(
        title = "Axiom",
        width = 1280,
        height = 720
    )

    while window.is_open() {
        frame = gfx.begin_frame(window)

        frame.clear(
            color = Color(0.05, 0.05, 0.08, 1.0)
        )

        frame.present()
    }
}
```

The simple path hides explicit synchronization while still using the underlying 615 architecture.

---

# 319. Example — Explicit Rendering

```text
encoder = device.create_command_encoder()

pass = encoder.begin_render_pass(render_target)

pass.bind_pipeline(pipeline)
pass.bind_vertex_buffer(vertices)
pass.bind_index_buffer(indices)

pass.draw_indexed(
    index_count = 36
)

pass.end()

commands = encoder.finish()

queue.submit(commands)
```

---

# 320. Example — Render Graph

```text
graph = RenderGraph.create()

shadow = graph.texture(shadow_desc)
depth  = graph.texture(depth_desc)
color  = graph.texture(color_desc)

graph.add_pass("shadow")
    .write(shadow)

graph.add_pass("depth")
    .write(depth)

graph.add_pass("lighting")
    .read(shadow)
    .read(depth)
    .write(color)

graph.add_pass("present")
    .read(color)
    .present()

compiled = graph.compile()

compiled.execute(frame)
```

---

# 321. Example — Async GPU Work

```text
fence = queue.submit(commands)

await fence

data = await texture.readback()
```

The executor remains available for other tasks.

---

# 322. Example — Device Recovery

```text
match gfx.state() {
    Ready => render(),
    Recovering => show_loading(),
    Unavailable => fallback_renderer()
}
```

The application does not manipulate native driver recovery directly.

---

# 323. Example — Capability Query

```text
if device.supports(Feature.HdrOutput) {
    surface.enable_hdr()
}
```

---

# 324. Example — Backend Extension

```text
if device.backend() == Backend.Vulkan {
    vk = device.vulkan_extension()
    ...
}
```

Backend escape hatches remain explicit.

---

# 325. Architecture Summary

```text
┌──────────────────────────────────────────────┐
│ Axiom Application / GUI / Engine             │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ 615 Graphics API                             │
│ Window / Surface / Swapchain                 │
│ Buffer / Texture / Sampler                   │
│ Shader / Pipeline / RenderPass               │
│ CommandBuffer / Queue                        │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ Render Graph                                 │
│ DAG / Lifetimes / Aliasing / Barriers        │
│ Queue Scheduling / Transient Resources       │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ Graphics Backend                             │
│ Vulkan / D3D12 / Metal / WebGPU / Software  │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ 614 Device Runtime                           │
│ Device / GPU Memory / DMA / Hardware         │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ OS / Driver / GPU                            │
└──────────────────────────────────────────────┘
```

Cross-cutting:

```text
603 Security
606 Resource Governor
607 Scheduler
608 Synchronization
602 Diagnostics
605 Supervision
611 Storage
612 Serialization
613 Package/CAS
610 Crypto
```

---

# 326. Final Architecture Decision

BOOTSTRAP-615 establishes the following permanent architectural rule:

> **Axiom's graphics model is an explicit, device-oriented, command-based rendering system with a high-level convenience layer, rather than a GUI framework disguised as a graphics API.**

The core therefore remains suitable for:

- desktop applications;
- games;
- GUI frameworks;
- CAD;
- scientific visualization;
- 3D engines;
- image processing;
- ML visualization;
- headless servers;
- video composition;
- embedded systems.

At the same time, the architecture does not force every application to directly manage GPU barriers, descriptor sets or command buffers.

The two levels coexist:

```text
Simple API
    ↓
Explicit Graphics Runtime
    ↓
Native GPU
```

without introducing a second incompatible graphics architecture.

---

# 327. Completion

**BOOTSTRAP-615 — COMPLETE**

The graphics foundation is now sufficiently defined for higher-level GUI, 2D, 3D, visualization, game-engine and compute/rendering systems.

## Next task

**BOOTSTRAP-616 — Native Media, Audio, Video, Camera, Codec, Capture, Streaming & Hardware Media Acceleration Runtime 5.0**

The next layer will unify audio/video/camera/media around the same principles used by 609–615, including native audio devices, audio graphs, low-latency playback/recording, camera capture, pixel formats, video decode/encode, hardware codecs, media containers, timestamps, A/V synchronization, streaming, frame queues, zero-copy GPU↔media transfer, and integration with 614 GPU/media devices and 615 textures/surfaces.

:::

BOOTSTRAP-615 đã hoàn tất; chuỗi kiến trúc tiếp tục tự động sang **BOOTSTRAP-616**.