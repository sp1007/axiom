Tiếp tục với **BOOTSTRAP-615**, xây lớp đồ họa native phía trên Device/GPU Runtime 5.0 của BOOTSTRAP-614, với API đủ thấp để đạt hiệu năng native nhưng đủ cao để compiler/runtime tối ưu và các framework GUI/game/visualization xây dựng phía trên.

:::writing{variant="document" id="58321" title="BOOTSTRAP-615 — Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0"}
# BOOTSTRAP-615 — Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Runtime / Graphics  
**Depends on:** BOOTSTRAP-600 → 614  
**Primary dependencies:** Device/GPU 614, Scheduler 607, Synchronization 608, Resource Governor 606, Security 603, Storage/VFS 611, Serialization 612, Package 613, Diagnostics 602  
**Targets:** Windows, Linux, macOS, Android, iOS, WASM/Web, Embedded

---

# 1. Purpose

BOOTSTRAP-615 defines Axiom's native graphics foundation:

1. Window creation and management.
2. Display/monitor enumeration.
3. Native rendering surfaces.
4. Swapchains and presentation.
5. GPU resource abstraction.
6. Graphics and compute pipelines.
7. Command recording/submission.
8. Resource state transitions.
9. Render-pass execution.
10. Render-graph compilation.
11. Frame pacing.
12. Color management/HDR.
13. GPU/CPU synchronization.
14. Shader compilation and reflection boundary.
15. Offscreen/headless rendering.
16. Screenshot/readback.
17. Software-rendering fallback.
18. Device-loss recovery.
19. Multi-window/multi-display rendering.
20. Cross-platform graphics backend abstraction.

The design deliberately keeps **graphics** separate from:

- GUI widgets;
- scene graphs;
- game engines;
- layout systems;
- text layout;
- animation frameworks;
- application-specific rendering engines.

Those may be built above BOOTSTRAP-615.

---

# 2. Design Goals

## 2.1 Performance

Graphics code must be capable of:

- near-native API overhead;
- explicit GPU resource lifetime;
- batched command recording;
- multithreaded command generation;
- asynchronous GPU execution;
- minimal CPU/GPU synchronization;
- transient resource reuse;
- pipeline caching;
- zero-copy where hardware permits.

No mandatory garbage collector exists in the graphics layer.

---

# 3. Architectural Position

```text
Application / Game / GUI / Visualization
                │
                ▼
      Rendering Engine / GUI Toolkit
                │
                ▼
         BOOTSTRAP-615
 ┌───────────────────────────────┐
 │ Window / Display              │
 │ Surface / Swapchain           │
 │ Render Graph                  │
 │ Pipeline                      │
 │ Command Recording             │
 │ Render Pass                   │
 │ Resource Binding              │
 │ Shader Boundary               │
 │ Frame Pacing                  │
 └───────────────┬───────────────┘
                 │
                 ▼
         BOOTSTRAP-614
     Device / GPU / Accelerator
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
      Vulkan   D3D12    Metal
      OpenGL*  WebGPU   Software
```

`OpenGL` is permitted as a compatibility backend where required, but it is not the preferred modern backend.

---

# 4. Core Graphics Objects

All public APIs follow Axiom's struct-oriented model.

Primary objects:

```text
GraphicsSystem
DisplayManager
Display
Monitor
Window
WindowHandle
Surface
Swapchain

GraphicsDevice
Queue
Buffer
Texture
Sampler

ShaderModule
PipelineLayout
BindGroupLayout
BindGroup

GraphicsPipeline
ComputePipeline

CommandEncoder
CommandBuffer

RenderPass
ComputePass
CopyPass

Fence
Semaphore
Timeline
QueryPool

RenderGraph
RenderGraphPass
RenderGraphResource
```

Objects are handles to runtime-owned resources rather than language-level pointers.

---

# 5. Handle Model

Graphics handles use:

```text
Handle<T>
```

internally represented by:

```text
index
generation
device_id
```

Conceptually:

```text
GpuBufferHandle
    index
    generation
    device
```

Invalid or stale handles must fail validation.

No public API exposes internal GPU pointers.

---

# 6. Windowing Model

## 6.1 Window

```text
struct Window {
    id: WindowId
    state: WindowState
    size: Size2D
    position: Point2D
    dpi: DpiScale
    surface: SurfaceHandle
}
```

## 6.2 Window states

```text
Created
Hidden
Visible
Minimized
Maximized
Fullscreen
BorderlessFullscreen
Closing
Destroyed
```

State transitions are validated.

---

# 7. Window Creation

```text
Window.create(WindowDesc)
```

Example:

```text
window = Window.create({
    title: "Axiom Graphics",
    width: 1280,
    height: 720,
    resizable: true,
    visible: true
})
```

Window creation does not implicitly create a GPU device.

This permits:

- CPU-only applications;
- multiple graphics devices;
- headless rendering;
- delayed GPU initialization.

---

# 8. Window Styles

Supported styles:

```text
Normal
Borderless
Tool
Dialog
Utility
Fullscreen
BorderlessFullscreen
Transparent
AlwaysOnTop
Resizable
NonResizable
```

Platform support is capability-dependent.

---

# 9. Window Events

Window events include:

```text
Created
Shown
Hidden
Moved
Resized
Minimized
Restored
Maximized
FocusGained
FocusLost
CloseRequested
DpiChanged
DisplayChanged
FullscreenChanged
Destroyed
```

Input events remain primarily in BOOTSTRAP-614.

615 only provides the window/display routing boundary.

---

# 10. Event Loop Integration

Window events integrate with BOOTSTRAP-607.

```text
event_loop.poll()
event_loop.wait(timeout)
```

Graphics must never require a dedicated UI thread unless the platform requires one.

The runtime exposes:

```text
WindowThreadAffinity
```

when necessary.

---

# 11. Display Model

```text
DisplayManager
Display
DisplayId
DisplayMode
```

A display provides:

```text
name
physical_size
logical_size
dpi
refresh_rates
color_spaces
hdr_capabilities
modes
```

---

# 12. Display Modes

```text
DisplayMode {
    width
    height
    refresh_rate
    pixel_format
    color_space
    hdr
}
```

Refresh rate supports rational values:

```text
numerator
denominator
```

rather than floating-point-only representation.

---

# 13. Monitor Enumeration

```text
displays = DisplayManager.enumerate()
```

Each monitor has a stable runtime identity when the platform provides one.

Physical monitor IDs must not be assumed globally stable across operating systems.

---

# 14. DPI

The graphics layer exposes:

```text
DpiScale {
    x
    y
}
```

Logical and physical dimensions remain distinct.

Applications may request:

```text
LogicalPixels
PhysicalPixels
NativePixels
```

without hidden conversion.

---

# 15. Surface

A `Surface` represents a renderable presentation target.

Sources include:

- desktop window;
- native view;
- Android Surface;
- iOS layer;
- Web canvas;
- embedded framebuffer;
- offscreen image;
- headless target.

```text
Surface.create(window)
```

or:

```text
Surface.create_offscreen(desc)
```

---

# 16. Swapchain

A swapchain owns a rotating set of presentation images.

```text
Swapchain.create({
    surface,
    width,
    height,
    format,
    present_mode,
    image_count
})
```

---

# 17. Present Modes

Standard modes:

```text
FIFO
Mailbox
Immediate
```

Backend may reject unsupported modes.

The API must never silently claim a requested mode was honored when it was not.

---

# 18. Frame Acquisition

```text
frame = swapchain.acquire()
```

returns:

```text
AcquiredImage {
    image
    image_index
    acquire_token
}
```

The token participates in presentation synchronization.

---

# 19. Presentation

```text
swapchain.present(frame)
```

Presentation may return:

```text
Presented
Suboptimal
OutOfDate
SurfaceLost
DeviceLost
Timeout
Error
```

---

# 20. No Hidden Global GPU Stall

The runtime must not implement:

```text
submit()
wait_gpu_idle()
present()
```

as an implicit frame mechanism.

Synchronization must remain explicit.

---

# 21. Render Targets

A render target may contain:

```text
color attachments
depth attachment
stencil attachment
resolve attachments
```

Example:

```text
RenderTarget {
    color: Texture
    depth: Texture?
}
```

---

# 22. Texture Model

Supported dimensions:

```text
Texture1D
Texture2D
Texture3D
TextureCube
Texture2DArray
TextureCubeArray
```

with capability checks.

---

# 23. Texture Properties

```text
width
height
depth
mip_levels
array_layers
sample_count
format
usage
```

---

# 24. Texture Usage

Explicit usage flags:

```text
Sampled
Storage
RenderTarget
DepthStencil
CopySource
CopyDestination
Present
InputAttachment
```

Backends may expose additional capabilities.

---

# 25. Buffer Model

Buffers support:

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

A buffer may combine compatible usages.

---

# 26. Buffer Creation

```text
buffer = device.create_buffer({
    size: 1024 * 1024,
    usage: Vertex | CopyDestination
})
```

Allocation strategy is backend-specific.

---

# 27. Memory Classes

Graphics memory distinguishes:

```text
DeviceLocal
HostVisible
HostCached
HostCoherent
Unified
Readback
Upload
```

The runtime exposes capabilities instead of assuming discrete GPU architecture.

---

# 28. Mapping

```text
mapped = buffer.map(range)
```

For device-local resources without host visibility, the operation must fail explicitly.

Staging/upload paths are provided.

---

# 29. Sampler

```text
SamplerDesc {
    min_filter
    mag_filter
    mip_filter
    address_u
    address_v
    address_w
    anisotropy
    compare_mode
    lod_min
    lod_max
}
```

---

# 30. Shader Model

Shader stages:

```text
Vertex
Fragment
Compute
Geometry
TessellationControl
TessellationEvaluation
Mesh
Task
RayGeneration
AnyHit
ClosestHit
Miss
Intersection
Callable
```

Optional stages require capability checks.

---

# 31. Shader Boundary

Axiom does not require a single universal native GPU instruction format.

Instead:

```text
Axiom Shader IR
       │
 ┌─────┼────────┬────────┐
 ▼     ▼        ▼        ▼
SPIR-V DXIL     MSL     WGSL
```

The compiler/runtime may lower directly to target formats.

---

# 32. Shader IR Requirements

Shader IR must represent:

- scalar/vector types;
- matrices;
- structs;
- arrays;
- resources;
- bindings;
- interpolation;
- memory operations;
- control flow;
- barriers;
- atomics;
- subgroup operations;
- texture operations;
- derivative operations;
- precision constraints.

---

# 33. Shader Safety

Shader execution must be validated before execution where the backend requires validation.

The runtime must enforce:

- bounded resource access;
- legal binding indices;
- valid descriptor types;
- valid workgroup dimensions;
- backend capability limits.

Shaders cannot escape their declared GPU memory/resources.

---

# 34. Shader Reflection

Compiler-generated metadata:

```text
ShaderReflection {
    inputs
    outputs
    resources
    bindings
    push_constants
    workgroup_size
}
```

No runtime source-code reflection is required.

---

# 35. Pipeline Layout

Pipeline layouts describe:

```text
BindGroupLayout[]
push_constants
shader interface
```

They are immutable after creation.

---

# 36. Bind Groups

A bind group contains resources bound to a pipeline layout.

```text
BindGroup {
    buffers[]
    textures[]
    samplers[]
}
```

Validation happens at creation where possible.

---

# 37. Graphics Pipeline

```text
GraphicsPipelineDesc {
    vertex_shader
    fragment_shader
    layout
    vertex_layout
    raster_state
    depth_state
    blend_state
    multisample_state
    render_target_formats
}
```

Pipeline objects are immutable.

---

# 38. Compute Pipeline

```text
ComputePipelineDesc {
    shader
    layout
}
```

Pipeline creation must be thread-safe.

---

# 39. Pipeline Cache

Pipeline keys are deterministic hashes of:

```text
shader identity
shader variant
layout
render formats
vertex layout
raster state
depth state
blend state
multisample state
backend/device identity
driver compatibility identity
```

Pipeline caches integrate with BOOTSTRAP-613.

---

# 40. Pipeline Persistence

A pipeline cache may be stored as:

```text
.axgcache
```

It must contain:

```text
format_version
compiler_version
backend
device_identity
driver_identity
pipeline_key
binary
```

Invalid caches are safely discarded.

---

# 41. Command Encoder

Command recording starts with:

```text
encoder = device.create_command_encoder()
```

Commands are recorded without immediate GPU execution.

---

# 42. Command Types

Core command classes:

```text
BeginRenderPass
EndRenderPass
BeginComputePass
EndComputePass

CopyBuffer
CopyTexture
CopyBufferToTexture
CopyTextureToBuffer

Draw
DrawIndexed
DrawIndirect
DrawIndexedIndirect

Dispatch
DispatchIndirect

SetPipeline
SetBindGroup
SetVertexBuffer
SetIndexBuffer

Barrier
DebugMarker
Timestamp
```

---

# 43. Render Pass

```text
pass = encoder.begin_render_pass(desc)
```

A render pass defines:

```text
color attachments
depth/stencil attachment
load operations
store operations
clear values
resolve targets
```

---

# 44. Load Operations

```text
Load
Clear
DontCare
```

---

# 45. Store Operations

```text
Store
DontCare
Resolve
```

---

# 46. Compute Pass

```text
compute = encoder.begin_compute_pass()
compute.set_pipeline(pipeline)
compute.set_bind_group(0, group)
compute.dispatch(x, y, z)
compute.end()
```

---

# 47. Copy Pass

Copy operations are explicit.

No implicit format conversion is performed unless explicitly requested through a conversion operation.

---

# 48. Resource Barriers

The runtime tracks resource states:

```text
Undefined
CopySource
CopyDestination
Vertex
Index
Uniform
StorageRead
StorageWrite
ShaderRead
RenderTarget
DepthRead
DepthWrite
Present
Indirect
```

---

# 49. Barrier Compilation

The runtime may automatically derive backend barriers from declared resource usage.

This does **not** mean synchronization is hidden.

The application/RenderGraph declares intended usage; the runtime generates necessary native transitions.

---

# 50. Render Graph

Render Graph is an optional but native-supported higher-level facility.

```text
graph = RenderGraph.create()
```

Applications can declare:

```text
resource
pass
read
write
dependency
```

---

# 51. Render Graph Pass

```text
graph.add_pass("shadow", {
    writes: [shadow_map]
})

graph.add_pass("lighting", {
    reads: [shadow_map],
    writes: [color]
})
```

---

# 52. DAG Compilation

The graph compiler:

1. validates resources;
2. builds dependencies;
3. detects cycles;
4. removes unused passes;
5. determines lifetimes;
6. inserts transitions;
7. determines synchronization;
8. performs transient allocation;
9. generates command scheduling.

---

# 53. Cycle Detection

A cyclic dependency is a compile-time/runtime graph error.

Example:

```text
A -> B -> C -> A
```

must never be silently resolved.

---

# 54. Transient Resource Aliasing

Resources with non-overlapping lifetimes may share physical memory.

Example:

```text
ShadowTemp lifetime: 1..3
BloomTemp  lifetime: 4..7
```

may share the same backing allocation.

This reduces VRAM consumption.

---

# 55. Persistent Resources

Persistent resources are explicitly retained by application ownership.

Render Graph compilation must distinguish:

```text
Persistent
Transient
Imported
Exported
```

resources.

---

# 56. Imported Resources

External resources may enter the graph:

```text
graph.import_texture(texture)
```

Examples:

- swapchain images;
- camera textures;
- video frames;
- shared GPU resources.

---

# 57. Exported Resources

```text
graph.export_texture(texture)
```

prevents unsafe reclamation of resources required outside the graph.

---

# 58. Async Compute

Where supported:

```text
GraphicsQueue
ComputeQueue
CopyQueue
```

may execute concurrently.

The graph determines legal synchronization.

No concurrency is assumed unless the backend supports it.

---

# 59. Queue Types

Queue capabilities:

```text
Graphics
Compute
Transfer
Present
VideoDecode
VideoEncode
```

Video queues remain optional and connect to later media runtime.

---

# 60. Command Submission

```text
queue.submit(command_buffers, waits, signals)
```

Submission must be nonblocking whenever the platform permits.

---

# 61. Timeline Synchronization

A queue supports timeline values:

```text
queue.signal(42)
queue.wait(42)
```

Timeline values monotonically increase.

---

# 62. Binary Synchronization

For APIs requiring binary synchronization:

```text
Semaphore
```

is exposed.

Backend implementation is hidden.

---

# 63. GPU Fence

```text
fence = queue.submit(...)
fence.wait(timeout)
```

Waiting must support:

```text
NonBlocking
Timeout
Infinite
```

---

# 64. CPU/GPU Synchronization Rule

The runtime must not insert CPU waits into ordinary resource operations.

Explicit waits are required.

This avoids accidental serialization.

---

# 65. Frames In Flight

Applications configure:

```text
max_frames_in_flight
```

Typical values:

```text
1
2
3
```

No mandatory value is hard-coded.

---

# 66. Frame Context

```text
FrameContext {
    frame_id
    command_pool
    transient_allocator
    descriptor_allocator
    upload_allocator
    completion_token
}
```

Frame contexts can be recycled after GPU completion.

---

# 67. Frame Pacing

Frame pacing tracks:

```text
CPU frame time
GPU frame time
present interval
queue latency
acquisition latency
present latency
```

The runtime exposes measurements but does not force a specific pacing policy.

---

# 68. VSync

VSync is controlled through swapchain/present mode.

The runtime must report the actual selected mode.

---

# 69. Triple Buffering

Triple buffering is supported where the backend permits.

It is not equivalent to three arbitrary application-visible frame contexts.

---

# 70. Present Timing

Where supported:

```text
present_timestamp
refresh_timestamp
display_timestamp
```

are exposed.

Unsupported timestamps return `Unavailable`.

---

# 71. Color Space

Core color spaces include:

```text
sRGB
LinearSRGB
DisplayP3
Rec2020
HDR10
ScRGB
```

Backend capability determines availability.

---

# 72. Transfer Functions

Supported representations include:

```text
sRGB
Linear
PQ
HLG
```

---

# 73. HDR

HDR support exposes:

```text
HDR capability
maximum luminance
color primaries
transfer function
metadata capability
```

The runtime must not assume the OS compositor preserves arbitrary HDR metadata.

---

# 74. Color Management

A surface has:

```text
ColorSpace
TransferFunction
Format
HDRMetadata?
```

Applications may explicitly select compatible combinations.

---

# 75. MSAA

Supported sample counts are device-dependent.

```text
SampleCount:
1
2
4
8
16...
```

The runtime exposes supported counts.

---

# 76. Depth/Stencil

Formats include capability-defined:

```text
D16
D24
D32
D24S8
D32S8
```

---

# 77. Texture Formats

Core normalized formats include:

```text
RGBA8
BGRA8
RGBA16
RGBA16F
RGBA32F
R8
RG8
R16F
RG16F
R32F
```

Integer formats are separately identified.

---

# 78. Compressed Texture Formats

Capability-dependent families include:

```text
BC
ETC
ASTC
```

The package system can carry multiple variants.

---

# 79. Texture Variant Selection

AXPK may contain:

```text
texture.bc
texture.astc
texture.etc
texture.raw
```

Runtime chooses the best compatible variant.

---

# 80. Resource Upload

Upload paths use staging resources.

```text
upload(texture, source)
```

may perform:

```text
CPU -> staging -> GPU
```

or direct mapping when available.

---

# 81. Readback

```text
readback(texture, region)
```

returns a GPU-to-CPU transfer operation.

Readback is asynchronous by default.

---

# 82. Screenshot

```text
capture(surface)
```

produces an image buffer.

Encoding to PNG/JPEG/etc. belongs to the media/image layer.

---

# 83. Headless Rendering

Graphics devices may operate without a window.

Supported use cases:

- server rendering;
- testing;
- thumbnail generation;
- offline rendering;
- CI;
- AI/data generation.

---

# 84. Software Renderer

A deterministic CPU renderer is defined as an optional backend:

```text
SoftwareGraphicsBackend
```

It exists primarily for:

- tests;
- systems without GPU access;
- CI;
- deterministic rendering;
- fallback applications.

It does not need to match GPU performance.

---

# 85. Deterministic Renderer

A test renderer may expose:

```text
Deterministic
SingleThreaded
FixedPrecision
NoAsync
```

mode.

This allows graphics tests to compare exact or normalized output.

---

# 86. Device Loss

GPU device loss is a first-class state.

```text
DeviceLost
```

must invalidate affected GPU handles.

The runtime reports:

```text
reason
backend_error
device_identity
generation
```

---

# 87. Device Recovery

Recovery sequence:

```text
Detect loss
    ↓
Stop submissions
    ↓
Invalidate GPU handles
    ↓
Preserve CPU-side resource descriptions
    ↓
Recreate device
    ↓
Recreate reconstructible resources
    ↓
Rebuild pipelines
    ↓
Recreate swapchains
    ↓
Resume rendering
```

---

# 88. Resource Reconstruction

Resources created from immutable descriptors may be reconstructible.

Example:

```text
TextureDesc
source_package_hash
```

can be retained.

This integrates with BOOTSTRAP-613.

---

# 89. Non-Reconstructible Resources

Live GPU state such as:

- mapped transient memory;
- synchronization objects;
- command buffers;
- query state;

must not be assumed recoverable.

Applications receive explicit invalidation notifications.

---

# 90. Device Generation

Every GPU device has:

```text
DeviceId
Generation
```

A resource is valid only against the correct generation.

This prevents stale handles after device reset.

---

# 91. Multi-GPU

Multiple graphics devices may coexist.

```text
GraphicsSystem.devices()
```

Selection may consider:

```text
performance
memory
power
features
vendor
adapter type
application policy
```

The runtime must not silently migrate resources between unrelated devices.

---

# 92. GPU Affinity

Resources belong to a device.

Cross-device copies require explicit transfer.

---

# 93. External GPU Resources

Supported where backend allows:

```text
ImportTexture
ImportBuffer
ExportTexture
ExportBuffer
```

Security and capability checks are mandatory.

---

# 94. Shared GPU Memory

Cross-process GPU memory sharing is integrated with BOOTSTRAP-604.

It requires explicit:

```text
DeviceShareCapability
```

and backend support.

---

# 95. Window Capture

Capturing another application's window/display requires a dedicated capability from BOOTSTRAP-603.

Normal graphics access does not imply capture authority.

---

# 96. Protected Content

Protected surfaces/resources are represented explicitly.

Applications without the required capability cannot map or capture them.

---

# 97. Shader Execution Security

Shaders must not provide an escape mechanism into:

- CPU memory;
- arbitrary physical memory;
- unauthorized GPU resources;
- operating-system interfaces.

---

# 98. Debug Validation

Optional validation mode:

```text
GraphicsValidation.Strict
GraphicsValidation.Normal
GraphicsValidation.Off
```

Validation may detect:

- use-after-destroy;
- wrong resource state;
- invalid pipeline binding;
- incompatible formats;
- invalid command ordering;
- synchronization hazards.

---

# 99. Debug Markers

Commands support:

```text
push_debug_group(name)
pop_debug_group()
insert_debug_marker(name)
```

Markers integrate with backend GPU debuggers where supported.

---

# 100. GPU Timestamp Queries

```text
QueryPool.create(Timestamp)
```

allows:

```text
timestamp_begin
timestamp_end
```

and GPU duration measurement.

---

# 101. Occlusion Queries

Optional:

```text
Occlusion
BinaryOcclusion
```

query types.

---

# 102. Pipeline Statistics

Optional counters:

```text
vertices
primitives
fragment_invocations
compute_invocations
```

where supported.

---

# 103. Graphics Diagnostics

BOOTSTRAP-602 receives:

```text
frame_id
gpu_time
cpu_time
present_latency
draw_count
dispatch_count
pipeline_switches
barrier_count
resource_bytes
transient_bytes
descriptor_count
queue_wait_time
```

---

# 104. GPU Crash Diagnostics

On supported platforms, the runtime records:

```text
device
driver
backend
pipeline
command buffer
resource state
frame id
shader identity
```

without recording secret data.

---

# 105. Resource Leak Detection

Debug builds track:

```text
resource type
creation site
owner
size
generation
```

Release builds may eliminate tracking metadata.

---

# 106. Resource Governor Integration

Graphics allocations consume BOOTSTRAP-606 budgets:

```text
VRAM
device memory
mapped memory
descriptor count
command buffers
pipeline count
query count
swapchain images
```

---

# 107. Admission Control

Large GPU allocations may fail before allocation if the resource budget cannot satisfy them.

This prevents uncontrolled memory pressure.

---

# 108. Memory Pressure

GPU memory pressure states:

```text
Normal
Elevated
Critical
```

Applications may register callbacks.

The runtime itself does not arbitrarily destroy application resources.

---

# 109. Scheduler Integration

GPU submission is integrated with BOOTSTRAP-607.

Rules:

- command recording may occur on worker threads;
- submission occurs through queue objects;
- blocking waits use explicit scheduler-aware operations;
- UI thread is never blocked unnecessarily;
- GPU completion may wake async tasks.

---

# 110. Synchronization Integration

GPU synchronization uses BOOTSTRAP-608 concepts:

```text
Fence
Semaphore
Timeline
Event
```

CPU-side waits obey the language memory model.

---

# 111. Async GPU API

Operations such as readback may return:

```text
Future<Result<ReadbackBuffer>>
```

without blocking the calling task.

---

# 112. Cancellation

Cancellation is supported before submission where possible.

Once a GPU command has been submitted, cancellation normally means:

```text
do not await result
```

rather than attempting unsafe GPU command removal.

---

# 113. Window Resize

Resize sequence:

```text
ResizeRequested
    ↓
Pause rendering to old surface
    ↓
Recreate swapchain
    ↓
Recreate dependent targets
    ↓
Resume
```

No GPU resource is silently resized.

---

# 114. Minimized Window

A minimized window may expose:

```text
ZeroRenderableExtent
```

The application can suspend rendering.

The runtime must avoid busy loops.

---

# 115. Fullscreen

Modes:

```text
Windowed
BorderlessFullscreen
ExclusiveFullscreen
```

Exclusive mode is optional and platform-dependent.

---

# 116. Multi-Window Rendering

A single graphics device can own multiple surfaces and swapchains.

Each surface has independent:

- dimensions;
- format;
- color space;
- present mode;
- frame state.

---

# 117. Multi-Monitor Migration

When a window crosses monitors, the runtime emits:

```text
DisplayChanged
DpiChanged
ColorSpaceChanged
```

where applicable.

---

# 118. Window Compositor Boundary

615 does not implement:

- desktop compositor;
- OS taskbar;
- widget layout;
- accessibility tree;
- application menu;
- native control toolkit.

It only supplies the rendering/presentation boundary.

---

# 119. GUI Toolkit Boundary

A higher-level GUI system may use:

```text
Window
Surface
Texture
CommandEncoder
RenderGraph
```

to render widgets.

---

# 120. Text Rendering Boundary

Text shaping and font management belong to a later text/media layer.

615 accepts already prepared glyph geometry or texture resources.

---

# 121. 2D Rendering Boundary

A future 2D API can build on:

```text
Texture
Sampler
Pipeline
VertexBuffer
RenderPass
```

without modifying 615.

---

# 122. 3D Rendering Boundary

A 3D engine can build:

```text
Mesh
Material
Camera
Lighting
Scene
```

above the core graphics runtime.

These are intentionally outside 615.

---

# 123. Compute Boundary

General-purpose GPU compute is supported through:

```text
ComputePipeline
ComputePass
StorageBuffer
StorageTexture
```

AI/tensor runtimes may build on this layer.

---

# 124. GPU Accelerator Boundary

Specialized accelerators from 614 may expose graphics-compatible resources where supported.

The graphics runtime does not assume every accelerator is a graphics device.

---

# 125. Package Integration

AXPK can contain:

```text
shaders/
textures/
meshes/
pipelines/
materials/
render-config/
```

Each asset can contain target-specific variants.

---

# 126. Shader Package Entry

Example logical entry:

```text
shader://lighting/main
```

with variants:

```text
vulkan
d3d12
metal
webgpu
software
```

---

# 127. Asset Fingerprints

Graphics resources derived from package assets retain content hashes.

This enables:

- deterministic caches;
- device-loss reconstruction;
- incremental builds;
- shader/pipeline cache validation.

---

# 128. Compiler Integration

The compiler may generate:

```text
.axshader
.axpipeline
.axgfxmeta
```

metadata.

Metadata can contain:

```text
shader interface
resource bindings
pipeline compatibility
target architectures
required features
```

---

# 129. Compile-Time Validation

The compiler should reject known-invalid combinations such as:

```text
shader binding mismatch
pipeline layout mismatch
unsupported shader stage combination
invalid resource format
```

before runtime where possible.

---

# 130. Dead Stripping

Unused graphics components must be removable.

An application using only:

```text
headless compute
```

must not automatically link:

- desktop windowing;
- monitor enumeration;
- swapchain;
- GUI support.

---

# 131. Backend Selection

Backend selection may use:

```text
Auto
Vulkan
D3D12
Metal
WebGPU
Software
```

Applications can explicitly request a backend.

---

# 132. Native Backend Mapping

## Windows

Primary:

```text
D3D12
Vulkan
```

Windowing:

```text
Win32
```

Optional compatibility:

```text
D3D11
OpenGL
```

---

# 133. Linux

Primary:

```text
Vulkan
```

Windowing:

```text
Wayland
X11
```

The windowing backend is separate from the GPU backend.

---

# 134. macOS

Primary:

```text
Metal
```

Windowing:

```text
AppKit
CAMetalLayer
```

---

# 135. iOS

Primary:

```text
Metal
UIKit
CAMetalLayer
```

Lifecycle is controlled by the mobile application runtime.

---

# 136. Android

Primary:

```text
Vulkan
```

Surface integration uses native Android surfaces.

OpenGL ES may exist as compatibility backend.

---

# 137. WASM/Web

Primary:

```text
WebGPU
Canvas
```

The runtime must obey browser sandbox restrictions.

No arbitrary native device access is assumed.

---

# 138. Embedded

Possible backends:

```text
Framebuffer
DRM/KMS
Vendor GPU
Software
```

The backend is capability-driven.

---

# 139. API Capability Query

Every backend exposes:

```text
GraphicsCapabilities
```

including:

```text
max_texture_size
max_bind_groups
max_samples
max_storage_buffers
shader_stages
queue_types
hdr
ray_tracing
mesh_shaders
timestamp_queries
```

---

# 140. Feature Negotiation

Features are requested explicitly:

```text
device.request_features([
    TimestampQueries,
    Compute,
    StorageTextures
])
```

Unsupported required features cause device creation failure.

Optional features may be queried and skipped.

---

# 141. Limits

```text
GraphicsLimits
```

contains backend/device-specific limits.

Applications must not assume desktop GPU limits on mobile/Web.

---

# 142. Error Model

Graphics operations return:

```text
Result<T, GraphicsError>
```

Major categories:

```text
InvalidState
InvalidResource
Unsupported
OutOfMemory
Timeout
SurfaceLost
DeviceLost
ValidationFailed
BackendFailure
PermissionDenied
```

---

# 143. Error Preservation

Backend-specific error information may be attached:

```text
GraphicsError {
    kind
    backend_code
    message_id
    device
}
```

Localized human text is not required for the core error object.

---

# 144. Thread Safety

Immutable graphics objects may be shared across threads where declared thread-safe.

Mutable recording objects are thread-affine unless documented otherwise.

Example:

```text
CommandEncoder
```

is not implicitly shared.

---

# 145. Parallel Command Recording

Multiple command encoders can be recorded concurrently.

```text
worker1 -> encoder1
worker2 -> encoder2
worker3 -> encoder3
```

Then:

```text
queue.submit([cmd1, cmd2, cmd3])
```

---

# 146. Descriptor Allocation

Descriptor/bind-group allocation uses per-thread or per-frame pools.

The hot path must avoid a global mutex.

---

# 147. Upload Allocator

Frame upload memory may use:

```text
linear arena
ring buffer
staging pool
```

and is reclaimed after GPU completion.

---

# 148. Transient Allocator

RenderGraph transient memory is lifetime-aware.

It must reuse allocations where safe.

---

# 149. Resource Lifetime

A resource remains alive until:

```text
logical owner releases it
AND
GPU no longer references it
```

The runtime therefore tracks GPU completion before physical reclamation.

---

# 150. Deferred Destruction

```text
destroy(buffer)
```

may become:

```text
retire(buffer, completion_value)
```

internally.

No garbage collector is required.

---

# 151. Command Buffer Lifetime

Command buffers become invalid after their recorded resources are destroyed or after the backend's documented reuse point.

The runtime must validate reuse.

---

# 152. Debug Resource Labels

Resources may have optional:

```text
debug_name
```

This metadata can be removed from release builds.

---

# 153. GPU Memory Statistics

Runtime exposes:

```text
allocated
reserved
resident
mapped
transient
free_estimate
```

where supported.

---

# 154. Capture Integration

A graphics capture subsystem may record:

```text
frame
commands
resources
pipeline IDs
timestamps
```

Capture must be explicitly enabled.

---

# 155. Capture Privacy

Capture must not automatically include:

- secret resources;
- protected surfaces;
- unrelated application windows;
- private IPC content.

---

# 156. State/Checkpoint Boundary

BOOTSTRAP-600 may checkpoint application graphics configuration, but not live GPU state.

Checkpointable:

```text
window configuration
render settings
selected device policy
pipeline cache identity
asset hashes
```

Not checkpointable:

```text
live command buffer
GPU fence state
mapped transient allocation
live swapchain image
```

---

# 157. Recovery After Application Restart

The graphics runtime can reconstruct:

```text
device
surface
swapchain
persistent textures
pipelines
```

from application descriptors and packaged assets.

---

# 158. Configuration Integration

BOOTSTRAP-601 may configure:

```text
backend
validation
vsync
frames_in_flight
preferred_gpu
shader_cache
pipeline_cache
hdr_policy
present_mode
```

Configuration is immutable per runtime snapshot.

---

# 159. Security Integration

BOOTSTRAP-603 defines:

```text
graphics.device
graphics.create_surface
graphics.capture
graphics.shared_resource
graphics.shader_execute
graphics.protected_resource
```

capabilities.

---

# 160. Resource Governor Integration

Every major GPU resource is attributable to:

```text
application
service
resource_group
device
frame
```

for diagnostics and quota enforcement.

---

# 161. Diagnostics Integration

Graphics events use stable event IDs.

Examples:

```text
GFX_DEVICE_CREATED
GFX_DEVICE_LOST
GFX_SWAPCHAIN_RECREATED
GFX_PIPELINE_COMPILED
GFX_SHADER_FAILED
GFX_GPU_TIMEOUT
GFX_FRAME_PRESENTED
```

---

# 162. Supervision Integration

BOOTSTRAP-605 can monitor a graphics service.

Device failure must not automatically terminate the entire application unless policy requires it.

---

# 163. IPC Integration

GPU resource handles can cross process boundaries only through explicit export/import operations.

Normal handles are process-local.

---

# 164. Serialization Integration

Graphics descriptors may implement generated AXBIN schemas.

Live GPU handles are not serialized as ordinary portable objects.

---

# 165. Compression/Package Integration

Textures and shader packages use BOOTSTRAP-613.

Large resources can use chunked package entries.

---

# 166. Network Boundary

Remote rendering is not part of core 615.

A future remote-rendering layer may serialize:

```text
command streams
resource deltas
frame data
```

using higher-level protocols.

---

# 167. API Example — Basic Window

```text
graphics = GraphicsSystem.create()

window = Window.create({
    title: "Axiom",
    width: 1280,
    height: 720
})

surface = Surface.from_window(window)

device = graphics.create_device({
    surface
})

swapchain = device.create_swapchain({
    surface,
    format: BGRA8_SRGB,
    present_mode: FIFO
})
```

---

# 168. API Example — Rendering

```text
frame = swapchain.acquire()

encoder = device.create_command_encoder()

pass = encoder.begin_render_pass({
    color: frame.image,
    clear: true
})

pass.set_pipeline(pipeline)
pass.set_bind_group(0, globals)
pass.set_vertex_buffer(0, vertices)
pass.draw(vertex_count)

pass.end()

commands = encoder.finish()

device.graphics_queue.submit(commands)

swapchain.present(frame)
```

---

# 169. API Example — Compute

```text
encoder = device.create_command_encoder()

pass = encoder.begin_compute_pass()

pass.set_pipeline(compute_pipeline)
pass.set_bind_group(0, bindings)
pass.dispatch(128, 128, 1)

pass.end()

device.compute_queue.submit(encoder.finish())
```

---

# 170. API Example — RenderGraph

```text
graph = RenderGraph.create()

shadow = graph.create_texture(shadow_desc)
color  = graph.create_texture(color_desc)

graph.add_pass("shadow", {
    writes: [shadow]
})

graph.add_pass("lighting", {
    reads: [shadow],
    writes: [color]
})

graph.compile()
graph.execute(frame)
```

---

# 171. API Example — Struct Method Extension

Consistent with Axiom's struct-only model:

```text
fn Window.render(self, renderer: Renderer) -> Result<()> {
    ...
}
```

The function remains an ordinary function whose first parameter is the receiver.

No class runtime is required.

---

# 172. API Example — Custom Renderer

```text
struct Renderer {
    device: GraphicsDevice
    pipeline: GraphicsPipeline
}

fn Renderer.draw_triangle(
    self,
    frame: SurfaceFrame
) -> Result<()> {
    ...
}
```

---

# 173. No Mandatory Engine Abstraction

615 does not impose:

```text
Scene
Entity
Material
Camera
Transform
Component
Widget
```

These belong to higher layers.

---

# 174. Graphics Memory Safety

The graphics runtime guarantees:

- no stale handle reuse;
- generation checking;
- explicit lifetime;
- bounds validation where required;
- no CPU pointer exposure to arbitrary device memory;
- no use-after-device-loss.

---

# 175. No GC Requirement

The runtime uses:

```text
explicit ownership
reference-counted handles where useful
generation handles
deferred GPU destruction
frame retirement
```

but does not require a tracing garbage collector.

---

# 176. Reference Counting Policy

Reference counting may be used internally for shared immutable graphics metadata.

It must not be required for ordinary GPU command recording.

---

# 177. Hot Path Allocation Rule

The following should be allocation-free after initialization where practical:

```text
draw
dispatch
set_pipeline
set_bind_group
set_vertex_buffer
set_index_buffer
command_record
queue_submit
```

---

# 178. Error Fast Path

Successful GPU command recording must avoid exceptions and dynamic string construction.

---

# 179. Backend Abstraction

Core interface:

```text
trait GraphicsBackend {
    create_device(...)
    create_surface(...)
    create_swapchain(...)
    create_buffer(...)
    create_texture(...)
    create_pipeline(...)
    create_command_encoder(...)
}
```

Backends are compile-time selectable modules.

---

# 180. Backend Independence

Application code must not depend on:

```text
Vk*
ID3D12*
MTL*
```

types unless explicitly entering an FFI/backend extension.

---

# 181. Native Escape Hatch

Advanced applications may request:

```text
NativeGraphicsHandle
```

through an explicit unsafe/backend capability.

This is not available through ordinary safe APIs.

---

# 182. Unsafe Boundary

Unsafe native graphics operations must be explicitly marked:

```text
unsafe
```

and may require capability:

```text
graphics.native_backend
```

---

# 183. FFI Boundary

External graphics APIs can be accessed through Axiom FFI without contaminating the core graphics API.

---

# 184. ABI Stability

Public serialized graphics descriptors use versioned AXBIN schemas.

Internal GPU object layouts are not ABI-stable.

---

# 185. Reproducibility

Pipeline and shader cache keys must be deterministic for the same:

```text
source
compiler
target
device/driver identity
pipeline configuration
```

---

# 186. Cache Invalidation

Caches invalidate when incompatible:

```text
shader compiler version
backend
GPU architecture
driver
pipeline format
runtime format
```

changes.

---

# 187. Compiler Cache Integration

The compiler may reuse:

```text
shader IR
compiled shader
reflection metadata
pipeline descriptors
```

when source and compilation inputs are unchanged.

---

# 188. Build Artifact Separation

Graphics build artifacts:

```text
source shader
    ↓
shader IR
    ↓
target shader
    ↓
reflection
    ↓
pipeline metadata
    ↓
package/cache
```

are separate from ordinary application object files.

---

# 189. AI-Readable Graphics Metadata

`.axgfxmeta` should expose:

```text
resource graph
shader bindings
pipeline requirements
target features
texture formats
memory requirements
```

in deterministic machine-readable form.

---

# 190. AI Build Assistance

The compiler may report structured diagnostics:

```text
code
location
resource
expected
actual
suggested_fix_category
```

without generating arbitrary source changes automatically.

---

# 191. Render Graph Serialization

A render graph description can optionally be serialized for diagnostics/build tooling.

Live graph execution state is not portable.

---

# 192. Frame Debug Metadata

Each frame may have:

```text
FrameId
RenderGraphHash
PipelineSetHash
ResourceSetHash
DeviceGeneration
```

to correlate diagnostics.

---

# 193. GPU Timeout

A GPU timeout produces:

```text
GpuTimeout
```

and enters recovery policy.

The runtime must avoid indefinite waits.

---

# 194. Hang Recovery

Where the OS/backend supports reset:

```text
detect timeout
capture diagnostics
stop submissions
attempt reset/recreate
```

Otherwise the error is propagated.

---

# 195. Thermal Interaction

GPU thermal/power information comes from BOOTSTRAP-614.

615 may respond by reducing:

```text
frame rate
resolution
quality
```

only if an application policy explicitly requests adaptive behavior.

---

# 196. Power Policy

Applications can request:

```text
Performance
Balanced
PowerSaving
```

but actual GPU behavior remains platform-controlled.

---

# 197. Mobile Lifecycle

Mobile platforms may suspend rendering when:

```text
application backgrounded
surface destroyed
activity/view detached
```

615 exposes explicit surface invalidation.

---

# 198. Surface Recreation

A mobile surface can disappear while the graphics device remains valid.

Therefore:

```text
SurfaceLost
```

does not necessarily mean:

```text
DeviceLost
```

---

# 199. WASM Lifecycle

Browser canvas resize, visibility, and context loss map to:

```text
SurfaceChanged
DeviceLost
```

as appropriate.

---

# 200. Context Loss

Web/embedded backends may lose graphics context.

The recovery model follows the same generation-based resource reconstruction model.

---

# 201. Embedded Framebuffer

A framebuffer backend may expose:

```text
FramebufferSurface
```

without a traditional window manager.

---

# 202. Remote Display Boundary

Remote desktop/compositor systems remain outside 615.

615 only sees the native surface abstraction.

---

# 203. Presentation Ownership

A swapchain image is owned by one of:

```text
Available
Acquired
Rendering
Queued
Presented
```

Invalid transitions are rejected.

---

# 204. Swapchain State Machine

```text
Created
    ↓
Available
    ↓
Acquired
    ↓
Rendering
    ↓
Queued
    ↓
Presented
    ↓
Available
```

Exceptions:

```text
OutOfDate
SurfaceLost
DeviceLost
```

---

# 205. Resource State Machine

Resources transition through declared usages.

The runtime tracks:

```text
current_state
required_state
queue_owner
last_submission
```

---

# 206. Queue Ownership

Multi-queue resources may require explicit ownership transfer.

RenderGraph can derive this automatically.

---

# 207. Barrier Batching

Compatible barriers should be grouped to minimize backend command overhead.

---

# 208. Descriptor Validation

Descriptor validation occurs at:

```text
BindGroup creation
Pipeline binding
```

with debug-level deep checks.

---

# 209. Push Constants

Small frequently changed constants may use:

```text
PushConstants
```

where backend supports them.

Maximum size is capability-dependent.

---

# 210. Dynamic Uniform Data

For larger dynamic values:

```text
UploadBuffer
UniformBuffer
DynamicOffset
```

may be used.

---

# 211. Indirect Drawing

Supported:

```text
draw_indirect
draw_indexed_indirect
dispatch_indirect
```

where backend permits.

---

# 212. Multi-Draw

Optional:

```text
multi_draw
multi_draw_indirect
```

extensions are capability-driven.

---

# 213. Instancing

Native draw calls support:

```text
instance_count
first_instance
```

---

# 214. Vertex Layout

Vertex layouts define:

```text
binding
stride
input_rate
attribute
format
offset
```

---

# 215. Blend State

Supports:

```text
source_factor
destination_factor
operation
alpha factors
write mask
```

---

# 216. Raster State

Includes:

```text
cull_mode
front_face
fill_mode
depth_bias
depth_clamp
scissor
```

---

# 217. Depth State

Includes:

```text
depth_test
depth_write
compare
stencil
```

---

# 218. Stencil State

Separate front/back configuration:

```text
compare
fail_op
depth_fail_op
pass_op
read_mask
write_mask
reference
```

---

# 219. Viewport and Scissor

Commands:

```text
set_viewport(...)
set_scissor(...)
```

are dynamic when backend permits.

---

# 220. Dynamic State

Dynamic state may include:

```text
viewport
scissor
blend_constant
stencil_reference
depth_bias
```

Capability determines support.

---

# 221. Resource Barriers and RenderGraph

Applications using RenderGraph do not manually emit ordinary resource barriers.

Low-level users can use explicit barriers.

Both APIs share the same underlying state model.

---

# 222. Low-Level Mode

615 must expose a lower-level command API for advanced engines that do not want RenderGraph.

---

# 223. High-Level Mode

RenderGraph provides automatic scheduling and resource lifetime optimization.

---

# 224. Two-Level API Principle

```text
Low-level:
maximum control

RenderGraph:
maximum scheduling convenience
```

Neither replaces the other.

---

# 225. Graphics Initialization

Initialization sequence:

```text
GraphicsSystem
    ↓
Enumerate devices
    ↓
Select device
    ↓
Request features
    ↓
Create device
    ↓
Create queues
    ↓
Create surfaces
    ↓
Create swapchains
```

---

# 226. Lazy Initialization

A program may delay:

```text
GPU device
shader compiler
pipeline cache
swapchain
```

until first use.

---

# 227. Minimal Profile

A headless application requiring only compute should be able to link:

```text
GraphicsCore
Compute
Device
```

without:

```text
Windowing
Display
Desktop compositor
```

---

# 228. Window-Only Profile

A program may create windows without creating a GPU device.

This is required for tools that perform custom/native rendering later.

---

# 229. Software-Only Profile

A program may use:

```text
Window
Surface
SoftwareRenderer
```

without a GPU backend.

---

# 230. Testing Profiles

Supported profiles:

```text
MockGraphics
SoftwareDeterministic
NativeValidation
NativePerformance
```

---

# 231. Mock Backend

Mock backend records:

```text
commands
resource creation
resource destruction
submission
presentation
```

for unit tests.

---

# 232. Graphics Fuzzing

Fuzz targets include:

- shader parser;
- shader IR;
- pipeline descriptors;
- render graph;
- command validation;
- AXBIN graphics metadata;
- package shader entries;
- resource state transitions.

---

# 233. Fault Injection

Injectable failures:

```text
OutOfMemory
DeviceLost
SurfaceLost
PipelineCompileFailure
ShaderCompileFailure
Timeout
SwapchainOutOfDate
AllocationFailure
```

---

# 234. Deterministic Scheduling

Graphics tests can use:

```text
FakeClock
MockQueue
MockFence
DeterministicScheduler
```

from earlier runtime layers.

---

# 235. Performance Benchmarks

Benchmarks must measure independently:

```text
command recording
command submission
pipeline creation
descriptor creation
buffer upload
texture upload
GPU execution
readback
present
frame latency
```

---

# 236. Performance Targets

Reference targets:

```text
ordinary command recording: near-native API overhead
no allocation in steady-state draw loop
no global lock in command recording
parallel recording scales with worker count
resource destruction amortized
```

Exact nanosecond targets remain backend/platform-specific.

---

# 237. Binary Size

A graphics-free application must link zero graphics runtime.

A compute-only application should not link desktop windowing.

Backend modules are separately dead-strippable.

---

# 238. Security Invariant

A graphics capability must not imply:

```text
filesystem access
network access
process creation
arbitrary device access
```

---

# 239. Memory Invariant

GPU memory must never be interpreted as ordinary Axiom memory without an explicit mapping operation.

---

# 240. Handle Invariant

A stale GPU handle must never resolve to a newly allocated unrelated resource.

Generation validation is mandatory.

---

# 241. Device Invariant

Resources belong to exactly one graphics device generation.

---

# 242. Synchronization Invariant

The runtime must not report GPU completion before the backend guarantees completion.

---

# 243. Presentation Invariant

A swapchain image cannot be simultaneously:

```text
presented
and
application-owned
```

without explicit backend semantics.

---

# 244. Pipeline Invariant

Immutable pipeline objects cannot be mutated after successful creation.

---

# 245. Shader Invariant

Shader resources and bindings must match the pipeline layout.

---

# 246. RenderGraph Invariant

A compiled graph must be acyclic.

---

# 247. Resource Lifetime Invariant

A physical resource cannot be reclaimed while referenced by an unfinished GPU submission.

---

# 248. Device-Loss Invariant

After device generation changes, all old GPU handles are invalid.

---

# 249. Security Capture Invariant

Graphics capture cannot bypass protected-resource restrictions.

---

# 250. Determinism Invariant

Given identical:

```text
shader inputs
pipeline descriptor
device/backend identity
compiler version
```

the pipeline cache key must be identical.

---

# 251. Acceptance Criteria

BOOTSTRAP-615 is complete when at least the following are verified.

### Windowing

1. Window creation works on Windows.
2. Window creation works on Linux.
3. Window creation works on macOS.
4. Android surface integration exists.
5. iOS surface integration exists.
6. WASM canvas integration exists.
7. Embedded surface backend exists.
8. Resize works.
9. DPI changes are reported.
10. Fullscreen state transitions work.
11. Minimize/restore works.
12. Window events integrate with scheduler.

### Display

13. Display enumeration works.
14. Display modes are exposed.
15. Refresh rates are represented exactly.
16. DPI is exposed.
17. HDR capability is exposed.
18. Color-space capability is exposed.
19. Monitor changes are detected.

### GPU

20. Device enumeration works.
21. Device selection is explicit.
22. Device generations are enforced.
23. Device loss is detectable.
24. Device recreation works where backend permits.
25. GPU queues are exposed.
26. Queue capabilities are reported.
27. Device limits are reported.

### Resources

28. Buffers work.
29. Textures work.
30. Samplers work.
31. Render targets work.
32. Depth/stencil works.
33. MSAA works where supported.
34. Mapping works for host-visible resources.
35. Upload staging works.
36. Readback works.
37. Deferred destruction works.
38. Stale handles are rejected.

### Shaders

39. Vertex shaders work.
40. Fragment shaders work.
41. Compute shaders work.
42. Shader reflection works.
43. Binding validation works.
44. Shader compilation errors are structured.
45. Shader caches work.
46. Invalid shader resources cannot execute.

### Pipelines

47. Graphics pipelines work.
48. Compute pipelines work.
49. Pipeline layouts work.
50. Bind groups work.
51. Pipeline caching works.
52. Pipeline keys are deterministic.
53. Pipeline cache invalidation works.

### Commands

54. Command encoders work.
55. Render passes work.
56. Compute passes work.
57. Copy passes work.
58. Draw works.
59. Indexed draw works.
60. Indirect draw works where supported.
61. Dispatch works.
62. Resource transitions work.
63. Barriers are correct.
64. Parallel command recording works.

### Synchronization

65. GPU fences work.
66. Binary semaphores work where required.
67. Timeline synchronization works where supported.
68. CPU waits are explicit.
69. GPU completion callbacks work.
70. No hidden global GPU stall occurs.

### Swapchain

71. Swapchain creation works.
72. Acquire works.
73. Present works.
74. FIFO mode works.
75. Mailbox works where supported.
76. Immediate works where supported.
77. Out-of-date recovery works.
78. Surface-loss recovery works.
79. Multi-window swapchains work.

### RenderGraph

80. Resource declaration works.
81. Pass declaration works.
82. DAG construction works.
83. Cycle detection works.
84. Unused-pass elimination works.
85. Resource lifetime analysis works.
86. Transient aliasing works.
87. Barrier generation works.
88. Multi-queue synchronization works where supported.
89. Graph recompilation is deterministic.

### Frame Runtime

90. Frames-in-flight work.
91. Frame pacing metrics work.
92. GPU timing works where supported.
93. Present timing works where supported.
94. Triple buffering works where supported.
95. Resize does not corrupt frame state.

### Color/HDR

96. sRGB works.
97. Linear color works.
98. HDR capability detection works.
99. PQ/HLG handling works where supported.
100. Color-space changes are reported.

### Diagnostics

101. GPU timings are exposed.
102. Resource statistics are exposed.
103. pipeline compilation diagnostics work.
104. device-loss diagnostics work.
105. GPU timeout diagnostics work.
106. debug markers work.
107. resource leak diagnostics work in debug mode.

### Security

108. graphics capabilities are enforced.
109. protected resources cannot be captured without authority.
110. cross-process GPU sharing is capability-controlled.
111. unsafe native handles require explicit unsafe boundary.
112. shader execution cannot access unauthorized resources.

### Recovery

113. device loss invalidates stale handles.
114. reconstructible resources can be recreated.
115. swapchains can be recreated.
116. pipeline caches can be rebuilt.
117. application restart can reconstruct persistent graphics state.

### Packaging

118. shader assets can be packaged in AXPK.
119. texture variants can be packaged.
120. content hashes are preserved.
121. target-specific shader variants are selectable.
122. package corruption is detected.

### Compiler

123. graphics metadata can be generated.
124. shader interfaces can be validated.
125. pipeline metadata can be cached.
126. unused graphics modules are dead-strippable.
127. headless compute does not pull desktop windowing.

### Cross-platform

128. Windows backend passes tests.
129. Linux backend passes tests.
130. macOS backend passes tests.
131. Android backend passes tests.
132. iOS backend passes tests.
133. WASM backend passes tests.
134. software backend passes deterministic tests.

### Quality

135. command recording has no mandatory per-command heap allocation.
136. command recording avoids global locks.
137. stale-resource tests pass.
138. device-loss fault injection passes.
139. shader fuzzing passes.
140. render-graph fuzzing passes.
141. synchronization stress tests pass.
142. resize stress tests pass.
143. multi-window stress tests pass.
144. GPU memory quota tests pass.
145. capture security tests pass.
146. deterministic pipeline-key tests pass.
147. package/cache corruption tests pass.
148. mock backend tests pass.
149. software renderer regression tests pass.
150. public API documentation is generated.

---

# 252. Final Architecture

```text
                 AXIOM APPLICATION
                        │
          ┌─────────────┴─────────────┐
          │                           │
     GUI / GAME                  COMPUTE / AI
          │                           │
          └─────────────┬─────────────┘
                        ▼
              BOOTSTRAP-615
     ┌────────────────────────────────────┐
     │ Window / Display / Surface          │
     │ Swapchain / Presentation            │
     │                                    │
     │ Buffer / Texture / Sampler         │
     │ Shader / Pipeline / BindGroup      │
     │                                    │
     │ Command Encoder / Render Pass      │
     │ Compute Pass / Copy Pass           │
     │                                    │
     │ RenderGraph / Resource Barriers    │
     │ Frame Pacing / GPU Timing          │
     │ HDR / Color Management              │
     └──────────────────┬─────────────────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
       BOOTSTRAP-614         BOOTSTRAP-607
       Device / GPU          Scheduler
              │                   │
       ┌──────┼──────┐            │
       ▼      ▼      ▼            ▼
     Vulkan  D3D12  Metal      Async Tasks
       │      │      │
       └──────┼──────┘
              │
         Native Hardware
```

Cross-cutting:

```text
603 Security
604 IPC
606 Resource Governor
608 Synchronization
610 Crypto
611 Storage
612 Serialization
613 Package/CAS
602 Diagnostics
600 State/Recovery
```

---

# 253. Architectural Decision

BOOTSTRAP-615 establishes the **lowest practical graphics abstraction** above physical GPU/device management.

It deliberately provides two levels:

```text
Explicit GPU API
        +
Optional RenderGraph
```

This gives Axiom both:

- low-level control suitable for engines requiring C/C++-class performance;
- a higher-level scheduling facility without forcing an engine architecture onto the language.

The core runtime remains:

- non-GC;
- handle-based;
- explicit;
- capability-aware;
- cross-platform;
- dead-strippable;
- suitable for native applications;
- suitable for GPU compute;
- suitable as the foundation for later GUI/game/visualization/media layers.

---

# 254. Task Completion

**BOOTSTRAP-615 — COMPLETE**

Next queued architecture task:

**BOOTSTRAP-616 — Native Audio, Video, Camera, Media Codec, Streaming, Capture & Media Pipeline Runtime 5.0**
:::

BOOTSTRAP-615 đã hoàn tất và chuỗi kiến trúc tự động chuyển sang **BOOTSTRAP-616**.